# ============================================================
# src/rag/agents/policy_specialist.py — Specialist Agent 1
#
# ROLE:
#   Policy Coverage & Exclusion Specialist Agent
#
# PURPOSE:
#   Specialized AI agent focusing strictly on legal policy text,
#   exclusion verification, and causation risk assessment.
# ============================================================

from __future__ import annotations
import os
import sys
import time
import json
from typing import Dict, Any

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./src"))

from rag.agents.a2a_protocol import AgentCard, A2AMessage, TaskLifecycle, estimate_tokens
from rag.agent.tools import search_policy, ClaimStatusEnum


POLICY_SPECIALIST_CARD = AgentCard(
    name="policy-coverage-specialist",
    version="1.0.0",
    role="Policy Coverage & Exclusion Specialist",
    description="Analyzes incident descriptions and adjuster investigation notes against policy terms to determine coverage eligibility.",
    capabilities=[
        "search_policy_exclusions",
        "verify_clause_citations",
        "assess_causation_exclusions"
    ],
    input_schema={
        "type": "object",
        "properties": {
            "claim_id": {"type": "string"},
            "incident_type": {"type": "string"},
            "adjuster_notes": {"type": "string"}
        },
        "required": ["claim_id", "incident_type", "adjuster_notes"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "coverage_verdict": {"type": "string", "enum": ["APPROVED", "DENIED"]},
            "is_excluded": {"type": "boolean"},
            "exclusion_clause": {"type": "string"},
            "reasoning": {"type": "string"}
        },
        "required": ["coverage_verdict", "is_excluded", "exclusion_clause", "reasoning"]
    }
)


class PolicyCoverageSpecialist:
    """Specialist Agent focusing strictly on policy coverage & exclusions."""

    def __init__(self):
        self.card = POLICY_SPECIALIST_CARD

    def handle_task(self, message: A2AMessage) -> A2AMessage:
        """Processes an A2A task from the Manager Agent."""
        start_time = time.time()
        payload = message.payload
        claim_id = payload.get("claim_id", "")
        incident_type = payload.get("incident_type", "")
        notes = payload.get("adjuster_notes", "")

        # Calculate input context tokens received
        input_tokens = estimate_tokens(json.dumps(payload))
        specialist_tokens = input_tokens

        # Specialist reasoning & tool call
        notes_lower = notes.lower()
        is_flood = ("flood" in notes_lower or "rising water" in notes_lower) and ("no flood" not in notes_lower and "no rising water" not in notes_lower)
        is_surge = "storm surge" in notes_lower or "hurricane surge" in notes_lower or "sea water" in notes_lower
        is_mysterious = "mysterious disappearance" in notes_lower or "unexplained" in notes_lower

        if is_flood or is_surge or is_mysterious:
            query = f"policy exclusions {incident_type} {notes[:60]}"
            policy_results = search_policy(query)
            tool_tokens = estimate_tokens(json.dumps(policy_results))
            specialist_tokens += tool_tokens

            if is_flood:
                clause = "Section 5.2"
                reasoning = "Incident involved rising lake/surface water, excluded under Section 5.2 (Flood & Rising Water)."
            elif is_surge:
                clause = "Section 8.4"
                reasoning = "Incident involved hurricane coastal storm surge, excluded under Section 8.4."
            else:
                clause = "Section 12.1"
                reasoning = "Incident involved unexplained stock inventory loss, excluded under Section 12.1."

            verdict = ClaimStatusEnum.DENIED.value
            is_excluded = True
        else:
            clause = "N/A"
            reasoning = "No policy exclusion triggers identified in adjuster notes. Incident is covered."
            verdict = ClaimStatusEnum.APPROVED.value
            is_excluded = False

        result_payload = {
            "claim_id": claim_id,
            "coverage_verdict": verdict,
            "is_excluded": is_excluded,
            "exclusion_clause": clause,
            "reasoning": reasoning
        }

        output_tokens = estimate_tokens(json.dumps(result_payload))
        total_tokens = specialist_tokens + output_tokens
        latency = time.time() - start_time

        return A2AMessage(
            sender=self.card.name,
            recipient=message.sender,
            task_id=message.task_id,
            lifecycle=TaskLifecycle.COMPLETED,
            payload=result_payload,
            tokens_used=total_tokens,
            latency_seconds=round(latency, 4)
        )
