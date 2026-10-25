# ============================================================
# src/rag/api/routes/capstone.py
#
# Week 12: full suite in one click, known weak spots, four-part demo script.
# ============================================================

from fastapi import APIRouter, HTTPException
from rag.services import capstone_service as svc

router = APIRouter()


@router.post("/suite", summary="Run the full suite across every week's capability")
async def run_suite():
    try:
        return svc.run_full_suite()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Suite failed: {exc}")


@router.get("/weak-spots", summary="Honest list of simulated, unmeasured or limited areas")
async def weak_spots():
    return {"weak_spots": svc.known_weak_spots()}


@router.get("/demo", summary="Four-part demo script filled from real results")
async def demo():
    return svc.demo_script()
