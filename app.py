"""
app.py

Streamlit frontend for the Personal RAG Chatbot.

Responsibilities
----------------
- Streamlit UI
- Sidebar settings
- Chat history
- User interaction
- Display retrieved sources

Business logic is implemented in rag.py.
"""

from __future__ import annotations

# import logging
from utils.logger import get_logger
import streamlit as st

from rag import RAGEngine
from models import ConversationMessage
from uuid import uuid4
from api.request_context import request_id
# -------------------------------------------------------
# Logging
# -------------------------------------------------------
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)s | %(message)s",
# )

# logger = logging.getLogger(__name__)
logger = get_logger(__name__)

# -------------------------------------------------------
# Page Configuration
# -------------------------------------------------------
st.set_page_config(
    page_title="Personal RAG Chatbot",
    page_icon="🤖",
    layout="wide",
)

# -------------------------------------------------------
# Cached RAG Engine
# -------------------------------------------------------
@st.cache_resource
def load_engine() -> RAGEngine:
    """
    Create the RAG engine once.

    The same instance is reused for all
    reruns during the Streamlit session.
    """

    return RAGEngine()

# -------------------------------------------------------
# Session State
# -------------------------------------------------------
def initialize_session() -> None:
    """
    Initialize Streamlit session state.
    """

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "engine" not in st.session_state:
        st.session_state.engine = load_engine()

# -------------------------------------------------------
# Sidebar
# -------------------------------------------------------
def sidebar() -> None:
    """
    Render sidebar controls.

    Settings are applied only when the user
    clicks the Apply button.
    """

    st.sidebar.title("⚙️ Settings")

    engine: RAGEngine = st.session_state.engine


    # -------------------------------------------------------
    # Settings Form
    # -------------------------------------------------------

    with st.sidebar.form(
        "rag_settings"
    ):

        # ----------------------------
        # Retrieval
        # ----------------------------

        st.subheader("Retrieval")

        k = st.slider(
            "Top K Documents",
            min_value=1,
            max_value=10,
            value=engine.k,
        )

        # st.sidebar.write(
        # type(engine.score_threshold),
        # engine.score_threshold
        # )

        threshold = st.slider(
            "Similarity Threshold",
            min_value=0.0,
            max_value=1.0,
            value=engine.score_threshold,
            step=0.05,
        )


        # ----------------------------
        # Model
        # ----------------------------

        st.subheader("Model")

        # st.sidebar.write(
        # type(engine.temperature),
        # engine.temperature
        # )

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=engine.temperature,
            step=0.1,
        )


        submitted = st.form_submit_button(
            "Apply Settings",
            use_container_width=True,
        )


    # -------------------------------------------------------
    # Apply Changes
    # -------------------------------------------------------

    if submitted:

        retriever_changed = (
            k != engine.k
            or
            threshold != engine.score_threshold
        )


        llm_changed = (
            temperature != engine.temperature
        )


        if retriever_changed:

            engine.update_retriever(
                k=k,
                score_threshold=threshold,
            )


        if llm_changed:

            engine.update_llm(
                temperature=temperature,
            )


        st.sidebar.success(
            "Settings updated ✅"
        )


    # -------------------------------------------------------
    # Current Configuration
    # -------------------------------------------------------

    with st.sidebar.expander(
        "Current Configuration",
        expanded=False,
    ):

        st.json(
            engine.configuration
        )
        # st.write("Configuration loaded")


    # -------------------------------------------------------
    # Clear Chat
    # -------------------------------------------------------

    if st.sidebar.button(
        "🗑 Clear Conversation",
        use_container_width=True,
    ):

        st.session_state.messages = []

        st.rerun()
# -------------------------------------------------------
# Chat History
# -------------------------------------------------------

def render_chat_history() -> None:
    """
    Display previous conversation.
    """

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )

# -------------------------------------------------------
# Helper
# -------------------------------------------------------

def add_message(
    role: str,
    content: str,
) -> None:
    """
    Add message to session history.
    """

    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
        }
    )

# -------------------------------------------------------
# Sources
# -------------------------------------------------------

def display_sources(
    response: RAGResponse,
) -> None:
    """
    Display retrieved documents.
    """

    if not response.documents:
        return

    with st.expander(
        "📚 Retrieved Documents",
        expanded=False,
    ):

        for index, document in enumerate(
            response.documents,
            start=1,
        ):

            st.markdown(
                f"### Document {index}"
            )

            st.write(
                f"**Source:** {document.source}"
            )

            st.write(
                f"**Page:** {document.page}"
            )

            st.write(
                f"**Chunk:** {document.chunk}"
            )

            st.code(
                document.content,
                language=None,
            )

            st.divider()

# -------------------------------------------------------
# Metrics
# -------------------------------------------------------

def display_metrics(
    response: RAGResponse,
) -> None:
    """
    Display pipeline timings.
    """

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Retrieval",
            f"{response.retrieval_time:.2f}s",
        )

    with col2:

        st.metric(
            "Generation",
            f"{response.generation_time:.2f}s",
        )

# -------------------------------------------------------
# Answer Display
# -------------------------------------------------------

def display_answer(
    response: RAGResponse,
) -> None:
    """
    Display the generated answer,
    sources, and performance metrics.
    """

    # ----------------------------
    # Answer
    # ----------------------------

    st.markdown(
        response.answer
    )

    # ----------------------------
    # Citations
    # ----------------------------

    if response.citations:

        with st.expander(
            "📌 Sources",
            expanded=False,
        ):

            for citation in response.citations:

                st.markdown(
                    f"- {citation}"
                )

    # ----------------------------
    # Retrieved Context
    # ----------------------------

    display_sources(
        response
    )

    # ----------------------------
    # Timing
    # ----------------------------

    with st.expander(
        "⏱ Performance",
        expanded=False,
    ):

        display_metrics(
            response
        )

# -------------------------------------------------------
# User Interaction
# -------------------------------------------------------

def handle_user_input() -> None:
    """
    Handle new user questions.
    """

    prompt = st.chat_input(
        "Ask a question about your documents..."
    )

    if not prompt:

        return

    # ----------------------------
    # User Message
    # ----------------------------
    add_message(
        role="user",
        content=prompt,
    )

    with st.chat_message(
        "user"
    ):

        st.markdown(
            prompt
        )


    # ----------------------------
    # Assistant Response
    # ----------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Searching documents..."
        ):

            try:
                rid = str(uuid4())
                token = request_id.set(rid)

                try:
                    conversation_history = [
                        ConversationMessage(
                            role=message["role"],
                            content=message["content"],
                        )
                        for message in st.session_state.messages[:-1]
                    ]

                    response = st.session_state.engine.ask(
                        prompt,
                        conversation_history=conversation_history,
                        )
                finally:
                    request_id.reset(token)

                display_answer(
                    response
                )


                add_message(
                    role="assistant",
                    content=response.answer,
                )


            # except Exception:
            #     logger.exception(
            #         "RAG pipeline failed"
            #     )
            except Exception as e:

                import traceback

                traceback.print_exc()

                st.exception(e)

                logger.exception(
                    "RAG pipeline failed"
                )

                error_message = (
                    "⚠️ Sorry, I encountered "
                    "an error while processing "
                    "your question."
                )

                st.error(
                    error_message
                )


                add_message(
                    role="assistant",
                    content=error_message,
                )

# -------------------------------------------------------
# Application Entry Point
# -------------------------------------------------------

def main() -> None:
    """
    Main Streamlit application.
    """

    initialize_session()
    st.title(
        "🤖 Personal RAG Chatbot"
    )

    st.caption(
        "Ask questions about your uploaded documents."
    )

    sidebar()

    render_chat_history()

    handle_user_input()

    ## TEST

    # history = [
    #     ConversationMessage(
    #         role="user",
    #         content="What is reinforcement learning?",
    #     ),
    #     ConversationMessage(
    #         role="assistant",
    #         content="Reinforcement learning is a machine learning approach...",
    #     ),
    # ]

    # rewritten = st.session_state.engine.rewrite_query(
    #     "Who invented it?",
    #     history,
    # )

    # print(rewritten)

# -------------------------------------------------------
# Run Application
# -------------------------------------------------------

if __name__ == "__main__":
    main()