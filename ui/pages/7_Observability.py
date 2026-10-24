"""
ui/pages/7_Observability.py

Page 7: Production Observability, Support Drill & Caching (Weeks 5 & 11)
- OpenTelemetry span-level production tracing & latency/cost breakdowns
- Deterministic trace replay from saved context
- Support Triage Drill diagnosing vague customer complaints
- Semantic cache benchmark proving >=35% cost reduction
"""
import streamlit as st
from ui.api_client import api

st.set_page_config(page_title="Observability & Drill — Insurance RAG", page_icon="📊", layout="wide")

st.title("📊 Production Observability, Support Drill & Caching")
st.markdown(
    "Granular OpenTelemetry spans, step-level costing, PII redaction, production support drill, "
    "and semantic cache cost reduction."
)

tab_traces, tab_replay, tab_drill, tab_cache = st.tabs([
    "📈 Span-Level Traces",
    "🔁 Trace Replay",
    "🚨 Support Triage Drill",
    "⚡ Semantic Cache Benchmark"
])

# ── Tab 1: Span-Level Traces ─────────────────────────────────
with tab_traces:
    st.subheader("Recent Production Spans & Step Cost Breakdown")

    try:
        t_data = api.list_traces(limit=25, trace_type="production")
        traces = t_data.get("traces", [])

        if not traces:
            st.info("No production traces found yet.")
        else:
            for t in reversed(traces[-10:]):
                with st.expander(f"📍 Trace `{t.get('trace_id')}` — {t.get('status')} (${t.get('total_cost_usd', 0.0):.6f} | {t.get('total_duration_ms', 0):.1f}ms)"):
                    tc1, tc2, tc3 = st.columns(3)
                    tc1.metric("Total Tokens", t.get("total_tokens"))
                    tc2.metric("Total Cost", f"${t.get('total_cost_usd', 0.0):.6f}")
                    tc3.metric("Total Latency", f"{t.get('total_duration_ms', 0.0):.1f}ms")

                    st.markdown("**Per-Step Span Breakdown:**")
                    steps = t.get("step_breakdown", [])
                    if steps:
                        for s in steps:
                            st.write(f"- `{s.get('step')}`: **{s.get('duration_ms')}ms** | {s.get('tokens')} tok | ${s.get('cost_usd', 0.0):.6f} | Status: `{s.get('status')}`")
                    else:
                        st.json(t)
    except Exception as e:
        st.error(f"Failed to load traces: {e}")

# ── Tab 2: Trace Replay ──────────────────────────────────────
with tab_replay:
    st.subheader("Trace Replay Verification")
    st.markdown("Prove complete auditability by re-running an LLM generation purely using the context saved in a trace record.")

    replay_tid = st.text_input("Enter Trace ID to Replay", value="trc_20260830_1bafba6e")

    if st.button("🔁 Replay Trace", type="primary"):
        with st.spinner("Replaying query against stored context..."):
            try:
                r_res = api.replay_trace(replay_tid)
                st.markdown("---")
                st.write(f"**Query**: *{r_res.get('query')}*")
                st.caption(f"Prompt Version: `{r_res.get('prompt_version')}` | Retrieved Chunks: `{r_res.get('retrieved_chunk_ids')}`")

                col_orig, col_rep = st.columns(2)
                with col_orig:
                    st.markdown("#### 📜 Original Output")
                    st.info(r_res.get("original_output"))
                with col_rep:
                    st.markdown("#### 🔄 Replayed Output")
                    st.success(r_res.get("replayed_output"))
            except Exception as e:
                st.error(f"Replay failed: {e}")

# ── Tab 3: Support Triage Drill ──────────────────────────────
with tab_drill:
    st.subheader("🚨 Production Support Triage Drill")
    st.markdown(
        "Diagnose a vague customer complaint across 100 realistic traces with 1 planted bad answer "
        "(a flood claim wrongly approved for $14,500 despite Section 5.2 exclusion)."
    )

    complaint = st.text_input(
        "Customer Complaint / Ticket",
        value="Customer claims their basement water damage payout was approved or denied incorrectly."
    )

    if st.button("🔍 Run Diagnostic Investigation", type="primary"):
        with st.spinner("Scanning traces for failure symptoms..."):
            try:
                drill_res = api.run_support_drill(complaint)
                st.markdown("---")

                if drill_res.get("found"):
                    st.error("🚨 Planted Bad Answer Located!")
                    d1, d2, d3 = st.columns(3)
                    d1.metric("Faulty Trace ID", drill_res.get("trace_id"))
                    d2.metric("Claim ID", drill_res.get("claim_id"))
                    d3.metric("Improper Payout", f"${drill_res.get('improper_payout', 0.0):,.2f}")

                    st.markdown(f"**Diagnosis**: {drill_res.get('diagnosis')}")
                    st.warning(f"**Root Cause**: {drill_res.get('root_cause')}")
                    st.info(f"**Mitigation**: {drill_res.get('mitigation')}")
                else:
                    st.info(drill_res.get("message"))
            except Exception as e:
                st.error(f"Drill failed: {e}")

# ── Tab 4: Semantic Cache Benchmark ──────────────────────────
with tab_cache:
    st.subheader("⚡ Semantic Cache Cost Optimization Benchmark")
    st.markdown("Simulate production query traffic to verify >= 35% cost savings using dual-layer prompt hashing and sparse cosine caching.")

    num_q = st.slider("Number of Test Queries", min_value=10, max_value=50, value=20)

    if st.button("📊 Run Cost Optimization Benchmark", type="primary"):
        with st.spinner("Simulating traffic with and without semantic cache..."):
            try:
                c_bench = api.run_cache_benchmark(num_queries=num_q)
                st.markdown("---")

                imp = c_bench.get("improvements", {})
                b_info = c_bench.get("baseline", {})
                o_info = c_bench.get("optimized", {})

                k1, k2, k3 = st.columns(3)
                k1.metric("Cost Reduction", f"{imp.get('cost_reduction_pct')}%", delta=f"${imp.get('cost_saved_usd'):.5f} saved")
                k2.metric("Cache Hit Rate", f"{c_bench.get('hit_rate_pct')}%", delta=f"{c_bench.get('cache_hits')}/{c_bench.get('total_queries')} hits")
                k3.metric("Latency Reduction", f"{imp.get('latency_reduction_pct')}%", delta=f"{o_info.get('avg_latency_ms')}ms vs {b_info.get('avg_latency_ms')}ms")

                st.markdown("### Cost & Token Consumption")
                col_b, col_o = st.columns(2)
                with col_b:
                    st.markdown("#### 🔴 Baseline (No Cache)")
                    st.write(f"- Total Tokens: **{b_info.get('total_tokens')}**")
                    st.write(f"- Total Cost: **${b_info.get('total_cost_usd'):.5f}**")
                    st.write(f"- Avg Latency: **{b_info.get('avg_latency_ms')} ms**")
                with col_o:
                    st.markdown("#### 🟢 Optimized (With Cache)")
                    st.write(f"- Total Tokens: **{o_info.get('total_tokens')}**")
                    st.write(f"- Total Cost: **${o_info.get('total_cost_usd'):.5f}**")
                    st.write(f"- Avg Latency: **{o_info.get('avg_latency_ms')} ms**")

            except Exception as e:
                st.error(f"Benchmark failed: {e}")
