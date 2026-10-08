# ============================================================
# src/rag/agents/claims_manager.py — Manager Agent (Orchestrator)
#
# ROLE:
#   Claims Squad Manager / Orchestrator Agent
#
# PURPOSE:
#   Orchestrates the multi-agent workflow:
#     1. Inspects claim records and adjuster notes
#     2. Hands off coverage analysis to Policy Specialist via A2A
#     3. Hands off payout math to Payout Specialist via A2A
#     4. Synthesizes final decision and aggregates hand-off token costs
# ============================================================

from __future__ import annotations
import os
import sys
import time
import json
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./src"))

from rag.agents.a2a_protocol import AgentCard, A2AMessage, TaskLifecycle, estimate_tokens
from rag.agents.policy_specialist import PolicyCoverageSpecialist
from rag.agents.payout_specialist import PayoutCalculationSpecialist
from rag.agent.tools import get_claim

COST_PER_1K_TOKENS = 0.002

CLAIMS_MANAGER_CARD = AgentCard(
    name="claims-squad-manager",
    version="1.0.0",
    role="Claims Squad Manager & Orchestrator",
    description="Coordinates insurance claims triage squad, delegates legal and financial subtasks, and synthesizes final settlement decisions.",
    capabilities=[
        "triage_orchestration",
        "a2a_task_delegation",
        "multi_agent_synthesis"
    ],
    input_schema={
        "type": "object",
        "properties": {
            "claim_id": {"type": "string"}
        },
        "required": ["claim_id"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "claim_id": {"type": "string"},
            "system": {"type": "string"},
            "passed": {"type": "boolean"},
            "final_status": {"type": "string"},
            "net_payable": {"type": "number"},
            "total_tokens": {"type": "integer"},
            "total_cost": {"type": "number"},
            "latency_seconds": {"type": "number"},
            "a2a_transcripts": {"type": "array"}
        }
    }
)


class ClaimsSquadManager:
    """Manager Agent that coordinates specialist agents via standard A2A protocol."""

    def __init__(self):
        self.card = CLAIMS_MANAGER_CARD
        self.policy_specialist = PolicyCoverageSpecialist()
        self.payout_specialist = PayoutCalculationSpecialist()

    def run_claim_squad(self, claim_id: str) -> Dict[str, Any]:
        """Runs the multi-agent claims triage squad over A2A protocol."""
        start_time = time.time()
        total_tokens = 0
        a2a_transcripts: List[Dict[str, Any]] = []
        execution_log = []

        execution_log.append(f"[MANAGER START] Claims Squad initialized for claim {claim_id}")

        # ── Step 1: Manager pulls claim record ────────────────────────────────
        claim_rec = get_claim(claim_id)
        step1_tokens = estimate_tokens(json.dumps(claim_rec))
        total_tokens += step1_tokens
        execution_log.append(f"  Manager Step 1: Retrieved claim record for {claim_id}.")

        if "error" in claim_rec:
            latency = time.time() - start_time
            return {
                "claim_id": claim_id,
                "system": "Multi-Agent Squad",
                "passed": False,
                "final_status": "ERROR",
                "net_payable": 0.0,
                "total_tokens": total_tokens,
                "total_cost": round((total_tokens / 1000.0) * COST_PER_1K_TOKENS, 6),
                "latency_seconds": round(latency, 4),
                "a2a_transcripts": a2a_transcripts,
                "execution_log": execution_log
            }

        # ── Step 2: A2A Hand-off to Policy Specialist ─────────────────────────
        # Note: Hand-off resends claim metadata and adjuster notes over the wire
        policy_req_payload = {
            "claim_id": claim_id,
            "incident_type": claim_rec.get("incident_type", ""),
            "adjuster_notes": claim_rec.get("adjuster_notes", "")
        }
        policy_msg_in = A2AMessage(
            sender=self.card.name,
            recipient=self.policy_specialist.card.name,
            lifecycle=TaskLifecycle.SUBMITTED,
            payload=policy_req_payload
        )
        # Context re-send token overhead for hand-off request
        hand_off_1_tokens = estimate_tokens(json.dumps(policy_msg_in.to_dict()))
        total_tokens += hand_off_1_tokens

        execution_log.append(f"  Manager Step 2 (A2A -> Policy Specialist): Delegating exclusion review.")
        policy_msg_out = self.policy_specialist.handle_task(policy_msg_in)
        total_tokens += policy_msg_out.tokens_used
        a2a_transcripts.append({
            "step": "Policy Specialist Hand-Off",
            "request": policy_msg_in.to_dict(),
            "response": policy_msg_out.to_dict()
        })
        execution_log.append(f"  Policy Specialist -> Manager: Verdict = {policy_msg_out.payload.get('coverage_verdict')}, Clause = {policy_msg_out.payload.get('exclusion_clause')}.")

        coverage_verdict = policy_msg_out.payload.get("coverage_verdict", "APPROVED")

        # ── Step 3: A2A Hand-off to Payout Specialist ─────────────────────────
        # Note: Hand-off resends claim financial context over the wire
        payout_req_payload = {
            "claim_id": claim_id,
            "claim_status": coverage_verdict,
            "gross_amount": claim_rec.get("gross_claim_amount", 0.0),
            "deductible": claim_rec.get("policy_deductible", 0.0)
        }
        payout_msg_in = A2AMessage(
            sender=self.card.name,
            recipient=self.payout_specialist.card.name,
            lifecycle=TaskLifecycle.SUBMITTED,
            payload=payout_req_payload
        )
        hand_off_2_tokens = estimate_tokens(json.dumps(payout_msg_in.to_dict()))
        total_tokens += hand_off_2_tokens

        execution_log.append(f"  Manager Step 3 (A2A -> Payout Specialist): Delegating settlement computation.")
        payout_msg_out = self.payout_specialist.handle_task(payout_msg_in)
        total_tokens += payout_msg_out.tokens_used
        a2a_transcripts.append({
            "step": "Payout Specialist Hand-Off",
            "request": payout_msg_in.to_dict(),
            "response": payout_msg_out.to_dict()
        })
        execution_log.append(f"  Payout Specialist -> Manager: Net Payable = ${payout_msg_out.payload.get('net_payable'):.2f}.")

        # ── Step 4: Manager synthesizes final decision ────────────────────────
        final_payout = payout_msg_out.payload.get("net_payable", 0.0)
        manager_synthesis_tokens = estimate_tokens(f"Synthesized final claim {claim_id} decision: {coverage_verdict}, payout: {final_payout}")
        total_tokens += manager_synthesis_tokens
        execution_log.append(f"[MANAGER SUCCESS] Final settlement synthesized in Multi-Agent squad.")

        latency = time.time() - start_time
        total_cost = (total_tokens / 1000.0) * COST_PER_1K_TOKENS

        return {
            "claim_id": claim_id,
            "system": "Multi-Agent Squad (Manager + 2 Specialists)",
            "passed": True,
            "final_status": coverage_verdict,
            "net_payable": float(final_payout),
            "policy_clause": policy_msg_out.payload.get("exclusion_clause", "N/A"),
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 6),
            "latency_seconds": round(latency, 4),
            "a2a_transcripts": a2a_transcripts,
            "execution_log": execution_log
        }


def run_claim_multi_agent(claim_id: str) -> Dict[str, Any]:
    manager = ClaimsSquadManager()
    return manager.run_claim_squad(claim_id)


if __name__ == "__main__":
    cid = sys.argv[1] if len(sys.argv) > 1 else "CLM-7002"
    manager = ClaimsSquadManager()
    res = manager.run_claim_squad(cid)
    print(f"Multi-Agent Squad Result for {cid}:\n{json.dumps(res, indent=2)}")
