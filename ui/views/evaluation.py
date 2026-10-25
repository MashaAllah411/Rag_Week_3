"""
ui/views/evaluation.py

Weeks 4, 6 and 11 - Evaluation: retrieval quality on the current corpus, the historical
before/after record, failure separation, assertions, the LLM judge (and whether to trust it),
and the failure-to-test regression loop.
"""
import pandas as pd
import streamlit as st

from ui.api_client import api
from ui.components import call, info_card, ollama_notice, page_header, pill

page_header(
    "Evaluation", "🎯",
    "Measure whether a change actually helped: retrieval hit-rate, failure type, rule checks, judge agreement and permanent regression tests.",
    weeks=["4", "6", "11"],
)

MODES = {"semantic": "Semantic only", "hybrid": "Hybrid (BM25 + semantic, RRF)", "reranked": "Hybrid + reranker + MMR"}


@st.cache_data(ttl=10, show_spinner=False)
def _ollama_up() -> bool:
    try:
        return bool(api.get_system_status().get("components", {}).get("ollama_llm", {}).get("reachable"))
    except Exception:
        return False


tab_quality, tab_hist, tab_fail, tab_assert, tab_judge, tab_loop = st.tabs([
    "📈 Retrieval quality", "🗄️ Historical (HR corpus)", "🔍 Failure analysis",
    "✅ Assertions", "⚖️ LLM judge", "🔁 Failure → test loop",
])

# ── Retrieval quality (current corpus) ───────────────────────
with tab_quality:
    st.subheader("Does the right passage show up in the top results?")
    st.markdown("Each question has a known answer phrase. A retrieved chunk counts as a **hit** if it contains that phrase. "
                "This runs on retrieval only, so it needs **no LLM**.")

    ok, ds = call(api.eval_datasets, spinner="Loading dataset status...")
    if ok:
        with st.expander("Which datasets can be scored on the current index?", expanded=False):
            for item in ds["datasets"]:
                tone = "ok" if item["usable_on_current_index"] else "bad"
                label = "Usable now" if item["usable_on_current_index"] else "Not usable on current index"
                st.markdown(f"**{item['name']}** &nbsp; {pill(label, tone)}", unsafe_allow_html=True)
                st.caption(f"`{item['file']}` · {item['questions']} questions · corpus: {item['corpus']} · "
                           f"ground truth: {item['ground_truth']}")
                if item["reason"]:
                    st.write(item["reason"])

    top_k = st.slider("Top-k (chunks considered per question)", 1, 10, 3, key="ev_topk")
    b1, b2, b3, b4 = st.columns(4)
    run_modes = []
    for col, (mode, label) in zip((b1, b2, b3), MODES.items()):
        if col.button(f"Run {mode}", key=f"ev_run_{mode}", width="stretch", help=label):
            run_modes = [mode]
    if b4.button("Run all three", type="primary", key="ev_run_all", width="stretch"):
        run_modes = list(MODES)
    for mode in run_modes:
        ok, res = call(api.run_insurance_eval, mode, top_k,
                       spinner=f"Evaluating {mode} (the reranker loads on first use)...")
        if ok:
            st.success(f"{MODES[mode]}: hit-rate@{res['top_k']} = {res['hit_rate']:.3f}, MRR = {res['mrr']:.3f}")

    ok, saved = call(api.insurance_eval_results, spinner="Loading saved results...")
    if ok:
        results = {m: r for m, r in saved.items() if r}
        if not results:
            st.info("No results yet. Click **Run all three** to measure each retrieval mode on the current documents.")
        else:
            n = next(iter(results.values()))["num_questions"]
            frame = pd.DataFrame([{
                "Mode": MODES[m], "top-k": r["top_k"], "Hit-rate@k": r["hit_rate"],
                "Recall@k": r["recall"], "MRR": r["mrr"], "Questions": r["num_questions"],
            } for m, r in results.items()])
            m_cols = st.columns(len(results))
            for col, (m, r) in zip(m_cols, results.items()):
                col.metric(MODES[m], f"{r['hit_rate'] * 100:.1f}% hit", help=f"top-k={r['top_k']}")
                col.caption(f"MRR {r['mrr']:.3f} · recall {r['recall']:.3f}")
            st.dataframe(frame, hide_index=True, width="stretch")
            st.bar_chart(frame.set_index("Mode")[["Hit-rate@k", "Recall@k", "MRR"]])

            # "What the numbers say": every sentence is computed from the displayed results.
            lines = []
            sem, hyb, rer = (results.get(k) for k in ("semantic", "hybrid", "reranked"))
            if sem and hyb:
                d = hyb["hit_rate"] - sem["hit_rate"]
                dm = hyb["mrr"] - sem["mrr"]
                verb = "improved" if d > 0 else ("matched" if d == 0 else "lowered")
                lines.append(f"Hybrid {verb} hit-rate versus semantic-only by {d * 100:+.1f} points "
                             f"({sem['hit_rate']:.3f} → {hyb['hit_rate']:.3f}) and MRR by {dm:+.3f}.")
            if hyb and rer:
                d = rer["hit_rate"] - hyb["hit_rate"]
                if d < 0:
                    lines.append(f"Reranked is **worse** than hybrid on this set ({rer['hit_rate']:.3f} vs {hyb['hit_rate']:.3f} "
                                 f"hit-rate): the extra reranking/diversity step pushed answers out of the top {rer['top_k']}. "
                                 "Check the per-question grid below to see which questions it lost.")
                elif d > 0:
                    lines.append(f"Reranked is better than hybrid by {d * 100:+.1f} points hit-rate.")
                else:
                    lines.append("Reranked matched hybrid on hit-rate.")
            if len({r["top_k"] for r in results.values()}) > 1:
                lines.append("Modes were saved with different top-k values, so compare them only after re-running with the same k.")
            lines.append(f"Caveat: only **{n} questions**, so a difference of one question is "
                         f"{100 / n:.1f} points of hit-rate and may be noise. Grow the set before trusting small gaps.")
            info_card("<b>What the numbers say</b><br>" + "<br>".join(f"• {l}" for l in lines))

            st.markdown("#### Per-question results")
            first = next(iter(results.values()))
            grid = []
            for i, item in enumerate(first["per_question"]):
                row = {"ID": item["id"], "Question": item["question"], "Expected phrase": " | ".join(item["expected_text"])}
                for m, r in results.items():
                    pq = r["per_question"][i] if i < len(r["per_question"]) and r["per_question"][i]["id"] == item["id"] \
                        else next((x for x in r["per_question"] if x["id"] == item["id"]), None)
                    if pq is None:
                        row[m] = "-"
                    elif pq["hit"]:
                        row[m] = f"✅ rank {pq['relevant_flags'].index(True) + 1}"
                    else:
                        row[m] = "❌ miss"
                grid.append(row)
            st.dataframe(pd.DataFrame(grid), hide_index=True, width="stretch")
            with st.expander("Retrieved chunk ids per question and mode"):
                for item in first["per_question"]:
                    st.markdown(f"**{item['id']}** · {item['question']}")
                    for m, r in results.items():
                        pq = next((x for x in r["per_question"] if x["id"] == item["id"]), None)
                        if pq:
                            marks = ", ".join(f"{'✅' if f else '▫️'} `{cid}`" for cid, f in zip(pq["retrieved_ids"], pq["relevant_flags"]))
                            st.caption(f"{m}: {marks}")

# ── Historical ───────────────────────────────────────────────
with tab_hist:
    st.subheader("Historical retrieval proof (Weeks 4-6)")
    info_card("<b>Measured on an earlier HR-policy PDF, not the current documents.</b> The questions ask about a different "
              "document and the ground truth uses old chunk ids (such as <code>chunk_107</code>), so these numbers cannot be "
              "reproduced on the current index. They are kept as the record of the original before/after experiment. "
              "Use the <b>Retrieval quality</b> tab for live measurements.", "warn")
    ok, metrics = call(api.get_eval_metrics, spinner="Loading saved metrics...")
    if ok:
        b, a, imp = metrics.get("before", {}), metrics.get("after", {}), metrics.get("improvement", {})
        m1, m2, m3 = st.columns(3)
        m1.metric("Hit Rate@3", f"{a.get('hit_rate', 0) * 100:.1f}%", delta=f"{imp.get('hit_rate_delta', 0) * 100:+.1f}% vs baseline")
        m2.metric("MRR", f"{a.get('mrr', 0):.3f}", delta=f"{imp.get('mrr_delta', 0):+.3f} vs baseline")
        m3.metric("Recall@3", f"{a.get('recall', 0):.3f}", delta=f"{a.get('num_questions', '?')} questions")
        c_b, c_a = st.columns(2)
        for col, data, icon in ((c_b, b, "🔴"), (c_a, a, "🟢")):
            with col, st.container(border=True):
                st.markdown(f"#### {icon} {data.get('label')}")
                st.write(f"- **Hit Rate@{data.get('top_k')}**: {data.get('hit_rate', 0) * 100:.1f}%")
                st.write(f"- **Recall@{data.get('top_k')}**: {data.get('recall', 0):.3f}")
                st.write(f"- **MRR**: {data.get('mrr', 0):.3f}")
                st.caption(f"{data.get('num_questions')} questions, top_k={data.get('top_k')}")
        st.info(f"**The one change made:** {imp.get('one_change_made')}")
        ok2, res = call(api.get_eval_results, "hybrid", spinner="Loading per-question results...", show_error=False)
        if ok2:
            with st.expander("Per-question results (hybrid, historical)"):
                st.dataframe(pd.DataFrame(res.get("per_question", [])), hide_index=True, width="stretch")

# ── Failure analysis ─────────────────────────────────────────
with tab_fail:
    st.subheader("Wrong document fetched, or right document and a bad answer?")
    st.markdown("These two failures need different fixes. Diagnose which one each question is, then record a human override. "
                "(This analysis is over the historical question set.)")
    ok, f_data = call(api.get_failures, spinner="Loading failure analysis...")
    if ok:
        failures = f_data.get("failures", [])
        if not failures:
            st.info("No failure records available.")
        else:
            selected_q = st.selectbox("Select question to inspect", [f["question"] for f in failures], key="ev_fail_q")
            q_item = next(f for f in failures if f["question"] == selected_q)
            col_diag, col_label = st.columns([2, 1])
            with col_diag:
                st.markdown(f"**Question**: *{q_item.get('question')}*")
                st.caption(f"Ground-truth relevant chunks: `{q_item.get('relevant_chunks')}`")
                b_res, h_res = q_item.get("baseline", {}), q_item.get("hybrid", {})
                st.write(f"- Baseline retrieval: `{b_res.get('retrieved')}` → auto label **{b_res.get('auto_label')}**")
                st.write(f"- Hybrid retrieval: `{h_res.get('retrieved')}` → auto label **{h_res.get('auto_label')}**")
                st.info(f"Effective failure label: **{q_item.get('effective_label')}**")
            with col_label:
                st.markdown("#### Human review override")
                new_label = st.selectbox("Assign label", ["pass", "retrieval_failure", "generation_failure"], key="ev_fail_label")
                evidence = st.text_input("Reviewer evidence / note", key="ev_fail_evidence")
                if st.button("💾 Save label override", key="ev_fail_save"):
                    ok2, _ = call(api.save_failure_label, selected_q, new_label, evidence, spinner="Saving...")
                    if ok2:
                        st.success("Human override saved.")
                        st.rerun()

# ── Assertions ───────────────────────────────────────────────
with tab_assert:
    st.subheader("Rule checks that cost nothing to run")
    st.markdown("Do these first: they are instant and free. They check that an answer contains the required facts.")
    sample_claim_text = ("Claim CLM-2024-00123 occurred on 2024-05-15. "
                         "Claim is APPROVED with net payout of $3,500.00 after deductible.")
    test_text = st.text_area("Response text to test", value=sample_claim_text, height=120, key="ev_assert_text")
    is_denial = st.checkbox("Claim is a denial (requires a Section/Clause citation)", key="ev_assert_denial")
    if st.button("🧪 Run assertions", type="primary", key="ev_assert_btn"):
        ok, res = call(api.check_assertions, test_text, is_denial=is_denial, spinner="Checking...")
        if ok:
            st.session_state["ev_assert_res"] = res
    res = st.session_state.get("ev_assert_res")
    if res:
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Claim number", "PASS" if res.get("claim_number_format") else "FAIL")
        a2.metric("Date of loss", "PASS" if res.get("date_of_loss_present") else "FAIL")
        a3.metric("Numeric deductible", "PASS" if res.get("numeric_deductible_present") else "FAIL")
        a4.metric("Clause cited", "PASS" if res.get("exclusion_clause_cited") else "FAIL")
        if res.get("all_passed"):
            st.success("All 4 assertions passed.")
        else:
            st.warning(f"{res.get('passed_count')}/4 assertions passed.")

# ── LLM judge ────────────────────────────────────────────────
with tab_judge:
    st.subheader("Using an AI to grade an answer, and checking it first")
    st.markdown("A rule cannot judge tone or grounding, so a second model grades the answer. An unchecked judge is just a "
                "confident number, so first measure how often it agrees with a human.")

    st.markdown("#### Can we trust the judge? (agreement with human labels)")
    ok, jv = call(api.judge_validation, spinner="Loading judge validation...")
    if ok:
        if not jv.get("available"):
            st.info("No human labels file found, so agreement cannot be computed.")
        else:
            v1, c2, c3, c4 = st.columns(4)
            v1.metric("Human-labelled cases", jv["total_cases"], help=jv.get("criterion", ""))
            c2.metric("Human PASS / FAIL", f"{jv['human_pass']} / {jv['human_fail']}")
            c3.metric("Judge V1 agreement", f"{jv['judge_v1_agreement_pct']}%")
            c4.metric("Trust threshold", f"{jv['trust_threshold_pct']}%")
            if jv["judge_v1_trusted"]:
                st.success("Judge V1 meets the trust threshold.")
            else:
                st.warning("Judge V1 is below the trust threshold: its scores should not be relied on without recalibration.")
            st.caption(f"Criterion: {jv.get('criterion')} · labelled {jv.get('labelled_at')}")
            dis = jv.get("judge_v1_disagreements", [])
            if dis:
                with st.expander(f"{len(dis)} cases where Judge V1 disagreed with the human"):
                    st.dataframe(pd.DataFrame([{
                        "ID": d["id"], "Query": d["query"],
                        "Human": "PASS" if d["human"] == 1 else "FAIL",
                        "Judge V1": "PASS" if d["judge_v1"] == 1 else "FAIL",
                        "Answer (start)": d["answer"],
                    } for d in dis]), hide_index=True, width="stretch")
            info_card(jv["judge_v2_note"])

    st.markdown("#### Try the judge")
    if not _ollama_up():
        ollama_notice("The judge needs the local LLM")
    j_query = st.text_input("Query", value="What is the schedule of depreciation for fixing IDV of the vehicle?", key="ev_j_query")
    j_context = st.text_area("Retrieved context",
                             value="Age of vehicle not exceeding 6 months: 0% depreciation. Exceeding 6 months but not exceeding 1 year: 5%.",
                             height=100, key="ev_j_context")
    j_answer = st.text_area("Candidate answer",
                            value="For vehicles up to 6 months old, depreciation is 0%. For 6 months to 1 year, it is 5%.",
                            height=80, key="ev_j_answer")
    j_version = st.radio("Judge prompt version", ["v2", "v1"], horizontal=True, key="ev_j_version",
                         help="V2 adds few-shot calibration examples for out-of-scope and fallback edge cases.")
    if st.button("⚖️ Run LLM judge", type="primary", key="ev_j_btn"):
        ok, res = call(api.evaluate_judge, j_query, j_context, j_answer, judge_version=j_version, spinner="Calling the local judge...")
        if ok:
            st.session_state["ev_j_res"] = res
    res = st.session_state.get("ev_j_res")
    if res:
        if res.get("verdict_label") == "ERROR":
            ollama_notice("The judge call failed")
            st.caption(res.get("raw_judge_response", ""))
        else:
            if res.get("verdict") == 1:
                st.success("Verdict: **PASS (1)**: the answer is grounded in the context.")
            else:
                st.error("Verdict: **FAIL (0)**: the answer is unsupported or hallucinated.")
            st.caption(f"Raw judge response:\n{res.get('raw_judge_response')}")

# ── Failure -> test loop ─────────────────────────────────────
with tab_loop:
    st.subheader("Every real failure becomes a permanent test")
    st.markdown("When the support drill found a bad answer (a flood claim approved despite the Section 5.2 exclusion), it was "
                "turned into regression cases so the same mistake cannot quietly return. Run them any time.")
    ok, cases = call(api.regression_cases, spinner="Loading regression cases...")
    if ok:
        st.dataframe(pd.DataFrame([{
            "Case": c["id"], "What it guards": c["title"], "Origin": c["origin"], "Expected": c["expect_status"],
        } for c in cases["cases"]]), hide_index=True, width="stretch")
        with st.expander("Adjuster notes used by each case"):
            for c in cases["cases"]:
                st.markdown(f"**{c['id']}** ({c['incident_type']})")
                st.caption(c["notes"])
    if st.button("▶️ Run regression suite", type="primary", key="ev_loop_run"):
        ok, res = call(api.run_regression, spinner="Running regression cases...")
        if ok:
            st.session_state["ev_loop_res"] = res
    res = st.session_state.get("ev_loop_res")
    if res:
        (st.success if res["passed"] == res["total"] else st.error)(f"{res['passed']} of {res['total']} regression cases hold.")
        for r in res["results"]:
            obs = r["observed"]
            with st.container(border=True):
                st.markdown(f"{'✅' if r['passed'] else '❌'} **{r['id']}** · {r['title']}")
                o1, o2, o3 = st.columns(3)
                o1.metric("Status", obs["status"])
                o2.metric("Clause cited", obs["clause"] or "none")
                o3.metric("Net payable", f"${obs['net_payable']:,.2f}")
                st.caption(obs["reasoning"])
                for problem in r["problems"]:
                    st.error(problem)
