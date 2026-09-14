from typing import Sequence
from dataclasses import dataclass

def precision_at_k(
    retrieved: Sequence[str],
    relevant: set[str],
    k: int,
) -> float:
    """
    Calculate Precision@K.
    Precision@K = relevant retrieved items in top K / K
    """

    if k <= 0:
        raise ValueError("k must be greater than zero.")

    top_k = list(retrieved[:k])

    if not top_k:
        return 0.0
    
    relevant_retrieved = sum(
        1
        for chunk_id in top_k
        if chunk_id in relevant
    )

    return relevant_retrieved / len(top_k)

def recall_at_k(
    retrieved: Sequence[str],
    relevant: set[str],
    k: int,
) -> float:
    """
    Calculate Recall@K.

    Recall@K = relevant retrieved items in top K / total relevant items
    """

    if k <= 0:
        raise ValueError("k must be greater than zero.")

    if not relevant:
        return 0.0
    
    top_k = set(retrieved[:k])

    relevant_retrieved = len(top_k & relevant)

    return relevant_retrieved / len(relevant)

def reciprocal_rank(
    retrieved: Sequence[str],
    relevant: set[str],
) -> float:
    """
    Calculate reciprocal rank for one query.
    """

    for rank, chunk_id in enumerate(retrieved, start=1):
        if chunk_id in relevant:
            return 1.0 / rank
    
    return 0.0

def mean_reciprocal_rank(
    results: Sequence[float],
) -> float:
    """
    Calculate Mean Reciprocal Rank across queries.
    """

    if not results:
        return 0.0
    
    return sum(results)/len(results)

def hit_at_k(
    retrieved: Sequence[str],
    relevant: set[str],
    k: int,
) -> float:

    if k <= 0:
        raise ValueError(
            "k must be greater than zero."
        )

    if not relevant:
        return 0.0

    top_k = set(
        retrieved[:k]
    )

    return float(
        bool(
            top_k & relevant
        )
    )


@dataclass(frozen=True)
class RetrievalEvaluationResult:
    precision_at_1: float
    precision_at_3: float
    recall_at_1: float
    recall_at_3: float
    reciprocal_rank: float

def evaluate_retrieval(
    retrieved: Sequence[str],
    relevant: set[str],
) -> RetrievalEvaluationResult:
    
    return RetrievalEvaluationResult(
        precision_at_1=precision_at_k(
            retrieved,
            relevant,
            1,
        ),
        precision_at_3=precision_at_k(
            retrieved,
            relevant,
            3,
        ),
        recall_at_1=recall_at_k(
            retrieved,
            relevant,
            1,
        ),
        recall_at_3=recall_at_k(
            retrieved,
            relevant,
            3,
        ),
        reciprocal_rank=reciprocal_rank(
            retrieved,
            relevant,
        )
    )

        