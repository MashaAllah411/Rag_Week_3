"""
ui/app.py

Main Streamlit Application Entrance.
Provides stack overview, system status check, and navigation guide.
"""
import streamlit as st
from ui.api_client import api

st.set_page_config(
    page_title="Insurance Policy & Claims RAG Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.title("🛡️ Insurance RAG Stack")
    st.caption("Weeks 1–11 Capstone Production Architecture")

    # Stack Health Indicator
    try:
        health = api.get_health()
        st.success("🟢 Backend Online (FastAPI)")
    except Exception as e:
        st.error("🔴 Backend Offline — Run `python run.py`")

    st.markdown("---")
    st.markdown("### 🧭 Capabilities")
    st.markdown(
        "- **1. Documents**: Upload, list, index & chunk inspector\n"
        "- **2. Search & Q&A**: Hybrid, reranked, citations & context\n"
        "- **3. Agent Triage**: ReAct Agent (4 budgets) vs Workflow\n"
        "- **4. MCP Ecosystem**: JSON-RPC servers & tool discovery\n"
        "- **5. Multi-Agent Squad**: Manager + Specialists (A2A)\n"
        "- **6. Evaluation**: Retrieval metrics & LLM judge\n"
        "- **7. Observability**: Spans, replay & support drill\n"
        "- **8. System**: Health, masked config & live logs\n"
    )

# ── Main Page ────────────────────────────────────────────────
st.title("🛡️ Enterprise Insurance Policy & Claims RAG Platform")
st.markdown(
    "Welcome to the production refactored RAG system. Every feature across Weeks 1 through 11 "
    "is accessible below or via the pages in the sidebar. "
    "All operations call the FastAPI backend strictly over HTTP."
)

# System Summary KPI Cards
try:
    status_data = api.get_system_status()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Backend Status", status_data.get("status", "unknown").upper(), delta="Port 8000")
    with c2:
        ollama_info = status_data.get("components", {}).get("ollama_llm", {})
        st.metric("LLM Provider", ollama_info.get("model", "llama3.2"), delta="Reachable" if ollama_info.get("reachable") else "Offline")
    with c3:
        pinecone_info = status_data.get("components", {}).get("pinecone_vector_db", {})
        st.metric("Vector Database", "Pinecone", delta=pinecone_info.get("index_name", "rag-week-3-py"))
    with c4:
        doc_count = status_data.get("storage", {}).get("pdf_documents_count", 0)
        st.metric("Indexed Documents", f"{doc_count} PDFs", delta="resources/")
except Exception as exc:
    st.warning(f"Could not connect to backend at {api.base_url}. Make sure FastAPI is running.")

st.markdown("---")

# Feature Showcase Grid
st.subheader("⚡ Quick Launch Capabilities")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### 📄 1. Document Management")
        st.write("Upload PDFs, inspect sentence/fixed chunk boundaries, monitor background ingestion, or re-index into Pinecone.")
        st.page_link("pages/1_Documents.py", label="Open Document Management →", icon="📄")

    with st.container(border=True):
        st.markdown("### 🤖 3. Agent Triage & Budget Enforcement")
        st.write("Execute claim triage with dynamic ReAct agent enforcing 4 budgets (iterations, tokens, cost, timeout) or race against Fixed Workflow.")
        st.page_link("pages/3_Agent_Triage.py", label="Open Agent Triage →", icon="🤖")

    with st.container(border=True):
        st.markdown("### 👥 5. Multi-Agent Claims Squad (A2A)")
        st.write("Orchestrate Claims Manager + Policy Specialist + Payout Specialist over structured A2A message envelopes.")
        st.page_link("pages/5_Multi_Agent_Squad.py", label="Open Multi-Agent Squad →", icon="👥")

    with st.container(border=True):
        st.markdown("### 📊 7. Observability & Support Drill")
        st.write("Inspect OpenTelemetry spans, replay traces from saved context, run support triage drill on 100 traces, and test cache cost reduction.")
        st.page_link("pages/7_Observability.py", label="Open Observability →", icon="📊")

with col2:
    with st.container(border=True):
        st.markdown("### 🔍 2. Search & Grounded Q&A")
        st.write("Semantic, Hybrid (BM25 + Pinecone via RRF), and Reranked (Cross-Encoder + MMR) retrieval with confidence assessment and citations.")
        st.page_link("pages/2_Search_and_QA.py", label="Open Search & Q&A →", icon="🔍")

    with st.container(border=True):
        st.markdown("### 🔌 4. Model Context Protocol (MCP)")
        st.write("Connect to policy and claims MCP servers, dynamically discover tools via JSON-RPC 2.0, and execute tool calls.")
        st.page_link("pages/4_MCP_Ecosystem.py", label="Open MCP Ecosystem →", icon="🔌")

    with st.container(border=True):
        st.markdown("### 🎯 6. Evaluation & LLM Judge")
        st.write("Compare baseline vs hybrid Hit Rate@3 & Recall@3, review failure separation, run regex assertions, and test LLM Judge V1 vs V2.")
        st.page_link("pages/6_Evaluation.py", label="Open Evaluation →", icon="🎯")

    with st.container(border=True):
        st.markdown("### ⚙️ 8. System & Logs")
        st.write("View component health, inspect masked environment variables, and review real-time application logs.")
        st.page_link("pages/8_System.py", label="Open System Page →", icon="⚙️")
