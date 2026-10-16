# ============================================================
# src/rag/observability/tracer.py — Production Tracing & Spans
#
# PURPOSE:
#   Implements production-grade observability for AI agent requests:
#     1. Granular Span-level timing & token/dollar costing
#     2. OpenTelemetry / Phoenix / LangSmith compatible schema
#     3. Per-step cost and latency breakdown (never just one lump sum)
#     4. Export to traces/production_traces.jsonl
# ============================================================

from __future__ import annotations
import os
import sys
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

# Token pricing defaults (e.g. GPT-4o-mini / Claude 3.5 Haiku class: $0.15/1M input, $0.60/1M output)
DEFAULT_INPUT_COST_PER_1K = 0.00015
DEFAULT_OUTPUT_COST_PER_1K = 0.00060

DEFAULT_TRACES_PATH = os.path.join("traces", "production_traces.jsonl")


@dataclass
class Span:
    """Represents a single discrete execution step within a request."""
    span_id: str
    name: str
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    duration_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    status: str = "OK"  # "OK" | "ERROR"
    attributes: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    def end(self, status: str = "OK", error: Optional[str] = None):
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000.0, 2)
        self.status = status
        self.error_message = error
        # Calculate cost
        self.cost_usd = round(
            (self.tokens_in / 1000.0) * DEFAULT_INPUT_COST_PER_1K +
            (self.tokens_out / 1000.0) * DEFAULT_OUTPUT_COST_PER_1K,
            6
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RequestTrace:
    """Represents the complete trace of an end-to-end request."""
    trace_id: str = field(default_factory=lambda: f"tr_{uuid.uuid4().hex[:12]}")
    request_id: str = ""
    timestamp: float = field(default_factory=time.time)
    query: str = ""
    spans: List[Span] = field(default_factory=list)
    total_duration_ms: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    status: str = "COMPLETED"  # "COMPLETED" | "FAILED"
    metadata: Dict[str, Any] = field(default_factory=dict)
    final_output: Dict[str, Any] = field(default_factory=dict)

    def start_span(self, name: str, parent_span_id: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None) -> Span:
        span = Span(
            span_id=f"sp_{uuid.uuid4().hex[:8]}",
            name=name,
            parent_span_id=parent_span_id,
            start_time=time.time(),
            attributes=attributes or {}
        )
        self.spans.append(span)
        return span

    def complete(self, final_output: Optional[Dict[str, Any]] = None, status: str = "COMPLETED"):
        self.status = status
        if final_output:
            self.final_output = final_output
        self.total_duration_ms = round(sum(s.duration_ms for s in self.spans), 2)
        self.total_tokens = sum(s.tokens_in + s.tokens_out for s in self.spans)
        self.total_cost_usd = round(sum(s.cost_usd for s in self.spans), 6)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["span_count"] = len(self.spans)
        # Add human-readable step breakdown
        d["step_breakdown"] = [
            {
                "step": s.name,
                "duration_ms": s.duration_ms,
                "tokens": s.tokens_in + s.tokens_out,
                "cost_usd": s.cost_usd,
                "status": s.status
            }
            for s in self.spans
        ]
        return d


class ProductionTracer:
    """Manages recording, persisting, and querying production traces."""

    def __init__(self, log_path: str = DEFAULT_TRACES_PATH):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_trace(self, trace: RequestTrace):
        """Appends a completed trace to the production log file."""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace.to_dict()) + "\n")

    def load_all_traces(self) -> List[Dict[str, Any]]:
        """Loads all traces from the production log file."""
        if not os.path.exists(self.log_path):
            return []
        traces = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    traces.append(json.loads(line))
        return traces

    def find_trace_by_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific trace by its unique trace_id."""
        for t in self.load_all_traces():
            if t.get("trace_id") == trace_id:
                return t
        return None
