# ============================================================
# evaluator.py
#
# PURPOSE:
#   Runs evaluation questions against either:
#     - Semantic Search (Pinecone alone)
#     - Hybrid Search   (Semantic + BM25 + RRF)
#
#   Calculates Hit Rate@3, Recall@3, and MRR.
# ============================================================

import json
import sys
from rag.config import EVALUATION_DATASET_PATH, BASELINE_RESULTS_PATH, HYBRID_RESULTS_PATH
from rag.infra.embedder import embed_user_query
from rag.infra.vectorstore import search_in_pinecone
from rag.core.retrieval.hybrid_retriever import hybrid_search

DATASET_PATH = EVALUATION_DATASET_PATH


def calculate_hit_rate(relevant_chunks, retrieved_ids):
    for chunk_id in relevant_chunks:
        if chunk_id in retrieved_ids:
            return 1
    return 0


def calculate_recall(relevant_chunks, retrieved_ids):
    found = sum(1 for c in relevant_chunks if c in retrieved_ids)
    return found / len(relevant_chunks)


def calculate_reciprocal_rank(relevant_chunks, retrieved_ids):
    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant_chunks:
            return 1.0 / rank
    return 0.0


def run_evaluation(mode="semantic", top_k=3):
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    retriever_label = "Hybrid Search (Semantic + BM25 + RRF)" if mode == "hybrid" else "Semantic Search"

    print(f"\n{'=' * 60}")
    print(f"EVALUATION -- {retriever_label}")
    print(f"Top K = {top_k}    |    Questions = {len(dataset)}")
    print(f"{'=' * 60}\n")

    hit_rates = []
    recalls = []
    recip_ranks = []
    per_question = []

    for i, item in enumerate(dataset, start=1):
        question = item["question"]
        relevant_chunks = item["relevant_chunks"]

        if mode == "hybrid":
            results = hybrid_search(question, top_k=top_k)
        else:
            query_vector = embed_user_query(question)
            results = search_in_pinecone(query_vector, top_k=top_k)

        retrieved_ids = [r["id"] for r in results]

        hit = calculate_hit_rate(relevant_chunks, retrieved_ids)
        rec = calculate_recall(relevant_chunks, retrieved_ids)
        rr = calculate_reciprocal_rank(relevant_chunks, retrieved_ids)

        hit_rates.append(hit)
        recalls.append(rec)
        recip_ranks.append(rr)

        status = "HIT  [+]" if hit else "MISS [-]"
        print(f"Q{i:02d} {status}")
        print(f"     Question       : {question}")
        print(f"     Relevant chunks: {relevant_chunks}")
        print(f"     Retrieved      : {retrieved_ids}")
        print(f"     Hit={hit}  Recall={rec:.2f}  RR={rr:.2f}\n")

        per_question.append({
            "question": question,
            "relevant_chunks": relevant_chunks,
            "retrieved_ids": retrieved_ids,
            "hit": hit,
            "recall": round(rec, 4),
            "reciprocal_rank": round(rr, 4)
        })

    final_hit_rate = sum(hit_rates) / len(hit_rates)
    final_recall = sum(recalls) / len(recalls)
    final_mrr = sum(recip_ranks) / len(recip_ranks)

    print(f"{'=' * 60}")
    print(f"RESULTS -- {retriever_label}")
    print(f"{'=' * 60}")
    print(f"  Hit Rate@{top_k} : {final_hit_rate * 100:.1f}%")
    print(f"  Recall@{top_k}   : {final_recall:.4f}")
    print(f"  MRR        : {final_mrr:.4f}")
    print(f"{'=' * 60}\n")

    return {
        "retriever": retriever_label,
        "top_k": top_k,
        "num_questions": len(dataset),
        "hit_rate": round(final_hit_rate, 4),
        "recall": round(final_recall, 4),
        "mrr": round(final_mrr, 4),
        "per_question": per_question
    }


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "hybrid"
    results = run_evaluation(mode=mode)

    output_path = HYBRID_RESULTS_PATH if mode == "hybrid" else BASELINE_RESULTS_PATH
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print(f"Results saved to: {output_path}\n")
