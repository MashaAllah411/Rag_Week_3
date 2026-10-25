# Features

One section per capability. Each says which week it comes from, where to use it in the UI, which API endpoints back it, and how real it is.

- [Architecture](architecture.md) · [Setup](setup.md) · [Legacy index](legacy.md)

**Status legend:** *Live* = real computation. *Scripted* = real protocol and bookkeeping with scripted decisions. *Simulated* = generated or estimated data, labelled as such in the UI. *Needs Ollama* = needs the local LLM. *Added* = built in the consolidation pass because the task brief asked for it and the UI had no way to use it.

All endpoints are under `http://localhost:8000` (interactive docs: `/api/docs`).

## Coverage by week

| Week | Topic | Where in the UI | Status |
|---|---|---|---|
| 1 | Tokens, cost, temperature, embeddings | Foundations Lab | Live, Added |
| 2 | Structured output, validation and retry, tool calling, guardrails | Guardrails & Security, Agent Triage | Live (generation needs Ollama), Added |
| 3 | Ingest PDFs, chunking, embeddings, vector store, citations, "I don't know" | Documents, Search & Q&A | Live |
| 4 | BM25, hybrid RRF, reranking, MMR, query rewrite, failure separation, hit-rate / recall / MRR | Search & Q&A, Evaluation | Live (rewrite needs Ollama) |
| 5 | Complete traces, seeded sample, open coding, taxonomy, prediction | Error Analysis, Observability | Live, Added |
| 6 | Assertions, LLM judge, judge validation, before/after, regression tests | Evaluation | Live (judge needs Ollama) |
| 7 | Agent loop, budgets, fixed workflow, race | Agent Triage | Scripted |
| 8 | Trajectory evaluation, outcome-vs-trajectory gap, prompt injection, least privilege | Agent Triage, Guardrails & Security | Scripted (trajectory), Live (injection scan), Added |
| 9 | MCP: discovery, own servers, config swap | MCP Ecosystem | Scripted |
| 10 | Manager + two specialists, A2A envelopes, single vs team race | Multi-Agent Squad | Scripted |
| 11 | Per-request spans, support drill, cost and cache, failure-to-test loop | Observability, Evaluation, System | Live (spans, regression); Simulated (drill data, cache benchmark) |
| 12 | One entry point, guide, full suite, weak spots, demo | Capstone, Documentation | Live |

Named in the briefs but **not implemented**: HyDE and Cohere/BGE rerank APIs (Week 4; a local cross-encoder is used), RAGAS and G-Eval metrics (Week 6), agent memory (Week 7), remote MCP with auth and the fastmcp SDK (Week 9; a hand-written JSON-RPC layer is used), CrewAI / AutoGen (Week 10), LiteLLM routing and rate-limit fallbacks (Week 11).

---

## Foundations Lab (Week 1, Added)

**What:** hands-on versions of the Week 1 ideas using the app's real models. Count tokens and context-window use; estimate cost per request from token counts and editable prices; see how temperature, top-k and top-p reshape next-token probabilities and sampled draws; compare embedding similarity between texts.
**Use it:** *Foundations Lab*.
**Endpoints:** `POST /api/foundations/tokenize`, `/cost`, `/sampling`, `/similarity`.
**Notes:** token counts use the embedding model's WordPiece tokenizer (hosted models use their own, so counts differ). Prices are illustrative; local Ollama models cost $0 per token.

## Guardrails & Security (Weeks 2 and 8, Added)

**What:**
- *Input guardrail:* the scope guard rejects gibberish and off-topic questions before retrieval.
- *Structured output:* answers must match a Pydantic schema (`answer`, `citations`, `confidence`, `refused`). A pasted reply can be validated for free; the live generator asks the LLM for JSON, feeds validation errors back, and gives up safely after the retry limit.
- *Prompt injection:* a deterministic scanner finds instructions hidden in retrieved text (override, role hijack, prompt exfiltration, fake system messages, tool abuse, exfiltration links, hidden characters) and can quarantine those chunks.
- *Tool permissions:* the agent tools can read claims and policy text and compute numbers; none can write, send or delete.

**Use it:** *Guardrails & Security*; switch the injection scan on in *Search & Q&A* (off by default).
**Endpoints:** `POST /api/guardrails/scope`, `GET /structured/schema`, `POST /structured/validate`, `POST /structured/generate` (needs Ollama), `GET /injection/demo`, `POST /injection/scan`, `POST /injection/scan-retrieval`, `GET /tools`; `scan_injection` on `POST /api/ask`.
**Limits:** the scanner is rule-based; it misses paraphrased or encoded attacks and can flag legitimate text. The UI lists what it does not catch. Against the two shipped policy PDFs it flags nothing (checked by a test).

## Documents (Week 3)

**What:** list indexed PDFs, upload (indexed in the background), delete (removes vectors too), re-index, inspect chunks. The chunk inspector supports fixed, keyword and semantic strategies with adjustable size and overlap. The chunk-size experiment compares sizes for a query and an expected phrase, showing whether the answer stays intact and how BM25 ranks it. Text is read with pypdf plus Tesseract OCR on embedded images.
**Use it:** *Documents*.
**Endpoints:** `GET /api/documents`, `POST /upload`, `DELETE /{filename}`, `POST /reindex`, `GET /{filename}/chunks?strategy=&chunk_size=&chunk_overlap=`, `POST /{filename}/chunk-compare`.

## Search & Q&A (Weeks 3 and 4)

**What:** ask a question against all documents or one. Modes: **semantic** (vectors only), **hybrid** (BM25 + vectors fused by Reciprocal Rank Fusion), **reranked** (hybrid, then cross-encoder, then MMR for diversity). Shows the answer, citations as `document:chunk_N` with scores and ranks, a confidence label, and every pipeline step. Out-of-scope questions and unsupported questions get a plain refusal or "I don't know" instead of an invented answer.
**Use it:** *Search & Q&A*.
**Endpoint:** `POST /api/ask` (`question`, `mode`, `top_k`, `similarity_threshold`, `use_query_rewriter`, `document_name`, `scan_injection`).
**Needs Ollama for:** the written answer and query rewriting. Retrieved chunks and citations work without it.

## Evaluation (Weeks 4, 6 and 11)

**What:**
- *Retrieval quality:* hit-rate@k, recall@k and MRR for semantic, hybrid and reranked on a **12-question insurance set** whose answers were checked against the indexed PDF text. Per-question hit/miss is shown.
- *Historical (HR corpus):* the original before/after numbers, kept for the record. They came from an earlier HR-policy PDF with `chunk_107`-style ids and cannot be reproduced on the current index (the page says so).
- *Failure analysis:* sort each failure into "retrieved the wrong chunk" or "right chunk, bad answer", with human overrides.
- *Assertions:* four deterministic checks (claim id format, date of loss, dollar amount, exclusion clause cited for denials).
- *LLM judge:* V1 vs V2 prompts, plus a validation panel comparing the judge with 25 human labels.
- *Failure to test loop:* permanent regression cases, including the planted drill failure `CLM-FAIL-7701` (rising lake water must be denied under Section 5.2) and an over-blocking guard (a burst pipe must be approved).

**Use it:** *Evaluation*.
**Endpoints:** `GET /api/evaluate/datasets`, `GET /insurance/results`, `POST /insurance/run`, `GET /metrics`, `GET /results/{mode}`, `POST /run`, `POST /assertions`, `POST /judge` (needs Ollama), `GET /judge-validation`, `GET /regression`, `POST /regression/run`; `GET /api/failures`, `POST /api/failures/label`.
**Honest reading:** the set is small, so one question is noise. At the time of writing hybrid beat semantic and reranked scored lower than hybrid; the Capstone page states current numbers from live runs.

## Error Analysis (Week 5, Added)

**What:** a guided workflow. Take a seeded random sample of real request traces (default 20, seed 42, reproducible), write one honest note per trace *before* choosing categories, group the notes into named problems, rank them by frequency x severity, and record a prediction before trying a fix.
**Use it:** *Error Analysis*. Traces appear after questions are asked in *Search & Q&A*.
**Endpoints:** `GET /api/observability/error-analysis/sample`, `POST /notes`, `GET /taxonomy`, `POST /prediction`. Notes are stored in `data/error_analysis.json`.

## Agent Triage (Weeks 7 and 8)

**What:** triage ten sample claims with a budgeted agent loop (max iterations, tokens, cost, wall-clock time) or a fixed four-step workflow; force each budget to trip; score the path as well as the answer (tool-choice accuracy, argument validity, step efficiency, outcome-vs-trajectory gap); race agent against workflow on pass rate, speed, tokens and cost.
**Use it:** *Agent Triage*.
**Endpoints:** `GET /api/agent/claims`, `POST /triage`, `POST /benchmark`.
**Status: Scripted.** The loop follows a fixed plan; no LLM picks the next step, and token and cost figures are estimates. Budgets, stop conditions and trajectory scoring are real.

## MCP Ecosystem (Week 9)

**What:** a host exchanges JSON-RPC messages (`initialize`, `notifications/initialized`, `tools/list`, `tools/call`) with a policy server and a claims server, discovers their tools instead of having them hard-coded, calls them, runs a claim triage over MCP, and switches between the bundled configuration files (one server, or both) with no change to the agent's code.
**Use it:** *MCP Ecosystem*.
**Endpoints:** `GET /api/mcp/servers`, `POST /call`, `POST /triage`, `POST /config`.
**Status: Scripted.** The message formats and discovery handshake are real JSON-RPC, but the two servers are called in-process, selected by module name. The `command` / `args` in `data/mcp_config*.json` are not launched, so an external stdio server cannot be added by configuration alone; that would need a small change to the host's `connect()`.

## Multi-Agent Squad (Week 10)

**What:** a manager agent hands work to a policy specialist and a payout specialist using A2A message envelopes (agent cards, task lifecycle, per-hand-off tokens and latency), shows the full transcript, and races the squad against the single agent on quality, speed, tokens and cost.
**Use it:** *Multi-Agent Squad*.
**Endpoints:** `GET /api/multi-agent/agents`, `POST /triage`, `POST /benchmark`.
**Status: Scripted.** Decisions are scripted; the envelopes, hand-off accounting and race are real. A key mismatch in the service that left the transcript blank and scored every squad result as failed was fixed in this pass (covered by `tests/test_squad_service.py`).

## Observability (Weeks 5 and 11)

**What:** every real `/api/ask` request is traced step by step (`scope_guard`, `query_rewrite`, `retrieval:<mode>`, `generation:llm`) with time, estimated tokens and cost per step, PII redacted, and exported through OpenTelemetry. Replay any trace from its saved context. Run the support drill: find the planted bad answer from a vague complaint. Benchmark the semantic cache.
**Use it:** *Observability*.
**Endpoints:** `GET /api/observability/traces`, `GET /traces/{id}`, `POST /replay` (needs Ollama), `POST /drill`, `POST /cache-benchmark`, `GET /otel`.
**Status:** request traces and the OpenTelemetry export are live. **Simulated:** the drill's 100 traces are generated with one planted failure, and the cache benchmark simulates latency with a fixed per-query cost.

## System & Health (all weeks)

**What:** shows each tool and whether it is actually active (ChromaDB, OpenTelemetry, Tesseract, embeddings, reranker, BM25, Ollama), runs a self-test that exercises them for real, shows indexing progress, masked configuration and live logs.
**Use it:** *System & Health*.
**Endpoints:** `GET /api/system/status`, `POST /selftest?deep=`, `GET /logs`; `GET /health`.

## Capstone (Week 12)

**What:** run the whole suite in one click (tool round trips, hybrid vs semantic, structured output, injection scan, agent race, MCP discovery, A2A squad, regression cases, and an end-to-end answer when Ollama is up). Checks that need a missing dependency are reported as *skipped*, never as passed. Also lists known weak spots and gives a four-part demo script filled from real results.
**Use it:** *Capstone*.
**Endpoints:** `POST /api/capstone/suite`, `GET /weak-spots`, `GET /demo`.

## Documentation page

An end-user guide inside the UI: request-flow diagrams, a guide to each page, step-by-step "how do I" walkthroughs, a table of what is real versus simulated, and a glossary. See *Documentation* in the sidebar.

## Themes: System, Light, Dark

The menu in the top-right corner of every page (the three dots) has a **System / Light / Dark** switcher. *System* follows the operating system; *Light* and *Dark* force one. The choice is remembered in the browser and applies to every page, including after a refresh or in a new tab. A saved preference from before this was added needs picking once more.

How it is built (for anyone changing it): `.streamlit/config.toml` defines `[theme.light]` and `[theme.dark]`. Do not add a single `[theme]` block: Streamlit only shows the switcher when more than one theme exists, and a single block hides it. The shared stylesheet in `ui/components.py` takes its colours from the active theme, and a small script in `persist_theme_across_pages` mirrors the choice across page URLs, because Streamlit stores it under a per-page key. `tests/test_theme_config.py` guards these rules.

