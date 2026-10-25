# Root-level copies archived from the project root

These files sat loose at the repo root. Each was byte-compared (sha256) with the copy already in legacy/ before moving.

| File | sha256 (root copy) | Matches legacy/ copy? |
|---|---|---|
| eval_assertions.py | `d5d529c6fb528d32…` | identical |
| evaluate_all.py | `3e08bd07d7de5dfc…` | identical |
| generate_traces.py | `f4102906d72ccde3…` | identical |
| inspect_sampled_traces.py | `a6a98e880ef863d1…` | identical |
| race_benchmark.py | `0d8f528ee4158d60…` | identical |
| run_server.py | `275243cb3cba7cb2…` | identical |
| run_week10_race.py | `669a1a4d9b47beaf…` | identical |
| run_week11_eval.py | `397ff467a0481c39…` | identical |
| run_week8_eval.py | `b906958404a0ba9c…` | identical |
| run_week9_mcp.py | `c8299107487ded96…` | identical |
| sample_traces.py | `c6f116c4bc9e9b6e…` | identical |
| test_replay.py | `8dd62b9de669b204…` | identical |
| tracer.py | `0cbfc92c3c1ef4ff…` | DIFFERENT (root copy is a compat stub forwarding to rag.observability.tracer) |
