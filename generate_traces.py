# ============================================================
# generate_traces.py — Synthetic Trace Generator
#
# PURPOSE:
#   Generates 50+ realistic traces in traces/traces.jsonl across
#   a broad variety of queries (standard, edge cases, PII queries,
#   vague queries, out-of-scope requests, and policy edge cases).
# ============================================================

import sys
import os

# Add root and src to sys.path so imports work seamlessly
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./src"))

from tracer import log_trace
from rag.scripts.main_rag import run_master_rag

REALISTIC_QUERIES = [
    # ── Category A: Standard HR Policies ─────────────────────
    "What are the official working hours for GESCI staff?",
    "Are flexible working hours a guaranteed right for employees?",
    "What is the standard annual leave entitlement for full-time staff?",
    "How many days of sick leave is a staff member entitled to per year?",
    "What is the length of the probationary period for new staff?",
    "How long is the maternity leave entitlement with full pay?",
    "What is the required notice period for resignation?",
    "Can an employee take uncertified sick leave, and for how many days?",
    "What happens if an employee is recalled from annual leave due to an emergency?",
    "What is the paternity leave entitlement for male staff members?",

    # ── Category B: Specific / Edge-Case Policy Queries ──────
    "What is the company policy on compassionate leave for family bereavement?",
    "How are public holidays and company holidays handled if they fall on weekends?",
    "Can accrued annual leave be used to serve out a resignation notice period?",
    "What is the process for temporary responsibility allowance when covering a higher grade post?",
    "What are the grounds for summary dismissal under the disciplinary policy?",
    "Is there medical insurance coverage during the 6-month probation period?",
    "What is the policy for carrying forward unused annual leave into the next year?",
    "How is overtime compensated for work performed during weekends?",
    "What happens if an employee is absent without authorization for 3 consecutive days?",
    "What is the retirement age policy for full-time staff?",

    # ── Category C: Queries Containing Explicit PII (Redaction Test) ────────
    "Claimant John Doe with CLM-12981 asks what the notice period for resignation is.",
    "Employee Sarah Jenkins (ID EMP-4412, email sarah.j@gesci.org) needs clarification on maternity leave.",
    "Mr. Robert Taylor from Finance (Phone 555-019-2834) wants to know if flexible hours are allowed.",
    "Claimant Mary Smith (CLM-99823) inquires about sick leave entitlement without doctor note.",
    "Employee David Miller (EMP-8821) is asking how many annual leave days accrue per month.",
    "Claimant Alice Johnson (CLM-44102, email alice.j@company.org) asks about paternity leave.",
    "Employee Bob Smith (ID EMP-3321) asks if probation can be extended beyond 6 months.",
    "Claimant Michael Brown (CLM-55912) asks what happens upon separation from service.",
    "Employee Emma Wilson (EMP-1102) inquires about compassionate leave days.",
    "Claimant Jane Doe (CLM-77123) asks about temporary responsibility allowance.",

    # ── Category D: Short / Vague / Messy Queries ────────────
    "timing?",
    "leave?",
    "resignation?",
    "probation?",
    "sick note?",
    "maternity?",
    "notice?",
    "holiday?",
    "overtime?",
    "pension?",

    # ── Category E: Out-of-Scope / Misaligned Queries ────────
    "What is the reimbursement policy for private car auto insurance claims?",
    "Does GESCI cover dental insurance and cosmetic surgery for dependents?",
    "What is the coverage limit for commercial flood insurance under Form 2012?",
    "How do I submit a claim for stolen personal pet property?",
    "What is the corporate discount rate for international airline flight bookings?",
    "Does the policy cover home office electricity and internet bills?",
    "What is the claim payout limit for third-party property liability under Edition 2010?",
    "What is the procedure for requesting an interest-free personal loan?",
    "How does the policy handle international relocation shipping expenses?",
    "What is the company stock option vesting schedule for junior managers?"
]


def generate_all_traces():
    print(f"\n[GENERATOR] Generating {len(REALISTIC_QUERIES)} realistic traces into traces/traces.jsonl...\n")
    
    for idx, query in enumerate(REALISTIC_QUERIES, start=1):
        print(f"[{idx}/{len(REALISTIC_QUERIES)}] Processing query: '{query[:60]}...'")
        try:
            run_master_rag(query)
        except Exception as e:
            print(f"   [WARNING] Error processing query '{query}': {e}")

    print("\n[DONE] Trace generation complete! All traces saved in traces/traces.jsonl\n")


if __name__ == "__main__":
    generate_all_traces()
