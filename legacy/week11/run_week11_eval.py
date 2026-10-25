# ============================================================
# run_week11_eval.py — Week 11 Practical Evaluation Suite
#
# PURPOSE:
#   Validates all Week 11 Production & Capstone Deliverables (Track D):
#     1. Per-request logging with step-by-step time & cost per span
#     2. The Support Drill: Locate planted bad answer from vague complaint
#     3. Measured cost-per-request improvement with semantic caching
#     4. The Failure → Test Loop: Verify regression test guards against failure
# ============================================================

from __future__ import annotations
import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./src"))

from rag.observability.tracer import ProductionTracer
from rag.observability.support_drill import (
    generate_production_traces,
    diagnose_complaint,
    PLANTED_TRACE_ID,
    PLANTED_CLAIM_ID,
    DRILL_TRACES_PATH
)
from rag.cache.semantic_cache import benchmark_cost_optimization
from tests.test_failure_loop_regression import check_exclusion_guardrail

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def run_week11_evaluation():
    print("=" * 75)
    print("WEEK 11 PRACTICAL EVALUATION SUITE -- Track D: Insurance Claims")
    print("Production: Observability, Cost & the Failure -> Test Loop")
    print("=" * 75 + "\n")

    # ──────────────────────────────────────────────────────────────────────────
    # 1. PER-REQUEST LOGGING & STEP-BY-STEP SPANS
    # ──────────────────────────────────────────────────────────────────────────
    print("1. PER-REQUEST OBSERVABILITY & SPAN-LEVEL COST/TIME LOGGING")
    print("-" * 75)
    print("  Generating 100 realistic production traces with discrete spans...")
    generate_production_traces(DRILL_TRACES_PATH, count=100)

    tracer = ProductionTracer(DRILL_TRACES_PATH)
    traces = tracer.load_all_traces()
    print(f"  Total production traces loaded: {len(traces)}")

    # Inspect a representative trace
    sample_trace = traces[0]
    print(f"  Sample Request Trace ID : {sample_trace['trace_id']}")
    print(f"  Request ID / Claim ID   : {sample_trace['request_id']}")
    print(f"  Total Duration (ms)     : {sample_trace['total_duration_ms']} ms")
    print(f"  Total Cost (USD)        : ${sample_trace['total_cost_usd']:.6f}")
    print("  Granular Step Breakdown (Time & Cost per Step):")

    for idx, step in enumerate(sample_trace.get("step_breakdown", []), 1):
        print(f"    Step {idx}: {step['step']:<32} | {step['duration_ms']:>6.2f} ms | {step['tokens']:>4} tokens | ${step['cost_usd']:.6f}")

    assert len(sample_trace.get("spans", [])) > 0, "Trace must contain discrete spans"
    assert sample_trace["total_cost_usd"] > 0, "Cost must be calculated per trace"
    print("  Step-Level Observability Check: [PASS]\n")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. THE SUPPORT DRILL (TRACK D: INSURANCE CLAIMS)
    # ──────────────────────────────────────────────────────────────────────────
    print("2. THE SUPPORT DRILL (FINDING BAD ANSWER FROM VAGUE COMPLAINT)")
    print("-" * 75)
    vague_complaint = (
        "A senior supervisor filed an audit flag: Yesterday a customer's basement flood "
        "claim was improperly approved for $14,500 despite adjuster notes citing rising "
        "lake water and storm runoff, directly violating our Section 5.2 exclusion clause."
    )
    print(f"  Incoming Complaint: \"{vague_complaint}\"\n")
    print("  Searching production trace logs for symptoms...")

    diagnosis = diagnose_complaint(vague_complaint, DRILL_TRACES_PATH)
    suspect = diagnosis.get("primary_suspect")

    assert suspect is not None, "Support drill failed to locate bad answer"
    assert suspect["claim_id"] == PLANTED_CLAIM_ID, f"Expected {PLANTED_CLAIM_ID}, got {suspect['claim_id']}"
    assert suspect["trace_id"] == PLANTED_TRACE_ID, f"Expected {PLANTED_TRACE_ID}, got {suspect['trace_id']}"

    print(f"  [DISCOVERED BAD ANSWER TRACE]")
    print(f"    Trace ID       : {suspect['trace_id']}")
    print(f"    Claim ID       : {suspect['claim_id']}")
    print(f"    Wrong Payout   : ${suspect['net_payable']:,.2f} ({suspect['final_status']})")
    print(f"    Faulty Span    : {suspect['faulty_span_name']}")
    print(f"    Span Error     : {suspect['faulty_span_error']}")
    print(f"    Root Cause     : {suspect['root_cause']}")
    print(f"    Remediation    : {suspect['remediation']}")
    print("  Support Drill Resolution: [PASS]\n")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. MEASURED COST-PER-REQUEST IMPROVEMENT
    # ──────────────────────────────────────────────────────────────────────────
    print("3. MEASURED COST-PER-REQUEST IMPROVEMENT (SEMANTIC CACHING & ROUTING)")
    print("-" * 75)
    print("  Benchmarking 20 incoming production-like claim queries...")
    cost_bench = benchmark_cost_optimization(num_queries=20)

    print(f"  Total Queries Processed : {cost_bench['total_queries']}")
    print(f"  Semantic Cache Hits     : {cost_bench['cache_hits']} ({cost_bench['hit_rate_pct']}%)")
    print(f"  Baseline Avg Cost/Query : ${cost_bench['baseline']['avg_cost_per_request']:.6f} ({cost_bench['baseline']['avg_latency_ms']} ms)")
    print(f"  Optimized Avg Cost/Query: ${cost_bench['optimized']['avg_cost_per_request']:.6f} ({cost_bench['optimized']['avg_latency_ms']} ms)")
    print(f"  Cost Reduction (%)      : {cost_bench['improvements']['cost_reduction_pct']}% SAVINGS")
    print(f"  Latency Reduction (%)   : {cost_bench['improvements']['latency_reduction_pct']}% FASTER")

    assert cost_bench["improvements"]["cost_reduction_pct"] >= 35.0, "Cost savings must be at least 35%"
    print("  Cost Optimization Benchmark: [PASS]\n")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. FAILURE -> TEST LOOP (PERMANENT REGRESSION TEST)
    # ──────────────────────────────────────────────────────────────────────────
    print("4. THE FAILURE -> TEST LOOP (PERMANENT REGRESSION TEST)")
    print("-" * 75)
    print("  Testing that the Support Drill failure (CLM-FAIL-7701) is permanently guarded...")

    # Case 1: Exact failure scenario
    planted_notes = "Heavy torrential rainfall caused rising lake waters and surface runoff to flood the finished basement."
    res1 = check_exclusion_guardrail(planted_notes, "Basement Water Damage")
    assert res1["status"] == "DENIED"
    assert res1["is_excluded"] is True
    assert res1["exclusion_clause"] == "Section 5.2"
    print(f"  Case 1 (CLM-FAIL-7701 Flooding) -> Status: {res1['status']} | Exclusion: {res1['exclusion_clause']} [PASS]")

    # Case 2: Surface runoff variation
    res2 = check_exclusion_guardrail("Torrential rainfall runoff accumulated against wall", "Heavy Rain Seepage")
    assert res2["status"] == "DENIED"
    print(f"  Case 2 (Surface Runoff Variant) -> Status: {res2['status']} | Exclusion: {res2['exclusion_clause']} [PASS]")

    # Case 3: Legitimate covered burst pipe (no false positive)
    res3 = check_exclusion_guardrail("Cold snap caused sudden burst pipe in ceiling", "Burst Pipe")
    assert res3["status"] == "APPROVED"
    assert res3["is_excluded"] is False
    print(f"  Case 3 (Legitimate Burst Pipe)  -> Status: {res3['status']} | Is Excluded: {res3['is_excluded']} [PASS]")

    print("  Regression Guardrail Check: [PASS]\n")

    # ──────────────────────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────────────────────
    print("=" * 75)
    print("ALL WEEK 11 SUBMISSION DELIVERABLES SUCCESSFULLY VERIFIED [100/100]")
    print("=" * 75)


if __name__ == "__main__":
    run_week11_evaluation()
