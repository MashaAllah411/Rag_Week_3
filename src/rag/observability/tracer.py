# ============================================================
# src/rag/observability/tracer.py — Production Tracing, Spans & PII Redaction
#
# PURPOSE:
#   Implements production-grade observability and tracing:
#     1. Granular Span-level timing & token/dollar costing (OpenTelemetry compatible)
#     2. PII Redaction (names, IDs, emails, phone numbers) before logging
#     3. RequestTrace for complete end-to-end request tracking
#     4. Trace replay capability to re-run queries purely from logged context
#     5. Export to traces/production_traces.jsonl and traces/traces.jsonl
# ============================================================

from __future__ import annotations
import os
import re
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

# Token pricing defaults (e.g. GPT-4o-mini / Claude 3.5 Haiku class: $0.15/1M input, $0.60/1M output)
DEFAULT_INPUT_COST_PER_1K = 0.00015
DEFAULT_OUTPUT_COST_PER_1K = 0.00060

DEFAULT_PROD_TRACES_PATH = os.path.join("traces", "production_traces.jsonl")
DEFAULT_TRACES_PATH = os.path.join("traces", "traces.jsonl")


# ── PII Redaction ─────────────────────────────────────────────

def redact_pii(text: str) -> str:
    """
    Redacts personally identifiable information (PII) from text BEFORE saving.
    Redacts:
      - Claimant/Employee Names
      - Claim / Policy Numbers (e.g. 'CLM-12345', 'POL-99882', 'EMP-4412')
      - Email Addresses
      - Phone Numbers
    """
    if not text:
        return text

    redacted = str(text)

    # Redact Emails
    redacted = re.sub(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        '[REDACTED_EMAIL]',
        redacted
    )

    # Redact Phone Numbers
    redacted = re.sub(
        r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        '[REDACTED_PHONE]',
        redacted
    )

    # Redact Claim / Policy / Employee IDs (e.g. CLM-12345, EMP-9912, POL-77123)
    redacted = re.sub(
        r'\b(CLM|POL|EMP|ID|CLAIM|SSN)[-_]?\d{3,8}\b',
        '[REDACTED_ID]',
        redacted,
        flags=re.IGNORECASE
    )

    # Redact explicit claimant / employee names
    redacted = re.sub(
        r'\b(Claimant|Employee|Mr\.|Mrs\.|Ms\.|Dr\.)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',
        '[REDACTED_NAME]',
        redacted
    )

    # Specific common synthetic PII names
    known_pii_names = [
        "John Doe", "Jane Doe", "Alice Johnson", "Bob Smith", "Mary Jane",
        "David Miller", "Sarah Jenkins", "Michael Brown", "Emma Wilson", "Robert Taylor",
        "Alice Miller", "Robert Vance", "Carlos Gomez", "Diana Prince", "Edward Stark",
        "Fiona Gallagher", "George Clark", "Hannah Abbott", "Ian Malcolm", "Julia Roberts"
    ]
    for name in known_pii_names:
        redacted = re.sub(re.escape(name), '[REDACTED_NAME]', redacted, flags=re.IGNORECASE)

    return redacted


# ── Span & RequestTrace (Week 11 OpenTelemetry Model) ─────────

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

    def __init__(self, log_path: str = DEFAULT_PROD_TRACES_PATH):
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
                    try:
                        traces.append(json.loads(line))
                    except Exception:
                        continue
        return traces

    def find_trace_by_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific trace by its unique trace_id."""
        for t in self.load_all_traces():
            if t.get("trace_id") == trace_id:
                return t
        return None


# ── Week 5 Classic Tracing & Replay Functions ────────────────

def log_trace(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    raw_llm_output: str,
    prompt_version: str = "v1.0",
    retriever_type: str = "Hybrid (Pinecone + BM25 + RRF + CrossEncoder + MMR)",
    model_name: str = "llama3.2",
    model_parameters: Optional[Dict[str, Any]] = None,
    traces_file: str = DEFAULT_TRACES_PATH
) -> Dict[str, Any]:
    """
    Constructs a trace record, redacts PII BEFORE writing, and appends to traces.jsonl.
    """
    os.makedirs(os.path.dirname(traces_file), exist_ok=True)

    if model_parameters is None:
        model_parameters = {"temperature": 0.4, "top_p": 0.9}

    formatted_chunks = []
    for item in retrieved_chunks:
        chunk_id = item.get("id", item.get("chunk_id", "unknown"))
        score = item.get("rerank_score", item.get("rrf_score", item.get("score", 0.0)))
        formatted_chunks.append({
            "chunk_id": str(chunk_id),
            "score": round(float(score), 4)
        })

    trace_id = f"trc_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
    timestamp = datetime.now(timezone.utc).isoformat()

    redacted_query = redact_pii(query)
    redacted_output = redact_pii(raw_llm_output)

    trace_record = {
        "trace_id": trace_id,
        "timestamp": timestamp,
        "query": redacted_query,
        "prompt_version": prompt_version,
        "retrieved_chunks": formatted_chunks,
        "retriever_type": retriever_type,
        "model": model_name,
        "model_parameters": model_parameters,
        "raw_llm_output": redacted_output,
        "pii_redacted": True
    }

    with open(traces_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(trace_record) + "\n")

    return trace_record


def get_trace_by_id(trace_id: str, traces_file: str = DEFAULT_TRACES_PATH) -> Dict[str, Any]:
    """Retrieves a single trace record by trace_id from traces.jsonl."""
    # Check classic traces first, then production traces
    candidates = [traces_file, DEFAULT_PROD_TRACES_PATH]
    for path in candidates:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        if record.get("trace_id") == trace_id:
                            return record
                    except Exception:
                        continue

    raise KeyError(f"Trace ID {trace_id} not found.")


def replay_trace(trace_id: str, traces_file: str = DEFAULT_TRACES_PATH) -> Dict[str, Any]:
    """
    Replays a request purely from the fields saved in a trace record.
    """
    record = get_trace_by_id(trace_id, traces_file)
    query = record.get("query", "")
    retrieved_chunk_ids = [c["chunk_id"] for c in record.get("retrieved_chunks", [])]

    # Reconstruct context
    from rag.core.retrieval.bm25 import _ensure_index, _chunk_ids, _chunk_texts
    chunk_map = {}
    try:
        _ensure_index()
        for cid, ctext in zip(_chunk_ids, _chunk_texts):
            chunk_map[cid] = ctext
    except Exception:
        pass

    context_chunks = [chunk_map.get(cid, f"[Content for chunk {cid}]") for cid in retrieved_chunk_ids]
    context_str = "\n\n---\n\n".join(context_chunks)

    from rag.infra.llm import query_llm_with_context
    replayed_output = query_llm_with_context(query, context_str)

    return {
        "original_trace_id": trace_id,
        "query": query,
        "prompt_version": record.get("prompt_version", "v1.0"),
        "retrieved_chunk_ids": retrieved_chunk_ids,
        "original_output": record.get("raw_llm_output", ""),
        "replayed_output": replayed_output
    }
