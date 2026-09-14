"""
Utilities for normalizing LLM usage metadata.
"""

from __future__ import annotations


def normalize_usage(
    usage: dict | None,
) -> dict:
    """
    Extract stable token usage fields.

    Keeps API responses independent
    from provider-specific metadata.
    """

    if not usage:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

    return {
        "input_tokens": usage.get(
            "input_tokens",
            0,
        ),

        "output_tokens": usage.get(
            "output_tokens",
            0,
        ),

        "total_tokens": usage.get(
            "total_tokens",
            0,
        ),
    }