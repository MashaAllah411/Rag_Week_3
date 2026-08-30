# Week 6 Disagreement Analysis & Judge Validation Notes — Task Set D

## 1. Disagreement Analysis (2 Detailed Case Studies)

### Case Study 1: `eval_11` (Out-of-Scope Fallback)
- **Question:** *"Does the policy cover home office electricity and internet bills?"*
- **RAG Generated Output:** *"I don't know based on the provided documents."*
- **Human Label:** `1` (PASS)
- **Judge V1 Verdict:** `0` (FAIL)
- **Verdict on Who Was Right:** **HUMAN WAS RIGHT.** Home office utility reimbursement is not mentioned anywhere in the HR policy document. Returning *"I don't know based on the provided documents"* is the exact expected, grounded behavior to prevent hallucination. Judge V1 incorrectly penalized the model for returning an IDK fallback on an out-of-scope query.

### Case Study 2: `eval_01` (Regression Case — Notice Period Duration)
- **Question:** *"What is the required notice period for resignation?"*
- **RAG Generated Output:** *"Section 5.2.7 Carry forward of leave and Section 5.2.8 Leaving the organization do not directly address the required notice..."*
- **Human Label:** `0` (FAIL)
- **Judge V1 Verdict:** `1` (PASS)
- **Verdict on Who Was Right:** **HUMAN WAS RIGHT.** Section 10.1 of the HR Policy explicitly mandates a 4-week written notice period (`chunk_227`). The RAG system retrieved generic separation chunks and failed to deliver the required duration. Judge V1 was fooled by the polite tone of the answer and gave a false-positive PASS verdict.

---

## 2. Prediction vs. Outcome Evaluation

- **Prediction (written in `prediction.txt` before prompt iteration):**
  > *"Adding few-shot examples of judge-human disagreements (specifically false-negative fallbacks when context is present, and out-of-scope question handling) will increase judge-human agreement from around 76% to above 88% by correcting the judge's tendency to mark accurate out-of-scope fallback responses as failures."*

- **Empirical Results:**
  - `agreement_before` (Judge V1): **60.0%** (15/25 matches)
  - `agreement_after` (Judge V2): **64.0%** (16/25 matches)
  - Net Delta: **+4.0%**

- **Where the Prediction Was Wrong:**
  1. **Baseline Overestimate:** The baseline agreement was predicted to be ~76%, but was actually **60.0%** because Judge V1 severely struggled with binary fallback nuances.
  2. **Magnitude Overestimate:** The predicted agreement increase (+12%) was much larger than the actual empirical gain (**+4.0%**). While Judge V2 successfully fixed out-of-scope handling for `eval_12`, it still misclassified ambiguous one-word queries (`eval_16`, `eval_17`), showing that prompt-only few-shot iteration has limits without deterministic boundary rules.

---

## 3. Deterministic Assertions vs. LLM Judged Criteria Split

- **Deterministic Assertions Count:** `4`
  1. `assert_claim_number_format` — Validates `CLM-YYYY-NNNNN` or `CLM-XXXXX` regex pattern.
  2. `assert_date_of_loss_present` — Validates presence of parseable dates (`YYYY-MM-DD`).
  3. `assert_numeric_deductible` — Validates numeric excess/deductible figures.
  4. `assert_exclusion_clause_cited` — Validates section/clause citation on denials.
- **LLM Judged Criteria Count:** `1` (Single Binary Grounded Summary Criterion).
- **Ratio:** **4 Assertions vs 1 Judged Criterion**.

---

## 4. Public Benchmark Analysis (3 Sentences)

1. Public benchmarks evaluate LLM judges using clean, balanced open-domain QA pairs rather than domain-specific RAG contexts where subtle false-negative fallbacks occur.
2. Standard benchmark accuracy metrics score surface-level agreement across generic prompts, completely hiding severe failure modes like misclassifying legitimate out-of-scope "I don't know" responses.
3. A high public benchmark score provides zero guarantee that an LLM judge will align with human ops team verdicts on multi-document cross-talk or policy edition conflicts.
