# ============================================================
# src/rag/api/routes/multi_agent.py
#
# Endpoints for Multi-Agent Claims Squad via A2A Protocol (Week 10)
# ============================================================

from fastapi import APIRouter, HTTPException
from rag.models.schemas import SquadTriageRequest, MultiAgentRaceRequest
from rag.services.multi_agent_service import (
    get_agent_cards,
    run_squad_triage,
    run_multi_agent_race
)

router = APIRouter()


@router.get("/agents", summary="List Agent Cards for the squad")
async def list_agents():
    """Returns Agent Cards for Claims Manager, Policy Specialist, and Payout Specialist."""
    try:
        cards = get_agent_cards()
        return {"agents": cards, "count": len(cards)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/triage", summary="Run claim triage with Multi-Agent Squad")
async def triage(request: SquadTriageRequest):
    """Executes claim triage across the 3-agent squad via A2A message envelopes."""
    try:
        return run_squad_triage(request.claim_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Squad triage failed: {e}")


@router.post("/benchmark", summary="Race Single Agent vs Multi-Agent Squad")
async def benchmark(request: MultiAgentRaceRequest):
    """Races Single Agent vs Multi-Agent Squad across claims."""
    try:
        return run_multi_agent_race(claims_subset=request.claims)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-agent benchmark failed: {e}")
