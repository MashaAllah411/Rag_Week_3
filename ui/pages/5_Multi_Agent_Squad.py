"""
ui/pages/5_Multi_Agent_Squad.py

Page 5: Multi-Agent Claims Squad via A2A Protocol (Week 10)
- Agent Cards: Claims Manager, Policy Specialist, Payout Specialist
- Execution of triage via structured A2A message envelopes
- Full A2A context hand-off transcript
- Race Benchmark: Single Agent vs Multi-Agent Squad
"""
import streamlit as st
from ui.api_client import api

st.set_page_config(page_title="Multi-Agent Squad — Insurance RAG", page_icon="👥", layout="wide")

st.title("👥 Multi-Agent Claims Squad (A2A Protocol)")
st.markdown(
    "Orchestrate a specialized 3-agent squad communicating over a structured Agent-to-Agent (A2A) protocol "
    "with explicit task lifecycles, capabilities, and token accounting."
)

tab_cards, tab_triage, tab_race = st.tabs([
    "🪪 Agent Cards",
    "🚀 Squad Triage & A2A Transcript",
    "🏁 Single vs Squad Race"
])

# ── Tab 1: Agent Cards ───────────────────────────────────────
with tab_cards:
    st.subheader("Claims Squad Registry")
    try:
        cards_data = api.get_multi_agent_cards()
        for card in cards_data.get("agents", []):
            with st.container(border=True):
                st.markdown(f"### `{card.get('name')}` (v{card.get('version')})")
                st.markdown(f"**Role**: {card.get('role')}")
                st.write(card.get('description'))
                st.markdown("**Capabilities:**")
                for cap in card.get("capabilities", []):
                    st.caption(f"• `{cap}`")
    except Exception as e:
        st.error(f"Failed to load agent cards: {e}")

# ── Tab 2: Squad Triage & A2A Transcript ────────────────────
with tab_triage:
    st.subheader("Execute Squad Triage")

    claim_choice = st.selectbox(
        "Select Claim",
        ["CLM-7001", "CLM-7002", "CLM-7003", "CLM-7007", "CLM-7010"],
        index=1,
        help="CLM-7002 and CLM-7007 trigger policy exclusion verifications."
    )

    if st.button("🚀 Run Squad Triage", type="primary"):
        with st.spinner("Dispatching tasks across Claims Squad..."):
            try:
                res = api.run_squad_triage(claim_choice)
                st.markdown("---")

                # Results KPI
                fin = res.get("final_decision", {})
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Verdict", fin.get("status"))
                k2.metric("Net Payable", f"${fin.get('net_payable', 0.0):,.2f}")
                k3.metric("Squad Tokens", f"{res.get('total_tokens')} tok")
                k4.metric("Squad Latency", f"{res.get('total_latency_seconds', 0.0):.4f}s")

                st.info(f"**Final Explanation**: {fin.get('explanation')}")

                # A2A Message Envelopes
                st.subheader("📬 A2A Message Envelopes (Context Hand-offs)")
                for step in res.get("hand_offs", []):
                    with st.expander(f"✉️ {step.get('step')}: {step.get('sender')} ➔ {step.get('recipient')} ({step.get('lifecycle')})"):
                        c_m1, c_m2, c_m3 = st.columns(3)
                        c_m1.caption(f"Task ID: `{step.get('task_id')}`")
                        c_m2.caption(f"Tokens: {step.get('tokens_used')}")
                        c_m3.caption(f"Latency: {step.get('latency_seconds'):.4f}s")
                        st.json(step.get("payload"))

                # Transcript Markdown
                with st.expander("📜 Full Transcript (Markdown)"):
                    st.markdown(res.get("transcript_markdown", ""))

            except Exception as e:
                st.error(f"Squad triage failed: {e}")

# ── Tab 3: Single vs Squad Race ──────────────────────────────
with tab_race:
    st.subheader("🏁 Architecture Race: Single Agent vs Multi-Agent Squad")
    st.markdown("Quantify the tradeoff: auditability & separation of concerns vs token overhead & latency.")

    if st.button("🏎️ Run Architecture Benchmark", type="primary"):
        with st.spinner("Racing Single Agent vs Multi-Agent Squad over claims..."):
            try:
                race = api.run_multi_agent_benchmark()
                sa = race.get("single_agent", {})
                sq = race.get("multi_agent_squad", {})

                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Single Agent Accuracy", f"{sa.get('accuracy_pct')}%")
                r2.metric("Squad Accuracy", f"{sq.get('accuracy_pct')}%")
                r3.metric("Single Agent Tokens", f"{sa.get('total_tokens')}")
                r4.metric("Squad Tokens", f"{sq.get('total_tokens')}")

                st.markdown("---")
                st.info(f"**Architectural Verdict:**\n\n{race.get('verdict')}")

            except Exception as e:
                st.error(f"Race benchmark failed: {e}")
