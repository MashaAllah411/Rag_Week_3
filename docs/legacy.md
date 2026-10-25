# Legacy index

Everything superseded, duplicated or no longer used was moved into `legacy/` instead of being deleted. Nothing was dropped silently. Files are grouped by the week or feature they belong to.

- [Architecture](architecture.md) · [Setup](setup.md) · [Features](features.md) · [Technical reference](technical-reference.md)

> **Archived scripts are for reference only.** They import module paths from before the consolidation (for example `rag.core.retrieval...`, `rag.infra...`, `rag.scripts.main_rag`) and some expect to run from the repo root with sibling modules. They are kept as a record, not as runnable tools. Use the replacement listed for each.

## 1. Loose files at the project root

The project root held 12 scripts that were byte-identical copies of files already in `legacy/`, plus a compatibility stub, a log and a CSV. They were moved to `legacy/_root_copies/` (duplicates and stub) or `legacy/week07/` (outputs). SHA-256 hashes of the duplicates are recorded in [`legacy/_root_copies/NOTE.md`](../legacy/_root_copies/NOTE.md).

| Old path | Now | Replaced by / why archived |
|---|---|---|
| `eval_assertions.py`, `evaluate_all.py` | `legacy/_root_copies/` (identical copy also at `legacy/week06/`) | Duplicate of `legacy/week06/`. Logic lives in `services/evaluation_service.py` and the Evaluation page |
| `generate_traces.py`, `sample_traces.py`, `test_replay.py`, `inspect_sampled_traces.py` | `legacy/_root_copies/` (identical copy also at `legacy/week05/`) | Duplicates. Replaced by the Observability and Error Analysis pages |
| `race_benchmark.py` | `legacy/_root_copies/` (copy at `legacy/week07/`) | Duplicate. Replaced by `services/agent_service.py` and the Agent Triage page |
| `run_week8_eval.py` | `legacy/_root_copies/` (copy at `legacy/week08/`) | Duplicate. Replaced by `evaluation/trajectory_eval.py` and Agent Triage |
| `run_week9_mcp.py` | `legacy/_root_copies/` (copy at `legacy/week09/`) | Duplicate. Replaced by `services/mcp_service.py` and MCP Ecosystem |
| `run_week10_race.py` | `legacy/_root_copies/` (copy at `legacy/week10/`) | Duplicate. Replaced by `services/multi_agent_service.py` and Multi-Agent Squad |
| `run_week11_eval.py` | `legacy/_root_copies/` (copy at `legacy/week11/`) | Duplicate. Replaced by the Observability page and the Capstone suite |
| `run_server.py` | `legacy/_root_copies/` (copy at `legacy/week04_web_ui/`) | Duplicate. Replaced by `python run.py` |
| `tracer.py` (root) | `legacy/_root_copies/tracer.py` | A stub that only re-exported `rag.observability.tracer`; the full Week 5 version is at `legacy/week05/tracer.py` |
| `budget_termination.log` | `legacy/week07/budget_termination.log` | Sample output of the Week 7 budget run |
| `race.csv` | `legacy/week07/race.csv` | Sample output of the Week 7 race |

## 2. Existing `legacy/` scripts, regrouped by week

| Old path | Now |
|---|---|
| `legacy/tracer.py`, `generate_traces.py`, `sample_traces.py`, `test_replay.py`, `inspect_sampled_traces.py` | `legacy/week05/` |
| `legacy/eval_assertions.py`, `evaluate_all.py` | `legacy/week06/` |
| `legacy/race_benchmark.py` | `legacy/week07/` |
| `legacy/run_week8_eval.py` | `legacy/week08/` |
| `legacy/run_week9_mcp.py` | `legacy/week09/` |
| `legacy/run_week10_race.py` | `legacy/week10/` |
| `legacy/run_week11_eval.py` | `legacy/week11/` |
| `legacy/run_server.py` | `legacy/week04_web_ui/` |

## 3. Code moved out of `src/rag/`

| Old path | Now | Replaced by / why archived |
|---|---|---|
| `src/rag/scripts/main_rag.py` | `legacy/week03_04_cli/` | Console version of the hybrid + rerank + MMR pipeline; superseded by `services/pipeline.py` and Search & Q&A |
| `src/rag/scripts/queryprocessor.py` | `legacy/week03_04_cli/` | Week 3 console query script; same replacement |
| `src/rag/scripts/chunk_inspector.py` | `legacy/week03_04_cli/` | Wrote `chunk_map.txt` from the console; superseded by `GET /api/documents/{file}/chunks` and the Documents page |
| `src/rag/web/` (HTML, CSS, JS) | `legacy/week04_web_ui/web/` | The Week 4 browser UI; replaced by the Streamlit UI. The `/legacy-web` and `/static` routes were removed from the API |
| `src/rag/infra/vectorstore.py` (Pinecone implementation) | `legacy/pinecone/vectorstore_pinecone.py` | Replaced by the ChromaDB store in `storage/vectorstore.py` (open-source swap) |
| `src/rag_week_3.egg-info/` | `legacy/build_artifacts/rag_week_3.egg-info/` | Generated packaging metadata that had been committed; `pip install -e .` regenerates it |
| `src/rag/core/ingest/__init__.py`, `src/rag/core/retrieval/__init__.py`, `src/rag/infra/__init__.py` | `legacy/_stale_packages/` | Empty markers of packages that no longer exist |

## 4. Modules renamed into the target package structure (not archived)

These files still exist and are live; only their import path changed.

| Old import path | New import path |
|---|---|
| `rag.core.ingest.pdfreader`, `.chunker` | `rag.ingestion.pdfreader`, `rag.ingestion.chunker` |
| `rag.scripts.dataprocessor` | `rag.ingestion.indexer` |
| `rag.core.retrieval.bm25`, `.hybrid_retriever`, `.mmr`, `.reranker` | `rag.retrieval.bm25`, `.hybrid_retriever`, `.mmr`, `.reranker` |
| `rag.infra.llm` | `rag.generation.llm` |
| `rag.infra.embedder` | `rag.storage.embedder` |
| `rag.infra.vectorstore` (Pinecone) | `rag.storage.vectorstore` (ChromaDB; functions renamed `store_chunks`, `search_chunks`, `delete_document`) |
| `rag.scripts.evaluator` | `rag.evaluation.retrieval_eval` |
| `rag.agent.trajectory_eval` | `rag.evaluation.trajectory_eval` |
| `rag.services.failure_labeler` | `rag.evaluation.failure_labeler` |

## 5. Other relocations

| Old path | Now | Note |
|---|---|---|
| `documentation/` (22 weekly notes and guides) | `docs/weekly/` | Historical notes; see [`docs/weekly/README.md`](weekly/README.md) |
| `ui/pages/1_Documents.py` ... `8_System.py` | `ui/views/documents.py` ... `system.py` | The UI now uses grouped navigation (`ui/app.py` is the router) |
| the old `ui/app.py` landing page | `ui/views/home.py` | |
| `Ai Task List/` (empty folder at the root) | removed | It contained no files |
| guardrail function defined inside a test | `src/rag/evaluation/regression.py` | The test and the UI now share one implementation |

## 6. Why `legacy/` still holds both an original and a root copy

Because the root copies were byte-identical to the originals, keeping both is redundant, but the rules for this consolidation forbid deleting files. The root copies sit in `legacy/_root_copies/` with recorded hashes so that deleting them later is a safe, verifiable decision for the repository owner.
