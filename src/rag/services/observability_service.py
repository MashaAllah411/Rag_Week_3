"""
observability_service.py

Service layer orchestrating:
- OpenTelemetry span-level production traces
- Support Triage Drill: diagnosing customer complaints and locating faulty spans
- Trace replay execution and side-by-side comparison
"""
from __future__ import annotations
import os
import json
from typing import Dict, Any, List, Optional

from rag.observability.tracer import (
    ProductionTracer,
    RequestTrace,
    Span,
    DEFAULT_PROD_TRACES_PATH,
    DEFAULT_TRACES_PATH,
    get_trace_by_id,
    replay_trace
)
from rag.observability.support_drill import (
    generate_production_traces,
    diagnose_complaint,
    PLANTED_TRACE_ID,
    PLANTED_CLAIM_ID
)

_prod_tracer = ProductionTracer(log_path=DEFAULT_PROD_TRACES_PATH)


def list_recent_traces(limit: int = 50, trace_type: str = "production") -> List[Dict[str, Any]]:
    """List recent traces from either production or standard log."""
    if trace_type == "production":
        # If production traces do not exist yet, generate them once
        if not os.path.exists(DEFAULT_PROD_TRACES_PATH):
            generate_production_traces(DEFAULT_PROD_TRACES_PATH, count=100)
        traces = _prod_tracer.load_all_traces()
        return traces[-limit:]
    else:
        if not os.path.exists(DEFAULT_TRACES_PATH):
            return []
        traces = []
        with open(DEFAULT_TRACES_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        traces.append(json.loads(line))
                    except Exception:
                        continue
        return traces[-limit:]


def get_trace_details(trace_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full trace details including span breakdown."""
    # Check production traces
    t = _prod_tracer.find_trace_by_id(trace_id)
    if t:
        return t
    # Fallback to standard trace
    try:
        return get_trace_by_id(trace_id)
    except Exception:
        return None


def replay_saved_trace(trace_id: str) -> Dict[str, Any]:
    """Replay a trace purely from saved fields."""
    return replay_trace(trace_id)


def run_support_drill(complaint_text: str = "Customer says their water damage claim was denied incorrectly or approved when it should not be.") -> Dict[str, Any]:
    """
    Run support triage diagnosis across 100 realistic traces to locate the planted bad answer.
    """
    if not os.path.exists(DEFAULT_PROD_TRACES_PATH):
        generate_production_traces(DEFAULT_PROD_TRACES_PATH, count=100)

    diagnosis = diagnose_complaint(complaint_text, DEFAULT_PROD_TRACES_PATH)
    diagnosis["planted_reference"] = {
        "expected_trace_id": PLANTED_TRACE_ID,
        "expected_claim_id": PLANTED_CLAIM_ID
    }
    return diagnosis
