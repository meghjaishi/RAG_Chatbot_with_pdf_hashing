"""
ingest.py

Production-ready PDF ingestion pipeline for a RAG application.

Pipeline:

PDF Documents
      |
      v
SHA256 Change Detection
      |
      v
Load PDF
      |
      v
Split into Chunks
      |
      v
Generate Embeddings
      |
      v
Store in Pinecone
      |
      v
Update Manifest


Responsibilities:
- Manage Pinecone vector database
- Load and split documents
- Create embeddings
- Upload vectors
- Maintain ingestion metadata

Author: Meghnath Jaishi
"""

from __future__ import annotations

# import logging
from utils.logger import get_logger
import time
from pathlib import Path
from typing import List

from pinecone import Pinecone, ServerlessSpec

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
from config import (
    PDF_DIRECTORY,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_CLOUD,
    PINECONE_REGION,
    INDEX_DIMENSION,
    INDEX_METRIC,
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    SEPARATORS,
    BATCH_SIZE,
)

from hashing import (
    load_manifest,
    save_manifest,
    should_index,
    update_manifest,
    compute_file_hash,
    print_manifest_summary,
)

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)s | %(message)s",
# )

# logger = logging.getLogger(__name__)
logger = get_logger(__name__)

# ---------------------------------------------------------------------
# Pinecone Setup
# ---------------------------------------------------------------------
def create_index(pc: Pinecone) -> None:
    """
    Create the Pinecone index if it does not already exist.
    """

    existing_indexes = [
        index["name"]
        for index in pc.list_indexes()
    ]

    if PINECONE_INDEX_NAME in existing_indexes:
        logger.info("Using existing Pinecone index '%s'.", 
                    PINECONE_INDEX_NAME)
        return

    logger.info("Creating Pinecone index '%s'...",
                PINECONE_INDEX_NAME)

    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=INDEX_DIMENSION,
        metric=INDEX_METRIC,
        spec=ServerlessSpec(
            cloud=PINECONE_CLOUD,
            region=PINECONE_REGION,
        ),
    )
    while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        logger.info(
            "Waiting for Pinecone index..."
        )
        time.sleep(2)

    logger.info("Pinecone index is ready.")

# ---------------------------------------------------------------------
# Vector Store
# ---------------------------------------------------------------------
def create_vector_store() -> PineconeVectorStore:
    """
    Create the Pinecone vector store for document ingestion
    """

    pc=Pinecone(api_key=PINECONE_API_KEY)
    create_index(pc)
    index=pc.Index(PINECONE_INDEX_NAME)

    embeddings=OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
    )

    return PineconeVectorStore(
        index=index,
        embedding=embeddings,
    )
# -------------------------------------------------------------------
# PDF Discovery
# -------------------------------------------------------------------
def discover_pdfs() -> list[Path]:
    """
    Recursively find all PDFs.
    """

    if not PDF_DIRECTORY.exists():
        raise FileNotFoundError(
            f"Missing directory: {PDF_DIRECTORY}"
        )

    pdfs = list(
        PDF_DIRECTORY.rglob("*.pdf")
    )

    logger.info(
        "Found %d PDF files.",
        len(pdfs),
    )
    return pdfs

# ---------------------------------------------------------------------
# Load PDFs
# ---------------------------------------------------------------------
# def load_documents() -> list[Document]:
#     """
#     Load all PDFs from the Document directory.
#     """

#     if not PDF_DIRECTORY.exists():
#         raise FileNotFoundError(
#             f"Directory '{PDF_DIRECTORY}' does not exist."
#         )

#     logger.info("Loading PDF documents...")

#     loader=PyPDFDirectoryLoader(str(PDF_DIRECTORY))
#     raw_documents=loader.load()
#     logger.info("Loaded %d pages.", len(raw_documents))

#     return raw_documents

def load_pdf(pdf_path: Path,) -> list[Document]:
    """
    Load a single PDF.
    """
    loader = PyPDFLoader(
        str(pdf_path)
    )
    documents = loader.load()

    logger.info(
        "Loaded %s (%d pages)",
        pdf_path.name,
        len(documents),
    )
    return documents

# ---------------------------------------------------------------------
# Split Documents
# ---------------------------------------------------------------------
# def split_documents(
#     documents: list[Documents],
# ) -> list[Documents]:
#     """
#     Split documents into overlapping chunks.
#     """
#     logger.info("Splitting documents...")

#     splitter=RecursiveCharacterTextSplitter(
#         chunk_size=CHUNK_SIZE,
#         chunk_overlap=CHUNK_OVERLAP,
#         length_function=len,
#         separators=[
#             "\n\n",
#             "\n",
#             ". ",
#             " ",
#             "",
#         ],
#     )
    
#     chunks=splitter.split_documents(documents)

#     for i, chunk in enumerate(chunks, start=1):
#         chunk.metadata["chunk"]=i

#     logger.info("Created %d chunks.",
#                 len(chunks))
#     return chunks

def split_documents(
    documents: list[Document],
    pdf_path: Path,
    file_hash: str,
) -> list[Document]:
    """
    Split PDF pages into chunks and enrich metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=SEPARATORS,
    )


    chunks = splitter.split_documents(documents)
    for index, chunk in enumerate(chunks, start=1,):

        chunk.metadata.update(
            {
                "source_file": pdf_path.name,
                "relative_path": str(
                    pdf_path.relative_to(
                        PDF_DIRECTORY
                    )
                ),
                "chunk": index,
                "file_hash": file_hash,
            }
        )
    logger.info("%s split into %d chunks", pdf_path.name, len(chunks),)

    return chunks

# ---------------------------------------------------------------------
# UUIDs
# ---------------------------------------------------------------------
# def generate_ids(
#     documents: list[Documents]) -> list[str]:
#     """
#     Generate unique IDs for each chunk.
#     """

#     return [str(uuid4) for _ in documents]

# ---------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------
def upload_documents(
    vector_store: PineconeVectorStore,
    documents: list[Document],
) -> None:
    """
    Upload documents to Pinecone in batches.
    """
    ids = [
        f"{doc.metadata['file_hash']}_{i}"
        for i, doc in enumerate(documents)
    ]
    total = len(documents)

    for start in range(0, total, BATCH_SIZE,):
        end = start + BATCH_SIZE
        batch_docs = documents[start:end]
        batch_ids = ids[start:end]

        vector_store.add_documents(
            documents=batch_docs,
            ids=batch_ids,
        )

        logger.info("Uploaded %d/%d chunks", min(end, total), total,)

# -------------------------------------------------------------------
# Process One PDF
# -------------------------------------------------------------------
def process_pdf(
    pdf_path: Path,
    vector_store: PineconeVectorStore,
    manifest: dict,
) -> None:
    """
    Process a single PDF if required.
    """
    should_process, reason = should_index(pdf_path,manifest,)

    logger.info("%s -> %s",pdf_path.name,reason,)

    if not should_process:
        return

    start = time.time()
    file_hash = compute_file_hash(pdf_path)
    raw_documents = load_pdf(pdf_path)
    chunks = split_documents(
        raw_documents,
        pdf_path,
        file_hash,
    )
    upload_documents(
        vector_store,
        chunks,
    )
    elapsed = time.time() - start

    update_manifest(
        pdf_path,
        manifest,
        pages=len(raw_documents),
        chunks=len(chunks),
        file_size=pdf_path.stat().st_size,
        embedding_model=EMBEDDING_MODEL,
        pinecone_index=PINECONE_INDEX_NAME,
        upload_time_seconds=round(elapsed,2,),
    )

    save_manifest(manifest)
# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
# def main() -> None:
#     start_time=time.time()
#     logger.info("="*60)
#     logger.info("Starting ingestion pipeline")
#     logger.info("="*60)

#     try:
#         vector_store=create_vector_store()
#         raw_documents=load_documents()
#         chunks=split_documents(raw_documents)

#         upload_documents(
#             vector_store,
#             chunks,
#         )

#         elapsed=time.time() - start_time
#         logger.info("="*60)
#         logger.info(
#             "Ingestion completed in %.2f seconds.",
#             elapsed,
#         )
#         logger.info("="*60)
    
#     except Exception as exc:
#         logger.exception(
#             "Ingestion failed: %s",
#             exc,
#         )
#         raise
def main():
    start = time.time()
    logger.info(
        "Starting ingestion pipeline"
    )
    vector_store = create_vector_store()
    manifest = load_manifest()
    pdf_files = discover_pdfs()

    for pdf in pdf_files:
        process_pdf(pdf, vector_store, manifest,)

    print_manifest_summary(
        manifest
    )

    logger.info(
        "Completed in %.2f seconds",
        time.time() - start,
    )

# ---------------------------------------------------------------------
if __name__=="__main__":
    main()