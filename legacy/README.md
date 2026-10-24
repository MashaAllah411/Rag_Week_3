# Legacy Scripts Archive

This directory preserves the historical week-by-week scripts and evaluation runners from Weeks 1 through 11.
In the refactored architecture, all underlying logic has been promoted into production modules under `src/rag/` and exposed via the FastAPI backend and Streamlit UI. These standalone scripts are preserved here for reference, verification, and benchmarking.

## Preserved Files Inventory

| File | Origin | Purpose / Functionality | Refactored Equivalent |
|---|---|---|---|
| `run_server.py` | Week 4 | Historical entrypoint for uvicorn server with Jinja2 frontend | `run.py` (orchestrates backend + UI) |
| `tracer.py` | Week 5 | PII-redacted tracing framework and replay helper | `src/rag/observability/tracer.py` |
| `generate_traces.py` | Week 5 | Generates 50+ diverse test traces for offline analysis | `src/rag/services/observability_service.py` & UI Page 7 |
| `sample_traces.py` | Week 5 | Deterministically samples 20 traces (seed=42) | UI Page 7 (Observability) |
| `test_replay.py` | Week 5 | Replays single trace against LLM with original context | UI Page 7 (Observability replay) |
| `eval_assertions.py` | Week 6 | 4 regex deterministic assertions (claim ID, date, deductible, clause) | `src/rag/services/evaluation_service.py` |
| `evaluate_all.py` | Week 6 | Runs 25+ assertions + LLM Judge V1 & V2 prompt calibration | `src/rag/services/evaluation_service.py` & UI Page 6 |
| `race_benchmark.py` | Week 7 | Benchmark racing ReAct Agent (with 4 budgets) vs Fixed Workflow | `src/rag/services/agent_service.py` & UI Page 3 |
| `run_week8_eval.py` | Week 8 | Evaluates agent trajectory paths, tool accuracy, and step efficiency | `src/rag/agent/trajectory_eval.py` & UI Page 3 |
| `run_week9_mcp.py` | Week 9 | Verifies MCP JSON-RPC protocol, tool discovery, and policy/claims servers | `src/rag/services/mcp_service.py` & UI Page 4 |
| `run_week10_race.py` | Week 10 | Races Single Agent vs Multi-Agent Claims Squad (A2A protocol) | `src/rag/services/multi_agent_service.py` & UI Page 5 |
| `run_week11_eval.py` | Week 11 | Production spans, support triage drill, semantic cache benchmark | `src/rag/services/observability_service.py` & UI Page 7 |
| `inspect_sampled_traces.py`| Week 5 | Prints 20 sampled traces verbatim | UI Page 7 |
