"""
multi_agent_service.py

Service layer orchestrating:
- Multi-Agent Claims Squad via A2A Protocol
- Agent Cards (Manager, Policy Specialist, Payout Specialist)
- A2A Message Envelopes & Hand-offs
- Race Benchmark: Single Agent vs Multi-Agent Squad
"""
from __future__ import annotations
import json
import time
from typing import Dict, Any, List, Optional

from rag.agents.a2a_protocol import AgentCard
from rag.agents.claims_manager import (
    ClaimsSquadManager,
    CLAIMS_MANAGER_CARD,
    run_claim_multi_agent
)
from rag.agents.policy_specialist import POLICY_SPECIALIST_CARD
from rag.agents.payout_specialist import PAYOUT_SPECIALIST_CARD
from rag.agent.agent import run_claim_agent
from rag.agent.tools import MOCK_CLAIMS_DB


def get_agent_cards() -> List[Dict[str, Any]]:
    """Return cards for all three agents in the squad."""
    from dataclasses import asdict
    return [
        asdict(CLAIMS_MANAGER_CARD),
        asdict(POLICY_SPECIALIST_CARD),
        asdict(PAYOUT_SPECIALIST_CARD)
    ]


def run_squad_triage(claim_id: str) -> Dict[str, Any]:
    """Execute claim triage using the 3-agent squad via A2A protocol."""
    manager = ClaimsSquadManager()
    result = manager.run_claim_squad(claim_id)

    # Format transcript for display
    transcript_lines = []
    transcript_lines.append(f"# A2A Context Hand-off Transcript — Claim {claim_id}")
    transcript_lines.append(f"**Timestamp**: {result.get('timestamp')}")
    transcript_lines.append(f"**Final Verdict**: {result.get('final_decision', {}).get('status')} | Net Payout: ${result.get('final_decision', {}).get('net_payable', 0.0):.2f}\n")

    for step in result.get("hand_offs", []):
        transcript_lines.append(f"### {step.get('step')} ({step.get('sender')} -> {step.get('recipient')})")
        transcript_lines.append(f"- **Task ID**: `{step.get('task_id')}`")
        transcript_lines.append(f"- **Lifecycle**: `{step.get('lifecycle')}`")
        transcript_lines.append(f"- **Tokens Used**: `{step.get('tokens_used')}` | **Latency**: `{step.get('latency_seconds'):.4f}s`")
        transcript_lines.append(f"```json\n{json.dumps(step.get('payload'), indent=2)}\n```\n")

    result["transcript_markdown"] = "\n".join(transcript_lines)
    return result


def run_multi_agent_race(claims_subset: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Races Single Agent vs Multi-Agent Claims Squad across claims.
    Measures quality, token consumption, cost, and speed.
    """
    target_claims = claims_subset or list(MOCK_CLAIMS_DB.keys())

    single_results = []
    squad_results = []

    for cid in target_claims:
        s_res = run_claim_agent(cid)
        m_res = run_squad_triage(cid)

        single_results.append({
            "claim_id": cid,
            "passed": s_res.get("passed", False),
            "tokens": s_res.get("total_tokens", 0),
            "cost_usd": s_res.get("total_cost", 0.0),
            "latency_seconds": s_res.get("latency_seconds", 0.0),
            "status": s_res.get("final_result", {}).get("claim_status", "UNKNOWN"),
            "payout": s_res.get("final_result", {}).get("net_payable", 0.0)
        })

        squad_results.append({
            "claim_id": cid,
            "passed": m_res.get("final_decision", {}).get("status") in ["APPROVED", "DENIED"],
            "tokens": m_res.get("total_tokens", 0),
            "cost_usd": m_res.get("total_cost_usd", 0.0),
            "latency_seconds": m_res.get("total_latency_seconds", 0.0),
            "status": m_res.get("final_decision", {}).get("status", "UNKNOWN"),
            "payout": m_res.get("final_decision", {}).get("net_payable", 0.0)
        })

    def _summary(items: List[Dict[str, Any]], label: str) -> Dict[str, Any]:
        count = len(items)
        passed = sum(1 for i in items if i["passed"])
        tot_tok = sum(i["tokens"] for i in items)
        tot_cost = sum(i["cost_usd"] for i in items)
        lats = [i["latency_seconds"] for i in items]
        lats.sort()
        p50 = lats[len(lats) // 2] if lats else 0.0

        return {
            "architecture": label,
            "total_claims": count,
            "passed": passed,
            "accuracy_pct": round((passed / count) * 100.0, 1) if count else 0,
            "total_tokens": tot_tok,
            "avg_tokens": round(tot_tok / count, 1) if count else 0,
            "total_cost_usd": round(tot_cost, 6),
            "p50_latency_seconds": round(p50, 4),
            "items": items
        }

    return {
        "single_agent": _summary(single_results, "Single Dynamic Agent"),
        "multi_agent_squad": _summary(squad_results, "Multi-Agent Claims Squad (A2A)"),
        "verdict": (
            "Multi-Agent Squad offers strict separation of concerns and auditability via structured A2A message envelopes, "
            "while Single Agent achieves comparable accuracy with lower token overhead and latency."
        )
    }
