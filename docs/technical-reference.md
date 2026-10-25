# Technical reference

Complete technical documentation for this repository: what it is built from, how to watch it, how to install it on another machine, the exact PowerShell commands, and how to verify and fix it.

- Related: [Setup](setup.md) · [Architecture](architecture.md) · [Features](features.md) · [Legacy index](legacy.md)

## How to read this document

Every statement comes from the repository files or from something that was actually run. Labels:

| Label | Meaning |
|---|---|
| **Implemented** | Exists in the code and works today |
| **Verified** | I ran it and saw it work (what was run is listed in [Appendix E](#appendix-e-what-was-verified-and-what-was-not)) |
| **Optional** | Works without it; adds a capability |
| **Recommendation** | A suggestion that is *not* part of the repository |
| **Not verified here** | Stated from documentation or code only; I could not run it on the test machine |

Test machine: Windows 11 Pro (10.0.26200), Windows PowerShell 5.1, Python 3.12.10, Git 2.55, Tesseract 5.5, **no Ollama**. Dates: 2026-10-25.

## Contents

1. [Packages, libraries, frameworks and tools](#1-packages-libraries-frameworks-and-tools)
2. [Monitoring, tracing and evaluation: is there a dashboard?](#2-monitoring-tracing-and-evaluation-is-there-a-dashboard)
3. [Setup on another system](#3-setup-on-another-system)
4. [Exact PowerShell commands](#4-exact-powershell-commands)
5. [Verification and troubleshooting](#5-verification-and-troubleshooting)
- Appendices: [A API routes](#appendix-a-api-routes-60-operations) · [B environment variables](#appendix-b-environment-variables) · [C files the app writes](#appendix-c-files-and-folders-the-app-reads-and-writes) · [D UI pages](#appendix-d-ui-pages) · [E verification log](#appendix-e-what-was-verified-and-what-was-not)

---

## 1. Packages, libraries, frameworks and tools

### 1.1 Direct Python dependencies

Declared in [`requirements.txt`](../requirements.txt) and mirrored in [`pyproject.toml`](../pyproject.toml) (a test, `tests/test_launcher.py`, fails if they drift apart). **None are version-pinned**, so a new machine installs whatever is current; the "version tested" column is what the clean-machine run installed on 2026-10-25.

| Package | Version tested | What it does here | Where it is used |
|---|---|---|---|
| `fastapi` | 0.162.0 | REST API framework | `src/rag/api/main.py` and all 12 routers in `src/rag/api/routes/` |
| `uvicorn[standard]` | 0.54.0 | Web server that runs the API | Started by `run.py` as `python -m uvicorn rag.api.main:app`; not imported by code |
| `python-multipart` | 0.0.32 | Lets FastAPI parse file uploads | Needed by `POST /api/documents/upload`; not imported directly |
| `pydantic` | 2.14.1 | Request/response models, the structured-output schema | `src/rag/models/schemas.py`, routers (documents, evaluate, foundations, guardrails, observability), `src/rag/generation/structured.py` |
| `pypdf` | 6.21.2 | Reads text and page counts from PDFs | `src/rag/ingestion/pdfreader.py`, `src/rag/api/routes/documents.py` |
| `sentence-transformers` | 6.2.0 | Embedding model (`SentenceTransformer`) and the cross-encoder reranker (`CrossEncoder`); its tokenizer feeds the Foundations Lab | `src/rag/storage/embedder.py`, `src/rag/retrieval/reranker.py` |
| `chromadb` | 1.5.9 | Embedded, persistent vector database | `src/rag/storage/vectorstore.py` (everything else calls its functions) |
| `rank-bm25` | 0.2.2 | BM25 keyword search | `src/rag/retrieval/bm25.py`, chunk-size experiment in `src/rag/api/routes/documents.py` |
| `ollama` | 0.6.3 | Client for the local LLM server | `src/rag/generation/llm.py` (answers), `src/rag/core/query_rewriter.py`, `src/rag/core/scope_guard.py`, `src/rag/services/evaluation_service.py` (judge), `src/rag/api/routes/guardrails.py`, `src/rag/api/routes/system.py`, `src/rag/services/capstone_service.py` |
| `python-dotenv` | 1.2.4 | Loads `.env` | `src/rag/config.py`, `run.py` |
| `numpy` | 2.5.4 | Vector maths, sampling demo | `src/rag/retrieval/mmr.py`, `src/rag/ingestion/chunker.py`, `src/rag/cache/semantic_cache.py`, `src/rag/evaluation/trajectory_eval.py`, `src/rag/services/foundations_service.py` |
| `pandas` | 3.1.0 | Tables in the UI | `ui/views/documents.py`, `error_analysis.py`, `evaluation.py`, `foundations.py` |
| `pytesseract` | 0.3.13 | Python wrapper for the Tesseract OCR program | `src/rag/ingestion/pdfreader.py` |
| `Pillow` | 13.0.0 | Image handling for OCR | `src/rag/ingestion/pdfreader.py` |
| `streamlit` | 1.66.1 | The web UI | `ui/app.py`, `ui/components.py`, every file in `ui/views/` |
| `requests` | 2.34.2 | The UI's HTTP client for the API | `ui/api_client.py` (also error types in `ui/components.py`, `ui/views/guardrails.py`) |
| `httpx` | 0.28.1 | HTTP client that `ollama` and `chromadb` depend on | Not imported by this repository's code. (Starlette's `TestClient`, used in `tests/`, prefers `httpx2`, which `huggingface_hub` installs, and falls back to `httpx`.) Declared explicitly, but it would be installed anyway |
| `opentelemetry-api`, `opentelemetry-sdk` | 1.45.1 | Real tracing | `src/rag/observability/otel.py` (initialised in `src/rag/api/main.py`) |
| `opentelemetry-exporter-otlp-proto-http` | 1.45.1 | Sends spans to an OTLP collector | Imported lazily in `otel.py` **only** when `OTEL_EXPORTER_OTLP_ENDPOINT` is set |
| `pytest` | 9.1.1 | Test runner | `tests/` |
| `reportlab` | 5.1.0 | Builds the sample policy PDF (development only) | `src/rag/scripts/build_insurance_pdf.py` |

`pandas` was imported by the UI but not declared (it arrived indirectly through Streamlit); it is now declared in `requirements.txt`, `pyproject.toml` and `run.py`.

### 1.2 Large packages installed indirectly (not declared, not imported by this code)

The clean install ends up with 124 distributions and a virtual environment of about 1.5-1.7 GB. The big ones: `torch` 2.14.1 (pulled in by `sentence-transformers`, by far the largest download), `transformers` 5.20.2, `huggingface_hub` 2.3.0 (downloads the models), `onnxruntime` 1.31.0 and `grpcio` (ChromaDB), `scikit-learn` and `scipy`, `starlette` 1.10.0 (FastAPI), `protobuf` (OTLP), `altair` (Streamlit).

### 1.3 Models

| Model | Source | Used by | Setting |
|---|---|---|---|
| `all-MiniLM-L6-v2` (384-dimension embeddings) | Hugging Face | `src/rag/storage/embedder.py` | `EMBEDDING_MODEL` |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | Hugging Face | `src/rag/retrieval/reranker.py` | `RERANKER_MODEL` |
| `llama3.2` | Ollama (local) | answers, query rewrite, scope guard, judge, structured output | `OLLAMA_MODEL` |

The two Hugging Face models total about 176 MB on a fresh cache (measured). `run.py` downloads them once. BM25 is an algorithm (BM25Okapi from `rank-bm25`), not a model.

### 1.4 Programs outside Python

| Program | Needed? | Used for |
|---|---|---|
| Python 3.10 or newer | **Yes** (tested on 3.12) | everything; `pyproject.toml` says `requires-python = ">=3.10"` |
| Git | Only to clone | getting the code |
| Tesseract OCR | Optional | reading text inside images in PDFs (`pdfreader.py`); without it OCR is off and normal PDF text still works |
| Ollama | Optional | the LLM features listed in 1.3; everything else works without it |
| A web browser | Yes | the UI |
| Graphviz | **No** | The Documentation page diagrams are drawn in the browser. Verified: no `dot` program is installed on the test machine and the diagrams rendered |

### 1.5 Protocols implemented in this repository's own code

- **MCP-style JSON-RPC 2.0** (`initialize`, `tools/list`, `tools/call`): `src/rag/mcp/protocol.py`, `policy_server.py`, `claims_server.py`, host in `src/rag/agent/mcp_agent.py`. Hand-written; the `fastmcp` SDK is **not** used, and the servers are called in-process.
- **A2A message envelopes** (agent cards, task lifecycle): `src/rag/agents/a2a_protocol.py`.
- **OpenTelemetry / OTLP over HTTP**: `src/rag/observability/otel.py`.

### 1.6 Searched for and *not* used

The code and `requirements.txt` were searched for these; none is imported or installed: LangChain, LangSmith, Langfuse, RAGAS, DeepEval, MLflow, Weights & Biases, LiteLLM, OpenAI and Anthropic SDKs, FAISS, Qdrant, Redis, SQL databases, Docker. A few of the names appear only as words in comments and UI text (for example "LangSmith / Phoenix / OpenTelemetry" in the `otel.py` docstring, or "RAGAS" in the list of known weak spots). Pinecone was replaced by ChromaDB; the old implementation is archived in `legacy/pinecone/` and its package is not installed.

---

## 2. Monitoring, tracing and evaluation: is there a dashboard?

### 2.1 Short answer

**No separate, LangSmith-style dashboard ships with this repository.** There is no hosted service, no extra server to start and no extra login. What exists:

1. **Implemented, built into the one UI:** pages for traces, spans, replay, evaluation results, error analysis, logs and health (2.2).
2. **Implemented, as files:** JSONL trace files and JSON result files you can open or load with any tool (2.3).
3. **Implemented hook, dashboard not included:** the app can also send its spans to an external OTLP dashboard you run yourself (2.5). **Verified** against Arize Phoenix.

### 2.2 What the built-in UI shows

Start the app (`python run.py`), then open the page.

| Page (URL) | What you see | Data comes from |
|---|---|---|
| **Observability** (`/observability`) | Tabs: *Request traces* (every `/api/ask` request with a span table: step, duration, tokens, cost, status), *OpenTelemetry* (SDK status, exporters, recent exported spans), *Trace replay*, *Support drill*, *Cost & cache* | `traces/production_traces.jsonl`, `traces/traces.jsonl`, `traces/otel_spans.jsonl` |
| **Evaluation** (`/evaluation`) | Retrieval quality per mode (hit-rate@k, recall@k, MRR with a per-question grid), historical results, failure analysis, assertions, LLM judge and judge validation, the failure-to-test regression runner | `data/insurance_results_<mode>.json`, `data/*.json` |
| **Error Analysis** (`/error-analysis`) | Seeded sample of real traces, notes, ranked problem taxonomy, prediction | `traces/traces.jsonl`, `data/error_analysis.json` |
| **Capstone** (`/capstone`) | One-click suite across all weeks, known weak spots, demo script | live runs |
| **System & Health** (`/system`) | Which tools are active, a real self-test, indexing progress, masked configuration, **Logs** tab | `logs/*.log` |
| FastAPI docs (`http://localhost:8000/api/docs`, also `/api/redoc`) | Interactive explorer for all 60 API operations | the API itself |

The FastAPI docs are an API explorer, not a trace viewer. Access and configuration: nothing extra to run or configure; the UI port is `FRONTEND_PORT` (default 8501).

### 2.3 What gets recorded

Every `POST /api/ask` creates one trace: a root span `rag.request` and four child spans, `scope_guard`, `query_rewrite`, `retrieval:<mode>` and `generation:llm`. Each span has duration, estimated tokens (about 4 characters per token, because the local model does not report usage here) and an illustrative cost (hosted-price equivalent; the local models cost $0). Text is passed through a PII redactor before it is stored or exported.

| File | Content | Growth |
|---|---|---|
| `traces/production_traces.jsonl` | One JSON object per request with a `spans` list (`name`, `duration_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `status`, `attributes`, ...). Also holds 100 generated drill traces with one planted failure | appended, not rotated |
| `traces/traces.jsonl` | The older flat record per request (`query`, `retrieved_chunks`, `raw_llm_output`, `retriever_type`, `model`, ...), used by Error Analysis and trace replay | appended, not rotated |
| `traces/otel_spans.jsonl` | One OpenTelemetry span per line: `trace_id`, `span_id`, `parent_span_id`, `name`, `start_time_ns`, `end_time_ns`, `duration_ms`, `status`, `service`, `attributes` (`rag.*`) | rotates to `otel_spans.jsonl.1` at 5 MB |

A real exported line (shortened): `{"name": "rag.request", "status": "ERROR", "service": "insurance-rag", "duration_ms": 17430.276, "attributes": {"rag.span_count": 4, "rag.total_tokens": 729, "rag.total_cost_usd": 0.000129, ...}}`. That one is `ERROR` because Ollama was not running, so the generation step failed.

### 2.4 How this compares with LangSmith

| Capability | Here | Note |
|---|---|---|
| List traces, see step timing | **Yes** (Observability page) | |
| Look up a trace by id | **Yes** (`GET /api/observability/traces/{trace_id}`, UI) | |
| Replay a past request | **Yes** | needs Ollama |
| Evaluation datasets and runs | **Partly** | one 12-question set, runs in the Evaluation page |
| Human review and labelling | **Partly** | Error Analysis notes, failure labels |
| Prompt playground, prompt versioning UI | No | |
| Compare two runs side by side | No (only the three retrieval modes in one table) | |
| Per-model token/cost accounting from real usage | No | tokens and cost are estimates |
| Multi-user accounts, sharing, retention, alerts | No | single local user |
| Hosted, always-on service | No | runs on your machine |

### 2.5 Optional: send traces to an external dashboard

**Implemented:** set `OTEL_EXPORTER_OTLP_ENDPOINT` in `.env` and the app sends the same spans to that OTLP/HTTP endpoint *in addition to* the local file (`src/rag/observability/otel.py`). The exporter package is already in `requirements.txt`. Restart after changing it.

**Verified in two steps:**

1. A stand-in collector received a real OTLP/HTTP protobuf `POST /v1/traces` from the app, and the System/Observability status listed both exporters (`jsonl`, `otlp-http`).
2. **Arize Phoenix 20.26.0** accepted and displayed the app's spans. One real `/api/ask` request produced 5 spans in Phoenix's `default` project (`rag.request` with `scope_guard`, `query_rewrite`, `retrieval:hybrid`, `generation:llm`), with the failed generation step marked as an error.

**What Phoenix shows and does not show.** The spans are generic OpenTelemetry spans, so Phoenix lists them as traces with timing and status but its input/output columns read `--`; it does not render them as LLM calls, and its Datasets, Evaluators, Prompts and Playground sections are not connected to this app. It is a viewer for the traces, not a replacement for the app's own pages.

**Phoenix facts (checked on the installed package):** licence **Elastic-2.0** (source-available, not an OSI open-source licence: read the terms), requires Python **3.11 to 3.14** (so install it in its own environment, not this project's), about 620 MB installed. Its server log showed it listening on `0.0.0.0:6006` (all interfaces); I did not test or enable any authentication.

Run it (**Recommendation**: Phoenix is not part of this repository). In a separate PowerShell window:

```powershell
python -m venv "$HOME\phoenix-venv"
& "$HOME\phoenix-venv\Scripts\python.exe" -m pip install arize-phoenix
& "$HOME\phoenix-venv\Scripts\phoenix.exe" serve
```

Open `http://localhost:6006`. Then in this project's `.env` set:

```
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:6006/v1/traces
```

Restart `python run.py`, ask a question on **Search & Q&A**, and open **Tracing > default** in Phoenix. Phoenix keeps its data under the folder given by `PHOENIX_WORKING_DIR` (verified: it created `phoenix.db` there).

**Other backends: Not verified here.** Any OTLP/HTTP-compatible backend should accept the same spans. Jaeger is the usual generic choice; its OTLP HTTP port is normally 4318 with path `/v1/traces`. I did not run Jaeger or any other backend, so treat that as a starting point, not a tested recipe. If you only need to look at traces, the built-in Observability page already does that with nothing to install.

### 2.6 Evaluation tools

Evaluation is the repository's own code; no external evaluation framework is used.

| What | Code | View it |
|---|---|---|
| Retrieval hit-rate@k, recall@k, MRR on 12 questions with checked answer phrases | `src/rag/evaluation/retrieval_eval.py`, data `data/evaluation_dataset_insurance.json` | Evaluation page; results saved to `data/insurance_results_{semantic,hybrid,reranked}.json` |
| Agent trajectory scoring | `src/rag/evaluation/trajectory_eval.py` | Agent Triage page |
| Deterministic assertions, LLM judge (Ollama), judge validation against 25 human labels | `src/rag/services/evaluation_service.py`, `data/labels_25.json` | Evaluation page |
| Failure-to-test regression cases | `src/rag/evaluation/regression.py` | Evaluation page; also run by `pytest` |
| Whole-app suite | `src/rag/services/capstone_service.py` | Capstone page (result is shown, not saved) |
| Automated tests | `tests/` (64 tests) | `pytest` output |

---

## 3. Setup on another system

Written for a clean Windows machine. Nothing needs to be installed except Python (and Git to clone); the launcher does the rest.

### 3.1 What you need

| Item | Required | Notes |
|---|---|---|
| Windows 10/11 with PowerShell | Yes | tested on Windows 11 and Windows PowerShell 5.1 |
| Python 3.10+ | **Yes** | tested on 3.12; install with the *Add python.exe to PATH* option, or use the `winget` command below |
| Git | To clone | or download the repository as a ZIP |
| Internet on first run | Yes | PyTorch and the other packages (a few hundred MB) and two models (about 176 MB) |
| Disk space | about 2 GB | measured: virtual environment about 1.7 GB, models 176 MB |
| Tesseract OCR | Optional | PDF images only |
| Ollama + `llama3.2` | Optional | written answers and the other LLM features |
| API keys | **None** | nothing in this repository needs an account or key |

### 3.2 Steps

1. **Install the prerequisites** (commands in section 4.1). Close and reopen PowerShell afterwards so `python` and `git` are on the path.
2. **Clone** the repository and enter it (4.2).
3. **Run `python run.py`.** On the first run it:
   1. checks Python is 3.10+,
   2. creates `.venv\` in the project folder and re-runs itself with that environment's Python (you never activate anything),
   3. installs `requirements.txt` with pip's progress shown (this is the long step),
   4. creates `.env` from `.env.example` (and stops with exit code 2 only if a key marked `[required]` is empty, which none is today),
   5. downloads the two models once,
   6. checks for Ollama, the model, Tesseract and a writable vector-store folder, printing a warning and an exact fix for anything optional that is missing,
   7. starts the API, waits for `/health`, starts the UI, waits for it, and opens the browser,
   8. indexes the PDFs in `resources/` in the background if the vector store is empty.

   Measured from a real `git clone` on an unprimed machine (no pip cache, empty model cache): the application was serving after about **196 seconds** on a connection of roughly 12 MB/s. Your time depends on your connection.
4. **Fill in `.env` only if asked.** The defaults work. Settings are listed in [Appendix B](#appendix-b-environment-variables).
5. **Optional LLM:** install Ollama, run `ollama pull llama3.2`, leave it running (4.5).
6. **Verify** (section 5).
7. **Stop** with `Ctrl+C`; both servers and their child processes exit.

Later runs skip steps 2-5 of the list above when nothing changed (about 0.7 seconds of checks on the test machine). If you pull changes that touch `requirements.txt`, `python run.py` notices and updates by itself.

> Offline use after the first run should work because the models are cached, but I did not test it offline.

---

## 4. Exact PowerShell commands

### 4.1 Prerequisites

The `winget` package ids below were checked with `winget show --exact`.

```powershell
winget install --id Python.Python.3.12 --exact          # Python (tested version: 3.12.10)
winget install --id Git.Git --exact                      # Git
winget install --id UB-Mannheim.TesseractOCR --exact     # optional: OCR for images inside PDFs
winget install --id Ollama.Ollama --exact                # optional: local LLM server
```

Close and reopen PowerShell, then confirm:

```powershell
python --version        # expect Python 3.10 or newer
git --version
```

If Tesseract is not installed in `C:\Program Files\Tesseract-OCR\` or `C:\Program Files (x86)\Tesseract-OCR\` and is not on `PATH`, set `TESSERACT_PATH` in `.env` to the full path of `tesseract.exe`.

### 4.2 Clone and run

```powershell
git clone https://github.com/MashaAllah411/Rag_Week_3.git
cd Rag_Week_3
python run.py
```

The UI opens at `http://localhost:8501`; the API docs are at `http://localhost:8000/api/docs`. If a port is busy the launcher picks the next free one and prints it.

### 4.3 Launcher options

```powershell
python run.py                    # set up anything missing, then start API + UI
python run.py --setup            # set up only (venv, packages, .env, models, service check); do not start
python run.py --setup --force    # reinstall packages and re-download models
python run.py --skip-setup       # skip all checks and start with the current Python
python run.py --help
```

### 4.4 Virtual environment by hand (optional)

`run.py` does this for you; use it only if you prefer to manage the environment yourself. Then start with `--skip-setup`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1                 # if blocked, see "Execution policy" in section 5.3
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python run.py --skip-setup
```

Start the two parts separately (this exact pair was tested; the API needs `PYTHONPATH` because the package lives in `src\`):

```powershell
$env:PYTHONPATH = "$PWD\src;$PWD"
.\.venv\Scripts\python.exe -m uvicorn rag.api.main:app --host 127.0.0.1 --port 8000
```

In a second window, from the same folder:

```powershell
$env:PYTHONPATH = "$PWD\src;$PWD"
$env:BACKEND_URL = "http://127.0.0.1:8000"
.\.venv\Scripts\python.exe -m streamlit run ui\app.py --server.port 8501
```

Always start from the repository root: the app writes to relative folders (`traces\`, `logs\`, `data\`).

### 4.5 Services

There is **no database to install**: ChromaDB is embedded and keeps its files in `data\vectorstore\`. The only separate service is the optional Ollama LLM server (commands from Ollama's own CLI; Ollama was **not installed on the test machine, so these were not run here**):

```powershell
ollama serve                 # starts the server if it is not already running
ollama pull llama3.2         # download the model named by OLLAMA_MODEL
ollama list                  # confirm llama3.2 is listed
```

### 4.6 Configuration

```powershell
Copy-Item .env.example .env          # only if run.py has not already created it
notepad .env
```

Example `.env` edits (all optional):

```
OLLAMA_MODEL=llama3.2
BACKEND_PORT=8000
FRONTEND_PORT=8501
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:6006/v1/traces
```

### 4.7 Day-to-day

```powershell
Invoke-RestMethod http://localhost:8000/health                                   # {"status":"ok",...}
Invoke-RestMethod http://localhost:8000/api/system/status | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method Post http://localhost:8000/api/system/selftest | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Post http://localhost:8000/api/documents/reindex       # rebuild the vector index

$body = '{"question":"What is the maximum cost for removal of a disabled vehicle after an accident?","mode":"hybrid","use_query_rewriter":false,"top_k":3}'
Invoke-RestMethod -Method Post http://localhost:8000/api/ask -ContentType "application/json" -Body $body

Get-Content logs\backend.log -Tail 50 -Wait         # follow the API log (Ctrl+C to stop following)
Get-Content logs\frontend.log -Tail 50              # UI log
git pull                                            # update; then run python run.py (it updates packages if needed)
```

### 4.8 Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Expected on the test machine: `64 passed` (about 15 seconds; no Ollama needed).

---

## 5. Verification and troubleshooting

### 5.1 Verification ladder

Each step lists what was observed on a fresh clone.

| # | Check | Expected |
|---|---|---|
| 1 | `python run.py` prints `[SETUP] ...` lines then `[HEALTH] Backend is healthy and ready` and `[READY] Stack is fully online!` | Warnings about Ollama are normal if it is not running |
| 2 | `Invoke-RestMethod http://localhost:8000/health` | `status: ok`, `version: 2.0.0` |
| 3 | UI at `http://localhost:8501` → **System & Health → Open-source stack** | ChromaDB, OpenTelemetry, OCR (if Tesseract is installed), Embeddings, Reranker, Keyword search **Active**; LLM Inactive until Ollama runs (6 of 7 active without Ollama) |
| 4 | **System & Health → Self-test → Run self-test** | 4 of 4 pass |
| 5 | Wait for indexing (System → Indexing, or Home banner) | 128 passages for the two shipped PDFs |
| 6 | **Search & Q&A**: ask the Rs 1500 question | Among the top three sources is `insurancepolicy:chunk_10` (observed order: a commercial-vehicles chunk, `insurancepolicy:chunk_10`, another commercial-vehicles chunk) |
| 7 | **Evaluation → Retrieval quality → Run all three** | Observed hit@3 / MRR: semantic 0.917 / 0.653, hybrid 1.000 / 0.778, reranked 0.583 / 0.528 (12 questions; small set, so differences of one question are noise) |
| 8 | **Evaluation → Failure → test loop → Run regression suite** | 3 of 3 pass |
| 9 | **Capstone → Run the full suite** | Without Ollama: 8 pass, 0 fail, 1 *skipped* (the end-to-end answer check). Skipped is not a pass |
| 10 | `pytest` | `64 passed` |

A scripted version of steps 2, 4-8 plus the trace and OpenTelemetry checks passed 9 of 9 against a fresh `git clone` of this repository.

### 5.2 Where to look

| What | Where |
|---|---|
| Startup and API log | `logs\backend.log`, or **System & Health → Logs** |
| UI log | `logs\frontend.log` (same Logs tab) |
| Request traces and spans | **Observability** page; `traces\production_traces.jsonl` |
| OpenTelemetry spans | **Observability → OpenTelemetry**; `traces\otel_spans.jsonl` |
| Retrieval evaluation results | **Evaluation**; `data\insurance_results_*.json` |
| Error-analysis notes | **Error Analysis**; `data\error_analysis.json` (created on first note) |
| Human failure labels | `data\failure_labels.json` |
| Vector index | `data\vectorstore\` (generated, git-ignored) |
| Test results | the `pytest` output |

The `.log` files are appended on every run and never rotated; delete them when they get large.

### 5.3 Common problems

All of these come from messages in `run.py`, errors seen while building and testing, or the code's behaviour.

| Symptom | Cause | Fix |
|---|---|---|
| `python` is not recognised | Python not installed, or the terminal was opened before it was | Run the `winget` command in 4.1, close and reopen PowerShell |
| `Python 3.10 or newer is required` | An older Python is first on the path | Install 3.12 and run again |
| `Could not create a virtual environment` | The `venv` module is missing (mainly Linux) | `sudo apt install python3-venv` on Debian/Ubuntu |
| `Dependency installation failed` | No internet, a proxy, or a Python version without prebuilt PyTorch wheels | Fix the connection or proxy and run `python run.py` again; it resumes. The project was tested on Python 3.12 |
| `.venv exists but its Python does not run` | The folder was moved or copied from another machine | Delete the `.venv` folder and run again |
| `Activate.ps1 cannot be loaded` (only if you activate by hand) | PowerShell's script policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then reopen PowerShell. Not needed for `python run.py` |
| `Action needed: fill in these keys in .env` (exit code 2) | A key marked `[required]` in `.env.example` is empty | Fill it in and run again. None is required today |
| `Backend port 8000 is busy` | Another program uses the port (seen on the test machine: a Docker app) | Nothing; the launcher uses the next free port and prints it. Or set `BACKEND_PORT` / `FRONTEND_PORT` in `.env` |
| UI says "Backend offline" / "Can't reach the backend" | The API is not running, or `BACKEND_URL` points elsewhere | Start with `python run.py`; check `logs\backend.log` |
| `No module named 'rag'` when starting uvicorn by hand | The package is in `src\` and is not installed | Set `$env:PYTHONPATH = "$PWD\src;$PWD"` first (4.4), or use `python run.py` |
| Traces or logs appear in the wrong folder, or the Logs tab is empty | The app uses relative paths | Run from the repository root (`run.py` does) |
| `Ollama is not reachable` warning; answers say "LLM unavailable" | Ollama not installed or not running | Install it, `ollama serve`, `ollama pull llama3.2`. Retrieval and citations still work without it |
| `Ollama is running but model 'llama3.2' is not pulled` | Model missing | `ollama pull llama3.2` |
| `Tesseract OCR not found` | Not installed or not on `PATH` | Install it (4.1) or set `TESSERACT_PATH`. Without it, normal PDF text still works |
| `Could not download the models (offline?)` | No connection during first setup | Reconnect and run `python run.py --setup`; otherwise the models are fetched on first use |
| Search returns nothing right after the first start | The background indexing has not finished | Watch **System & Health → Indexing**; about 5-15 seconds for the shipped PDFs |
| `Expected a name containing 3-512 characters from [a-zA-Z0-9._-]` | `VECTOR_STORE_COLLECTION` is too short or contains other characters | Use a valid name (default `insurance_rag`) |
| `warning: LF will be replaced by CRLF` during git commands | Git's line-ending setting on Windows | Harmless |
| `huggingface_hub cache-system uses symlinks...` | Windows without Developer Mode | Harmless; the launcher already hides it for the servers |
| Want a clean rebuild of the index | | **Documents → Re-index**, or stop the app, delete `data\vectorstore\`, and run again |
| Want to start completely fresh | | Stop the app; delete `.venv\` and `.env`; run `python run.py` |

---

## Appendix A: API routes (60 operations)

Generated from the running application. Interactive version: `http://localhost:8000/api/docs`.

| Area | Method and path | Purpose |
|---|---|---|
| System | `GET /`, `GET /health` | service info, health |
| | `GET /api/system/status` | component health and the open-source stack |
| | `POST /api/system/selftest` | real round trip through each tool |
| | `GET /api/system/logs` | tail of `logs/*.log` |
| Search & Q&A | `POST /api/ask` | the full RAG pipeline |
| Documents | `GET /api/documents` | list documents |
| | `POST /api/documents/upload`, `POST /api/documents/reindex` | add / rebuild |
| | `DELETE /api/documents/{filename}` | remove a document and its vectors |
| | `GET /api/documents/{filename}/chunks` | inspect chunks (strategy, size, overlap) |
| | `POST /api/documents/{filename}/chunk-compare` | chunk-size experiment |
| Evaluation & Judge | `GET /api/evaluate/datasets`, `GET /insurance/results`, `POST /insurance/run` | current-corpus retrieval evaluation |
| | `GET /api/evaluate/metrics`, `GET /results/{mode}`, `POST /run` | historical results and live run (the live run needs Ollama per its description) |
| | `POST /api/evaluate/assertions`, `POST /judge`, `GET /judge-validation` | assertions, LLM judge, judge validation |
| | `GET /api/evaluate/regression`, `POST /regression/run` | failure-to-test cases |
| Failure Analysis | `GET /api/failures`, `POST /api/failures/label` | labels |
| Agent Loops & Benchmark | `GET /api/agent/claims`, `POST /triage`, `POST /benchmark` | agent vs fixed workflow |
| MCP Ecosystem | `GET /api/mcp/servers`, `POST /call`, `POST /triage`, `POST /config` | tool discovery and calls |
| Multi-Agent Squad | `GET /api/multi-agent/agents`, `POST /triage`, `POST /benchmark` | A2A squad |
| Observability & Caching | `GET /api/observability/traces`, `GET /traces/{trace_id}`, `POST /replay` | traces and replay |
| | `POST /api/observability/drill`, `POST /cache-benchmark` | support drill, cache benchmark |
| | `GET /api/observability/otel` | exporter status and recent spans |
| | `GET /error-analysis/sample`, `POST /notes`, `GET /taxonomy`, `POST /prediction` | error analysis |
| Foundations Lab | `POST /api/foundations/tokenize`, `/cost`, `/sampling`, `/similarity` | Week 1 lab |
| Guardrails | `POST /api/guardrails/scope`, `GET /structured/schema`, `POST /structured/validate`, `POST /structured/generate` | input guardrail, structured output |
| | `GET /api/guardrails/injection/demo`, `POST /injection/scan`, `POST /injection/scan-retrieval`, `GET /tools` | prompt-injection scan, tool permissions |
| Capstone | `POST /api/capstone/suite`, `GET /weak-spots`, `GET /demo` | Week 12 |

## Appendix B: environment variables

Read by the code (found by scanning `src/`, `ui/` and `run.py`). All are optional; `.env.example` lists 11 of them (everything except `OLLAMA_HOST`, `BACKEND_HOST`, `BACKEND_URL`, `TESSERACT_PATH` and `RAG_IN_VENV`).

| Variable | Default | Read in | Meaning |
|---|---|---|---|
| `OLLAMA_MODEL` | `llama3.2` | `config.py`, `run.py` | local LLM model name |
| `OLLAMA_HOST` | `http://localhost:11434` | `run.py` (preflight); the `ollama` client also reads it | where Ollama listens |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | `config.py`, `run.py` | embedding model |
| `RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | `config.py`, `run.py` | reranker model |
| `VECTOR_STORE_DIR` | `data/vectorstore` | `config.py`, `run.py` | ChromaDB folder |
| `VECTOR_STORE_COLLECTION` | `insurance_rag` | `config.py` | collection name (3+ characters of letters, digits, `. _ -`) |
| `OTEL_SERVICE_NAME` | `insurance-rag` | `config.py` | service name on spans |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | empty | `config.py` | also send spans to this OTLP/HTTP URL |
| `RAG_DOCUMENT` | `InsurancePolicy.pdf` | `config.py` | default document in `resources/` |
| `BACKEND_PORT` / `FRONTEND_PORT` | `8000` / `8501` | `run.py`, `config.py` | ports (the launcher moves to the next free port if busy) |
| `FRONTEND_ORIGINS` | localhost origins | `config.py` | CORS allow-list |
| `BACKEND_HOST` | `127.0.0.1` | `run.py` | API bind address; leave local, the API has no authentication |
| `BACKEND_URL` | `http://localhost:8000` | `ui/api_client.py`, set by `run.py` | where the UI finds the API |
| `TESSERACT_PATH` | auto-detected | `ingestion/pdfreader.py`, `run.py` | path to `tesseract.exe` |
| `RAG_IN_VENV` | unset | `run.py` | set to `1` to use the interpreter you started instead of `.venv` |

`run.py` also sets `PYTHONPATH`, `PYTHONIOENCODING` and `HF_HUB_DISABLE_SYMLINKS_WARNING` for the two child processes.

## Appendix C: files and folders the app reads and writes

| Path | Purpose | In git? |
|---|---|---|
| `resources/*.pdf` | policy documents that are indexed | yes |
| `data/vectorstore/` | ChromaDB files | no (generated) |
| `data/evaluation_dataset_insurance.json` | the 12-question evaluation set | yes |
| `data/insurance_results_*.json` | latest retrieval evaluation per mode | yes |
| `data/error_analysis.json` | notes and prediction from Error Analysis | created on use |
| `data/failure_labels.json`, `data/labels_25.json`, `data/*.json` | labels, judge data, MCP configs, historical results | yes |
| `traces/production_traces.jsonl`, `traces/traces.jsonl` | request traces | yes (and appended by use) |
| `traces/otel_spans.jsonl` | exported OpenTelemetry spans | no |
| `logs/backend.log`, `logs/frontend.log` | process output | no |
| `.env` | your settings | no |
| `.venv/` | the project's Python environment | no |
| `.streamlit/config.toml` | UI themes (light and dark) | yes |

## Appendix D: UI pages

Eight sidebar groups, 14 pages (paths are what you type after `http://localhost:8501`): Start (`/`, `/documentation`), Learn & Guardrails (`/foundations`, `/guardrails`), Documents & Answers (`/documents`, `/search`), Evaluate (`/evaluation`, `/error-analysis`), Agents (`/agent-triage`, `/mcp`, `/multi-agent`), Production (`/observability`), Capstone (`/capstone`), System (`/system`). The menu at the top right has a System / Light / Dark theme switcher.

## Appendix E: what was verified, and what was not

**Verified by running it (2026-10-25):**

- A real `git clone https://github.com/MashaAllah411/Rag_Week_3.git` into an empty folder, then `python run.py` from the system Python with no pip cache and an empty model cache: virtual environment, packages, `.env`, models, indexing of 128 passages, API and UI up in about 196 s; 9 of 9 scripted API checks passed; Ctrl+Break shutdown exited 0 with no leftover processes and both ports free.
- The manual start commands in 4.4 and the `Invoke-RestMethod` commands in 4.7 (health, status, ask).
- 64 tests passing; 29 of 29 browser checks across all 14 pages in a real Chromium; theme switcher behaviour (13 of 13).
- OTLP export to a stand-in collector, and ingestion of the app's spans by Arize Phoenix 20.26.0 (5 spans from one real request visible in its UI).
- `winget` package ids for Python, Git, Tesseract and Ollama (existence only; Ollama itself was not installed or run).
- Package versions and import sites, environment variables, API routes, and the span/trace file formats, read from the repository and the installed environment.

**Not verified:**

- Anything that needs Ollama running: written answers, query rewrite, the LLM judge, live structured output, trace replay, the capstone end-to-end check. Only their "Ollama is not running" behaviour was exercised.
- The `ollama serve` / `ollama pull` / `ollama list` commands themselves.
- macOS or Linux; Python versions other than 3.12; Windows versions other than Windows 11; offline use after setup.
- Jaeger or any OTLP backend other than the stand-in collector and Phoenix.
- Memory use and behaviour under load; the documents upload and delete buttons (they change `resources/`); the semantic chunking strategy.
