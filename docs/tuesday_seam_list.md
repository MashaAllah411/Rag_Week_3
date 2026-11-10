# Tuesday's Integration Seam List (Unedited)

**Date Recorded:** Tuesday, Week 12  
**System:** Policy Answer Desk — Integrated Capstone (Variant C)  
**Status Legend:** `FIXED` · `ACCEPTED` · `RAN-OUT-OF-TIME`

---

### Seam 1: Pre-Retrieval Grade & Entity Injection vs Document Text
* **What broke at the seam:** The Week 3 RAG retriever was searching generic handbook text before the employee's Grade (1–7) or Entity (India vs UK) was known. An employee in Chennai was retrieving general handbook parental leave (12 weeks) instead of India statutory leave.
* **Decision:** `FIXED`
* **Resolution:** Re-architected entry point to force `lookup_employee_record()` as mandatory Step 1 before RRF retrieval executes.

---

### Seam 2: Silent Annex Priority (Local Law vs Global Handbook)
* **What broke at the seam:** ChromaDB cosine similarity ranked Section 2.3 of the 40-page Global Handbook higher than Clause IN-1.1 of the India Annex because the handbook text had higher keyword overlap.
* **Decision:** `FIXED`
* **Resolution:** Created the *Annex Prioritization Post-Filter*: If an employee belongs to the India or UK entity, the entity annex silently supersedes and suppresses conflicting global handbook clauses.

---

### Seam 3: Citation Version & Effective Date Metadata Loss
* **What broke at the seam:** Standard retriever citations were only returning `document_id:chunk_id`. Week 12 requires citing policy VERSION (2024 vs 2025 vs Addendum A) and effective dates.
* **Decision:** `FIXED`
* **Resolution:** Injected `policy_version` and `effective_date` into ChromaDB chunk metadata during indexing, and formatted citations as `[Policy: <Doc> | Version: <Ver> | Effective: <Date> | Clause: <X>]`.

---

### Seam 4: Discretionary Boundary Failure (Overconfident Hallucination)
* **What broke at the seam:** When asked for a 4-month unpaid sabbatical, the LLM attempted to synthesize an answer or calculate accrual instead of recognizing that sabbaticals >3 months are strictly discretionary.
* **Decision:** `FIXED`
* **Resolution:** Implemented `_is_discretionary_query()` routing to `escalate_to_hrbp()`, returning a structured ticket reference (`HRBP-XXXXXX`) and 24h SLA.

---

### Seam 5: PII Leak Across OpenTelemetry & Log Trace Hops
* **What broke at the seam:** Full employee records returned by `lookup_employee_record()` contained salary band, grade, and personal leave balances, which appeared unmasked in `traces.jsonl`.
* **Decision:** `FIXED`
* **Resolution:** Added regex-based PII scrubbers in `tracer.py` replacing Grade, Salary, and Leave balances with `[REDACTED_GRADE]`, `[REDACTED_SALARY_BAND]`, and `[REDACTED_LEAVE_BALANCE]`.

---

### Seam 6: External Remote stdio MCP Process Spawning
* **What broke at the seam:** Launching remote MCP servers over stdio child processes required cross-platform OS socket permissions that risked timeout on fresh evaluator machines.
* **Decision:** `ACCEPTED`
* **Resolution:** Kept the JSON-RPC protocol wire-format and discovery handshakes real, but executed tools via clean module dispatchers. Documented as an honest limitation in weak spots.

---

### Seam 7: Multi-turn Session Memory Across Long Grievance Dialogues
* **What broke at the seam:** Context window bloat and token degradation when an employee engages in 5+ follow-up questions regarding complex leave calculations.
* **Decision:** `RAN-OUT-OF-TIME`
* **Resolution:** Scoped for Phase 2 roadmap. Currently single-query context is fully defensible.
