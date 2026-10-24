# ============================================================
# src/rag/api/routes/agent.py
#
# Endpoints for ReAct Agent Loop, Budgets & Benchmark (Weeks 7 & 8)
# ============================================================

from fastapi import APIRouter, HTTPException
from rag.models.schemas import AgentTriageRequest, AgentBenchmarkRequest
from rag.services.agent_service import (
    get_available_claims,
    triage_claim,
    run_agent_benchmark
)

router = APIRouter()


@router.get("/claims", summary="List mock claims available for triage")
async def list_claims():
    """Returns the list of 10 synthetic insurance claims with amounts and adjuster notes."""
    claims = get_available_claims()
    return {"claims": claims, "count": len(claims)}


@router.post("/triage", summary="Run claim triage with ReAct Agent or Fixed Workflow")
async def triage(request: AgentTriageRequest):
    """
    Executes claim triage and returns execution trace, tool laps, payout calculation,
    and trajectory evaluation metrics.
    """
    try:
        return triage_claim(
            claim_id=request.claim_id,
            system_type=request.system_type,
            force_budget_exceed=request.force_budget_exceed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent triage failed: {e}")


@router.post("/benchmark", summary="Race ReAct Agent vs Fixed Workflow")
async def benchmark(request: AgentBenchmarkRequest):
    """
    Races ReAct Agent vs Fixed Workflow across claims and measures
    pass rate, tokens, cost, and budget termination.
    """
    try:
        return run_agent_benchmark(claims_subset=request.claims)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent benchmark failed: {e}")
