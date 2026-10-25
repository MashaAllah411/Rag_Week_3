"""
ui/views/error_analysis.py

Week 5 - Error Analysis: read a fair sample of real traces, write one honest note per trace,
group the notes into named problems, rank them, and write a prediction before the next fix.
"""
import pandas as pd
import streamlit as st

from ui.api_client import api
from ui.components import call, info_card, page_header, pill

page_header(
    "Error Analysis", "🔬",
    "Turn 'it fails sometimes' into a ranked list of real problems by reading the app's actual answers.",
    weeks=["5"],
)

tab_sample, tab_notes, tab_tax, tab_predict = st.tabs([
    "① Sample", "② Read & note", "③ Taxonomy", "④ Predict",
])


def _load_sample(n: int, seed: int) -> None:
    ok, data = call(api.error_sample, n, seed, spinner="Drawing a random sample of traces...")
    if ok:
        st.session_state["ea_sample"] = data


def _existing_categories() -> list:
    ok, tax = call(api.error_taxonomy, spinner="Loading categories...", show_error=False)
    return [c["category"] for c in tax["categories"]] if ok else []


# Auto-load once with the defaults so the page is useful on first visit.
if "ea_sample" not in st.session_state:
    _load_sample(20, 42)

sample = st.session_state.get("ea_sample")

# ── ① Sample ─────────────────────────────────────────────────
with tab_sample:
    st.subheader("Take a fair, random sample")
    st.markdown("Reading only the good examples hides problems. A **seeded random sample** is fair and reproducible: the same "
                "seed always picks the same traces, so you cannot cherry-pick.")
    c1, c2 = st.columns(2)
    n = c1.slider("Traces to read", 5, 50, 20, key="ea_n", help="The brief suggests about 20.")
    seed = c2.number_input("Random seed", value=42, step=1, key="ea_seed")
    if st.button("Draw sample", type="primary", key="ea_draw"):
        _load_sample(int(n), int(seed))
        sample = st.session_state.get("ea_sample")
    if sample:
        m1, m2, m3 = st.columns(3)
        m1.metric("Traces in the log", sample["population"])
        m2.metric("Sampled", len(sample["sample"]))
        m3.metric("Seed", sample["seed"])
        if sample["population"] == 0:
            info_card("<b>No traces yet.</b> Traces are written whenever a question is answered. Ask a few questions in "
                      "<b>Search &amp; Q&amp;A</b>, then come back and draw a sample.")
        else:
            st.success(f"Sample of {len(sample['sample'])} drawn from {sample['population']} traces with seed {sample['seed']}.")

# ── ② Read & note ────────────────────────────────────────────
with tab_notes:
    st.subheader("Read each answer and write one honest sentence")
    info_card("Write what went wrong in <b>plain words first</b>. Decide on categories <b>afterwards</b>, once you have read "
              "many traces; categories chosen up front make you see only the problems you expected. "
              "Category and severity are optional on the first pass and can be added later.")
    if not sample or not sample["sample"]:
        st.info("Draw a sample in step ① first (traces appear after questions are asked in Search & Q&A).")
    else:
        items = sample["sample"]
        done = sum(1 for t in items if t.get("note", {}).get("note"))
        st.progress(done / len(items), text=f"{done} of {len(items)} traces have a note")
        existing = _existing_categories()
        for idx, trace in enumerate(items, start=1):
            saved = trace.get("note") or {}
            tid = trace["trace_id"]
            tag = "📝 noted" if saved.get("note") else "⬜ not read yet"
            with st.expander(f"{idx}. {tag} · {trace['query'][:90]}", expanded=False):
                st.markdown(f"**Question:** {trace['query']}")
                st.caption(f"Trace `{tid}` · {trace.get('retriever_type', '')}")
                chunks = trace.get("retrieved_chunks", [])
                if chunks:
                    st.dataframe(pd.DataFrame(chunks).rename(columns={"chunk_id": "Retrieved chunk", "score": "Score"}),
                                 hide_index=True, width="stretch")
                else:
                    st.caption("No chunks were retrieved.")
                st.markdown("**Answer:**")
                st.write(trace.get("answer") or "(empty)")
                with st.form(f"ea_form_{tid}"):
                    note = st.text_area("What went wrong (one honest sentence)?", value=saved.get("note", ""),
                                        key=f"ea_note_{tid}", height=70)
                    f1, f2, f3 = st.columns([2, 2, 1])
                    reuse = f1.selectbox("Reuse a category", [""] + existing,
                                         index=([""] + existing).index(saved["category"]) if saved.get("category") in existing else 0,
                                         key=f"ea_reuse_{tid}")
                    new_cat = f2.text_input("...or a new category", key=f"ea_cat_{tid}")
                    severity = f3.slider("Severity", 1, 5, int(saved.get("severity", 3)), key=f"ea_sev_{tid}")
                    submitted = st.form_submit_button("Save note")
                if submitted:
                    if len(note.strip()) < 3:
                        st.warning("Write at least a few words about what went wrong.")
                    else:
                        category = new_cat.strip() or reuse
                        ok, res = call(api.save_error_note, tid, note, category, int(severity), spinner="Saving note...")
                        if ok:
                            trace["note"] = res
                            st.success("Saved.")
                            st.rerun()
                if saved.get("note"):
                    st.markdown(pill(f"saved: {saved.get('category') or 'no category yet'} · severity {saved.get('severity')}", "ok"),
                                unsafe_allow_html=True)

# ── ③ Taxonomy ───────────────────────────────────────────────
with tab_tax:
    st.subheader("Group the notes and rank the problems")
    st.markdown("Problems are ranked by **frequency × average severity**: what happens often *and* hurts most comes first.")
    ok, tax = call(api.error_taxonomy, spinner="Building taxonomy...")
    if ok:
        cats = tax["categories"]
        st.metric("Notes written", tax["notes_written"])
        if not cats:
            st.info("No categorised notes yet. Add a category to your notes in step ② (after reading several traces).")
        else:
            if tax["fix_target"]:
                st.success(f"Fix target: **{tax['fix_target']}**, the highest-ranked problem.")
            frame = pd.DataFrame([{
                "Rank": i, "Problem": c["category"], "Count": c["count"], "Avg severity": c["avg_severity"],
                "Score (count × severity)": c["score"], "Example notes": " · ".join(c["examples"]),
            } for i, c in enumerate(cats, start=1)])
            st.dataframe(frame, hide_index=True, width="stretch")
            st.bar_chart(frame.set_index("Problem")["Score (count × severity)"])

# ── ④ Predict ────────────────────────────────────────────────
with tab_predict:
    st.subheader("Predict the result before you try the fix")
    st.markdown("Write down what you expect the fix to change, as a number if you can (for example: 'hit-rate@3 rises from "
                "0.92 to above 0.95'). Writing it first keeps you honest about whether the fix really worked.")
    ok, tax = call(api.error_taxonomy, spinner="Loading...", show_error=False)
    if ok and tax.get("fix_target"):
        st.caption(f"Current fix target from the taxonomy: **{tax['fix_target']}**")
    saved_prediction = (sample or {}).get("prediction", "") or (tax.get("prediction", "") if ok else "")
    prediction = st.text_area("My prediction", value=saved_prediction, height=120, key="ea_prediction")
    if st.button("Save prediction", type="primary", key="ea_pred_btn"):
        if len(prediction.strip()) < 3:
            st.warning("Write your prediction first.")
        else:
            ok2, res = call(api.save_prediction, prediction, spinner="Saving...")
            if ok2:
                if sample:
                    sample["prediction"] = res["prediction"]
                st.success("Prediction saved. Now make exactly one change and measure it on the Evaluation page.")
