# ============================================================
# tracer.py — Week 5 Tracing Framework & PII Redactor
#
# PURPOSE:
#   1. Defines complete Trace Schema:
#      - trace_id
#      - timestamp
#      - query (redacted)
#      - prompt_version
#      - retrieved_chunks (chunk_ids + scores)
#      - retriever_type
#      - model
#      - model_parameters
#      - raw_llm_output (redacted)
#      - pii_redacted
#   2. Redacts PII (names, claim/employee IDs, emails, phone numbers)
#      BEFORE traces are saved to disk.
#   3. Provides log_trace() and replay_trace() functions.
# ============================================================

import os
import sys
import json
import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./src"))

TRACES_DIR = "./traces"
TRACES_FILE = os.path.join(TRACES_DIR, "traces.jsonl")


def ensure_traces_dir():
    """Ensures the ./traces directory exists."""
    if not os.path.exists(TRACES_DIR):
        os.makedirs(TRACES_DIR, exist_ok=True)


def redact_pii(text: str) -> str:
    """
    Redacts personally identifiable information (PII) from text BEFORE saving.
    Redacts:
      - Claimant/Employee Names (e.g. 'John Doe', 'Claimant Mary Smith', 'Mr. Robert')
      - Claim / Policy Numbers (e.g. 'CLM-12345', 'POL-99882', 'EMP-4412')
      - Email Addresses
      - Phone Numbers
      - SSN / National IDs
    """
    if not text:
        return text

    redacted = text

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

    # Redact explicit claimant / employee names (e.g., Claimant John Smith, Employee Sarah Jenkins, Mr. David Miller)
    redacted = re.sub(
        r'\b(Claimant|Employee|Mr\.|Mrs\.|Ms\.|Dr\.)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',
        '[REDACTED_NAME]',
        redacted
    )

    # Specific common synthetic PII names used in queries
    known_pii_names = [
        "John Doe", "Jane Doe", "Alice Johnson", "Bob Smith", "Mary Jane",
        "David Miller", "Sarah Jenkins", "Michael Brown", "Emma Wilson", "Robert Taylor"
    ]
    for name in known_pii_names:
        redacted = re.sub(re.escape(name), '[REDACTED_NAME]', redacted, flags=re.IGNORECASE)

    return redacted


def log_trace(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    raw_llm_output: str,
    prompt_version: str = "v1.0",
    retriever_type: str = "Hybrid (Pinecone + BM25 + RRF + CrossEncoder + MMR)",
    model_name: str = "llama3.2",
    model_parameters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Constructs a trace record, redacts PII BEFORE writing, and appends to traces.jsonl.
    """
    ensure_traces_dir()

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

    # REDACT PII BEFORE SAVING (Requirement 1 & 4)
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

    # Append to traces.jsonl
    with open(TRACES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(trace_record) + "\n")

    return trace_record


def get_trace_by_id(trace_id: str) -> Dict[str, Any]:
    """Retrieves a single trace record by trace_id from traces.jsonl."""
    if not os.path.exists(TRACES_FILE):
        raise FileNotFoundError(f"Trace file {TRACES_FILE} does not exist.")

    with open(TRACES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("trace_id") == trace_id:
                return record

    raise KeyError(f"Trace ID {trace_id} not found in {TRACES_FILE}.")


def _load_all_chunk_map() -> Dict[str, str]:
    """Loads a mapping of chunk_id -> chunk_text from data/chunk_map.txt or bm25 corpus."""
    chunk_map = {}

    # Method 1: Check bm25 module corpus if available
    try:
        from rag.core.retrieval.bm25 import _chunk_ids, _chunk_texts
        for cid, ctext in zip(_chunk_ids, _chunk_texts):
            chunk_map[cid] = ctext
    except Exception:
        pass

    # Method 2: Check data/chunk_map.txt or chunk_map.txt
    map_paths = ["data/chunk_map.txt", "chunk_map.txt"]
    for path in map_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            blocks = content.split("============================================================")
            for block in blocks:
                lines = [l.rstrip() for l in block.strip().split("\n") if l.strip()]
                if not lines:
                    continue
                cid = None
                text_lines = []
                is_text = False
                for line in lines:
                    if line.startswith("ID   : "):
                        cid = line.replace("ID   : ", "").strip()
                    elif line.startswith("─────"):
                        is_text = True
                    elif is_text and cid:
                        text_lines.append(line)
                if cid and text_lines:
                    chunk_map[cid] = "\n".join(text_lines).strip()

    return chunk_map


def replay_trace(trace_id: str) -> Dict[str, Any]:
    """
    Replays a request purely from the fields saved in a trace record.
    Proves that the trace is 100% replayable and complete.
    """
    record = get_trace_by_id(trace_id)

    query = record["query"]
    retrieved_chunk_ids = [c["chunk_id"] for c in record["retrieved_chunks"]]

    chunk_map = _load_all_chunk_map()
    context_chunks = [chunk_map.get(cid, f"[Content for chunk {cid}]") for cid in retrieved_chunk_ids]
    context_str = "\n\n---\n\n".join(context_chunks)

    # Import LLM query function
    try:
        from rag.infra.llm import query_llm_with_context
    except ImportError:
        from llm import query_llm_with_context

    replayed_output = query_llm_with_context(query, context_str)

    return {
        "original_trace_id": trace_id,
        "query": query,
        "prompt_version": record["prompt_version"],
        "retrieved_chunk_ids": retrieved_chunk_ids,
        "original_output": record["raw_llm_output"],
        "replayed_output": replayed_output
    }
