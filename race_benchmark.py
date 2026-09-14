# ============================================================
# race_benchmark.py — Week 7 Agent vs Workflow Race Benchmark
#
# PURPOSE:
#   Races the dynamic ReAct Agent against the Fixed Workflow over
#   all 10 claim evaluation cases.
#
# OUTPUTS:
#   1. race.csv — Comparative benchmark table with 8 numbers.
#   2. Terminal comparative summary table.
#   3. budget_termination.log — Clean log excerpt demonstrating
#      enforced budget termination.
# ============================================================

import os
import sys
import json
import csv
import numpy as np

# Ensure src and root are in sys.path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./src"))

from rag.agent.agent import run_claim_agent
from rag.agent.workflow import run_claim_workflow

DATASET_PATH = "src/rag/agent/claims_dataset.json"
RACE_CSV_PATH = "race.csv"
BUDGET_LOG_PATH = "budget_termination.log"


def run_race_benchmark():
    print(f"\n{'=' * 75}")
    print("WEEK 7 BENCHMARK RACE — Agent Loop vs. Fixed Workflow")
    print(f"{'=' * 75}\n")

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        claims = json.load(f)

    print(f"Loaded {len(claims)} claim test cases.\n")

    agent_results = []
    workflow_results = []

    print(f"{'Claim ID':10s} | {'System':15s} | {'Passed':7s} | {'Tokens':7s} | {'Cost ($)':10s} | {'Latency (s)':10s}")
    print("-" * 75)

    for c in claims:
        cid = c["claim_id"]

        # Run Agent Loop
        ag_res = run_claim_agent(cid)
        agent_results.append(ag_res)
        print(f"{cid:10s} | {'Agent Loop':15s} | {str(ag_res['passed']):7s} | {ag_res['total_tokens']:7d} | ${ag_res['total_cost']:9.5f} | {ag_res['latency_seconds']:9.4f}s")

        # Run Fixed Workflow
        wf_res = run_claim_workflow(cid)
        workflow_results.append(wf_res)
        print(f"{cid:10s} | {'Fixed Workflow':15s} | {str(wf_res['passed']):7s} | {wf_res['total_tokens']:7d} | ${wf_res['total_cost']:9.5f} | {wf_res['latency_seconds']:9.4f}s")

    # ── Compute Benchmark Metrics ─────────────────────────────────────────────
    # Agent Metrics
    ag_passes = sum(1 for r in agent_results if r["passed"])
    ag_pass_rate = (ag_passes / len(claims)) * 100.0
    ag_latencies = [r["latency_seconds"] for r in agent_results]
    ag_p50_latency = float(np.median(ag_latencies))
    ag_total_tokens = sum(r["total_tokens"] for r in agent_results)
    ag_cost_per_claim = sum(r["total_cost"] for r in agent_results) / len(claims)

    # Workflow Metrics
    wf_passes = sum(1 for r in workflow_results if r["passed"])
    wf_pass_rate = (wf_passes / len(claims)) * 100.0
    wf_latencies = [r["latency_seconds"] for r in workflow_results]
    wf_p50_latency = float(np.median(wf_latencies))
    wf_total_tokens = sum(r["total_tokens"] for r in workflow_results)
    wf_cost_per_claim = sum(r["total_cost"] for r in workflow_results) / len(claims)

    # ── Print Comparative Table (8 Numbers) ──────────────────────────────────
    print(f"\n{'=' * 75}")
    print("RACE BENCHMARK RESULTS (THE 8 NUMBERS)")
    print(f"{'=' * 75}")
    print(f"{'Metric':25s} | {'Agent Loop':20s} | {'Fixed Workflow':20s}")
    print("-" * 75)
    print(f"{'Pass Rate (%)':25s} | {ag_pass_rate:19.1f}% | {wf_pass_rate:19.1f}%")
    print(f"{'P50 Latency (seconds)':25s} | {ag_p50_latency:19.4f}s | {wf_p50_latency:19.4f}s")
    print(f"{'Total Tokens':25s} | {ag_total_tokens:20d} | {wf_total_tokens:20d}")
    print(f"{'Cost Per Claim ($)':25s} | ${ag_cost_per_claim:19.6f} | ${wf_cost_per_claim:19.6f}")
    print(f"{'=' * 75}\n")

    # ── Export to race.csv ───────────────────────────────────────────────────
    with open(RACE_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["System", "Pass_Rate_Pct", "P50_Latency_Sec", "Total_Tokens", "Cost_Per_Claim_USD"])
        writer.writerow(["Agent Loop", f"{ag_pass_rate:.1f}", f"{ag_p50_latency:.4f}", ag_total_tokens, f"{ag_cost_per_claim:.6f}"])
        writer.writerow(["Fixed Workflow", f"{wf_pass_rate:.1f}", f"{wf_p50_latency:.4f}", wf_total_tokens, f"{wf_cost_per_claim:.6f}"])

    print(f"Benchmark comparative results exported to: {RACE_CSV_PATH}")

    # ── Generate Budget Termination Log ──────────────────────────────────────
    print("\nExecuting budget termination test to verify code enforcement...")
    budget_test_run = run_claim_agent("CLM-7002", force_budget_exceed="tokens")
    
    with open(BUDGET_LOG_PATH, "w", encoding="utf-8") as f:
        f.write("============================================================\n")
        f.write("WEEK 7 BUDGET TERMINATION LOG EXCERPT\n")
        f.write("============================================================\n")
        f.write(f"Claim ID         : {budget_test_run['claim_id']}\n")
        f.write(f"Budget Fired     : {budget_test_run['budget_triggered']}\n")
        f.write(f"Passed           : {budget_test_run['passed']}\n")
        f.write(f"Total Iterations : {budget_test_run['iterations']}\n")
        f.write(f"Total Tokens     : {budget_test_run['total_tokens']}\n")
        f.write(f"Total Cost ($)   : ${budget_test_run['total_cost']:.6f}\n")
        f.write("------------------------------------------------------------\n")
        f.write("EXECUTION TRACE LOG:\n")
        for log_line in budget_test_run["execution_log"]:
            f.write(f"  {log_line}\n")
        f.write("============================================================\n")

    print(f"Budget termination log saved to: {BUDGET_LOG_PATH}\n")


if __name__ == "__main__":
    run_race_benchmark()
