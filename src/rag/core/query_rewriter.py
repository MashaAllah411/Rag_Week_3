# ============================================================
# query_rewriter.py
#
# PURPOSE:
#   Rewrites short, vague, or conversational user queries into clear,
#   standalone search-optimized queries using Ollama (llama3.2).
#
# IMPORTANT:
#   Query rewriting improves search retrieval. It DOES NOT answer
#   the user's question directly.
# ============================================================

import ollama
import logging
from rag.config import OLLAMA_MODEL

logger = logging.getLogger(__name__)


def rewrite_query(original_query: str) -> str:
    """
    Takes a raw user query and rephrases it into a clearer, search-optimized string.

    Args:
        original_query : The raw input string from the user.

    Returns:
        The rewritten search query string.
    """
    system_prompt = """You are a search query optimizer for a document search engine.
Your task is to rephrase the user's input into a single clear, complete, and search-optimized question.

RULES:
1. Output ONLY the rewritten search query. No intro, no explanation, no quotes.
2. Do NOT answer the user's question.
3. Preserve key domain terms and user intent.
4. Expand short keywords into full, meaningful search questions.

Example Input: depreciation rate?
Example Output: What is the schedule of depreciation rates for vehicles and parts?
"""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User Input: {original_query}"}
            ],
            options={"temperature": 0.2}
        )

        rewritten = response["message"]["content"].strip()
        # Clean quotes if model adds them
        rewritten = rewritten.strip('"').strip("'")
        return rewritten

    except Exception as e:
        print(f"⚠️ [QUERY_REWRITER] Warning: Ollama query rewriting failed ({e}). Using original query.")
        return original_query


if __name__ == "__main__":
    test_queries = [
        "timing?",
        "how many leave days?",
        "resignation notice period",
        "can I take sick leave without a doctor note?"
    ]

    print("\n" + "=" * 60)
    print("QUERY REWRITER TEST")
    print("=" * 60)

    for q in test_queries:
        print(f"\nOriginal Query : '{q}'")
        rewritten = rewrite_query(q)
        print(f"Rewritten Query: '{rewritten}'")

    print("\n" + "=" * 60 + "\n")
