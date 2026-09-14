from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from uuid import uuid4

from api.request_context import request_id
from rag import RAGEngine

from evaluation.retrieval_metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    hit_at_k,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

GROUND_TRUTH_FILE = (
    PROJECT_ROOT
    / "evaluation"
    / "ground_truth.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "evaluation"
    / "retrieval_results.json"
)


def make_chunk_id(
    document,
) -> str:

    metadata = document.metadata

    return (
        f"{metadata['file_hash']}:"
        f"{int(metadata['chunk'])}"
    )


def get_relevant_chunk_ids(
    annotation: dict,
    include_partial: bool,
) -> set[str]:

    allowed = {
        "relevant",
    }

    if include_partial:
        allowed.add(
            "partially_relevant"
        )

    return {
        item["chunk_id"]
        for item
        in annotation["relevant_chunks"]
        if item["relevance"] in allowed
    }


def evaluate_supported_question(
    engine: RAGEngine(k=10),
    annotation: dict,
) -> dict:

    rid = str(
        uuid4()
    )

    token = request_id.set(
        rid
    )

    try:
        documents, retrieval_time = (
            engine.retrieve(
                annotation["question"]
            )
        )
    finally:
        request_id.reset(
            token
        )

    retrieved_ids = [
        make_chunk_id(doc)
        for doc in documents
    ]

    strict_relevant = (
        get_relevant_chunk_ids(
            annotation,
            include_partial=False,
        )
    )

    lenient_relevant = (
        get_relevant_chunk_ids(
            annotation,
            include_partial=True,
        )
    )

    return {
        "id": annotation["id"],
        "question": annotation[
            "question"
        ],
        "retrieval_time": retrieval_time,
        "documents_found": len(
            retrieved_ids
        ),
        "retrieved_chunk_ids":
            retrieved_ids,

        "strict": {
            "num_relevant_ground_truth":
                len(strict_relevant),

            "precision_at_1":
                precision_at_k(
                    retrieved_ids,
                    strict_relevant,
                    1,
                ),

            "precision_at_3":
                precision_at_k(
                    retrieved_ids,
                    strict_relevant,
                    3,
                ),

            "precision_at_5":
                precision_at_k(
                    retrieved_ids,
                    strict_relevant,
                    5,
                ),

            "precision_at_10":
                precision_at_k(
                    retrieved_ids,
                    strict_relevant,
                    10,
                ),

            "recall_at_1":
                recall_at_k(
                    retrieved_ids,
                    strict_relevant,
                    1,
                ),

            "recall_at_3":
                recall_at_k(
                    retrieved_ids,
                    strict_relevant,
                    3,
                ),

            "recall_at_5":
                recall_at_k(
                    retrieved_ids,
                    strict_relevant,
                    5,
                ),

            "recall_at_10":
                recall_at_k(
                    retrieved_ids,
                    strict_relevant,
                    10,
                ),

            "reciprocal_rank":
                reciprocal_rank(
                    retrieved_ids,
                    strict_relevant,
                ),

            "hit_at_1": hit_at_k(
                retrieved_ids,
                strict_relevant,
                1,
            ),

            "hit_at_3": hit_at_k(
                retrieved_ids,
                strict_relevant,
                3,
            ),

            "hit_at_5": hit_at_k(
                retrieved_ids,
                strict_relevant,
                5,
            ),

            "hit_at_10": hit_at_k(
                retrieved_ids,
                strict_relevant,
                10,
            ),
        },

        "lenient": {
            "num_relevant_ground_truth":
                len(lenient_relevant),

            "precision_at_1":
                precision_at_k(
                    retrieved_ids,
                    lenient_relevant,
                    1,
                ),

            "precision_at_3":
                precision_at_k(
                    retrieved_ids,
                    lenient_relevant,
                    3,
                ),
            
            "precision_at_5":
                precision_at_k(
                    retrieved_ids,
                    lenient_relevant,
                    5,
                ),

            "precision_at_10":
                precision_at_k(
                    retrieved_ids,
                    lenient_relevant,
                    10,
                ),

            "recall_at_1":
                recall_at_k(
                    retrieved_ids,
                    lenient_relevant,
                    1,
                ),

            "recall_at_3":
                recall_at_k(
                    retrieved_ids,
                    lenient_relevant,
                    3,
                ),
            
            "recall_at_5":
                recall_at_k(
                    retrieved_ids,
                    lenient_relevant,
                    5,
                ),

            "recall_at_10":
                recall_at_k(
                    retrieved_ids,
                    lenient_relevant,
                    10,
                ),

            "reciprocal_rank":
                reciprocal_rank(
                    retrieved_ids,
                    lenient_relevant,
                ),

            "hit_at_1": hit_at_k(
                retrieved_ids,
                lenient_relevant,
                1,
            ),

            "hit_at_3": hit_at_k(
                retrieved_ids,
                lenient_relevant,
                3,
            ),

            "hit_at_5": hit_at_k(
                retrieved_ids,
                lenient_relevant,
                5,
            ),

            "hit_at_10": hit_at_k(
                retrieved_ids,
                lenient_relevant,
                10,
            ),
        },
    }


def evaluate_unsupported_question(
    engine: RAGEngine,
    annotation: dict,
) -> dict:

    rid = str(
        uuid4()
    )

    token = request_id.set(
        rid
    )

    try:
        documents, retrieval_time = (
            engine.retrieve(
                annotation["question"]
            )
        )
    finally:
        request_id.reset(
            token
        )

    return {
        "id": annotation["id"],
        "question": annotation[
            "question"
        ],
        "retrieval_time": retrieval_time,
        "documents_found": len(
            documents
        ),
        "correct_abstention": (
            len(documents) == 0
        ),
    }


def aggregate_supported(
    results: list[dict],
    mode: str,
) -> dict:

    if not results:
        return {}

    return {
        "precision_at_1": mean(
            item[mode][
                "precision_at_1"
            ]
            for item in results
        ),
        "precision_at_3": mean(
            item[mode][
                "precision_at_3"
            ]
            for item in results
        ),
        "precision_at_5": mean(
            item[mode][
                "precision_at_5"
            ]
            for item in results
        ),
        "precision_at_10": mean(
            item[mode][
                "precision_at_10"
            ]
            for item in results
        ),
        "recall_at_1": mean(
            item[mode][
                "recall_at_1"
            ]
            for item in results
        ),
        "recall_at_3": mean(
            item[mode][
                "recall_at_3"
            ]
            for item in results
        ),
        "recall_at_5": mean(
            item[mode][
                "recall_at_5"
            ]
            for item in results
        ),
        "recall_at_10": mean(
            item[mode][
                "recall_at_10"
            ]
            for item in results
        ),
        "hit_at_1": mean(
            item[mode][
                "hit_at_1"
            ]
            for item in results
        ),
        "hit_at_3": mean(
            item[mode][
                "hit_at_3"
            ]
            for item in results
        ),
        "hit_at_5": mean(
            item[mode][
                "hit_at_5"
            ]
            for item in results
        ),
        "hit_at_10": mean(
            item[mode][
                "hit_at_10"
            ]
            for item in results
        ),
        "mrr": mean(
            item[mode][
                "reciprocal_rank"
            ]
            for item in results
        ),
    }


def main() -> None:

    ground_truth = json.loads(
        GROUND_TRUTH_FILE.read_text(
            encoding="utf-8"
        )
    )

    engine = RAGEngine()

    supported_results = []
    unsupported_results = []

    annotations = ground_truth[
        "annotations"
    ]

    for question_id in sorted(
        annotations
    ):

        annotation = annotations[
            question_id
        ]

        print(
            f"Evaluating "
            f"{question_id}: "
            f"{annotation['question']}"
        )

        if (
            annotation[
                "expected_retrieval"
            ]
            == "unsupported"
        ):

            result = (
                evaluate_unsupported_question(
                    engine,
                    annotation,
                )
            )

            unsupported_results.append(
                result
            )

        else:

            result = (
                evaluate_supported_question(
                    engine,
                    annotation,
                )
            )

            supported_results.append(
                result
            )

    strict_summary = (
        aggregate_supported(
            supported_results,
            "strict",
        )
    )

    lenient_summary = (
        aggregate_supported(
            supported_results,
            "lenient",
        )
    )

    if unsupported_results:

        abstention_accuracy = mean(
            item["correct_abstention"]
            for item
            in unsupported_results
        )

    else:

        abstention_accuracy = 0.0

    output = {
        "supported_questions": len(
            supported_results
        ),
        "unsupported_questions": len(
            unsupported_results
        ),
        "strict_summary":
            strict_summary,
        "lenient_summary":
            lenient_summary,
        "abstention_accuracy":
            abstention_accuracy,
        "supported_results":
            supported_results,
        "unsupported_results":
            unsupported_results,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STRICT RETRIEVAL METRICS"
    )

    for key, value in (
        strict_summary.items()
    ):

        print(
            f"{key}: "
            f"{value:.4f}"
        )

    print(
        "\nLENIENT RETRIEVAL METRICS"
    )

    for key, value in (
        lenient_summary.items()
    ):

        print(
            f"{key}: "
            f"{value:.4f}"
        )

    print(
        "\nABSTENTION ACCURACY: "
        f"{abstention_accuracy:.4f}"
    )

    print(
        "\nDetailed results saved to:"
    )

    print(
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()