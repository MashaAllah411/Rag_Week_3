"""
ui/views/observability.py

Observability (Weeks 5 and 11)
- Request traces: one span per step with time, tokens and cost (real app requests vs generated drill data)
- OpenTelemetry: what the SDK has exported and where it goes
- Trace replay from the context saved in a trace
- Support drill: find the planted bad answer from a vague complaint
- Cost and cache: the semantic-cache benchmark (a simulation)
"""
import streamlit as st

from ui.api_client import api
from ui.components import call, info_card, ollama_notice, page_header, pill, simulated_notice

page_header(
    "Observability",
    "📊",
    "If it isn't logged, it didn't happen. See what the app did on each request, step by step, and find a bad answer from a vague complaint.",
    weeks=("5", "11"),
)

REAL_REQUEST_ID = "ask"  # requests served by the app's /api/ask pipeline


def _ollama_up() -> bool:
    try:
        status = api.get_system_status()
        return bool(status.get("components", {}).get("ollama_llm", {}).get("reachable"))
    except Exception:
        return False


def _is_real(trace: dict) -> bool:
    return trace.get("request_id") == REAL_REQUEST_ID


def _fmt_ts(ts) -> str:
    import time
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ts)))
    except Exception:
        return str(ts)


tab_traces, tab_otel, tab_replay, tab_drill, tab_cache = st.tabs([
    "📈 Request traces", "🛰️ OpenTelemetry", "🔁 Trace replay", "🚨 Support drill", "⚡ Cost & cache",
])

# ── Request traces ───────────────────────────────────────────
with tab_traces:
    st.subheader("Request traces and step costs")
    ok, data = call(api.list_traces, limit=200, trace_type="production", spinner="Loading traces...")
    traces = (data or {}).get("traces", []) if ok else []

    if ok:
        real = [t for t in traces if _is_real(t)]
        drill = [t for t in traces if not _is_real(t)]
        c1, c2, c3 = st.columns(3)
        c1.metric("Real app requests", len(real), help="Questions answered through Search & Q&A (request id 'ask').")
        c2.metric("Generated drill traces", len(drill), help="Created by the support drill, with one planted failure.")
        c3.metric("Loaded (most recent 200)", len(traces))

        info_card("Token counts are estimates (about 4 characters per token) and cost is an <b>illustrative hosted-price equivalent</b>: "
                  "the models run locally, so the real per-token price is $0. Use the numbers to compare steps, not as a bill.")

        view = st.radio("Show", ["Real app requests", "Generated drill traces", "All"], horizontal=True)
        shown = real if view == "Real app requests" else drill if view == "Generated drill traces" else traces
        shown = list(reversed(shown))

        if view != "Real app requests":
            simulated_notice("Drill traces are generated for the Week 11 exercise. They contain one planted bad answer and use made-up claims.")

        if not shown:
            if view == "Real app requests":
                st.info("No real requests have been traced yet. Ask a question on the Search & Q&A page, then come back; "
                        "each answer is logged with one span per step (scope guard, query rewrite, retrieval, generation).")
                try:
                    st.page_link("views/search_qa.py", label="Go to Search & Q&A", icon="🔍")
                except Exception:
                    pass
            else:
                st.info("No traces in this view.")
        else:
            st.dataframe(
                [{"When": _fmt_ts(t.get("timestamp")), "Trace": t.get("trace_id"), "Kind": "real" if _is_real(t) else "drill",
                  "Query": (t.get("query") or "")[:70], "Spans": t.get("span_count"), "Tokens (est.)": t.get("total_tokens"),
                  "Cost (est., $)": round(t.get("total_cost_usd", 0.0), 6), "Status": t.get("status")} for t in shown[:50]],
                hide_index=True, width="stretch")

            labels = {t["trace_id"]: f"{_fmt_ts(t.get('timestamp'))}  ·  {t['trace_id']}  ·  {(t.get('query') or '')[:50]}" for t in shown[:50]}
            pick = st.selectbox("Inspect a trace", list(labels), format_func=labels.get)
            t = next(x for x in shown if x["trace_id"] == pick)
            st.markdown(pill("Real request", "ok") if _is_real(t) else pill("Generated drill trace", "sim"), unsafe_allow_html=True)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Status", t.get("status"))
            m2.metric("Total tokens (est.)", t.get("total_tokens"))
            m3.metric("Total cost (est.)", f"${t.get('total_cost_usd', 0.0):.6f}")
            m4.metric("Sum of step time", f"{t.get('total_duration_ms', 0.0):.1f} ms")
            st.caption("Each step is a span with its own start, duration, token count and cost, so you can see which step is slow or costly, not just one lump total.")
            st.dataframe(
                [{"Step": s.get("name"), "Duration (ms)": s.get("duration_ms"), "Tokens in": s.get("tokens_in"),
                  "Tokens out": s.get("tokens_out"), "Cost (est., $)": s.get("cost_usd"), "Status": s.get("status"),
                  "Error": s.get("error_message") or ""} for s in t.get("spans", [])],
                hide_index=True, width="stretch")
            with st.expander("Span attributes and final output"):
                for s in t.get("spans", []):
                    st.markdown(f"`{s.get('name')}`")
                    st.json(s.get("attributes", {}), expanded=False)
                st.json(t.get("final_output", {}), expanded=False)

# ── OpenTelemetry ────────────────────────────────────────────
with tab_otel:
    st.subheader("OpenTelemetry export")
    st.markdown("Every span above is also exported through the real OpenTelemetry SDK. This tab shows what the SDK has actually exported.")
    ok, otel = call(api.otel_status, limit=50, spinner="Reading OpenTelemetry status...")
    if ok:
        status = otel.get("status", {})
        o1, o2, o3, o4 = st.columns(4)
        o1.metric("SDK", "Active" if status.get("active") else "Inactive")
        o2.metric("SDK version", status.get("sdk_version", "n/a"))
        o3.metric("Service name", status.get("service_name", "n/a"))
        o4.metric("Spans exported this run", status.get("spans_exported", 0),
                  help="Counts since the backend started. The JSONL file below keeps earlier runs.")
        if status.get("error"):
            st.error(f"OpenTelemetry did not start: {status['error']}")
        st.markdown("**Exporters**")
        for exp in status.get("exporters", []):
            if exp.get("type") == "jsonl":
                st.markdown(pill("local file", "ok") + f" `{exp.get('path')}`", unsafe_allow_html=True)
            else:
                st.markdown(pill(exp.get("type", "otlp"), "ok") + f" `{exp.get('endpoint')}`", unsafe_allow_html=True)
        if not any(e.get("type") == "otlp-http" for e in status.get("exporters", [])):
            st.caption("No OTLP endpoint is set, so spans go to the local file only.")

        with st.expander("Send spans to Phoenix or Jaeger (optional)"):
            st.markdown(
                "Set `OTEL_EXPORTER_OTLP_ENDPOINT` in `.env` to any OTLP/HTTP collector, for example a self-hosted Arize Phoenix "
                "(`http://localhost:6006/v1/traces`) or Jaeger, then restart the app. Spans are then shipped there as well as to the local file. "
                "No hosted service is involved."
            )

        spans = list(reversed(otel.get("recent_spans", [])))
        st.markdown(f"**Most recent exported spans** ({len(spans)})")
        if spans:
            st.dataframe(
                [{"Trace": s.get("trace_id", "")[:12], "Span": s.get("span_id", "")[:8],
                  "Parent": (s.get("parent_span_id") or "root")[:8], "Name": s.get("name"),
                  "Duration (ms)": s.get("duration_ms"), "Status": s.get("status"), "Service": s.get("service")} for s in spans],
                hide_index=True, width="stretch")
        else:
            st.info("No spans exported yet. Ask a question on Search & Q&A, or run the System self-test.")

# ── Trace replay ─────────────────────────────────────────────
with tab_replay:
    st.subheader("Trace replay")
    st.markdown("Prove a past answer is reproducible: re-run the generation using only the context saved in the trace record.")
    ollama_up = _ollama_up()
    if not ollama_up:
        ollama_notice("Replay re-generates the answer with the local LLM")

    ok, std = call(api.list_traces, limit=100, trace_type="standard", spinner="Loading saved traces...", show_error=False)
    std_traces = list(reversed((std or {}).get("traces", []))) if ok else []
    choice = None
    if std_traces:
        opts = {t["trace_id"]: f"{t['trace_id']}  ·  {(t.get('query') or '')[:60]}" for t in std_traces}
        choice = st.selectbox("Saved trace", list(opts), format_func=opts.get)
        sel = next(t for t in std_traces if t["trace_id"] == choice)
        with st.expander("What the trace saved"):
            st.write(f"**Query:** {sel.get('query')}")
            st.caption(f"Prompt version `{sel.get('prompt_version')}` · retriever `{sel.get('retriever_type')}` · "
                       f"chunks {[c.get('chunk_id') for c in sel.get('retrieved_chunks', [])]}")
            st.info(sel.get("raw_llm_output", ""))
    replay_tid = st.text_input("Or enter a trace id", value=choice or "")

    if st.button("🔁 Replay trace", type="primary", disabled=not replay_tid):
        ok, r = call(api.replay_trace, replay_tid, spinner="Replaying against the stored context...")
        if ok:
            st.write(f"**Query:** {r.get('query')}")
            st.caption(f"Prompt version `{r.get('prompt_version')}` · chunks `{r.get('retrieved_chunk_ids')}`")
            left, right = st.columns(2)
            with left:
                st.markdown("##### Original output")
                st.info(r.get("original_output"))
            with right:
                st.markdown("##### Replayed output")
                st.success(r.get("replayed_output"))

# ── Support drill ────────────────────────────────────────────
with tab_drill:
    st.subheader("Support drill: find the bad answer")
    st.markdown("A customer complains vaguely. Search the logs, find the exact request, and pinpoint the step that went wrong.")
    simulated_notice("The drill runs on <b>generated</b> traces: 100 made-up claim requests containing exactly one planted bad answer "
                     "(a flood claim approved despite the Section 5.2 exclusion). The finding is real; the data is staged on purpose.")

    complaint = st.text_input("Customer complaint", value="A customer's basement flood claim was approved even though it should have been excluded.")
    if st.button("🔍 Investigate", type="primary"):
        ok, drill = call(api.run_support_drill, complaint, spinner="Scanning traces for the failure...")
        if ok:
            st.session_state["drill_result"] = drill

    drill = st.session_state.get("drill_result")
    if drill:
        suspect = drill.get("primary_suspect")
        expected = drill.get("planted_reference", {}).get("expected_trace_id")
        d1, d2 = st.columns(2)
        d1.metric("Traces searched", drill.get("traces_searched"))
        d2.metric("Matches found", drill.get("matches_found"))

        if suspect:
            found_it = suspect.get("trace_id") == expected
            st.markdown(pill("Found the planted trace", "ok") if found_it else pill("Found a different trace than the planted one", "warn"),
                        unsafe_allow_html=True)
            st.caption(f"Expected trace id: `{expected}`")
            s1, s2, s3 = st.columns(3)
            s1.metric("Trace", suspect.get("trace_id"))
            s2.metric("Claim", suspect.get("claim_id"))
            s3.metric("Wrongly paid", f"${suspect.get('net_payable', 0.0):,.2f}", delta=suspect.get("final_status"), delta_color="inverse")
            st.error(f"Faulty step: `{suspect.get('faulty_span_name')}`  \n{suspect.get('faulty_span_error')}")
            st.warning(f"**Root cause:** {suspect.get('root_cause')}")
            st.success(f"**Remediation:** {suspect.get('remediation')}")
            info_card("This failure is now a permanent regression test. Run it on the Evaluation page (Failure-to-test loop) to see it pass.")
            try:
                st.page_link("views/evaluation.py", label="Open the Evaluation page", icon="🎯")
            except Exception:
                pass
        else:
            st.info("The drill did not find a match for that complaint. Try wording it with what went wrong, such as flood, exclusion or approved.")

# ── Cost & cache ─────────────────────────────────────────────
with tab_cache:
    st.subheader("Semantic cache: cost per request")
    simulated_notice("This benchmark is a <b>simulation</b>. Latency is simulated with a short sleep and every uncached query is charged a fixed "
                     "650 tokens, so the percentage reduction shows how the cache mechanism behaves, <b>not measured savings</b> from real LLM usage.")
    st.markdown("Replays a stream of questions with repeats and near-duplicates, with and without a two-layer cache "
                "(exact prompt match, then similarity match).")

    num_q = st.slider("Number of test queries", 10, 50, 20)
    if st.button("📊 Run the benchmark", type="primary"):
        ok, bench = call(api.run_cache_benchmark, num_queries=num_q, spinner="Simulating traffic with and without the cache...")
        if ok:
            st.session_state["cache_bench"] = bench

    bench = st.session_state.get("cache_bench")
    if bench:
        imp, base, opt = bench.get("improvements", {}), bench.get("baseline", {}), bench.get("optimized", {})
        k1, k2, k3 = st.columns(3)
        k1.metric("Cost reduction (simulated)", f"{imp.get('cost_reduction_pct')}%", delta=f"${imp.get('cost_saved_usd', 0):.5f} saved")
        k2.metric("Cache hit rate", f"{bench.get('hit_rate_pct')}%", delta=f"{bench.get('cache_hits')}/{bench.get('total_queries')} hits", delta_color="off")
        k3.metric("Latency reduction (simulated)", f"{imp.get('latency_reduction_pct')}%",
                  delta=f"{opt.get('avg_latency_ms')} ms vs {base.get('avg_latency_ms')} ms", delta_color="off")
        st.dataframe(
            [{"Run": "Baseline (no cache)", "Tokens": base.get("total_tokens"), "Total cost ($)": base.get("total_cost_usd"), "Avg latency (ms)": base.get("avg_latency_ms")},
             {"Run": "With cache", "Tokens": opt.get("total_tokens"), "Total cost ($)": opt.get("total_cost_usd"), "Avg latency (ms)": opt.get("avg_latency_ms")}],
            hide_index=True, width="stretch")
