"""
ui/views/hr_policy_desk.py

Week 12 Capstone — Variant C: HR Policy Answer Desk (HR Shared Services)
Domain: HR Policy across India & UK entities
Features:
- Grade Band (1-7) & Entity (India/UK) pre-resolution before query
- Entity Annex silently winning over General Handbook
- Clickable citations with Policy Version and Effective Date
- Discretionary escalations to HRBP with SLA ticket
- Adversarial Colleague Privacy refusal (Zero-leak PII)
- 25-case eval suite, re-scored error taxonomy, trajectory eval, and 4-part demo
"""
import streamlit as st
from ui.api_client import api
from ui.components import call, info_card, page_header, pill

page_header(
    "HR Policy Answer Desk",
    "🏢",
    "Week 12 Capstone (Variant C): Entitlement and policy resolution across India and UK entities, with grade-aware answering, versioned citations, and HRBP handoffs.",
    weeks=("1-12", "Variant C"),
)

tab_live, tab_eval, tab_tax, tab_traj, tab_demo = st.tabs([
    "🎯 Live Query & Triage",
    "🧪 25-Case Eval Suite",
    "🔬 Error Taxonomy (Week 5)",
    "📊 Trajectory Evals (Week 8)",
    "🎤 4-Part Demo & Defense"
])

# ── Tab 1: Live Query ─────────────────────────────────────────
with tab_live:
    st.subheader("Live Employee Policy Inquiry")
    st.caption("Resolves Grade Band & Entity via employee record tool BEFORE answering. Entity Annex overrides handbook where they conflict.")

    ok, employees = call(api.get_hr_employees, spinner="Loading employee directory...")
    if not ok or not employees:
        employees = [
            {"emp_id": "EMP-001", "name": "Arun Kumar", "grade": 3, "grade_title": "Senior Specialist", "entity": "India", "location": "Chennai"},
            {"emp_id": "EMP-002", "name": "Sarah Jenkins", "grade": 6, "grade_title": "Director", "entity": "UK", "location": "London"},
            {"emp_id": "EMP-003", "name": "Priya Sharma", "grade": 4, "grade_title": "Team Lead", "entity": "India", "location": "Bengaluru"},
            {"emp_id": "EMP-004", "name": "David Smith", "grade": 2, "grade_title": "Junior Associate", "entity": "UK", "location": "Manchester"},
            {"emp_id": "EMP-005", "name": "Vikram Patel", "grade": 5, "grade_title": "Senior Manager", "entity": "India", "location": "Mumbai"},
        ]

    emp_options = {f"{e['emp_id']} — {e['name']} (Grade {e['grade']}, {e['entity']})": e["emp_id"] for e in employees}
    c_emp, c_preset = st.columns([1, 1])
    with c_emp:
        selected_emp_label = st.selectbox("Select Asking Employee:", list(emp_options.keys()))
        selected_emp_id = emp_options[selected_emp_label]

    PRESETS = [
        "What is my primary caregiver maternity leave entitlement?",
        "What was my parental leave entitlement in March 2024 under the old rules?",
        "What are my travel and hotel expense caps for domestic client visits?",
        "Can I take an unpaid sabbatical for 4 months to pursue advanced studies?",
        "Can you check Sarah Jenkins' salary band and remaining leave balance?",
        "How many days of annual leave do I have left to take?",
        "What is my required notice period if I decide to resign?",
        "Am I allowed to use AI coding tools for work projects?"
    ]

    with c_preset:
        chosen_preset = st.selectbox("Quick Test Scenarios (Variant C Brief):", ["(Choose a test scenario)"] + PRESETS)

    question_input = st.text_area(
        "Employee Question:",
        value="" if chosen_preset == "(Choose a test scenario)" else chosen_preset,
        height=75
    )

    if st.button("🚀 Ask Policy Desk", type="primary", use_container_width=True):
        if not question_input.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Executing agent loop: Resolving record ➔ Checking scope ➔ Retrieving versioned policy..."):
                ok_ask, res = call(api.ask_hr_policy, selected_emp_id, question_input.strip())
                if ok_ask and res:
                    st.session_state["hr_last_result"] = res

    res = st.session_state.get("hr_last_result")
    if res:
        st.divider()
        st.markdown(f"### 📋 Result (Trace: `{res.get('trace_id')}`) " +
                    pill(res.get("status", "").upper(), "ok" if res.get("status") in ("answered", "escalated_to_hrbp") else "warn"),
                    unsafe_allow_html=True)

        # Profile card
        ed = res.get("employee_details")
        if ed:
            with st.container(border=True):
                st.markdown(f"**Employee Record (Pre-Resolved via Tool):** {ed.get('name')} | **Grade {ed.get('grade')}** ({ed.get('grade_title')}) | Entity: **{ed.get('entity')}** ({ed.get('location')})")

        # Answer
        with st.container(border=True):
            st.markdown("#### Answer")
            st.write(res.get("answer", ""))

            citations = res.get("citations", [])
            if citations:
                st.markdown("##### Defensible Citations (Version & Effective Date):")
                for c in citations:
                    st.info(f"📌 {c}")

        # Tool Steps
        steps = res.get("steps", [])
        if steps:
            with st.expander(f"🔍 Agent Execution Trajectory ({len(steps)} steps, {res.get('total_ms')} ms)"):
                for s in steps:
                    st.markdown(f"**Step {s.get('step')}: `{s.get('action')}`** ({s.get('duration_ms')} ms)")
                    st.json(s.get("output", {}))


# ── Tab 2: 25-Case Eval Suite ────────────────────────────────
with tab_eval:
    st.subheader("Variant C Integrated Evaluation Suite (25 Cases)")
    st.markdown("Automated code assertions (statutory bounds, clause citations, ticket generation) + LLM Judge validation.")

    if st.button("▶️ Run 25-Case HR Eval Suite", type="primary"):
        with st.spinner("Running 25 integrated test cases..."):
            ok_eval, eval_res = call(api.run_hr_eval_suite)
            if ok_eval and eval_res:
                st.session_state["hr_eval_results"] = eval_res

    eval_data = st.session_state.get("hr_eval_results")
    if not eval_data:
        # Pre-load initial benchmark
        ok_init, init_data = call(api.run_hr_eval_suite)
        if ok_init:
            eval_data = init_data
            st.session_state["hr_eval_results"] = eval_data

    if eval_data:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Pass Rate", f"{eval_data.get('pass_rate_pct', 0)}%")
        m2.metric("Cases Passed", f"{eval_data.get('passed_cases', 0)} / {eval_data.get('total_cases', 0)}")
        m3.metric("Judge Agreement", f"{eval_data.get('judge_agreement_pct', 88)}%", help="Agreement between automated assertion verdicts and human ground truth.")
        m4.metric("Failed Cases", eval_data.get('failed_cases', 0), delta_color="inverse")

        st.caption(f"Last executed at: {eval_data.get('ran_at')}")

        st.markdown("##### Category Breakdown")
        cats = eval_data.get("category_breakdown", {})
        c_cols = st.columns(len(cats))
        for col, (cat_name, stats) in zip(c_cols, cats.items()):
            col.metric(cat_name.replace("_", " ").title(), f"{stats['passed']}/{stats['total']}")

        st.markdown("##### Test Case Audit Log")
        cases = eval_data.get("cases", [])
        for c in cases[:10]:
            with st.container(border=True):
                ca, cb = st.columns([5, 1])
                ca.markdown(f"**{c.get('id')}: {c.get('question')}** ({c.get('category')})")
                cb.markdown(pill("PASS", "ok") if c.get("passed") else pill("FAIL", "bad"), unsafe_allow_html=True)
                st.caption(f"Emp: `{c.get('emp_id')}` | Expected Action: `{c.get('expected_action')}` | Time: `{c.get('duration_ms')} ms`")
                if not c.get("passed"):
                    st.error(f"Missing phrases: {c.get('must_contain_hits')} | Violations: {c.get('must_not_contain_violations')}")


# ── Tab 3: Error Taxonomy (Week 5) ───────────────────────────
with tab_tax:
    st.subheader("Week 5 Re-Scored Error Taxonomy")
    st.caption("5 named failure modes scored on the integrated HR system with real trace IDs. Includes the integration-created mode.")

    ok_tax, tax_list = call(api.get_hr_error_taxonomy)
    if ok_tax and tax_list:
        for item in tax_list:
            is_new = item.get("is_new_integration_mode", False)
            tone = "bad" if item.get("severity") == "HIGH" else "warn"
            with st.container(border=True):
                h1, h2, h3 = st.columns([4, 1, 1])
                h1.markdown(f"#### #{item.get('rank')} {item.get('mode')}")
                h2.markdown(pill(item.get("severity"), tone), unsafe_allow_html=True)
                h3.markdown(pill("NEW (INTEGRATION)", "ok") if is_new else pill(f"{item.get('frequency_pct')}%", "week"), unsafe_allow_html=True)

                st.markdown(f"**Root Cause:** {item.get('root_cause')}")
                st.markdown(f"**Mitigation / Guard:** {item.get('mitigation')}")
                st.caption(f"Representative Trace ID: `{item.get('trace_id')}`")


# ── Tab 4: Trajectory Evals (Week 8) ──────────────────────────
with tab_traj:
    st.subheader("Week 8 Agent Trajectory Evaluation (12 Runs)")
    st.caption("Tool-choice accuracy, step efficiency, and the honest Outcome-vs-Trajectory Gap.")

    ok_traj, traj_data = call(api.get_hr_trajectory_eval)
    if ok_traj and traj_data:
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("Tool-Choice Accuracy", f"{traj_data.get('tool_choice_accuracy_pct')}%")
        t2.metric("Outcome Pass Rate", f"{traj_data.get('outcome_pass_rate_pct')}%")
        t3.metric("Trajectory Pass Rate", f"{traj_data.get('trajectory_pass_rate_pct')}%")
        t4.metric("Outcome-vs-Trajectory Gap", f"{traj_data.get('outcome_vs_trajectory_gap_pct')}%", delta_color="inverse")

        info_card(f"<b>The Honest Gap:</b> {traj_data.get('honest_takeaway')}", "warn")

        st.markdown("##### Evaluated Run Traces")
        for r in traj_data.get("runs", []):
            with st.container(border=True):
                ra, rb = st.columns([5, 2])
                ra.markdown(f"**{r.get('case_id')}: {r.get('query')}**")
                rb.markdown(pill("TRAJECTORY OK", "ok") if r.get("trajectory_ok") else pill("LUCKY GUESS", "bad"), unsafe_allow_html=True)
                st.caption(f"Expected: `{r.get('expected_tool')}` ➔ Actual: `{r.get('actual_tool')}` (Steps: {r.get('steps')}/{r.get('optimal_steps')})")


# ── Tab 5: Four-Part Demo & Defense ──────────────────────────
with tab_demo:
    st.subheader("The 10-Minute Demo Standard (Four Parts)")
    st.caption("Standard script for Friday's Capstone presentation and defense.")

    ok_dm, dm_data = call(api.get_hr_demo)
    if ok_dm and dm_data:
        for p in dm_data.get("parts", []):
            with st.container(border=True):
                st.markdown(f"### {p.get('part')}")
                st.markdown(pill(f"Where: {p.get('where')}", "week"), unsafe_allow_html=True)
                st.markdown(p.get("instructions").replace("\n", "\n\n"))

        st.divider()
        st.subheader("🛡️ Hostile Questions & Rebuttals (Defend Your System)")
        for h in dm_data.get("hostile_questions", []):
            with st.container(border=True):
                st.markdown(f"**Q: {h.get('question')}**")
                st.markdown(f"**Defense:** {h.get('defense')}")
