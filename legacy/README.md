# Legacy archive

Superseded, duplicated or unused files, kept for reference. **Nothing here is imported by the application.**

The full index (old path, new location or replacement, and why) is in [`docs/legacy.md`](../docs/legacy.md).

| Folder | Contents |
|---|---|
| `_root_copies/` | Files that sat loose at the project root. 12 were byte-identical to the weekly copies below (hashes in `NOTE.md`); `tracer.py` was a compatibility stub |
| `_stale_packages/` | Empty `__init__.py` markers of packages that were merged away |
| `build_artifacts/` | Committed packaging metadata (`rag_week_3.egg-info/`) |
| `pinecone/` | The previous Pinecone vector-store implementation, replaced by ChromaDB |
| `week03_04_cli/` | Console scripts for the Week 3-4 pipeline (`main_rag.py`, `queryprocessor.py`, `chunk_inspector.py`) |
| `week04_web_ui/` | The Week 4 browser UI (`web/`) and the old `run_server.py` |
| `week05/` | Tracing, trace generation, seeded sampling, replay (`tracer.py`, `generate_traces.py`, `sample_traces.py`, `test_replay.py`, `inspect_sampled_traces.py`) |
| `week06/` | Assertions and the unified eval suite (`eval_assertions.py`, `evaluate_all.py`) |
| `week07/` | Agent race and sample outputs (`race_benchmark.py`, `budget_termination.log`, `race.csv`) |
| `week08/` | Trajectory evaluation runner (`run_week8_eval.py`) |
| `week09/` | MCP verification runner (`run_week9_mcp.py`) |
| `week10/` | Multi-agent race runner (`run_week10_race.py`) |
| `week11/` | Production-eval runner (`run_week11_eval.py`) |

## Where each capability lives now

| Archived script | Live replacement |
|---|---|
| `run_server.py` (Week 4) | `python run.py` |
| `tracer.py`, `generate_traces.py`, `sample_traces.py`, `test_replay.py`, `inspect_sampled_traces.py` (Week 5) | `src/rag/observability/`, UI: Observability, Error Analysis |
| `eval_assertions.py`, `evaluate_all.py` (Week 6) | `src/rag/services/evaluation_service.py`, UI: Evaluation |
| `race_benchmark.py` (Week 7) | `src/rag/services/agent_service.py`, UI: Agent Triage |
| `run_week8_eval.py` (Week 8) | `src/rag/evaluation/trajectory_eval.py`, UI: Agent Triage |
| `run_week9_mcp.py` (Week 9) | `src/rag/services/mcp_service.py`, UI: MCP Ecosystem |
| `run_week10_race.py` (Week 10) | `src/rag/services/multi_agent_service.py`, UI: Multi-Agent Squad |
| `run_week11_eval.py` (Week 11) | UI: Observability and Capstone |
| `main_rag.py`, `queryprocessor.py` (Weeks 3-4) | `src/rag/services/pipeline.py`, UI: Search & Q&A |
| `chunk_inspector.py` (Week 3) | UI: Documents (chunk inspector and chunk-size experiment) |
| `vectorstore_pinecone.py` | `src/rag/storage/vectorstore.py` (ChromaDB) |

These scripts import module paths from before the consolidation, so they will not run unmodified.
