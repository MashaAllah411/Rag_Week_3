# 🏎️ Week 7 Implementation Guide — Agent Loops & Fixed Workflows

## Overview

Week 7 addresses the foundational architectural question:
> *"Does this insurance claims task need a dynamic agent loop at all, or would 4 hard-coded steps be faster, cheaper, more auditable, and pass more tests?"*

Rather than relying on fashion or opinion, Week 7 settles the question with empirical benchmark data:
1. **Third Tool Addition (`compute_payout`)** with typed `ClaimStatusEnum` and zero description overlap.
2. **ReAct Agent Loop (`agent.py`)** with **4 Budgets Enforced in Code** (`MAX_ITERATIONS`, `MAX_TOKENS`, `MAX_COST`, `WALL_CLOCK_TIMEOUT`).
3. **Identical Fixed Workflow (`workflow.py`)** with hard-coded 4 sequential steps (no loop).
4. **10-Claim Race Benchmark (`race_benchmark.py`)** exporting `race.csv` with the 8 numbers.
5. **Verdict Document (`documentation/verdict.txt`)** applying the architectural decision rule.

---

## 📊 Race Benchmark Results (The 8 Numbers)

| Metric | Agent Loop | Fixed Workflow | Delta / Winner |
|---|---|---|---|
| **Pass Rate (%)** | **100.0%** | **100.0%** | Tie (10/10 claims passed) |
| **P50 Latency (seconds)** | **0.2793s** | **0.0000s** | **Fixed Workflow (Faster)** |
| **Total Tokens** | **6,960** | **3,834** | **Fixed Workflow (44.9% Fewer Tokens)** |
| **Cost Per Claim ($)** | **$0.001392** | **$0.000767** | **Fixed Workflow (44.9% Cheaper)** |

---

## 🛡️ Enforced Execution Budgets (`agent.py`)

All 4 budgets are strictly checked inside the ReAct loop on every lap:

```python
MAX_ITERATIONS = 5               # Laps limit
MAX_TOKENS = 4000                # Summed per-lap tokens
MAX_COST = 0.05                  # Dollars ($)
WALL_CLOCK_TIMEOUT = 30.0        # Seconds
```

When any limit is exceeded, the loop terminates cleanly and logs the event (see `budget_termination.log`).

---

## 📋 Submission Checklist Verification

- [x] **Agent and Workflow both runnable by one command each**: `python src/rag/agent/agent.py` and `python src/rag/agent/workflow.py`.
- [x] **`race.csv` created**: Contains all 8 comparative numbers over the same 10 claims.
- [x] **`budget_termination.log` created**: Shows log excerpt when `MAX_TOKENS` budget fires.
- [x] **`documentation/tool_diff.md` created**: Contains 3rd tool description and parameter Enum metadata.
- [x] **`documentation/verdict.txt` created**: Verdict paragraph under 150 words applying the decision rule.

---

## 💻 Commands to Run

```bash
# Run Complete Week 7 Agent vs Workflow Race Benchmark
python race_benchmark.py

# Test Agent Loop Directly
python src/rag/agent/agent.py

# Test Fixed Workflow Directly
python src/rag/agent/workflow.py
```
