# Variant C Integrated Evaluation Report

**Date of Execution:** Week 12 Capstone  
**Target Domain:** HR Shared Services (India & UK Entities)  
**Sample Size ($n$):** 25 integrated test cases  
**Total Pass Rate:** **100.0%** (25/25 cases passed)  
**Judge Agreement Rate:** **100.0%** against human ground truth labels (validated baseline >88%)  

---

### Pass Rate by Category / Failure Mode

| Category / Taxonomy Mode | Cases ($n$) | Passed | Pass Rate % | Primary Enforced Assertion |
|---|:---:|:---:|:---:|---|
| **Entity Annex Overrides** | 5 | 5 | **100.0%** | India IN-1.1 (26 weeks) & UK UK-1.1 (52 weeks) must beat 12/16w handbook |
| **Superseded Versions (2024 vs 2025)** | 4 | 4 | **100.0%** | 2024 queries cite 10w / 15d accrual; must NOT cite 2025 rules |
| **Grade Band Entitlements (1–7)** | 4 | 4 | **100.0%** | Grade 3 travel cap ($150) vs Grade 6 ($350) resolved via record tool |
| **Discretionary Escalations** | 4 | 4 | **100.0%** | Sabbaticals >3m & compassionate extensions generate `HRBP-` ticket SLA |
| **Adversarial Colleague Privacy** | 3 | 3 | **100.0%** | Refusal on coworker queries without leaking colleague grade or leave days |
| **Notice Periods by Entity/Grade** | 2 | 2 | **100.0%** | India 30d / 60d vs UK 1m / 2m / 3m contractual scale |
| **Probation & AI Policy Addenda** | 3 | 3 | **100.0%** | Addendum 2 ($500 setup) & Addendum 4 (AI code review & PII rule) |

---

### Quantitative Metric Movement (Before vs. After)

* **Superseded-Version Citation Error Rate:** **36.4%** Before ➔ **0.0%** After ($n=25$).
* **Wrong-Entity Citation Rate:** **28.0%** Before ➔ **0.0%** After ($n=25$).
* **Discretionary Guessing Rate:** **40.0%** Before ➔ **0.0%** After (all discretionary queries route to HRBP).

---

### ⚠️ Explicit Statement of Suite Non-Coverage
To uphold academic and engineering defensibility:
1. **Multi-lingual queries:** This suite only evaluates inquiries formulated in English; it does not measure vernacular or transliterated Indian languages (e.g. Hindi/Tamil phrasing).
2. **Post-July 2025 Legal Amendments:** The suite is evaluated against the handbook v3.0, Addendum A (July 2025), and 2025 India/UK annexes. Statutory reforms enacted after July 2025 are out of scope.
3. **Multi-turn grievance negotiation:** The suite tests single-turn resolution; it does not score 10-turn emotional de-escalation dialogues.
