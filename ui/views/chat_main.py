"""
ui/views/chat_main.py

Production ChatGPT-style conversation workspace.
Features:
- "Where should we begin?" empty state with suggestion pills
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

    # ── Top Bar: Context Window Indicator ────────────────────
    total_tokens = sum(_approx_tokens(m.get("content", "")) for m in messages)
    context_limit = 4096
    pct = min(100, int((total_tokens / context_limit) * 100))
    tone = "bad" if pct > 85 else ("warn" if pct > 60 else "ok")

    t_col1, t_col2 = st.columns([4, 1])
    with t_col1:
        active_title = st.session_state.get("current_chat_title", "Conversation")
        st.markdown(f"#### 💬 {active_title}")
    with t_col2:
        st.markdown(
            f"""
            <div style="text-align: right; padding-top: 5px;">
                <span style="font-size: 0.8rem; font-weight: 600; color: #94a3b8;">
                    Context: {total_tokens:,} / {context_limit:,} toks
                </span>
                {pill(f"{pct}%", tone)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Empty State: Greeting & Suggestion Chips ─────────────
    if not messages:
        st.markdown(
            """
            <div style="text-align: center; margin: 40px 0 20px 0;">
                <h1 style="font-size: 2.2rem; font-weight: 700; margin-bottom: 8px;">
                    Where should we begin?
                </h1>
                <p style="color: #64748b; font-size: 1rem;">
                    Ask questions across your policy documents, claims rules, or employee guidelines.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        chip_col1, chip_col2 = st.columns(2)
        with chip_col1:
            if st.button("📌 What is the schedule of depreciation for fixing IDV?", use_container_width=True):
                st.session_state["pending_prompt"] = "What is the schedule of depreciation for fixing IDV?"
                st.rerun()
            if st.button("📌 What is my annual leave entitlement?", use_container_width=True):
                st.session_state["pending_prompt"] = "What is my annual leave entitlement?"
                st.rerun()
        with chip_col2:
            if st.button("📌 What are the exclusions under Section 1 Own Damage?", use_container_width=True):
                st.session_state["pending_prompt"] = "What are the exclusions under Section 1 Own Damage?"
                st.rerun()
            if st.button("📌 How do I escalate a discretionary approval to an HRBP?", use_container_width=True):
                st.session_state["pending_prompt"] = "How do I escalate a discretionary approval to an HRBP?"
                st.rerun()

        st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

    # ── Message History Rendering ────────────────────────────
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
