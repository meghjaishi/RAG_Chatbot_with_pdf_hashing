from __future__ import annotations
from openai import AsyncOpenAI

from ragas.llms import llm_factory
from ragas.embeddings.base import embedding_factory

from ragas.metrics.collections import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
)

from config import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Evaluation model.
#
# Keep this separate from the model being evaluated.
evaluator_llm = llm_factory("gpt-4o-mini", client=client)

evaluator_embeddings = embedding_factory("openai", model=EMBEDDING_MODEL, client=client)

faithfulness_metric = Faithfulness(llm=evaluator_llm)
answer_relevancy_metric = AnswerRelevancy(
    llm=evaluator_llm,
    embeddings=evaluator_embeddings,
)
context_precision_metric = ContextPrecision(llm=evaluator_llm)
context_recall_metric = ContextRecall(llm=evaluator_llm)