"""
web_parser.py
-------------
Fetches a webpage and extracts human-readable text using BeautifulSoup.

Extraction strategy
-------------------
1. Prefer <article>, <main>, and <section role="main"> elements — these
   contain primary content on research pages and documentation sites.
2. Fall back to the full <body> with boilerplate tags stripped.
3. Hard-truncate the result to HARD_TEXT_LIMIT characters before returning.

GitHub repos
------------
When the URL is a GitHub repository root, the tool fetches the rendered
README text from the API rather than parsing the HTML UI chrome.
"""

"""
web_parser.py
-------------
Fetch and extract clean text from webpages.

Handles:
- Documentation pages
- Articles
- GitHub repositories (README via API)

Safety:
- Truncates output to 3000 characters
- Removes boilerplate HTML
"""

import logging
import re
import os
from typing import Type

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

try:
    from crewai.tools import BaseTool
except ImportError:
    from langchain.tools import BaseTool  # type: ignore

from research_crew.utils.token_utils import truncate_text

logger = logging.getLogger(__name__)

HARD_TEXT_LIMIT = 3000
REQUEST_TIMEOUT = 20

STRIP_TAGS = {
    "script", "style", "noscript", "header", "footer",
    "nav", "aside", "form", "button", "svg", "img",
    "figure", "iframe"
}


class _WebInput(BaseModel):
    url: str = Field(..., description="URL of webpage or GitHub repo")


class WebParserTool(BaseTool):
    name: str = "Webpage Text Parser"
    description: str = "Extract clean readable text from webpages or GitHub repos."
    args_schema: Type[BaseModel] = _WebInput

    @retry(
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        wait=wait_exponential(multiplier=2, min=2, max=20),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _run(self, url: str) -> str:
        # GitHub special case
        if _is_github_repo_root(url):
            return _fetch_github_readme(url)

        logger.info("Fetching webpage: %s", url)

        resp = requests.get(
            url,
            headers={
                "User-Agent": "ResearchCrew/1.0",
                "Accept": "text/html",
            },
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()

        # ❗ Ensure HTML content
        if "text/html" not in resp.headers.get("Content-Type", ""):
            return "Error: URL does not contain HTML content."

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove junk tags
        for tag in soup(list(STRIP_TAGS)):
            tag.decompose()

        text = _extract_main_content(soup)
        text = _normalize_whitespace(text)

        # ❗ Empty check
        if not text.strip():
            return "Error: No readable content extracted from webpage."

        # ✅ Token-safe truncation
        text = truncate_text(text, HARD_TEXT_LIMIT)

        logger.info("Parsed %d chars from %s", len(text), url)

        return f"[WEB CONTENT]\n\n{text}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_main_content(soup: BeautifulSoup) -> str:
    for selector in [
        "article", "main", '[role="main"]',
        ".content", "#content", ".post-content", ".entry-content"
    ]:
        element = soup.select_one(selector)
        if element:
            return element.get_text(separator="\n")

    body = soup.find("body")
    return body.get_text(separator="\n") if body else soup.get_text(separator="\n")


def _normalize_whitespace(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines))


def _is_github_repo_root(url: str) -> bool:
    pattern = r"^https?://github\.com/[^/]+/[^/]+/?$"
    return bool(re.match(pattern, url))


def _fetch_github_readme(repo_url: str) -> str:
    match = re.search(r"github\.com/([^/]+/[^/]+)", repo_url)
    if not match:
        return f"Error: Invalid GitHub URL: {repo_url}"

    repo = match.group(1)
    api_url = f"https://api.github.com/repos/{repo}/readme"

    github_token = os.getenv("GITHUB_TOKEN")

    headers = {
        "Accept": "application/vnd.github.v3.raw",
        **({"Authorization": f"Bearer {github_token}"} if github_token else {})
    }

    try:
        resp = requests.get(api_url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        text = _normalize_whitespace(resp.text)

        if not text.strip():
            return "Error: Empty README content."

        text = truncate_text(text, HARD_TEXT_LIMIT)

        return f"[GITHUB README]\n\n{text}"

    except Exception as e:
        logger.warning("GitHub fetch failed: %s", e)
        return f"Error: Could not fetch README for {repo_url}"