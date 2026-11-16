"""
ui/views/config_panel.py

Configuration panel supporting basic user settings (search mode, top-k, LLM provider)
and admin-only advanced settings (feature flags kill-switch, confidence threshold, cache controls).
"""
import importlib
import json
import os
from pathlib import Path
import streamlit as st

import rag.feature_flags
if not hasattr(rag.feature_flags, "save_system_flags") or not hasattr(rag.feature_flags, "get_active_flags"):
    importlib.reload(rag.feature_flags)

try:
    from rag.feature_flags import DEFAULT_FEATURE_FLAGS, get_active_flags, save_system_flags
except ImportError:
    from rag.feature_flags import DEFAULT_FEATURE_FLAGS

    _CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "system_config.json"

    def get_active_flags() -> dict:
        flags = dict(DEFAULT_FEATURE_FLAGS)
        if _CONFIG_PATH.exists():
            try:
                with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if "flags" in saved and isinstance(saved["flags"], dict):
                        flags.update(saved["flags"])
            except Exception:
                pass
        return flags

    def save_system_flags(flags: dict, user_config: any = None) -> None:
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if _CONFIG_PATH.exists():
            try:
                with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["flags"] = flags
        if user_config:
            data["config"] = user_config
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

from ui.components import get_current_config


def render_config_panel():
    st.subheader("⚙️ System & Workspace Configuration")
    st.caption("Customize search behavior, retrieval parameters, LLM model choice, and platform feature flags.")

    cfg = get_current_config()
    is_admin = st.session_state.get("user", {}).get("role") == "admin"

    with st.form("config_form"):
        st.markdown("#### 🔍 Retrieval & Model Settings")
        c1, c2 = st.columns(2)

        with c1:
            search_mode = st.selectbox(
                "Default Search Mode",
                options=["hybrid", "semantic", "reranked"],
                index=["hybrid", "semantic", "reranked"].index(cfg.get("search_mode", "hybrid")),
                help="Hybrid combines BM25 keyword matching and dense vector search via Reciprocal Rank Fusion (RRF).",
            )
            top_k = st.slider(
                "Top-K Retrieved Chunks",
                min_value=1,
                max_value=10,
                value=cfg.get("top_k", 5),
                help="Number of document chunks passed to the LLM context window.",
            )

        with c2:
            llm_provider = st.selectbox(
                "LLM Provider",
                options=["groq", "ollama"],
                index=0 if cfg.get("llm_provider", "groq") == "groq" else 1,
                help="Groq provides fast cloud inference (~1.5s). Ollama runs locally on your machine.",
            )
            groq_model = st.selectbox(
                "Model",
                options=["openai/gpt-oss-20b", "llama3.2", "qwen/qwen3.8-27b"],
                index=0,
                help="Active model for answer synthesis and tool calling.",
            )

        # ── Admin Only Advanced Controls ─────────────────────────
        if is_admin:
            st.markdown("---")
            st.markdown("#### 🛡️ Admin Advanced Controls")

            a1, a2 = st.columns(2)
            with a1:
                conf_thresh = st.slider(
                    "Hallucination Guard Confidence Threshold",
                    min_value=0.0,
                    max_value=1.0,
                    value=cfg.get("confidence_threshold", 0.45),
                    step=0.05,
                    help="Queries whose top retrieved score is below this threshold automatically return 'I don't have enough context'.",
                )
                use_rewriter = st.toggle("Query Rewriting Expansion", value=cfg.get("use_query_rewriter", True))
            with a2:
                use_reranker = st.toggle("Cross-Encoder Re-Ranking", value=cfg.get("use_reranker", True))
                use_cache = st.toggle("Semantic Query Cache", value=cfg.get("use_cache", True))

            st.markdown("---")
            st.markdown("#### 🚩 Enterprise Feature Flags (Kill-Switch)")
            st.caption("Control visibility of capability tabs, agent triage, and observability modules across the workspace.")

            current_flags = get_active_flags()
            if "flags" in st.session_state:
                current_flags.update(st.session_state["flags"])
            st.session_state["flags"] = current_flags

            flag_cols = st.columns(3)
            updated_flags = {}

            keys = list(DEFAULT_FEATURE_FLAGS.keys())
            for idx, key in enumerate(keys):
                col = flag_cols[idx % 3]
                with col:
                    label = key.replace("show_", "").replace("_", " ").title()
                    updated_flags[key] = st.checkbox(label, value=current_flags.get(key, False), key=f"ff_{key}")

        submitted = st.form_submit_button("Save Configuration", type="primary", use_container_width=True)

        if submitted:
            cfg["search_mode"] = search_mode
            cfg["top_k"] = top_k
            cfg["llm_provider"] = llm_provider
            cfg["groq_model"] = groq_model
            os.environ["LLM_PROVIDER"] = llm_provider

            if is_admin:
                cfg["confidence_threshold"] = conf_thresh
                cfg["use_query_rewriter"] = use_rewriter
                cfg["use_reranker"] = use_reranker
                cfg["use_cache"] = use_cache
                st.session_state["flags"] = updated_flags
                save_system_flags(updated_flags, user_config=cfg)
                st.session_state["user_config"] = cfg
                st.success("✓ Workspace configuration and feature flags saved for all users!")
            else:
                st.session_state["user_config"] = cfg
                st.success("✓ Preferences updated for current session!")
            st.rerun()


render_config_panel()
