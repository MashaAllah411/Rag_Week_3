# ============================================================
# sample_traces.py — Seeded Random Trace Sampler
#
# PURPOSE:
#   Deterministically samples exactly 20 traces from traces.jsonl
#   using a fixed random seed (seed = 42).
#
#   Proves that the sample is 100% reproducible and random.
# ============================================================

import os
import json
import random
from typing import List, Dict, Any

TRACES_FILE = "./traces/traces.jsonl"
SAMPLE_SIZE = 20
RANDOM_SEED = 42


def sample_traces(seed: int = RANDOM_SEED, sample_size: int = SAMPLE_SIZE) -> List[Dict[str, Any]]:
    """
    Loads traces from traces.jsonl and selects a seeded random sample.
    """
    if not os.path.exists(TRACES_FILE):
        raise FileNotFoundError(f"Trace log file {TRACES_FILE} not found. Run generate_traces.py first.")

    traces = []
    with open(TRACES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                traces.append(json.loads(line))

    total_traces = len(traces)
    print(f"\n============================================================")
    print(f"SEEDED RANDOM TRACE SAMPLER (Week 5 Requirement 2)")
    print(f"============================================================")
    print(f"  Total Traces Available : {total_traces}")
    print(f"  Random Seed Value      : {seed}")
    print(f"  Sample Size Requested  : {sample_size}")
    print(f"============================================================\n")

    if total_traces < sample_size:
        raise ValueError(f"Not enough traces ({total_traces}) to draw a sample of {sample_size}.")

    # Seed Python's random generator deterministically
    random.seed(seed)
    sampled = random.sample(traces, sample_size)

    print("SELECTED 20 TRACE IDs (Seeded Sample):")
    print("-" * 60)
    for idx, t in enumerate(sampled, start=1):
        print(f"  {idx:02d}. {t['trace_id']}  | Query: '{t['query'][:50]}...'")
    print("-" * 60 + "\n")

    return sampled


if __name__ == "__main__":
    sampled_traces = sample_traces()
    
    # Save the sampled traces to a standalone file for easy reference
    sample_file = "./traces/sampled_20_traces.json"
    with open(sample_file, "w", encoding="utf-8") as f:
        json.dump(sampled_traces, f, indent=2)
    print(f"Sampled 20 traces saved to: {sample_file}\n")
