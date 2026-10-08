# 🔌 Week 9 Implementation Guide — MCP Multi-Server Tool Discovery

## Overview

Week 9 focuses on **Model Context Protocol (MCP)**:
> *"Bolt on the claims-system server without touching the agent."*

Instead of hard-coding tool registries or wrapping LLM logic inside tools, Week 9 establishes a standard, decoupled MCP client-server architecture:
1. **Config-Only Discovery**: The agent discovers tools at runtime over JSON-RPC 2.0. Adding Server 2 requires ZERO agent code changes (`agent_diff.txt`).
2. **Strict Host-Server Separation**: The MCP server exposes deterministic capabilities; the host agent runs the LLM model loop.
3. **Docstring-as-Prompt & Recoverable Errors**: Rewriting tool docstrings and providing actionable format guidance so the model self-corrects on invalid inputs (`error_before_after.md`).
4. **Annotated Wire Protocol**: Capturing the raw JSON-RPC `initialize` $\to$ `tools/list` $\to$ `tools/call` message sequence (`wire.json`).
5. **Third-Party Risk Analysis**: Exactly 5-line supply-chain risk evaluation (`risk_note.md`).

---

## 📊 Key Metrics & Submission Checklist

| Criterion | Target / Result | Deliverable File | Status |
|---|---|---|---|
| **Zero Lines Changed in Agent** | `0 lines` changed in `mcp_agent.py` | [`documentation/agent_diff.txt`](file:///D:/AI/Masha%20Week%205/Rag_Week_3/documentation/agent_diff.txt) | **PASS** |
| **Tool Count (tools/list)** | **`2 before -> 4 after`** | Console Output | **PASS** |
| **Raw Wire Protocol** | Annotated JSON-RPC 2.0 exchange | [`data/wire.json`](file:///D:/AI/Masha%20Week%205/Rag_Week_3/data/wire.json) | **PASS** |
| **Model Boundary Statement** | Stated in 1 explicit line | [`data/wire.json`](file:///D:/AI/Masha%20Week%205/Rag_Week_3/data/wire.json) | **PASS** |
| **Recoverable Error Transcript** | Before vs After transcript | [`documentation/error_before_after.md`](file:///D:/AI/Masha%20Week%205/Rag_Week_3/documentation/error_before_after.md) | **PASS** |
| **Third-Party Risk Note** | Exactly 5 lines | [`documentation/risk_note.md`](file:///D:/AI/Masha%20Week%205/Rag_Week_3/documentation/risk_note.md) | **PASS** |

---

## 🛠️ Architecture & Protocol Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Host Agent                           │
│                 (src/rag/agent/mcp_agent.py)                │
│                                                             │
│  • Reads data/mcp_config.json                               │
│  • Runs the LLM Model Call & Reasoning Loop                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
               JSON-RPC 2.0 (stdio Transport)
                               │
        ┌──────────────────────┴──────────────────────┐
        ▼                                             ▼
┌──────────────────────────────┐       ┌──────────────────────────────┐
│  Server 1: Policy Server     │       │  Server 2: Claims Server     │
│ (src/rag/mcp/policy_server)  │       │ (src/rag/mcp/claims_server)  │
├──────────────────────────────┤       ├──────────────────────────────┤
│ • search_policy              │       │ • get_claim_status           │
│ • get_policy_clause          │       │ • get_adjuster_notes         │
│   (Docstring-as-prompt with  │       │                              │
│    recoverable error path)   │       │                              │
└──────────────────────────────┘       └──────────────────────────────┘
```

---

## 💻 Commands to Run

```powershell
# Run the complete Week 9 Evaluation Suite (One Command)
python run_week9_mcp.py

# Run the MCP Host Agent directly
python -m rag.agent.mcp_agent data/mcp_config.json CLM-7002
```
