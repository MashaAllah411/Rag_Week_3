from rag.infra.embedder import embed_user_query
from rag.infra.vectorstore import search_in_pinecone
from rag.infra.llm import query_llm_with_context
from tracer import log_trace
from typing import List


# ============================================================
# PHASE 1 — NEW: print_inspection_view
#
# WHY: Makes retrieval completely transparent.
#      You can now see exactly WHICH chunks were retrieved,
#      their chunk IDs, and their similarity scores —
#      BEFORE the LLM generates its answer.
#
# This lets you diagnose:
#   - RETRIEVAL FAILURE → correct chunk is NOT in the list
#   - GENERATION FAILURE → correct chunk IS in the list
#                          but the LLM still answered wrong
# ============================================================
def print_inspection_view(
    query: str,
    retrieval_results: List[dict],
    answer: str
):
    """
    Prints a full inspection view of the RAG pipeline:
      1. The original query
      2. Every retrieved chunk with its ID, score, and text
      3. The final LLM answer
    """

    line = "=" * 60

    # ── QUERY ────────────────────────────────────────────────
    print(f"\n{line}")
    print("QUERY")
    print(line)
    print(f"\n{query}\n")

    # ── RETRIEVAL RESULTS ────────────────────────────────────
    print(f"\n{line}")
    print("RETRIEVAL RESULTS")
    print(line)

    for rank, result in enumerate(retrieval_results, start=1):
        print(f"\nRank {rank}")
        print(f"Chunk ID        : {result['id']}")
        print(f"Similarity Score: {result['score']}")
        safe_text = result['text'].encode('ascii', errors='replace').decode('ascii')
        print(f"\n{safe_text}")
        print()

    # ── FINAL ANSWER ─────────────────────────────────────────
    print(f"\n{line}")
    print("FINAL ANSWER")
    print(line)
    print(f"\n{answer}\n")


def process_user_query(query: str):

    # Step 1: Embed the user query into a 384-dim vector
    print("\n🧠 Embedding query...")
    query_vector = embed_user_query(query)

    # Step 2: Search Pinecone — returns structured list of dicts
    print("📌 Searching Pinecone...")
    retrieval_results = search_in_pinecone(query_vector)

    # Step 3: Build context string from structured results
    context = "\n\n---\n\n".join(
        result["text"] for result in retrieval_results
    )

    # Step 4: Send query + context to Ollama/llama3.2
    print("🤖 Generating answer with LLM...")
    answer = query_llm_with_context(query, context)

    # Step 5: Print the full inspection view
    print_inspection_view(query, retrieval_results, answer)

    # Step 6: Log complete PII-redacted trace (Week 5 Requirement 2 & 4)
    log_trace(
        query=query,
        retrieved_chunks=retrieval_results,
        raw_llm_output=answer,
        prompt_version="v1.0",
        retriever_type="Semantic Search (Pinecone)",
        model_name="llama3.2",
        model_parameters={"temperature": 0.4}
    )


if __name__ == "__main__":
    user_query = "What is the work timing policy?"
    process_user_query(user_query)
