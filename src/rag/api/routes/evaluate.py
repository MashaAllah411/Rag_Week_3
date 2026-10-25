# ============================================================
# src/rag/api/routes/evaluate.py
#
# Evaluation endpoints: retrieval metrics, live runs,
# deterministic assertions, and LLM judge evaluation.
# ============================================================

import json
import os
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from rag.models.schemas import (
    EvaluateRequest,
    EvaluateResponse,
    PerQuestionResult,
    JudgeEvalRequest,
    AssertionCheckRequest
)
from rag.evaluation.failure_labeler import get_aggregate_metrics, get_all_failure_labels
from rag.config import BASELINE_RESULTS_PATH, HYBRID_RESULTS_PATH
from rag.services.evaluation_service import run_deterministic_assertions, run_judge_evaluation

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

    failure_data = {item["question"]: item for item in get_all_failure_labels()}

    per_q = []
    for pq in data.get("per_question", []):
        q = pq["question"]
        fd = failure_data.get(q, {})
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
    Returns side-by-side before (semantic) vs after (hybrid) metrics.
    """
    return get_aggregate_metrics()


@router.post(
    "/run",
    summary="Run a fresh evaluation (requires ChromaDB + Ollama)"
)
async def run_evaluation(request: EvaluateRequest, background_tasks: BackgroundTasks):
    """
    Triggers a live evaluation run in the background.
    """
    def _run(mode: str, top_k: int):
        try:
            from rag.evaluation.retrieval_eval import run_evaluation as _eval
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


@router.post("/assertions", summary="Run deterministic assertions on text")
async def check_assertions(request: AssertionCheckRequest):
    """Runs 4 deterministic regex assertions: claim format, date of loss, deductible, and exclusion citation."""
    return run_deterministic_assertions(request.text, is_denial=request.is_denial)


@router.post("/judge", summary="Run LLM Judge (V1 or V2 calibration)")
async def evaluate_with_judge(request: JudgeEvalRequest):
    """Runs calibrated LLM Judge to assess grounding and correctness."""
    return run_judge_evaluation(
        query=request.query,
        context=request.context,
        answer=request.answer,
        judge_version=request.judge_version
    )


# ── Current-corpus evaluation, judge validation, regression loop ─────────────

import glob as _glob
from typing import Literal
from pydantic import BaseModel, Field
from rag.services.evaluation_service import get_judge_validation, get_dataset_status
from rag.evaluation.regression import REGRESSION_CASES, run_all_regression_cases


class InsuranceRunRequest(BaseModel):
    mode: Literal["semantic", "hybrid", "reranked"] = "hybrid"
    top_k: int = Field(default=3, ge=1, le=10)


@router.get("/datasets", summary="Which evaluation datasets can be scored on the current index")
async def datasets():
    return {"datasets": get_dataset_status()}


@router.get("/insurance/results", summary="Saved results of the current-corpus evaluation, per mode")
async def insurance_results():
    from rag.config import DATA_DIR
    out = {}
    for mode in ("semantic", "hybrid", "reranked"):
        path = os.path.join(str(DATA_DIR), f"insurance_results_{mode}.json")
        out[mode] = _load_result_file(path) or None
    return out


@router.post("/insurance/run", summary="Run the current-corpus evaluation for one retrieval mode")
async def insurance_run(request: InsuranceRunRequest):
    """Runs synchronously (12 questions, retrieval only: no LLM needed) and saves the result."""
    try:
        from rag.evaluation.retrieval_eval import run_text_evaluation
        return run_text_evaluation(mode=request.mode, top_k=request.top_k)
    except Exception as e:
        logger.error(f"[EVALUATE] insurance run failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")


@router.get("/judge-validation", summary="Judge agreement with human labels")
async def judge_validation():
    return get_judge_validation()


@router.get("/regression", summary="Failure-to-test loop: the permanent regression cases")
async def regression_cases():
    return {"cases": [{k: c[k] for k in ("id", "title", "origin", "notes", "incident_type", "expect_status")}
                      for c in REGRESSION_CASES]}


@router.post("/regression/run", summary="Run every regression case")
async def regression_run():
    return run_all_regression_cases()
