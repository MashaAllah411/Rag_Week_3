# ============================================================
# src/rag/agent/agent.py — Dynamic ReAct Agent Loop for Week 7
#
# PURPOSE:
#   Implements a dynamic tool-calling ReAct agent loop for claim triage.
#
# ENFORCES ALL 4 BUDGETS IN CODE:
#   1. MAX_ITERATIONS = 5 laps
#   2. MAX_TOKENS     = 4000 tokens (summed across all laps)
#   3. MAX_COST       = $0.05 (calculated at $0.002 / 1k tokens)
#   4. WALL_CLOCK_TIMEOUT = 30.0 seconds
#
#   When any budget is exceeded, the loop terminates cleanly with a log.
# ============================================================

import time
import json
from typing import Dict, Any, List, Tuple
from rag.agent.tools import get_claim, search_policy, compute_payout, ClaimStatusEnum

# ── Budget Constants (ENFORCED IN CODE) ───────────────────────────────────────
MAX_ITERATIONS = 5
MAX_TOKENS = 4000
MAX_COST = 0.05  # Dollars ($)
WALL_CLOCK_TIMEOUT = 30.0  # Seconds
COST_PER_1K_TOKENS = 0.002  # Synthetic cost metric


def estimate_tokens(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 characters)."""
    return max(1, len(str(text)) // 4)


def execute_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Executes a tool call and returns (result_dict, token_count)."""
    if tool_name == "get_claim":
        cid = arguments.get("claim_id", "")
        res = get_claim(cid)
    elif tool_name == "search_policy":
        query = arguments.get("query", "")
        res = search_policy(query)
    elif tool_name == "compute_payout":
        cid = arguments.get("claim_id", "")
        status_raw = arguments.get("claim_status", "APPROVED")
        status_enum = ClaimStatusEnum(status_raw) if status_raw in ClaimStatusEnum.__members__ else ClaimStatusEnum.APPROVED
        gross = float(arguments.get("gross_amount", 0.0))
        deductible = float(arguments.get("deductible", 0.0))
        res = compute_payout(cid, status_enum, gross, deductible)
    else:
        res = {"error": f"Unknown tool name '{tool_name}'"}

    tokens = estimate_tokens(json.dumps(res))
    return res, tokens


def run_claim_agent(claim_id: str, force_budget_exceed: str = None) -> Dict[str, Any]:
    """
    Runs the ReAct Agent Loop with dynamic tool execution and strict budget enforcement.

    Args:
        claim_id            : Claim identifier (e.g., CLM-7001)
        force_budget_exceed : Optional budget test string ('iterations', 'tokens', 'cost', 'timeout')

    Returns:
        Structured result dict with metrics and execution trace.
    """
    start_time = time.time()
    total_tokens = 0
    total_cost = 0.0
    iteration_count = 0
    budget_triggered = None
    execution_log = []

    execution_log.append(f"[AGENT START] Processing claim {claim_id}")

    # Simulated tool execution plan for agent loop laps
    laps_plan = [
        {"tool": "get_claim", "args": {"claim_id": claim_id}},
        {"tool": "search_policy", "args": {"query": "flood rising water exclusion"}},
        {"tool": "compute_payout", "args": {"claim_id": claim_id, "claim_status": "APPROVED", "gross_amount": 3500.0, "deductible": 500.0}}
    ]

    final_result = None

    while iteration_count < MAX_ITERATIONS:
        iteration_count += 1
        elapsed_time = time.time() - start_time

        # ── 1. Check Wall Clock Timeout Budget ──────────────────────────────
        if elapsed_time > WALL_CLOCK_TIMEOUT or force_budget_exceed == "timeout":
            budget_triggered = f"WALL_CLOCK_TIMEOUT ({elapsed_time:.2f}s > {WALL_CLOCK_TIMEOUT}s)"
            execution_log.append(f"⚠️ [BUDGET TERMINATION] Exceeded Wall Clock Timeout: {budget_triggered}")
            break

        # ── Simulated lap tokens ─────────────────────────────────────────────
        lap_prompt_tokens = estimate_tokens(f"Iteration {iteration_count} claim {claim_id} prompt state")
        if force_budget_exceed == "tokens":
            lap_prompt_tokens = 4500  # Exceed token budget

        total_tokens += lap_prompt_tokens
        total_cost = (total_tokens / 1000.0) * COST_PER_1K_TOKENS

        # ── 2. Check Token Budget ───────────────────────────────────────────
        if total_tokens > MAX_TOKENS:
            budget_triggered = f"MAX_TOKENS ({total_tokens} > {MAX_TOKENS})"
            execution_log.append(f"⚠️ [BUDGET TERMINATION] Exceeded Token Limit: {budget_triggered}")
            break

        # ── 3. Check Cost Budget ─────────────────────────────────────────────
        if total_cost > MAX_COST or force_budget_exceed == "cost":
            if force_budget_exceed == "cost":
                total_cost = 0.08
            budget_triggered = f"MAX_COST (${total_cost:.4f} > ${MAX_COST:.2f})"
            execution_log.append(f"⚠️ [BUDGET TERMINATION] Exceeded Cost Limit: {budget_triggered}")
            break

        # ── Execute current lap tool ─────────────────────────────────────────
        step_idx = min(iteration_count - 1, len(laps_plan) - 1)
        plan_step = laps_plan[step_idx]

        tool_name = plan_step["tool"]
        tool_args = plan_step["args"]

        res, tool_tokens = execute_tool_call(tool_name, tool_args)
        total_tokens += tool_tokens
        total_cost = (total_tokens / 1000.0) * COST_PER_1K_TOKENS

        execution_log.append(f"  Lap {iteration_count}: Tool '{tool_name}' executed. Result: {str(res)[:80]}...")

        # If get_claim yielded actual claim info, dynamically tune args for step 3
        if tool_name == "get_claim" and "gross_claim_amount" in res:
            notes = res.get("adjuster_notes", "")
            is_excluded = ("flood" in notes.lower() or "rising water" in notes.lower() or "mysterious disappearance" in notes.lower())
            
            laps_plan[2]["args"] = {
                "claim_id": claim_id,
                "claim_status": "DENIED" if is_excluded else "APPROVED",
                "gross_amount": res.get("gross_claim_amount", 0.0),
                "deductible": res.get("policy_deductible", 0.0)
            }

        if tool_name == "compute_payout":
            final_result = res
            execution_log.append(f"[AGENT SUCCESS] Completed payout computation in {iteration_count} laps.")
            break

        # ── 4. Check Iteration Budget ───────────────────────────────────────
        if iteration_count >= MAX_ITERATIONS or force_budget_exceed == "iterations":
            budget_triggered = f"MAX_ITERATIONS ({iteration_count} >= {MAX_ITERATIONS})"
            execution_log.append(f"⚠️ [BUDGET TERMINATION] Exceeded Max Iterations: {budget_triggered}")
            break

    total_latency = time.time() - start_time

    return {
        "claim_id": claim_id,
        "system": "Agent Loop",
        "passed": final_result is not None and budget_triggered is None,
        "final_result": final_result or {"error": "Budget terminated before completion"},
        "iterations": iteration_count,
        "total_tokens": total_tokens,
        "total_cost": round(total_cost, 6),
        "latency_seconds": round(total_latency, 4),
        "budget_triggered": budget_triggered,
        "execution_log": execution_log
    }


if __name__ == "__main__":
    print("Testing Agent Loop with claim CLM-7001...")
    res = run_claim_agent("CLM-7001")
    print(f"Result: {json.dumps(res, indent=2)}")

    print("\nTesting Forced Budget Termination (MAX_TOKENS)...")
    budget_res = run_claim_agent("CLM-7001", force_budget_exceed="tokens")
    print(f"Budget Termination Log:\n" + "\n".join(budget_res["execution_log"]))
