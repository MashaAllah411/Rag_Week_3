# ============================================================
# app/routes/evaluate.py
#
# POST /api/evaluate   — run live evaluation
# GET  /api/evaluate/results — return pre-computed results
# GET  /api/evaluate/metrics — return before/after summary
# ============================================================

import json
import os
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from rag.models.schemas import EvaluateRequest, EvaluateResponse, PerQuestionResult
from rag.services.failure_labeler import get_aggregate_metrics, get_all_failure_labels
from rag.config import BASELINE_RESULTS_PATH, HYBRID_RESULTS_PATH

logger = logging.getLogger(__name__)
router = APIRouter()

_BASELINE_FILE = BASELINE_RESULTS_PATH
_HYBRID_FILE = HYBRID_RESULTS_PATH


def _load_result_file(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get(
    "/results/{mode}",
    response_model=EvaluateResponse,
    summary="Return pre-computed evaluation results"
)
async def get_results(mode: str):
    """
    Returns saved evaluation results for `semantic` or `hybrid` mode.
    These are the pre-computed results from running `evaluator.py`.
    """
    if mode == "semantic":
        data = _load_result_file(_BASELINE_FILE)
    elif mode == "hybrid":
        data = _load_result_file(_HYBRID_FILE)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown mode '{mode}'. Use 'semantic' or 'hybrid'.")

    if not data:
        raise HTTPException(status_code=404, detail=f"No results found for mode '{mode}'.")

    # Merge failure labels into per_question
    failure_data = {item["question"]: item for item in get_all_failure_labels()}

    per_q = []
    for pq in data.get("per_question", []):
        q = pq["question"]
        fd = failure_data.get(q, {})
        mode_key = "hybrid" if mode == "hybrid" else "baseline"
        effective_label = fd.get("effective_label") or fd.get("hybrid", {}).get("auto_label")
        per_q.append(PerQuestionResult(
            question=pq["question"],
            relevant_chunks=pq["relevant_chunks"],
            retrieved_ids=pq["retrieved_ids"],
            hit=pq["hit"],
            recall=pq["recall"],
            reciprocal_rank=pq["reciprocal_rank"],
            failure_type=effective_label if pq["hit"] == 0 else None,
        ))

    return EvaluateResponse(
        retriever=data["retriever"],
        top_k=data["top_k"],
        num_questions=data["num_questions"],
        hit_rate=data["hit_rate"],
        recall=data["recall"],
        mrr=data["mrr"],
        per_question=per_q,
    )


@router.get("/metrics", summary="Before/after improvement metrics")
async def get_metrics():
    """
    Returns the side-by-side before (semantic) vs after (hybrid) metrics.
    This is the core proof-of-fix number required by Week 4 M2.
    """
    return get_aggregate_metrics()


@router.post(
    "/run",
    summary="Run a fresh evaluation (requires Pinecone + Ollama)"
)
async def run_evaluation(request: EvaluateRequest, background_tasks: BackgroundTasks):
    """
    Triggers a live evaluation run.
    Saves results to baseline_results.json or hybrid_results.json.
    Runs in the background — poll /api/evaluate/results/{mode} for output.
    """
    def _run(mode: str, top_k: int):
        try:
            from rag.scripts.evaluator import run_evaluation as _eval
            _eval(mode=mode, top_k=top_k)
            logger.info(f"[EVALUATE] Completed live evaluation for mode={mode}")
        except Exception as e:
            logger.error(f"[EVALUATE] Live evaluation failed: {e}", exc_info=True)

    background_tasks.add_task(_run, request.mode, request.top_k)
    return {
        "status": "started",
        "message": f"Evaluation running in background for mode='{request.mode}'. "
                   f"Poll GET /api/evaluate/results/{request.mode} for results.",
        "mode": request.mode
    }
