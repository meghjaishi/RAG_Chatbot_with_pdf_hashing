"""
config.py

Central configuration for the RAG ingestion pipeline
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------
PROJECT_ROOT=Path(__file__).resolve().parent
PDF_DIRECTORY=PROJECT_ROOT/"Documents"
MANIFEST_FILE=PROJECT_ROOT/"manifest.json"

# ---------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------
OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]
EMBEDDING_MODEL: str = "text-embedding-3-large"
CHAT_MODEL: str = "gpt-4o"
INDEX_DIMENSION: int = 3072
TEMPERATURE = 0.0

# ---------------------------------------------------------------------
# LLM Pricing (USD per 1M tokens)
# ---------------------------------------------------------------------
INPUT_TOKEN_COST_PER_MILLION = 1.25
OUTPUT_TOKEN_COST_PER_MILLION = 5.00

# ---------------------------------------------------------------------
# Pinecone
# ---------------------------------------------------------------------
PINECONE_API_KEY: str = os.environ["PINECONE_API_KEY"]
PINECONE_INDEX_NAME: str = os.environ["PINECONE_INDEX_NAME"]
PINECONE_CLOUD: str = "aws"
PINECONE_REGION: str = "us-east-1"
INDEX_METRIC: str = "cosine"

# ---------------------------------------------------------------------
# Text Splitting
# ---------------------------------------------------------------------
CHUNK_SIZE: int = 600
CHUNK_OVERLAP: int = 200
SEPARATORS=(
    "\n\n",
    "\n",
    ". ",
    " ",
    "",
)

# ---------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------
BATCH_SIZE: int = 100

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
LOGGING_LEVEL="INFO"

# ---------------------------------------------------------------------
# CONVERSATION HISTORY LIMIT
# ---------------------------------------------------------------------
MAX_CONVERSATION_TURNS = 5
MAX_CONVERSATION_TOKENS = 3000

# ---------------------------------------------------------------------
# LLM Context
# ---------------------------------------------------------------------
MAX_PROMPT_TOKENS = 9000
RESERVED_OUTPUT_TOKENS = 1000

# ---------------------------------------------------------------------
# JWT SETTINGS
# ---------------------------------------------------------------------
JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM=os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=int(
    os.getenv
    (
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        "30",
    )
)

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not configured.")
