# Week 5 Failure Taxonomy — Task Set D

| Failure Mode Name | Count | Freq % | Severity | Example Trace ID |
|---|---|---|---|---|
| **Query Rewriter Vector Drift on One-Word Prompts** | 3 | 15% | Merely annoys user (retrieves wrong document category or falls back) | `trc_20260830_4b5ea250` |
| **Missing Specific Policy Section Chunk Retrieval** | 5 | 25% | Wrongly denies / fails to provide exact policy rule | `trc_20260830_1bafba6e` |
| **Out-of-Scope / Non-Existent Policy Fallback** | 3 | 15% | Merely annoys user (correctly returns "I don't know") | `trc_20260830_555cd901` |
| **Form Edition & Multi-Document Cross-Pollination** | 2 | 10% | Wrongly applies incorrect form edition or document rules | `trc_20260830_dcdb7013` |
| **LLM False Negative Fallback (Chunk Present)** | 2 | 10% | Wrongly denies answer despite correct chunk in top 3 | `trc_20260830_24a5894d` |
| **Successful Execution (No Failure)** | 5 | 25% | None (Correctly retrieved & answered) | `trc_20260830_eb2810be` |

---

### Notes & Summary Table Overview
- **Total Traces Analyzed:** 20 (drawn via seeded random sampling, `seed = 42`)
- **Top Failure Mode:** Missing Specific Policy Section Chunk Retrieval (25% frequency)
- **Second Failure Mode:** Query Rewriter Vector Drift on One-Word Prompts (15% frequency)
