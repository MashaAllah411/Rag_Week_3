"""
ui/views/home.py

Landing page: what the platform does, live health at a glance, where to go next.
"""
import streamlit as st

from ui.api_client import api
from ui.components import call, info_card, page_header, pill

page_header(
    "Insurance Policy & Claims Assistant",
    "🛡️",
    "Ask questions about insurance policies and get answers that quote their source, "
    "triage claims with an agent, and see how well every step performs.",
)

st.markdown(
    "Upload a policy PDF and the platform splits it into passages, indexes them, and finds the "
    "right ones when you ask a question. Every answer shows the passages it used, so you can check it. "
    "Around that core you can explore agents, tool servers, multi-agent teams, evaluation and tracing. "
    "Everything on these pages is operated from the browser; you only started it with one command."
)

# ── Live health ──────────────────────────────────────────────
ok, status = call(api.get_system_status, spinner="Checking system...", show_error=False)
if not ok:
    info_card("<b>The backend is not reachable.</b> Start the whole stack with <code>python run.py</code>, "
              "then refresh this page.", "warn")
    status = {}

components = status.get("components", {}) if status else {}
llm = components.get("ollama_llm", {})
vec = components.get("vector_store", {})
tracing = components.get("tracing", {})
indexing = status.get("indexing", {}) if status else {}
docs_count = status.get("storage", {}).get("pdf_documents_count", 0) if status else 0

if ok:
    if indexing.get("state") == "indexing":
        info_card(f"<b>Indexing in progress.</b> Preparing <code>{indexing.get('current') or 'documents'}</code> "
                  f"({indexing.get('documents_done', 0)} finished). Search results appear as soon as it completes.")
    elif vec.get("reachable") and vec.get("chunks", 0) == 0:
        info_card("<b>Nothing is indexed yet.</b> Open <b>Documents</b> and upload a policy PDF, or press "
                  "<i>Re-index</i> to index the files in <code>resources/</code>.", "warn")
    if indexing.get("state") == "error":
        info_card(f"<b>The last indexing run failed:</b> {indexing.get('last_error')}", "warn")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Backend", "Online" if ok else "Offline")
k2.metric("Local LLM", "Reachable" if llm.get("reachable") else "Not running",
          help=f"Model: {llm.get('model', 'n/a')}. Needed to write answers, not to find passages.")
k3.metric("Vector store", (vec.get("backend") or "n/a").title(), delta=f"{vec.get('chunks', 0)} passages",
          delta_color="off")
k4.metric("Documents", docs_count, help="PDFs in the resources folder")
k5.metric("Tracing", "Active" if tracing.get("active") else "Off", delta=f"{tracing.get('spans_exported', 0)} spans",
          delta_color="off")

if ok and not llm.get("reachable"):
    info_card("The local LLM (Ollama) is not running, so answers are shown as retrieved passages only. "
              "Run <code>ollama serve</code> and <code>ollama pull llama3.2</code> to enable written answers.", "sim")

st.markdown("---")

# ── Start here ───────────────────────────────────────────────
st.subheader("Start here")
s1, s2, s3 = st.columns(3)
with s1:
    with st.container(border=True):
        st.markdown("#### 1. Upload a policy")
        st.write("Add a PDF. It is read (with OCR for scanned images), split into passages and indexed.")
        st.page_link("views/documents.py", label="Open Documents", icon="📄")
with s2:
    with st.container(border=True):
        st.markdown("#### 2. Ask a question")
        st.write("Get an answer with its source passages, a confidence level and the steps taken.")
        st.page_link("views/search_qa.py", label="Open Search & Q&A", icon="🔍")
with s3:
    with st.container(border=True):
        st.markdown("#### 3. Inspect the trace")
        st.write("See the time and cost of each step of the request you just made.")
        st.page_link("views/observability.py", label="Open Observability", icon="📊")

st.markdown("---")

# ── Capability grid, grouped like the sidebar ────────────────
st.subheader("Everything you can do")

GROUPS = [
    ("Learn & Guardrails", [
        ("views/foundations.py", "Foundations Lab", "🧪", "Tokens, cost, temperature and embeddings, hands on.", "1"),
        ("views/guardrails.py", "Guardrails & Security", "🛡️", "Fixed-format answers, input checks and prompt-injection defence.", "2, 8"),
    ]),
    ("Documents & Answers", [
        ("views/documents.py", "Documents", "📄", "Upload, index and inspect how documents are chunked.", "3"),
        ("views/search_qa.py", "Search & Q&A", "🔍", "Semantic, hybrid and reranked retrieval with citations.", "3, 4"),
    ]),
    ("Evaluate", [
        ("views/evaluation.py", "Evaluation", "🎯", "Measure retrieval, check assertions and validate the judge.", "4, 6"),
        ("views/error_analysis.py", "Error Analysis", "🔬", "Read real traces, name the problems and rank them.", "5"),
    ]),
    ("Agents", [
        ("views/agent_triage.py", "Agent Triage", "🤖", "Claim triage with budgets, versus a fixed workflow.", "7, 8"),
        ("views/mcp.py", "MCP Ecosystem", "🔌", "Tools discovered over the Model Context Protocol.", "9"),
        ("views/multi_agent.py", "Multi-Agent Squad", "👥", "A manager and two specialists, raced against one agent.", "10"),
    ]),
    ("Production", [
        ("views/observability.py", "Observability", "📊", "Spans, replay, the support drill and cost.", "5, 11"),
    ]),
    ("Capstone & System", [
        ("views/capstone.py", "Capstone", "🏁", "Run the full suite, see weak spots, rehearse the demo.", "12"),
        ("views/system.py", "System & Health", "⚙️", "Which open-source tools are live, self-tests, logs.", "3, 11"),
        ("views/documentation.py", "Documentation", "📖", "How it works and how to do common tasks.", ""),
    ]),
]

for group, items in GROUPS:
    st.markdown(f"**{group}**")
    cols = st.columns(len(items))
    for col, (path, label, icon, blurb, weeks) in zip(cols, items):
        with col:
            with st.container(border=True):
                st.page_link(path, label=label, icon=icon)
                st.caption(blurb)
                if weeks:
                    st.markdown(pill(f"Week {weeks}", "week"), unsafe_allow_html=True)
