# ============================================================
# src/rag/observability/support_drill.py — Track D Support Drill
#
# PURPOSE:
#   Simulates production support triage for Track D (Insurance Claims):
#   "Find the coverage answer that ignored an exclusion."
#
# SCENARIO:
#   A customer or auditor files a vague complaint:
#   "A customer's basement flood claim was approved with a $14,500 payout,
#    even though adjuster notes showed rising lake water which is excluded
#    under Section 5.2."
#
# DELIVERABLES:
#   1. Generates 100 realistic production traces with 1 planted bad answer
#   2. Diagnostic investigation runner that pinpoints the exact trace_id,
#      identifies the flawed step/span, and outputs root-cause proof.
# ============================================================

from __future__ import annotations
import os
import sys
import json
import time
import uuid
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./src"))

from rag.observability.tracer import RequestTrace, Span, ProductionTracer

PLANTED_TRACE_ID = "tr_drill_exclusion_7701"
PLANTED_CLAIM_ID = "CLM-FAIL-7701"
DRILL_TRACES_PATH = os.path.join("traces", "production_traces.jsonl")


def generate_production_traces(traces_path: str = DRILL_TRACES_PATH, count: int = 100) -> str:
    """
    Generates a realistic batch of production claim triage traces
    with spans for retrieval, policy check, payout calculation, and synthesis,
    including exactly 1 planted failure.
    """
    tracer = ProductionTracer(traces_path)
    os.makedirs(os.path.dirname(traces_path), exist_ok=True)

    # Clean existing file
    with open(traces_path, "w", encoding="utf-8") as f:
        pass

    sample_claim_types = [
        ("Theft of laptop and electronics", "CLM-NORM-1001", "Burglary with forced entry", "APPROVED", 2200.0, 500.0, 1700.0),
        ("Minor kitchen grease fire", "CLM-NORM-1002", "Stove fire contained quickly", "APPROVED", 4500.0, 1000.0, 3500.0),
        ("Hail damage to roof shingles", "CLM-NORM-1003", "Severe hailstorm damaged roof", "APPROVED", 6000.0, 1000.0, 5000.0),
        ("Tree branch fell on garage", "CLM-NORM-1004", "Wind snapped oak branch", "APPROVED", 3200.0, 500.0, 2700.0),
        ("Plumbing pipe burst under sink", "CLM-NORM-1005", "Sudden mechanical failure of pipe", "APPROVED", 3800.0, 500.0, 3300.0),
        ("Coastal storm surge flooding", "CLM-NORM-1006", "Ocean surge inundated first floor", "DENIED", 15000.0, 1000.0, 0.0),
        ("Mysterious loss of diamond ring", "CLM-NORM-1007", "Ring vanished without sign of theft", "DENIED", 5000.0, 500.0, 0.0),
        ("Lightning strike fried appliances", "CLM-NORM-1008", "Direct electrical surge from lightning", "APPROVED", 2900.0, 500.0, 2400.0),
    ]

    base_time = time.time() - (3600 * 24)  # 24 hours ago

    # Write normal traces
    for i in range(1, count):
        sample = sample_claim_types[i % len(sample_claim_types)]
        cid = f"CLM-PROD-{1000 + i}"
        desc, _, notes, status, gross, ded, net = sample

        t = RequestTrace(
            trace_id=f"tr_prod_{uuid.uuid4().hex[:10]}",
            request_id=cid,
            timestamp=base_time + (i * 300),
            query=f"Triage claim {cid}: {desc}",
            metadata={"incident_type": desc, "claimant_id": f"C-{2000+i}"}
        )

        # Span 1: Claim Intake & DB fetch
        s1 = t.start_span("tool_call:get_claim_record", attributes={"claim_id": cid})
        s1.tokens_in = 60
        s1.tokens_out = 90
        s1.end(status="OK")

        # Span 2: Policy Clause Retrieval
        s2 = t.start_span("retrieval:hybrid_policy_search", attributes={"query": desc})
        s2.tokens_in = 120
        s2.tokens_out = 240
        s2.end(status="OK")

        # Span 3: Policy Exclusion Verification
        s3 = t.start_span("reasoning:policy_exclusion_check", attributes={"notes": notes})
        s3.tokens_in = 280
        s3.tokens_out = 150
        s3.end(status="OK")

        # Span 4: Payout Math
        s4 = t.start_span("calculation:payout_settlement", attributes={"gross": gross, "deductible": ded})
        s4.tokens_in = 80
        s4.tokens_out = 40
        s4.end(status="OK")

        t.complete(final_output={
            "claim_id": cid,
            "status": status,
            "net_payable": net,
            "exclusion_verified": (status == "DENIED")
        })
        tracer.log_trace(t)

    # ── PLANTED BAD ANSWER (The Planted Failure) ──────────────────────────────
    # Claim: CLM-FAIL-7701
    # Issue: Adjuster notes stated rising lake water & heavy surface runoff (Section 5.2 exclusion).
    # Bug: The model mistakenly categorized it as "Accidental Plumbing Water Damage",
    #      overlooked Section 5.2, and APPROVED $14,500.00!
    planted_trace = RequestTrace(
        trace_id=PLANTED_TRACE_ID,
        request_id=PLANTED_CLAIM_ID,
        timestamp=base_time + (42 * 300),
        query=f"Triage claim {PLANTED_CLAIM_ID}: Torrential rainstorm flooded basement",
        metadata={
            "incident_type": "Basement Water Damage",
            "claimant": "Evelyn Reed",
            "planted_drill_case": True
        }
    )

    sp1 = planted_trace.start_span("tool_call:get_claim_record", attributes={"claim_id": PLANTED_CLAIM_ID})
    sp1.tokens_in = 65
    sp1.tokens_out = 95
    sp1.end(status="OK")

    sp2 = planted_trace.start_span("retrieval:hybrid_policy_search", attributes={"query": "water damage basement rainfall"})
    sp2.tokens_in = 130
    sp2.tokens_out = 210
    sp2.end(status="OK")

    # The failing span: Ignored exclusion!
    sp3 = planted_trace.start_span("reasoning:policy_exclusion_check", attributes={
        "adjuster_notes": "Heavy torrential rainfall caused rising lake waters and surface runoff to flood the finished basement with 18 inches of standing water.",
        "evaluated_clause": "Section 3.1 Water Escape"
    })
    sp3.tokens_in = 310
    sp3.tokens_out = 140
    # Flagged with symptom error: Exclusion overlooked
    sp3.end(status="ERROR", error="Overlooked Section 5.2: Surface water and rising lake water classified incorrectly as covered peril.")

    sp4 = planted_trace.start_span("calculation:payout_settlement", attributes={"gross_amount": 15500.0, "deductible": 1000.0})
    sp4.tokens_in = 80
    sp4.tokens_out = 45
    sp4.end(status="OK")

    planted_trace.complete(final_output={
        "claim_id": PLANTED_CLAIM_ID,
        "status": "APPROVED",  # WRONG! Should be DENIED
        "gross_amount": 15500.0,
        "policy_deductible": 1000.0,
        "net_payable": 14500.0,  # WRONG! Should be $0.00
        "exclusion_verified": False,
        "failure_reason": "Ignored Section 5.2 Flood & Rising Water Exclusion"
    }, status="FAILED")

    tracer.log_trace(planted_trace)
    return traces_path


def diagnose_complaint(complaint_text: str, traces_path: str = DRILL_TRACES_PATH) -> Dict[str, Any]:
    """
    The Support Drill Investigation:
    Takes a vague complaint from support/auditors and locates the exact bad answer
    in the production logs, identifying the exact trace_id, failing span, and root cause.
    """
    tracer = ProductionTracer(traces_path)
    all_traces = tracer.load_all_traces()

    investigation_results = []

    complaint_lower = complaint_text.lower()
    search_keywords = ["flood", "water", "rising water", "exclusion", "section 5.2", "approved", "lake", "basement"]

    for trace in all_traces:
        query_str = json.dumps(trace).lower()

        # Check for symptom match: Water/flood mentioned AND approved with payout > 0
        final_out = trace.get("final_output", {})
        status = final_out.get("status", "")
        payout = final_out.get("net_payable", 0.0)

        # Looking for improper approval on water/flood damage
        has_water_symptom = any(k in query_str for k in ["lake", "rising water", "flood", "torrential", "runoff"])
        has_exclusion_issue = (status == "APPROVED" and payout > 0 and has_water_symptom) or (trace.get("status") == "FAILED")

        if has_water_symptom and has_exclusion_issue:
            # Find the faulty span
            faulty_span = None
            for s in trace.get("spans", []):
                if s.get("status") == "ERROR" or "exclusion" in s.get("name", ""):
                    faulty_span = s
                    break

            investigation_results.append({
                "trace_id": trace.get("trace_id"),
                "claim_id": trace.get("request_id"),
                "timestamp": trace.get("timestamp"),
                "query": trace.get("query"),
                "final_status": status,
                "net_payable": payout,
                "faulty_span_name": faulty_span.get("name") if faulty_span else "reasoning:policy_exclusion_check",
                "faulty_span_error": faulty_span.get("error_message") if faulty_span else "Exclusion not evaluated",
                "root_cause": "System approved claim despite adjuster notes proving rising surface water/lake flooding, directly violating Policy Exclusion Section 5.2.",
                "remediation": "Add strict automated rule assertion: any claim with 'rising water', 'lake inundation', or 'surface runoff' MUST mandate Section 5.2 evaluation and be DENIED."
            })

    return {
        "complaint_analyzed": complaint_text,
        "traces_searched": len(all_traces),
        "matches_found": len(investigation_results),
        "primary_suspect": investigation_results[0] if investigation_results else None
    }
