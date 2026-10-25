# 🧭 Week 8 Implementation & Trajectory Evaluation Guide

## Overview

Week 8 addresses the **Outcome-vs-Trajectory Gap** in AI Agents:
> *"Score the path, expose the gap as a number, and kill your worst failure mode with the price tag attached."*

An outcome test checks if the final payout amount is correct. But if an agent reaches `$0` payout by guessing without ever opening policy exclusions, it represents a dangerous time bomb.

Week 8 implements:
1. **Trajectory Evaluation Suite (`src/rag/agent/trajectory_eval.py`)** with alternate valid path sets.
2. **Outcome-vs-Trajectory Gap Metric Calculation** ($\text{Gap} = \text{Outcome Pass Rate} - \text{Trajectory Pass Rate}$).
3. **Four Trajectory Numbers** (Tool Choice Acc, Arg Validity Rate, Step Efficiency Ratio, Cost P50 & MAX).
4. **Single Mitigation Application & Measured Price Paid**.
5. **Per-Mode Regression Check Table**.

---

## 📊 Summary Benchmark Metrics

| Metric | BEFORE Mitigation | AFTER Mitigation |
|---|---|---|
| **Outcome Pass Rate (%)** | `90.0%` | `100.0%` |
| **Trajectory Pass Rate (%)** | `60.0%` | `100.0%` |
| **Outcome-vs-Trajectory Gap (%)** | **`30.0%`** | **`0.0%`** |
| **Tool-Choice Accuracy (%)** | `60.0%` | `100.0%` |
| **Argument Validity Rate (%)** | `100.0%` | `100.0%` |
| **Step Efficiency Ratio** | `0.9500` | `0.7667` |
| **Cost P50 ($)** | `$0.001393` | `$0.001393` |
| **Cost MAX ($)** | `$0.001402` | `$0.001402` |
| **Top Failure Mode Count (`Unverified Exclusion Shortcut`)** | `4` | **`0`** (100% Closure) |
| **Measured Price Paid for Mitigation** | — | `+57` tokens total (`+0.0056s` latency P50) |

---

## 📋 Submission Checklist Verification

- [x] **10 Expected Tool Sequences in Code**: Defined in `src/rag/agent/trajectory_eval.py` with alternate valid path sets.
- [x] **Results Table**: Tool-choice accuracy, argument validity, step efficiency, cost P50 and MAX reported.
- [x] **Gap Number & Case Study**: Reported 30.0% gap and documented `CLM-7002` right-answer-wrong-path trace in `documentation/trajectory_notes.md`.
- [x] **Single Mitigation Diff & Price Paid**: Sharpened tool description in `src/rag/agent/tools.py`; measured `+57` tokens and `+0.0056s` latency.
- [x] **Per-Mode Regression Table**: Verified zero new or worsened failure modes in `run_week8_eval.py`.

---

## 💻 Commands to Run

```bash
# Run Complete Week 8 Trajectory Benchmark & Gap Analysis
python run_week8_eval.py
```
