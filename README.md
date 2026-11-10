# Insurance Policy & Claims RAG Platform

Upload insurance policy PDFs, ask questions and get cited answers, triage claims with agents, and evaluate, trace and inspect everything from one UI. It brings the Week 1-12 curriculum together as a single application with open-source tooling throughout: ChromaDB, OpenTelemetry, Tesseract, sentence-transformers, BM25 and Ollama. No account or API key is needed.

## Documentation

| Read this | For |
|---|---|
| [docs/setup.md](docs/setup.md) | install, configure, run, test, troubleshoot |
| [docs/architecture.md](docs/architecture.md) | design, diagrams, data flow, tool choices and the open-source swaps |
| [docs/technical-reference.md](docs/technical-reference.md) | packages and where they are used, monitoring and dashboards, fresh-machine setup, exact PowerShell commands, verification and troubleshooting |
| [docs/features.md](docs/features.md) | every capability by week: what it does, where to use it, endpoints, how real it is |
| [docs/legacy.md](docs/legacy.md) | everything archived in `legacy/`: old path, replacement, reason |
| [docs/weekly/](docs/weekly/README.md) | historical weekly notes |
| *Documentation* page in the UI | end-user guide with diagrams and step-by-step walkthroughs |

## Quick start

On a fresh machine you need only Python 3.10+:

1. Install Python from <https://www.python.org/downloads/>.
2. Clone or unzip this repository and open a terminal in its folder.
3. Run `python run.py`.
4. If it stops and lists keys to fill in, edit `.env` and run `python run.py` again (this project currently needs none).

The first run creates `.venv`, installs the dependencies, creates `.env`, downloads the models, checks for optional services, then starts everything. Later runs do a fast check and start straight away. No activation, `pip install` or file copying by hand. `python run.py --setup` prepares the machine without starting the servers. Details: [docs/setup.md](docs/setup.md).

`python run.py` starts the API and the UI together, waits until the API answers `/health`, opens the browser, and shuts everything down cleanly on `Ctrl+C`.

- UI: http://localhost:8501
- API docs: http://localhost:8000/api/docs
- Optional: [Ollama](https://ollama.com) with `llama3.2` for written answers, query rewriting and the LLM judge, and Tesseract for OCR. The launcher tells you if either is missing and how to add it. Everything else works without them.

## What is in the UI

Pages are grouped in the sidebar by what you are trying to do:

| Group | Pages |
|---|---|
| Start | Home, Documentation |
| Learn & Guardrails | Foundations Lab (Week 1), Guardrails & Security (Weeks 2, 8) |
| Documents & Answers | Documents (Week 3), Search & Q&A (Weeks 3-4) |
| Evaluate | Evaluation (Weeks 4, 6, 11), Error Analysis (Week 5) |
| Agents | Agent Triage (Weeks 7-8), MCP Ecosystem (Week 9), Multi-Agent Squad (Week 10) |
| Production | Observability (Weeks 5, 11) |
| Capstone | Capstone (Week 12), HR Policy Desk (Variant C) |
| System | System & Health |

### Week 12 Capstone — Variant C: HR Policy Answer Desk
To run and test Variant C (HR Policy across India & UK entities):
1. Launch with `python run.py`.
2. Open `http://localhost:8501` and navigate to **Capstone ➔ HR Policy Desk (Variant C)** in the sidebar.
3. Test pre-configured scenarios:
   - **Entity Annex Silent Override:** India Maternity 26 weeks silently beating 12/16w handbook.
   - **Superseded Version Citation:** March 2024 parental leave query citing the 2024 policy with effective dates.
   - **Discretionary Escalation:** Sabbaticals >3 months auto-escalate to an HRBP with ticket SLA.
   - **Adversarial Colleague Privacy:** Refusal on coworker inquiries without leaking Grade or PII.
4. Run the 25-case evaluation suite directly from the second tab. Detailed submission docs are in `docs/`:
   - `docs/tuesday_seam_list.md` (Tuesday's unedited seam list)
   - `docs/architecture_sketch.md` (One-page architecture & cost sketch)
   - `docs/eval_report.md` (25-case eval report with stated non-coverage)
   - `docs/top_3_weaknesses.md` (Top 3 unprompted weaknesses dated Wednesday)
   - `docs/fresh_eyes_note.md` (Thursday peer reviewer audit note)
   - `traces/sample_variant_c_trace.json` (End-to-end trace with PII line held)

The System page shows which tools are actually running and can run a real self-test of each.

The menu in the top-right corner has a **System / Light / Dark** theme switcher; the choice is remembered across pages and refreshes.

## Repository layout

```
Rag_Week_3/
├── run.py                  one-command launcher (API + UI)
├── requirements.txt, pyproject.toml, .env.example, .streamlit/
├── src/rag/
│   ├── api/                FastAPI app and routers
│   ├── services/           orchestration called by the API
│   ├── ingestion/          PDF reading + OCR, chunking, indexing
│   ├── retrieval/          BM25, hybrid RRF, reranker, MMR
│   ├── generation/         LLM answer, structured output
│   ├── storage/            embedder, ChromaDB vector store
│   ├── evaluation/         retrieval eval, trajectory, failure labels, regression cases
│   ├── core/               scope guard, injection guard, query rewriter, providers
│   ├── agent/ agents/ mcp/ single agent, A2A squad, JSON-RPC MCP
│   ├── observability/      spans, OpenTelemetry bridge, support drill
│   ├── cache/ models/ scripts/ config.py
├── ui/                     Streamlit UI (app.py router, components.py, api_client.py, views/)
├── tests/                  pytest suite
├── data/                   datasets, prompts, MCP configs, saved results
├── resources/              policy PDFs
├── traces/                 request traces (JSONL)
├── docs/                   architecture, setup, features, legacy index, weekly notes
└── legacy/                 archived scripts and files, grouped by week
```

## Tests

```powershell
python -m pytest tests -q
```

## Honest limits

Some parts are scripted or simulated, and the UI labels them: the agent loop follows a fixed plan, MCP servers are called in-process, the support drill runs on generated traces with one planted failure, and the cache benchmark simulates latency and cost. Details are in [docs/features.md](docs/features.md) and the Capstone page's *Known weak spots*.
