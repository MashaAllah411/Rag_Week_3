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
from rag.storage.chat_store import list_chats, load_chat, delete_chat, create_new_chat, save_chat

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
    # Hide sidebar completely for unauthenticated users
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)
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


# ── Global Sidebar CSS: Professional ChatGPT-like appearance ─
with st.sidebar:
    st.markdown(
        """
        <style>
        /* ─── SIDEBAR GLOBAL ─────────────────────────────── */
        section[data-testid="stSidebar"] {
            background: var(--secondary-background-color, #f7f7f8) !important;
        }
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem !important;
        }

        /* ─── HIDE "Workspace" nav group label ───────────── */
        section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] > ul > li > div > span {
            font-size: 0.7rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
            color: #94a3b8 !important;
            font-weight: 600 !important;
        }

        /* ─── Nav links styling ──────────────────────────── */
        section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] a {
            font-size: 0.88rem !important;
            padding: 6px 12px !important;
            border-radius: 8px !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] a:hover {
            background: rgba(128, 128, 128, 0.08) !important;
        }

        /* ─── ALL sidebar buttons: strip borders ────────── */
        section[data-testid="stSidebar"] button[kind="secondary"],
        section[data-testid="stSidebar"] button[kind="tertiary"] {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }

        /* ─── Recents row: flat, single-line ─────────────── */
        section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
            align-items: center !important;
            gap: 0px !important;
            margin-bottom: 1px !important;
            padding: 0 !important;
        }

        /* ─── Chat title buttons ─────────────────────────── */
        section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
            text-align: left !important;
            justify-content: flex-start !important;
            padding: 7px 10px !important;
            font-size: 0.85rem !important;
            font-weight: 400 !important;
            border-radius: 8px !important;
            color: inherit !important;
            line-height: 1.3 !important;
            min-height: unset !important;
            height: auto !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"]:hover {
            background-color: rgba(128, 128, 128, 0.07) !important;
            border-radius: 8px !important;
        }

        /* ─── Popover trigger (⋯ button) ────────────────── */
        section[data-testid="stSidebar"] div[data-testid="stPopover"] > div:first-child > button {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            padding: 4px 8px !important;
            color: #94a3b8 !important;
            font-size: 1.1rem !important;
            font-weight: 700 !important;
            border-radius: 6px !important;
            min-height: unset !important;
            height: auto !important;
            width: auto !important;
            min-width: unset !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stPopover"] > div:first-child > button:hover {
            color: inherit !important;
            background-color: rgba(128, 128, 128, 0.12) !important;
        }

        /* ─── HIDE only the dropdown chevron SVG, keep the ⋯ text ── */
        section[data-testid="stSidebar"] div[data-testid="stPopover"] > div:first-child > button svg {
            display: none !important;
        }

        /* ─── New Chat primary button ────────────────────── */
        section[data-testid="stSidebar"] button[kind="primary"] {
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-size: 0.88rem !important;
            padding: 8px 16px !important;
        }

        /* ─── Profile container ──────────────────────────── */
        section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"]:last-of-type {
            border: 1px solid rgba(128, 128, 128, 0.12) !important;
            border-radius: 10px !important;
            background: var(--background-color, #fff) !important;
        }

        /* ─── Popover content panel ──────────────────────── */
        div[data-testid="stPopoverBody"] {
            padding: 4px !important;
            min-width: 140px !important;
        }
        div[data-testid="stPopoverBody"] button {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            text-align: left !important;
            justify-content: flex-start !important;
            padding: 8px 12px !important;
            font-size: 0.85rem !important;
            border-radius: 6px !important;
            width: 100% !important;
        }
        div[data-testid="stPopoverBody"] button:hover {
            background: rgba(128, 128, 128, 0.08) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Brand ────────────────────────────────────────────────
    st.markdown(
        """
        <div style="padding: 4px 0 12px 0;">
            <div style="font-size: 1.1rem; font-weight: 700; letter-spacing: -0.02em;">
                🤖 DocChat Pro
            </div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 2px;">
                Enterprise RAG & Policy Intelligence
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # + New Chat
    if st.button("＋  New Chat", use_container_width=True, type="primary"):
        new_id = create_new_chat(username, "New Conversation")
        st.session_state["current_chat_id"] = new_id
        st.session_state["messages"] = []
        st.session_state["current_chat_title"] = "New Conversation"
        st.rerun()

    # ── Recents ──────────────────────────────────────────────
    st.markdown(
        '<div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; '
        'color: #94a3b8; font-weight: 600; margin: 16px 0 6px 4px;">Recents</div>',
        unsafe_allow_html=True,
    )

    past_chats = list_chats(username)
    if past_chats:
        for c in past_chats[:10]:
            cid = c.get("chat_id")
            ctitle = c.get("title", "Conversation")
            is_active = st.session_state.get("current_chat_id") == cid

            c_col, d_col = st.columns([6, 1])
            with c_col:
                label = ctitle[:28]
                if is_active:
                    label = f"▸ {label}"
                if st.button(label, key=f"cs_{cid}", use_container_width=True):
                    saved_chat = load_chat(username, cid)
                    if saved_chat:
                        st.session_state["current_chat_id"] = cid
                        st.session_state["messages"] = saved_chat.get("messages", [])
                        st.session_state["current_chat_title"] = saved_chat.get("title", "Conversation")
                        st.rerun()
            with d_col:
                with st.popover("⋯"):
                    if st.button("✏️ Rename", key=f"ren_{cid}", use_container_width=True):
                        st.session_state[f"renaming_{cid}"] = True
                    if st.button("🗑️ Delete", key=f"del_{cid}", use_container_width=True):
                        delete_chat(username, cid)
                        if st.session_state.get("current_chat_id") == cid:
                            st.session_state["current_chat_id"] = None
                            st.session_state["messages"] = []
                            st.session_state["current_chat_title"] = ""
                        st.rerun()

            # Inline rename field (appears below the row when triggered)
            if st.session_state.get(f"renaming_{cid}", False):
                new_title = st.text_input(
                    "New title", value=ctitle, key=f"ren_input_{cid}",
                    label_visibility="collapsed",
                )
                r1, r2 = st.columns(2)
                with r1:
                    if st.button("Save", key=f"save_ren_{cid}", use_container_width=True, type="primary"):
                        if new_title.strip():
                            saved = load_chat(username, cid)
                            msgs = saved.get("messages", []) if saved else []
                            save_chat(username, cid, new_title.strip(), msgs)
                            if st.session_state.get("current_chat_id") == cid:
                                st.session_state["current_chat_title"] = new_title.strip()
                            st.session_state[f"renaming_{cid}"] = False
                            st.rerun()
                with r2:
                    if st.button("Cancel", key=f"cancel_ren_{cid}", use_container_width=True):
                        st.session_state[f"renaming_{cid}"] = False
                        st.rerun()
    else:
        st.markdown(
            '<div style="font-size: 0.82rem; color: #94a3b8; padding: 4px 0 0 4px;">No conversations yet</div>',
            unsafe_allow_html=True,
        )

    # ── Spacer pushes profile to bottom ──────────────────────
    st.markdown('<div style="flex: 1; min-height: 30px;"></div>', unsafe_allow_html=True)

    # ── Backend status ───────────────────────────────────────
    online = _backend_online()
    status_color = "#22c55e" if online else "#ef4444"
    status_text = "Online" if online else "Offline"
    st.markdown(
        f'<div style="display: flex; align-items: center; gap: 6px; padding: 4px 4px 8px 4px;">'
        f'<div style="width: 7px; height: 7px; border-radius: 50%; background: {status_color};"></div>'
        f'<span style="font-size: 0.78rem; color: #94a3b8;">Backend {status_text}</span></div>',
        unsafe_allow_html=True,
    )

    # ── User Profile & Sign Out ──────────────────────────────
    with st.container(border=True):
        p_col1, p_col2 = st.columns([4, 1])
        with p_col1:
            avatar_color = current_user.get("avatar_color", "#6366f1")
            initials = current_user.get("avatar_initials", "U")
            display_name = current_user.get("display_name", "User")
            role = current_user.get("role", "user")
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 10px; padding: 2px 0;">
                    <div style="background: {avatar_color}; color: white; border-radius: 50%;
                         width: 32px; height: 32px; display: flex; align-items: center;
                         justify-content: center; font-weight: 600; font-size: 0.8rem;
                         flex-shrink: 0;">{initials}</div>
                    <div>
                        <div style="font-weight: 600; font-size: 0.85rem; line-height: 1.2;">{display_name}</div>
                        <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;
                             letter-spacing: 0.04em;">{role}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with p_col2:
            with st.popover("⋯"):
                if st.button("🚪 Sign Out", key="sign_out_btn", use_container_width=True):
                    st.session_state["authenticated"] = False
                    st.session_state["user"] = None
                    st.session_state["current_chat_id"] = None
                    st.session_state["messages"] = []
                    st.rerun()


navigation = st.navigation(PAGES, expanded=True)
persist_theme_across_pages(page.url_path for group in PAGES.values() for page in group)
navigation.run()
