"""
Pydantic models used by FastAPI endpoints.

These models define the JSON request
and response structure exposed by the API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal

# -------------------------------------------------------
# Chat Message
# -------------------------------------------------------
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(
        examples=["user"]
    )
    content: str = Field(
        examples=["What is reinforcement Learning?"]
    )

# -------------------------------------------------------
# Chat Request
# -------------------------------------------------------
class ChatRequest(BaseModel):
    """
    Incoming user question.
    """

    question: str = Field(
        ...,
        min_length=1,
        description="Question to ask the RAG chatbot",
        examples=[
            "Who invented it?"
        ],
    )
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        examples= [
            [
                {
                    "role": "user",
                    "content": "What is reinforcement learning?",
                },
                {
                    "role": "assistant",
                    "content": "Reinforcement learning is a machine learning approach where an agent learns through interaction with an environment.",
                },
            ]
        ],
    )


# -------------------------------------------------------
# Retrieved Document Response
# -------------------------------------------------------

class RetrievedDocumentResponse(BaseModel):
    """
    Document information returned to API clients.
    """

    source: str

    relative_path: str

    page: int | None = None

    chunk: int | None = None

    content: str

# -------------------------------------------------------
# Chat Response
# -------------------------------------------------------

class ChatResponse(BaseModel):
    """
    Complete RAG response returned by /chat.
    """

    answer: str

    citations: List[str] = Field(
        default_factory=list
    )

    documents: List[RetrievedDocumentResponse] = Field(
        default_factory=list
    )

    request_id: str

    retrieval_time: float = 0.0

    generation_time: float = 0.0

    total_time: float = 0.0

    num_documents: int = 0

# moved to converters.py
# from models import RAGResponse

# def rag_response_to_api(
#     response: RAGResponse,
# ) -> ChatResponse:
#     """
#     Convert internal RAGResponse
#     into API response format.
#     """

#     return ChatResponse(
#         answer=response.answer,

#         citations=response.citations,

#         documents=[
#             RetrievedDocumentResponse(
#                 **doc.to_dict()
#             )
#             for doc in response.documents
#         ],

#         retrieval_time=response.retrieval_time,

#         generation_time=response.generation_time,

#         total_time=response.total_time,

#         num_documents=response.num_documents,
#     )

# -------------------------------------------------------
# Error Details
# -------------------------------------------------------
class ErrorDetail(BaseModel):
    """
    Standard error information.
    """

    type: str = Field(
        description="Exception type"
    )

    message: str = Field(
        description="Human-readable error message"
    )

# -------------------------------------------------------
# Error Response
# -------------------------------------------------------
class ErrorResponse(BaseModel):
    """
    Standard API error response.
    """

    error: ErrorDetail


class StreamEvent(BaseModel):
    event: str
    data: dict | str