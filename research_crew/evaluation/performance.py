"""
performance.py
--------------
Evaluates performance metrics like token usage and latency.
"""

import time
from research_crew.utils.token_utils import count_tokens


def evaluate_performance(report: str) -> dict:
    """
    Returns:
    {
        "tokens": int,
        "latency": float
    }
    """

    tokens = count_tokens(report)

    return {
        "tokens": tokens
    }