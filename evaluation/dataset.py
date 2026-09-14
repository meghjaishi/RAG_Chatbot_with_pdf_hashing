from dataclasses import dataclass

@dataclass(frozen=True)
class EvaluationCase:
    """
    Ground-truth information for one evaluation question.
    """
    question: str
    reference_answer: str
    relevant_chunks: tuple[str, ...]

EVALUATION_DATASET = [
    EvaluationCase(
        question="What is reinforcement learning?",
        reference_answer=(
            "Reinforcement learning is a machine learning "
            "paradigm in which an agent learns by interacting "
            "with an environment and receiving rewards."
        ),
        relevant_chunks=(
            ## add later
        ),
    ),
    EvaluationCase(
        question="What is model-agnostic meta-learning?",
        reference_answer=(
           "Model-agnostic meta-learning is a meta-learning "
            "approach designed to enable models to adapt quickly "
            "to new tasks using only a small amount of data." 
        ),
        relevant_chunks=(
            # Add later
        ),
    ),
]

def make_chunk_id(
    file_hash: str,
    chunk: int | float,
) -> str:
    """
    Create a stable identifier for an indexed document chunk.
    """
    return f"{file_hash}:{int(chunk)}"