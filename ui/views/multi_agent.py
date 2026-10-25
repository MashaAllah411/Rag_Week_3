"""
ui/views/multi_agent.py

Multi-Agent Squad (Week 10)
- Agent cards (manager + two specialists)
- Squad triage with the A2A message hand-offs as a timeline
- Single agent vs squad race on quality, speed, tokens and cost
"""
import streamlit as st

from ui.api_client import api
from ui.components import call, info_card, page_header, pill, simulated_notice

page_header(
    "Multi-Agent Squad",
    "👥",
    "A manager hands pieces of a claim to two specialists over the A2A protocol. Then race the team against a single agent, with evidence.",
    weeks=("10",),
)
simulated_notice(
    "The A2A message envelopes (task id, lifecycle, token accounting) and the audit trail are real, and every hand-off is "
    "recorded. The specialists' decisions are scripted rules, not LLM reasoning, and token and cost figures are estimates "
    "(about 4 characters per token)."
)

tab_cards, tab_triage, tab_race = st.tabs(["🪪 Agent cards", "🚀 Squad triage", "🏁 Single vs squad race"])

# ── Agent cards ──────────────────────────────────────────────
with tab_cards:
    st.subheader("The squad: one manager, two specialists")
    st.caption("An agent card describes what an agent can do and what it expects, so other agents can find and use it.")
    ok, cards = call(api.get_multi_agent_cards, spinner="Loading agent cards...")
    if ok:
        for card in cards.get("agents", []):
            with st.container(border=True):
                st.markdown(f"#### `{card.get('name')}`  " + pill(f"v{card.get('version')}", "week"), unsafe_allow_html=True)
                st.markdown(f"**Role:** {card.get('role')}")
                st.write(card.get("description"))
                st.markdown("".join(pill(cap) for cap in card.get("capabilities", [])), unsafe_allow_html=True)

# ── Squad triage ─────────────────────────────────────────────
with tab_triage:
    st.subheader("Run a claim through the squad")
    ok, claims = call(api.list_claims, spinner="Loading claims...")
    ids = [c["claim_id"] for c in claims.get("claims", [])] if ok else ["CLM-7001", "CLM-7002"]
    claim_choice = st.selectbox("Claim", ids, index=min(1, len(ids) - 1), help="CLM-7002 and CLM-7007 trigger policy exclusions.")

    if st.button("🚀 Run squad triage", type="primary"):
        ok, res = call(api.run_squad_triage, claim_choice, spinner="Dispatching tasks across the squad...")
        if ok:
            st.session_state["squad_triage"] = res

    res = st.session_state.get("squad_triage")
    if res:
        st.divider()
        fin = res.get("final_decision", {})
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Verdict", fin.get("status"))
        k2.metric("Net payable", f"${fin.get('net_payable', 0.0):,.2f}")
        k3.metric("Tokens (est.)", f"{res.get('total_tokens', 0):,}")
        k4.metric("Cost (est.)", f"${res.get('total_cost_usd', 0.0):.5f}")
        k5.metric("Latency", f"{res.get('total_latency_seconds', 0.0):.4f}s")
        if fin.get("policy_clause") and fin.get("policy_clause") != "N/A":
            st.caption(f"Policy clause cited by the specialist: `{fin['policy_clause']}`")

        st.markdown("##### A2A hand-offs (the audit trail)")
        hand_offs = res.get("hand_offs", [])
        if not hand_offs:
            st.info("No hand-offs were recorded for this run.")
        for i, step in enumerate(hand_offs, start=1):
            with st.container(border=True):
                head, meta = st.columns([3, 2])
                head.markdown(f"**{i}. {step.get('step')}**  \n`{step.get('sender')}` ➔ `{step.get('recipient')}`")
                meta.markdown(pill(step.get("lifecycle", ""), "ok" if step.get("lifecycle") == "COMPLETED" else "warn") +
                              pill(f"{step.get('tokens_used')} tokens", "week") + pill(f"{step.get('latency_seconds', 0.0):.4f}s", "week"),
                              unsafe_allow_html=True)
                st.caption(f"Task id `{step.get('task_id')}`")
                st.json(step.get("payload"), expanded=False)
        st.caption("Every hand-off re-sends the claim context to the next agent, which is why a team spends more tokens than one agent.")

        with st.expander("Full transcript (markdown)"):
            st.markdown(res.get("transcript_markdown", ""))

# ── Race ─────────────────────────────────────────────────────
with tab_race:
    st.subheader("Single agent vs squad, on the same claims")
    st.caption("Each claim is run through both architectures. We compare quality, speed, tokens and cost.")

    if st.button("🏎️ Run the race", type="primary"):
        ok, race = call(api.run_multi_agent_benchmark, spinner="Racing the single agent against the squad...")
        if ok:
            st.session_state["squad_race"] = race

    race = st.session_state.get("squad_race")
    if race:
        sa, sq = race.get("single_agent", {}), race.get("multi_agent_squad", {})

        st.markdown("##### The four numbers")
        st.dataframe(
            [
                {"System": "Single agent", "Quality (accuracy)": f"{sa.get('accuracy_pct')}%", "Speed (p50)": f"{sa.get('p50_latency_seconds')}s",
                 "Tokens (est.)": f"{sa.get('total_tokens', 0):,}", "Cost (est.)": f"${sa.get('total_cost_usd', 0):.5f}"},
                {"System": "Squad (manager + 2)", "Quality (accuracy)": f"{sq.get('accuracy_pct')}%", "Speed (p50)": f"{sq.get('p50_latency_seconds')}s",
                 "Tokens (est.)": f"{sq.get('total_tokens', 0):,}", "Cost (est.)": f"${sq.get('total_cost_usd', 0):.5f}"},
            ],
            hide_index=True, width="stretch")

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Squad accuracy", f"{sq.get('accuracy_pct')}%", delta=f"{sq.get('accuracy_pct', 0) - sa.get('accuracy_pct', 0):+.1f} pts vs single")
        s_lat, q_lat = sa.get("p50_latency_seconds", 0), sq.get("p50_latency_seconds", 0)
        r2.metric("Squad median latency", f"{q_lat}s", delta=f"single {s_lat}s", delta_color="off")
        tok_ratio = (sq.get("total_tokens", 0) / sa["total_tokens"]) if sa.get("total_tokens") else 0
        r3.metric("Squad tokens", f"{sq.get('total_tokens', 0):,}", delta=f"{tok_ratio:.2f}x the single agent", delta_color="inverse")
        cost_ratio = (sq.get("total_cost_usd", 0) / sa["total_cost_usd"]) if sa.get("total_cost_usd") else 0
        r4.metric("Squad cost", f"${sq.get('total_cost_usd', 0):.5f}", delta=f"{cost_ratio:.2f}x the single agent", delta_color="inverse")

        st.markdown("##### Verdict")
        info_card(race.get("verdict", ""))

        st.markdown("##### Per-claim results")
        rows = []
        for a, b in zip(sa.get("items", []), sq.get("items", [])):
            rows.append({"Claim": a.get("claim_id"), "Single: status": a.get("status"), "Single: tokens": a.get("tokens"),
                         "Squad: status": b.get("status"), "Squad: tokens": b.get("tokens"),
                         "Same decision": a.get("status") == b.get("status")})
        st.dataframe(rows, hide_index=True, width="stretch")
    else:
        st.info("Press the button to run the race. It needs no LLM.")

    st.markdown("##### When does a team of agents help, and when does it not?")
    c_yes, c_no = st.columns(2)
    with c_yes:
        info_card("<b>It helps when</b> parts of the job are truly independent and can run in parallel, or need clearly different "
                  "instructions or permissions. It also gives a clean audit trail: one message per hand-off.")
    with c_no:
        info_card("<b>It does not help when</b> one agent can do the whole job. Every hand-off re-sends the context, so a team can "
                  "cost several times more for the same result. Measure first, and keep whichever wins.", "sim")
