from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

EVALUATION_DIR=(PROJECT_ROOT/ "evaluation")
QUESTIONS_FILE=(EVALUATION_DIR/ "questions.json")
CHUNKS_FILE=(EVALUATION_DIR/ "chunks.json")
GROUND_TRUTH_FILE=(EVALUATION_DIR/ "ground_truth.json")

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------
DEFAULT_TOP_K=12
STOP_WORDS={
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "why",
    "with",
}
# ---------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------
def load_json(path: Path) -> Any:

    return json.loads(path.read_text(encoding="utf-8"))

def load_questions() -> list[dict]:
    data = load_json(QUESTIONS_FILE)

    return data["questions"]

def load_chunks() -> list[dict]:

    return load_json(CHUNKS_FILE)

def load_ground_truth() -> dict:
    if not GROUND_TRUTH_FILE.exists():
        return {
            "dataset_version": "1.0",
            "annotations": {},
        }
    
    return load_json(
        GROUND_TRUTH_FILE
    )

def save_ground_truth(ground_truth: dict) -> None:
    
    GROUND_TRUTH_FILE.write_text(
        json.dumps(
            ground_truth,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

# ---------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------
def tokenize(text: str) -> list[str]:
    
    tokens = re.findall(r"[a-zA-Z0-9_-]+", text.casefold())

    return [
        token for token in tokens if (
            len(token) > 2 and token not in STOP_WORDS
            )
        ]

# ---------------------------------------------------------------------
# Candidate scoring
# ---------------------------------------------------------------------
def build_search_terms(question: dict) -> list[str]:
    terms = []

    #Full explicit annotation keywords
    for keyword in question.get("keywords",[]):
        keyword=keyword.casefold().strip()

        if keyword:
            terms.append(keyword)

    # Add useful words from question
    terms.extend(tokenize(question["question"]))

    # Preserve order while removing duplicates
    return list(dict.fromkeys(terms))

def score_chunk(chunk: dict, terms: list[str]) -> float:
    content = chunk["content"].casefold()
    score = 0.0

    for term in terms:
        # Multi-word phrases get larger weight
        if " " in term:
            occurences=content.count(term)
            score += (occurences * 5.0)
        else:
            occurences = len(
                re.findall(rf"\b{re.escape(term)}\b", content)
            )
            score += float(occurences)
    return score

def get_candidates(
    question: dict,
    chunks: list[dict],
    top_k: int,
) -> list[dict]:

    source_hint = question.get("source_hint")
    terms = build_search_terms(question)

    scored=[]

    for chunk in chunks:
        # When a question has an independently known
        # source document, restrict annotation candidate
        # discovery to that pdf.
        #
        # Cross-document questions have source_hint=None,
        # therefore all PDFs remain eligible.
        
        if (source_hint and chunk["source_file"] != source_hint):
            continue

        score = score_chunk(chunk, terms)
        if score <= 0:
            continue

        scored.append(
            {
                "score": score,
                "chunk": chunk,
            }

        )
    scored.sort(key=lambda item: item["score"], reverse=True)

    return scored[:top_k]

def find_chunk_by_id(
    chunks: list[dict],
    chunk_id: str,
) -> dict | None:
    """
    Find a chunk in the exported corpus
    using its stable chunk ID.
    """

    for chunk in chunks:

        if (
            chunk["chunk_id"]
            == chunk_id
        ):
            return chunk

    return None
# ---------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------
def display_question(question: dict) -> None:
    print("\n" + "="*100)

    print(f"QUESTION ID: {question['id']}")
    print(f"CATEGORY: {question['category']}")
    print(f"\nREFERENCE ANSWER:\n {question['reference_answer']}")
    
    source_hint = question.get("source_hint")
    if source_hint:
        print(f"\nSOURCE_HINT: {source_hint}")
    
    print("="*100)

def display_candidate(rank: int, candidate: dict) -> None:
    chunk = candidate["chunk"]
    score = candidate["score"]
    print("\n" + "-"*100)

    print(f"CANDIDATE #{rank}")
    print(f"Annotation search score: {score:.2f}")
    print(f"Chunk ID: {chunk['chunk_id']}")
    print(f"Source: {chunk['source_file']}")
    print(f"Page metadata: {chunk.get('page')}")
    print(f"Chunk: {chunk['chunk']}")
    print("-"*100)
    print(chunk["content"])
    print("-"*100)

# ---------------------------------------------------------------------
# Annotation helpers
# ---------------------------------------------------------------------
def build_annotation_record(question: dict) -> dict:

    return {
        "id": question["id"],
        "question": question["question"],
        "reference_answer": question["reference_answer"],
        "category": question["category"],
        "expected_retrieval": question["expected_retrieval"],
        "relevant_chunks": [],
        "annotation_complete": False,
    }

def make_chunk_annotation(chunk: dict, relevance: str) -> dict:

    return {
        "chunk_id": chunk["chunk_id"],
        "source_file": chunk["source_file"],
        "relative_path": chunk.get("relative_path", ""),
        "file_hash": chunk["file_hash"],
        "page": chunk.get("page"),
        "chunk": chunk["chunk"],
        "relevance": relevance,
    }

def annotation_exists(annotation: dict, chunk_id: str) -> bool:
    return any(
        item["chunk_id"] == chunk_id
        for item in annotation["relevant_chunks"]
        )

# ---------------------------------------------------------------------
# Question annotation
# ---------------------------------------------------------------------
def annotate_question(
    question: dict,
    chunks: list[dict],
    ground_truth: dict,
    top_k: int
) -> bool:
    """
    Annotate one question.

    Returns False when user chooses to quit
    the complete annotation session.
    """

    question_id = question["id"]
    annotations = ground_truth["annotations"]

    # -------------------------------------------------------------
    # Unsupported questions
    # -------------------------------------------------------------
    if (question["expected_retrieval"] == "unsupported"):
        annotations[question_id] = {
            "id": question_id,
            "question": question[
                "question"
            ],
            "reference_answer": None,
            "category": question[
                "category"
            ],
            "expected_retrieval":
                "unsupported",
            "relevant_chunks": [],
            "annotation_complete": True,
        }

        save_ground_truth(ground_truth)

        print(
            f"\n{question_id}: "
            "unsupported question — "
            "saved with zero relevant chunks."
        )

        return True
    # -------------------------------------------------------------
    # Existing/new annotation
    # -------------------------------------------------------------
    annotation = annotations.get(question_id)

    if annotation is None:

        annotation = (
            build_annotation_record(
                question
            )
        )

        annotations[
            question_id
        ] = annotation

    display_question(
        question
    )

    candidates = get_candidates(
        question,
        chunks,
        top_k,
    )

    if not candidates:

        print(
            "\nNo lexical candidates found."
        )

        print(
            "You may need to revise the "
            "keywords in questions.json."
        )

        return True
    # -------------------------------------------------------------
    # Review candidates
    # -------------------------------------------------------------
    for rank, candidate in enumerate(candidates, start=1):

        chunk = candidate["chunk"]

        if annotation_exists(annotation, chunk["chunk_id"]):
            continue

        display_candidate(rank, candidate)

        print("\nLabel:")
        print("  r = relevant")
        print("  p = partially relevant")
        print("  i = irrelevant")
        print("  s = skip candidate")
        print("  d = finish this question")
        print("  q = save and quit")

        choice = input("\nSelection: ").strip().casefold()

        if choice == "r":

            annotation[
                "relevant_chunks"
            ].append(
                make_chunk_annotation(
                    chunk,
                    "relevant",
                )
            )

        elif choice == "p":

            annotation[
                "relevant_chunks"
            ].append(
                make_chunk_annotation(
                    chunk,
                    "partially_relevant",
                )
            )

        elif choice in {"i", "s",}:
            pass

        elif choice == "d":
            break

        elif choice == "q":

            save_ground_truth(ground_truth)

            return False

        else:

            print("Unknown option. Candidate skipped.")

        # Save after every decision.
        save_ground_truth(ground_truth)

    # -------------------------------------------------------------
    # Complete question
    # -------------------------------------------------------------
    print("\nSelected relevant chunks:")

    for item in annotation["relevant_chunks"]:

        print(
            f"  {item['source_file']} | chunk={item['chunk']} | relevance={item['relevance']}"
        )

    complete = input(
        "\nMark this question "
        "annotation complete? [y/n]: "
    ).strip().casefold()

    annotation["annotation_complete"] = (
        complete == "y"
    )

    save_ground_truth(
        ground_truth
    )

    return True
# ---------------------------------------------------------------------
# REVIEW
# ---------------------------------------------------------------------
def review_question(
    question: dict,
    chunks: list[dict],
    ground_truth: dict,
) -> bool:
    """
    Review existing annotations for one question.

    Returns False if the user chooses to quit
    the complete review session.
    """

    question_id = question["id"]

    annotations = ground_truth[
        "annotations"
    ]

    annotation = annotations.get(
        question_id
    )

    if annotation is None:

        print(
            f"\nNo annotation exists for "
            f"{question_id}."
        )

        return True

    # Unsupported questions do not
    # have relevant chunks to review.
    if (
        annotation["expected_retrieval"]
        == "unsupported"
    ):

        print(
            f"\n{question_id} is marked "
            "as unsupported."
        )

        return True

    display_question(
        question
    )

    relevant_chunks = annotation[
        "relevant_chunks"
    ]

    if not relevant_chunks:

        print(
            "\nNo relevant chunks are "
            "currently annotated."
        )

        return True

    # Work on a copy so removing items
    # while iterating is safe.
    current_annotations = list(
        relevant_chunks
    )

    for index, chunk_annotation in enumerate(
        current_annotations,
        start=1,
    ):

        chunk_id = chunk_annotation[
            "chunk_id"
        ]

        chunk = find_chunk_by_id(
            chunks,
            chunk_id,
        )

        if chunk is None:

            print(
                f"\nWARNING: chunk not found: "
                f"{chunk_id}"
            )

            continue

        print(
            "\n"
            + "=" * 100
        )

        print(
            f"ANNOTATED CHUNK "
            f"#{index}"
        )

        print(
            f"Current relevance: "
            f"{chunk_annotation['relevance']}"
        )

        display_candidate(
            index,
            {
                "score": 0.0,
                "chunk": chunk,
            },
        )

        print(
            "\nReview action:"
        )

        print(
            "  r = mark relevant"
        )

        print(
            "  p = mark partially relevant"
        )

        print(
            "  x = remove from ground truth"
        )

        print(
            "  k = keep current label"
        )

        print(
            "  q = save and quit"
        )

        choice = input(
            "\nSelection: "
        ).strip().casefold()

        if choice == "r":

            chunk_annotation[
                "relevance"
            ] = "relevant"

        elif choice == "p":

            chunk_annotation[
                "relevance"
            ] = "partially_relevant"

        elif choice == "x":

            annotation[
                "relevant_chunks"
            ] = [
                item
                for item
                in annotation[
                    "relevant_chunks"
                ]
                if (
                    item["chunk_id"]
                    != chunk_id
                )
            ]

        elif choice == "k":

            pass

        elif choice == "q":

            save_ground_truth(
                ground_truth
            )

            return False

        else:

            print(
                "Unknown option. "
                "Keeping current label."
            )

        save_ground_truth(
            ground_truth
        )

    # -------------------------------------------------------------
    # Final review summary
    # -------------------------------------------------------------

    print(
        "\n"
        + "=" * 100
    )

    print(
        f"FINAL ANNOTATIONS FOR "
        f"{question_id}"
    )

    for item in annotation[
        "relevant_chunks"
    ]:

        print(
            f"{item['source_file']} "
            f"| page={item['page']} "
            f"| chunk={item['chunk']} "
            f"| {item['relevance']}"
        )

    complete = input(
        "\nKeep annotation marked "
        "complete? [y/n]: "
    ).strip().casefold()

    annotation[
        "annotation_complete"
    ] = (
        complete == "y"
    )

    save_ground_truth(
        ground_truth
    )

    return True

# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Human ground-truth annotation "
            "for RAG evaluation."
        )
    )

    parser.add_argument(
        "question_id",
        nargs="?",
        help=(
            "Optional question ID such "
            "as q04. If omitted, all "
            "questions are processed."
        ),
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help=(
            "Number of lexical candidate "
            "chunks to display."
        ),
    )

    parser.add_argument(
        "--review",
        action="store_true",
        help=(
            "Review and modify existing "
            "ground-truth annotations."
        ),
    )

    return parser.parse_args()


def main() -> None:

    args = parse_args()
    questions = load_questions()
    chunks = load_chunks()
    ground_truth = (load_ground_truth())

    if args.question_id:

        questions = [
            question
            for question in questions
            if question["id"]
            == args.question_id
        ]

        if not questions:
            raise ValueError(
                "Unknown question ID: "
                f"{args.question_id}"
            )

    for question in questions:
        if args.review:
            should_continue = (
                review_question(
                    question=question,
                    chunks=chunks,
                    ground_truth=ground_truth,
                )
            )

        else:
            should_continue = (
                annotate_question(
                    question=question,
                    chunks=chunks,
                    ground_truth=ground_truth,
                    top_k=args.top_k,
                )
            )

        if not should_continue:
            break

    save_ground_truth(
        ground_truth
    )

    print("\nGround truth saved to:")

    print(GROUND_TRUTH_FILE)


if __name__ == "__main__":
    main()




