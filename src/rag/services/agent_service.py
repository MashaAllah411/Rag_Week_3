"""
agent_service.py

Service layer orchestrating:
- ReAct Agent loop with 4 budget enforcements
- Fixed 4-step workflow comparison
- Trajectory evaluation (tool sequence, argument validity, step efficiency)
- Multi-claim race benchmark
"""
from __future__ import annotations
import json
import os
import time
from typing import Dict, Any, List, Optional

from rag.agent.agent import run_claim_agent, MAX_ITERATIONS, MAX_TOKENS, MAX_COST, WALL_CLOCK_TIMEOUT
from rag.agent.workflow import run_claim_workflow
from rag.agent.tools import MOCK_CLAIMS_DB
from rag.agent.trajectory_eval import evaluate_trajectory_run, EXPECTED_TRAJECTORIES


def get_available_claims() -> List[Dict[str, Any]]:
    """Return all mock claims available for triage."""
    claims = []
    for cid, data in MOCK_CLAIMS_DB.items():
        spec = EXPECTED_TRAJECTORIES.get(cid, {})
        claims.append({
            "claim_id": cid,
            "claimant": data.get("claimant", ""),
            "incident_type": data.get("incident_type", ""),
            "gross_claim_amount": data.get("gross_claim_amount", 0.0),
            "policy_deductible": data.get("policy_deductible", 0.0),
            "adjuster_notes": data.get("adjuster_notes", ""),
            "requires_policy_search": spec.get("requires_policy_search", False),
            "optimal_steps": spec.get("optimal_steps", 2)
        })
    return claims


def triage_claim(
    claim_id: str,
    system_type: str = "agent_loop",
    force_budget_exceed: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run claim triage using either the dynamic ReAct Agent Loop or Fixed Workflow.
    Evaluates trajectory metrics on completion.
    """
    if system_type == "fixed_workflow":
        res = run_claim_workflow(claim_id)
    else:
        res = run_claim_agent(claim_id, force_budget_exceed=force_budget_exceed)

    # Evaluate trajectory
    trajectory_eval = evaluate_trajectory_run(res)
    res["trajectory_evaluation"] = trajectory_eval
    res["budgets"] = {
        "max_iterations": MAX_ITERATIONS,
        "max_tokens": MAX_TOKENS,
        "max_cost_usd": MAX_COST,
        "timeout_seconds": WALL_CLOCK_TIMEOUT
    }
    return res


def run_agent_benchmark(claims_subset: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Race ReAct Agent vs Fixed Workflow across claims.
    Outputs comparative metrics: pass rate, latency, token consumption, cost, and budget termination.
    """
    target_claims = claims_subset or list(MOCK_CLAIMS_DB.keys())

    agent_results = []
    workflow_results = []

    for cid in target_claims:
        a_res = triage_claim(cid, system_type="agent_loop")
        w_res = triage_claim(cid, system_type="fixed_workflow")
        agent_results.append(a_res)
        workflow_results.append(w_res)

    def _aggregate(results: List[Dict[str, Any]], name: str) -> Dict[str, Any]:
        total = len(results)
        passed = sum(1 for r in results if r.get("passed", False))
        latencies = [r.get("latency_seconds", 0.0) for r in results]
        tokens = sum(r.get("total_tokens", 0) for r in results)
        costs = sum(r.get("total_cost", 0.0) for r in results)
        latencies.sort()
        p50_lat = latencies[len(latencies) // 2] if latencies else 0.0

        return {
            "system": name,
            "total_claims": total,
            "passed": passed,
            "pass_rate_pct": round((passed / total) * 100.0, 1) if total else 0.0,
            "total_tokens": tokens,
            "avg_tokens_per_claim": round(tokens / total, 1) if total else 0,
            "total_cost_usd": round(costs, 6),
            "p50_latency_seconds": round(p50_lat, 4),
            "results": results
        }

    # Run budget stress test
    budget_test = run_claim_agent("CLM-7001", force_budget_exceed="tokens")

    return {
        "agent": _aggregate(agent_results, "ReAct Agent Loop"),
        "workflow": _aggregate(workflow_results, "Fixed 4-Step Workflow"),
        "budget_stress_test": budget_test
    }
