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
from ui.components import call, pill, get_current_config
from rag.storage.chat_store import load_chat, save_chat, create_new_chat


def _approx_tokens(text: str) -> int:
    return max(1, len(text or "") // 4)


def _extract_title_from_messages(messages: list, fallback: str = "New Conversation") -> str:
    """Extract a clean title from the first user message."""
    for m in messages:
        if m.get("role") == "user":
            txt = (m.get("content") or "").strip()
            if txt:
                return txt.split("\n")[0].strip()[:36]
    return fallback


def render_chat_interface():
    user = st.session_state.get("user", {})
    username = user.get("username", "demo")
    cfg = get_current_config()

    chat_id = st.session_state.get("current_chat_id")

    if chat_id:
        if "messages" not in st.session_state:
            saved = load_chat(username, chat_id)
            st.session_state["messages"] = saved.get("messages", []) if saved else []
            if saved and saved.get("title"):
                st.session_state["current_chat_title"] = saved.get("title")
    else:
        if "messages" not in st.session_state:
            st.session_state["messages"] = []

    messages = st.session_state["messages"]

    # Derive chat title if currently default/blank and messages exist
    curr_title = st.session_state.get("current_chat_title", "")
    if not curr_title or curr_title.strip().lower() in ("new conversation", "conversation"):
        derived = _extract_title_from_messages(messages)
        if derived != "New Conversation":
            st.session_state["current_chat_title"] = derived

    # ── If there was a pending prompt submitted from the hero bar or suggestion pills ──
    pending = st.session_state.pop("pending_prompt", None)
    if pending:
        title = pending.strip().split("\n")[0][:36]
        if not chat_id:
            chat_id = create_new_chat(username, title)
            st.session_state["current_chat_id"] = chat_id

        st.session_state["current_chat_title"] = title
        messages.append({"role": "user", "content": pending, "timestamp": time.time()})
        save_chat(username, chat_id, title, messages)
        st.session_state["messages"] = messages

    # ── Global Styling ───────────────────────────────────────
    st.markdown(
        """
        <style>
        /* Pill-shaped chat input — identical styling to landing hero bar */
        [data-testid="stChatInput"] {
            border-radius: 36px !important;
            border: 1px solid rgba(128, 128, 128, 0.22) !important;
            box-shadow: 0 3px 20px -2px rgba(0, 0, 0, 0.06) !important;
            padding: 4px 10px !important;
            max-width: 680px !important;
            margin: 0 auto !important;
            background: var(--secondary-background-color, #ffffff) !important;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: rgba(128, 128, 128, 0.35) !important;
            box-shadow: 0 4px 24px -2px rgba(0, 0, 0, 0.09) !important;
        }

        /* Completely remove inner border, outline, focus ring, and background from chat input textarea */
        [data-testid="stChatInput"] div,
        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInput"] [data-baseweb="base-input"],
        [data-testid="stChatInput"] [data-baseweb="textarea"] {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }
        [data-testid="stChatInput"] textarea {
            font-size: 0.98rem !important;
            padding: 8px 6px !important;
            color: inherit !important;
            resize: none !important;
        }
        [data-testid="stChatInput"] textarea:focus {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }

        /* Submit button matching hero submit button */
        [data-testid="stChatInputSubmitButton"] {
            border-radius: 50% !important;
            width: 36px !important;
            height: 36px !important;
            min-height: 36px !important;
            padding: 0 !important;
            background-color: #2563eb !important;
            color: white !important;
            border: none !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        [data-testid="stChatInputSubmitButton"]:hover {
            background-color: #1d4ed8 !important;
        }
        [data-testid="stChatInputSubmitButton"] svg {
            fill: white !important;
            color: white !important;
        }

        /* Hero input bar — seamless pill capsule matching ChatGPT */
        div[data-testid="stForm"] {
            border-radius: 36px !important;
            border: 1px solid rgba(128, 128, 128, 0.22) !important;
            box-shadow: 0 3px 20px -2px rgba(0, 0, 0, 0.06) !important;
            padding: 4px 12px !important;
            background: var(--secondary-background-color, #ffffff) !important;
            max-width: 680px !important;
            margin: 0 auto !important;
        }
        /* Completely remove inner border, outline, and background from text input and all wrapper containers */
        div[data-testid="stForm"] div[data-testid="stTextInput"],
        div[data-testid="stForm"] div[data-testid="stTextInput"] > div,
        div[data-testid="stForm"] div[data-testid="stTextInput"] [data-baseweb="input"],
        div[data-testid="stForm"] div[data-testid="stTextInput"] [data-baseweb="base-input"],
        div[data-testid="stForm"] div[data-testid="stTextInputRootElement"] {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            outline: none !important;
        }
        div[data-testid="stForm"] div[data-testid="stTextInput"] input {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            outline: none !important;
            font-size: 0.98rem !important;
            padding: 8px 6px !important;
            color: inherit !important;
        }
        div[data-testid="stForm"] div[data-testid="stTextInput"] input:focus {
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }
        /* Hide the "Press Enter to submit form" hint */
        div[data-testid="stForm"] [data-testid="InputInstructions"],
        div[data-testid="stForm"] div[data-testid="stInputInstructions"],
        div[data-testid="stForm"] small {
            display: none !important;
        }
        /* Circular submit button */
        div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
            border-radius: 50% !important;
            width: 36px !important;
            height: 36px !important;
            min-height: 36px !important;
            padding: 0 !important;
            font-size: 1.15rem !important;
            background-color: #2563eb !important;
            color: white !important;
            border: none !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
            background-color: #1d4ed8 !important;
        }

        /* Suggestion rows */
        .suggestion-box button[kind="tertiary"] {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            text-align: left !important;
            justify-content: flex-start !important;
            padding: 9px 12px !important;
            font-size: 0.88rem !important;
            font-weight: 400 !important;
            border-radius: 10px !important;
            color: #64748b !important;
            transition: all 0.15s ease !important;
        }
        .suggestion-box button[kind="tertiary"]:hover {
            background: rgba(128, 128, 128, 0.08) !important;
            color: inherit !important;
        }

        /* Centered chat messages matching 680px container */
        [data-testid="stChatMessage"] {
            max-width: 680px !important;
            margin: 0 auto !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Empty State: Greeting & Hero Search Bar ──────────────
    if not messages:
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

        # Hero input bar — clean input and submit button
        _, center_col, _ = st.columns([1, 4.6, 1])
        with center_col:
            with st.form("hero_chat_form", clear_on_submit=True):
                c_input, c_btn = st.columns(
                    [8.8, 0.8],
                    vertical_alignment="center",
                )
                with c_input:
                    hero_query = st.text_input(
                        "Ask DocChat Pro...",
                        label_visibility="collapsed",
                        placeholder="Ask anything about your documents...",
                    )
                with c_btn:
                    hero_submit = st.form_submit_button("↑", type="primary")

                if hero_submit and hero_query.strip():
                    st.session_state["pending_prompt"] = hero_query.strip()
                    st.rerun()

            st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)

            suggestions = [
                ("📄", "What is the schedule of depreciation for fixing IDV?"),
                ("🏖️", "What is my annual leave entitlement under the policy?"),
                ("🛡️", "What are the exclusions under Section 1 Own Damage?"),
                ("📋", "How do I escalate a discretionary approval to an HRBP?"),
            ]

            st.markdown('<div class="suggestion-box">', unsafe_allow_html=True)
            for icon, text in suggestions:
                if st.button(
                    f"{icon}  {text}",
                    key=f"sug_{text[:12]}",
                    use_container_width=True,
                    type="tertiary",
                ):
                    st.session_state["pending_prompt"] = text
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        return  # On landing with no messages, return after showing hero UI

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
            f'<div style="text-align: right; padding: 4px 0;">'
            f'<span style="font-size: 0.75rem; color: #94a3b8; font-weight: 500;">'
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

            sources = msg.get("sources", [])
            if sources:
                with st.expander(f"📄 Cited Sources ({len(sources)} chunks)", expanded=False):
                    for idx, src in enumerate(sources):
                        score = src.get("score", 0.0)
                        cid = src.get("id", f"chunk_{idx}")
                        st.markdown(f"**Chunk `{cid}`** — Relevance: `{score:.4f}`")
                        st.caption(src.get("text", "")[:400] + "...")

            if role == "assistant" and "latency" in msg:
                lat = msg.get("latency", 0.0)
                prov = msg.get("provider", "LLM")
                st.caption(f"⏱️ {lat:.2f}s · 🧠 {prov} · Mode: {msg.get('mode', 'hybrid')}")

    # ── If last message is from user, generate assistant response ──
    if messages and messages[-1].get("role") == "user":
        latest_user_query = messages[-1].get("content", "")
        with st.chat_message("assistant", avatar="🤖"):
            with st.status("Thinking and searching policy corpus...", expanded=True) as status:
                st.write("🔍 Planning query analysis & checking safety scope...")
                time.sleep(0.1)

                st.write(f"⚙️ Running {cfg.get('search_mode', 'hybrid').title()} search (top_k={cfg.get('top_k', 5)})...")
                t0 = time.time()

                ok, resp = call(
                    api.ask,
                    question=latest_user_query,
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
            title = st.session_state.get("current_chat_title") or _extract_title_from_messages(messages, latest_user_query[:36])
            st.session_state["current_chat_title"] = title
            save_chat(username, chat_id, title, messages)

        st.rerun()

    # ── Continuous Chat Input (bottom bar) ───────────────────
    user_input = st.chat_input("Ask anything about your documents...")
    if user_input:
        if not chat_id:
            title = user_input.strip().split("\n")[0][:36]
            chat_id = create_new_chat(username, title)
            st.session_state["current_chat_id"] = chat_id
            st.session_state["current_chat_title"] = title

        messages.append({"role": "user", "content": user_input, "timestamp": time.time()})
        title = st.session_state.get("current_chat_title")
        if not title or title.strip().lower() in ("new conversation", "conversation"):
            title = _extract_title_from_messages(messages, user_input[:36])
            st.session_state["current_chat_title"] = title

        save_chat(username, chat_id, title, messages)
        st.session_state["messages"] = messages
        st.rerun()


render_chat_interface()
