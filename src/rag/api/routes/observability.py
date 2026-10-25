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


# ── Week 5: error analysis (sample -> open-code notes -> taxonomy -> prediction) ──

from pydantic import BaseModel, Field
from rag.services import error_analysis_service as ea


class NoteRequest(BaseModel):
    trace_id: str
    note: str = Field(..., min_length=3, max_length=1000)
    category: str = Field(default="", max_length=80)
    severity: int = Field(default=3, ge=1, le=5)


class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=2000)


@router.get("/error-analysis/sample", summary="Seeded random sample of real traces to read")
async def error_sample(n: int = Query(default=20, ge=1, le=100), seed: int = Query(default=42)):
    return ea.sample_traces(n=n, seed=seed)


@router.post("/error-analysis/notes", summary="Save one open-coding note for a trace")
async def error_note(request: NoteRequest):
    return ea.save_note(request.trace_id, request.note, request.category, request.severity)


@router.get("/error-analysis/taxonomy", summary="Named problem groups ranked by frequency x severity")
async def error_taxonomy():
    return ea.taxonomy()


@router.post("/error-analysis/prediction", summary="Record the prediction before trying the fix")
async def error_prediction(request: PredictionRequest):
    return {"prediction": ea.save_prediction(request.text)}


@router.get("/otel", summary="OpenTelemetry exporter status and recent exported spans")
async def otel_status(limit: int = Query(default=30, ge=1, le=200)):
    import json
    from rag.observability.otel import tracing_status
    from rag.config import OTEL_SPANS_PATH
    spans = []
    if OTEL_SPANS_PATH.exists():
        with open(OTEL_SPANS_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
        for line in lines:
            try:
                spans.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return {"status": tracing_status(), "recent_spans": spans}
