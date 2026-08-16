# ============================================================
# reranker.py
#
# PURPOSE:
#   Reranks top candidate chunks using a local Cross-Encoder model
#   (cross-encoder/ms-marco-MiniLM-L-6-v2).
#
# HOW IT WORKS:
#   1. Receives Top N candidates from Hybrid Search (e.g. N=10).
#   2. Passes pairs of (query, chunk_text) through the Cross-Encoder.
#   3. Produces a refined relevance score for each pair.
#   4. Re-sorts candidates and returns the Top K (e.g. K=3).
# ============================================================

from sentence_transformers import CrossEncoder
from typing import List, Dict

# Load local cross-encoder model (~80MB download on first run)
print("[RERANKER] Loading Cross-Encoder model (cross-encoder/ms-marco-MiniLM-L-6-v2)...")
reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
print("[RERANKER] Model loaded successfully.")


def rerank_chunks(query: str, candidates: List[Dict], top_k: int = 3) -> List[Dict]:
    """
    Reranks candidate chunks using a Cross-Encoder model.

    Args:
        query      : Raw user query
        candidates : List of dicts with 'id', 'text', etc. (from hybrid search)
        top_k      : Number of reranked candidates to return

    Returns:
        List of dicts sorted by cross-encoder score descending.
    """
    if not candidates:
        return []

    # Prepare pairs for cross-encoder scoring: [(query, text_1), (query, text_2), ...]
    pairs = [(query, c["text"]) for c in candidates]

    # Compute cross-encoder scores
    scores = reranker_model.predict(pairs)

    # Attach scores to candidates
    reranked = []
    for candidate, score in zip(candidates, scores):
        item = candidate.copy()
        item["rerank_score"] = round(float(score), 4)
        reranked.append(item)

    # Sort by rerank score descending
    reranked = sorted(reranked, key=lambda x: x["rerank_score"], reverse=True)

    return reranked[:top_k]


if __name__ == "__main__":
    from hybrid_retriever import hybrid_search

    test_query = "How many weeks notice must a staff member give when resigning?"
    print(f"\n[SEARCH] Fetching Top 10 candidates via Hybrid Search for: '{test_query}'")
    initial_candidates = hybrid_search(test_query, top_k=10)

    print(f"\n[RERANKING] Reranking Top 10 candidates with Cross-Encoder...")
    reranked_results = rerank_chunks(test_query, initial_candidates, top_k=3)

    print("\n" + "=" * 60)
    print("RERANKED RESULTS")
    print("=" * 60)
    for rank, res in enumerate(reranked_results, start=1):
        print(f"Rank {rank}")
        print(f"  Chunk ID    : {res['id']}")
        print(f"  Rerank Score: {res['rerank_score']}")
        print(f"  Original RRF: {res.get('rrf_score')}")
        safe_preview = res['text'][:100].encode('ascii', errors='replace').decode('ascii')
        print(f"  Text Preview: {safe_preview}...\n")
