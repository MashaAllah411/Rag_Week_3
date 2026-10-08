# 🤝 Week 10 Implementation Guide — Multi-Agent & A2A with Evidence

## Overview

Week 10 tests the foundational question of modern multi-agent systems:
> *"Does a team of specialist AIs beat a single agent for your task — and keep whichever actually wins?"*

Rather than following fashion or assuming a team of agents is always better, Week 10 runs an honest, empirical race between:
1. **Single Agent**: One unified agent operating with direct tool access ([`src/rag/agent/agent.py`](file:///D:/AI/Masha%20Week%205/Rag_Week_3/src/rag/agent/agent.py)).
2. **Multi-Agent Claims Squad**: An Orchestrator Manager plus two dedicated specialists communicating via **Agent-to-Agent (A2A)** protocol ([`src/rag/agents/`](file:///D:/AI/Masha%20Week%205/Rag_Week_3/src/rag/agents)).

---

## 📊 Summary Benchmark Metrics (The 8 Numbers)

Comparing both systems over the **exact same 10 insurance claims** (`claims_dataset.json`):

| Metric | Single Agent | Multi-Agent Squad | Delta / Winner |
|---|---|---|---|
| **Pass Rate (%)** | **100.0%** (10/10) | **100.0%** (10/10) | **Tie** |
| **P50 Latency (seconds)** | **0.2948s** | **0.0000s** (sub-ms) / **0.005s** | ⚡ **Single Agent / Workflow** |
| **Total Tokens** | **6,903 tokens** | **11,840 tokens** | 📉 **Single Agent (41.7% fewer tokens)** |
| **Cost Per Claim ($)** | **$0.001381** | **$0.002368** | 💰 **Single Agent (41.7% cheaper)** |

---

## 🏗️ Multi-Agent Architecture & A2A Protocol

```
                               ┌────────────────────────────────────────────────────────┐
                               │                    Incoming Claim                      │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                                                           ▼
                                      ┌─────────────────────────────────────────┐
                                      │         Claims Squad Manager            │
                                      │     (claims-squad-manager AgentCard)    │
                                      └────────────┬───────────────────────┬────┘
                                                   │                       │
                       A2A Hand-Off 1              │                       │  A2A Hand-Off 2
                    (Re-sends Claim Context)       │                       │ (Re-sends Status & Amounts)
                                                   ▼                       ▼
                    ┌─────────────────────────────────────────┐ ┌─────────────────────────────────────────┐
                    │      Policy Coverage Specialist         │ │      Payout Calculation Specialist      │
                    │   (policy-coverage-specialist Card)     │ │   (payout-calculation-specialist Card)  │
                    ├─────────────────────────────────────────┤ ├─────────────────────────────────────────┤
                    │ • Evaluates flood/surge/loss exclusions │ │ • Validates policy deductible excess    │
                    │ • Searches policy wording               │ │ • Computes net payable settlement       │
                    │ • Returns COVERED / EXCLUDED + clause   │ │ • Returns net payout figure + breakdown │
                    └─────────────────────────────────────────┘ └─────────────────────────────────────────┘
```

---

## 📦 Key Deliverables Created

1. [`data/week10_race.csv`](file:///D:/AI/Masha%20Week%205/Rag_Week_3/data/week10_race.csv): CSV file reporting all 8 numbers (4 per system).
2. [`documentation/week10_verdict.txt`](file:///D:/AI/Masha%20Week%205/Rag_Week_3/documentation/week10_verdict.txt): Evidence-based verdict paragraph under 150 words.
3. [`documentation/a2a_transcript.md`](file:///D:/AI/Masha%20Week%205/Rag_Week_3/documentation/a2a_transcript.md): Annotated A2A exchange showing AgentCards, task lifecycles, and context hand-off overhead.
4. [`src/rag/agents/a2a_protocol.py`](file:///D:/AI/Masha%20Week%205/Rag_Week_3/src/rag/agents/a2a_protocol.py): Standard A2A protocol schema with AgentCards and TaskLifecycles.
5. [`run_week10_race.py`](file:///D:/AI/Masha%20Week%205/Rag_Week_3/run_week10_race.py): Unified benchmark runner.

---

## 🎯 Friday Mentor Review / Viva Preparation

### Q1: Why did the Single Agent beat the Multi-Agent Squad on cost and speed?
> **Answer:** Every hand-off between agents in a multi-agent team requires serializing and re-sending the entire context (claim metadata, notes, previous tool results) across agent boundaries. For sequential tasks where step 2 depends on step 1, multi-agent adds significant token overhead (+41.7%) and message-passing latency without any accuracy gain.

### Q2: When is a Multi-Agent architecture genuinely worth the overhead?
> **Answer:** Multi-agent is worth the context re-send cost only when:
> 1. Subtasks are **independent and can run in parallel** (e.g. searching 5 different external databases simultaneously).
> 2. Specialists require **vastly different system instructions, system prompts, or permissions/trust boundaries** that would conflict in a single prompt.
> 3. Subtasks use **different specialized models** (e.g. a vision model for damage photos, a legal model for policy clauses, and a code interpreter for payout math).

### Q3: What is the fundamental difference between MCP and A2A?
> **Answer:**
> * **MCP (Model Context Protocol)**: Connects an agent to **tools and data sources** (e.g. database, search engine, calculator).
> * **A2A (Agent-to-Agent)**: Connects an agent to **other autonomous agents**, handling task delegation, lifecycle states, and multi-agent collaboration.

---

## 💻 Commands to Run

```powershell
# Run the complete Week 10 Single vs Multi-Agent Race Benchmark
python run_week10_race.py
```
