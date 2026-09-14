from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

GROUND_TRUTH_FILE = (
    PROJECT_ROOT
    / "evaluation"
    / "ground_truth.json"
)

CHUNKS_FILE = (
    PROJECT_ROOT
    / "evaluation"
    / "chunks.json"
)


def main() -> None:

    ground_truth = json.loads(
        GROUND_TRUTH_FILE.read_text(
            encoding="utf-8"
        )
    )

    chunks = json.loads(
        CHUNKS_FILE.read_text(
            encoding="utf-8"
        )
    )

    valid_chunk_ids = {
        chunk["chunk_id"]
        for chunk in chunks
    }

    annotations = ground_truth[
        "annotations"
    ]

    errors = []

    for question_id, annotation in annotations.items():

        if not annotation.get(
            "annotation_complete",
            False,
        ):
            errors.append(
                f"{question_id}: annotation incomplete"
            )

        expected = annotation[
            "expected_retrieval"
        ]

        relevant_chunks = annotation[
            "relevant_chunks"
        ]

        if (
            expected == "supported"
            and not relevant_chunks
        ):
            errors.append(
                f"{question_id}: supported but "
                "has no relevant chunks"
            )

        if (
            expected == "unsupported"
            and relevant_chunks
        ):
            errors.append(
                f"{question_id}: unsupported but "
                "has relevant chunks"
            )

        seen = set()

        for item in relevant_chunks:

            chunk_id = item[
                "chunk_id"
            ]

            if chunk_id not in valid_chunk_ids:
                errors.append(
                    f"{question_id}: unknown chunk "
                    f"{chunk_id}"
                )

            if chunk_id in seen:
                errors.append(
                    f"{question_id}: duplicate chunk "
                    f"{chunk_id}"
                )

            seen.add(
                chunk_id
            )

    print(
        f"Questions validated: "
        f"{len(annotations)}"
    )

    if errors:

        print(
            f"\nValidation failed with "
            f"{len(errors)} issue(s):"
        )

        for error in errors:
            print(
                f" - {error}"
            )

        raise SystemExit(1)

    print(
        "\nGround truth validation passed."
    )


if __name__ == "__main__":
    main()