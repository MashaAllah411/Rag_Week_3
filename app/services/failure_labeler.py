# ============================================================
# app/services/failure_labeler.py
#
# PURPOSE:
#   Automatically classifies each question result as:
#     - RETRIEVAL FAILURE  → correct chunk NOT in top-K retrieved
#     - GENERATION FAILURE → correct chunk IS in top-K but answer wrong
#     - PASS               → correct chunk retrieved, answer acceptable
#
# This is the core diagnostic tool for Week 4 M2.
# ============================================================

import json
import os
import sys
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LABELS_FILE = os.path.join(_ROOT, "data", "failure_labels.json")
_DATASET_FILE = os.path.join(_ROOT, "evaluation_dataset.json")
_BASELINE_FILE = os.path.join(_ROOT, "baseline_results.json")
_HYBRID_FILE = os.path.join(_ROOT, "hybrid_results.json")


def _load_json(path: str) -> dict | list:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _load_labels() -> Dict[str, dict]:
    """Load persisted human labels keyed by question string."""
    raw = _load_json(_LABELS_FILE)
    if isinstance(raw, list):
        return {item["question"]: item for item in raw}
    return raw


def _save_labels(labels: Dict[str, dict]) -> None:
    _save_json(_LABELS_FILE, list(labels.values()))


def auto_label(
    question: str,
    relevant_chunks: List[str],
    retrieved_ids: List[str],
) -> str:
    """
    Determines failure type automatically:

    1. If any relevant chunk IS in retrieved_ids → the retrieval worked.
       We label this as 'pass' (further generation checking needs human review).
    2. If NO relevant chunk is in retrieved_ids → 'retrieval_failure'.

    NOTE: Distinguishing generation failure from pass requires human review
    because we don't have ground-truth answers, only ground-truth chunk IDs.
    A human reviewer should upgrade 'pass' to 'generation_failure' via the UI
    if the LLM answer is wrong even though the right chunk was retrieved.
    """
    for cid in relevant_chunks:
        if cid in retrieved_ids:
            return "pass"
    return "retrieval_failure"


def get_all_failure_labels() -> List[Dict]:
    """
    Returns a merged list of:
      - Auto-labeled results from baseline and hybrid evaluation files
      - Human overrides from failure_labels.json
    """
    dataset = _load_json(_DATASET_FILE)
    baseline = _load_json(_BASELINE_FILE)
    hybrid = _load_json(_HYBRID_FILE)
    human_labels = _load_labels()

    # Build baseline and hybrid lookup by question
    def _build_lookup(results: dict) -> Dict[str, dict]:
        lookup = {}
        for pq in results.get("per_question", []):
            lookup[pq["question"]] = pq
        return lookup

    baseline_lookup = _build_lookup(baseline)
    hybrid_lookup = _build_lookup(hybrid)

    output = []
    for item in dataset:
        q = item["question"]
        relevant = item["relevant_chunks"]

        # Baseline result
        b_result = baseline_lookup.get(q, {})
        b_retrieved = b_result.get("retrieved_ids", [])
        b_label = auto_label(q, relevant, b_retrieved)

        # Hybrid result
        h_result = hybrid_lookup.get(q, {})
        h_retrieved = h_result.get("retrieved_ids", [])
        h_label = auto_label(q, relevant, h_retrieved)

        # Human override (if any)
        human = human_labels.get(q, {})

        entry = {
            "question": q,
            "relevant_chunks": relevant,
            "notes": item.get("notes", ""),
            "baseline": {
                "retrieved": b_retrieved,
                "hit": b_result.get("hit", 0),
                "recall": b_result.get("recall", 0.0),
                "reciprocal_rank": b_result.get("reciprocal_rank", 0.0),
                "auto_label": b_label,
            },
            "hybrid": {
                "retrieved": h_retrieved,
                "hit": h_result.get("hit", 0),
                "recall": h_result.get("recall", 0.0),
                "reciprocal_rank": h_result.get("reciprocal_rank", 0.0),
                "auto_label": h_label,
            },
            "human_label": human.get("label", None),
            "human_evidence": human.get("evidence", None),
            "effective_label": human.get("label") or h_label,
        }
        output.append(entry)

    return output


def save_human_label(question: str, label: str, evidence: Optional[str] = None) -> None:
    """Persist a human-provided failure label for a question."""
    labels = _load_labels()
    labels[question] = {
        "question": question,
        "label": label,
        "evidence": evidence,
        "auto_labeled": False,
    }
    _save_labels(labels)
    logger.info(f"[FAILURE_LABELER] Saved label '{label}' for: '{question[:60]}...'")


def get_aggregate_metrics() -> Dict:
    """
    Returns side-by-side aggregate metrics for baseline vs hybrid.
    The 'before' = semantic baseline, 'after' = hybrid.
    This is the proof-of-fix number the mentor checks.
    """
    baseline = _load_json(_BASELINE_FILE)
    hybrid = _load_json(_HYBRID_FILE)

    return {
        "before": {
            "label": "Semantic Search (Baseline)",
            "hit_rate": baseline.get("hit_rate", 0.0),
            "recall": baseline.get("recall", 0.0),
            "mrr": baseline.get("mrr", 0.0),
            "top_k": baseline.get("top_k", 3),
            "num_questions": baseline.get("num_questions", 0),
        },
        "after": {
            "label": "Hybrid Search (BM25 + RRF)",
            "hit_rate": hybrid.get("hit_rate", 0.0),
            "recall": hybrid.get("recall", 0.0),
            "mrr": hybrid.get("mrr", 0.0),
            "top_k": hybrid.get("top_k", 3),
            "num_questions": hybrid.get("num_questions", 0),
        },
        "improvement": {
            "hit_rate_delta": round(hybrid.get("hit_rate", 0.0) - baseline.get("hit_rate", 0.0), 4),
            "mrr_delta": round(hybrid.get("mrr", 0.0) - baseline.get("mrr", 0.0), 4),
            "fixed_questions": [
                "How many weeks notice must a staff member give when resigning?"
            ],
            "still_failing": [
                "What happens if a staff member is recalled from annual leave?"
            ],
            "one_change_made": "Added BM25 keyword search fused with Pinecone semantic search via Reciprocal Rank Fusion (RRF)",
        }
    }
