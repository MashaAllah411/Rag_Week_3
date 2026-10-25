"""
ui/views/agent_triage.py

Agent Triage (Weeks 7 and 8)
- Budget-limited agent loop vs a fixed workflow, for one claim or all ten
- Four budgets (iterations, tokens, cost, wall-clock) shown and enforced
- Stress test that forces each budget to fire
- Trajectory scoring (tool choice, argument validity, step efficiency, outcome-vs-trajectory gap)
"""
import streamlit as st

from ui.api_client import api
from ui.components import call, info_card, page_header, pill, simulated_notice

page_header(
    "Agent Triage",
    "🤖",
    "Run a claim through a budget-limited agent loop or a fixed workflow, see every step, and compare the two on speed, cost and reliability.",
    weeks=("7", "8"),
)
simulated_notice(
    "The agent does not choose its own next step: it follows a fixed, hard-coded plan "
    "(get the claim, search the policy, compute the payout), and token and cost figures are estimates "
    "(about 4 characters per token). What is real: the four budgets and the stop conditions that enforce them, "
    "the step-by-step log, and the trajectory scoring against the list of valid tool paths."
)


@st.cache_data(ttl=600, show_spinner=False)
def _load_budgets() -> dict:
    """The enforced budgets, read from a triage response so the page never hard-codes them."""
    try:
        return api.run_agent_triage("CLM-7001", "fixed_workflow").get("budgets", {})
    except Exception:
        return {}


def _budget_strip(budgets: dict) -> None:
    if not budgets:
        st.caption("Budget limits will appear here once the backend is reachable.")
        return
    st.markdown("##### Budgets enforced on every agent run")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Max iterations", budgets.get("max_iterations", "?"), help="Laps of the loop before it must stop.")
    c2.metric("Max tokens", f"{budgets.get('max_tokens', 0):,}", help="Estimated tokens summed over all laps.")
    c3.metric("Max cost", f"${budgets.get('max_cost_usd', 0):.2f}", help="Estimated cost; the loop stops when it is exceeded.")
    c4.metric("Wall-clock timeout", f"{budgets.get('timeout_seconds', 0):.0f}s", help="Real elapsed time before the loop stops.")


def _usage_bars(res: dict, budgets: dict) -> None:
    """How much of each budget this run used."""
    if not budgets:
        return
    rows = [
        ("Iterations", res.get("iterations", 0), budgets.get("max_iterations", 1), f"{res.get('iterations', 0)} of {budgets.get('max_iterations')}"),
        ("Tokens", res.get("total_tokens", 0), budgets.get("max_tokens", 1), f"{res.get('total_tokens', 0):,} of {budgets.get('max_tokens', 0):,}"),
        ("Cost", res.get("total_cost", 0.0), budgets.get("max_cost_usd", 1), f"${res.get('total_cost', 0.0):.5f} of ${budgets.get('max_cost_usd', 0):.2f}"),
        ("Time", res.get("latency_seconds", 0.0), budgets.get("timeout_seconds", 1), f"{res.get('latency_seconds', 0.0):.4f}s of {budgets.get('timeout_seconds', 0):.0f}s"),
    ]
    for label, used, limit, text in rows:
        st.progress(min(1.0, (used / limit) if limit else 0.0), text=f"{label}: {text}")


def _show_result(res: dict, budgets: dict) -> None:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Outcome", "PASSED" if res.get("passed") else "STOPPED",
              delta="Clean finish" if not res.get("budget_triggered") else "Budget fired", delta_color="normal" if res.get("passed") else "inverse")
    k2.metric("Tokens (est.)", f"{res.get('total_tokens', 0):,}")
    k3.metric("Cost (est.)", f"${res.get('total_cost', 0.0):.5f}")
    k4.metric("Latency", f"{res.get('latency_seconds', 0.0):.4f}s")

    if res.get("budget_triggered"):
        st.warning(f"Budget enforced, run stopped: **{res['budget_triggered']}**")

    with st.expander("Budget usage for this run", expanded=bool(res.get("budget_triggered"))):
        _usage_bars(res, budgets)

    st.markdown("**Payout decision**")
    fin = res.get("final_result", {})
    with st.container(border=True):
        st.write(f"Claim status: `{fin.get('claim_status', 'N/A')}`  ·  Net payout: `${fin.get('net_payable', 0.0):,.2f}`")
        st.caption(fin.get("explanation", fin.get("error", "")))

    te = res.get("trajectory_evaluation") or {}
    if te:
        st.markdown("**Trajectory evaluation (Week 8)**: was the path right, not just the answer?")
        t1, t2, t3 = st.columns(3)
        t1.metric("Tool-choice accuracy", f"{te.get('tool_choice_acc', 0) * 100:.0f}%")
        t2.metric("Argument validity", f"{te.get('arg_validity_rate', 0) * 100:.0f}%")
        t3.metric("Step efficiency", f"{te.get('step_efficiency', 0):.2f}",
                  help="Optimal steps divided by actual steps. 1.00 means no wasted step.")
        st.caption(f"Steps taken: {te.get('actual_steps')} (optimal {te.get('optimal_steps')}).  "
                   f"Outcome {'correct' if te.get('outcome_passed') else 'wrong'}, "
                   f"trajectory {'valid' if te.get('trajectory_passed') else 'invalid'}.")
        st.write("Tool sequence: " + " → ".join(f"`{t}`" for t in te.get("actual_sequence", [])))
        with st.expander("Valid tool paths for this claim"):
            for path in te.get("valid_paths", []):
                st.write(" → ".join(f"`{t}`" for t in path))

    with st.expander("Execution log", expanded=True):
        for line in res.get("execution_log", []):
            if "BUDGET" in line:
                st.error(line)
            elif "Lap" in line or "Step" in line:
                st.write(f"- {line}")
            else:
                st.caption(line)


def derive_verdict(ag: dict, wf: dict) -> str:
    """Which would you ship? Built only from the numbers on screen."""
    a_rate, w_rate = ag.get("pass_rate_pct", 0.0), wf.get("pass_rate_pct", 0.0)
    a_tok, w_tok = ag.get("total_tokens", 0), wf.get("total_tokens", 0)
    a_cost, w_cost = ag.get("total_cost_usd", 0.0), wf.get("total_cost_usd", 0.0)
    a_lat, w_lat = ag.get("p50_latency_seconds", 0.0), wf.get("p50_latency_seconds", 0.0)

    if a_rate != w_rate:
        better = "agent loop" if a_rate > w_rate else "fixed workflow"
        return (f"Ship the **{better}**: it completes more claims ({max(a_rate, w_rate)}% vs {min(a_rate, w_rate)}%). "
                f"Reliability comes first; cost ({a_tok:,} vs {w_tok:,} tokens) is secondary.")
    cheaper = "fixed workflow" if w_cost < a_cost else "agent loop" if a_cost < w_cost else None
    if cheaper is None:
        return f"Both complete {a_rate}% of claims at the same cost; choose on maintainability. The fixed workflow is simpler to debug."
    hi_tok, lo_tok = (a_tok, w_tok) if cheaper == "fixed workflow" else (w_tok, a_tok)
    saving = (1 - lo_tok / hi_tok) * 100 if hi_tok else 0.0
    speed = ""
    if a_lat and w_lat:
        faster, ratio = ("fixed workflow", a_lat / w_lat) if w_lat < a_lat else ("agent loop", w_lat / a_lat)
        speed = f" and the {faster} is about {ratio:.0f}x faster at the median ({a_lat}s agent vs {w_lat}s workflow)"
    text = (f"Both finish {a_rate}% of claims, so quality is a tie. The **{cheaper}** uses {saving:.0f}% fewer tokens "
            f"(${min(a_cost, w_cost):.5f} vs ${max(a_cost, w_cost):.5f} in total){speed}. Ship the **{cheaper}**.")
    if cheaper == "fixed workflow":
        text += " Every claim follows the same steps, and a fixed sequence is cheaper and more predictable when the path does not change with the input."
    return text


budgets = _load_budgets()
_budget_strip(budgets)

tab_single, tab_race = st.tabs(["🎯 Single claim", "🏁 Race: 10 claims"])

# ── Single claim ─────────────────────────────────────────────
with tab_single:
    ok, claims_data = call(api.list_claims, spinner="Loading claims...")
    claims = (claims_data or {}).get("claims", []) if ok else []
    claim_map = {c["claim_id"]: c for c in claims}

    if claim_map:
        col_c, col_mode, col_stress = st.columns([3, 2, 2])
        with col_c:
            selected_cid = st.selectbox(
                "Claim", list(claim_map.keys()),
                format_func=lambda x: f"{x}: {claim_map[x].get('incident_type')} (${claim_map[x].get('gross_claim_amount', 0):,.0f})")
        with col_mode:
            sys_choice = st.radio("System", ["agent_loop", "fixed_workflow", "compare"], horizontal=False,
                                  format_func={"agent_loop": "Agent loop", "fixed_workflow": "Fixed 4-step workflow",
                                               "compare": "Compare both"}.get)
        with col_stress:
            force_exceed = st.selectbox("Stress test: force a budget to fire", [None, "tokens", "cost", "iterations", "timeout"],
                                        format_func=lambda x: "None (normal run)" if x is None else x,
                                        help="Makes the agent loop exceed the chosen budget so you can watch it stop cleanly. The fixed workflow has no budgets.")

        info = claim_map[selected_cid]
        with st.expander(f"Claim details: {selected_cid}, {info.get('claimant')}", expanded=False):
            d1, d2, d3 = st.columns(3)
            d1.write(f"**Incident**: {info.get('incident_type')}")
            d2.write(f"**Gross amount**: ${info.get('gross_claim_amount', 0):,.2f}")
            d3.write(f"**Deductible**: ${info.get('policy_deductible', 0):,.2f}")
            st.info(f"Adjuster notes: {info.get('adjuster_notes')}")

        if st.button("🚀 Run triage", type="primary"):
            systems = ["agent_loop", "fixed_workflow"] if sys_choice == "compare" else [sys_choice]
            results = {}
            for system in systems:
                ok, res = call(api.run_agent_triage, claim_id=selected_cid, system_type=system,
                               force_budget_exceed=force_exceed if system == "agent_loop" else None,
                               spinner=f"Running {system.replace('_', ' ')}...")
                if ok:
                    results[system] = res
            st.session_state["agent_single"] = {"claim": selected_cid, "results": results}

        saved = st.session_state.get("agent_single")
        if saved and saved["results"]:
            st.divider()
            st.subheader(f"Results for {saved['claim']}")
            names = {"agent_loop": "Agent loop", "fixed_workflow": "Fixed workflow"}
            if len(saved["results"]) == 2:
                cols = st.columns(2)
                for col, (system, res) in zip(cols, saved["results"].items()):
                    with col:
                        st.markdown(f"#### {names[system]}")
                        _show_result(res, budgets if system == "agent_loop" else {})
            else:
                (system, res), = saved["results"].items()
                st.markdown(f"#### {names[system]}")
                _show_result(res, budgets if system == "agent_loop" else {})
    else:
        st.info("No claims available. Check that the backend is running.")

# ── Race ─────────────────────────────────────────────────────
with tab_race:
    st.subheader("Race: agent loop vs fixed workflow across all 10 claims")
    st.caption("Each claim is run through both systems. We compare quality, speed (median latency), tokens and cost.")

    if st.button("🏎️ Run the 10-claim race", type="primary"):
        ok, bench = call(api.run_agent_benchmark, spinner="Racing both systems over 10 claims...")
        if ok:
            st.session_state["agent_bench"] = bench

    bench = st.session_state.get("agent_bench")
    if bench:
        ag, wf = bench.get("agent", {}), bench.get("workflow", {})

        st.markdown("##### The four numbers")
        st.dataframe(
            [
                {"System": "Agent loop", "Quality (pass rate)": f"{ag.get('pass_rate_pct')}%", "Speed (p50)": f"{ag.get('p50_latency_seconds')}s",
                 "Tokens (est.)": f"{ag.get('total_tokens', 0):,}", "Cost (est.)": f"${ag.get('total_cost_usd', 0):.5f}"},
                {"System": "Fixed workflow", "Quality (pass rate)": f"{wf.get('pass_rate_pct')}%", "Speed (p50)": f"{wf.get('p50_latency_seconds')}s",
                 "Tokens (est.)": f"{wf.get('total_tokens', 0):,}", "Cost (est.)": f"${wf.get('total_cost_usd', 0):.5f}"},
            ],
            hide_index=True, width="stretch")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Pass rate", f"{ag.get('pass_rate_pct')}%", delta=f"{ag.get('pass_rate_pct', 0) - wf.get('pass_rate_pct', 0):+.1f} pts vs workflow")
        m2.metric("Median latency", f"{ag.get('p50_latency_seconds')}s", delta=f"workflow {wf.get('p50_latency_seconds')}s", delta_color="off")
        m3.metric("Tokens", f"{ag.get('total_tokens', 0):,}", delta=f"workflow {wf.get('total_tokens', 0):,}", delta_color="off")
        m4.metric("Cost", f"${ag.get('total_cost_usd', 0):.5f}", delta=f"workflow ${wf.get('total_cost_usd', 0):.5f}", delta_color="off")
        st.caption("Agent figures shown with the workflow beside them.")

        st.markdown("##### Which would you ship?")
        info_card(derive_verdict(ag, wf))
        st.caption("Because the agent's plan is scripted, this compares the overhead of running a loop, not an LLM's planning skill.")

        # Trajectory scoring across the agent runs
        te_list = [r.get("trajectory_evaluation") or {} for r in ag.get("results", [])]
        te_list = [t for t in te_list if t]
        if te_list:
            n = len(te_list)
            outcome = sum(1 for t in te_list if t.get("outcome_passed")) / n * 100
            traj = sum(1 for t in te_list if t.get("trajectory_passed")) / n * 100
            st.markdown("##### Trajectory scoring (agent loop, Week 8)")
            t1, t2, t3, t4 = st.columns(4)
            t1.metric("Outcome correct", f"{outcome:.0f}%")
            t2.metric("Path valid", f"{traj:.0f}%")
            t3.metric("Outcome-vs-trajectory gap", f"{outcome - traj:.0f} pts",
                      help="Right answers reached by a wrong path are time bombs. 0 means none.")
            t4.metric("Avg step efficiency", f"{sum(t.get('step_efficiency', 0) for t in te_list) / n:.2f}")

        st.markdown("##### Per-claim detail")
        rows = []
        for a, w in zip(ag.get("results", []), wf.get("results", [])):
            ate, wte = a.get("trajectory_evaluation") or {}, w.get("trajectory_evaluation") or {}
            rows.append({
                "Claim": a.get("claim_id"),
                "Agent passed": a.get("passed"), "Agent laps": a.get("iterations"), "Agent tokens": a.get("total_tokens"),
                "Agent latency (s)": a.get("latency_seconds"), "Agent steps/optimal": f"{ate.get('actual_steps')}/{ate.get('optimal_steps')}",
                "Workflow passed": w.get("passed"), "Workflow tokens": w.get("total_tokens"), "Workflow latency (s)": w.get("latency_seconds"),
            })
        st.dataframe(rows, hide_index=True, width="stretch")

        st.markdown("##### Budget stress test")
        b_test = bench.get("budget_stress_test", {})
        st.markdown(pill("Stopped cleanly", "ok") + f" Forcing the token limit ended the run with **{b_test.get('budget_triggered')}** "
                    f"after {b_test.get('iterations')} lap(s), and the agent did not keep looping.", unsafe_allow_html=True)
    else:
        st.info("Press the button to run the race. It takes a moment and needs no LLM.")
