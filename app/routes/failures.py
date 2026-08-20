# ============================================================
# app/routes/failures.py
#
# GET  /api/failures        — list all questions with labels
# POST /api/failures/label  — save a human label
# ============================================================

import logging
from fastapi import APIRouter
from app.models.schemas import LabelRequest
from app.services.failure_labeler import get_all_failure_labels, save_human_label

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", summary="Get all failure labels and analysis")
async def get_failures():
    """
    Returns all evaluation questions with:
    - Auto-labeled failure type (retrieval_failure | pass) for baseline and hybrid
    - Human label override (if set via POST /api/failures/label)
    - Evidence text
    - Before/after retrieved chunk IDs for comparison
    """
    labels = get_all_failure_labels()
    return {"failures": labels, "count": len(labels)}


@router.post("/label", summary="Save a human failure label")
async def save_label(request: LabelRequest):
    """
    Saves a human-provided failure label for a specific question.

    Labels:
    - `retrieval_failure` — correct document was NOT fetched
    - `generation_failure` — correct document WAS fetched, but LLM answered wrong
    - `pass` — both retrieval and answer were correct
    """
    save_human_label(
        question=request.question,
        label=request.label,
        evidence=request.evidence,
    )
    return {
        "status": "saved",
        "question": request.question,
        "label": request.label,
        "evidence": request.evidence,
    }
