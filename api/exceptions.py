"""
Custom exceptions used by the API.
"""


class RAGException(Exception):
    """Base exception for the RAG application."""


class RetrievalException(RAGException):
    """Raised when document retrieval fails."""


class LLMException(RAGException):
    """Raised when LLM generation fails."""


class VectorStoreException(RAGException):
    """Raised when Pinecone operations fail."""


class ConfigurationException(RAGException):
    """Raised when configuration is invalid."""