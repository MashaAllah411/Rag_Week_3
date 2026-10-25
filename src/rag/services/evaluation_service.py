"""
evaluation_service.py

Service layer orchestrating:
- Week 6 Deterministic Regex Assertions (Claim number format, Date of loss, Numeric deductible, Exclusion clause)
- LLM Judge V1 & V2 prompt calibration
- Agreement analysis before vs after few-shot calibration
"""
from __future__ import annotations
import os
import re
import json
from typing import Dict, Any, List, Optional

from rag.config import DATA_DIR
import ollama
from rag.config import OLLAMA_MODEL


# ── Deterministic Assertions ─────────────────────────────────

def assert_claim_number_format(text: str) -> bool:
    """Verifies that a valid claim ID pattern (e.g. CLM-2024-00123 or CLM-7001) exists."""
    pattern = r'\bCLM-(?:20\d{2}-\d{4,5}|\d{4})\b'
    return bool(re.search(pattern, text))


def assert_date_of_loss_present(text: str) -> bool:
    """Verifies that an incident date exists in YYYY-MM-DD or MM/DD/YYYY format."""
    patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',
        r'\b\d{1,2}/\d{1,2}/\d{4}\b',
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b'
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def assert_numeric_deductible(text: str) -> bool:
    """Verifies that a dollar/currency deductible or payout is explicitly cited."""
    pattern = r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\b\d+(?:\.\d{2})?\s*(?:dollars|USD)\b'
    return bool(re.search(pattern, text, re.IGNORECASE))


def assert_exclusion_clause_cited(text: str, is_denial: bool = True) -> bool:
    """Verifies that if a claim is denied, a specific Section or Clause is cited."""
    if not is_denial:
        return True
    pattern = r'\b(?:Section|Clause|Article|Endorsement)\s+\d+(?:\.\d+)*\b'
    return bool(re.search(pattern, text, re.IGNORECASE))


def run_deterministic_assertions(text: str, is_denial: bool = False) -> Dict[str, Any]:
    """Runs all 4 assertions on a given text."""
    c_num = assert_claim_number_format(text)
    d_loss = assert_date_of_loss_present(text)
    n_ded = assert_numeric_deductible(text)
    e_clause = assert_exclusion_clause_cited(text, is_denial=is_denial)

    passed_count = sum([c_num, d_loss, n_ded, e_clause])
    return {
        "claim_number_format": c_num,
        "date_of_loss_present": d_loss,
        "numeric_deductible_present": n_ded,
        "exclusion_clause_cited": e_clause,
        "passed_count": passed_count,
        "total_assertions": 4,
        "all_passed": passed_count == 4
    }


# ── LLM Judge V1 & V2 Prompt Calibration ──────────────────────

def get_judge_prompts() -> Dict[str, str]:
    """Return Judge V1 and V2 prompt templates."""
    v1_path = os.path.join(DATA_DIR, "prompts", "judge_v1.txt")
    v2_path = os.path.join(DATA_DIR, "prompts", "judge_v2.txt")

    v1_text = ""
    v2_text = ""
    if os.path.exists(v1_path):
        with open(v1_path, "r", encoding="utf-8") as f:
            v1_text = f.read()
    if os.path.exists(v2_path):
        with open(v2_path, "r", encoding="utf-8") as f:
            v2_text = f.read()

    return {"judge_v1": v1_text, "judge_v2": v2_text}


def run_judge_evaluation(
    query: str,
    context: str,
    answer: str,
    judge_version: str = "v2"
) -> Dict[str, Any]:
    """Runs LLM Judge V1 or V2 on an answer."""
    prompts = get_judge_prompts()
    template = prompts.get(f"judge_{judge_version}") or prompts["judge_v2"]

    formatted_prompt = template.format(
        query=query,
        context=context,
        answer=answer
    )

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": formatted_prompt}],
            options={"temperature": 0.0}
        )
        content = response["message"]["content"].strip()
        verdict = 1 if "VERDICT: 1" in content or "VERDICT: PASS" in content.upper() else 0
        return {
            "judge_version": judge_version,
            "verdict": verdict,
            "verdict_label": "PASS" if verdict == 1 else "FAIL",
            "raw_judge_response": content
        }
    except Exception as e:
        return {
            "judge_version": judge_version,
            "verdict": 0,
            "verdict_label": "ERROR",
            "raw_judge_response": f"Judge call failed: {e}"
        }


# ── Week 6: judge validation against human labels ────────────

def get_judge_validation() -> Dict[str, Any]:
    """Compare the LLM judge's recorded verdicts with the human ground-truth labels.

    The saved analysis lists the cases where Judge V1 disagreed with the human. Judge V2's
    per-case verdicts were not persisted, so V2 agreement needs a live run (requires Ollama).
    """
    labels_path = os.path.join(DATA_DIR, "labels_25.json")
    dis_path = os.path.join(DATA_DIR, "disagreements_analysis.json")
    result: Dict[str, Any] = {"available": False}
    if not os.path.exists(labels_path):
        return result
    with open(labels_path, "r", encoding="utf-8") as f:
        labels_doc = json.load(f)
    labels = labels_doc.get("labels", {})
    disagreements: List[Dict[str, Any]] = []
    if os.path.exists(dis_path):
        with open(dis_path, "r", encoding="utf-8") as f:
            disagreements = json.load(f)
    total = len(labels)
    agree_v1 = total - len(disagreements)
    result.update({
        "available": True,
        "criterion": labels_doc.get("criterion", ""),
        "labelled_at": labels_doc.get("timestamp", ""),
        "total_cases": total,
        "human_pass": sum(1 for v in labels.values() if v == 1),
        "human_fail": sum(1 for v in labels.values() if v == 0),
        "judge_v1_agreement_pct": round(100.0 * agree_v1 / total, 1) if total else 0.0,
        "judge_v1_disagreements": disagreements,
        "judge_v2_note": "Judge V2 verdicts per case were not saved. Re-run the suite with Ollama running to measure V2 agreement.",
        "trust_threshold_pct": 80.0,
    })
    result["judge_v1_trusted"] = result["judge_v1_agreement_pct"] >= result["trust_threshold_pct"]
    return result


# ── Week 6: which eval datasets fit the current index ────────

def get_dataset_status() -> List[Dict[str, Any]]:
    """Describe each eval dataset and whether it can be scored against the current index."""
    from rag.config import EVALUATION_DATASET_PATH
    from rag.storage.vectorstore import get_vector_store
    out: List[Dict[str, Any]] = []
    try:
        data = get_vector_store()._collection().get(include=[])
        indexed_ids = set(data["ids"])
    except Exception:
        indexed_ids = set()

    if os.path.exists(EVALUATION_DATASET_PATH):
        with open(EVALUATION_DATASET_PATH, "r", encoding="utf-8") as f:
            hist = json.load(f)
        wanted = {c for q in hist for c in q.get("relevant_chunks", [])}
        out.append({
            "name": "Historical chunk-id dataset (Weeks 4-6)",
            "file": "data/evaluation_dataset.json",
            "questions": len(hist),
            "corpus": "earlier HR-policy PDF (no longer in resources/)",
            "ground_truth": "chunk ids such as chunk_107",
            "usable_on_current_index": bool(wanted & indexed_ids),
            "reason": ("" if wanted & indexed_ids else
                       "None of its chunk ids exist in the current index (ids are now 'document:chunk_N'), and its questions ask about a different document. Kept for the historical before/after record only."),
        })
    ins_path = os.path.join(DATA_DIR, "evaluation_dataset_insurance.json")
    if os.path.exists(ins_path):
        with open(ins_path, "r", encoding="utf-8") as f:
            ins = json.load(f)
        out.append({
            "name": "Insurance phrase dataset (current corpus)",
            "file": "data/evaluation_dataset_insurance.json",
            "questions": len(ins),
            "corpus": "current insurance PDFs in resources/",
            "ground_truth": "the phrase that answers each question",
            "usable_on_current_index": True,
            "reason": "Phrases were checked against the indexed text when the set was authored. Small set: treat differences of one question as noise.",
        })
    return out
