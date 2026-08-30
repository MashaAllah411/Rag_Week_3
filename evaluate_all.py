# ============================================================
# evaluate_all.py — Unified Week 6 Evaluation Suite
#
# PURPOSE:
#   Executes all 25+ evaluation cases in taxonomy_eval_set.json:
#     1. Runs 4 Deterministic Assertions (eval_assertions.py)
#     2. Runs LLM Judge V1 (judge_v1.txt) and measures agreement_before
#     3. Runs LLM Judge V2 (judge_v2.txt) and measures agreement_after
#     4. Prints Pass Rate by Week-5 Taxonomy Mode
#     5. Reports assertion vs. judge count (4 assertions vs 1 judged criterion)
# ============================================================

import sys
import os
import json
import ollama
from typing import Dict, Any, List

# Ensure src and root are in sys.path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./src"))

from eval_assertions import run_all_assertions
from rag.scripts.main_rag import run_master_rag

EVAL_SET_PATH = "taxonomy_eval_set.json"
HUMAN_LABELS_PATH = "labels_25.json"
JUDGE_V1_PATH = "judge_v1.txt"
JUDGE_V2_PATH = "judge_v2.txt"


def load_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def run_llm_judge(prompt_template: str, query: str, context: str, answer: str) -> int:
    """
    Invokes Ollama llama3.2 using the judge prompt template.
    Returns 1 for PASS, 0 for FAIL.
    """
    user_content = f"Query: {query}\n\nRetrieved Context:\n{context}\n\nGenerated Answer:\n{answer}"
    
    try:
        response = ollama.chat(
            model="llama3.2",
            messages=[
                {"role": "system", "content": prompt_template},
                {"role": "user", "content": user_content}
            ],
            options={"temperature": 0.0}
        )
        output = response["message"]["content"].strip()
        if "VERDICT: 1" in output or "VERDICT:1" in output:
            return 1
        elif "VERDICT: 0" in output or "VERDICT:0" in output:
            return 0
        else:
            # Fallback parsing
            return 1 if "pass" in output.lower() else 0
    except Exception as e:
        print(f"⚠️ Judge call failed ({e}), defaulting to 0.")
        return 0


def run_complete_evaluation():
    print(f"\n{'=' * 70}")
    print("WEEK 6 UNIFIED EVALUATION SUITE — Task Set D")
    print(f"{'=' * 70}\n")

    # Load eval dataset and human labels
    with open(EVAL_SET_PATH, "r", encoding="utf-8") as f:
        eval_items = json.load(f)

    with open(HUMAN_LABELS_PATH, "r", encoding="utf-8") as f:
        human_labels_data = json.load(f)["labels"]

    judge_v1_prompt = load_file(JUDGE_V1_PATH)
    judge_v2_prompt = load_file(JUDGE_V2_PATH)

    # Track metrics
    mode_counts = {}
    mode_passes = {}
    
    v1_matches = 0
    v2_matches = 0
    disagreements_v1 = []

    print(f"Loaded {len(eval_items)} evaluation cases across 6 taxonomy modes.\n")
    print("Running pipeline & evaluations for all 25 cases...\n")

    for idx, item in enumerate(eval_items, start=1):
        item_id = item["id"]
        mode = item["mode"]
        query = item["question"]
        human_label = human_labels_data.get(item_id, 0)

        # Track mode stats
        mode_counts[mode] = mode_counts.get(mode, 0) + 1

        # Run pipeline (using hybrid retrieval)
        from rag.core.retrieval.hybrid_retriever import hybrid_search
        from rag.core.retrieval.reranker import rerank_chunks
        from rag.core.retrieval.mmr import apply_mmr
        from rag.infra.llm import query_llm_with_context

        hybrid_cand = hybrid_search(query, top_k=10)
        reranked = rerank_chunks(query, hybrid_cand, top_k=6)
        final_chunks = apply_mmr(query, reranked, top_k=3, lambda_param=0.6)
        
        context_str = "\n\n---\n\n".join(c["text"] for c in final_chunks)
        answer = query_llm_with_context(query, context_str)

        # 1. Deterministic Assertions (4 Assertions)
        assertions_res = run_all_assertions(item, answer)

        # 2. LLM Judge V1
        judge_v1_verdict = run_llm_judge(judge_v1_prompt, query, context_str, answer)
        if judge_v1_verdict == human_label:
            v1_matches += 1
        else:
            disagreements_v1.append({
                "id": item_id,
                "query": query,
                "human": human_label,
                "judge_v1": judge_v1_verdict,
                "answer": answer[:120]
            })

        # 3. LLM Judge V2
        judge_v2_verdict = run_llm_judge(judge_v2_prompt, query, context_str, answer)
        if judge_v2_verdict == human_label:
            v2_matches += 1

        # Final pass criteria for taxonomy table: Assertions Pass AND Human/Judge V2 Pass
        is_pass = assertions_res["all_passed"] and judge_v2_verdict == 1
        if is_pass:
            mode_passes[mode] = mode_passes.get(mode, 0) + 1

        status_str = "[PASS]" if is_pass else "[FAIL]"
        print(f"[{idx:02d}/25] {item_id} | Mode: {mode:25s} | Assertions: {str(assertions_res['all_passed']):5s} | Human: {human_label} | V1: {judge_v1_verdict} | V2: {judge_v2_verdict} | Overall: {status_str}")

    # Compute Agreement Percentages
    total_cases = len(eval_items)
    agreement_before = (v1_matches / total_cases) * 100.0
    agreement_after = (v2_matches / total_cases) * 100.0

    print(f"\n{'=' * 70}")
    print("1. DETERMINISTIC ASSERTIONS VS JUDGED CRITERIA SPLIT")
    print(f"{'=' * 70}")
    print("  Deterministic Assertions Count : 4")
    print("    - Claim Number Format (CLM-YYYY-NNNNN)")
    print("    - Date of Loss Present & Parseable")
    print("    - Numeric Deductible / Excess Amount")
    print("    - Exclusion Clause ID Cited on Denials")
    print("  LLM Judged Criteria Count     : 1 (Single Binary Grounded Summary Criterion)")
    print("  Ratio                          : 4 Assertions vs 1 Judged Criterion")

    print(f"\n{'=' * 70}")
    print("2. LLM JUDGE AGREEMENT METRICS (BEFORE vs AFTER)")
    print(f"{'=' * 70}")
    print(f"  Agreement Before (Judge V1) : {agreement_before:.1f}% ({v1_matches}/{total_cases})")
    print(f"  Agreement After  (Judge V2) : {agreement_after:.1f}% ({v2_matches}/{total_cases})")
    print(f"  Net Agreement Increase      : +{agreement_after - agreement_before:.1f}%")

    print(f"\n{'=' * 70}")
    print("3. PASS RATE BREAKDOWN BY WEEK-5 TAXONOMY MODE")
    print(f"{'=' * 70}")
    print(f" {'Taxonomy Mode':30s} | {'Total':5s} | {'Passed':6s} | {'Pass Rate':10s}")
    print("-" * 60)
    for m in sorted(mode_counts.keys()):
        cnt = mode_counts[m]
        pss = mode_passes.get(m, 0)
        rate = (pss / cnt) * 100.0
        print(f" {m:30s} | {cnt:5d} | {pss:6d} | {rate:9.1f}%")
    print(f"{'=' * 70}\n")

    # Save disagreement details for notes
    disagreement_file = "disagreements_analysis.json"
    with open(disagreement_file, "w", encoding="utf-8") as f:
        json.dump(disagreements_v1, f, indent=2)

    return {
        "agreement_before": round(agreement_before, 1),
        "agreement_after": round(agreement_after, 1),
        "assertions_count": 4,
        "judged_criteria_count": 1,
        "mode_pass_rates": {m: round((mode_passes.get(m, 0)/mode_counts[m])*100, 1) for m in mode_counts}
    }


if __name__ == "__main__":
    run_complete_evaluation()
