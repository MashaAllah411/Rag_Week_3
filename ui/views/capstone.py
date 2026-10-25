"""
ui/views/capstone.py

Capstone (Week 12)
- Run the full suite across every week's capability
- Known weak spots, stated plainly
- The four-part demo, filled from real results
- Packaging checklist against the Week 12 brief
"""
import streamlit as st

from ui.api_client import api
from ui.components import call, info_card, page_header, pill

page_header(
    "Capstone",
    "🏁",
    "Everything from the last eleven weeks in one place: run the whole suite, know your weak spots before anyone else points them out, and prepare an honest demo.",
    weeks=("12",),
)

STATUS_TONE = {"pass": "ok", "fail": "bad", "skipped": "warn"}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
SEVERITY_TONE = {"high": "bad", "medium": "warn", "low": "week"}

tab_suite, tab_weak, tab_demo, tab_pack = st.tabs(["▶️ Run the full suite", "⚠️ Known weak spots", "🎤 Four-part demo", "📦 Packaging checklist"])

# ── Full suite ───────────────────────────────────────────────
with tab_suite:
    st.subheader("Full suite")
    st.markdown("One click runs a live check of each capability: the tools, retrieval, structured output, injection scan, the agents, MCP, the squad, the regression cases and an end-to-end answer.")

    if st.button("▶️ Run the full suite", type="primary"):
        ok, suite = call(api.run_capstone_suite, spinner="Running every check (this can take a minute)...")
        if ok:
            st.session_state["capstone_suite"] = suite

    suite = st.session_state.get("capstone_suite")
    if suite:
        counts = suite.get("counts", {})
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Passed", counts.get("pass", 0))
        m2.metric("Failed", counts.get("fail", 0), delta_color="inverse")
        m3.metric("Skipped", counts.get("skipped", 0), help="A needed component was not running, so the check did not run. It is not a pass.")
        m4.metric("Total checks", suite.get("total", 0))
        st.caption(f"Ran at {suite.get('ran_at')}")

        if counts.get("skipped"):
            info_card("<b>Skipped is not passed.</b> A skipped check needs something that is not running (usually Ollama, the local LLM). "
                      "Start it and run the suite again to exercise that part for real.", "warn")
        if counts.get("fail"):
            info_card("<b>Failures are shown below with the reason.</b> Fix these before demoing.", "warn")

        for c in suite.get("checks", []):
            with st.container(border=True):
                a, b = st.columns([5, 2])
                a.markdown(f"**{c.get('check')}**")
                b.markdown(pill(c.get("status", "").upper(), STATUS_TONE.get(c.get("status"), "")) +
                           pill(f"Week {c.get('week')}", "week") + pill(f"{c.get('ms')} ms", "week"), unsafe_allow_html=True)
                st.caption(c.get("detail", ""))
    else:
        st.info("Press the button to run the suite.")

# ── Weak spots ───────────────────────────────────────────────
with tab_weak:
    st.subheader("Known weak spots")
    st.markdown("A demo where nothing ever fails hides the failures. These are the limits of this app, in plain words, with the first fix to try.")
    ok, data = call(api.capstone_weak_spots, spinner="Loading weak spots...")
    if ok:
        spots = sorted(data.get("weak_spots", []), key=lambda s: SEVERITY_ORDER.get(s.get("severity"), 3))
        for s in spots:
            with st.container(border=True):
                st.markdown(f"#### {s.get('area')}  " + pill(s.get("severity", "").upper(), SEVERITY_TONE.get(s.get("severity"), "")), unsafe_allow_html=True)
                st.write(s.get("what"))
                st.markdown(f"**First fix to try:** {s.get('next')}")

# ── Four-part demo ───────────────────────────────────────────
with tab_demo:
    st.subheader("Four-part demo")
    st.markdown("A real run, a real failure you caught, a number that improved, and what is next. The numbers below come from saved results, not from this page.")
    ok, demo = call(api.capstone_demo, spinner="Preparing the demo script...")
    if ok:
        for i, part in enumerate(demo.get("parts", []), start=1):
            with st.container(border=True):
                st.markdown(f"#### {part.get('part')}")
                st.markdown(pill(f"Where: {part.get('where')}", "week"), unsafe_allow_html=True)
                st.write(part.get("do"))
                st.caption(f"Needs: {part.get('needs')}")
                nums = part.get("numbers")
                if nums:
                    n1, n2, n3 = st.columns(3)
                    n1.metric(f"{nums.get('metric')}: before", f"{nums.get('before', 0):.3f}")
                    n2.metric(f"{nums.get('metric')}: after", f"{nums.get('after', 0):.3f}", delta=f"{nums.get('after', 0) - nums.get('before', 0):+.3f}")
                    n3.metric("MRR before to after", f"{nums.get('mrr_after', 0):.3f}", delta=f"{nums.get('mrr_after', 0) - nums.get('mrr_before', 0):+.3f}")
                    st.caption(f"Measured on {nums.get('questions')} questions. A set this small can swing by a whole question, so say so.")
                elif i == 3:
                    st.info("No saved evaluation results yet. Run the evaluation on the Evaluation page first.")
        st.markdown("##### Tough questions to prepare for")
        for q in demo.get("tough_questions", []):
            st.markdown(f"- {q}")

# ── Packaging checklist ──────────────────────────────────────
with tab_pack:
    st.subheader("Packaging checklist")
    st.caption("Mapped to the Week 12 brief. Ticks are kept for this browser session only.")
    items = [
        ("single", "**Single entry point.** The whole app starts with one command: `python run.py` (it starts the backend, waits for it to be healthy, then opens this UI)."),
        ("guide", "**A guide a stranger can follow.** Read the Documentation page from zero to a working answer, and try it as if you had never seen the app."),
        ("suite", "**Full eval suite.** Run the suite on the first tab and read every failed or skipped line."),
        ("weak", "**Known weak spots written down.** Review the second tab and be ready to name the top two."),
        ("report", "**Eval report.** Have the retrieval numbers (before and after) and the judge agreement on hand, with the size of each test set."),
        ("fresh", "**Fresh-eyes test.** Ask someone new to get an answer using only the guide."),
        ("demo", "**Demo rehearsed.** Practise the four parts, including a failure you show on purpose."),
    ]
    done = 0
    for key, text in items:
        if st.checkbox(text, key=f"pack_{key}"):
            done += 1
    st.progress(done / len(items), text=f"{done} of {len(items)} done")
    try:
        st.page_link("views/documentation.py", label="Open the Documentation page", icon="📖")
    except Exception:
        pass
