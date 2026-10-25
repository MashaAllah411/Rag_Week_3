"""
ui/views/system.py

System & Health (Weeks 3, 11): proves which open-source tools are live, exercises them with a
real self-test, shows indexing state, masked configuration and logs.
"""
import html

import streamlit as st

from ui.api_client import api
from ui.components import call, info_card, kv_table, page_header, pill, status_pill

page_header(
    "System & Health",
    "⚙️",
    "Which tools are actually running, a self-test that exercises each one for real, and the logs.",
    weeks=["3", "11"],
)

ok_status, status = call(api.get_system_status, spinner="Checking system...")
if not ok_status:
    st.stop()

tab_stack, tab_test, tab_index, tab_config, tab_logs = st.tabs(
    ["🧰 Open-source stack", "🧪 Self-test", "🗂️ Indexing", "🔒 Configuration", "📜 Logs"]
)

components = status.get("components", {})
vec = components.get("vector_store", {})
tracing = components.get("tracing", {})
llm = components.get("ollama_llm", {})

# ── Open-source stack ────────────────────────────────────────
with tab_stack:
    st.subheader("Open-source tools in use")
    st.caption("This is live state read from the running backend, not just configuration. "
               "Press the self-test tab to exercise each tool.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Backend", f"v{status.get('backend', {}).get('version', '?')}", delta=f"port {status.get('backend', {}).get('port')}",
              delta_color="off")
    m2.metric("Vector store", (vec.get("backend") or "n/a").title(), delta=f"{vec.get('chunks', 0)} passages",
              delta_color="off")
    m3.metric("Tracing", "OpenTelemetry" if tracing.get("active") else "Off",
              delta=f"{tracing.get('spans_exported', 0)} spans this run", delta_color="off")
    m4.metric("Local LLM", "Reachable" if llm.get("reachable") else "Not running", delta=llm.get("model"), delta_color="off")

    stack = status.get("open_source_stack", [])
    rows = []
    for item in stack:
        rows.append(
            "<tr>"
            f"<td><b>{html.escape(str(item.get('capability')))}</b></td>"
            f"<td>{html.escape(str(item.get('tool')))}</td>"
            f"<td>{html.escape(str(item.get('replaces')))}</td>"
            f"<td>{html.escape(str(item.get('week')))}</td>"
            f"<td>{html.escape(str(item.get('license')))}</td>"
            f"<td>{status_pill(bool(item.get('active')))}</td>"
            f"<td style='opacity:0.72'>{html.escape(str(item.get('detail')))}</td>"
            "</tr>"
        )
    st.markdown(
        "<table style='width:100%; border-collapse:collapse; font-size:0.9rem'>"
        "<thead><tr style='text-align:left; border-bottom:2px solid rgba(128,128,128,0.45)'>"
        "<th>Capability</th><th>Tool</th><th>Replaces</th><th>Week</th><th>Licence</th><th>Active</th><th>Detail</th>"
        "</tr></thead><tbody>" + "".join(
            r.replace("<tr>", "<tr style='border-bottom:1px solid rgba(128,128,128,0.2)'>") for r in rows) + "</tbody></table>",
        unsafe_allow_html=True,
    )

    inactive = [i["capability"] for i in stack if not i.get("active")]
    if inactive:
        st.markdown("")
        info_card(f"<b>Not active right now:</b> {', '.join(inactive)}. See the Detail column for how to fix each.", "warn")

    exporters = tracing.get("exporters", [])
    if exporters:
        st.markdown("##### Tracing exporters")
        for e in exporters:
            st.markdown(f"- {pill(e.get('type', ''), 'ok')} `{e.get('path') or e.get('endpoint')}`", unsafe_allow_html=True)

# ── Self-test ────────────────────────────────────────────────
with tab_test:
    st.subheader("Self-test")
    st.caption("Each check does real work: writes, queries and deletes vectors in ChromaDB, exports an OpenTelemetry span, "
               "reads rendered text with OCR, and embeds a sentence.")
    deep = st.checkbox("Include reranker (downloads the model the first time)", value=False)
    if st.button("▶ Run self-test", type="primary"):
        ok_t, res = call(api.run_selftest, deep, spinner="Exercising each tool (the first run loads models)...")
        if ok_t:
            st.session_state["selftest_result"] = res

    result = st.session_state.get("selftest_result")
    if result:
        passed, total = result.get("passed", 0), result.get("total", 0)
        (st.success if passed == total else st.warning)(f"{passed} of {total} checks passed")
        for c in result.get("checks", []):
            with st.container(border=True):
                a, b, d = st.columns([4, 1, 1])
                a.markdown(f"**{c.get('check')}**")
                b.markdown(status_pill(bool(c.get("ok")), "Pass", "Fail"), unsafe_allow_html=True)
                d.caption(f"{c.get('ms')} ms")
                st.caption(c.get("detail", ""))

# ── Indexing ─────────────────────────────────────────────────
with tab_index:
    st.subheader("Indexing")
    state = status.get("indexing", {})
    i1, i2, i3 = st.columns(3)
    i1.metric("State", str(state.get("state", "idle")).title())
    i2.metric("Passages in vector store", vec.get("chunks", 0))
    i3.metric("Documents finished this run", state.get("documents_done", 0))
    if state.get("current"):
        st.info(f"Working on `{state.get('current')}`")
    if state.get("last_error"):
        st.error(f"Last indexing error: {state.get('last_error')}")
    if vec.get("reachable") and vec.get("chunks", 0) == 0:
        st.warning("The vector store is empty. Re-index to index the PDFs in `resources/`.")
    c1, c2 = st.columns(2)
    if c1.button("🔄 Refresh status"):
        st.rerun()
    if c2.button("⚡ Re-index all documents"):
        ok_r, res = call(api.reindex_documents, spinner="Starting background re-indexing...")
        if ok_r:
            st.success(res.get("message", "Re-indexing started."))
    st.caption(f"Store location: `{vec.get('collection')}` collection. Indexing runs in the background; refresh to follow progress.")

# ── Configuration ────────────────────────────────────────────
with tab_config:
    st.subheader("Configuration")
    st.caption("Settings are read from `.env`. Anything secret-looking is masked and never displayed in full.")
    kv_table(status.get("config_masked", {}))
    storage = status.get("storage", {})
    st.markdown("##### Storage")
    kv_table({"Documents folder": storage.get("resources_dir"), "Data folder": storage.get("data_dir"),
              "PDF files": storage.get("pdf_documents_count")})

# ── Logs ─────────────────────────────────────────────────────
with tab_logs:
    st.subheader("Application logs")
    l1, l2 = st.columns([1, 2])
    with l1:
        n_lines = st.selectbox("Lines per file", [50, 100, 200, 500], index=1)
    with l2:
        needle = st.text_input("Filter (case-insensitive)", placeholder="e.g. ERROR or hybrid")
    ok_l, logs = call(api.get_system_logs, n_lines, spinner="Reading logs...")
    if ok_l:
        files = logs.get("logs", [])
        if not files:
            st.info("No log files yet in `logs/`. They appear when the stack is started with `python run.py`.")
        for lf in files:
            lines = lf.get("lines", [])
            if needle:
                lines = [ln for ln in lines if needle.lower() in ln.lower()]
            with st.expander(f"📄 {lf.get('file')} ({len(lines)} lines)", expanded=True):
                st.code("\n".join(lines) or "No matching lines.", language="text")
