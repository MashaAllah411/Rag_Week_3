"""Backward-compatibility stub forwarding to rag.observability.tracer."""
from rag.observability.tracer import (
    redact_pii,
    log_trace,
    get_trace_by_id,
    replay_trace,
    Span,
    RequestTrace,
    ProductionTracer,
    TRACES_FILE,
    DEFAULT_TRACES_PATH,
    DEFAULT_PROD_TRACES_PATH
)

__all__ = [
    "redact_pii",
    "log_trace",
    "get_trace_by_id",
    "replay_trace",
    "Span",
    "RequestTrace",
    "ProductionTracer",
    "TRACES_FILE",
    "DEFAULT_TRACES_PATH",
    "DEFAULT_PROD_TRACES_PATH"
]
