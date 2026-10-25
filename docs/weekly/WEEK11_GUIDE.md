# 🛠️ Week 11 Implementation Guide — Production Observability, Cost & the Failure → Test Loop

## Track D: Insurance Claims
> *"Find the coverage answer that ignored an exclusion."*

👉 **[Read the Full Week 11 Concepts Master Guide (All 12 Topics Deep Dive)](file:///d:/AI/Masha%20Week%205/Rag_Week_3/documentation/WEEK11_CONCEPTS_MASTER_GUIDE.md)**

---

## 📋 Submission Checklist & Deliverables

| Deliverable | Requirement | Location / Artifact | Status |
|---|---|---|---|
| **1. Per-Request Logging & Spans** | Discrete time and cost per step (not just one lump sum) | [`src/rag/observability/tracer.py`](file:///d:/AI/Masha%20Week%205/Rag_Week_3/src/rag/observability/tracer.py)<br>[`traces/production_traces.jsonl`](file:///d:/AI/Masha%20Week%205/Rag_Week_3/traces/production_traces.jsonl) | **PASS** |
| **2. The Support Drill** | Find planted bad answer from vague complaint | [`src/rag/observability/support_drill.py`](file:///d:/AI/Masha%20Week%205/Rag_Week_3/src/rag/observability/support_drill.py) | **PASS** |
| **3. Measured Cost Improvement** | Measure cost per query; cut via semantic cache | [`src/rag/cache/semantic_cache.py`](file:///d:/AI/Masha%20Week%205/Rag_Week_3/src/rag/cache/semantic_cache.py) | **PASS** |
| **4. Failure → Test Loop** | Convert production failure into permanent test | [`tests/test_failure_loop_regression.py`](file:///d:/AI/Masha%20Week%205/Rag_Week_3/tests/test_failure_loop_regression.py) | **PASS** |
| **5. The 10× Scaling Plan** | Bottleneck analysis and mitigation architecture | [`documentation/ten_x_plan.md`](file:///d:/AI/Masha%20Week%205/Rag_Week_3/documentation/ten_x_plan.md) | **PASS** |
| **6. Single-Command Suite** | Automated evaluation script | [`run_week11_eval.py`](file:///d:/AI/Masha%20Week%205/Rag_Week_3/run_week11_eval.py) | **PASS** |

---

## 🚀 How to Run the Week 11 Evaluation Suite

Run the complete evaluation suite with a single command:

```powershell
python run_week11_eval.py
```

To run the permanent regression test with pytest:

```powershell
pytest tests/test_failure_loop_regression.py -v
```

---

## 🔍 How the Support Drill Works (Track D)

1. **Vague Complaint:** *"A customer complained yesterday that a basement flood claim was approved with a \$14,500 payout, even though adjuster notes showed rising lake water which is excluded under Section 5.2."*
2. **Search:** The diagnostic tool loads the 100 production traces and searches across spans, notes, and outcomes.
3. **Pinpointed Result:** Identifies `trace_id: tr_drill_exclusion_7701` (`CLM-FAIL-7701`).
4. **Root Cause:** Identifies that span `reasoning:policy_exclusion_check` misclassified rising lake water as covered accidental plumbing overflow, ignoring Section 5.2.
5. **Remediation & Regression Test:** Turned into `test_planted_failure_case_clm_fail_7701_is_denied()` in `tests/test_failure_loop_regression.py`.
