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
from rag.config import RESOURCES_DIR
from rag.core.document_ids import document_id
from rag.core.ingest.pdfreader import read_pdf
from rag.core.ingest.chunker import chunk_pages
from typing import List


# ── BUILD THE CHUNK CORPUS ────────────────────────────────────────────────────
# We rebuild chunks from the PDF at import time.
# This is fast (< 1 second) and ensures chunk IDs match Pinecone exactly.

def _build_corpus():
    """
    Reads the PDF and chunks it — same logic as dataprocessor.py.
    Returns:
        chunk_ids   : ["chunk_0", "chunk_1", ...]
        chunk_texts : ["Staff must work...", "Leave entitlement...", ...]
    """
    chunk_ids   = []
    chunk_texts = []
    chunk_documents = []
    for pdf_path in sorted(RESOURCES_DIR.glob("*.pdf")):
        pages = read_pdf(str(pdf_path))
        doc_id = document_id(pdf_path.name)
        counter = 0
        for page_text in pages:
            if not page_text or not page_text.strip():
                continue
            for chunk_text in chunk_pages([page_text]):
                if chunk_text.strip():
                    chunk_ids.append(f"{doc_id}:chunk_{counter}")
                    chunk_texts.append(chunk_text)
                    chunk_documents.append(pdf_path.name)
                    counter += 1

    return chunk_ids, chunk_texts, chunk_documents


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

# Lazy initialization to avoid heavy work at import time
_chunk_ids = None
_chunk_texts = None
_chunk_documents = None
_tokenized_corpus = None
_bm25_index = None


def _ensure_index():
    """Build the BM25 index on first use."""
    global _chunk_ids, _chunk_texts, _chunk_documents, _tokenized_corpus, _bm25_index
    if _bm25_index is not None:
        return

    print("[BM25] Building index from PDF chunks (lazy init)...")
    _chunk_ids, _chunk_texts, _chunk_documents = _build_corpus()
    if not _chunk_texts:
        return
    _tokenized_corpus = [_tokenize(text) for text in _chunk_texts]
    _bm25_index = BM25Okapi(_tokenized_corpus)
    print(f"[BM25] Index ready — {len(_chunk_ids)} chunks indexed.")


# ── PUBLIC SEARCH FUNCTION ────────────────────────────────────────────────────

def reset_bm25_index() -> None:
    """Force a rebuild after a PDF is uploaded."""
    global _chunk_ids, _chunk_texts, _chunk_documents, _tokenized_corpus, _bm25_index
    _chunk_ids = _chunk_texts = _chunk_documents = _tokenized_corpus = _bm25_index = None


def search_bm25(query: str, top_k: int = 10, document_name: str | None = None) -> List[dict]:
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
    # Ensure the BM25 index is built (lazy init)
    _ensure_index()

    query_tokens = _tokenize(query)
    if _bm25_index is None:
        # No index could be built (e.g., missing PDF) — return empty
        return []

    scores = _bm25_index.get_scores(query_tokens)

    # Pair each chunk with its score, sort descending
    scored = sorted(
        zip(_chunk_ids, _chunk_texts, _chunk_documents, scores),
        key=lambda x: x[3],
        reverse=True
    )

    results = []
    for chunk_id, chunk_text, chunk_document, score in scored:
        if document_name and chunk_document != document_name:
            continue
        results.append({
            "id"   : chunk_id,
            "score": round(float(score), 4),
            "text" : chunk_text
        })
        if len(results) == top_k:
            break

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
