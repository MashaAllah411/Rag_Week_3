"""
ui/views/chat_main.py

Production ChatGPT-style conversation workspace.
Features:
- "Where should we begin?" empty state with suggestion rows
- Live step-by-step thinking indicator
- Citations accordion with chunk scores and source document references
- Context token gauge
- Session persistence via chat_store
"""
import time
import streamlit as st
from ui.api_client import api
from ui.components import call, pill
from rag.storage.chat_store import load_chat, save_chat, create_new_chat
from ui.views.config_panel import get_current_config


def _approx_tokens(text: str) -> int:
    return max(1, len(text or "") // 4)


def render_chat_interface():
    user = st.session_state.get("user", {})
    username = user.get("username", "demo")
    cfg = get_current_config()

    # Active conversation session
    if "current_chat_id" not in st.session_state or not st.session_state["current_chat_id"]:
        st.session_state["current_chat_id"] = create_new_chat(username, "New Conversation")
        st.session_state["messages"] = []

    chat_id = st.session_state["current_chat_id"]

    # Load messages if not loaded
    if "messages" not in st.session_state:
        saved = load_chat(username, chat_id)
        st.session_state["messages"] = saved.get("messages", []) if saved else []

    messages = st.session_state["messages"]

    # ── Global ChatGPT-style input styling ───────────────────
    st.markdown(
        """
        <style>
        /* Pill-shaped chat input */
        [data-testid="stChatInput"] {
            border-radius: 24px !important;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04) !important;
            padding: 2px 8px !important;
            max-width: 820px !important;
            margin: 0 auto !important;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: rgba(37, 99, 235, 0.4) !important;
            box-shadow: 0 2px 16px rgba(37, 99, 235, 0.08) !important;
        }
        [data-testid="stChatInputSubmitButton"] {
            border-radius: 50% !important;
            background-color: #2563eb !important;
            color: white !important;
        }
        [data-testid="stChatInputSubmitButton"]:hover {
            background-color: #1d4ed8 !important;
        }

        /* Hero form styling for landing page */
        div[data-testid="stForm"] {
            border-radius: 28px !important;
            border: 1px solid rgba(128, 128, 128, 0.18) !important;
            box-shadow: 0 2px 20px -2px rgba(0, 0, 0, 0.06) !important;
            padding: 2px 8px !important;
            background: var(--secondary-background-color, #ffffff) !important;
            max-width: 680px !important;
            margin: 0 auto !important;
        }
        div[data-testid="stForm"] div[data-testid="stTextInput"] input {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            font-size: 0.95rem !important;
            padding: 8px 4px !important;
        }
        div[data-testid="stForm"] div[data-testid="stTextInput"] input:focus {
            box-shadow: none !important;
        }
        div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
            border-radius: 50% !important;
            width: 34px !important;
            height: 34px !important;
            min-height: 34px !important;
            padding: 0 !important;
            font-size: 1.1rem !important;
            background-color: #2563eb !important;
            color: white !important;
            border: none !important;
        }
        div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
            background-color: #1d4ed8 !important;
        }

        /* Suggestion rows – clean, borderless */
        .suggestion-row {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 14px;
            border-radius: 10px;
            cursor: pointer;
            transition: background 0.15s ease;
            font-size: 0.9rem;
            color: inherit;
            max-width: 680px;
            margin: 0 auto;
        }
        .suggestion-row:hover {
            background: rgba(128, 128, 128, 0.06);
        }
        .suggestion-icon {
            font-size: 1rem;
            opacity: 0.5;
            flex-shrink: 0;
        }
        .suggestion-text {
            opacity: 0.7;
        }

        /* Chat message styling */
        [data-testid="stChatMessage"] {
            max-width: 820px !important;
            margin: 0 auto !important;
        }

        /* Context indicator */
        .ctx-indicator {
            text-align: right;
            padding: 4px 0;
        }
        .ctx-label {
            font-size: 0.75rem;
            font-weight: 500;
            color: #94a3b8;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Empty State: Greeting & Hero Search Bar ──────────────
    if not messages:
        # Hide bottom pinned chat input on landing
        st.markdown(
            """
            <style>
            [data-testid="stChatInput"] { display: none !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Centered greeting
        st.markdown(
            """
            <div style="text-align: center; margin: 10vh auto 28px auto; max-width: 680px;">
                <h1 style="font-size: 2rem; font-weight: 600; margin-bottom: 0;
                    letter-spacing: -0.02em; color: inherit;">
                    Where should we begin?
                </h1>
                <p style="font-size: 0.88rem; color: #94a3b8; margin-top: 8px;">
                    Ask questions across your policy documents, claims rules, or employee guidelines.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Hero input bar
        _, center_col, _ = st.columns([1.2, 4, 1.2])
        with center_col:
            with st.form("hero_chat_form", clear_on_submit=True):
                col_input, col_btn = st.columns([8, 1])
                with col_input:
                    hero_query = st.text_input(
                        "Ask DocChat Pro...",
                        label_visibility="collapsed",
                        placeholder="Ask anything about your documents...",
                    )
                with col_btn:
                    hero_submit = st.form_submit_button("↑", type="primary")

                if hero_submit and hero_query.strip():
                    st.session_state["pending_prompt"] = hero_query.strip()
                    st.rerun()

        # Suggestion rows (clean, icon + text, no borders)
        st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

        suggestions = [
            ("📄", "What is the schedule of depreciation for fixing IDV?"),
            ("🏖️", "What is my annual leave entitlement under the policy?"),
            ("🛡️", "What are the exclusions under Section 1 Own Damage?"),
            ("📋", "How do I escalate a discretionary approval to an HRBP?"),
        ]

        _, sug_col, _ = st.columns([1.2, 4, 1.2])
        with sug_col:
            for icon, text in suggestions:
                if st.button(
                    f"{icon}  {text}",
                    key=f"sug_{text[:12]}",
                    use_container_width=True,
                ):
                    st.session_state["pending_prompt"] = text
                    st.rerun()

        # Style suggestion buttons to look like flat rows
        st.markdown(
            """
            <style>
            /* Target suggestion buttons specifically */
            div[data-testid="stVerticalBlock"] button[kind="secondary"] {
                border: none !important;
                background: transparent !important;
                box-shadow: none !important;
                text-align: left !important;
                justify-content: flex-start !important;
                padding: 10px 14px !important;
                font-size: 0.88rem !important;
                font-weight: 400 !important;
                border-radius: 10px !important;
                color: #64748b !important;
            }
            div[data-testid="stVerticalBlock"] button[kind="secondary"]:hover {
                background: rgba(128, 128, 128, 0.06) !important;
                color: inherit !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        return  # Don't render chat input or history on landing

    # ── Active Conversation Header ───────────────────────────
    total_tokens = sum(_approx_tokens(m.get("content", "")) for m in messages)
    context_limit = 4096
    pct = min(100, int((total_tokens / context_limit) * 100))

    h_col1, h_col2 = st.columns([5, 1])
    with h_col1:
        active_title = st.session_state.get("current_chat_title", "Conversation")
        st.markdown(
            f'<div style="font-size: 1.05rem; font-weight: 600; padding: 6px 0;">{active_title}</div>',
            unsafe_allow_html=True,
        )
    with h_col2:
        tone = "bad" if pct > 85 else ("warn" if pct > 60 else "ok")
        st.markdown(
            f'<div class="ctx-indicator"><span class="ctx-label">'
            f'{total_tokens:,} / {context_limit:,} toks</span> {pill(f"{pct}%", tone)}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="border-top: 1px solid rgba(128,128,128,0.12); margin: 4px 0 16px 0;"></div>',
                unsafe_allow_html=True)

    # ── Message History ──────────────────────────────────────
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        with st.chat_message(role, avatar="🧑‍💻" if role == "user" else "🤖"):
            st.markdown(content)

            # Sources / Citations
            sources = msg.get("sources", [])
            if sources:
                with st.expander(f"📄 Cited Sources ({len(sources)} chunks)", expanded=False):
                    for idx, src in enumerate(sources):
                        score = src.get("score", 0.0)
                        cid = src.get("id", f"chunk_{idx}")
                        st.markdown(f"**Chunk `{cid}`** — Relevance: `{score:.4f}`")
                        st.caption(src.get("text", "")[:400] + "...")

            # Metadata footer
            if role == "assistant" and "latency" in msg:
                lat = msg.get("latency", 0.0)
                prov = msg.get("provider", "LLM")
                st.caption(f"⏱️ {lat:.2f}s · 🧠 {prov} · Mode: {msg.get('mode', 'hybrid')}")

    # ── Chat Input & Action Pipeline ─────────────────────────
    pending = st.session_state.pop("pending_prompt", None)
    user_input = st.chat_input("Ask anything about your documents...") or pending

    if user_input:
        # Display user message immediately
        messages.append({"role": "user", "content": user_input, "timestamp": time.time()})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)

        # Update chat title if it's the first message
        if len(messages) == 1:
            st.session_state["current_chat_title"] = user_input[:40]

        # Assistant generation with thinking steps
        with st.chat_message("assistant", avatar="🤖"):
            with st.status("Thinking and searching policy corpus...", expanded=True) as status:
                st.write("🔍 Planning query analysis & checking safety scope...")
                time.sleep(0.1)

                st.write(f"⚙️ Running {cfg.get('search_mode', 'hybrid').title()} search (top_k={cfg.get('top_k', 5)})...")
                t0 = time.time()

                ok, resp = call(
                    api.ask,
                    question=user_input,
                    mode=cfg.get("search_mode", "hybrid"),
                    top_k=cfg.get("top_k", 5),
                    use_query_rewriter=cfg.get("use_query_rewriter", True),
                    similarity_threshold=cfg.get("confidence_threshold", 0.45),
                )
                elapsed = time.time() - t0

                if ok and resp:
                    psteps = resp.get("pipeline_steps", [])
                    for step in psteps:
                        st.write(f"✓ {step}")
                    status.update(label=f"Answer ready in {elapsed:.2f}s", state="complete", expanded=False)
                    answer_text = resp.get("answer", "No response returned.")
                    sources = resp.get("retrieved_chunks", [])
                else:
                    status.update(label="Retrieval failed", state="error", expanded=True)
                    answer_text = "I encountered an error retrieving or generating the response. Please check backend connection."
                    sources = []

            st.markdown(answer_text)

            if sources:
                with st.expander(f"📄 Cited Sources ({len(sources)} chunks)", expanded=False):
                    for idx, src in enumerate(sources):
                        score = src.get("score", 0.0)
                        cid = src.get("id", f"chunk_{idx}")
                        st.markdown(f"**Chunk `{cid}`** — Relevance: `{score:.4f}`")
                        st.caption(src.get("text", "")[:400] + "...")

            assistant_msg = {
                "role": "assistant",
                "content": answer_text,
                "sources": sources,
                "latency": elapsed,
                "provider": cfg.get("llm_provider", "groq").upper(),
                "mode": cfg.get("search_mode", "hybrid"),
                "timestamp": time.time(),
            }
            messages.append(assistant_msg)

            # Persist chat
            title = st.session_state.get("current_chat_title", user_input[:40])
            save_chat(username, chat_id, title, messages)

        st.rerun()


render_chat_interface()
