"""
Chat API endpoints.

This module exposes the RAG agent
through HTTP endpoints.
"""

# import logging
from typing import Annotated
from utils.logger import get_logger
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import StreamingResponse
from rag import RAGEngine
from api.dependencies import (
    get_rag_engine
)
from models import ConversationMessage
from api.schemas import (
    ChatRequest,
    ChatResponse,
)
from api.converters import (
    rag_response_to_api,
)
from api.auth.models import User
from api.auth.security import get_current_user
from json import dumps

# logger = logging.getLogger(__name__)
logger = get_logger(__name__)

# -------------------------------------------------------
# Router
# -------------------------------------------------------
router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

# -------------------------------------------------------
# POST /chat
# -------------------------------------------------------
@router.post("", response_model=ChatResponse,)
def chat(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    engine: RAGEngine = Depends(get_rag_engine),
) -> ChatResponse:
    """
    Ask a question to the RAG chatbot.

    Example:

    POST /chat

    {
        "question": "What is the remote work policy?"
    }
    """

    logger.info(
        "Received question: %s",
        request.question,
    )

    try:
        conversation_history = [
            ConversationMessage(
                role=message.role,
                content=message.content,
            )
            for message in request.conversation_history
        ]

        response = engine.ask(
            request.question,
            conversation_history=conversation_history,
            )

        return rag_response_to_api(response)


    except Exception as exc:

        logger.exception("RAG request failed")

        raise HTTPException(
            status_code=500,
            detail=(
                "An error occurred "
                "while processing the question."
            ),
        ) from exc

# -------------------------------------------------------
# POST /chat/stream
# -------------------------------------------------------

@router.post("/stream")
def chat_stream(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    engine: RAGEngine = Depends(get_rag_engine),
):

    def event_generator():
        conversation_history = [
            ConversationMessage(
                role=message.role,
                content=message.content,
            )
            for message in request.conversation_history
        ]
        for event in engine.stream(
            request.question,
            conversation_history=conversation_history,
        ):
            yield (
                f"event: {event['event']}\n"
                f"data: {dumps(event['data'])}\n\n"
            )


    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )