"""
Health check API endpoints.

Used to verify that the API service
is running correctly.
"""

from datetime import datetime, timezone
from fastapi import APIRouter

# -------------------------------------------------------
# Router
# -------------------------------------------------------
router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

# -------------------------------------------------------
# GET /health
# -------------------------------------------------------
@router.get("")
def health_check() -> dict:
    """
    Basic service health check.

    Returns service status and timestamp.
    """

    return {
        "status": "healthy",
        "service": "Personal RAG Chatbot API",
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
    }