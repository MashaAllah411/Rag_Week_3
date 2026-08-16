# ============================================================
# bm25.py
#
# PURPOSE:
#   Keyword-based retrieval using BM25 (Best Match 25).
#   Complements semantic search by finding chunks that contain
#   EXACT words from the query — not just similar meaning.
#
# WHY WE NEED IT:
#   Semantic search failed on:
#     - "recalled from annual leave"  (rare exact word: "recalled")
#     - "resignation notice period"   (specific term: "notice")
#
#   BM25 finds these directly because it matches exact words.
#
# HOW IT WORKS:
#   1. At startup, re-reads the PDF and rebuilds chunks.
#      (Same chunker as dataprocessor.py — deterministic order,
#       so chunk_0...chunk_N match exactly what's in Pinecone.)
#   2. Tokenises each chunk into lowercase words.
#   3. Builds an in-memory BM25 index over all tokens.
#   4. At query time, tokenises the query and scores every chunk.
#
# RETURN FORMAT (same structure as search_in_pinecone):
#   [
#       {"id": "chunk_110", "score": 14.21, "text": "..."},
#       {"id": "chunk_108", "score": 11.03, "text": "..."},
#   ]
#
# NOTE ON SCORES:
#   BM25 scores are NOT between 0 and 1.
#   They are raw relevance scores (can be 0 to ~30+).
#   Higher = more keyword overlap.
#   They CANNOT be directly compared to Pinecone cosine scores.
#   That is why RRF (Phase 6) uses RANKS not raw scores to combine.
# ============================================================

from rank_bm25 import BM25Okapi
from pdfreader import read_pdf
from chunker import chunk_pages
from typing import List


# ── BUILD THE CHUNK CORPUS ────────────────────────────────────────────────────
# We rebuild chunks from the PDF at import time.
# This is fast (< 1 second) and ensures chunk IDs match Pinecone exactly.

def _build_corpus(pdf_path: str = "./resources/HRPolicy.pdf"):
    """
    Reads the PDF and chunks it — same logic as dataprocessor.py.
    Returns:
        chunk_ids   : ["chunk_0", "chunk_1", ...]
        chunk_texts : ["Staff must work...", "Leave entitlement...", ...]
    """
    pages = read_pdf(pdf_path)

    chunk_ids   = []
    chunk_texts = []
    counter     = 0

    for page_text in pages:
        if not page_text or not page_text.strip():
            continue
        for chunk_text in chunk_pages([page_text]):
            if chunk_text.strip():
                chunk_ids.append(f"chunk_{counter}")
                chunk_texts.append(chunk_text)
                counter += 1

    return chunk_ids, chunk_texts


def _tokenize(text: str) -> List[str]:
    """
    Converts text to a list of lowercase tokens.

    Example:
        "Staff must work 9AM to 5:30PM" 
        → ["staff", "must", "work", "9am", "to", "5:30pm"]

    We keep it simple: just lowercase + split on whitespace.
    No stopword removal — BM25 handles rare vs common words natively.
    """
    return text.lower().split()


# ── INITIALISE AT IMPORT TIME ────────────────────────────────────────────────
# This runs once when any file does: from bm25 import search_bm25
# Takes < 1 second.

print("[BM25] Building index from PDF chunks...")
_chunk_ids, _chunk_texts = _build_corpus()
_tokenized_corpus = [_tokenize(text) for text in _chunk_texts]
_bm25_index = BM25Okapi(_tokenized_corpus)
print(f"[BM25] Index ready — {len(_chunk_ids)} chunks indexed.")


# ── PUBLIC SEARCH FUNCTION ────────────────────────────────────────────────────

def search_bm25(query: str, top_k: int = 10) -> List[dict]:
    """
    Searches the BM25 index for the most keyword-relevant chunks.

    Args:
        query  : The user's raw query string
        top_k  : How many results to return

    Returns:
        List of dicts, each with:
            "id"    : chunk ID  (e.g. "chunk_110")
            "score" : BM25 raw score (higher = more keyword overlap)
            "text"  : original chunk text

    Example:
        search_bm25("recalled from annual leave", top_k=3)
        → [
            {"id": "chunk_110", "score": 14.21, "text": "GESCI may recall..."},
            {"id": "chunk_109", "score": 6.03,  "text": "leave accrues at..."},
            {"id": "chunk_108", "score": 3.11,  "text": "Any approved flexible..."},
          ]
    """
    query_tokens = _tokenize(query)
    scores       = _bm25_index.get_scores(query_tokens)

    # Pair each chunk with its score, sort descending
    scored = sorted(
        zip(_chunk_ids, _chunk_texts, scores),
        key=lambda x: x[2],
        reverse=True
    )

    results = []
    for chunk_id, chunk_text, score in scored[:top_k]:
        results.append({
            "id"   : chunk_id,
            "score": round(float(score), 4),
            "text" : chunk_text
        })

    return results


# ── QUICK TEST ────────────────────────────────────────────────────────────────
# Run this file directly to verify BM25 is working:
#   python bm25.py

if __name__ == "__main__":
    test_queries = [
        "What happens if a staff member is recalled from annual leave?",
        "How many weeks notice must a staff member give when resigning?",
        "What are the official working hours?"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        results = search_bm25(query, top_k=3)
        for rank, r in enumerate(results, start=1):
            print(f"  Rank {rank} | ID: {r['id']} | Score: {r['score']}")
            safe_preview = r['text'][:100].encode('ascii', errors='replace').decode('ascii')
            print(f"           {safe_preview}...")
        print()
