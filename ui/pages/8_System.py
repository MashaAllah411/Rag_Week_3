"""
ui/pages/8_System.py

Page 8: System Health, Configuration & Live Logs
- Health status of FastAPI, Ollama, and Pinecone
- Masked environment configuration (secrets never displayed)
- Live log tail viewer for troubleshooting
"""
import streamlit as st
from ui.api_client import api

st.set_page_config(page_title="System & Health — Insurance RAG", page_icon="⚙️", layout="wide")

st.title("⚙️ System Status, Configuration & Logs")
st.markdown("Monitor backend health, inspect configuration with masked credentials, and review application log output.")

tab_status, tab_config, tab_logs = st.tabs(["🟢 Component Health", "🔒 Environment Configuration", "📜 Application Logs"])

# ── Tab 1: Component Health ──────────────────────────────────
with tab_status:
    st.subheader("Subsystem Health & Connections")

    try:
        status_data = api.get_system_status()

        h1, h2, h3, h4 = st.columns(4)
        h1.metric("FastAPI Backend", "ONLINE", delta="v2.0.0")

        ollama_info = status_data.get("components", {}).get("ollama_llm", {})
        h2.metric("Ollama LLM", "REACHABLE" if ollama_info.get("reachable") else "OFFLINE",
                  delta=ollama_info.get("model", "llama3.2"))

        pc_info = status_data.get("components", {}).get("pinecone_vector_db", {})
        h3.metric("Pinecone DB", "CONFIGURED" if pc_info.get("configured") else "NOT CONFIGURED",
                  delta=pc_info.get("index_name"))

        doc_count = status_data.get("storage", {}).get("pdf_documents_count", 0)
        h4.metric("Policy Documents", f"{doc_count} Files", delta="resources/")

        st.markdown("### Component Specifications")
        with st.container(border=True):
            emb_info = status_data.get("components", {}).get("embedding_model", {})
            st.write(f"- **Embedding Model**: `{emb_info.get('name')}` (Vector dimensions: {emb_info.get('dimensions')})")
            rerank_info = status_data.get("components", {}).get("reranker_model", {})
            st.write(f"- **Cross-Encoder Reranker**: `{rerank_info.get('name')}`")
            st.write(f"- **Local Document Storage**: `{status_data.get('storage', {}).get('resources_dir')}`")
            st.write(f"- **Data & Index Directory**: `{status_data.get('storage', {}).get('data_dir')}`")

    except Exception as e:
        st.error(f"Failed to query system status: {e}")

# ── Tab 2: Environment Configuration ─────────────────────────
with tab_config:
    st.subheader("Environment Configuration (Secrets Masked)")
    st.markdown("All credentials and API keys are read strictly from `.env` and masked for security.")

    try:
        status_data = api.get_system_status()
        masked = status_data.get("config_masked", {})
        for k, v in masked.items():
            st.text(f"{k} = {v}")
    except Exception as e:
        st.error(f"Error: {e}")

# ── Tab 3: Application Logs ──────────────────────────────────
with tab_logs:
    st.subheader("Live Application Logs")
    st.markdown("Recent log lines captured from `logs/` directory.")

    num_lines = st.slider("Lines to view", min_value=20, max_value=200, value=50)

    try:
        logs_data = api.get_system_logs(lines=num_lines)
        log_files = logs_data.get("logs", [])

        if not log_files:
            st.info("No log files generated yet in `logs/` directory.")
        else:
            for lf in log_files:
                with st.expander(f"📄 {lf.get('file')}", expanded=True):
                    log_text = "\n".join(lf.get("lines", []))
                    st.code(log_text or "Log is empty.", language="text")
    except Exception as e:
        st.error(f"Failed to fetch logs: {e}")
