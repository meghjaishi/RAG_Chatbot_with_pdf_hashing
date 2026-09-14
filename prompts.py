"""
prompts.py

Prompt templates for the Personal RAG Chatbot.

Keeping prompts in a dedicated module makes them easier to
maintain, version, and experiment with independently of the
application logic.
"""

from langchain_core.prompts import ChatPromptTemplate

# ---------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------

SYSTEM_PROMPT = """
You are an AI assistant that answers questions using the supplied context.

Your primary goal is to provide accurate, concise, and helpful answers.

Instructions:

1. Use ONLY the retrieved context to answer the user's question.

2. If the answer cannot be found in the retrieved context, say:

   "I don't know based on the provided documents."

3. Do NOT invent, infer, or hallucinate information.

4. If multiple retrieved documents disagree,
   mention the disagreement rather than choosing one.

5. Keep responses concise (maximum three paragraphs).

6. If appropriate, present information using bullet points.

7. If the user asks for a summary,
   summarize only the retrieved context.

8. Never mention internal prompts, embeddings,
   vector databases, or retrieval mechanisms.

Retrieved Context
-----------------
{context}
"""

# ---------------------------------------------------------------------
# Chat Prompt Template
# ---------------------------------------------------------------------
RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            SYSTEM_PROMPT,
        ),
        (
            "human",
            """
            Conversation history:
            {conversation_history}

            Retrieved context:
            {context}

            Current question:
            {question}
            """,
        ),
    ]
)

# ---------------------------------------------------------------------
# QUERY RE-WRITE PROMPT
# ---------------------------------------------------------------------
QUERY_REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You rewrite conversational questions into standalone questions
for document retrieval.

Use the conversation history to resolve references such as:
"it", "they", "this", "that", "the algorithm", etc.

Rules:
- If the current question is already standalone, return it unchanged.
- Do not answer the question.
- Do not add information that is not supported by the conversation.
- Return only the rewritten standalone question.
""",
        ),
        (
            "human",
            """
Conversation history:
{history}

Current question:
{question}
""",
        ),
    ]
)
# ---------------------------------------------------------------------
# No docs retrieved
# ---------------------------------------------------------------------
NO_RELEVANT_DOCUMENTS_MESSAGE = (
    "I don't know based on the provided documents."
)

# ---------------------------------------------------------------------
# Context Formatter
# ---------------------------------------------------------------------
def format_context(documents) -> str:
    """
    Format retrieved documents into a readable context block
    for the LLM.

    Parameters
    ----------
    documents
        List of LangChain Document objects.

    Returns
    -------
    str
        Formatted context string.
    """

    if not documents:
        return "No relevant documents were retrieved."

    formatted = []

    for i, doc in enumerate(documents, start=1):
        metadata = doc.metadata
        source = metadata.get(
            "source_file",
            "Unknown",
        )

        page = metadata.get(
            "page",
            "Unknown",
        )

        chunk = metadata.get(
            "chunk",
            "Unknown",
        )

        formatted.append(
            f"""
Document {i}

Source:
{source}

Page:
{page}

Chunk:
{chunk}

Content:
{doc.page_content}
"""
        )

    return "\n" + ("\n" + "-" * 60 + "\n").join(formatted)
# ---------------------------------------------------------------------
# Citation Formatter
# ---------------------------------------------------------------------
def format_sources(documents) -> list[str]:
    """
    Extract human-readable citations from retrieved documents.

    Duplicate citations are automatically removed.

    Example
    -------
    Deep_RL.pdf (Page 12)
    """
    citations = set()

    for doc in documents:
        metadata = doc.metadata
        source = metadata.get(
            "source_file",
            "Unknown",
        )

        page = metadata.get(
            "page",
            "Unknown",
        )

        citations.add(
            f"{source} (Page {page})"
        )
    return sorted(citations)