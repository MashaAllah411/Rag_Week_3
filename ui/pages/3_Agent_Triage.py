"""
ui/pages/3_Agent_Triage.py

Page 3: Agent Triage & Budget Enforcement (Weeks 7 & 8)
- Dynamic ReAct Agent loop enforcing 4 budgets
- Fixed 4-step sequential workflow
- Budget termination stress tests
- Trajectory evaluation & tool-choice accuracy
- Race Benchmark comparing Agent vs Workflow
"""
import json
import streamlit as st
from ui.api_client import api

st.set_page_config(page_title="Agent Triage — Insurance RAG", page_icon="🤖", layout="wide")

st.title("🤖 Claim Triage: ReAct Agent Loop vs Fixed Workflow")
st.markdown(
    "Test the dynamic tool-calling ReAct agent with strict budget enforcement (iterations, tokens, cost, wall-clock timeout) "
    "and evaluate its trajectory against a deterministic workflow."
)

tab_single, tab_benchmark = st.tabs(["🎯 Single Claim Triage", "🏁 Race Benchmark (10 Claims)"])

# ── Tab 1: Single Claim Triage ───────────────────────────────
with tab_single:
    st.subheader("Interactive Claim Triage")

    try:
        claims_data = api.list_claims()
        claims = claims_data.get("claims", [])
        claim_map = {c["claim_id"]: c for c in claims}

        col_c, col_mode, col_stress = st.columns([2, 2, 2])
        with col_c:
            selected_cid = st.selectbox(
                "Select Claim",
                options=list(claim_map.keys()),
                format_func=lambda x: f"{x} — {claim_map[x].get('incident_type')} (${claim_map[x].get('gross_claim_amount', 0):,.0f})"
            )
        with col_mode:
            sys_type = st.radio("Execution System", ["agent_loop", "fixed_workflow"], index=0,
                                format_func=lambda x: "ReAct Agent Loop (Dynamic)" if x == "agent_loop" else "Fixed 4-Step Workflow")
        with col_stress:
            force_exceed = st.selectbox("Force Budget Termination (Stress Test)", [None, "tokens", "cost", "iterations", "timeout"])

        claim_info = claim_map.get(selected_cid, {})
        with st.expander(f"📋 Claim Details: {selected_cid} — {claim_info.get('claimant')}", expanded=True):
            ci1, ci2, ci3 = st.columns(3)
            ci1.write(f"**Incident**: {claim_info.get('incident_type')}")
            ci2.write(f"**Gross Amount**: ${claim_info.get('gross_claim_amount', 0):,.2f}")
            ci3.write(f"**Deductible**: ${claim_info.get('policy_deductible', 0):,.2f}")
            st.info(f"**Adjuster Notes**: {claim_info.get('adjuster_notes')}")

        if st.button("🚀 Run Claim Triage", type="primary"):
            with st.spinner("Executing triage..."):
                try:
                    res = api.run_agent_triage(
                        claim_id=selected_cid,
                        system_type=sys_type,
                        force_budget_exceed=force_exceed
                    )

                    st.markdown("---")
                    st.subheader("Triage Results")

                    # KPI Cards
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("Status", "PASSED" if res.get("passed") else "FAILED",
                              delta="Clean finish" if not res.get("budget_triggered") else "Budget terminated")
                    k2.metric("Total Tokens", f"{res.get('total_tokens', 0)} tokens")
                    k3.metric("Total Cost", f"${res.get('total_cost', 0.0):.5f}")
                    k4.metric("Latency", f"{res.get('latency_seconds', 0.0):.4f}s")

                    # Budget Alert if triggered
                    b_trig = res.get("budget_triggered")
                    if b_trig:
                        st.warning(f"⚠️ Budget Enforced & Terminated: **{b_trig}**")

                    # Final Result Box
                    st.markdown("#### Payout Decision")
                    fin = res.get("final_result", {})
                    with st.container(border=True):
                        st.write(f"**Claim Status**: `{fin.get('claim_status', 'N/A')}`")
                        st.write(f"**Net Payout**: `${fin.get('net_payable', 0.0):,.2f}`")
                        st.caption(f"**Explanation**: {fin.get('explanation', fin.get('error', ''))}")

                    # Trajectory Evaluation
                    te = res.get("trajectory_evaluation", {})
                    if te:
                        st.markdown("#### 🎯 Trajectory Evaluation (Week 8)")
                        t1, t2, t3 = st.columns(3)
                        t1.metric("Tool Choice Accuracy", f"{te.get('tool_choice_acc', 0) * 100:.0f}%")
                        t2.metric("Argument Validity Rate", f"{te.get('arg_validity_rate', 0) * 100:.0f}%")
                        t3.metric("Step Efficiency", f"{te.get('step_efficiency', 0):.2f}",
                                  delta=f"Actual: {te.get('actual_steps')} / Optimal: {te.get('optimal_steps')}")

                        st.write(f"**Actual Tool Sequence**: `{ ' -> '.join(te.get('actual_sequence', [])) }`")
                        with st.expander("Valid Path Sets for this Claim"):
                            st.json(te.get("valid_paths", []))

                    # Execution Log Laps
                    st.markdown("#### 📜 Execution Log Laps")
                    with st.container(border=True):
                        for log_line in res.get("execution_log", []):
                            if "BUDGET" in log_line:
                                st.error(log_line)
                            elif "Lap" in log_line or "Step" in log_line:
                                st.write(f"- {log_line}")
                            else:
                                st.caption(log_line)

                except Exception as e:
                    st.error(f"Triage execution failed: {e}")

    except Exception as e:
        st.error(f"Failed to load claims: {e}")

# ── Tab 2: Race Benchmark (10 Claims) ────────────────────────
with tab_benchmark:
    st.subheader("🏁 Race Benchmark: ReAct Agent vs Fixed Workflow (10 Claims)")
    st.markdown("Measures pass rate, P50 latency, token overhead, and cost across all 10 standard synthetic claims.")

    if st.button("🏎️ Run 10-Claim Benchmark", type="primary"):
        with st.spinner("Running benchmark across both architectures..."):
            try:
                bench = api.run_agent_benchmark()

                ag = bench.get("agent", {})
                wf = bench.get("workflow", {})

                # Summary Table
                st.markdown("### Comparative Performance")
                b_cols = st.columns(4)
                b_cols[0].metric("Agent Pass Rate", f"{ag.get('pass_rate_pct')}%")
                b_cols[1].metric("Workflow Pass Rate", f"{wf.get('pass_rate_pct')}%")
                b_cols[2].metric("Agent P50 Latency", f"{ag.get('p50_latency_seconds')}s")
                b_cols[3].metric("Workflow P50 Latency", f"{wf.get('p50_latency_seconds')}s")

                st.markdown("### Cost & Token Comparison")
                c_cols = st.columns(4)
                c_cols[0].metric("Agent Total Tokens", f"{ag.get('total_tokens')}")
                c_cols[1].metric("Workflow Total Tokens", f"{wf.get('total_tokens')}")
                c_cols[2].metric("Agent Total Cost", f"${ag.get('total_cost_usd'):.5f}")
                c_cols[3].metric("Workflow Total Cost", f"${wf.get('total_cost_usd'):.5f}")

                # Budget Stress Test Result
                st.markdown("### Budget Stress Test Verification")
                b_test = bench.get("budget_stress_test", {})
                st.info(f"Forced token limit test cleanly terminated with: **{b_test.get('budget_triggered')}** in {b_test.get('iterations')} laps.")

            except Exception as e:
                st.error(f"Benchmark execution failed: {e}")
