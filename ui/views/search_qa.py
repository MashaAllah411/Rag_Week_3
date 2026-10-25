"""
ui/views/search_qa.py

Search & Q&A (Weeks 3, 4, 8): ask a question, see the answer, its sources and how it was produced.
"""
import streamlit as st

from ui.api_client import api
from ui.components import call, info_card, ollama_notice, page_header, pill

page_header(
    "Search & Q&A",
    "🔍",
    "Ask a question about your insurance documents. Every answer shows the passages it came from.",
    weeks=["3", "4", "8"],
)

_OUT_OF_SCOPE = "I can only answer questions related to"
_DONT_KNOW = "I don't know based on the provided documents"
_LLM_DOWN = "LLM unavailable"

ok_status, status = call(api.get_system_status, show_error=False)
llm_up = bool(ok_status and status.get("components", {}).get("ollama_llm", {}).get("reachable"))

# ── Sidebar controls ─────────────────────────────────────────
with st.sidebar:
    st.subheader("⚙️ Retrieval settings")
    mode = st.selectbox(
        "Retrieval mode",
        options=["hybrid", "reranked", "semantic"],
        help=("semantic: vector similarity only\n\n"
              "hybrid: vector + BM25 keyword search fused with reciprocal rank fusion\n\n"
              "reranked: hybrid, then a cross-encoder re-scores and MMR removes near-duplicates"),
    )
    top_k = st.slider("Passages to use (k)", 1, 10, 3)
    sim_threshold = st.slider("Confidence threshold", 0.0, 1.0, 0.0, 0.05,
                              help="The top passage must score at least this to count as a confident match")
    use_rewriter = st.toggle("Rewrite the question first (needs local LLM)", value=llm_up,
                             help="Uses the local LLM to turn a messy question into a better search. On by default only when the LLM is reachable.")
    scan_injection = st.toggle("Scan retrieved context for prompt injection", value=False,
                               help="Quarantines passages that contain hidden instructions before the LLM sees them (Week 8). Off by default.")

    doc_filter = None
    ok_docs, docs_data = call(api.list_documents, show_error=False)
    documents = docs_data.get("documents", []) if ok_docs else []
    if documents:
        choice = st.selectbox("Search in", ["All documents"] + [d.get("filename") for d in documents])
        if choice != "All documents":
            doc_filter = choice


if ok_status and not llm_up:
    ollama_notice("Written answers need the local LLM")

# ── Suggested questions ──────────────────────────────────────
DEFAULT_QUESTIONS = [
    ("IDV depreciation", "What is the schedule of depreciation for fixing IDV of the vehicle?"),
    ("Towing limit", "What is the maximum amount the company will bear for protection and removal of a disabled vehicle?"),
    ("Total loss", "When is the insured vehicle treated as a constructive total loss?"),
    ("Personal accident", "What is the compensation scale for owner-driver personal accident cover?"),
    ("Cancellation", "How much notice must the company give to cancel a policy on grounds of fraud?"),
    ("Drink driving", "Is accidental loss covered when the driver is under the influence of intoxicating liquor or drugs?"),
]
suggestions = [(q["label"], q["query"]) for d in documents
               if (doc_filter is None or d.get("filename") == doc_filter) for q in d.get("suggested_questions", [])][:6]
if not suggestions:
    suggestions = DEFAULT_QUESTIONS

st.markdown("##### 💡 Questions to try")
cols = st.columns(3)


def _use_suggestion(text: str) -> None:
    st.session_state["qa_question"] = text


for idx, (label, text) in enumerate(suggestions):
    cols[idx % 3].button(f"📌 {label}", key=f"sq_{idx}", width="stretch",
                         on_click=_use_suggestion, args=(text,), help=text)

if "qa_question" not in st.session_state:
    st.session_state["qa_question"] = DEFAULT_QUESTIONS[0][1]
question = st.text_input("Your question", key="qa_question")

if st.button("🔎 Ask", type="primary", width="stretch"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        ok, res = call(api.ask, question=question, mode=mode, top_k=top_k, similarity_threshold=sim_threshold,
                       use_query_rewriter=use_rewriter, document_name=doc_filter, scan_injection=scan_injection,
                       spinner=f"Running the {mode} pipeline...")
        if ok:
            st.session_state["qa_result"] = res

res = st.session_state.get("qa_result")
if res:
    st.markdown("---")
    answer = res.get("answer", "")
    chunks = res.get("retrieved_chunks", [])
    steps = res.get("pipeline_steps", [])

    col_ans, col_meta = st.columns([3, 1])
    with col_meta:
        conf = res.get("confidence", "unknown").upper()
        tone = {"HIGH": "ok", "LOW": "warn"}.get(conf, "")
        st.markdown(f"**Confidence** {pill(conf, tone)}", unsafe_allow_html=True)
        st.caption(f"Mode: `{res.get('mode')}` · Source: `{res.get('source_document')}`")
        rewritten = res.get("rewritten_query")
        if rewritten and rewritten != res.get("question"):
            st.info(f"**Searched for:**\n\n*{rewritten}*")

    with col_ans:
        st.markdown("### 💬 Answer")
        if answer.startswith(_OUT_OF_SCOPE):
            info_card(f"<b>Out of scope.</b> {answer} Try a question about coverage, claims, premiums or the policy terms.")
        elif answer.startswith(_DONT_KNOW):
            info_card("<b>Not found in the documents.</b> The assistant declined to guess because the retrieved passages "
                      "do not clearly answer this. Rephrase the question or check the passages below.")
        elif answer.startswith(_LLM_DOWN):
            info_card("<b>No written answer.</b> The local LLM is not running, so the useful result is the "
                      "source passages below, ranked by relevance.", "sim")
            with st.expander("Technical detail"):
                st.code(answer, language="text")
        else:
            st.markdown(answer)

    # Sources ----------------------------------------------------
    if chunks:
        st.markdown("##### 📎 Sources")
        for i, c in enumerate(chunks, 1):
            doc = (c.get("chunk_id") or "").split(":")[0]
            st.markdown(f"{i}. `{c.get('chunk_id')}` — score {c.get('score', 0.0):.4f}" + (f" · from *{doc}*" if doc else ""))

    # Injection scan messages -------------------------------------
    for s in steps:
        if "Injection scan quarantined" in s:
            st.warning(f"🛑 {s}. The flagged passage was removed before reaching the LLM.")
        elif s.startswith("Injection scan"):
            st.success(f"✅ {s}")

    with st.expander("🧭 How this answer was produced"):
        for n, s in enumerate(steps, 1):
            st.write(f"**{n}.** {s}")

    st.subheader(f"📑 Retrieved passages ({len(chunks)})")
    if not chunks:
        st.info("No passages matched this question, document filter and threshold.")
    for i, c in enumerate(chunks, 1):
        with st.container(border=True):
            left, right = st.columns([1, 4])
            with left:
                st.markdown(f"**#{i}**")
                st.caption(f"`{c.get('chunk_id')}`")
                st.metric("Score", f"{c.get('score', 0.0):.4f}")
                if c.get("semantic_rank"):
                    st.caption(f"Semantic rank #{c['semantic_rank']}")
                if c.get("bm25_rank"):
                    st.caption(f"Keyword (BM25) rank #{c['bm25_rank']}")
                if c.get("rerank_score") is not None:
                    st.caption(f"Rerank score {c['rerank_score']:.4f}")
            with right:
                st.markdown(c.get("text", ""))
