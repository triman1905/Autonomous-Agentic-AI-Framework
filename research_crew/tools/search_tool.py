"""
search_tool.py
--------------
CrewAI-compatible tools for searching academic and technical sources.

Two search backends:
  * ExaSearchTool (primary)
  * TavilySearchTool (fallback)

Returns structured JSON list of SourceResult dicts.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Type

import requests
from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

try:
    from crewai.tools import BaseTool
except ImportError:
    from langchain.tools import BaseTool  # type: ignore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain classification
# ---------------------------------------------------------------------------
PAPER_DOMAINS = (
    "arxiv.org", "ieee.org", "acl.org", "aclweb.org",
    "semanticscholar.org", "papers.nips.cc", "openreview.net",
    "dl.acm.org", "pubmed.ncbi.nlm.nih.gov"
)

REPO_DOMAINS = ("github.com", "gitlab.com", "huggingface.co")

DOC_DOMAINS = (
    "docs.", "readthedocs.io", "pytorch.org", "tensorflow.org",
    "scikit-learn.org", "numpy.org", "scipy.org",
    "kubernetes.io", "developer.mozilla.org"
)

JUNK_DOMAINS = (
    "medium.com", "towardsdatascience.com", "analyticsvidhya.com",
    "machinelearningmastery.com", "kdnuggets.com", "datacamp.com",
    "buzzfeed", "quora.com", "reddit.com"
)


def _classify_source(url: str) -> str:
    url = url.lower()
    if any(d in url for d in PAPER_DOMAINS):
        return "paper"
    if any(d in url for d in REPO_DOMAINS):
        return "repo"
    if any(d in url for d in DOC_DOMAINS):
        return "documentation"
    return "web"


def _is_junk(url: str) -> bool:
    return any(d in url.lower() for d in JUNK_DOMAINS)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
class SourceResult(BaseModel):
    title: str
    url: str
    source_type: str
    published_date: str
    snippet: str


# ---------------------------------------------------------------------------
# Exa Tool
# ---------------------------------------------------------------------------
class _ExaInput(BaseModel):
    query: str
    num_results: int = 8


class ExaSearchTool(BaseTool):
    name: str = "Exa Academic Search"
    description: str = "Search academic papers, repos, and docs using Exa API."
    args_schema: Type[BaseModel] = _ExaInput

    @retry(
        retry=retry_if_exception_type(requests.exceptions.HTTPError),
        wait=wait_exponential(min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _run(self, query: str, num_results: int = 8) -> str:
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            return json.dumps([])

        payload = {
            "query": query,
            "numResults": min(num_results, 10),
            "useAutoprompt": True,
            "type": "neural",
            "contents": {"text": {"maxCharacters": 800}},
            "includeDomains": list(PAPER_DOMAINS) + list(REPO_DOMAINS),
        }

        resp = requests.post(
            "https://api.exa.ai/search",
            headers={"x-api-key": api_key},
            json=payload,
            timeout=20,
        )

        resp.raise_for_status()
        data = resp.json()

        results: List[Dict[str, Any]] = []

        for item in data.get("results", []):
            url = item.get("url", "")
            if _is_junk(url):
                continue

            results.append(
                SourceResult(
                    title=item.get("title", "Untitled"),
                    url=url,
                    source_type=_classify_source(url),
                    published_date=item.get("publishedDate") or "Unknown",
                    snippet=(item.get("text") or item.get("snippet", ""))[:500],
                ).model_dump()
            )
            time.sleep(0.1)

        # Deduplicate
        unique = {r["url"]: r for r in results}
        results = list(unique.values())

        # Limit results
        results = results[:10]

        if not results:
            logger.warning("No Exa results for query: %s", query)

        return json.dumps(results, indent=2)


# ---------------------------------------------------------------------------
# Tavily Tool
# ---------------------------------------------------------------------------
class _TavilyInput(BaseModel):
    query: str
    num_results: int = 8


class TavilySearchTool(BaseTool):
    name: str = "Tavily Academic Search"
    description: str = "Fallback search using Tavily API."
    args_schema: Type[BaseModel] = _TavilyInput

    @retry(
        retry=retry_if_exception_type(requests.exceptions.HTTPError),
        wait=wait_exponential(min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _run(self, query: str, num_results: int = 8) -> str:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return json.dumps([])

        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": min(num_results, 10),
        }

        resp = requests.post(
            "https://api.tavily.com/search",
            json=payload,
            timeout=20,
        )

        resp.raise_for_status()
        data = resp.json()

        results: List[Dict[str, Any]] = []

        for item in data.get("results", []):
            url = item.get("url", "")
            if _is_junk(url):
                continue

            results.append(
                SourceResult(
                    title=item.get("title", "Untitled"),
                    url=url,
                    source_type=_classify_source(url),
                    published_date=item.get("published_date") or "Unknown",
                    snippet=item.get("content", "")[:500],
                ).model_dump()
            )

        # Deduplicate
        unique = {r["url"]: r for r in results}
        results = list(unique.values())

        # Limit results
        results = results[:10]

        if not results:
            logger.warning("No Tavily results for query: %s", query)

        return json.dumps(results, indent=2)