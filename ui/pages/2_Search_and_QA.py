"""
ui/pages/2_Search_and_QA.py

Page 2: Search & Grounded Question Answering
- Query input with dynamic suggested questions
- Mode selection: Semantic | Hybrid (RRF) | Reranked (Cross-Encoder + MMR)
- Scope guard & query rewriting visibility
- Grounded answer, citations, confidence badge, and retrieved chunks with scores
"""
import streamlit as st
from ui.api_client import api

st.set_page_config(page_title="Search & Q&A — Insurance RAG", page_icon="🔍", layout="wide")

st.title("🔍 Search & Policy Question Answering")
st.markdown("Ask natural language questions against indexed insurance documents using advanced retrieval pipelines.")

# ── Sidebar Controls ─────────────────────────────────────────
with st.sidebar:
    st.subheader("⚙️ Retrieval Settings")

    mode = st.selectbox(
        "Retrieval Mode",
        options=["hybrid", "reranked", "semantic"],
        index=0,
        help=(
            "semantic: Pinecone vector search only\n"
            "hybrid: Pinecone + BM25 keyword search fused via RRF\n"
            "reranked: Hybrid + Cross-Encoder reranker + MMR diversity"
        )
    )

    top_k = st.slider("Top Chunks (k)", min_value=1, max_value=10, value=3)
    sim_threshold = st.slider("Confidence Threshold", min_value=0.0, max_value=1.0, value=0.0, step=0.05)
    use_rewriter = st.toggle("Enable Query Rewriter (Ollama)", value=True, help="Uses local LLM to rewrite ambiguous queries")

    # Document filter
    doc_filter = None
    try:
        doc_list = api.list_documents().get("documents", [])
        doc_names = ["All Documents"] + [d.get("filename") for d in doc_list]
        selected_doc = st.selectbox("Target Document", doc_names)
        if selected_doc != "All Documents":
            doc_filter = selected_doc
    except Exception:
        pass

# ── Suggested Questions ──────────────────────────────────────
st.markdown("##### 💡 Suggested Questions")
sq_cols = st.columns(3)
quick_queries = [
    ("IDV Depreciation?", "What is the schedule of depreciation for fixing IDV of the vehicle?"),
    ("Zero Dep Add-on?", "What are the rules and exclusions for Depreciation Reimbursement add-on cover?"),
    ("Engine Guard Cover?", "What damages are covered under the Engine Guard add-on?"),
    ("Personal Accident?", "What is the compensation scale for Owner-Driver personal accident cover?"),
    ("Notice Period?", "How many weeks notice must a staff member give when resigning?"),
    ("Basement Flood?", "Does standard policy cover basement water damage from rising lake water?")
]

preset_query = ""
for idx, (lbl, query_text) in enumerate(quick_queries):
    col = sq_cols[idx % 3]
    if col.button(f"📌 {lbl}", key=f"sq_{idx}", use_container_width=True):
        st.session_state["query_input"] = query_text

# ── Question Input ───────────────────────────────────────────
query_val = st.session_state.get("query_input", "What is the schedule of depreciation for fixing IDV of the vehicle?")
user_query = st.text_input("Enter your insurance policy question:", value=query_val, key="main_query_input")

if st.button("🔎 Submit Question", type="primary", use_container_width=True):
    if not user_query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner(f"Running RAG pipeline in '{mode}' mode..."):
            try:
                res = api.ask(
                    question=user_query,
                    mode=mode,
                    top_k=top_k,
                    similarity_threshold=sim_threshold,
                    use_query_rewriter=use_rewriter,
                    document_name=doc_filter
                )

                # ── Response Header ──────────────────────────
                st.markdown("---")
                col_ans, col_meta = st.columns([3, 1])

                with col_meta:
                    conf = res.get("confidence", "unknown").upper()
                    if conf == "HIGH":
                        st.success(f"Confidence: **{conf}**")
                    elif conf == "LOW":
                        st.warning(f"Confidence: **{conf}**")
                    else:
                        st.info(f"Confidence: **{conf}**")

                    st.caption(f"**Source**: `{res.get('source_document')}`")
                    st.caption(f"**Mode**: `{res.get('mode')}`")

                    # Query rewriting indicator
                    rewritten = res.get("rewritten_query")
                    if rewritten and rewritten != user_query:
                        st.info(f"**Rewritten Query:**\n*{rewritten}*")

                with col_ans:
                    st.markdown("### 💬 Answer")
                    st.markdown(res.get("answer", ""))

                # ── Pipeline Trace ───────────────────────────
                steps = res.get("pipeline_steps", [])
                if steps:
                    with st.expander("📍 Pipeline Execution Trace", expanded=False):
                        for step_idx, s in enumerate(steps, 1):
                            st.write(f"**Step {step_idx}:** {s}")

                # ── Retrieved Chunks ─────────────────────────
                chunks = res.get("retrieved_chunks", [])
                st.subheader(f"📑 Retrieved Context Chunks ({len(chunks)})")

                if not chunks:
                    st.info("No chunks retrieved matching this query and confidence threshold.")
                else:
                    for i, chunk in enumerate(chunks, 1):
                        with st.container(border=True):
                            c_top, c_body = st.columns([1, 4])
                            with c_top:
                                st.markdown(f"**Chunk #{i}**")
                                st.caption(f"ID: `{chunk.get('chunk_id')}`")
                                st.metric("Score", f"{chunk.get('score', 0.0):.4f}")
                                if chunk.get("semantic_rank"):
                                    st.caption(f"Semantic Rank: #{chunk.get('semantic_rank')}")
                                if chunk.get("bm25_rank"):
                                    st.caption(f"BM25 Rank: #{chunk.get('bm25_rank')}")
                                if chunk.get("rerank_score"):
                                    st.caption(f"Rerank Score: {chunk.get('rerank_score'):.4f}")
                            with c_body:
                                st.markdown(chunk.get("text", ""))

            except Exception as e:
                st.error(f"Error executing RAG pipeline: {e}")
