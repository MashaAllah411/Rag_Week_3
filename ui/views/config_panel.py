"""
ui/views/config_panel.py

Configuration panel supporting basic user settings (search mode, top-k, LLM provider)
and admin-only advanced settings (feature flags kill-switch, confidence threshold, cache controls).
"""
import os
import streamlit as st
from rag.feature_flags import DEFAULT_FEATURE_FLAGS


def get_current_config() -> dict:
    if "user_config" not in st.session_state:
        st.session_state["user_config"] = {
            "search_mode": "hybrid",
            "top_k": 5,
            "llm_provider": os.getenv("LLM_PROVIDER", "groq"),
            "groq_model": os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", "0.45")),
            "use_query_rewriter": True,
            "use_reranker": True,
            "use_cache": True,
        }
    return st.session_state["user_config"]


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
            st.caption("Control visibility of legacy test suites, triage tabs, and observability modules in the UI.")

            if "flags" not in st.session_state:
                st.session_state["flags"] = dict(DEFAULT_FEATURE_FLAGS)

            flag_cols = st.columns(3)
            current_flags = st.session_state["flags"]
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

            st.session_state["user_config"] = cfg
            st.success("✓ Configuration and feature flags saved successfully!")
            st.rerun()


render_config_panel()
