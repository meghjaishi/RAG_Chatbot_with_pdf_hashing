from __future__ import annotations

import json
from pathlib import Path

from config import PDF_DIRECTORY

from ingestion import (
    load_pdf,
    split_documents,
)

from hashing import compute_file_hash

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FILE = (
    PROJECT_ROOT
    / "evaluation"
    / "chunks.json"
)

def build_chunk_id(
    file_hash: str,
    chunk_number: int,
) -> str:
    """
    Stable evaluation identifier.

    Uses metadata chunk numbering,
    which starts at 1.
    """

    return (
        f"{file_hash}:{chunk_number}"
    )

def export_chunks() -> None:
    """
    Reproduce the production chunking process
    without uploading anything to Pinecone.
    """

    records=[]

    pdf_paths = sorted(PDF_DIRECTORY.glob("*.pdf"))

    for pdf_path in pdf_paths:
        file_hash = compute_file_hash(pdf_path)
        raw_documents = load_pdf(pdf_path)
        chunks = split_documents(raw_documents, pdf_path, file_hash)

        for chunk in chunks:
            metadata = chunk.metadata
            chunk_number = int(metadata["chunk"])

            records.append(
                {
                    "chunk_id": build_chunk_id(metadata["file_hash"], chunk_number),
                    "source_file": metadata["source_file"],
                    "relative_path": metadata.get("relative_path", ""),
                    "file_hash": metadata["file_hash"],
                    "page": metadata.get("page"),
                    "chunk": chunk_number,
                    "content": chunk.page_content,
                }
            )
    
    OUTPUT_FILE.write_text(
        json.dumps(
            records,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf_8",
    )
    print(f"Exported {len(records)} chunks")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    export_chunks()



