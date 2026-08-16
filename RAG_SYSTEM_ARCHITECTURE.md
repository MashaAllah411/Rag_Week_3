# 📚 Advanced RAG Architecture & Execution Guide

> **Confirmation:** YES! You are **100% on the right path**. Your understanding of every single component is spot on. 

This document explains your complete Week 4 RAG system, how `main_rag.py` ties all 11 phases together with your existing RAG, and how each component communicates.

---

## 🧠 Part 1: Validation of Your Understanding

Here is a breakdown confirming and expanding on each of your points:

### 1. `DataProcessor.py` (Ingestion Phase)
- **Your Understanding:** *Gets doc $\rightarrow$ processes/chunks $\rightarrow$ embeds $\rightarrow$ stores in Pinecone DB.*
- **Status:** **CORRECT!** Runs once to ingest `HRPolicy.pdf` into Pinecone vector index (`rag-week-3-py`).

### 2. `QueryProcessor.py` (Previous vs. Phase 1 Inspection View)
- **Your Understanding:** *Previously: query $\rightarrow$ embed $\rightarrow$ search Pinecone $\rightarrow$ send string to LLM $\rightarrow$ return answer. Now: added Phase 1 Inspection View showing `chunk_id`, `rank`, `score`, and text before answer.*
- **Status:** **CORRECT!** Instead of returning an opaque string, `search_in_pinecone()` returns a structured list of dicts:
  ```python
  [{"id": "chunk_107", "score": 0.8123, "text": "..."}]
  ```
  This separates **data retrieval** from **display/LLM context generation**, making error diagnosis possible.

### 3. `chunk_inspector.py` & `chunk_map.txt` (Phase 2)
- **Your Understanding:** *Why is it used, and how is it related to RAG?*
- **Detailed Explanation:**
  - **Why it exists:** Pinecone assigns IDs like `chunk_0`, `chunk_1`, `chunk_2` in the exact order pages are processed. You **cannot guess** which chunk ID contains which policy.
  - **What it does:** It re-runs `pdfreader.py` and `chunker.py` locally and writes every chunk with its ID and page source to `chunk_map.txt`.
  - **Relation to RAG:** It allows human engineers to read `chunk_map.txt`, find where the policy answers live, and build an accurate **ground-truth evaluation dataset** (`evaluation_dataset.json`). Without real chunk IDs, evaluation is impossible.

### 4. `evaluator.py` & JSON Files (Phases 3, 4, 7)
- **Your Understanding:** *Used to check Hit Rate@3, Recall@3, and MRR. What JSON files are used?*
- **JSON Files Used:**
  1. `evaluation_dataset.json` — The **ground truth input** (10 questions + ground-truth `relevant_chunks` list).
  2. `semantic_results.json` / `baseline_results.json` — Saved evaluation output when running **Semantic Search alone** (Hit Rate@3 = 80.0%, MRR = 0.65).
  3. `hybrid_results.json` — Saved evaluation output when running **Hybrid Search (Semantic + BM25 + RRF)** (Hit Rate@3 = 90.0%, MRR = 0.70).

### 5. `bm25.py` (Phase 5 Keyword Search)
- **Your Understanding:** *Used to do keyword search. Need more info.*
- **Detailed Explanation:**
  - Semantic Search matches *concepts* via vectors, but often misses *exact terms* (e.g. "notice", "recalled", numbers).
  - BM25 indexes the raw word tokens of all 256 chunks.
  - It scores chunks based on **term frequency** and **inverse document frequency** (rare words like "recalled" get high weights).
  - It complements vector search by catching exact matches that vector search glosses over.

### 6. `hybrid_retriever.py` (Phase 6 RRF Fusion)
- **Your Understanding:** *Gets ranking from both semantic and keyword, and combines them using RRF.*
- **Status:** **CORRECT!** Pinecone outputs 0.0-1.0 cosine scores, while BM25 outputs 0-30+ raw scores. RRF ignores raw scores and fuses candidate rankings using:
  $$\text{RRF Score} = \frac{1}{60 + \text{rank}_{\text{semantic}}} + \frac{1}{60 + \text{rank}_{\text{bm25}}}$$

### 7. `reranker.py` (Phase 9 Cross-Encoder)
- **Your Understanding:** *Compares query and chunks together to get refined results.*
- **Status:** **CORRECT!** Bi-encoders (Pinecone/BM25) evaluate queries and documents separately. The Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) feeds `(query, text)` together through all attention layers, giving deep precision. (Boosted `chunk_227` to Rank 1!).

### 8. `mmr.py` (Phase 10 Diversity)
- **Your Understanding:** *Prevents duplicates by balancing relevance and diversity.*
- **Status:** **CORRECT!** Uses $\lambda = 0.6$ to pick candidates that are relevant to the query BUT different from already selected chunks, saving LLM context space.

### 9. `query_rewriter.py` (Phase 11)
- **Your Understanding:** *Rewrites user query for better LLM/retrieval results.*
- **Status:** **CORRECT!** Expands short prompts like `"timing?"` into `"What are the official working hours and timing policy for employees?"` using Llama 3.2.

---

## ⚙️ Part 2: End-to-End Execution Flow of `main_rag.py`

`main_rag.py` ties your existing Week 3 codebase and all 11 Week 4 phases into one unified pipeline.

```text
                               ┌────────────────────────┐
                               │ User Input: "timing?"  │
                               └───────────┬────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: QUERY REWRITING (Phase 11 — query_rewriter.py)                                │
│   - Sends raw input "timing?" to Ollama (Llama 3.2).                                   │
│   - System Prompt: "Rewrite into a standalone search query. Do NOT answer."             │
│   - Output: "What are the official working hours and timing policy for staff?"          │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: HYBRID RETRIEVAL (Phase 6 — hybrid_retriever.py)                               │
│   ┌───────────────────────────────────┐    ┌────────────────────────────────────────┐  │
│   │ Semantic Search (vectorstore.py)  │    │ Keyword Search (bm25.py)               │  │
│   │  - Embeds query (embedder.py)     │    │  - Tokenizes query                     │  │
│   │  - Queries Pinecone index         │    │  - Scores 256 in-memory chunks         │  │
│   │  - Returns Top 10 vector candidates│    │  - Returns Top 10 keyword candidates   │  │
│   └─────────────────┬─────────────────┘    └──────────────────┬─────────────────────┘  │
│                     └──────────────────┬──────────────────────┘                        │
│                                        ▼                                               │
│   - Reciprocal Rank Fusion: RRF_score = 1/(60 + rank_sem) + 1/(60 + rank_bm25)         │
│   - Output: Top 10 fused candidates                                                    │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: CROSS-ENCODER RERANKING (Phase 9 — reranker.py)                                │
│   - Passes (search_query, chunk_text) pairs into ms-marco-MiniLM-L-6-v2 Cross-Encoder.│
│   - Evaluates deep cross-attention interaction.                                        │
│   - Output: Top 6 reranked candidates sorted by cross-encoder score.                  │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: MMR DIVERSITY FILTER (Phase 10 — mmr.py)                                       │
│   - Computes query similarity vs chunk-to-chunk similarity (lambda = 0.6).             │
│   - Filters out redundant/duplicate chunks.                                            │
│   - Output: Top 3 diverse, high-relevance chunks.                                      │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: LLM ANSWER & INSPECTION VIEW (Phase 1 — llm.py & queryprocessor.py)            │
│   - Joins top 3 chunk texts into a clean context string.                               │
│   - Calls Ollama Llama 3.2 with context + user query.                                  │
│   - Calls print_inspection_view() to display:                                          │
│       1. Original Query                                                                │
│       2. Ranked Chunks with IDs, Scores & Text                                         │
│       3. Final LLM Answer                                                              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Part 3: Quick Command Reference

| Task | Command |
|---|---|
| Ingest PDF to Pinecone | `python DataProcessor.py` |
| Run Basic Query + Inspection View | `python Queryprocessor.py` |
| Generate Chunk Map for Ground Truth | `python chunk_inspector.py` |
| Evaluate Semantic Search (Baseline) | `python evaluator.py semantic` |
| Evaluate Hybrid Search | `python evaluator.py hybrid` |
| Test BM25 Keyword Search | `python bm25.py` |
| Test Hybrid Search (RRF) | `python hybrid_retriever.py` |
| Test Cross-Encoder Reranker | `python reranker.py` |
| Test MMR Diversity Filter | `python mmr.py` |
| Test Query Rewriter | `python query_rewriter.py` |
| **Run Master Integrated RAG** | **`python main_rag.py`** |
