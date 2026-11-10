# One-Page Architecture Sketch: Policy Answer Desk (Variant C)

```
                         [ USER / EMPLOYEE ]
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │  FastAPI / Streamlit UI   │
                    │      (Single Entry)       │
                    └─────────────┬─────────────┘
                                  │
                   Trace ID Generated: `trc_hr_xxxx`
                                  │
                                  ▼
                 ┌─────────────────────────────────┐
                 │    Step 1: Employee Resolver    │  ◄── $0.00 (In-memory DB lookup)
                 │  `lookup_employee_record(emp)`  │      Grade (1-7), Entity (India/UK)
                 └────────────────┬────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
[ Colleague PII Query? ]   [ Discretionary? ]        [ Valid Policy Query ]
  • Refusal returned         • Auto-escalate to        • Proceed to Scoped RAG
  • No PII leaked              `escalate_to_hrbp()`
  • Code of Conduct cited    • Ticket: `HRBP-XXXXXX`
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │    Step 2: Scoped RAG     │  ◄── $0.00 (Local sentence-transformers
                    │  (Hybrid: BM25 + Chroma)  │             + local BM25 ranking)
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ Step 3: Annex Prioritizer │  ◄── $0.00 (Deterministic rule)
                    │  (Entity Annex SILENTLY   │      India IN-1.1 > Handbook 2.3
                    │   overrides Handbook)     │      UK UK-1.1 > Handbook 2.3
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │  Step 4: Answer Generator │  ◄── WHERE THE MONEY GOES:
                    │  (Grounded Synthesis with │      ~$0.0034 / query hosted equiv
                    │   Version & Date Citation)│      (0.00 with local Ollama llama3.2)
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ Step 5: PII Redaction &   │  ◄── PII line held before logging:
                    │      OpenTelemetry Log    │      [REDACTED_GRADE],
                    │   `tracer.redact_pii()`   │      [REDACTED_SALARY_BAND],
                    │      `traces.jsonl`       │      [REDACTED_LEAVE_BALANCE]
                    └───────────────────────────┘
```

---

### Where the Money Goes (Cost Breakdown per Query)

| Component | Operation | Model / Tool | Latency | Cost (Hosted Equiv) | Real Local Cost |
|---|---|---|:---:|:---:|:---:|
| **Record Resolution** | Employee directory lookup | Python dictionary | 0.8 ms | $0.0000 | $0.00 |
| **Embeddings** | Dense query vector | `all-MiniLM-L6-v2` | 24.5 ms | $0.0001 | $0.00 |
| **Keyword Search** | Sparse index retrieval | `BM25Okapi` | 3.2 ms | $0.0000 | $0.00 |
| **Reranker** | Cross-encoder rescore | `ms-marco-MiniLM-L-6-v2` | 45.0 ms | $0.0003 | $0.00 |
| **LLM Generation** | Answer synthesis & citations | `llama3.2` (~450 tokens) | 680.0 ms | $0.0030 | $0.00 |
| **Total per Query** | **End-to-End Pipeline** | **Integrated Stack** | **~753 ms** | **~$0.0034** | **$0.00** |
