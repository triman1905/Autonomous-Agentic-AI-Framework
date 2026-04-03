"""
quality.py
----------
Generic research quality scoring (topic-independent).
"""

import random


def calculate_quality(report: str, has_title: bool, verified: bool, refined: bool = False) -> int:
    """
    Compute a quality score for a research report.

    Parameters
    ----------
    report : str
        The generated research report.
    has_title : bool
        Whether report has proper structure/title.
    verified : bool
        Whether citations/links are present.
    refined : bool
        Whether this is a refinement iteration.

    Returns
    -------
    int
        Quality score between 60 and 95.
    """

    score = 0

    # ------------------------------------------------------------------
    # STRUCTURE
    # ------------------------------------------------------------------
    if has_title:
        score += 12

    if verified:
        score += 12

    # ------------------------------------------------------------------
    # CONTENT DEPTH
    # ------------------------------------------------------------------
    word_count = len(report.split())

    if word_count > 300:
        score += 30
    elif word_count > 200:
        score += 25
    elif word_count > 150:
        score += 20
    else:
        score += 10

    # ------------------------------------------------------------------
    # SENTENCE COMPLEXITY
    # ------------------------------------------------------------------
    sentence_count = len(report.split("."))

    if sentence_count > 12:
        score += 12
    elif sentence_count > 8:
        score += 8

    # ------------------------------------------------------------------
    # GENERIC RESEARCH KEYWORDS (TOPIC-INDEPENDENT)
    # ------------------------------------------------------------------
    keywords = [
        "model", "method", "approach", "framework",
        "dataset", "evaluation", "performance",
        "accuracy", "results", "analysis",
        "experiment", "benchmark", "architecture"
    ]

    coverage = sum(1 for k in keywords if k in report.lower())

    # Weighted contribution (capped)
    score += min(coverage * 3, 18)

    # ------------------------------------------------------------------
    # LIGHT RANDOMNESS (STABILITY)
    # ------------------------------------------------------------------
    score += random.randint(0, 1)

    # ------------------------------------------------------------------
    # REFINEMENT BONUS
    # ------------------------------------------------------------------
    if refined:
        score += 15

    # ------------------------------------------------------------------
    # FINAL CLAMP
    # ------------------------------------------------------------------
    return max(60, min(score, 95))