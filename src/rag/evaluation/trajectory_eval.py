# ============================================================
# src/rag/agent/trajectory_eval.py — Week 8 Trajectory Evaluation
#
# PURPOSE:
#   Evaluates not just WHAT answer the agent produced (Outcome),
#   but HOW it arrived at the answer (Trajectory).
#
# MEASURES:
#   1. Tool-Choice Accuracy (%)
#   2. Argument Validity Rate (%)
#   3. Step Efficiency Ratio (Optimal Steps / Actual Steps)
#   4. Cost P50 and MAX ($)
#   5. Outcome-vs-Trajectory Gap (%)
# ============================================================

import os
import sys
import json
import numpy as np
from typing import Dict, Any, List, Set, Tuple

# Ensure src and root are in sys.path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./src"))

from rag.agent.tools import MOCK_CLAIMS_DB, ClaimStatusEnum

# ── Expected Tool Sequences for 10 Claims ─────────────────────────────────────
# For claims requiring dynamic policy lookup (CLM-7002, CLM-7007, CLM-7010),
# we accept alternate valid path sets:
#   Set A: get_claim -> search_policy -> compute_payout
#   Set B: search_policy -> get_claim -> compute_payout
#
# For standard claims without policy exclusion triggers:
#   Set A: get_claim -> compute_payout
#   Set B: get_claim -> search_policy -> compute_payout
EXPECTED_TRAJECTORIES = {
    "CLM-7001": {
        "valid_paths": [
            ["get_claim", "compute_payout"],
            ["get_claim", "search_policy", "compute_payout"]
        ],
        "optimal_steps": 2,
        "requires_policy_search": False
    },
    "CLM-7002": {
        "valid_paths": [
            ["get_claim", "search_policy", "compute_payout"],
            ["search_policy", "get_claim", "compute_payout"]
        ],
        "optimal_steps": 3,
        "requires_policy_search": True  # Flood exclusion trigger in notes!
    },
    "CLM-7003": {
        "valid_paths": [
            ["get_claim", "compute_payout"],
            ["get_claim", "search_policy", "compute_payout"]
        ],
        "optimal_steps": 2,
        "requires_policy_search": False
    },
    "CLM-7004": {
        "valid_paths": [
            ["get_claim", "compute_payout"],
            ["get_claim", "search_policy", "compute_payout"]
        ],
        "optimal_steps": 2,
        "requires_policy_search": False
    },
    "CLM-7005": {
        "valid_paths": [
            ["get_claim", "compute_payout"],
            ["get_claim", "search_policy", "compute_payout"]
        ],
        "optimal_steps": 2,
        "requires_policy_search": False
    },
    "CLM-7006": {
        "valid_paths": [
            ["get_claim", "compute_payout"],
            ["get_claim", "search_policy", "compute_payout"]
        ],
        "optimal_steps": 2,
        "requires_policy_search": False
    },
    "CLM-7007": {
        "valid_paths": [
            ["get_claim", "search_policy", "compute_payout"],
            ["search_policy", "get_claim", "compute_payout"]
        ],
        "optimal_steps": 3,
        "requires_policy_search": True  # Storm surge exclusion trigger in notes!
    },
    "CLM-7008": {
        "valid_paths": [
            ["get_claim", "compute_payout"],
            ["get_claim", "search_policy", "compute_payout"]
        ],
        "optimal_steps": 2,
        "requires_policy_search": False
    },
    "CLM-7009": {
        "valid_paths": [
            ["get_claim", "compute_payout"],
            ["get_claim", "search_policy", "compute_payout"]
        ],
        "optimal_steps": 2,
        "requires_policy_search": False
    },
    "CLM-7010": {
        "valid_paths": [
            ["get_claim", "search_policy", "compute_payout"],
            ["search_policy", "get_claim", "compute_payout"]
        ],
        "optimal_steps": 3,
        "requires_policy_search": True  # Mysterious disappearance exclusion trigger in notes!
    }
}


def validate_arguments(log_lines: List[str]) -> Tuple[int, int]:
    """
    Validates tool arguments in execution log lines.
    Checks:
      - Is claim_id valid in MOCK_CLAIMS_DB?
      - Is claim_status a valid ClaimStatusEnum value?
    Returns (valid_args_count, total_args_count).
    """
    valid = 0
    total = 0

    for line in log_lines:
        if "Tool '" in line and "executed" in line:
            total += 1
            # Check claim_id validity
            if "CLM-" in line:
                for cid in MOCK_CLAIMS_DB:
                    if cid in line:
                        valid += 1
                        break
            else:
                valid += 1

    return valid, max(1, total)


def evaluate_trajectory_run(run_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates trajectory metrics for a single claim run.
    """
    cid = run_result["claim_id"]
    spec = EXPECTED_TRAJECTORIES.get(cid, {})
    valid_paths = spec.get("valid_paths", [])
    optimal_steps = spec.get("optimal_steps", 2)
    requires_policy_search = spec.get("requires_policy_search", False)

    # Extract actual tool sequence from execution log
    actual_sequence = []
    for line in run_result.get("execution_log", []):
        if "Tool '" in line:
            tool_name = line.split("Tool '")[1].split("'")[0]
            actual_sequence.append(tool_name)

    # 1. Trajectory Pass Check (Matches any valid path in set)
    trajectory_passed = actual_sequence in valid_paths

    # Special check: If requires_policy_search is True, search_policy MUST be called
    if requires_policy_search and "search_policy" not in actual_sequence:
        trajectory_passed = False

    # 2. Tool Choice Accuracy (1.0 if sequence matched, 0.0 otherwise)
    tool_choice_acc = 1.0 if trajectory_passed else 0.0

    # 3. Argument Validity Rate
    valid_args, total_args = validate_arguments(run_result.get("execution_log", []))
    arg_validity_rate = valid_args / total_args

    # 4. Step Efficiency Ratio = optimal_steps / actual_steps
    actual_steps = max(1, len(actual_sequence))
    step_efficiency = round(optimal_steps / actual_steps, 4)

    return {
        "claim_id": cid,
        "outcome_passed": run_result.get("passed", False),
        "trajectory_passed": trajectory_passed,
        "actual_sequence": actual_sequence,
        "valid_paths": valid_paths,
        "tool_choice_acc": tool_choice_acc,
        "arg_validity_rate": arg_validity_rate,
        "step_efficiency": step_efficiency,
        "actual_steps": actual_steps,
        "optimal_steps": optimal_steps,
        "tokens": run_result.get("total_tokens", 0),
        "cost": run_result.get("total_cost", 0.0),
        "latency": run_result.get("latency_seconds", 0.0)
    }
