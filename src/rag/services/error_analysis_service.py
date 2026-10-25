"""Week 5 error analysis: read a fair sample of real traces, take notes, group, and rank.

Method (per the task brief):
  1. Take a random sample (seeded, so it is reproducible and not cherry-picked).
  2. Write one honest note per trace BEFORE choosing categories (open coding).
  3. Group notes into named problem types and rank them by frequency x severity.
  4. Write a prediction for the fix you will try next, before you try it.
"""
from __future__ import annotations

import json
import os
import random
import threading
from typing import Any, Dict, List

from rag.config import DATA_DIR
from rag.observability.tracer import DEFAULT_TRACES_PATH

_STORE = os.path.join(str(DATA_DIR), "error_analysis.json")
_lock = threading.Lock()


def _load_store() -> Dict[str, Any]:
    if os.path.exists(_STORE):
        with open(_STORE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"notes": {}, "prediction": ""}


def _save_store(store: Dict[str, Any]) -> None:
    with open(_STORE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def _load_traces() -> List[Dict[str, Any]]:
    if not os.path.exists(DEFAULT_TRACES_PATH):
        return []
    traces = []
    with open(DEFAULT_TRACES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    traces.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return traces


def sample_traces(n: int = 20, seed: int = 42) -> Dict[str, Any]:
    """Seeded random sample of real request traces, with any notes already written."""
    traces = _load_traces()
    store = _load_store()
    picked = random.Random(seed).sample(traces, min(n, len(traces))) if traces else []
    items = []
    for t in picked:
        tid = t.get("trace_id")
        items.append({
            "trace_id": tid, "timestamp": t.get("timestamp"), "query": t.get("query"),
            "retriever_type": t.get("retriever_type"),
            "retrieved_chunks": t.get("retrieved_chunks", []),
            "answer": t.get("raw_llm_output", ""),
            "note": store["notes"].get(tid, {}),
        })
    return {"seed": seed, "requested": n, "population": len(traces), "sample": items,
            "prediction": store.get("prediction", "")}


def save_note(trace_id: str, note: str, category: str, severity: int) -> Dict[str, Any]:
    with _lock:
        store = _load_store()
        store["notes"][trace_id] = {"note": note.strip(), "category": category.strip(), "severity": int(severity)}
        _save_store(store)
    return store["notes"][trace_id]


def save_prediction(text: str) -> str:
    with _lock:
        store = _load_store()
        store["prediction"] = text.strip()
        _save_store(store)
    return store["prediction"]


def taxonomy() -> Dict[str, Any]:
    """Group notes by category and rank by frequency x average severity."""
    store = _load_store()
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for tid, entry in store["notes"].items():
        if entry.get("category"):
            groups.setdefault(entry["category"], []).append({"trace_id": tid, **entry})
    ranked = []
    for name, entries in groups.items():
        avg_sev = sum(e["severity"] for e in entries) / len(entries)
        ranked.append({"category": name, "count": len(entries), "avg_severity": round(avg_sev, 2),
                       "score": round(len(entries) * avg_sev, 2),
                       "examples": [e["note"] for e in entries[:3]]})
    ranked.sort(key=lambda r: r["score"], reverse=True)
    noted = len(store["notes"])
    return {"notes_written": noted, "categories": ranked,
            "fix_target": ranked[0]["category"] if ranked else None,
            "prediction": store.get("prediction", "")}
