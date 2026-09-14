from __future__ import annotations

import asyncio
import json
from pathlib import Path
from statistics import mean
from uuid import uuid4
from api.request_context import request_id
from rag import RAGEngine

from evaluation.ragas_metrics import (
    faithfulness_metric,
    answer_relevancy_metric,
    context_precision_metric,
    context_recall_metric,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GROUND_TRUTH_FILE = PROJECT_ROOT/ "evaluation" / "ground_truth.json"
OUTPUT_FILE = PROJECT_ROOT/ "evaluation" / "ragas_results.json"

async def evaluate_question(
    engine: RAGEngine,
    annotation: dict,
) -> dict:
    rid = str(uuid4())
    token = request_id.set(rid)

    try: 
        response = engine.ask(annotation["question"])
    finally:
        request_id.reset(token)
    
    retrieved_contexts = [document.content for document in response.documents]
    user_input = annotation["question"]
    generated_response = response.answer
    reference = annotation["reference_answer"]

    # ---------------------------------------------------------
    # Faithfulness
    # ---------------------------------------------------------
    # faithfulness_result = (
    #     await faithfulness_metric.ascore(
    #         user_input=user_input,
    #         response=generated_response,
    #         retrieved_contexts=retrieved_contexts,
    #     )
    # )
    # ---------------------------------------------------------
    # Answer relevancy
    # ---------------------------------------------------------
    # answer_relevancy_result=(
    #     await answer_relevancy_metric.ascore(
    #         user_input=user_input,
    #         response=generated_response,
    #     )
    # )
    # ---------------------------------------------------------
    # Context precision
    # ---------------------------------------------------------
    # context_precision_result=(
    #     await context_precision_metric.ascore(
    #         user_input=user_input,
    #         reference=reference,
    #         retrieved_contexts=retrieved_contexts,
    #     )
    # )
    # ---------------------------------------------------------
    # Context recall
    # ---------------------------------------------------------
    # context_recall_result=(
    #     await context_recall_metric.ascore(
    #         user_input=user_input,
    #         reference=reference,
    #         retrieved_contexts=retrieved_contexts,
    #     )
    # )

    (
        faithfulness_result,
        answer_relevancy_result,
        context_precision_result,
        context_recall_result,
    ) = await asyncio.gather(
        faithfulness_metric.ascore(
            user_input=user_input,
            response=generated_response,
            retrieved_contexts=retrieved_contexts,
        ),
        answer_relevancy_metric.ascore(
            user_input=user_input,
            response=generated_response,
        ),
        context_precision_metric.ascore(
            user_input=user_input,
            reference=reference,
            retrieved_contexts=retrieved_contexts,
        ),
        context_recall_metric.ascore(
            user_input=user_input,
            reference=reference,
            retrieved_contexts=retrieved_contexts,
        ),
    )

    return {
        "id": annotation["id"],
        "question": user_input,
        "answer": generated_response,
        "reference_answer": reference,
        "documents_found": len(retrieved_contexts),
        "faithfulness": float(faithfulness_result.value),
        "answer_relevancy": float(answer_relevancy_result.value),
        "context_precision": float(context_precision_result.value),
        "context_recall": float(context_recall_result.value),
    }

async def main() -> None:
    ground_truth = json.loads(
        GROUND_TRUTH_FILE.read_text(encoding="utf-8")
    )

    annotations = ground_truth["annotations"]
    annotations = {
            "q02": annotations["q02"]
        }
    engine = RAGEngine()
    results = []
    
    for question_id in sorted(annotations):
        annotation=annotations[question_id]
        if annotation["expected_retrieval"] != "supported":
            continue
        print(f"Evaluating {question_id}: {annotation['question']}")
        result = await evaluate_question(engine, annotation)
        print(
            f"  faithfulness="
            f"{result['faithfulness']:.4f} | "
            f"answer_relevancy="
            f"{result['answer_relevancy']:.4f} | "
            f"context_precision="
            f"{result['context_precision']:.4f} | "
            f"context_recall="
            f"{result['context_recall']:.4f}"
        )
        results.append(result)
    
    summary = {
        "faithfulness": mean(result["faithfulness"] for result in results),
        "answer_relevancy": mean(result["answer_relevancy"] for result in results),
        "context_precision": mean(result["context_precision"]for result in results),
        "context_recall": mean(result["context_recall"]for result in results),
    }

    output = {
        "num_questions": len(results),
        "summary": summary,
        "results": results,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("\n" + "="*100)
    print("RAGAS EVALUATION")

    for name, value in summary.items():
        print(f"{name}: {value:.4f}")
    
    print("\nResults saved to:")
    print(OUTPUT_FILE)

if __name__ == "__main__":
    asyncio.run(main())
