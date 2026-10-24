# ============================================================
# src/rag/api/routes/observability.py
#
# Endpoints for Production Tracing, Spans, Support Drill & Caching
# (Weeks 5 & 11)
# ============================================================

from fastapi import APIRouter, HTTPException, Query
from rag.models.schemas import SupportDrillRequest, ReplayRequest, CacheBenchmarkRequest
from rag.services.observability_service import (
    list_recent_traces,
    get_trace_details,
    replay_saved_trace,
    run_support_drill
)
from rag.services.cache_service import run_cache_benchmark

router = APIRouter()


@router.get("/traces", summary="List recent request traces")
async def get_traces(
    limit: int = Query(default=50, ge=1, le=200),
    trace_type: str = Query(default="production", pattern="^(production|standard)$")
):
    """Returns recent traces with span metrics, token counts, and costs."""
    try:
        traces = list_recent_traces(limit=limit, trace_type=trace_type)
        return {"traces": traces, "count": len(traces)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traces/{trace_id}", summary="Get trace details and span breakdown")
async def get_trace(trace_id: str):
    """Returns detailed trace record with step-by-step span latency and costs."""
    trace = get_trace_details(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found.")
    return trace


@router.post("/replay", summary="Replay a trace from logged context")
async def replay(request: ReplayRequest):
    """Replays a query using only the saved context from the trace."""
    try:
        return replay_saved_trace(request.trace_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay failed: {e}")


@router.post("/drill", summary="Run support triage drill on production traces")
async def support_drill(request: SupportDrillRequest):
    """Diagnoses a vague customer complaint across traces and locates the faulty span."""
    try:
        return run_support_drill(complaint_text=request.complaint_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Support drill failed: {e}")


@router.post("/cache-benchmark", summary="Benchmark semantic cache cost savings")
async def cache_benchmark(request: CacheBenchmarkRequest):
    """Simulates production traffic and measures cost and latency reduction."""
    try:
        return run_cache_benchmark(num_queries=request.num_queries)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache benchmark failed: {e}")
