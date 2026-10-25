# ============================================================
# evaluator.py
#
# PURPOSE:
#   Runs evaluation questions against either:
#     - Semantic Search (ChromaDB alone)
#     - Hybrid Search   (Semantic + BM25 + RRF)
#
#   Calculates Hit Rate@3, Recall@3, and MRR.
# ============================================================

import json
import sys
from rag.config import EVALUATION_DATASET_PATH, BASELINE_RESULTS_PATH, HYBRID_RESULTS_PATH
from rag.storage.embedder import embed_user_query
from rag.storage.vectorstore import search_chunks
from rag.retrieval.hybrid_retriever import hybrid_search

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
            results = search_chunks(query_vector, top_k=top_k)

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


# ── Text-based ground truth (current corpus) ─────────────────────────────────
# The original dataset above names chunk ids from an earlier HR-policy corpus
# (e.g. "chunk_107"), which cannot exist in today's document-aware id scheme
# ("insurancepolicy:chunk_17"). The insurance dataset instead records the phrase that
# answers each question, so a retrieved chunk is relevant when it contains that phrase.
import re
from rag.config import DATA_DIR

INSURANCE_DATASET_PATH = DATA_DIR / "evaluation_dataset_insurance.json"


def _norm(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _contains_any(text, phrases):
    haystack = _norm(text)
    return any(_norm(p) in haystack for p in phrases)


def _retrieve_for_eval(question, mode, top_k, document_name=None):
    if mode == "semantic":
        flt = {"document_name": {"$eq": document_name}} if document_name else None
        return search_chunks(embed_user_query(question), top_k=top_k, filter=flt)
    if mode == "hybrid":
        return hybrid_search(question, top_k=top_k, document_name=document_name)
    if mode == "reranked":
        from rag.retrieval.reranker import rerank_chunks
        from rag.retrieval.mmr import apply_mmr
        cands = hybrid_search(question, top_k=10, candidate_k=10, document_name=document_name)
        reranked = rerank_chunks(question, cands, top_k=min(6, len(cands)))
        return apply_mmr(question, reranked, top_k=top_k, lambda_param=0.6)
    raise ValueError(f"Unknown mode '{mode}'")


def run_text_evaluation(mode="hybrid", top_k=3, dataset_path=INSURANCE_DATASET_PATH, save=True):
    """Hit-rate@k, recall@k and MRR where relevance means the chunk text contains the answer phrase."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    per_question, hits, recalls, rrs = [], [], [], []
    for item in dataset:
        results = _retrieve_for_eval(item["question"], mode, top_k)
        expected = item["expected_text"]
        relevant_flags = [_contains_any(r["text"], expected) for r in results]
        hit = 1 if any(relevant_flags) else 0
        found = sum(1 for phrase in expected if any(_contains_any(r["text"], [phrase]) for r in results))
        recall = found / len(expected)
        rr = next((1.0 / rank for rank, ok in enumerate(relevant_flags, start=1) if ok), 0.0)
        hits.append(hit); recalls.append(recall); rrs.append(rr)
        per_question.append({
            "id": item["id"], "question": item["question"], "expected_text": expected,
            "retrieved_ids": [r["id"] for r in results], "relevant_flags": relevant_flags,
            "hit": hit, "recall": round(recall, 4), "reciprocal_rank": round(rr, 4),
        })

    summary = {
        "retriever": {"semantic": "Semantic Search", "hybrid": "Hybrid Search (Semantic + BM25 + RRF)",
                      "reranked": "Hybrid + Cross-Encoder + MMR"}[mode],
        "mode": mode, "top_k": top_k, "num_questions": len(dataset),
        "corpus": "current insurance PDFs (resources/)",
        "hit_rate": round(sum(hits) / len(hits), 4), "recall": round(sum(recalls) / len(recalls), 4),
        "mrr": round(sum(rrs) / len(rrs), 4), "per_question": per_question,
    }
    if save:
        out = DATA_DIR / f"insurance_results_{mode}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
    return summary


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "hybrid"
    results = run_evaluation(mode=mode)

    output_path = HYBRID_RESULTS_PATH if mode == "hybrid" else BASELINE_RESULTS_PATH
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print(f"Results saved to: {output_path}\n")
