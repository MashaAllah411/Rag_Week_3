"""Failure -> test loop (Week 11): production failures kept as permanent regression cases.

The support drill (observability/support_drill.py) plants one bad answer:
CLM-FAIL-7701 - a claim approved although adjuster notes showed rising lake water,
which Section 5.2 excludes. That failure is encoded here as data so the same cases run
from pytest (tests/test_failure_loop_regression.py) and from the UI.
"""
from __future__ import annotations

from typing import Any, Dict, List

from rag.agent.tools import ClaimStatusEnum, compute_payout

FLOOD_TRIGGERS = [
    "rising lake water",
    "rising water",
    "surface runoff",
    "torrential rainfall runoff",
    "flood",
    "inundation",
    "overflow of inland waters",
]


def check_exclusion_guardrail(notes: str, incident_type: str) -> dict:
    """Deterministic Section 5.2 check (flood and rising-water perils)."""
    text_lower = f"{notes} {incident_type}".lower()

    if any(trigger in text_lower for trigger in FLOOD_TRIGGERS):
        return {
            "status": ClaimStatusEnum.DENIED.value,
            "is_excluded": True,
            "exclusion_clause": "Section 5.2",
            "reasoning": "Damage caused by rising surface waters, lake overflow, or runoff is strictly excluded under Section 5.2.",
        }

    if "burst pipe" in text_lower or "pipe burst" in text_lower:
        return {
            "status": ClaimStatusEnum.APPROVED.value,
            "is_excluded": False,
            "exclusion_clause": None,
            "reasoning": "Sudden accidental plumbing failure is covered under standard perils.",
        }

    return {
        "status": ClaimStatusEnum.UNDER_INVESTIGATION.value,
        "is_excluded": False,
        "exclusion_clause": None,
        "reasoning": "Further investigation required.",
    }


REGRESSION_CASES: List[Dict[str, Any]] = [
    {
        "id": "CLM-FAIL-7701",
        "title": "Planted drill failure: rising lake water must be DENIED",
        "origin": "Week 11 support drill (trace tr_drill_exclusion_7701)",
        "notes": ("Heavy torrential rainfall caused rising lake waters and surface runoff "
                  "to flood the finished basement with 18 inches of standing water."),
        "incident_type": "Basement Water Damage",
        "gross": 15500.0, "deductible": 1000.0,
        "expect_status": "DENIED", "expect_clause": "Section 5.2", "expect_net": 0.0,
    },
    {
        "id": "VARIANT-RUNOFF",
        "title": "Wording variation: surface runoff must be DENIED",
        "origin": "Variation of CLM-FAIL-7701",
        "notes": "Torrential rainfall runoff accumulated against foundation and seeped through window well.",
        "incident_type": "Heavy Rain Seepage",
        "gross": 6000.0, "deductible": 500.0,
        "expect_status": "DENIED", "expect_clause": "Section 5.2", "expect_net": 0.0,
    },
    {
        "id": "GUARD-PIPE-BURST",
        "title": "Over-blocking guard: a covered pipe burst must be APPROVED",
        "origin": "False-positive check",
        "notes": "Cold snap caused sudden burst pipe in ceiling; fresh water poured into living room.",
        "incident_type": "Burst Pipe",
        "gross": 4000.0, "deductible": 500.0,
        "expect_status": "APPROVED", "expect_clause": None, "expect_net": 3500.0,
    },
]


def run_regression_case(case: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate one case; returns the observed values and a pass/fail with reasons."""
    verdict = check_exclusion_guardrail(case["notes"], case["incident_type"])
    payout = compute_payout(case["id"], ClaimStatusEnum(verdict["status"]), case["gross"], case["deductible"])
    problems = []
    if verdict["status"] != case["expect_status"]:
        problems.append(f"status {verdict['status']} != expected {case['expect_status']}")
    if verdict["exclusion_clause"] != case["expect_clause"]:
        problems.append(f"clause {verdict['exclusion_clause']} != expected {case['expect_clause']}")
    if payout["net_payable"] != case["expect_net"]:
        problems.append(f"net payable {payout['net_payable']} != expected {case['expect_net']}")
    return {
        "id": case["id"], "title": case["title"], "origin": case["origin"],
        "passed": not problems, "problems": problems,
        "observed": {"status": verdict["status"], "clause": verdict["exclusion_clause"],
                     "net_payable": payout["net_payable"], "reasoning": verdict["reasoning"]},
    }


def run_all_regression_cases() -> Dict[str, Any]:
    results = [run_regression_case(c) for c in REGRESSION_CASES]
    return {"passed": sum(r["passed"] for r in results), "total": len(results), "results": results}
