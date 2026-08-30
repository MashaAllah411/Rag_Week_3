# ============================================================
# app/services/pipeline.py
#
# PURPOSE:
#   Orchestrates the existing RAG modules to serve the FastAPI
#   routes. This is a thin wrapper — it imports and calls the
#   existing console scripts as library functions.
#
# EXISTING MODULES USED (ALL UNCHANGED):
#   embedder.py        → embed_user_query
#   vectorstore.py     → search_in_pinecone
#   bm25.py            → search_bm25
#   hybrid_retriever.py→ hybrid_search
#   reranker.py        → rerank_chunks
#   mmr.py             → apply_mmr
#   query_rewriter.py  → rewrite_query
#   llm.py             → query_llm_with_context
# ============================================================

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

_OUT_OF_SCOPE_RESPONSE = (
    "I can only answer questions related to the provided insurance policy document."
)

_IDK_RESPONSE = (
    "I don't know based on the provided documents. "
    "The retrieved context does not contain a clear answer to your question. "
    "Please rephrase or consult the Insurance Policy document directly."
)


# ── Lazy imports (heavy models load only once) ────────────────

def _get_embedder():
    from rag.core.providers import get_embedding_provider
    return get_embedding_provider().embed_user_query


def _get_pinecone_search():
    from rag.core.providers import get_vectorstore_provider
    return get_vectorstore_provider().search


def _get_hybrid_search():
    from rag.core.providers import get_hybrid_retriever
    return get_hybrid_retriever()


def _get_reranker():
    from rag.core.providers import get_reranker
    return get_reranker()


def _get_mmr():
    from rag.core.providers import get_mmr
    return get_mmr()


def _get_query_rewriter():
    from rag.core.providers import get_query_rewriter
    return get_query_rewriter()


def _get_llm():
    from rag.core.providers import get_llm_provider
    return get_llm_provider().query_with_context


# ── Confidence gate ──────────────────────────────────────────

def _assess_confidence(chunks: List[Dict], threshold: float) -> str:
    """
    Returns 'high', 'low', or 'unknown' based on top chunk score.
    """
    if not chunks:
        return "unknown"
    top = chunks[0]
    score = top.get("rerank_score") or top.get("rrf_score") or top.get("score") or 0.0
    if score >= threshold:
        return "high"
    elif score > 0:
        return "low"
    return "unknown"


# ── Main pipeline function ───────────────────────────────────

def run_pipeline(
    question: str,
    mode: str = "hybrid",
    top_k: int = 3,
    similarity_threshold: float = 0.0,
    use_query_rewriter: bool = True,
    document_name: Optional[str] = None,
) -> Dict:
    """
    Full RAG pipeline:
      1. Scope Check
      2. (Optional) Query rewriting
      3. Retrieval:  semantic | hybrid | reranked
      4. Confidence check
      5. LLM grounded answer generation
      6. Log PII-redacted trace (Week 5)
      7. Return structured result dict
    """
    pipeline_steps = []

    # Reject invalid/unrelated requests before query rewriting and retrieval.
    from rag.core.scope_guard import check_question_scope
    scope = check_question_scope(question, document_name=document_name)
    if not scope.allowed:
        pipeline_steps.append(f"Scope guard rejected request: {scope.reason}")
        return {
            "question": question,
            "rewritten_query": None,
            "answer": _OUT_OF_SCOPE_RESPONSE,
            "retrieved_chunks": [],
            "mode": mode,
            "confidence": "unknown",
            "source_document": document_name or "InsurancePolicy.pdf",
            "pipeline_steps": pipeline_steps,
        }
    if scope.reason == "guard_unavailable":
        pipeline_steps.append("Scope guard unavailable; continuing with retrieval")

    # ── Step 1: Query Rewriting ──────────────────────────────
    rewritten_query = question
    if use_query_rewriter:
        try:
            logger.info(f"[PIPELINE] Rewriting query: '{question}'")
            rewrite_query = _get_query_rewriter()
            rewritten_query = rewrite_query(question)
            pipeline_steps.append(f"Query rewritten: '{question}' → '{rewritten_query}'")
            logger.info(f"[PIPELINE] Rewritten: '{rewritten_query}'")
        except Exception as e:
            logger.warning(f"[PIPELINE] Query rewriter failed: {e}. Using original.")
            rewritten_query = question
            pipeline_steps.append(f"Query rewriter failed (using original): {e}")
    else:
        pipeline_steps.append("Query rewriting skipped (disabled by user)")

    search_query = rewritten_query

    # ── Step 2: Retrieval ────────────────────────────────────
    raw_chunks: List[Dict] = []

    if mode == "semantic":
        logger.info("[PIPELINE] Mode: Semantic Search")
        embed_fn = _get_embedder()
        search_fn = _get_pinecone_search()
        query_vec = embed_fn(search_query)
        metadata_filter = {"document_name": {"$eq": document_name}} if document_name else None
        raw_results = search_fn(query_vec, top_k=top_k, filter=metadata_filter)
        for r in raw_results:
            raw_chunks.append({
                "id": r["id"],
                "text": r["text"],
                "score": r.get("score", 0.0),
            })
        pipeline_steps.append(f"Semantic search → {len(raw_chunks)} chunks retrieved")

    elif mode == "hybrid":
        logger.info("[PIPELINE] Mode: Hybrid Search (BM25 + Pinecone + RRF)")
        hybrid_fn = _get_hybrid_search()
        raw_results = hybrid_fn(search_query, top_k=top_k, candidate_k=10, document_name=document_name)
        for r in raw_results:
            raw_chunks.append({
                "id": r["id"],
                "text": r["text"],
                "score": r.get("rrf_score", 0.0),
                "semantic_rank": r.get("semantic_rank"),
                "bm25_rank": r.get("bm25_rank"),
            })
        pipeline_steps.append(f"Hybrid search (RRF) → {len(raw_chunks)} chunks retrieved")

    elif mode == "reranked":
        logger.info("[PIPELINE] Mode: Hybrid + Cross-Encoder Reranking + MMR")
        hybrid_fn = _get_hybrid_search()
        hybrid_candidates = hybrid_fn(search_query, top_k=10, candidate_k=10, document_name=document_name)
        pipeline_steps.append(f"Hybrid search → {len(hybrid_candidates)} candidates")

        rerank_fn = _get_reranker()
        reranked = rerank_fn(search_query, hybrid_candidates, top_k=min(6, len(hybrid_candidates)))
        pipeline_steps.append(f"Cross-encoder reranking → top {len(reranked)} reranked")

        mmr_fn = _get_mmr()
        final = mmr_fn(search_query, reranked, top_k=top_k, lambda_param=0.6)
        pipeline_steps.append(f"MMR diversity filter → top {len(final)} diverse chunks")

        for r in final:
            raw_chunks.append({
                "id": r["id"],
                "text": r["text"],
                "score": r.get("rerank_score", r.get("rrf_score", 0.0)),
                "semantic_rank": r.get("semantic_rank"),
                "bm25_rank": r.get("bm25_rank"),
                "rerank_score": r.get("rerank_score"),
            })
    else:
        raise ValueError(f"Unknown mode: '{mode}'. Use 'semantic', 'hybrid', or 'reranked'.")

    # ── Step 3: Confidence Check ─────────────────────────────
    confidence = _assess_confidence(raw_chunks, similarity_threshold)
    pipeline_steps.append(f"Confidence assessment: {confidence.upper()}")
    logger.info(f"[PIPELINE] Confidence: {confidence}")

    # ── Step 4: LLM Grounded Answer ──────────────────────────
    if not raw_chunks or confidence == "unknown":
        answer = _IDK_RESPONSE
        pipeline_steps.append("No chunks retrieved → returning I-don't-know response")
    else:
        try:
            llm_fn = _get_llm()
            context = "\n\n---\n\n".join(c["text"] for c in raw_chunks)
            answer = llm_fn(question, context)
            pipeline_steps.append("LLM grounded answer generated (Llama 3.2)")
            logger.info("[PIPELINE] LLM answer generated.")
        except Exception as e:
            logger.error(f"[PIPELINE] LLM call failed: {e}")
            answer = (
                "LLM unavailable — retrieved context shown below. "
                f"Error: {e}"
            )
            pipeline_steps.append(f"LLM call failed: {e}")

    # ── Step 5: Log PII-Redacted Trace (Week 5 Requirement) ──
    try:
        from tracer import log_trace
        log_trace(
            query=question,
            retrieved_chunks=raw_chunks,
            raw_llm_output=answer,
            prompt_version="v1.0",
            retriever_type=f"Web API ({mode})",
            model_name="llama3.2",
            model_parameters={"temperature": 0.4, "top_p": 0.9}
        )
        pipeline_steps.append("PII-redacted trace logged to traces/traces.jsonl")
    except Exception as e:
        logger.warning(f"[PIPELINE] Trace logging failed: {e}")

    # ── Step 6: Return structured result ─────────────────────
    return {
        "question": question,
        "rewritten_query": rewritten_query if rewritten_query != question else None,
        "answer": answer,
        "retrieved_chunks": raw_chunks,
        "mode": mode,
        "confidence": confidence,
        "source_document": document_name or "InsurancePolicy.pdf",
        "pipeline_steps": pipeline_steps,
    }
