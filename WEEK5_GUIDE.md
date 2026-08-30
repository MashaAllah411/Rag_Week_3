# 📊 Week 5 Implementation & Error Analysis Guide

## Overview

Week 5 introduces **Production Error Analysis & Redacted Tracing** to our RAG application.

Instead of guessing why an application fails or changing code based on random instincts, Week 5 establishes a formal, scientific workflow:
1. **Complete Tracing & PII Redaction** before storage.
2. **Seeded Random Sampling** (20 traces).
3. **Manual Open-Coding** (observing exact behaviors without fixing).
4. **Taxonomy & Severity Clustering**.
5. **Falsifiable Dated Prediction** committed to Git before any code fix.

---

## Architecture & Workflow

```text
User Request / Query
        │
        ▼
   [redact_pii()]  ──▶ Redacts names, IDs, emails, phone numbers BEFORE log
        │
        ▼
   [RAG Pipeline] ──▶ Rewriter → Hybrid (Pinecone+BM25+RRF) → Reranker → MMR → LLM
        │
        ▼
  [log_trace()]   ──▶ Saves 10-field JSON record to traces/traces.jsonl
        │
        ▼
[Seeded Sampler]  ──▶ sample_traces.py (seed=42) → selects 20 traces
        │
        ▼
[Open-Coding]    ──▶ Verbatim observation sentences written in notes.md
        │
        ▼
  [Taxonomy]     ──▶ Clustered into 5 legible failure modes in taxonomy.md
        │
        ▼
[Prediction]     ──▶ Falsifiable prediction committed to Git with commit hash
```

---

## 1. Trace Schema

Every execution logs a complete, replayable JSON record into `traces/traces.jsonl`:

```json
{
  "trace_id": "trc_20260830_1bafba6e",
  "timestamp": "2026-08-30T15:35:00Z",
  "query": "What is the required notice period for resignation?",
  "prompt_version": "v1.0",
  "retrieved_chunks": [
    { "chunk_id": "chunk_240", "score": -0.6616 },
    { "chunk_id": "commercial-vehicles-package-policy-93ee460add:chunk_25", "score": -8.1672 },
    { "chunk_id": "chunk_228", "score": -2.4834 }
  ],
  "retriever_type": "Hybrid (Pinecone + BM25 + RRF + CrossEncoder + MMR)",
  "model": "llama3.2",
  "model_parameters": { "temperature": 0.4, "top_p": 0.9 },
  "raw_llm_output": "Section i. In the case of resignation...",
  "pii_redacted": true
}
```

---

## 2. PII Redaction (`tracer.py`)

Redaction happens **BEFORE** saving the trace to disk.
- **Emails:** `[REDACTED_EMAIL]`
- **Phone Numbers:** `[REDACTED_PHONE]`
- **Claim / Policy / Employee IDs:** `[REDACTED_ID]`
- **Names:** `[REDACTED_NAME]`

---

## 3. Seeded Random Sampling (`sample_traces.py`)

- **Seed:** `42`
- **Sample Size:** `20`
- **Output:** Saves sampled traces to `traces/sampled_20_traces.json` and outputs trace IDs to `notes.md`.

---

## 4. Verification & Replayability (`test_replay.py`)

Replays a request using **only** the fields stored in the trace record.
- Command: `python test_replay.py`
- Result: Verifies 100% replayability.

---

## 5. Key Artifacts

- 📄 [`taxonomy.md`](file:///c:/Users/mashaallah/OneDrive/Desktop/Rag_Week_3/taxonomy.md) — 5 failure modes with count, frequency %, severity, and example trace ID.
- 📄 [`notes.md`](file:///c:/Users/mashaallah/OneDrive/Desktop/Rag_Week_3/notes.md) — 20 open-coding observation sentences, seeded sample, replay evidence, PII confirmation, and dated prediction.
- 🛠️ [`tracer.py`](file:///c:/Users/mashaallah/OneDrive/Desktop/Rag_Week_3/tracer.py) — Tracing & PII redaction engine.
- 🎲 [`sample_traces.py`](file:///c:/Users/mashaallah/OneDrive/Desktop/Rag_Week_3/sample_traces.py) — Seeded random trace sampler.
- 🧪 [`test_replay.py`](file:///c:/Users/mashaallah/OneDrive/Desktop/Rag_Week_3/test_replay.py) — Trace replay evidence verification script.
