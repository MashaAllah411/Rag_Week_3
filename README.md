# HR Policy RAG — Week 4 · Module 2
## Debugging Retrieval: Hybrid, Reranking & Failure Separation

> **Topic C — HR Policy** | Evaluated Week 5 · Monday

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Make sure Ollama is running with Llama 3.2
ollama serve
ollama pull llama3.2

# 3. Start the FastAPI server
python run_server.py

# 4. Open browser
# UI:   http://localhost:8000
# Docs: http://localhost:8000/api/docs
```

---

## Architecture

```
User Query
    │
    ▼
Query Rewriter (Llama 3.2)
    │
    ▼
Hybrid Search ──────────────────────────────────────┐
    │  Pinecone (semantic)  +  BM25 (keyword)        │
    │  Fused via RRF: score = 1/(60+rank_sem)        │
    │               + 1/(60+rank_bm25)               │
    ├── (reranked mode) Cross-Encoder Reranking      │
    ├── (reranked mode) MMR Diversity Filter         │
    └────────────────────────────────────────────────┘
    │
    ▼
Confidence Check
    │
    ├── PASS → Llama 3.2 Grounded Answer
    └── FAIL → "I don't know based on the provided documents."
```

---

## Before vs After (The Proof)

| Metric       | Semantic (Baseline) | Hybrid (Fix) | Delta  |
|---|---|---|---|
| Hit-Rate@3   | 80%                 | **90%**      | **+10%** |
| MRR          | 0.65                | **0.70**     | **+0.05** |
| Recall@3     | 0.75                | 0.75         | 0.00   |

**One change made:** Added BM25 keyword search, fused with Pinecone via Reciprocal Rank Fusion (RRF).

**Why it worked:** Q7 ("notice period") contained exact HR terms (`notice`, `resignation`) that semantic search missed but BM25 matched directly.

**What it didn't fix:** Q9 ("recalled from annual leave") — still a retrieval failure. The word "recalled" is rare and the chunk (`chunk_110`) scores low even with BM25. This would require query expansion or HyDE to fix.

---

## Failure Taxonomy

| Question | Baseline | Hybrid | Label | Evidence |
|---|---|---|---|---|
| Notice period (Q7) | ✗ MISS | ✓ HIT | **Fixed** | BM25 matched exact keyword "notice" |
| Recalled from leave (Q9) | ✗ MISS | ✗ MISS | **Retrieval Failure** | chunk_110 never retrieved; rare term "recalled" has low BM25 weight |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/ask` | Ask a question (semantic/hybrid/reranked) |
| `GET`  | `/api/evaluate/metrics` | Before/after improvement metrics |
| `GET`  | `/api/evaluate/results/{mode}` | Per-question results for `semantic` or `hybrid` |
| `POST` | `/api/evaluate/run` | Trigger live evaluation (background) |
| `GET`  | `/api/failures` | All questions with failure labels |
| `POST` | `/api/failures/label` | Save a human failure label |
| `GET`  | `/api/documents` | List indexed documents |
| `GET`  | `/api/docs` | Interactive API documentation (Swagger) |
| `GET`  | `/health` | Health check |

---

## Project Structure

```
Rag_Week_3/
├── app/
│   ├── main.py              ← FastAPI app factory
│   ├── routes/
│   │   ├── ask.py           ← POST /api/ask
│   │   ├── evaluate.py      ← GET /api/evaluate/*
│   │   ├── failures.py      ← GET/POST /api/failures
│   │   └── documents.py     ← GET /api/documents
│   ├── services/
│   │   ├── pipeline.py      ← RAG pipeline orchestrator
│   │   └── failure_labeler.py ← Auto-label retrieval vs generation
│   └── models/
│       └── schemas.py       ← Pydantic request/response models
│
├── static/
│   ├── css/style.css        ← Dark glassmorphism UI
│   └── js/app.js            ← Vanilla JS frontend
│
├── templates/
│   └── index.html           ← Main SPA
│
├── data/
│   └── failure_labels.json  ← Human failure labels
│
├── resources/
│   └── HRPolicy.pdf         ← Source document
│
│  ── Core RAG modules (UNCHANGED) ──────────────────────────
├── pdfreader.py             ← PDF extraction
├── chunker.py               ← Fixed-size chunker (900c, 150 overlap)
├── embedder.py              ← all-MiniLM-L6-v2 embeddings
├── vectorstore.py           ← Pinecone upsert + query
├── bm25.py                  ← BM25Okapi keyword search
├── hybrid_retriever.py      ← Semantic + BM25 → RRF fusion
├── reranker.py              ← Cross-Encoder ms-marco-MiniLM-L-6-v2
├── mmr.py                   ← MMR diversity filter
├── query_rewriter.py        ← Llama 3.2 query expansion
├── llm.py                   ← Grounded LLM answer generation
├── evaluator.py             ← hit-rate@3, recall@3, MRR
├── main_rag.py              ← Original console pipeline
├── dataprocessor.py         ← PDF → chunks → embed → Pinecone
├── chunk_inspector.py       ← Builds chunk_map.txt
│  ─────────────────────────────────────────────────────────
│
├── evaluation_dataset.json  ← 10 questions + ground-truth chunk IDs
├── baseline_results.json    ← Semantic evaluation (Hit-Rate@3=80%)
├── hybrid_results.json      ← Hybrid evaluation (Hit-Rate@3=90%)
├── run_server.py            ← Entry point: python run_server.py
└── requirements.txt
```

---

## Environment Variables (.env)

```env
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=rag-week-3-py
OPENAI_API_KEY=optional
```
