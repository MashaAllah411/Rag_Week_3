# 🛡️ Enterprise Insurance Policy & Claims RAG Platform

Production-style refactored Retrieval-Augmented Generation (RAG) platform covering Weeks 1 through 11 curriculum, featuring hybrid retrieval, cross-encoder reranking, ReAct agent loops with budget governance, MCP (Model Context Protocol) tool integration, Multi-Agent Squads (A2A protocol), and span-level OpenTelemetry observability.

---

## 🏗️ System Architecture

```
                          ┌───────────────────────────┐
                          │   Streamlit Frontend UI   │
                          │   (http://localhost:8501) │
                          └─────────────┬─────────────┘
                                        │ HTTP calls only (ui/api_client.py)
                                        ▼
                          ┌───────────────────────────┐
                          │    FastAPI HTTP Backend   │
                          │   (http://localhost:8000) │
                          └─────────────┬─────────────┘
                                        │
      ┌──────────────────┬──────────────┼──────────────┬──────────────────┐
      ▼                  ▼              ▼              ▼                  ▼
┌───────────┐      ┌───────────┐  ┌───────────┐  ┌───────────┐      ┌───────────┐
│ Documents │      │  Search   │  │   Agent   │  │    MCP    │      │Observabil.│
│ & Ingest  │      │   & Q&A   │  │  Triage   │  │ Ecosystem │      │  & Spans  │
└─────┬─────┘      └─────┬─────┘  └─────┬─────┘  └─────┬─────┘      └─────┬─────┘
      │                  │              │              │                  │
      ▼                  ▼              ▼              ▼                  ▼
 [pypdf / OCR]    [BM25 + Pinecone] [4 Budgets]  [JSON-RPC 2.0]      [Span Tracing]
 [Chunking]       [Cross-Encoder]   [Laps Loop]  [Claims/Policy Srv] [Support Drill]
 [Embedder]       [MMR Diversity]   [Trajectory] [Tool Discovery]    [Semantic Cache]
```

### Key Architectural Standards
1. **Strict Layer Separation**: The UI (`ui/`) never imports backend internals. All interactions occur over the HTTP API client (`ui/api_client.py`).
2. **One-Command Launcher**: `python run.py` automatically validates ports, environment settings, boots FastAPI, waits for `/health`, launches Streamlit, and provides clean process tree shutdown on Ctrl+C.
3. **Budget Governance**: ReAct Agent enforces 4 strict budgets in code (max iterations, max tokens, max dollar cost, wall-clock timeout).
4. **Zero-Code MCP Discovery**: New MCP servers are plugged in via configuration only (`data/mcp_config.json`); zero lines of agent code change.
5. **Decoupled A2A Protocol**: Multi-agent claims squad communicates over structured `A2AMessage` envelopes with complete audit trails.

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.10+ (Windows PowerShell)
- Optional: [Ollama](https://ollama.ai) with `llama3.2` model (`ollama run llama3.2`) for local generation & query rewriting
- Optional: Pinecone Vector Database API Key for vector queries

### 2. Environment Setup
```powershell
# In your virtual environment:
python run.py --setup
```
This automatically verifies and installs all required dependencies from `requirements.txt`.

Ensure your `.env` contains your settings:
```ini
PINECONE_API_KEY=your_key_here
PINECONE_INDEX_NAME=rag-week-3-py
OLLAMA_MODEL=llama3.2
EMBEDDING_MODEL=all-MiniLM-L6-v2
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RAG_DOCUMENT=InsurancePolicy.pdf
BACKEND_PORT=8000
FRONTEND_PORT=8501
```

### 3. Start the Full Stack (One Command)
```powershell
python run.py
```
This command:
1. Validates the environment and `.env`
2. Checks that ports 8000 and 8501 are free (or assigns fallbacks)
3. Boots FastAPI with Uvicorn
4. Waits for `http://localhost:8000/health` to confirm healthy status
5. Boots Streamlit on `http://localhost:8501`
6. Opens the UI in your default browser
7. Pipes colored logs to the terminal and records them in `logs/backend.log` and `logs/frontend.log`
8. Shuts down cleanly on `Ctrl+C` (no orphaned Windows processes)

---

## 🧭 Comprehensive UI Guide

The unified Streamlit frontend exposes every capability from Weeks 1 through 11 across 8 dedicated pages:

| Page | Capability & Operations |
|---|---|
| **Home (`app.py`)** | Subsystem health indicator, live KPI metrics cards, quick-navigation cards |
| **1. Documents** | List indexed policy PDFs, view page count & size, upload new PDFs with background indexing, delete documents & vectors, reindex all, and inspect chunk boundaries |
| **2. Search & Q&A** | Natural language queries with quick suggested questions, retrieval mode switch (`semantic`, `hybrid`, `reranked`), similarity threshold & top-k sliders, query rewriter toggle, confidence badges, citations, and context inspection |
| **3. Agent Triage** | Claim triage with dynamic ReAct loop enforcing 4 budgets, fixed workflow comparison, budget termination stress tests, trajectory evaluation, and 10-claim race benchmark |
| **4. MCP Ecosystem** | Connected JSON-RPC 2.0 MCP servers, dynamically discovered tools, interactive tool execution, end-to-end claim triage, and live configuration swapping |
| **5. Multi-Agent Squad** | Inspect Agent Cards (Manager, Policy Specialist, Payout Specialist), run A2A squad triage, inspect message envelopes and full markdown hand-off transcripts, and race Single Agent vs Squad |
| **6. Evaluation & QA** | Retrieval quality improvement proof (Baseline vs Hybrid Hit Rate@3 & MRR), failure separation diagnosis with human reviewer overrides, deterministic regex assertions tester, and calibrated LLM Judge V1 vs V2 |
| **7. Observability** | OpenTelemetry span-level production traces, step latency & costing breakdown, deterministic trace replay, support triage drill locating planted failure, and semantic cache cost reduction benchmark (≥35%) |
| **8. System & Logs** | Component connection health (FastAPI, Ollama, Pinecone), environment configuration with secrets masked (`****`), vector index specifications, and live application logs |

---

## 📁 Repository Structure

```
Rag_Week_3/
├── pyproject.toml              # Build & package configuration
├── requirements.txt            # Dependency specification
├── README.md                   # System documentation & UI guide
├── .env.example                # Safe environment template (no real keys)
├── .gitignore                  # Git ignore rules
├── run.py                      # The unified one-command launcher
├── src/
│   └── rag/
│       ├── config.py           # Central application configuration
│       ├── core/               # Scope guard, query rewriter, document IDs, providers
│       ├── ingestion/          # PDF reader (OCR), chunking strategies, indexing
│       ├── retrieval/          # BM25, hybrid retriever (RRF), cross-encoder, MMR
│       ├── storage/            # Pinecone vector store operations
│       ├── generation/         # Ollama LLM provider & grounded prompts
│       ├── services/           # Pipeline, agent, MCP, multi-agent, cache, observability
│       ├── api/                # FastAPI factory, schemas, and 8 routers
│       └── web/                # Legacy HTML/CSS/JS interface
├── ui/
│   ├── app.py                  # Streamlit entrance & landing dashboard
│   ├── api_client.py           # Clean HTTP API client (no backend imports)
│   └── pages/                  # 8 modular capability pages
├── tests/                      # Unit tests & full health smoke test
├── data/                       # Datasets, prompts, MCP configs, benchmarks
├── resources/                  # Policy documents (PDFs)
├── traces/                     # Production traces (JSONL)
├── logs/                       # Backend and frontend log files
└── legacy/                     # Preserved historical week-by-week scripts
```

---

## 🧪 Running Tests

To run the complete test suite (18 tests verifying chunking, hybrid retrieval, MMR, scope guard, failure regression loop, and full API endpoint smoke tests):
```powershell
python -m pytest tests/ -v
```

---

## 📜 Legacy Scripts

All historical standalone runner scripts are preserved under `legacy/` with an explanatory `legacy/README.md` documenting their original context and their corresponding production module in the new architecture.
