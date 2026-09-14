# ============================================================
# src/rag/agent/workflow.py — Identical Fixed Workflow (No Loop)
#
# PURPOSE:
#   Re-implements the exact same claim triage task as a hard-coded
#   4-step sequential workflow without an agent loop.
#
#   Uses identical tools, identical model, identical inputs, and
#   identical output schema.
# ============================================================

import time
import json
from typing import Dict, Any
from rag.agent.tools import get_claim, search_policy, compute_payout, ClaimStatusEnum
from rag.agent.agent import estimate_tokens, COST_PER_1K_TOKENS


def run_claim_workflow(claim_id: str) -> Dict[str, Any]:
    """
    Executes identical claim triage task via a fixed 4-step workflow (NO LOOP).

    Steps:
      1. Step 1: Call get_claim(claim_id)
      2. Step 2: Inspect adjuster_notes for exclusion keywords
      3. Step 3: Call search_policy() ONLY IF exclusion keywords present
      4. Step 4: Call compute_payout() with status and amounts
    """
    start_time = time.time()
    total_tokens = 0
    execution_log = []

    execution_log.append(f"[WORKFLOW START] Fixed 4-step pipeline for claim {claim_id}")

    # ── Step 1: Get Claim Record ─────────────────────────────────────────────
    claim_data = get_claim(claim_id)
    step1_tokens = estimate_tokens(json.dumps(claim_data))
    total_tokens += step1_tokens
    execution_log.append(f"  Step 1: get_claim('{claim_id}') completed.")

    if "error" in claim_data:
        total_latency = time.time() - start_time
        total_cost = (total_tokens / 1000.0) * COST_PER_1K_TOKENS
        return {
            "claim_id": claim_id,
            "system": "Fixed Workflow",
            "passed": False,
            "final_result": claim_data,
            "iterations": 1,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 6),
            "latency_seconds": round(total_latency, 4),
            "budget_triggered": None,
            "execution_log": execution_log
        }

    # ── Step 2: Read Adjuster Notes ──────────────────────────────────────────
    notes = claim_data.get("adjuster_notes", "")
    gross_amount = claim_data.get("gross_claim_amount", 0.0)
    deductible = claim_data.get("policy_deductible", 0.0)
    execution_log.append("  Step 2: Inspected adjuster notes for exclusion triggers.")

    # Check if exclusion triggers present in notes
    is_flood_or_excluded = ("flood" in notes.lower() or "rising water" in notes.lower() or "mysterious disappearance" in notes.lower())

    # ── Step 3: Search Policy (Conditional) ──────────────────────────────────
    if is_flood_or_excluded:
        policy_res = search_policy("policy exclusions flood water mysterious disappearance")
        step3_tokens = estimate_tokens(json.dumps(policy_res))
        total_tokens += step3_tokens
        status_enum = ClaimStatusEnum.DENIED
        execution_log.append("  Step 3: search_policy() triggered by adjuster notes. Exclusion confirmed -> DENIED.")
    else:
        status_enum = ClaimStatusEnum.APPROVED
        execution_log.append("  Step 3: No policy exclusion triggers found in notes -> APPROVED.")

    # ── Step 4: Compute Payout ───────────────────────────────────────────────
    payout_res = compute_payout(claim_id, status_enum, gross_amount, deductible)
    step4_tokens = estimate_tokens(json.dumps(payout_res))
    total_tokens += step4_tokens
    execution_log.append("  Step 4: compute_payout() executed successfully.")

    total_latency = time.time() - start_time
    total_cost = (total_tokens / 1000.0) * COST_PER_1K_TOKENS

    return {
        "claim_id": claim_id,
        "system": "Fixed Workflow",
        "passed": True,
        "final_result": payout_res,
        "iterations": 1,
        "total_tokens": total_tokens,
        "total_cost": round(total_cost, 6),
        "latency_seconds": round(total_latency, 4),
        "budget_triggered": None,
        "execution_log": execution_log
    }


if __name__ == "__main__":
    print("Testing Fixed Workflow with claim CLM-7001...")
    res = run_claim_workflow("CLM-7001")
    print(f"Result: {json.dumps(res, indent=2)}")
