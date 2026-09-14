"""
Cost calculation utilities for LLM usage.
"""

from __future__ import annotations


def calculate_cost(
    usage: dict,
    input_price_per_million: float,
    output_price_per_million: float,
) -> float:
    """
    Calculate estimated LLM cost.

    Parameters
    ----------
    usage:
        Dictionary containing token counts.

    input_price_per_million:
        Cost per 1M input tokens.

    output_price_per_million:
        Cost per 1M output tokens.

    Returns
    -------
    float
        Estimated USD cost.
    """

    input_tokens = usage.get(
        "input_tokens",
        0,
    )

    output_tokens = usage.get(
        "output_tokens",
        0,
    )

    input_cost = (
        input_tokens / 1_000_000
    ) * input_price_per_million

    output_cost = (
        output_tokens / 1_000_000
    ) * output_price_per_million

    return round(
        input_cost + output_cost,
        6,
    )