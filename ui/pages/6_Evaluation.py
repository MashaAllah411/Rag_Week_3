"""
ui/pages/6_Evaluation.py

Page 6: Evaluation, Failure Separation & LLM Judge (Weeks 4 & 6)
- Proof of fix: Baseline vs Hybrid metrics (Hit Rate@3, Recall@3, MRR)
- Diagnostic failure separation and human labeling
- Deterministic regex assertions tester
- LLM Judge V1 vs V2 calibration
"""
import streamlit as st
from ui.api_client import api

st.set_page_config(page_title="Evaluation & QA — Insurance RAG", page_icon="🎯", layout="wide")

st.title("🎯 Evaluation, Quality Proof & Failure Separation")
st.markdown(
    "Quantify retrieval quality improvement, diagnose root causes (retrieval vs generation failure), "
    "and validate outputs using regex assertions and calibrated LLM Judges."
)

tab_metrics, tab_failures, tab_assertions, tab_judge = st.tabs([
    "📈 Before / After Improvement Proof",
    "🔍 Failure Analysis & Labeling",
    "✅ Deterministic Regex Assertions",
    "⚖️ LLM Judge V1 vs V2"
])

# ── Tab 1: Improvement Proof ─────────────────────────────────
with tab_metrics:
    st.subheader("Retrieval Quality Proof-of-Fix")

    try:
        metrics = api.get_eval_metrics()
        b = metrics.get("before", {})
        a = metrics.get("after", {})
        imp = metrics.get("improvement", {})

        m1, m2, m3 = st.columns(3)
        m1.metric("Hit Rate@3", f"{a.get('hit_rate', 0)*100:.1f}%", delta=f"{imp.get('hit_rate_delta', 0)*100:+.1f}% vs Baseline")
        m2.metric("Mean Reciprocal Rank (MRR)", f"{a.get('mrr', 0):.3f}", delta=f"{imp.get('mrr_delta', 0):+.3f} vs Baseline")
        m3.metric("Recall@3", f"{a.get('recall', 0):.3f}", delta="Evaluated over 25 questions")

        st.markdown("### Side-by-Side Comparison")
        c_b, c_a = st.columns(2)
        with c_b:
            with st.container(border=True):
                st.markdown(f"#### 🔴 {b.get('label')}")
                st.write(f"- **Hit Rate@3**: {b.get('hit_rate') * 100:.1f}%")
                st.write(f"- **Recall@3**: {b.get('recall'):.3f}")
                st.write(f"- **MRR**: {b.get('mrr'):.3f}")
                st.caption(f"Tested over {b.get('num_questions')} questions (top_k={b.get('top_k')})")
        with c_a:
            with st.container(border=True):
                st.markdown(f"#### 🟢 {a.get('label')}")
                st.write(f"- **Hit Rate@3**: {a.get('hit_rate') * 100:.1f}%")
                st.write(f"- **Recall@3**: {a.get('recall'):.3f}")
                st.write(f"- **MRR**: {a.get('mrr'):.3f}")
                st.caption(f"Tested over {a.get('num_questions')} questions (top_k={a.get('top_k')})")

        st.info(f"**Root Architectural Fix:** {imp.get('one_change_made')}")

    except Exception as e:
        st.error(f"Failed to load metrics: {e}")

# ── Tab 2: Failure Analysis & Labeling ────────────────────────
with tab_failures:
    st.subheader("Diagnostic Failure Separation")
    st.markdown("Diagnose whether errors originate from the retrieval stage or generation stage.")

    try:
        f_data = api.get_failures()
        failures = f_data.get("failures", [])

        if failures:
            q_options = [f["question"] for f in failures]
            selected_q = st.selectbox("Select Question to Inspect", q_options)
            q_item = next(f for f in failures if f["question"] == selected_q)

            col_diag, col_label = st.columns([2, 1])

            with col_diag:
                st.markdown(f"**Question**: *{q_item.get('question')}*")
                st.caption(f"Ground Truth Relevant Chunks: `{q_item.get('relevant_chunks')}`")

                b_res = q_item.get("baseline", {})
                h_res = q_item.get("hybrid", {})

                st.write(f"- Baseline Retrieval: `{b_res.get('retrieved')}` ➔ Auto Label: **{b_res.get('auto_label')}**")
                st.write(f"- Hybrid Retrieval: `{h_res.get('retrieved')}` ➔ Auto Label: **{h_res.get('auto_label')}**")
                st.info(f"Effective Failure Label: **{q_item.get('effective_label')}**")

            with col_label:
                st.markdown("#### Human Review Override")
                new_label = st.selectbox("Assign Label", ["pass", "retrieval_failure", "generation_failure"])
                evidence = st.text_input("Reviewer Evidence / Note")
                if st.button("💾 Save Label Override"):
                    try:
                        api.save_failure_label(selected_q, new_label, evidence)
                        st.success("Human override saved.")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Failed to save: {err}")
    except Exception as e:
        st.error(f"Error loading failures: {e}")

# ── Tab 3: Deterministic Regex Assertions ─────────────────────
with tab_assertions:
    st.subheader("Deterministic Regex Assertions (Week 6)")
    st.markdown("Validate that generated claim outputs contain required factual components.")

    sample_claim_text = (
        "Claim CLM-2024-00123 occurred on 2024-05-15. "
        "Claim is APPROVED with net payout of $3,500.00 after deductible."
    )
    test_text = st.text_area("Response Text to Test", value=sample_claim_text, height=120)
    is_denial = st.checkbox("Is Claim Denial? (Enforces Section/Clause citation)")

    if st.button("🧪 Run Regex Assertions", type="primary"):
        res = api.check_assertions(test_text, is_denial=is_denial)
        st.markdown("---")
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Claim Number", "PASS" if res.get("claim_number_format") else "FAIL")
        a2.metric("Date of Loss", "PASS" if res.get("date_of_loss_present") else "FAIL")
        a3.metric("Numeric Deductible", "PASS" if res.get("numeric_deductible_present") else "FAIL")
        a4.metric("Clause Cited", "PASS" if res.get("exclusion_clause_cited") else "FAIL")

        if res.get("all_passed"):
            st.success("All 4 assertions passed.")
        else:
            st.warning(f"{res.get('passed_count')}/4 assertions passed.")

# ── Tab 4: LLM Judge V1 vs V2 ────────────────────────────────
with tab_judge:
    st.subheader("Calibrated LLM Judge (Ollama)")
    st.markdown("Judge V2 incorporates few-shot disagreement calibration examples to correct false negative fallback misjudgments.")

    j_query = st.text_input("Query", value="What is the schedule of depreciation for fixing IDV of the vehicle?")
    j_context = st.text_area("Retrieved Context", value="Age of vehicle not exceeding 6 months: 0% depreciation. Exceeding 6 months but not exceeding 1 year: 5%.", height=100)
    j_answer = st.text_area("Candidate Answer", value="For vehicles up to 6 months old, depreciation is 0%. For 6 months to 1 year, it is 5%.", height=80)
    j_version = st.radio("Judge Prompt Version", ["v2", "v1"], horizontal=True,
                         help="V2 includes few-shot calibration examples for out-of-scope and fallback edge cases.")

    if st.button("⚖️ Run LLM Judge", type="primary"):
        with st.spinner("Calling local LLM Judge..."):
            try:
                j_res = api.evaluate_judge(j_query, j_context, j_answer, judge_version=j_version)
                st.markdown("---")
                if j_res.get("verdict") == 1:
                    st.success(f"Verdict: **PASS (1)** — Answer is factually grounded in context.")
                else:
                    st.error(f"Verdict: **FAIL (0)** — Answer hallucinated or unsupported.")
                st.caption(f"Raw Judge Response:\n{j_res.get('raw_judge_response')}")
            except Exception as e:
                st.error(f"Judge evaluation failed: {e}")
