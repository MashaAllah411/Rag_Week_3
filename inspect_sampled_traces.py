# ============================================================
# inspect_sampled_traces.py
#
# PURPOSE:
#   Prints the 20 sampled traces verbatim so we can perform
#   manual open-coding (writing 1 observation sentence per trace).
# ============================================================

import json

with open("data/sampled_20_traces.json", "r", encoding="utf-8") as f:
    sampled = json.load(f)

print(f"============================================================")
print(f"SAMPLED 20 TRACES FOR OPEN-CODING (Seed = 42)")
print(f"============================================================\n")

for idx, t in enumerate(sampled, start=1):
    print(f"--- TRACE [{idx}/20] ---")
    print(f"Trace ID       : {t['trace_id']}")
    print(f"Query          : {t['query']}")
    print(f"Retrieved Chunks: {[c['chunk_id'] for c in t['retrieved_chunks']]}")
    print(f"Raw Output     : {t['raw_llm_output']}")
    print()
