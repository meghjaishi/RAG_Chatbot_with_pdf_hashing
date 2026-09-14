from __future__ import annotations
import tiktoken
from config import CHAT_MODEL
from langchain_core.documents import Document
from utils.logger import get_logger

logger = get_logger(__name__)

def get_tokenizer(
    model: str = CHAT_MODEL
):
    """
    Return the tokenizer appropriate for the model.
    """
    try: 
        return tiktoken.encoding_for_model(
            model
        )
    except KeyError:
        return tiktoken.get_encoding(
            "cl100k_base"
        )

def count_tokens(
    text: str,
    model: str = CHAT_MODEL,
) -> int:
    """
    Count tokens in a text string.
    """

    encoding = get_tokenizer(
        model
    )

    return len(
        encoding.encode(text)
    )

def calculate_context_budget(
    max_prompt_tokens: int,
    reserved_output_tokens: int,
    system_tokens: int,
    question_tokens: int,
    history_tokens: int,
) -> int:
    """
    Calculate how many tokens remain available
    for retrieved document context.
    """

    return max(
        0, 
        max_prompt_tokens
        - reserved_output_tokens
        - system_tokens
        - question_tokens
        - history_tokens,
    )

def select_documents_by_token_budget(
    documents,
    max_tokens: int,
    formatter,
) -> list:
    """
    Select retrieved documents while keeping the fully formatted
    context within the available token budget.

    Documents are considered in retrieval order.

    An individual document that cannot fit within the available
    budget is skipped so that smaller, lower-ranked documents can
    still be considered.
    """
    if not documents or max_tokens <= 0:
        return []
    
    logger.info(
        "document_selection_started",
        extra={
            "extra_data": {
                "documents_available": len(documents),
                "max_tokens": max_tokens,
            }
        },
    )

    selected: list[Document] = []

    for index, document in enumerate(documents, start=1):
        # ---------------------------------------------------------
        # Check whether this document can fit by itself.
        # ---------------------------------------------------------
        document_context = formatter(
            [document]
        )

        document_tokens = count_tokens(
            document_context
        )

        logger.info(
            "document_selection_candidate",
            extra={
                "extra_data": {
                    "document_index": index,
                    "document_content_tokens": count_tokens(
                        document.page_content
                    ),
                    "document_context_tokens": document_tokens,
                    "max_tokens": max_tokens,
                    "selected_so_far": len(selected),
                }
            },
        )

        if document_tokens > max_tokens:
            logger.info(
                "document_skipped_too_large",
                extra={
                    "extra_data": {
                        "document_index": index,
                        "document_context_tokens": document_tokens,
                        "max_tokens": max_tokens,
                    }
                },
            )

            continue

        # ---------------------------------------------------------
        # Check whether this document fits with documents
        # already selected.
        # ---------------------------------------------------------
        candidate = selected + [document]
        formatted_context = formatter(
            candidate
        )
        context_tokens = count_tokens(
            formatted_context
        )

        # document_tokens = count_tokens(
        #     document.page_content
        # )

        # logger.info(
        #     "document_selection_candidate",
        #     extra={
        #         "extra_data": {
        #             "document_index": index,
        #             "document_content_tokens": document_tokens,
        #             "candidate_context_tokens": context_tokens,
        #             "max_tokens": max_tokens,
        #             "selected_so_far": len(selected),
        #         }
        #     },
        # )

        if context_tokens > max_tokens:

            logger.info(
                "document_selection_stopped",
                extra={
                    "extra_data": {
                        "document_index": index,
                        "candidate_context_tokens": context_tokens,
                        "max_tokens": max_tokens,
                        "documents_selected": len(selected),
                    }
                },
            )

            break

        selected.append(document)

    # -------------------------------------------------------------
    # Final selection summary
    # -------------------------------------------------------------
    final_context = formatter(
        selected
    )

    final_context_tokens = count_tokens(final_context)

    logger.info(
        "document_selection_completed",
        extra={
            "extra_data": {
                "documents_retrieved": len(documents),
                "documents_selected": len(selected),
                "max_tokens": max_tokens,
                "final_context_tokens": final_context_tokens,
            }
        },
    )

    return selected