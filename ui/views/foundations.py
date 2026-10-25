"""
ui/views/foundations.py

Week 1 - Foundations Lab: tokens and context windows, cost per token, temperature and
sampling, embeddings. Everything is computed by the backend from real parts (the embedding
model's tokenizer and vectors, plain numpy for sampling); nothing is mocked.
"""
import pandas as pd
import streamlit as st

from ui.api_client import api
from ui.components import call, info_card, page_header, pill

page_header(
    "Foundations Lab", "🧪",
    "See how a language model reads text, what it costs, why answers vary, and how meaning becomes numbers.",
    weeks=["1"],
)

tab_tokens, tab_cost, tab_sampling, tab_embed, tab_models = st.tabs([
    "🔤 Tokens & context", "💲 Cost", "🎲 Temperature & sampling", "🧭 Embeddings", "📚 Model families & hallucination",
])

# ── Tokens & context ─────────────────────────────────────────
with tab_tokens:
    st.subheader("How text is chopped into tokens")
    st.markdown("A model never sees words. It sees **tokens** (pieces of words). You pay per token, and the model can only "
                "read so many at once (the **context window**).")
    default_text = ("The insured vehicle was damaged in a flood. Under Section 5.2, rising lake water and surface "
                    "runoff are excluded from standard coverage.")
    text = st.text_area("Text to tokenize", value=default_text, height=120, key="fl_tok_text")
    window = st.select_slider("Context window (tokens)", options=[512, 1024, 2048, 4096, 8192, 32768, 131072], value=4096,
                              key="fl_tok_window")
    if st.button("Count tokens", type="primary", key="fl_tok_btn"):
        if not text.strip():
            st.warning("Enter some text first.")
        else:
            ok, res = call(api.tokenize, text, window, spinner="Tokenizing...")
            if ok:
                st.session_state["fl_tok_res"] = res
    res = st.session_state.get("fl_tok_res")
    if res:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tokens", res["token_count"])
        c2.metric("Characters", res["characters"])
        c3.metric("Words", res["words"])
        c4.metric("Chars per token", res["chars_per_token"])
        pct = min(res["context_used_pct"], 100.0)
        st.progress(pct / 100.0, text=f"{res['context_used_pct']}% of a {res['context_window']:,}-token context window used")
        chips = "".join(pill(t.replace("<", "&lt;"), "") for t in res["tokens"][:80])
        st.markdown(chips, unsafe_allow_html=True)
        if res["truncated"] or res["token_count"] > 80:
            st.caption(f"Showing the first {min(80, len(res['tokens']))} of {res['token_count']} tokens.")
        st.caption(f"Tokenizer: {res['method']}")
        info_card(res["note"])

# ── Cost ─────────────────────────────────────────────────────
with tab_cost:
    st.subheader("What a request costs")
    info_card("Local Ollama models cost <b>$0 per token</b> (you pay in hardware and time). The prices below are "
              "<b>illustrative hosted-model prices</b> you can edit; they show how token counts turn into a bill.", "sim")
    c1, c2 = st.columns(2)
    with c1:
        in_tok = st.number_input("Input tokens per request", min_value=0, value=900, step=50, key="fl_cost_in",
                                 help="Prompt + retrieved context. In RAG this is usually the larger share.")
        out_tok = st.number_input("Output tokens per request", min_value=0, value=150, step=10, key="fl_cost_out")
        reqs = st.number_input("Requests per day", min_value=1, value=10000, step=500, key="fl_cost_reqs")
    with c2:
        p_in = st.number_input("$ per 1M input tokens", min_value=0.0, value=0.15, step=0.05, format="%.4f", key="fl_cost_pin")
        p_out = st.number_input("$ per 1M output tokens", min_value=0.0, value=0.60, step=0.05, format="%.4f", key="fl_cost_pout")
    if st.button("Estimate cost", type="primary", key="fl_cost_btn"):
        ok, res = call(api.estimate_cost, int(in_tok), int(out_tok), int(reqs), float(p_in), float(p_out),
                       spinner="Calculating...")
        if ok:
            st.session_state["fl_cost_res"] = res
    res = st.session_state.get("fl_cost_res")
    if res:
        m1, m2, m3 = st.columns(3)
        m1.metric("Per request", f"${res['per_request_usd']:.6f}")
        m2.metric(f"Per day ({res['requests']:,} requests)", f"${res['total_usd']:,.2f}")
        m3.metric("Share from input tokens", f"{res['input_share_pct']}%")
        st.caption(f"Assumed prices per million tokens: input ${res['assumed_prices_per_million']['input']}, "
                   f"output ${res['assumed_prices_per_million']['output']}. "
                   "Shrinking the retrieved context is usually the biggest lever, which is why chunk size matters.")

# ── Temperature & sampling ───────────────────────────────────
with tab_sampling:
    st.subheader("Why the same question can give different answers")
    st.markdown("The model scores every possible next token. **Temperature** reshapes those scores into probabilities: low "
                "is predictable, high is varied. **Temperature 0 is greedy decoding** (always the top token). "
                "**Top-k** and **top-p** cut off the unlikely tail before sampling.")
    st.caption("Edit the candidate tokens and their scores (logits) below.")
    base = pd.DataFrame({"token": ["approved", "denied", "pending", "review"], "logit": [2.0, 1.2, 0.4, -0.5]})
    table = st.data_editor(base, num_rows="dynamic", hide_index=True, key="fl_samp_table", width="stretch")
    s1, s2, s3 = st.columns(3)
    temperature = s1.slider("Temperature (0 = greedy)", 0.0, 3.0, 1.0, 0.1, key="fl_samp_temp")
    top_k = s2.slider("Top-k (0 = off)", 0, 10, 0, key="fl_samp_k")
    top_p = s3.slider("Top-p", 0.05, 1.0, 1.0, 0.05, key="fl_samp_p")
    s4, s5 = st.columns(2)
    draws = s4.slider("Number of draws", 10, 2000, 200, 10, key="fl_samp_draws")
    seed = s5.number_input("Random seed", value=42, step=1, key="fl_samp_seed")
    if st.button("Sample", type="primary", key="fl_samp_btn"):
        clean = table.dropna(subset=["token", "logit"])
        clean = clean[clean["token"].astype(str).str.strip() != ""]
        if len(clean) < 2:
            st.warning("Provide at least two candidate tokens with scores.")
        else:
            ok, res = call(api.sampling_demo, clean["token"].astype(str).tolist(), clean["logit"].astype(float).tolist(),
                           temperature, int(top_k), float(top_p), int(draws), int(seed), spinner="Sampling...")
            if ok:
                st.session_state["fl_samp_res"] = res
    res = st.session_state.get("fl_samp_res")
    if res:
        rows = pd.DataFrame(res["rows"])
        m1, m2, m3 = st.columns(3)
        m1.metric("Mode", res["mode"].title())
        m2.metric("Entropy (bits)", res["entropy_bits"], help="0 = always the same token; higher = more varied.")
        m3.metric("Distinct tokens drawn", res["distinct_tokens_drawn"])
        chart = rows.set_index("token")[["probability", "final_probability"]]
        st.bar_chart(chart)
        st.caption("probability = after temperature · final_probability = after top-k / top-p filtering")
        show = rows.rename(columns={"probability": "after temperature", "kept": "kept by top-k/top-p",
                                    "final_probability": "final probability", "drawn": "times drawn"})
        st.dataframe(show, hide_index=True, width="stretch")
        if res["mode"] == "greedy":
            st.success("Greedy: the highest-scoring token wins every time, so the answer never varies.")
        else:
            st.info("Sampled: lower temperature concentrates the draws on the top token; higher temperature spreads them out.")

# ── Embeddings ───────────────────────────────────────────────
with tab_embed:
    st.subheader("Meaning as numbers")
    st.markdown("An **embedding** turns text into a list of numbers so a computer can compare *meaning*, not just words. "
                "This uses the app's real embedding model, the same one that powers retrieval.")
    defaults = ["flood damage is excluded", "damage from flooding is not covered", "office opens at nine"]
    count = st.slider("How many texts to compare", 2, 6, 3, key="fl_emb_n")
    texts = []
    for i in range(count):
        texts.append(st.text_input(f"Text {i + 1}", value=defaults[i] if i < len(defaults) else "", key=f"fl_emb_t{i}"))
    if st.button("Compare meaning", type="primary", key="fl_emb_btn"):
        filled = [t for t in texts if t.strip()]
        if len(filled) < 2:
            st.warning("Enter at least two non-empty texts.")
        else:
            ok, res = call(api.embedding_similarity, filled, spinner="Embedding texts (the first call loads the model)...")
            if ok:
                st.session_state["fl_emb_res"] = res
    res = st.session_state.get("fl_emb_res")
    if res:
        labels = [f"{i + 1}. {t[:34]}" for i, t in enumerate(res["texts"])]
        matrix = pd.DataFrame(res["matrix"], index=labels, columns=[str(i + 1) for i in range(len(labels))])
        def _shade(value: float) -> str:
            level = max(0.0, min(1.0, float(value)))
            style = f"background-color: rgba(31, 111, 235, {0.08 + 0.72 * level:.2f})"
            return style + "; color: #fff" if level > 0.6 else style   # low levels keep the theme's own text colour

        st.dataframe(matrix.style.map(_shade).format("{:.2f}"), width="stretch")
        st.caption(f"Cosine similarity across {res['dimensions']} dimensions. 1.00 = identical meaning. {res['note']}")

# ── Model families & hallucination ───────────────────────────
with tab_models:
    st.subheader("Model families and why models make things up")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("#### Decoder models (GPT, Claude, LLaMA)")
            st.write("Predict the next token, over and over, to write text. This app's answer generator "
                     "(Ollama / llama3.2) is a decoder.")
        with st.container(border=True):
            st.markdown("#### Encoder models (BERT-style)")
            st.write("Read text and produce numbers that represent it. The embedding model (all-MiniLM-L6-v2) and the "
                     "cross-encoder reranker are encoder-style models. They compare; they do not write.")
    with c2:
        with st.container(border=True):
            st.markdown("#### Static vs contextual embeddings")
            st.write("Old word embeddings (Word2Vec, GloVe) give a word one fixed vector. Modern ones change with the "
                     "sentence, so 'bank' in 'river bank' and 'bank loan' differ.")
        with st.container(border=True):
            st.markdown("#### Why sounding right is not being right")
            st.write("The model picks the *likely* next words, it does not look facts up. A fluent answer can be invented. "
                     "That is a hallucination.")
    st.markdown("#### How this app reduces hallucination")
    st.markdown(
        "1. **Retrieve first**: the answer is written from policy text found for your question, not from memory.\n"
        "2. **Cite**: Search & Q&A shows the chunks the answer came from.\n"
        "3. **Say 'I don't know'**: if nothing relevant is retrieved, the pipeline refuses instead of guessing.\n"
        "4. **Guard**: off-topic or gibberish questions are rejected before retrieval (see Guardrails & Security).\n"
        "5. **Measure**: the Evaluation page checks whether the right passage is actually being found."
    )
