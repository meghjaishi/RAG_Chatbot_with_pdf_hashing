from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RESULTS_FILE = (
    PROJECT_ROOT
    / "evaluation"
    / "retrieval_results.json"
)


def main() -> None:

    data = json.loads(
        RESULTS_FILE.read_text(
            encoding="utf-8"
        )
    )

    results = data[
        "supported_results"
    ]

    print(
        "\n"
        "PER-QUESTION RETRIEVAL ANALYSIS"
    )

    print(
        "=" * 100
    )

    for result in results:

        strict = result["strict"]
        lenient = result["lenient"]

        print(
            f"\n{result['id']}: "
            f"{result['question']}"
        )

        print(
            f"  Documents returned: "
            f"{result['documents_found']}"
        )

        print(
            f"  Strict GT chunks: "
            f"{strict['num_relevant_ground_truth']}"
        )

        print(
            f"  Lenient GT chunks: "
            f"{lenient['num_relevant_ground_truth']}"
        )

        print(
            f"  Strict P@3: "
            f"{strict['precision_at_3']:.3f}"
        )

        print(
            f"  Strict R@3: "
            f"{strict['recall_at_3']:.3f}"
        )

        print(
            f"  Strict RR: "
            f"{strict['reciprocal_rank']:.3f}"
        )

        print(
            f"  Lenient P@3: "
            f"{lenient['precision_at_3']:.3f}"
        )

        print(
            f"  Lenient R@3: "
            f"{lenient['recall_at_3']:.3f}"
        )

        print(
            f"  Lenient RR: "
            f"{lenient['reciprocal_rank']:.3f}"
        )

        if result["documents_found"] == 0:

            print(
                "  STATUS: "
                "NO DOCUMENTS RETRIEVED"
            )

        elif (
            lenient["reciprocal_rank"]
            == 0
        ):

            print(
                "  STATUS: "
                "NO GROUND-TRUTH CHUNK "
                "IN TOP-K"
            )

        elif (
            strict["reciprocal_rank"] == 0
            and lenient["reciprocal_rank"] > 0
        ):

            print(
                "  STATUS: "
                "PARTIAL EVIDENCE RETRIEVED, "
                "BUT NO STRICT MATCH"
            )

        else:

            print(
                "  STATUS: "
                "STRICT MATCH RETRIEVED"
            )


if __name__ == "__main__":
    main()