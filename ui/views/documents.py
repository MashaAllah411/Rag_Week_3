"""
ui/views/documents.py

Documents (Week 3): library, upload, chunk inspector and the chunk-size experiment.
"""
import pandas as pd
import streamlit as st

from ui.api_client import api
from ui.components import call, info_card, page_header

page_header(
    "Documents",
    "📄",
    "Manage the policy PDFs the assistant answers from, and see exactly how each one is split into passages.",
    weeks=["3"],
)

# Verified question/answer pairs for the shipped policies (each phrase exists in that PDF).
EXPERIMENT_DEFAULTS = {
    "InsurancePolicy.pdf": ("maximum cost protection removal disabled vehicle", "Rs 1500"),
    "Commercial_Vehicles_Package_Policy_93ee460add.pdf": ("painting charges material component depreciation",
                                                          "25% of total painting charges"),
}

tab_list, tab_upload, tab_inspect, tab_experiment = st.tabs(
    ["📚 Library", "📤 Upload", "🔍 Chunk inspector", "🧮 Chunk-size experiment"]
)


def _indexing_banner() -> None:
    ok, status = call(api.get_system_status, show_error=False)
    if not ok:
        return
    state = status.get("indexing", {})
    chunks = status.get("components", {}).get("vector_store", {}).get("chunks", 0)
    if state.get("state") == "indexing":
        info_card(f"<b>Indexing in progress:</b> <code>{state.get('current') or 'documents'}</code> "
                  f"({state.get('documents_done', 0)} finished). Refresh to update.")
    elif state.get("state") == "error":
        info_card(f"<b>The last indexing run failed:</b> {state.get('last_error')}", "warn")
    st.caption(f"Passages currently in the vector store: **{chunks}**")


# ── Library ──────────────────────────────────────────────────
with tab_list:
    top_l, top_r = st.columns([4, 1])
    with top_l:
        st.subheader("Indexed policy documents")
    with top_r:
        if st.button("🔄 Refresh", width="stretch"):
            st.rerun()
    _indexing_banner()

    ok, data = call(api.list_documents, spinner="Loading documents...")
    if ok:
        docs = data.get("documents", [])
        st.caption(f"Documents: **{data.get('count', 0)}** · Vector store: `{data.get('vector_db')}` "
                   f"(collection `{data.get('index_name')}`)")
        if not docs:
            st.info("No documents found in `resources/`. Use the Upload tab to add one.")
        for doc in docs:
            with st.expander(f"📑 {doc.get('title')} (`{doc.get('filename')}`)", expanded=len(docs) <= 2):
                col_info, col_actions = st.columns([4, 1])
                with col_info:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Pages", doc.get("pages"))
                    m2.metric("Size", f"{doc.get('size_kb')} KB")
                    m3.metric("Status", str(doc.get("status", "")).title())
                    st.markdown(f"- **Embedding model:** `{doc.get('embedding_model')}`")
                    st.markdown(f"- **Chunking:** `{doc.get('chunking_strategy')}`")
                    questions = doc.get("suggested_questions", [])
                    if questions:
                        st.markdown("**Questions to try**")
                        for q in questions:
                            st.caption(f"• *{q.get('label')}* - {q.get('query')}")
                with col_actions:
                    if st.button("🗑️ Delete", key=f"del_{doc.get('filename')}", type="secondary",
                                 help="Removes the PDF and its indexed passages"):
                        ok_d, res = call(api.delete_document, doc.get("filename"),
                                         spinner="Deleting document and its indexed passages...")
                        if ok_d:
                            st.success(f"Deleted `{res.get('filename')}`.")
                            st.rerun()

        st.markdown("---")
        st.subheader("Batch operations")
        st.caption("Re-reads every PDF in `resources/`, re-chunks it, embeds it and rebuilds the keyword index.")
        if st.button("⚡ Re-index all documents"):
            ok_r, res = call(api.reindex_documents, spinner="Starting background re-indexing...")
            if ok_r:
                st.success(res.get("message", "Re-indexing started."))

# ── Upload ───────────────────────────────────────────────────
with tab_upload:
    st.subheader("Upload a policy PDF")
    st.caption("Policy wordings, schedules or endorsements. PDF only, up to 20 MB. Scanned images inside the PDF are read with OCR.")
    uploaded = st.file_uploader("Choose a PDF file", type=["pdf"])
    if uploaded is not None:
        st.info(f"Selected **{uploaded.name}** ({round(len(uploaded.getvalue()) / 1024, 1)} KB)")
        if st.button("🚀 Upload & index", type="primary"):
            ok_u, res = call(api.upload_document, uploaded.getvalue(), uploaded.name,
                             spinner="Uploading and starting indexing...")
            if ok_u:
                st.success(res.get("message", "Upload saved."))
                st.info("The file is now being read, split into passages, embedded and stored. "
                        "Check progress on the Library tab (Refresh).")

# ── Chunk inspector ──────────────────────────────────────────
with tab_inspect:
    st.subheader("Chunk inspector")
    st.caption("Chunks are the passages the assistant searches. Pick a strategy and size to see where the cuts fall.")
    ok, docs_data = call(api.list_documents, show_error=True)
    options = [d.get("filename") for d in docs_data.get("documents", [])] if ok else []
    if not options:
        st.info("No documents available to inspect.")
    else:
        c1, c2 = st.columns([2, 2])
        with c1:
            selected = st.selectbox("Document", options, key="inspect_doc")
        with c2:
            strategy = st.radio("Strategy", ["fixed", "keyword", "semantic"], horizontal=True,
                                format_func=lambda s: {"fixed": "Fixed size", "keyword": "Keyword topics",
                                                       "semantic": "Semantic (embeddings)"}[s],
                                help="Fixed: character windows with overlap. Keyword: splits when the topic words change. "
                                     "Semantic: splits where meaning shifts (slower, uses the embedding model).")
        size, overlap = 900, 150
        if strategy == "fixed":
            s1, s2 = st.columns(2)
            size = s1.slider("Chunk size (characters)", 200, 4000, 900, 100)
            overlap = s2.slider("Overlap (characters)", 0, 1000, 150, 25)
        if st.button("🔍 Inspect chunks", key="btn_inspect"):
            ok_i, res = call(api.inspect_document_chunks, selected, strategy, size, overlap,
                             spinner="Reading and chunking the document...")
            if ok_i:
                m1, m2, m3 = st.columns(3)
                m1.metric("Pages", res.get("total_pages"))
                m2.metric("Chunks", res.get("total_chunks"))
                m3.metric("Average length", f"{res.get('avg_length')} chars")
                st.markdown("#### First 20 chunks")
                for c in res.get("sample_chunks", []):
                    with st.container(border=True):
                        st.caption(f"**Chunk #{c.get('chunk_index')}** · {c.get('length')} characters")
                        st.text(c.get("preview"))

# ── Chunk-size experiment ────────────────────────────────────
with tab_experiment:
    st.subheader("Chunk-size experiment")
    info_card("<b>Week 3 check: did you try more than one chunk size and notice the difference?</b> "
              "Chunks that are too small split an answer across pieces; chunks that are too large bury it among "
              "unrelated text. This runs the same question at several sizes and reports where the answer ranks. "
              "It uses keyword ranking only, so it is instant and needs no LLM.")
    ok, docs_data = call(api.list_documents, show_error=False)
    options = [d.get("filename") for d in docs_data.get("documents", [])] if ok else []
    if not options:
        st.info("No documents available.")
    else:
        start = options.index("InsurancePolicy.pdf") if "InsurancePolicy.pdf" in options else 0
        selected = st.selectbox("Document", options, index=start, key="exp_doc")
        default_q, default_e = EXPERIMENT_DEFAULTS.get(selected, ("", ""))
        query = st.text_input("Question", value=default_q, key=f"exp_q_{selected}",
                              help="Words the retrieval step would search for")
        expected = st.text_input("Phrase that answers it (must appear in the document)",
                                 value=default_e, key=f"exp_e_{selected}")
        sizes = st.multiselect("Chunk sizes to compare", [200, 300, 450, 600, 900, 1200, 1500, 2500, 4000],
                               default=[300, 600, 900, 1500], key="exp_sizes")
        if st.button("▶ Run experiment", type="primary"):
            if len(query.strip()) < 3 or len(expected.strip()) < 2 or len(sizes) < 2:
                st.warning("Enter a question, the answer phrase, and pick at least two sizes.")
            else:
                ok_e, res = call(api.compare_chunk_sizes, selected, query, expected, sorted(sizes),
                                 spinner="Chunking at each size and ranking...")
                if ok_e:
                    rows = res.get("results", [])
                    df = pd.DataFrame(rows).rename(columns={
                        "chunk_size": "Chunk size", "overlap": "Overlap", "chunks": "Chunks",
                        "avg_length": "Avg length", "answer_in_a_chunk": "Answer intact in a chunk",
                        "answer_chunk_rank": "Rank of answer chunk", "found_in_top3": "In top 3"})
                    st.dataframe(df, hide_index=True, width="stretch")
                    chart_a, chart_b = st.columns(2)
                    with chart_a:
                        st.markdown("**Rank of the chunk holding the answer** (lower is better; missing = not found)")
                        rank_df = df.set_index("Chunk size")[["Rank of answer chunk"]].dropna()
                        if rank_df.empty:
                            st.info("The answer phrase was not intact in any chunk at these sizes.")
                        else:
                            st.bar_chart(rank_df)
                    with chart_b:
                        st.markdown("**Number of chunks**")
                        st.bar_chart(df.set_index("Chunk size")[["Chunks"]])
                    st.info(res.get("reading", ""))
                    best = [r for r in rows if r.get("found_in_top3")]
                    if best:
                        st.success("Sizes that keep the answer in the top 3: "
                                   + ", ".join(str(r["chunk_size"]) for r in best))
                    else:
                        st.warning("No tested size placed the answer in the top 3. Try other sizes or check the phrase.")
