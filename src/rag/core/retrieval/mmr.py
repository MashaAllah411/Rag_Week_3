# ============================================================
# mmr.py
#
# PURPOSE:
#   Implements Maximal Marginal Relevance (MMR) to select a diverse
#   subset of candidate chunks, reducing redundancy in LLM context.
#
# HOW IT WORKS:
#   1. Takes candidate chunks (with their sentence-transformer embeddings).
#   2. Iteratively picks chunks that are high relevance to query
#      AND low similarity to already selected chunks.
#   3. Controlled by lambda (lambda_param = 0.5 balances relevance & diversity).
# ============================================================

from typing import List, Dict
import numpy as np
from rag.infra.embedder import embed_texts, embed_user_query


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Computes cosine similarity between two 1D vectors."""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm == 0:
        return 0.0
    return float(np.dot(v1, v2) / norm)


def apply_mmr(
    query: str,
    candidates: List[Dict],
    top_k: int = 3,
    lambda_param: float = 0.6
) -> List[Dict]:
    """
    Selects top_k candidates from candidate pool using MMR.

    Args:
        query        : User query string
        candidates   : List of dicts with 'id', 'text', etc.
        top_k        : Number of diverse candidates to return
        lambda_param : 1.0 = Pure relevance, 0.0 = Pure diversity (0.6 is balanced)

    Returns:
        List of selected diverse candidate dicts.
    """
    if not candidates or len(candidates) <= top_k:
        return candidates

    # 1. Embed query and candidate texts
    query_vec = embed_user_query(query)
    cand_texts = [c["text"] for c in candidates]
    cand_vecs = embed_texts(cand_texts)

    # 2. Compute similarity of each candidate to query
    query_sims = [cosine_similarity(query_vec, v) for v in cand_vecs]

    selected_indices = []
    unselected_indices = list(range(len(candidates)))

    # 3. First selection: Pick candidate with highest query similarity
    best_first = int(np.argmax(query_sims))
    selected_indices.append(best_first)
    unselected_indices.remove(best_first)

    # 4. Iteratively select remaining candidates using MMR formula
    while len(selected_indices) < top_k and unselected_indices:
        best_mmr_score = -float('inf')
        best_candidate_idx = -1

        for idx in unselected_indices:
            rel_score = query_sims[idx]

            # Max similarity to any already selected candidate
            sim_to_selected = max([
                cosine_similarity(cand_vecs[idx], cand_vecs[sel_idx])
                for sel_idx in selected_indices
            ])

            # MMR formula
            mmr_score = (lambda_param * rel_score) - ((1 - lambda_param) * sim_to_selected)

            if mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_candidate_idx = idx

        selected_indices.append(best_candidate_idx)
        unselected_indices.remove(best_candidate_idx)

    # Return selected candidate objects
    return [candidates[i] for i in selected_indices]


if __name__ == "__main__":
    from rag.core.retrieval.hybrid_retriever import hybrid_search

    test_query = "What is the annual leave and company holiday policy?"
    print(f"\n[SEARCH] Retrieving Top 10 candidates via Hybrid Search for: '{test_query}'")
    candidates = hybrid_search(test_query, top_k=10)

    print(f"\n[MMR] Applying MMR (lambda=0.6) to select 3 diverse chunks...")
    diverse_chunks = apply_mmr(test_query, candidates, top_k=3, lambda_param=0.6)

    print("\n" + "=" * 60)
    print("MMR DIVERSE RESULTS")
    print("=" * 60)
    for rank, res in enumerate(diverse_chunks, start=1):
        print(f"Rank {rank}")
        print(f"  Chunk ID    : {res['id']}")
        safe_preview = res['text'][:100].encode('ascii', errors='replace').decode('ascii')
        print(f"  Text Preview: {safe_preview}...\n")
