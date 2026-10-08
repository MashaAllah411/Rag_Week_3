# ============================================================
# src/rag/agents/payout_specialist.py — Specialist Agent 2
#
# ROLE:
#   Payout & Financial Settlement Specialist Agent
#
# PURPOSE:
#   Specialized AI agent focusing strictly on policy excess,
#   deductible mathematics, and financial settlement computation.
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
from rag.agent.tools import compute_payout, ClaimStatusEnum


PAYOUT_SPECIALIST_CARD = AgentCard(
    name="payout-calculation-specialist",
    version="1.0.0",
    role="Payout & Financial Settlement Specialist",
    description="Computes precise financial payouts, applies policy deductibles, and enforces settlement limits based on verified claim status.",
    capabilities=[
        "compute_net_payout",
        "validate_policy_excess",
        "generate_settlement_breakdown"
    ],
    input_schema={
        "type": "object",
        "properties": {
            "claim_id": {"type": "string"},
            "claim_status": {"type": "string", "enum": ["APPROVED", "DENIED", "UNDER_INVESTIGATION"]},
            "gross_amount": {"type": "number"},
            "deductible": {"type": "number"}
        },
        "required": ["claim_id", "claim_status", "gross_amount", "deductible"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "claim_id": {"type": "string"},
            "claim_status": {"type": "string"},
            "gross_amount": {"type": "number"},
            "deductible": {"type": "number"},
            "net_payable": {"type": "number"},
            "explanation": {"type": "string"}
        },
        "required": ["claim_id", "claim_status", "gross_amount", "deductible", "net_payable", "explanation"]
    }
)


class PayoutCalculationSpecialist:
    """Specialist Agent focusing strictly on deductible math & settlement payouts."""

    def __init__(self):
        self.card = PAYOUT_SPECIALIST_CARD

    def handle_task(self, message: A2AMessage) -> A2AMessage:
        """Processes an A2A task from the Manager Agent."""
        start_time = time.time()
        payload = message.payload
        claim_id = payload.get("claim_id", "")
        status_str = payload.get("claim_status", "APPROVED")
        gross = float(payload.get("gross_amount", 0.0))
        deductible = float(payload.get("deductible", 0.0))

        input_tokens = estimate_tokens(json.dumps(payload))
        specialist_tokens = input_tokens

        # Execute payout computation
        status_enum = ClaimStatusEnum(status_str) if status_str in ClaimStatusEnum.__members__ else ClaimStatusEnum.APPROVED
        payout_res = compute_payout(claim_id, status_enum, gross, deductible)

        tool_tokens = estimate_tokens(json.dumps(payout_res))
        specialist_tokens += tool_tokens

        output_tokens = estimate_tokens(json.dumps(payout_res))
        total_tokens = specialist_tokens + output_tokens
        latency = time.time() - start_time

        return A2AMessage(
            sender=self.card.name,
            recipient=message.sender,
            task_id=message.task_id,
            lifecycle=TaskLifecycle.COMPLETED,
            payload=payout_res,
            tokens_used=total_tokens,
            latency_seconds=round(latency, 4)
        )
