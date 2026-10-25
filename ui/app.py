"""
ui/app.py

Navigation router for the Streamlit UI. Every capability lives on its own page under
ui/views/, grouped in the sidebar by what you are trying to do. Pages talk to the
FastAPI backend only through ui/api_client.py.

Run the whole stack with:  python run.py
"""
import streamlit as st

from ui.api_client import api
from ui.components import apply_theme, persist_theme_across_pages, pill

st.set_page_config(
    page_title="Insurance Policy & Claims RAG Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

PAGES = {
    "Start": [
        st.Page("views/home.py", title="Home", icon="🏠", default=True),
        st.Page("views/documentation.py", title="Documentation", icon="📖", url_path="documentation"),
    ],
    "Learn & Guardrails": [
        st.Page("views/foundations.py", title="Foundations Lab", icon="🧪", url_path="foundations"),
        st.Page("views/guardrails.py", title="Guardrails & Security", icon="🛡️", url_path="guardrails"),
    ],
    "Documents & Answers": [
        st.Page("views/documents.py", title="Documents", icon="📄", url_path="documents"),
        st.Page("views/search_qa.py", title="Search & Q&A", icon="🔍", url_path="search"),
    ],
    "Evaluate": [
        st.Page("views/evaluation.py", title="Evaluation", icon="🎯", url_path="evaluation"),
        st.Page("views/error_analysis.py", title="Error Analysis", icon="🔬", url_path="error-analysis"),
    ],
    "Agents": [
        st.Page("views/agent_triage.py", title="Agent Triage", icon="🤖", url_path="agent-triage"),
        st.Page("views/mcp.py", title="MCP Ecosystem", icon="🔌", url_path="mcp"),
        st.Page("views/multi_agent.py", title="Multi-Agent Squad", icon="👥", url_path="multi-agent"),
    ],
    "Production": [
        st.Page("views/observability.py", title="Observability", icon="📊", url_path="observability"),
    ],
    "Capstone": [
        st.Page("views/capstone.py", title="Capstone", icon="🏁", url_path="capstone"),
    ],
    "System": [
        st.Page("views/system.py", title="System & Health", icon="⚙️", url_path="system"),
    ],
}

navigation = st.navigation(PAGES, expanded=True)   # show every page; the default collapses after 10


@st.cache_data(ttl=5, show_spinner=False)
def _backend_online() -> bool:
    try:
        api.get_health()
        return True
    except Exception:
        return False


with st.sidebar:
    st.markdown("### 🛡️ Insurance RAG")
    st.caption("Policy & claims assistant · Weeks 1-12")
    online = _backend_online()
    st.markdown(pill("Backend online", "ok") if online else pill("Backend offline", "bad"), unsafe_allow_html=True)
    if not online:
        st.caption("Start everything with `python run.py`.")

persist_theme_across_pages(page.url_path for group in PAGES.values() for page in group)

navigation.run()
