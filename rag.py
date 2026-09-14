"""
rag.py

Core Retrieval-Augmented Generation (RAG) pipeline.

Responsibilities
----------------
- Initialize OpenAI
- Initialize Pinecone
- Create vector store
- Create retriever
- Query documents
- Build prompts
- Generate answers

This module contains NO Streamlit code.
"""

from __future__ import annotations

# import logging
from utils.logger import get_logger
import time
from dataclasses import dataclass
from typing import List

from pinecone import Pinecone
from langchain_core.documents import Document
from langchain_openai import (
    ChatOpenAI,
    OpenAIEmbeddings,
)
from langchain_pinecone import (
    PineconeVectorStore,
)
from config import (
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    EMBEDDING_MODEL,
    CHAT_MODEL,
    TEMPERATURE,
    INPUT_TOKEN_COST_PER_MILLION,
    OUTPUT_TOKEN_COST_PER_MILLION,
    MAX_CONVERSATION_TURNS,
    MAX_CONVERSATION_TOKENS,
    MAX_PROMPT_TOKENS,
    RESERVED_OUTPUT_TOKENS,
)
from prompts import (
    SYSTEM_PROMPT,
    RAG_PROMPT,
    QUERY_REWRITE_PROMPT,
    NO_RELEVANT_DOCUMENTS_MESSAGE,
    format_context,
    format_sources,
)
from models import RetrievedDocument, RAGResponse, ConversationMessage
from api.request_context import request_id
from utils.cost import calculate_cost
from utils.usage import normalize_usage
from utils.conversation import trim_conversation_history, count_message_tokens
from utils.tokens import (
    count_tokens, 
    calculate_context_budget, 
    select_documents_by_token_budget,
)
from evaluation.dataset import make_chunk_id
# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
# logger = logging.getLogger(__name__)
logger = get_logger(__name__)
# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
DEFAULT_K = 3

DEFAULT_SCORE_THRESHOLD = 0.65

DEFAULT_MODEL = CHAT_MODEL

DEFAULT_TEMPERATURE = TEMPERATURE

# ---------------------------------------------------------------------
# RAG Engine
# ---------------------------------------------------------------------

class RAGEngine:
    """
    Production-ready RAG engine.

    One instance should live for the
    lifetime of the application.
    """
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        k: int = DEFAULT_K,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    ) -> None:

        self.model = model
        self.temperature = temperature
        self.k = k
        self.score_threshold = score_threshold

        logger.info("Initializing embeddings...")

        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            api_key=OPENAI_API_KEY,
        )

        logger.info("Connecting to Pinecone...")

        self.pc = Pinecone(
            api_key=PINECONE_API_KEY,
        )

        self.index = self.pc.Index(
            PINECONE_INDEX_NAME
        )

        self.vector_store = PineconeVectorStore(
            index=self.index,
            embedding=self.embeddings,
        )

        # logger.info(
        #     "vector_store_configuration",
        #     extra={
        #         "extra_data": {
        #             "vector_store_type": type(
        #                 self.vector_store
        #             ).__name__,
        #         }
        #     },
        # )
        logger.info("Creating retriever...")

        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",

            search_kwargs={
                "k": self.k,
                "score_threshold": self.score_threshold,
            },
        )
        # logger.info(
        #     "retriever_configuration",
        #     extra={
        #         "extra_data": {
        #             "retriever_type": type(
        #                 self.retriever
        #             ).__name__,
        #             "search_type": getattr(
        #                 self.retriever,
        #                 "search_type",
        #                 None,
        #             ),
        #             "search_kwargs": getattr(
        #                 self.retriever,
        #                 "search_kwargs",
        #                 None,
        #             ),
        #             "configured_score_threshold":
        #                 self.score_threshold,
        #             "configured_k": self.k,
        #         }
        #     },
        # )
        logger.info("Initializing ChatOpenAI...")

        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            api_key=OPENAI_API_KEY,
            streaming=True,
            stream_usage=True
        )

    # -------------------------------------------------------------
    def retrieve(
        self,
        question: str,
    ) -> tuple[List[Document], float]:
        """
        Retrieve relevant documents.
        """

        start = time.perf_counter()

        logger.info(
            "[%s] Question: %s",
            request_id.get(),
            question,
        )

        try:
            docs = self.retriever.invoke(question)
            
        except Exception as exc:
            raise RetrievalException("Failed to retrieve documents.") from exc

        elapsed = (
            time.perf_counter()
            - start
        )

        # TEST
        # results = self.vector_store.similarity_search_with_score(
        #     "What is the boiling point of water?",
        #     k=self.k,
        # )

        # for doc, score in results:
        #     print(
        #         "score:",
        #         score,
        #         "metadata:",
        #         doc.metadata,
        #     )

        # results = self.vector_store.similarity_search_with_relevance_scores(
        #     question,
        #     k=self.k,
        # )
        # for rank, (doc, score) in enumerate(results, start=1):
        #     print(
        #         f"rank={rank}, "
        #         f"relevance_score={score}, "
        #         f"source={doc.metadata.get('source_file')}"
        #     )
        # TEST COMPLETED

        logger.info(
            "retrieval_completed",
            extra={
                "extra_data": {
                    "documents_found": len(docs),
                    "retrieval_time": elapsed,
                }
            },
        )

        retrieval_documents = []
        for rank, doc in enumerate(docs, start=1):
            metadata = doc.metadata
            retrieval_documents.append(
                {
                    "rank": rank,
                    "source": metadata.get(
                        "source_file",
                        "Unknown",
                    ),
                    "page": metadata.get(
                        "page",
                    ),
                    "chunk": metadata.get(
                        "chunk",
                    ),
                    "chunk_id": make_chunk_id(
                        metadata["file_hash"],
                        metadata["chunk"],
                    ),
                    "tokens": count_tokens(
                        doc.page_content
                    ),
                    "score": metadata.get(
                        "score", 
                    ),
                }
            )
        
        logger.info(
            "retrieval_documents",
            extra={
                "extra_data": {
                    "documents": retrieval_documents,
                }
            }
        )

        return docs, elapsed       
    # -------------------------------------------------------------

    def rewrite_query(
        self,
        question: str,
        conversation_history: list[ConversationMessage] | None = None,
    ) -> str:
        """
        Rewrite a conversational question into a standalone
        retrieval query.

        If there is no conversation history, the original question
        is returned unchanged.
        """

        if not conversation_history:
            return question

        history = "\n".join(
            f"{message.role}: {message.content}"
            for message in conversation_history
        )

        prompt = QUERY_REWRITE_PROMPT.invoke(
            {
                "history": history,
                "question": question,
            }
        )

        response = self.llm.invoke(prompt)

        rewritten_question = response.content.strip()

        if not rewritten_question:
            return question

        logger.info(
            "query_rewritten",
            extra={
                "extra_data": {
                    "original_question": question,
                    "rewritten_question": rewritten_question,
                }
            },
        )

        return rewritten_question

    # -------------------------------------------------------------
    def build_prompt(
        self,
        question: str,
        documents: List[Document],
        conversation_history: list[ConversationMessage] | None = None,
    ):
        """
        Build the chat prompt using conversation history
        and retrieve document context.
        """

        conversation_history = (
            conversation_history or []
        )

        history = "\n".join(
            f"{message.role}: {message.content}"
            for message in conversation_history
        )

        history_tokens = count_tokens(
            history
        )

        context_budget = calculate_context_budget(
            max_prompt_tokens=MAX_PROMPT_TOKENS,
            reserved_output_tokens=RESERVED_OUTPUT_TOKENS,
            system_tokens=count_tokens(SYSTEM_PROMPT),
            question_tokens=count_tokens(question),
            history_tokens=history_tokens,
        )

        logger.info(
            "context_budget_calculated",
            extra={
                "extra_data": {
                    "max_prompt_tokens": MAX_PROMPT_TOKENS,
                    "reserved_output_tokens": RESERVED_OUTPUT_TOKENS,
                    "system_tokens": count_tokens(SYSTEM_PROMPT),
                    "question_tokens": count_tokens(question),
                    "history_tokens": history_tokens,
                    "context_budget": context_budget,
                }
            },
        )

        selected_documents = select_documents_by_token_budget(
                documents=documents,
                max_tokens=context_budget,
                formatter=format_context,
            )
        
        selected_metadata = []

        for rank, doc in enumerate(selected_documents, start=1):
            metadata = doc.metadata
            selected_metadata.append(
                {
                    "rank": rank, 
                    "source": metadata.get(
                        "source_file",
                        "Unknown",
                    ),
                    "page": metadata.get(
                        "page",
                    ),
                    "chunk": metadata.get(
                        "chunk",
                    ),
                    "tokens": count_tokens(
                        doc.page_content
                    ),
                }
            )
        logger.info(
            "context_documents_selected",
            extra={
                "extra_data": {
                    "documents_retrieved": len(
                        documents
                    ),
                    "documents_selected": len(
                        selected_documents
                    ),
                    "context_budget": context_budget,
                    "context_tokens": count_tokens(
                        format_context(
                            selected_documents
                        )
                    ),
                    "documents": selected_metadata,
                }
            },
        )
        
        context = format_context(
            selected_documents
        )

        return RAG_PROMPT.invoke(
            {
                "conversation_history": history,
                "context": context,
                "question": question,
            }
        )

    # -------------------------------------------------------------

    def generate(
        self,
        prompt,
    ) -> tuple[str, float, dict]:
        """
        Invoke the LLM synchronously and extract usage metadata.
        """

        start = time.perf_counter()

        try:
            response = self.llm.invoke(prompt)
        except Exception as exc:
            raise LLMException("LLM generation failed.") from exc

        elapsed = (time.perf_counter() - start)

        # Extract usage metadata attached by Langchain
        usage_metadata = getattr(response, "usage_metadata", {}) or {}

        logger.info(
            "generation_completed",
            extra={
                "extra_data": {
                    "generation_time": elapsed,
                    "usage": normalize_usage(usage_metadata),
                }
            },
        )

        return response.content, elapsed, usage_metadata

    # -------------------------------------------------------------

    def generate_stream(
        self,
        prompt: str,
    ):
        """
        Stream LLM tokens.
        """

        # messages = [
        #     SystemMessage(
        #         content=prompt
        #     )
        # ]
        usage = {}

        for chunk in self.llm.stream(prompt):
            # normal token
            if chunk.content:
                yield {
                    "type": "token",
                    "content": chunk.content,
                }
            
            # usage metadata
            if hasattr(chunk, "usage_metadata"):
                usage = chunk.usage_metadata
        yield {
            "type": "usage",
            "content": usage
        }
    # -------------------------------------------------------------

    def stream(
        self,
        question: str,
        conversation_history: list[ConversationMessage] | None = None,
    ):
        """
        Execute RAG pipeline with streaming output.
        """

        logger.info("-" * 60)
        logger.info(
            "[%s] Streaming question: %s",
            request_id.get(),
            question,
        )

        try:
            managed_history = trim_conversation_history(
                conversation_history,
                max_turns=MAX_CONVERSATION_TURNS,
                max_tokens=MAX_CONVERSATION_TOKENS,
            )
            
            managed_history_tokens = sum(
                count_message_tokens(message)
                for message in managed_history
            )

            logger.info(
                "conversation_history_managed",
                extra={
                    "extra_data": {
                        "original_messages": len(
                            conversation_history or []
                        ),
                        "managed_messages": len(
                            managed_history
                        ),
                        "managed_tokens": managed_history_tokens,
                        "max_turns": MAX_CONVERSATION_TURNS,
                        "max_tokens": MAX_CONVERSATION_TOKENS,
                    }
                },
            )

            retrieval_question = self.rewrite_query(
                question,
                managed_history,
            )

            documents, retrieval_time = self.retrieve(
                retrieval_question
            )
            if not documents:

                logger.info(
                    "no_relevant_documents",
                    extra={
                        "extra_data": {
                            "documents_found": 0,
                            "retrieval_time": retrieval_time,
                        }
                    },
                )

                yield {
                    "event": "token",
                    "data": NO_RELEVANT_DOCUMENTS_MESSAGE,
                }

                yield {
                    "event": "done",
                    "data": {
                        "status": "completed",
                        "request_id": request_id.get(),
                        "documents_found": 0,
                        "retrieval_time": retrieval_time,
                        "generation_time": 0.0,
                    },
                }

                return

            yield {
                "event": "metadata",
                "data": {
                    "request_id": request_id.get(),
                    "documents_found": len(documents),
                    "retrieval_time": retrieval_time,
                },
            }

            prompt = self.build_prompt(
                question,
                documents,
                conversation_history = managed_history,
            )

            generation_start = time.perf_counter()

            usage = {}
            for chunk in self.generate_stream(prompt):
                if chunk["type"] == "token":
                    # yield token
                    yield {
                        "event": "token",
                        "data": chunk["content"],
                    }
                elif chunk["type"] == "usage":
                    usage = chunk["content"]
            
            generation_time = (time.perf_counter() - generation_start)
            
            retrieved_documents = self.create_retrieved_documents(documents)

            yield {
                "event": "sources",
                "data": [
                    # doc.model_dump()
                    doc.to_dict()
                    for doc in retrieved_documents
                ],
            }

            normalized_usage = normalize_usage(usage)

            estimated_cost = calculate_cost(
                normalized_usage,
                INPUT_TOKEN_COST_PER_MILLION,
                OUTPUT_TOKEN_COST_PER_MILLION,
            )
        
            yield {
                "event": "done",
                "data": {
                    "status": "completed",
                    "request_id": request_id.get(),
                    "documents_found": len(documents),
                    "retrieval_time": retrieval_time,
                    "generation_time": generation_time,
                    "usage": normalized_usage,
                    "estimated_cost_usd": estimated_cost,
                },
            }

        except Exception as exc:
            # logger.exception(exc)
            logger.exception(
                "rag_pipeline_failed",
                extra={
                    "extra_data": {
                        "question": question,
                    }
                },
            )

            yield {
                "event": "error",
                "data": {
                    "message": str(exc),
                },
            }

    # -------------------------------------------------------------

    def create_retrieved_documents(
        self,
        documents,
    ):
        retrieved_documents = []

        for doc in documents:

            retrieved_documents.append(
                RetrievedDocument(
                    source=doc.metadata.get(
                        "source_file",
                        "Unknown",
                    ),

                    relative_path=doc.metadata.get(
                        "relative_path",
                        "",
                    ),

                    page=doc.metadata.get(
                        "page",
                    ),

                    chunk=doc.metadata.get(
                        "chunk",
                    ),

                    content=doc.page_content,
                )
            )

        return retrieved_documents

    # -------------------------------------------------------------

    def ask(
        self,
        question: str,
        conversation_history: list[ConversationMessage] | None = None,
    ) -> RAGResponse:
        """
        Execute the complete RAG pipeline.

        Steps
        -----
        1. Rewrite the question using conversation history.
        1. Retrieve relevant documents.
        2. Build the prompt using the original question.
        3. Generate an answer.
        4. Return the answer together with metadata.
        """

        logger.info("-" * 60)
        logger.info("[%s] Question: %s", request_id.get(), question)

        managed_history = trim_conversation_history(
            conversation_history,
            max_turns=MAX_CONVERSATION_TURNS,
            max_tokens=MAX_CONVERSATION_TOKENS,
        )

        managed_history_tokens = sum(
            count_message_tokens(message)
            for message in managed_history
        )

        logger.info(
            "conversation_history_managed",
            extra={
                "extra_data": {
                    "original_messages": len(
                        conversation_history or []
                    ),
                    "managed_messages": len(
                        managed_history
                    ),
                    "managed_tokens": managed_history_tokens,
                    "max_turns": MAX_CONVERSATION_TURNS,
                    "max_tokens": MAX_CONVERSATION_TOKENS,
                }
            },
        )

        retrieval_question = self.rewrite_query(
            question,
            managed_history,
        )

        documents, retrieval_time = self.retrieve(
            retrieval_question
        )

        if not documents:

            logger.info(
                "no_relevant_documents",
                extra={
                    "extra_data": {
                        "documents_found": 0,
                        "retrieval_time": retrieval_time,
                    }
                },
            )

            return RAGResponse(
                answer=NO_RELEVANT_DOCUMENTS_MESSAGE,
                documents=[],
                retrieval_time=retrieval_time,
                generation_time=0.0,
            )

        prompt = self.build_prompt(
            question,
            documents,
            conversation_history = managed_history,
        )

        answer, generation_time, usage_metadata = self.generate(
            prompt
        )

        normalized_usage = normalize_usage(usage_metadata)
        estimated_cost = calculate_cost(
            normalized_usage,
            INPUT_TOKEN_COST_PER_MILLION,
            OUTPUT_TOKEN_COST_PER_MILLION,
        )

        logger.info(
            "rag_pipeline_completed",
            extra={
                "extra_data": {
                    "documents_found": len(documents),
                    "retrieval_time": retrieval_time,
                    "generation_time": generation_time,
                    "usage": normalized_usage,
                    "estimated_cost_usd": estimated_cost,
                }
            },
        )

        retrieved_documents = (
            self.create_retrieved_documents(
                documents
            )
        )
        return RAGResponse(
            answer=answer,
            documents=retrieved_documents,
            # citations=citations,
            retrieval_time=retrieval_time,
            generation_time=generation_time,
        )

    # -------------------------------------------------------------

    def update_retriever(
        self,
        *,
        k: int | None = None,
        score_threshold: float | None = None,
    ) -> None:
        """
        Recreate the retriever with updated settings.
        """

        if k is not None:
            self.k = k

        if score_threshold is not None:
            self.score_threshold = score_threshold

        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": self.k,
                "score_threshold": self.score_threshold,
            },
        )

        logger.info(
            "Retriever updated (k=%d, threshold=%.2f)",
            self.k,
            self.score_threshold,
        )

    # -------------------------------------------------------------

    def update_llm(
        self,
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        """
        Update LLM settings without recreating
        the entire RAG engine.
        """

        if model is not None:
            self.model = model

        if temperature is not None:
            self.temperature = temperature

        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            api_key=OPENAI_API_KEY,
        )

        logger.info(
            "LLM updated (model=%s, temperature=%.2f)",
            self.model,
            self.temperature,
        )

    # -------------------------------------------------------------

    @property
    def configuration(self) -> dict:
        """
        Return the current configuration.
        """

        return {
            "model": self.model,
            "temperature": self.temperature,
            "k": self.k,
            "score_threshold": self.score_threshold,
            "embedding_model": EMBEDDING_MODEL,
            "pinecone_index": PINECONE_INDEX_NAME,
        }