"""
hashing.py

Utilities for incremental document ingestion.

Responsibilities
----------------
- Compute SHA256 hashes for files.
- Maintain the ingestion manifest.
- Detect new or modified files.
- Provide helper functions for manifest management.

This module intentionally knows nothing about:
    - Pinecone
    - LangChain
    - OpenAI
    - Chunking
    - Embeddings

Those responsibilities belong to ingest.py.
"""

from __future__ import annotations

import hashlib
import json
# import logging
from utils.logger import get_logger
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import MANIFEST_FILE, PDF_DIRECTORY

# logger=logging.getLogger(__name__)
logger = get_logger(__name__)

Manifest=dict[str, dict[str, Any]]

# ---------------------------------------------------------------------
# Path Helpers
# ---------------------------------------------------------------------
def manifest_key(file_path: Path) -> str:
    """
    Convert a PDF path into a manifest key.

    Example
    -------
    Documents/HR/handbook.pdf

    becomes

    HR/handbook.pdf
    """

    return file_path.relative_to(PDF_DIRECTORY).as_posix()

# ---------------------------------------------------------------------
# SHA256
# ---------------------------------------------------------------------
def compute_file_hash(file_path: Path) -> str:
    """
    Compute the SHA256 hash of a file.
    """

    sha=hashlib.sha256()

    with file_path.open("rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()

# ---------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------
def load_manifest() -> Manifest:
    """
    Load the manifest from disk.

    Returns
    -------
    dict

    If the manifest does not exist,
    an empty one is returned.
    """

    if not MANIFEST_FILE.exists():
        logger.info(
            "Manifest not found. Creating a new one."
        )

        return {}
    try:
        with MANIFEST_FILE.open("r", encoding="utf-8",) as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.warning(
            "Manifest is corrupt. Starting fresh."
        )

        return {}

def save_manifest(manifest: Manifest,) -> None:
    """
    Persist the manifest.
    """

    MANIFEST_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with MANIFEST_FILE.open("w", encoding="utf-8",) as f:
        json.dump(manifest, f, indent=4, sort_keys=True,)

# ---------------------------------------------------------------------
# Manifest Queries
# ---------------------------------------------------------------------
def get_manifest_record(
    file_path: Path,
    manifest: Manifest,
) -> dict[str, Any] | None:
    """
    Return the manifest record for a file.
    """

    return manifest.get(
        manifest_key(file_path)
    )

def should_index(
    file_path: Path,
    manifest: Manifest,
) -> tuple[bool, str]:
    """
    Determine whether a PDF should be ingested.

    Returns
    -------
    (should_index, reason)
    """

    current_hash = compute_file_hash(file_path)

    record = get_manifest_record(file_path, manifest,)

    if record is None:

        return (True, "New document",)

    if record["hash"] != current_hash:

        return (True, "Document modified",)

    return (False, "Already indexed",)

# ---------------------------------------------------------------------
# Manifest Updates
# ---------------------------------------------------------------------
def update_manifest(
    file_path: Path,
    manifest: Manifest,
    **metadata: Any,
) -> None:
    """
    Update the manifest after a successful ingestion.

    Parameters
    ----------
    file_path
        PDF that was indexed.

    manifest
        Current manifest.

    **metadata
        Additional information supplied by ingest.py.

    Examples
    --------
    update_manifest(
        pdf,
        manifest,
        pages=42,
        chunks=173,
        upload_time=3.52,
        embedding_model="text-embedding-3-large",
    )
    """

    manifest[
        manifest_key(file_path)
    ] = {

        "hash": compute_file_hash(file_path),

        "indexed_at": datetime.now(
            timezone.utc
        ).isoformat(),

        **metadata,
    }

# ---------------------------------------------------------------------
# Manifest Summary
# ---------------------------------------------------------------------
def print_manifest_summary(
    manifest: Manifest,
) -> None:
    """
    Log a readable summary.
    """

    logger.info("-" * 60)

    logger.info(
        "Indexed PDFs: %d",
        len(manifest),
    )

    for path, info in manifest.items():

        logger.info(path)

        logger.info(
            "    Hash: %s...",
            info["hash"][:12],
        )

        logger.info(
            "    Indexed: %s",
            info["indexed_at"],
        )

    logger.info("-" * 60)