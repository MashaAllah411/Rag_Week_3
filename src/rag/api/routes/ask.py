# ============================================================
# app/routes/ask.py
#
# POST /api/ask
# Runs the full RAG pipeline and returns structured result.
# ============================================================

import logging
from fastapi import APIRouter, HTTPException
from rag.models.schemas import AskRequest, AskResponse, ChunkResult
from rag.services.pipeline import run_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ask", response_model=AskResponse, summary="Ask a question against the HR Policy")
async def ask(request: AskRequest):
    """
    Runs the RAG pipeline for the given question.

    **Modes:**
    - `semantic` — Pinecone vector search only (baseline)
    - `hybrid` — Semantic + BM25 keyword search fused via RRF
    - `reranked` — Hybrid + Cross-Encoder reranking + MMR diversity

    Returns the LLM answer, retrieved chunks with scores, and pipeline trace.
    """
    logger.info(f"[ASK] Question: '{request.question}' | Mode: {request.mode} | top_k: {request.top_k}")

    try:
        result = run_pipeline(
            question=request.question,
            mode=request.mode,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            use_query_rewriter=request.use_query_rewriter,
            document_name=request.document_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[ASK] Pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    # Map raw chunk dicts to ChunkResult models
    chunks = [
        ChunkResult(
            chunk_id=c["id"],
            score=round(float(c.get("score", 0.0)), 6),
            text=c["text"],
            semantic_rank=c.get("semantic_rank"),
            bm25_rank=c.get("bm25_rank"),
            rerank_score=c.get("rerank_score"),
        )
        for c in result["retrieved_chunks"]
    ]

    return AskResponse(
        question=result["question"],
        rewritten_query=result.get("rewritten_query"),
        answer=result["answer"],
        retrieved_chunks=chunks,
        mode=result["mode"],
        confidence=result["confidence"],
        source_document=result["source_document"],
        pipeline_steps=result["pipeline_steps"],
    )
