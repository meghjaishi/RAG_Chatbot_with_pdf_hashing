from dataclasses import dataclass, asdict, field
from typing import Any

@dataclass(slots=True)
class RetrievedDocument:
    """
    A UI-agnostic representation of a retrieved document.
    """

    source: str
    relative_path: str
    page: int | None
    chunk: int |None
    content: str

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to a JSON-serializable dictionary.
        """
        return asdict(self)

@dataclass(slots=True)
class RAGResponse:
    """
    Response returned by the RAG pipeline.

    This class contains only plain Python types,
    making it independent of Streamlit, FastAPI,
    LangChain, or any other UI framework.
    """

    answer: str

    documents: list[RetrievedDocument] = field(default_factory=list)

    retrieval_time: float = 0.0

    generation_time: float = 0.0

    @property
    def citations(self) -> list[str]:
        """
        Return unique document citations.
        """

        citations = {
            f"{doc.source} (Page {doc.page})"
            for doc in self.documents
        }

        return sorted(citations)

    @property
    def total_time(self) -> float:
        """
        Total pipeline execution time.
        """

        return (
            self.retrieval_time
            + self.generation_time
        )
    
    @property
    def num_documents(self) -> int:
        """
        Number of retrieved documents.
        """

        return len(self.documents)

    def to_dict(self) -> dict:
        """
        Convert to a JSON-serializable dictionary.
        """

        return {
            "answer": self.answer,
            "documents": [
                doc.to_dict()
                for doc in self.documents
            ],
            "citations": self.citations,
            "retrieval_time": self.retrieval_time,
            "generation_time": self.generation_time,
            "total_time": self.total_time,
            "num_documents": self.num_documents,
        }

@dataclass(slots=True)
class ConversationMessage:
    """
    A UI-agnostic representation of a conversation message
    """

    role: str
    content: str

    def to_dict(self) -> dict:
        asdict(self)