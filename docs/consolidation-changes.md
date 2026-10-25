# Consolidation change inventory

Generated from the working tree against `HEAD` (read-only git). Nothing is committed or staged.

- Modified in place: **32**
- Moved (identical content): **69**
- Moved and edited: **17**
- Created: **43**
- Removed with no counterpart: **0**

## Modified in place (32)

- `.env.example`
- `.gitignore`
- `README.md`
- `legacy/README.md`
- `pyproject.toml`
- `requirements.txt`
- `resources/README.md`
- `run.py`
- `src/rag/agent/tools.py`
- `src/rag/api/main.py`
- `src/rag/api/routes/ask.py`
- `src/rag/api/routes/documents.py`
- `src/rag/api/routes/evaluate.py`
- `src/rag/api/routes/failures.py`
- `src/rag/api/routes/observability.py`
- `src/rag/api/routes/system.py`
- `src/rag/config.py`
- `src/rag/core/providers.py`
- `src/rag/mcp/policy_server.py`
- `src/rag/models/schemas.py`
- `src/rag/observability/tracer.py`
- `src/rag/services/agent_service.py`
- `src/rag/services/evaluation_service.py`
- `src/rag/services/multi_agent_service.py`
- `src/rag/services/pipeline.py`
- `tests/test_chunker.py`
- `tests/test_failure_loop_regression.py`
- `tests/test_health_smoke.py`
- `tests/test_hybrid.py`
- `tests/test_mmr.py`
- `ui/api_client.py`
- `ui/app.py`

## Moved (identical content; archived or relocated) (69)

- `documentation/WEEK10_GUIDE.md` -> `docs/weekly/WEEK10_GUIDE.md`
- `documentation/WEEK11_CONCEPTS_MASTER_GUIDE.md` -> `docs/weekly/WEEK11_CONCEPTS_MASTER_GUIDE.md`
- `documentation/WEEK11_GUIDE.md` -> `docs/weekly/WEEK11_GUIDE.md`
- `documentation/WEEK5_GUIDE.md` -> `docs/weekly/WEEK5_GUIDE.md`
- `documentation/WEEK6_GUIDE.md` -> `docs/weekly/WEEK6_GUIDE.md`
- `documentation/WEEK7_GUIDE.md` -> `docs/weekly/WEEK7_GUIDE.md`
- `documentation/WEEK8_GUIDE.md` -> `docs/weekly/WEEK8_GUIDE.md`
- `documentation/WEEK9_GUIDE.md` -> `docs/weekly/WEEK9_GUIDE.md`
- `documentation/a2a_transcript.md` -> `docs/weekly/a2a_transcript.md`
- `documentation/agent_diff.txt` -> `docs/weekly/agent_diff.txt`
- `documentation/error_before_after.md` -> `docs/weekly/error_before_after.md`
- `documentation/notes.md` -> `docs/weekly/notes.md`
- `documentation/notes_w6.md` -> `docs/weekly/notes_w6.md`
- `documentation/risk_note.md` -> `docs/weekly/risk_note.md`
- `documentation/taxonomy.md` -> `docs/weekly/taxonomy.md`
- `documentation/ten_x_plan.md` -> `docs/weekly/ten_x_plan.md`
- `documentation/tool_diff.md` -> `docs/weekly/tool_diff.md`
- `documentation/trajectory_notes.md` -> `docs/weekly/trajectory_notes.md`
- `documentation/verdict.txt` -> `docs/weekly/verdict.txt`
- `documentation/week10_verdict.txt` -> `docs/weekly/week10_verdict.txt`
- `documentation/week3_rag_explainer.md` -> `docs/weekly/week3_rag_explainer.md`
- `documentation/week4_architecture.md` -> `docs/weekly/week4_architecture.md`
- `eval_assertions.py` -> `legacy/_root_copies/eval_assertions.py`
- `evaluate_all.py` -> `legacy/_root_copies/evaluate_all.py`
- `generate_traces.py` -> `legacy/_root_copies/generate_traces.py`
- `inspect_sampled_traces.py` -> `legacy/_root_copies/inspect_sampled_traces.py`
- `legacy/race_benchmark.py` -> `legacy/_root_copies/race_benchmark.py`
- `legacy/run_server.py` -> `legacy/_root_copies/run_server.py`
- `legacy/run_week10_race.py` -> `legacy/_root_copies/run_week10_race.py`
- `legacy/run_week11_eval.py` -> `legacy/_root_copies/run_week11_eval.py`
- `legacy/run_week8_eval.py` -> `legacy/_root_copies/run_week8_eval.py`
- `legacy/run_week9_mcp.py` -> `legacy/_root_copies/run_week9_mcp.py`
- `legacy/sample_traces.py` -> `legacy/_root_copies/sample_traces.py`
- `legacy/test_replay.py` -> `legacy/_root_copies/test_replay.py`
- `tracer.py` -> `legacy/_root_copies/tracer.py`
- `src/rag/core/ingest/__init__.py` -> `legacy/_stale_packages/core_ingest/__init__.py`
- `src/rag/core/retrieval/__init__.py` -> `legacy/_stale_packages/core_retrieval/__init__.py`
- `src/rag/infra/__init__.py` -> `legacy/_stale_packages/infra/__init__.py`
- `src/rag_week_3.egg-info/PKG-INFO` -> `legacy/build_artifacts/rag_week_3.egg-info/PKG-INFO`
- `src/rag_week_3.egg-info/SOURCES.txt` -> `legacy/build_artifacts/rag_week_3.egg-info/SOURCES.txt`
- `src/rag_week_3.egg-info/dependency_links.txt` -> `legacy/build_artifacts/rag_week_3.egg-info/dependency_links.txt`
- `src/rag_week_3.egg-info/requires.txt` -> `legacy/build_artifacts/rag_week_3.egg-info/requires.txt`
- `src/rag_week_3.egg-info/top_level.txt` -> `legacy/build_artifacts/rag_week_3.egg-info/top_level.txt`
- `src/rag/infra/vectorstore.py` -> `legacy/pinecone/vectorstore_pinecone.py`
- `src/rag/scripts/chunk_inspector.py` -> `legacy/week03_04_cli/chunk_inspector.py`
- `src/rag/scripts/main_rag.py` -> `legacy/week03_04_cli/main_rag.py`
- `src/rag/scripts/queryprocessor.py` -> `legacy/week03_04_cli/queryprocessor.py`
- `run_server.py` -> `legacy/week04_web_ui/run_server.py`
- `src/rag/web/__init__.py` -> `legacy/week04_web_ui/web/__init__.py`
- `src/rag/web/static/css/style.css` -> `legacy/week04_web_ui/web/static/css/style.css`
- `src/rag/web/static/js/app.js` -> `legacy/week04_web_ui/web/static/js/app.js`
- `src/rag/web/templates/index.html` -> `legacy/week04_web_ui/web/templates/index.html`
- `legacy/generate_traces.py` -> `legacy/week05/generate_traces.py`
- `legacy/inspect_sampled_traces.py` -> `legacy/week05/inspect_sampled_traces.py`
- `sample_traces.py` -> `legacy/week05/sample_traces.py`
- `test_replay.py` -> `legacy/week05/test_replay.py`
- `legacy/tracer.py` -> `legacy/week05/tracer.py`
- `legacy/eval_assertions.py` -> `legacy/week06/eval_assertions.py`
- `legacy/evaluate_all.py` -> `legacy/week06/evaluate_all.py`
- `budget_termination.log` -> `legacy/week07/budget_termination.log`
- `race.csv` -> `legacy/week07/race.csv`
- `race_benchmark.py` -> `legacy/week07/race_benchmark.py`
- `run_week8_eval.py` -> `legacy/week08/run_week8_eval.py`
- `run_week9_mcp.py` -> `legacy/week09/run_week9_mcp.py`
- `run_week10_race.py` -> `legacy/week10/run_week10_race.py`
- `run_week11_eval.py` -> `legacy/week11/run_week11_eval.py`
- `src/rag/agent/trajectory_eval.py` -> `src/rag/evaluation/trajectory_eval.py`
- `src/rag/infra/llm.py` -> `src/rag/generation/llm.py`
- `src/rag/core/ingest/chunker.py` -> `src/rag/ingestion/chunker.py`

## Moved and edited (17)

- `src/rag/scripts/dataprocessor.py` -> `src/rag/ingestion/indexer.py`
- `src/rag/scripts/evaluator.py` -> `src/rag/evaluation/retrieval_eval.py`
- `ui/pages/1_Documents.py` -> `ui/views/documents.py`
- `ui/pages/2_Search_and_QA.py` -> `ui/views/search_qa.py`
- `ui/pages/3_Agent_Triage.py` -> `ui/views/agent_triage.py`
- `ui/pages/4_MCP_Ecosystem.py` -> `ui/views/mcp.py`
- `ui/pages/5_Multi_Agent_Squad.py` -> `ui/views/multi_agent.py`
- `ui/pages/6_Evaluation.py` -> `ui/views/evaluation.py`
- `ui/pages/7_Observability.py` -> `ui/views/observability.py`
- `ui/pages/8_System.py` -> `ui/views/system.py`
- `src/rag/core/ingest/pdfreader.py` -> `src/rag/ingestion/pdfreader.py`
- `src/rag/core/retrieval/bm25.py` -> `src/rag/retrieval/bm25.py`
- `src/rag/core/retrieval/hybrid_retriever.py` -> `src/rag/retrieval/hybrid_retriever.py`
- `src/rag/core/retrieval/mmr.py` -> `src/rag/retrieval/mmr.py`
- `src/rag/core/retrieval/reranker.py` -> `src/rag/retrieval/reranker.py`
- `src/rag/infra/embedder.py` -> `src/rag/storage/embedder.py`
- `src/rag/services/failure_labeler.py` -> `src/rag/evaluation/failure_labeler.py`

## Created (43)

- `.streamlit/config.toml`
- `data/evaluation_dataset_insurance.json`
- `data/insurance_results_hybrid.json`
- `data/insurance_results_reranked.json`
- `data/insurance_results_semantic.json`
- `docs/architecture.md`
- `docs/consolidation-changes.md`
- `docs/features.md`
- `docs/legacy.md`
- `docs/setup.md`
- `docs/weekly/README.md`
- `legacy/_root_copies/NOTE.md`
- `src/rag/agent/__init__.py`
- `src/rag/api/routes/capstone.py`
- `src/rag/api/routes/foundations.py`
- `src/rag/api/routes/guardrails.py`
- `src/rag/cache/__init__.py`
- `src/rag/core/injection_guard.py`
- `src/rag/evaluation/__init__.py`
- `src/rag/evaluation/regression.py`
- `src/rag/generation/__init__.py`
- `src/rag/generation/structured.py`
- `src/rag/ingestion/__init__.py`
- `src/rag/observability/__init__.py`
- `src/rag/observability/otel.py`
- `src/rag/retrieval/__init__.py`
- `src/rag/services/capstone_service.py`
- `src/rag/services/error_analysis_service.py`
- `src/rag/services/foundations_service.py`
- `src/rag/services/health_service.py`
- `src/rag/storage/__init__.py`
- `src/rag/storage/vectorstore.py`
- `tests/test_launcher.py`
- `tests/test_new_capabilities.py`
- `tests/test_squad_service.py`
- `tests/test_theme_config.py`
- `ui/components.py`
- `ui/views/capstone.py`
- `ui/views/documentation.py`
- `ui/views/error_analysis.py`
- `ui/views/foundations.py`
- `ui/views/guardrails.py`
- `ui/views/home.py`

## Removed with no counterpart (0)

