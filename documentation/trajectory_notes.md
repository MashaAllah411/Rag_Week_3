# Week 8 Trajectory Evaluation Notes — Task Set D

## 1. Outcome-vs-Trajectory Gap Analysis

- **Outcome Pass Rate (BEFORE Mitigation):** `90.0%` (9 out of 10 claims reached correct payout number)
- **Trajectory Pass Rate (BEFORE Mitigation):** `60.0%` (6 out of 10 claims took a valid tool execution path)
- **Outcome-vs-Trajectory Gap Number:** **`30.0%`** ($\text{Outcome Pass Rate} - \text{Trajectory Pass Rate}$)

---

## 2. Right-Answer-Wrong-Path Case Study (`CLM-7002`)

### Claim Overview:
- **Claim ID:** `CLM-7002` (Claimant: *Robert Vance*)
- **Incident Type:** *Basement Water Damage*
- **Adjuster Notes:** *"Heavy torrential rainfall caused rising lake water and surface runoff to inundate basement. Excluded flood event under Section 5.2."*
- **Correct Payout:** `$0.00` (DENIED due to flood exclusion).

### Execution Trace BEFORE Mitigation (Wrong Path):
1. `Step 1`: Tool `get_claim("CLM-7002")` executed $\rightarrow$ returned gross claim `$12,000.00`, deductible `$1,000.00`, and adjuster notes mentioning rising lake water.
2. `Step 2`: Tool `compute_payout("CLM-7002", "DENIED", 12000.0, 1000.0)` executed $\rightarrow$ returned `$0.00` payout.
3. **CRITICAL PATH FAILURE:** The agent **never invoked `search_policy()`** to verify the flood exclusion in policy wording. It guessed the denial status and reached the right payout (`$0.00`) purely by luck.

### Execution Trace AFTER Mitigation (Correct Path):
1. `Step 1`: Tool `get_claim("CLM-7002")` executed.
2. `Step 2`: Tool `search_policy("flood rising water exclusion")` executed $\rightarrow$ verified `Section 5.2` flood exclusion in policy text.
3. `Step 3`: Tool `compute_payout("CLM-7002", "DENIED", 12000.0, 1000.0)` executed $\rightarrow$ returned `$0.00` payout with verified policy audit trail.

---

## 3. Four Trajectory Numbers (BEFORE vs. AFTER)

| Metric | BEFORE Mitigation | AFTER Mitigation | Net Change / Delta |
|---|---|---|---|
| **Tool-Choice Accuracy (%)** | **60.0%** | **100.0%** | **+40.0%** 🚀 |
| **Argument Validity Rate (%)** | **100.0%** | **100.0%** | **0.0%** (100% Valid) |
| **Step Efficiency Ratio** | **0.9500** | **0.7667** | **-0.1833** |
| **Cost P50 ($)** | **$0.001393** | **$0.001393** | **+$0.000000** |
| **Cost MAX ($)** | **$0.001402** | **$0.001402** | **+$0.000000** |
| **Latency P50 (seconds)** | **0.3685s** | **0.3741s** | **+0.0056s** |
| **Latency MAX (seconds)** | **66.3172s** | **0.4066s** | **-65.9106s** |
| **Total Tokens** | **6,903** | **6,960** | **+57 tokens** |

---

## 4. Single Mitigation & Price Paid Measurement

- **Target Failure Mode:** `Unverified Exclusion Shortcut` (Skipping `search_policy` on complex claims).
- **Single Mitigation Applied:** Sharpened tool trigger metadata in `src/rag/agent/tools.py` mandating policy exclusion verification whenever adjuster notes contain water, flood, or inventory loss keywords.
- **Before -> After Mode Count:** **`4 -> 0`** (100% Closure of failure mode).
- **Price Paid (Measured):**
  - **Added Tokens:** `+57` total tokens across suite (`+120` tokens per complex claim).
  - **Added Cost P50:** `+$0.000000` per claim.
  - **Added Latency P50:** `+0.0056` seconds per claim.

---

## 5. Per-Mode Regression Check Table

| Taxonomy Mode Name | Count BEFORE | Count AFTER | Status |
|---|---|---|---|
| **Unverified Exclusion Shortcut** | 4 | 0 | **CLOSED [PASS]** |
| **Invalid Tool Argument Fiction** | 0 | 0 | **NO REGRESSION** |
| **Unnecessary Loop Spinning** | 0 | 0 | **NO REGRESSION** |
| **Budget Exceeded Termination** | 0 | 0 | **NO REGRESSION** |
