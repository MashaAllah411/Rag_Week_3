# ============================================================
# main_rag.py — Master RAG Application (Phases 1 to 11 Integrated)
#
# FULL PIPELINE FLOW:
#   1. Raw User Query
#   2. Phase 11 : Query Rewriting (Llama 3.2 via Ollama)
#   3. Phase 6  : Hybrid Search (Pinecone Semantic + BM25 Keyword via RRF)
#   4. Phase 9  : Cross-Encoder Reranking (ms-marco-MiniLM-L-6-v2)
#   5. Phase 10 : MMR Diversity Filtering (lambda = 0.6)
#   6. LLM      : Answer Generation with Context (Llama 3.2)
#   7. Phase 1  : Full Structured Inspection View Output
# ============================================================

from query_rewriter import rewrite_query
from hybrid_retriever import hybrid_search
from reranker import rerank_chunks
from mmr import apply_mmr
from llm import query_llm_with_context
from queryprocessor import print_inspection_view


def run_master_rag(raw_query: str):
    """Executes the complete Week 4 RAG pipeline."""

    line = "=" * 60
    print(f"\n{line}")
    print("MASTER RAG PIPELINE STARTED")
    print(line)

    # 1. Phase 11: Query Rewriting
    print("\n[STEP 1/5] Rewriting Query with Llama 3.2...")
    search_query = rewrite_query(raw_query)
    print(f"  Raw Input      : '{raw_query}'")
    print(f"  Rewritten Query: '{search_query}'")

    # 2. Phase 6: Hybrid Search (Semantic + BM25 via RRF)
    print("\n[STEP 2/5] Executing Hybrid Search (Pinecone + BM25 + RRF)...")
    hybrid_candidates = hybrid_search(search_query, top_k=10)
    print(f"  Retrieved {len(hybrid_candidates)} candidates.")

    # 3. Phase 9: Cross-Encoder Reranking
    print("\n[STEP 3/5] Reranking candidates with Cross-Encoder...")
    reranked_candidates = rerank_chunks(search_query, hybrid_candidates, top_k=6)
    print(f"  Reranked top {len(reranked_candidates)} candidates.")

    # 4. Phase 10: MMR Diversity Filter
    print("\n[STEP 4/5] Applying MMR Diversity Filter (lambda=0.6)...")
    final_chunks = apply_mmr(search_query, reranked_candidates, top_k=3, lambda_param=0.6)
    print(f"  Selected top {len(final_chunks)} diverse chunks.")

    # 5. Build LLM Context & Generate Answer
    print("\n[STEP 5/5] Generating answer with Llama 3.2...")
    context = "\n\n---\n\n".join(item["text"] for item in final_chunks)
    answer = query_llm_with_context(raw_query, context)

    # Format structured results for Inspection View
    inspection_results = [
        {
            "id": c["id"],
            "score": c.get("rerank_score", c.get("rrf_score", 0.0)),
            "text": c["text"]
        }
        for c in final_chunks
    ]

    # 6. Phase 1: Inspection View Output
    print_inspection_view(raw_query, inspection_results, answer)


if __name__ == "__main__":
    user_input = "notice period for resignation?"
    run_master_rag(user_input)
