from models import RAGResponse

from api.schemas import (
    ChatResponse,
    RetrievedDocumentResponse,
)

from api.request_context import request_id

def rag_response_to_api(
    response: RAGResponse,
) -> ChatResponse:

    return ChatResponse(

        answer=response.answer,

        citations=response.citations,

        documents=[
            RetrievedDocumentResponse(
                **doc.to_dict()
            )
            for doc in response.documents
        ],

        request_id=request_id.get(),

        retrieval_time=response.retrieval_time,

        generation_time=response.generation_time,

        total_time=response.total_time,

        num_documents=response.num_documents,
    )