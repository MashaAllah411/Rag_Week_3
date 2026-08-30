# Week 5 Error Analysis Notes — Task Set D

## 1. Seeded Random Sample Details

- **Random Seed Value:** `42`
- **Total Trace Population:** `44`
- **Sample Size:** `20`
- **Sample Selection Command:** `python sample_traces.py`

### Selected 20 Trace IDs:
1. `trc_20260830_555cd901` — Query: "Does the policy cover home office electricity and..."
2. `trc_20260830_b9ca6585` — Query: "What happens if an employee is recalled from annua..."
3. `trc_20260830_24a5894d` — Query: "Are flexible working hours a guaranteed right for..."
4. `trc_20260830_1554a8e9` — Query: "What is the retirement age policy for full-time st..."
5. `trc_20260830_66e335ec` — Query: "How is overtime compensated for work performed dur..."
6. `trc_20260830_b581339b` — Query: "What is the policy for carrying forward unused ann..."
7. `trc_20260830_28189b78` — Query: "What is the paternity leave entitlement for male s..."
8. `trc_20260830_bc3702ab` — Query: "Can an employee take uncertified sick leave, and f..."
9. `trc_20260830_4a99b54f` — Query: "pension?..."
10. `trc_20260830_1bafba6e` — Query: "What is the required notice period for resignation..."
11. `trc_20260830_941c091d` — Query: "timing?..."
12. `trc_20260830_eb2810be` — Query: "What is the standard annual leave entitlement for..."
13. `trc_20260830_dcdb7013` — Query: "What is the claim payout limit for third-party pro..."
14. `trc_20260830_4b5ea250` — Query: "notice?..."
15. `trc_20260830_6afbd9a1` — Query: "Does GESCI cover dental insurance and cosmetic sur..."
16. `trc_20260830_572cc178` — Query: "What is the procedure for requesting an interest-f..."
17. `trc_20260830_2ff6bfd8` — Query: "What happens if an employee is absent without auth..."
18. `trc_20260830_5b4058bb` — Query: "[REDACTED_NAME] (ID [REDACTED_ID], email [REDACTED..."
19. `trc_20260830_ad2f0426` — Query: "What are the official working hours for GESCI staf..."
20. `trc_20260830_a6c98189` — Query: "How does the policy handle international relocatio..."

---

## 2. Replay Evidence & Verification

- **Target Trace ID:** `trc_20260830_1bafba6e`
- **Fields Present in Trace Schema:** `trace_id`, `timestamp`, `query`, `prompt_version`, `retrieved_chunks` (`chunk_id` + `score`), `retriever_type`, `model`, `model_parameters`, `raw_llm_output`, `pii_redacted`.
- **Fields Added / reconstructed:** None missing; all 10 required fields present in trace schema.

### Original vs Replayed Output Comparison:
- **Query from Trace:** `'What is the required notice period for resignation?'`
- **Original Output (from trace record):**
  > *"Section i. In the case of resignation, the date shall be either the date of expiration of the notice period or such other date as the CEO accepts. Answer: The required notice period for resignation is not explicitly stated..."*
- **Replayed Output (reconstructed from trace fields alone via `python test_replay.py`):**
  > *"I don't know based on the provided documents."*

---

## 3. PII Redaction Confirmation

**Confirmation:** All claimant/employee names, claim/policy IDs, phone numbers, and email addresses are sanitized using `redact_pii()` **BEFORE** the trace record is written to `traces/traces.jsonl`, not after writing.

---

## 4. 20 Verbatim Open-Coding Observation Sentences

*Rule: Exactly one observation sentence per trace describing what WAS SEEN, without diagnosis, categories, or code fixes.*

1. **`trc_20260830_555cd901`**: Output returned "I don't know based on the provided documents" because home office utility reimbursements are not mentioned in any of the retrieved HR policy chunks.
2. **`trc_20260830_b9ca6585`**: Retrieved chunks `doc_default_120`, `doc_default_104`, and `commercial-vehicles-package-policy-93ee460add:chunk_49` missed section 5.2.1 on annual leave recall, resulting in a fallback "I don't know" answer.
3. **`trc_20260830_24a5894d`**: Retrieved chunk `chunk_108` contained the text stating flexible working hours are not a right, but the LLM returned "I don't know based on the provided documents".
4. **`trc_20260830_1554a8e9`**: Retrieved chunks missed the retirement age section (10.3), leading the LLM to output "I don't know based on the provided documents".
5. **`trc_20260830_66e335ec`**: Retrieved chunks discussed standard working hours and separation pay but omitted weekend time-off allowance rules, producing "I don't know".
6. **`trc_20260830_b581339b`**: Retrieved `doc_default_117` and correctly answered that staff members shall not carry forward more than 5 days of annual leave beyond December 31st.
7. **`trc_20260830_28189b78`**: Retrieved `chunk_126` and correctly answered that male staff members are entitled to two weeks of paternity leave with full pay.
8. **`trc_20260830_bc3702ab`**: Retrieved `chunk_119` and correctly answered that employees can take up to seven working days of uncertified sick leave in an annual cycle.
9. **`trc_20260830_4a99b54f`**: Query rewriter expanded "pension?" to a generic query, but retrieved chunks covered vehicle insurance and general termination rather than pension rules, causing "I don't know".
10. **`trc_20260830_1bafba6e`**: Retrieved `chunk_240` (separation dates) instead of `chunk_227` (four weeks notice requirement), causing the LLM to state that the exact notice duration is not explicitly stated.
11. **`trc_20260830_941c091d`**: One-word query "timing?" was rewritten to flexible work schedules, but retrieved vehicle insurance policy chunks, producing "I don't know".
12. **`trc_20260830_eb2810be`**: Retrieved `chunk_108` and correctly stated that standard annual leave entitlement for full-time staff is 24 days per annum.
13. **`trc_20260830_dcdb7013`**: Query asked about Commercial Vehicle Policy Edition 2010 limits, but retrieved chunks from a different policy section without edition limits, outputting "I don't know".
14. **`trc_20260830_4b5ea250`**: One-word query "notice?" retrieved commercial vehicle loss notification rules (`commercial-vehicles-package-policy-93ee460add:chunk_25`) instead of employee resignation notice rules.
15. **`trc_20260830_6afbd9a1`**: Query asked about excluded dental and cosmetic treatments; retrieved chunks covered general benefits without mentioning exclusions, outputting "I don't know".
16. **`trc_20260830_572cc178`**: Retrieved SACCO loan payroll deduction text (`chunk_93`), but outputted "I don't know" because the text mentions SACCO contributions rather than direct interest-free loans.
17. **`trc_20260830_2ff6bfd8`**: Retrieved `chunk_120` (uncertified sick leave) instead of post abandonment rules (10.4), producing "I don't know".
18. **`trc_20260830_5b4058bb`**: PII redaction successfully stripped employee name, ID, and email before saving, but retrieval fetched general agreement chunks instead of `chunk_124`, outputting "I don't know".
19. **`trc_20260830_ad2f0426`**: Retrieved `chunk_107` and correctly answered 9:00 am to 5:30 pm Monday to Friday (40 hours per week).
20. **`trc_20260830_a6c98189`**: Retrieved `doc_default_102` and `chunk_98` and correctly detailed relocation shipment weight allowances and travel coverage.

---

## 5. Dated Falsifiable Prediction

- **Date:** `2026-08-30`
- **Target Failure Mode:** Mode 1 (Query Rewriter Vector Drift on One-Word Prompts) & Mode 2 (Missing Specific Policy Section Chunk Retrieval).
- **Specific Fix Planned:** Implement metadata-based document routing (HR vs Insurance form scope filter) and preserve raw user keywords alongside LLM rewritten queries during BM25 retrieval.
- **Expected Numeric Delta:** "Adding metadata scope filtering and hybrid keyword retention will drop Failure Mode 1 (One-Word Vector Drift) from 15% (3/20) to 0% (0/20) and improve retrieval hit rate for specific section rules (Mode 2) from 25% failure down to under 10%."
- **Git Commit Hash:** `PENDING_COMMIT` *(To be populated upon git commit)*

---

## 6. Public Benchmark Analysis (3 Sentences)

1. Public benchmarks evaluate models using synthetic, perfectly formatted multiple-choice or factual QA pairs that do not reflect real-world user behaviors like typing one-word prompts ("timing?").
2. They test general reasoning across clean static datasets rather than domain-specific multi-document crosstalk (e.g. confusing employee HR resignation rules with commercial vehicle loss notice clauses).
3. Public benchmark metrics like ROUGE or Exact Match measure surface text overlap rather than production failure modes like LLM false-negative fallbacks when correct context is present.
