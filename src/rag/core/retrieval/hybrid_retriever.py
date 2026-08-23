# ============================================================
# hybrid_retriever.py
#
# PURPOSE:
#   Combines Semantic Search (Pinecone) and Keyword Search (BM25)
#   using Reciprocal Rank Fusion (RRF).
#
# HOW IT WORKS:
#   1. Runs Semantic Search -> retrieves Top 10 chunks
#   2. Runs BM25 Search     -> retrieves Top 10 chunks
#   3. Merges results using RRF formula: RRF_score = 1 / (60 + rank)
#   4. Returns top K hybrid candidates with full rank metadata.
# ============================================================

from typing import List, Dict
from rag.infra.embedder import embed_user_query
from rag.infra.vectorstore import search_in_pinecone
from rag.core.retrieval.bm25 import search_bm25

RRF_K = 60  # Standard smoothing constant for RRF


def hybrid_search(query: str, top_k: int = 3, candidate_k: int = 10, document_name: str | None = None) -> List[Dict]:
    """
    Executes hybrid search (Semantic + BM25) and fuses rankings via RRF.

    Args:
        query       : User search prompt
        top_k       : Number of final combined results to return
        candidate_k : Number of candidates to retrieve from each retriever

    Returns:
        Structured list of dicts with RRF scores and individual ranks:
        [
            {
                "id": "chunk_107",
                "text": "...",
                "rrf_score": 0.0325,
                "semantic_rank": 1,
                "bm25_rank": 2
            }
        ]
    """
    # 1. Retrieve candidates from both retrievers
    query_vector = embed_user_query(query)
    metadata_filter = {"document_name": {"$eq": document_name}} if document_name else None
    semantic_results = search_in_pinecone(query_vector, top_k=candidate_k, filter=metadata_filter)
    bm25_results = search_bm25(query, top_k=candidate_k, document_name=document_name)

    # 2. Track ranks and chunks by ID
    chunks_map = {}          # chunk_id -> chunk_text
    semantic_ranks = {}      # chunk_id -> rank (1-indexed)
    bm25_ranks = {}          # chunk_id -> rank (1-indexed)
    rrf_scores = {}          # chunk_id -> total rrf score

    # Process Semantic Search results
    for rank, item in enumerate(semantic_results, start=1):
        cid = item["id"]
        chunks_map[cid] = item["text"]
        semantic_ranks[cid] = rank
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (RRF_K + rank))

    # Process BM25 Search results
    for rank, item in enumerate(bm25_results, start=1):
        cid = item["id"]
        chunks_map[cid] = item["text"]
        bm25_ranks[cid] = rank
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (RRF_K + rank))

    # 3. Sort chunks by RRF score descending
    sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

    # 4. Construct final structured output
    final_results = []
    for cid in sorted_ids[:top_k]:
        final_results.append({
            "id": cid,
            "text": chunks_map[cid],
            "rrf_score": round(rrf_scores[cid], 6),
            "semantic_rank": semantic_ranks.get(cid, None),
            "bm25_rank": bm25_ranks.get(cid, None)
        })

    return final_results


if __name__ == "__main__":
    test_query = "How many weeks notice must a staff member give when resigning?"
    print(f"\n[SEARCH] Testing Hybrid Search for: '{test_query}'\n")

    results = hybrid_search(test_query, top_k=3)

    for idx, res in enumerate(results, start=1):
        print(f"Rank {idx}")
        print(f"  Chunk ID     : {res['id']}")
        print(f"  RRF Score    : {res['rrf_score']}")
        print(f"  Semantic Rank: {res['semantic_rank']}")
        print(f"  BM25 Rank    : {res['bm25_rank']}")
        safe_preview = res['text'][:100].encode('ascii', errors='replace').decode('ascii')
        print(f"  Text Preview : {safe_preview}...\n")
