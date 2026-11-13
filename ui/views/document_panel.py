"""
ui/views/document_panel.py

Modern document management panel.
Handles multi-document upload, indexing status, chunk preview, and document deletion.
"""
import streamlit as st
from ui.api_client import api
from ui.components import call, info_card, page_header, pill


def render_document_panel():
    st.markdown(
        """
        <style>
        /* Document card styling */
        .doc-card {
            border-radius: 12px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="font-size: 1.3rem; font-weight: 600; margin-bottom: 4px;">📂 Document Management</div>',
        unsafe_allow_html=True,
    )
    st.caption("Upload, inspect, and manage enterprise policy & claims documents indexed in ChromaDB.")

    st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2.5, 1])

    with col1:
        with st.container(border=True):
            st.markdown("**Upload New Documents**")
            uploaded_files = st.file_uploader(
                "Upload PDF policy manuals, annexes, or claim forms",
                type=["pdf"],
                accept_multiple_files=True,
                help="Uploaded files will be parsed via PyPDF/Tesseract, chunked, and embedded into ChromaDB.",
                label_visibility="collapsed",
            )
            if uploaded_files:
                if st.button(f"🚀 Index {len(uploaded_files)} File(s)", type="primary"):
                    progress_bar = st.progress(0)
                    for i, uf in enumerate(uploaded_files):
                        file_bytes = uf.read()
                        with st.spinner(f"Ingesting & indexing {uf.name}..."):
                            ok, res = call(api.upload_document, file_bytes, uf.name)
                            if ok:
                                st.success(f"✓ Indexed {uf.name}")
                            else:
                                st.error(f"Failed to index {uf.name}")
                        progress_bar.progress((i + 1) / len(uploaded_files))
                    st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("**Vector Store Sync**")
            st.caption("Trigger full re-indexing of all documents in the corpus.")
            if st.button("🔄 Reindex All", use_container_width=True):
                with st.spinner("Re-indexing complete repository documents..."):
                    ok, res = call(api.reindex_documents)
                    if ok:
                        st.success(f"Re-indexed {res.get('indexed_chunks', 0)} chunks!")
                        st.rerun()
                    else:
                        st.error("Reindex failed.")

    # ── Indexed Documents ─────────────────────────────────────
    st.markdown(
        '<div style="border-top: 1px solid rgba(128,128,128,0.12); margin: 20px 0 16px 0;"></div>',
        unsafe_allow_html=True,
    )
    st.markdown("**Currently Indexed Documents**")

    ok, doc_data = call(api.list_documents)
    docs = doc_data.get("documents", []) if (ok and doc_data) else []

    if not docs:
        st.info("No documents are currently indexed in ChromaDB. Upload one above to begin.")
        return

    for doc in docs:
        fname = doc.get("filename", "Unknown")
        chunks = doc.get("chunks", 0)
        pages = doc.get("pages", 0)
        size_kb = doc.get("size_kb") or round(doc.get("size_bytes", 0) / 1024, 1)

        with st.container(border=True):
            c_info, c_actions = st.columns([4, 1.5])
            with c_info:
                st.markdown(f"**📄 {fname}**")
                # Show meaningful info even if API returns 0
                parts = []
                if chunks:
                    parts.append(f"{chunks} chunks")
                if pages:
                    parts.append(f"{pages} pages")
                if size_kb:
                    parts.append(f"{size_kb} KB")
                st.caption(" · ".join(parts) if parts else "Indexed")

            with c_actions:
                a1, a2 = st.columns(2)
                with a1:
                    if st.button("🔍", key=f"prev_{fname}", help="Preview chunks"):
                        st.session_state[f"preview_{fname}"] = not st.session_state.get(f"preview_{fname}", False)
                with a2:
                    if st.button("🗑️", key=f"del_{fname}", help="Delete document"):
                        with st.spinner(f"Deleting {fname}..."):
                            ok_del, _ = call(api.delete_document, fname)
                            if ok_del:
                                st.success(f"Deleted {fname}")
                                st.rerun()
                            else:
                                st.error(f"Could not delete {fname}")

            if st.session_state.get(f"preview_{fname}", False):
                with st.spinner("Loading chunk preview..."):
                    ok_chk, chk_res = call(api.inspect_document_chunks, fname)
                    sample_chunks = chk_res.get("sample_chunks") or chk_res.get("chunks", []) if (ok_chk and chk_res) else []
                    total_chunks = chk_res.get("total_chunks", len(sample_chunks)) if (ok_chk and chk_res) else chunks

                    if sample_chunks:
                        st.markdown(f"**Chunk Preview** — {total_chunks} total chunks indexed")
                        for idx, chunk in enumerate(sample_chunks[:4]):
                            c_text = chunk.get("preview") or chunk.get("text", "")
                            c_len = chunk.get("length", len(c_text))
                            st.text_area(
                                f"Chunk #{idx+1} ({c_len} chars)",
                                c_text,
                                height=100,
                                key=f"txt_{fname}_{idx}",
                                disabled=True,
                            )
                    else:
                        st.caption("No chunk preview data available from the backend.")


render_document_panel()
