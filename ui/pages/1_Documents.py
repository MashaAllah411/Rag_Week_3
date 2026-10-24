"""
ui/pages/1_Documents.py

Page 1: Document Management & Chunk Inspection
- List indexed documents with metadata
- Upload PDF with progress and background indexing
- Delete document and its Pinecone vectors
- Trigger full re-indexing
- Chunk inspector previewing chunk sizes and boundaries
"""
import streamlit as st
from ui.api_client import api

st.set_page_config(page_title="Document Management — Insurance RAG", page_icon="📄", layout="wide")

st.title("📄 Document Management & Ingestion")
st.markdown("Manage policy documents stored in `resources/`, monitor Pinecone indexing, and inspect chunk boundaries.")

tab_list, tab_upload, tab_inspect = st.tabs(["📚 Document Library", "📤 Upload New Document", "🔍 Chunk Inspector"])

# ── Tab 1: Document Library ──────────────────────────────────
with tab_list:
    st.subheader("Indexed Policy Documents")

    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("🔄 Refresh Library", use_container_width=True):
            st.rerun()

    try:
        data = api.list_documents()
        docs = data.get("documents", [])
        total = data.get("count", 0)

        st.caption(f"Total documents: **{total}** | Vector Index: `{data.get('index_name')}`")

        if not docs:
            st.info("No documents found in `resources/` folder. Upload one using the Upload tab.")
        else:
            for doc in docs:
                with st.expander(f"📑 {doc.get('title')} (`{doc.get('filename')}`)", expanded=True):
                    col_info, col_actions = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"- **Pages**: {doc.get('pages')} | **Size**: {doc.get('size_kb')} KB")
                        st.markdown(f"- **Embedding Model**: `{doc.get('embedding_model')}`")
                        st.markdown(f"- **Chunking**: `{doc.get('chunking_strategy')}`")
                        st.markdown(f"- **Status**: `{doc.get('status')}`")

                        # Suggested questions
                        sq = doc.get("suggested_questions", [])
                        if sq:
                            st.markdown("**Suggested Quick Questions:**")
                            for q in sq:
                                st.caption(f"• *{q.get('label')}*: {q.get('query')}")

                    with col_actions:
                        st.write("**Actions**")
                        del_key = f"del_{doc.get('filename')}"
                        if st.button(f"🗑️ Delete Document", key=del_key, type="secondary"):
                            with st.spinner("Deleting document and Pinecone vectors..."):
                                try:
                                    res = api.delete_document(doc.get("filename"))
                                    st.success(f"Deleted `{res.get('filename')}` successfully.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to delete: {e}")

        st.markdown("---")
        st.subheader("Batch Operations")
        if st.button("⚡ Re-index All Documents in Pinecone & BM25"):
            with st.spinner("Starting background re-indexing..."):
                try:
                    re_res = api.reindex_documents()
                    st.success(f"{re_res.get('message')}")
                except Exception as e:
                    st.error(f"Re-indexing failed: {e}")

    except Exception as exc:
        st.error(f"Failed to load documents from backend: {exc}")

# ── Tab 2: Upload New Document ───────────────────────────────
with tab_upload:
    st.subheader("Upload Policy PDF")
    st.markdown("Upload insurance policy schedules, wordings, or endorsements (max 20 MB).")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        st.info(f"Selected: **{uploaded_file.name}** ({round(len(uploaded_file.getvalue()) / 1024, 1)} KB)")

        if st.button("🚀 Upload & Start Ingestion", type="primary"):
            with st.spinner("Uploading file and initiating background ingestion..."):
                try:
                    res = api.upload_document(uploaded_file.getvalue(), uploaded_file.name)
                    st.success(f"✅ {res.get('message')}")
                    st.info("The document is now being chunked, embedded with sentence-transformers, and upserted to Pinecone.")
                except Exception as e:
                    st.error(f"Upload failed: {e}")

# ── Tab 3: Chunk Inspector ───────────────────────────────────
with tab_inspect:
    st.subheader("Chunk Boundary Inspector")
    st.markdown("Inspect how documents are sliced into chunks (fixed 900 chars with 150 char overlap and sentence boundary preservation).")

    try:
        docs_data = api.list_documents()
        doc_options = [d.get("filename") for d in docs_data.get("documents", [])]

        if doc_options:
            selected_doc = st.selectbox("Select document to inspect", doc_options)

            if st.button("🔍 Inspect Chunks", key="btn_inspect"):
                with st.spinner("Extracting and chunking document..."):
                    inspect_res = api.inspect_document_chunks(selected_doc)
                    st.success(f"Document contains **{inspect_res.get('total_pages')} pages** and was sliced into **{inspect_res.get('total_chunks')} chunks**.")

                    st.markdown("#### Sample Chunks (First 20)")
                    for c in inspect_res.get("sample_chunks", []):
                        with st.container(border=True):
                            st.caption(f"**Chunk #{c.get('chunk_index')}** | Length: {c.get('length')} characters")
                            st.text(c.get("preview"))
        else:
            st.info("No documents available for chunk inspection.")
    except Exception as e:
        st.error(f"Inspector unavailable: {e}")
