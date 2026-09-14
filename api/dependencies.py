"""
FastAPI dependency providers.

This module manages application-level
objects that are reused across requests.
"""

# import logging
# from functools import lru_cache
from fastapi import Request
from rag import RAGEngine

# logger = logging.getLogger(__name__)

# @lru_cache(maxsize=1)
def get_rag_engine(request: Request) -> RAGEngine:
    """
    Retrieve the initialized RAG engine
    from application state.
    """

    return request.app.state.rag_engine
