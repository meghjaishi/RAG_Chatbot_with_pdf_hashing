"""
FastAPI application entry point.

This module creates the API application
and registers all API routers.
"""

# import logging
from utils.logger import get_logger
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.exceptions import (
    RetrievalException,
    LLMException,
    VectorStoreException,
)
from api.schemas import ErrorResponse, ErrorDetail
from api.routers import chat, health
from api.auth.router import router as auth_router
from rag import RAGEngine
from api.middleware import RequestIDMiddleware
# from utils.logging import setup_logging
# -------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------
# logging.basicConfig(
#     level=logging.INFO,
#     format=(
#         "%(asctime)s | "
#         "%(levelname)s | "
#         "%(name)s | "
#         "%(message)s"
#     ),
# )
# logger = logging.getLogger(__name__)
logger = get_logger(__name__)

# -------------------------------------------------------
# Application Lifecycle
# -------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs during application startup
    and shutdown.
    """

    logger.info(
        "Starting Personal RAG Chatbot API..."
    )

    # Initialize RAG engine once
    logger.info("Initializing RAG Engine...")

    app.state.rag_engine = RAGEngine()

    logger.info("RAG Engine initialized successfully.")

    yield


    logger.info("Shutting down Personal RAG Chatbot API...")

# -------------------------------------------------------
# FastAPI Application
# -------------------------------------------------------
# setup_logging()

app = FastAPI(
    title="Personal RAG Chatbot API",

    description=(
        "A Retrieval-Augmented Generation API "
        "powered by Pinecone and OpenAI."
    ),

    version="1.0.0",

    lifespan=lifespan,
)

# -------------------------------------------------------
# Register Routers
# -------------------------------------------------------
app.include_router(
    health.router
)


app.include_router(
    chat.router
)

app.include_router(
    auth_router
)
# -------------------------------------------------------
# Register middleware
# -------------------------------------------------------
app.add_middleware(
    RequestIDMiddleware,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------
# Root endpoint
# -------------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "Personal RAG Chatbot API",
        "docs": "/docs",
        "health": "/health"
    }

# -------------------------------------------------------
# Exception Handling
# -------------------------------------------------------
@app.exception_handler(RetrievalException)
async def retrieval_exception_handler(
    request: Request, 
    exc: RetrievalException,
):
    logger.exception(exc)

    response = ErrorResponse(
        error=ErrorDetail(
            type="RetrievalException",
            message=str(exc),
        )
    )

    return JSONResponse(
        status_code=503,
        content=response.model_dump(),
    )


@app.exception_handler(LLMException)
async def llm_exception_handler(
    request: Request, 
    exc: LLMException,
):
    logger.exception(exc)

    response = ErrorResponse(
        error=ErrorDetail(
            type="LLMException",
            message=str(exc),
        )
    )

    return JSONResponse(
        status_code=502,
        content=response.model_dump(),
    )


@app.exception_handler(VectorStoreException)
async def vector_exception_handler(
    request: Request, 
    exc: VectorStoreException,
):
    logger.exception(exc)

    response = ErrorResponse(
        error=ErrorDetail(
            type="VectorStoreException",
            message=str(exc),
        )
    )

    return JSONResponse(
        status_code=503,
        content=response.model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, 
    exc: Exception,
):
    logger.exception(exc)

    response = ErrorResponse(
        error=ErrorDetail(
            type="InternalServerError",
            message="An unexpected error occurred.",
        )
    )

    return JSONResponse(
        status_code=500,
        content=response.model_dump(),
    )