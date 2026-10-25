# ⚖️ Week 6 Implementation & LLM Judge Validation Guide

## Overview

Week 6 focuses on **LLM Judge Validation & Assertion Splitting**:
> *"Validate the claim-summary judge before you trust its number."*

Rather than blindly trusting an LLM judge prompt or paying an LLM to check regex formats (like `CLM-YYYY-NNNNN`), Week 6 implements:
1. **25-Case Taxonomy & Regression Suite** (`taxonomy_eval_set.json`).
2. **4 Deterministic Assertions vs 1 Judged Criterion Split** (`eval_assertions.py`).
3. **Blind Human Protocol** (`labels_25.json` committed to Git FIRST).
4. **Judge V1 vs V2 Prompt Calibration** with few-shot disagreement learning.
5. **Single-Command Evaluation** (`evaluate_all.py`).

---

## Key Metrics Achieved

| Metric | Output Value |
|---|---|
| **Deterministic Assertions Count** | `4` (`claim_number`, `date_of_loss`, `numeric_deductible`, `exclusion_clause`) |
| **LLM Judged Criteria Count** | `1` (Single Binary Grounded Summary Criterion) |
| **`agreement_before` (Judge V1)** | **`60.0%`** (15 / 25 matches with human labels) |
| **`agreement_after` (Judge V2)** | **`64.0%`** (16 / 25 matches with human labels) |
| **Net Agreement Delta** | **`+4.0%`** |

---

## 📋 Pass Rate Breakdown by Week-5 Taxonomy Mode

| Week-5 Taxonomy Mode | Total Cases | Passed Cases | Pass Rate % |
|---|---|---|---|
| `edition_confusion` | 2 | 0 | 0.0% |
| `llm_false_negative` | 2 | 0 | 0.0% |
| `missing_policy_section` | 7 | 3 | 42.9% |
| `out_of_scope_fallback` | 3 | 0 | 0.0% |
| `query_rewriter_drift` | 3 | 0 | 0.0% |
| `success` | 8 | 5 | 62.5% |

---

## 🛠️ Submission Checklist Verification

- [x] `labels_25.json` committed FIRST (`commit hash: e88dd18`) to prove blind protocol.
- [x] `judge_v1.txt` and `judge_v2.txt` diffable, with 2 disagreement examples visible in v2.
- [x] `prediction.txt` filed and committed BEFORE iterating judge prompt (`commit hash: b30181b`).
- [x] Single command `python evaluate_all.py` prints pass rate by taxonomy mode.
- [x] `agreement_before` (60.0%) and `agreement_after` (64.0%) reported along with 4 assertions vs 1 judge criterion split.
- [x] Disagreement case studies and honest prediction scoring documented in `notes_w6.md`.

---

## 💻 Commands to Run

```bash
# Run Complete Week 6 Evaluation Suite (One Command)
python evaluate_all.py

# Check Blind Protocol Commit History
git log --oneline -n 5
```
