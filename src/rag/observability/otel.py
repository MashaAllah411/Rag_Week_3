"""OpenTelemetry bridge (Week 11: LangSmith / Phoenix / OpenTelemetry -> OpenTelemetry).

The app's ``Span`` / ``RequestTrace`` classes (observability/tracer.py) keep their
interface; every finished span is also exported through the real OpenTelemetry
SDK to:

  * a local JSONL file (traces/otel_spans.jsonl)  - always on
  * any OTLP/HTTP collector, e.g. self-hosted Arize Phoenix or Jaeger - only when
    OTEL_EXPORTER_OTLP_ENDPOINT is set

No hosted SaaS is involved. If the SDK is not installed, tracing degrades to the
JSONL traces written by ``ProductionTracer`` and ``tracing_status()`` reports it.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any, Dict, Optional, Sequence

from rag.config import OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_SERVICE_NAME, OTEL_SPANS_PATH

logger = logging.getLogger(__name__)

_MAX_JSONL_BYTES = 5 * 1024 * 1024
_lock = threading.Lock()
_ready = False
_init_error: Optional[str] = None
_tracer = None
_provider = None
_jsonl_exporter = None
_otlp_endpoint_active = ""
_roots: Dict[str, Any] = {}          # request trace_id -> root OTel span
_emitted_ctx: Dict[str, Any] = {}    # app span_id -> OTel context (for explicit parents)


def _to_attr(value: Any) -> Any:
    """OTel attribute values must be primitives; redact PII in strings before export."""
    if isinstance(value, (bool, int, float)):
        return value
    from rag.observability.tracer import redact_pii
    return redact_pii(str(value))[:2000]


def _ns(ts: float) -> int:
    return int(ts * 1_000_000_000)


def init_tracing() -> bool:
    """Idempotently configure the SDK. Returns True when spans can be exported."""
    global _ready, _init_error, _tracer, _provider, _jsonl_exporter, _otlp_endpoint_active
    if _ready:
        return True
    with _lock:
        if _ready:
            return True
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import (
                BatchSpanProcessor, SimpleSpanProcessor, SpanExporter, SpanExportResult)

            class JsonlSpanExporter(SpanExporter):
                """Appends one JSON object per finished span."""

                def __init__(self, path):
                    self.path = str(path)
                    self.exported = 0
                    self._io_lock = threading.Lock()
                    os.makedirs(os.path.dirname(self.path), exist_ok=True)

                def export(self, spans: Sequence[Any]) -> "SpanExportResult":
                    lines = []
                    for s in spans:
                        ctx = s.get_span_context()
                        parent = s.parent.span_id if s.parent else None
                        lines.append(json.dumps({
                            "trace_id": format(ctx.trace_id, "032x"),
                            "span_id": format(ctx.span_id, "016x"),
                            "parent_span_id": format(parent, "016x") if parent else None,
                            "name": s.name,
                            "start_time_ns": s.start_time,
                            "end_time_ns": s.end_time,
                            "duration_ms": round(((s.end_time or s.start_time) - s.start_time) / 1e6, 3),
                            "status": s.status.status_code.name,
                            "service": s.resource.attributes.get("service.name"),
                            "attributes": {k: v for k, v in (s.attributes or {}).items()},
                        }))
                    with self._io_lock:
                        try:
                            if os.path.exists(self.path) and os.path.getsize(self.path) > _MAX_JSONL_BYTES:
                                os.replace(self.path, self.path + ".1")
                            with open(self.path, "a", encoding="utf-8") as f:
                                f.write("\n".join(lines) + "\n")
                            self.exported += len(lines)
                        except OSError:
                            logger.exception("Could not write OTel span export")
                            return SpanExportResult.FAILURE
                    return SpanExportResult.SUCCESS

                def shutdown(self) -> None:
                    return None

            provider = TracerProvider(resource=Resource.create({"service.name": OTEL_SERVICE_NAME}))
            _jsonl_exporter = JsonlSpanExporter(OTEL_SPANS_PATH)
            provider.add_span_processor(SimpleSpanProcessor(_jsonl_exporter))

            if OTEL_EXPORTER_OTLP_ENDPOINT:
                try:
                    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
                    provider.add_span_processor(BatchSpanProcessor(
                        OTLPSpanExporter(endpoint=OTEL_EXPORTER_OTLP_ENDPOINT)))
                    _otlp_endpoint_active = OTEL_EXPORTER_OTLP_ENDPOINT
                except Exception as exc:  # exporter package missing / bad endpoint
                    logger.warning("OTLP exporter disabled: %s", exc)

            _provider = provider
            _tracer = provider.get_tracer("rag.pipeline")
            _ready = True
            _init_error = None
            logger.info("OpenTelemetry tracing initialised (otlp=%s)", bool(_otlp_endpoint_active))
        except Exception as exc:
            _init_error = f"{type(exc).__name__}: {exc}"
            logger.warning("OpenTelemetry unavailable (%s); using JSONL traces only", _init_error)
    return _ready


def begin_request(trace_id: str, query: str, start_ts: float) -> None:
    """Open the root span for one request trace."""
    if not init_tracing():
        return
    try:
        root = _tracer.start_span("rag.request", start_time=_ns(start_ts),
                                  attributes={"rag.trace_id": trace_id, "rag.query": _to_attr(query)})
        with _lock:
            if len(_roots) > 5000:        # safety valve for traces that never complete
                _roots.clear()
            _roots[trace_id] = root
    except Exception:
        logger.debug("begin_request failed", exc_info=True)


def emit_span(trace_id: str, span_id: str, name: str, start_ts: float, end_ts: float,
              attributes: Dict[str, Any], status: str, error: Optional[str],
              parent_span_id: Optional[str]) -> None:
    """Export one finished application span as an OTel span under the request root."""
    if not init_tracing():
        return
    try:
        from opentelemetry import trace
        from opentelemetry.trace import Status, StatusCode

        parent = _emitted_ctx.get(parent_span_id) if parent_span_id else None
        if parent is None:
            root = _roots.get(trace_id)
            parent = trace.set_span_in_context(root) if root is not None else None
        span = _tracer.start_span(name, context=parent, start_time=_ns(start_ts))
        for key, value in (attributes or {}).items():
            span.set_attribute(f"rag.{key}", _to_attr(value))
        if status == "ERROR":
            span.set_status(Status(StatusCode.ERROR, _to_attr(error or "error")))
            if error:
                span.set_attribute("rag.error", _to_attr(error))
        else:
            span.set_status(Status(StatusCode.OK))
        with _lock:
            _emitted_ctx[span_id] = trace.set_span_in_context(span)
            if len(_emitted_ctx) > 5000:
                _emitted_ctx.clear()
        span.end(end_time=_ns(end_ts))
    except Exception:
        logger.debug("emit_span failed", exc_info=True)


def end_request(trace_id: str, end_ts: float, status: str, totals: Dict[str, Any]) -> None:
    """Close the request root span with aggregate attributes."""
    if not _ready:
        return
    try:
        from opentelemetry.trace import Status, StatusCode
        with _lock:
            root = _roots.pop(trace_id, None)
        if root is None:
            return
        for key, value in totals.items():
            root.set_attribute(f"rag.{key}", _to_attr(value))
        root.set_status(Status(StatusCode.ERROR if status == "FAILED" else StatusCode.OK))
        root.end(end_time=_ns(end_ts))
    except Exception:
        logger.debug("end_request failed", exc_info=True)


def tracing_status() -> Dict[str, Any]:
    """Live facts for the System page (what is actually loaded, not just configured)."""
    ready = init_tracing()
    info: Dict[str, Any] = {
        "active": ready,
        "service_name": OTEL_SERVICE_NAME,
        "exporters": [],
        "spans_exported": 0,
        "error": _init_error,
    }
    if ready:
        try:
            from importlib.metadata import version
            info["sdk_version"] = version("opentelemetry-sdk")
        except Exception:
            info["sdk_version"] = "unknown"
        info["exporters"].append({"type": "jsonl", "path": str(OTEL_SPANS_PATH)})
        if _otlp_endpoint_active:
            info["exporters"].append({"type": "otlp-http", "endpoint": _otlp_endpoint_active})
        info["spans_exported"] = getattr(_jsonl_exporter, "exported", 0)
    return info


def self_test() -> Dict[str, Any]:
    """Emit a span and confirm the exporter really received it."""
    if not init_tracing():
        return {"ok": False, "detail": _init_error or "OpenTelemetry SDK not available"}
    before = getattr(_jsonl_exporter, "exported", 0)
    now = time.time()
    emit_span("selftest", f"selftest_{int(now * 1000)}", "otel.self_test", now, now + 0.001,
              {"purpose": "health-check"}, "OK", None, None)
    after = getattr(_jsonl_exporter, "exported", 0)
    return {"ok": after > before, "detail": f"exporter count {before} -> {after}", "path": str(OTEL_SPANS_PATH)}
