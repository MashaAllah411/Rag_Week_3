"""
ui/app.py

Navigation router for DocChat Pro / Insurance RAG Platform.
Provides role-based access control, session-level feature flag evaluation,
and a modern ChatGPT-style workspace for users and admins.

Run the whole stack with:  python run.py
"""
import sys
import os
import threading
import time
import urllib.request
from pathlib import Path
import streamlit as st

# Ensure src and repo root are in sys.path regardless of execution context
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@st.cache_resource(show_spinner=False)
def _ensure_backend_started() -> bool:
    """On Streamlit Cloud or standalone runs, auto-start FastAPI backend in a daemon thread."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=0.8) as resp:
            if resp.status == 200:
                return True
    except Exception:
        pass

    try:
        import uvicorn
        from rag.api.main import app as fastapi_app
        config = uvicorn.Config(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")
        server = uvicorn.Server(config)
        t = threading.Thread(target=server.run, daemon=True)
        t.start()
        time.sleep(1.5)
        return True
    except Exception:
        return False


_ensure_backend_started()

from ui.api_client import api
from ui.components import apply_theme, persist_theme_across_pages, pill
from rag.feature_flags import get_active_flags
from rag.storage.chat_store import list_chats, load_chat, delete_chat, create_new_chat

st.set_page_config(
    page_title="DocChat Pro · Enterprise RAG",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

# ── Session State Initialization ─────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None
if "flags" not in st.session_state:
    st.session_state["flags"] = get_active_flags()


@st.cache_data(ttl=5, show_spinner=False)
def _backend_online() -> bool:
    try:
        api.get_health()
        return True
    except Exception:
        return False


# ── Route: Unauthenticated Users ─────────────────────────────
if not st.session_state.get("authenticated", False):
    PAGES = {
        "Authentication": [
            st.Page("views/login_page.py", title="Sign In", icon="🔐", url_path="login", default=True),
        ]
    }
    navigation = st.navigation(PAGES, expanded=True)
    persist_theme_across_pages(page.url_path for group in PAGES.values() for page in group)
    navigation.run()
    st.stop()


# ── Authenticated Workspace ──────────────────────────────────
current_user = st.session_state.get("user", {})
username = current_user.get("username", "demo")
is_admin = current_user.get("role") == "admin"
flags = st.session_state.get("flags", {})

# ── Primary Workspace Pages ──────────────────────────────────
PAGES = {
    "Workspace": [
        st.Page("views/chat_main.py", title="Chat", icon="💬", url_path="chat", default=True),
        st.Page("views/document_panel.py", title="My Documents", icon="📂", url_path="documents-panel"),
        st.Page("views/config_panel.py", title="Configuration", icon="⚙️", url_path="configuration"),
    ]
}

# ── Admin Legacy Dev Tools (Activated via Feature Flags) ─────
if is_admin:
    legacy_pages = []
    if flags.get("show_foundations_lab_tab"):
        legacy_pages.append(st.Page("views/foundations.py", title="Foundations Lab", icon="🧪", url_path="foundations"))
    if flags.get("show_guardrails_tab"):
        legacy_pages.append(st.Page("views/guardrails.py", title="Guardrails & Security", icon="🛡️", url_path="guardrails"))
    if flags.get("show_advanced_search_modes"):
        legacy_pages.append(st.Page("views/search_qa.py", title="Legacy Search & Q&A", icon="🔍", url_path="search"))
        legacy_pages.append(st.Page("views/documents.py", title="Legacy Documents", icon="📄", url_path="legacy-docs"))
    if flags.get("show_evaluation_tab"):
        legacy_pages.append(st.Page("views/evaluation.py", title="Evaluation", icon="🎯", url_path="evaluation"))
    if flags.get("show_error_analysis_tab"):
        legacy_pages.append(st.Page("views/error_analysis.py", title="Error Analysis", icon="🔬", url_path="error-analysis"))
    if flags.get("show_agent_triage_tab"):
        legacy_pages.append(st.Page("views/agent_triage.py", title="Agent Triage", icon="🤖", url_path="agent-triage"))
    if flags.get("show_mcp_ecosystem_tab"):
        legacy_pages.append(st.Page("views/mcp.py", title="MCP Ecosystem", icon="🔌", url_path="mcp"))
    if flags.get("show_multi_agent_tab"):
        legacy_pages.append(st.Page("views/multi_agent.py", title="Multi-Agent Squad", icon="👥", url_path="multi-agent"))
    if flags.get("show_observability_tab"):
        legacy_pages.append(st.Page("views/observability.py", title="Observability", icon="📊", url_path="observability"))
    if flags.get("show_capstone_tab"):
        legacy_pages.append(st.Page("views/capstone.py", title="Capstone", icon="🏁", url_path="capstone"))
    if flags.get("show_hr_policy_desk_tab"):
        legacy_pages.append(st.Page("views/hr_policy_desk.py", title="HR Policy Desk", icon="🏢", url_path="hr-policy-desk"))

    if legacy_pages:
        legacy_pages.append(st.Page("views/system.py", title="System & Health", icon="🩺", url_path="system"))
        legacy_pages.append(st.Page("views/documentation.py", title="Documentation", icon="📖", url_path="documentation"))
        PAGES["Legacy / Dev Tools"] = legacy_pages


# ── Render Custom Sidebar Elements ───────────────────────────
with st.sidebar:
    st.markdown("### 🤖 DocChat Pro")
    st.caption("Enterprise RAG & Policy Intelligence")

    # + New Chat Action
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        new_id = create_new_chat(username, "New Conversation")
        st.session_state["current_chat_id"] = new_id
        st.session_state["messages"] = []
        st.session_state["current_chat_title"] = "New Conversation"
        st.rerun()

    # Recents History
    st.markdown("##### 🕒 Recents")
    past_chats = list_chats(username)
    if past_chats:
        for c in past_chats[:6]:
            cid = c.get("chat_id")
            ctitle = c.get("title", "Conversation")
            c_col, d_col = st.columns([5, 1])
            with c_col:
                is_active = (st.session_state.get("current_chat_id") == cid)
                btn_label = f"▸ {ctitle}" if is_active else ctitle
                if st.button(btn_label[:28], key=f"chat_sel_{cid}", use_container_width=True):
                    saved_chat = load_chat(username, cid)
                    if saved_chat:
                        st.session_state["current_chat_id"] = cid
                        st.session_state["messages"] = saved_chat.get("messages", [])
                        st.session_state["current_chat_title"] = saved_chat.get("title", "Conversation")
                        st.rerun()
            with d_col:
                if st.button("×", key=f"del_c_{cid}", help="Delete chat"):
                    delete_chat(username, cid)
                    if st.session_state.get("current_chat_id") == cid:
                        st.session_state["current_chat_id"] = None
                        st.session_state["messages"] = []
                    st.rerun()
    else:
        st.caption("No saved conversations yet.")

    st.markdown("---")

    # Backend status badge
    online = _backend_online()
    st.markdown(pill("Backend online", "ok") if online else pill("Backend offline", "bad"), unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # User Profile Pill & Sign Out
    with st.container(border=True):
        u_col1, u_col2 = st.columns([3, 1])
        with u_col1:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="background: {current_user.get('avatar_color', '#6366f1')}; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.75rem;">
                        {current_user.get('avatar_initials', 'U')}
                    </div>
                    <div>
                        <div style="font-weight: 600; font-size: 0.85rem; line-height: 1.1;">{current_user.get('display_name', 'User')}</div>
                        <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">{current_user.get('role', 'user')}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with u_col2:
            if st.button("🚪", help="Sign Out", key="sign_out_btn"):
                st.session_state["authenticated"] = False
                st.session_state["user"] = None
                st.session_state["current_chat_id"] = None
                st.session_state["messages"] = []
                st.rerun()


navigation = st.navigation(PAGES, expanded=True)
persist_theme_across_pages(page.url_path for group in PAGES.values() for page in group)
navigation.run()
