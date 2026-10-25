# Week 4 — Advanced RAG Architecture

Week 4 evolves the Week 3 semantic-search RAG into a retrieval pipeline that improves relevance, reduces repeated context, and makes retrieval quality measurable.

## End-to-end request flow

```text
Question
  -> scope guard (reject invalid or unrelated requests)
  -> optional query rewriting (Ollama)
  -> retrieval
       semantic mode: Pinecone vector search
       hybrid mode: Pinecone + BM25, fused with RRF
       reranked mode: hybrid -> cross-encoder -> MMR
  -> confidence check
  -> grounded Ollama answer
  -> API response with chunks, scores, and pipeline trace
```

The FastAPI UI and API run together on port 8000. The browser requests `/api/*` from the same origin. A separate frontend can be used later by setting `FRONTEND_ORIGINS`.

The scope guard immediately rejects obvious gibberish without a model call. For
meaningful text, it uses a small local Ollama routing prompt to reject questions
unrelated to the insurance policy before retrieval starts.

## Retrieval features

### Query rewriting

`rag.core.query_rewriter` uses Ollama to turn vague questions into clear standalone search queries. If Ollama is unavailable, the original query is used so retrieval can still continue.

### Semantic retrieval

`rag.infra.embedder` converts a question into an embedding with `all-MiniLM-L6-v2`. `rag.infra.vectorstore` sends that embedding to Pinecone and returns the most similar stored chunks.

### BM25 keyword retrieval

`rag.core.retrieval.bm25` builds a local BM25 index from the configured PDF. It complements semantic search by handling precise terms, numbers, and policy phrases.

### Hybrid retrieval and RRF

`rag.core.retrieval.hybrid_retriever` gets candidates from both Pinecone and BM25, then combines their rankings using Reciprocal Rank Fusion:

```text
RRF score = 1 / (60 + semantic rank) + 1 / (60 + BM25 rank)
```

Ranks—not incompatible raw scores—are fused. Both ingestion and BM25 use deterministic `chunk_N` identifiers, so their results can be joined correctly. Re-run ingestion after changing the chunking strategy or document.

### Cross-encoder reranking

`rag.core.retrieval.reranker` scores query/chunk pairs with `cross-encoder/ms-marco-MiniLM-L-6-v2`. This is slower but more precise than initial retrieval, so it runs only on the hybrid candidate pool.

### MMR diversity

`rag.core.retrieval.mmr` applies Maximal Marginal Relevance after reranking. With the default lambda of 0.6, it balances relevance with diversity and avoids sending duplicate chunks to the LLM.

## Ingestion and evaluation

```text
PDF -> text extraction (optional OCR) -> overlapping chunks
    -> embeddings -> Pinecone upsert
```

Use `python -m rag.scripts.dataprocessor` to index the configured document. The chunk inspector writes a human-readable chunk map, which supports the ground-truth evaluation dataset.

`rag.scripts.evaluator` calculates Hit Rate@K, Recall@K, and Mean Reciprocal Rank (MRR) for semantic and hybrid modes. The failure-labeling service combines those results with human overrides to distinguish retrieval failures from generation failures.

The files in `data/` are evaluation fixtures and saved evaluation snapshots; they
are not the live inspection view. Uploading or editing a PDF does not rewrite
them automatically because their ground-truth chunk labels need human review.
After changing a document, re-index it, regenerate the chunk map if needed, and
run the evaluator again to refresh saved metrics.

## Implemented package layout

```text
src/rag/
  api/        FastAPI application and routes
  services/   pipeline orchestration and failure labels
  core/       ingestion, query rewriting, BM25, RRF, reranking, MMR
  infra/      Sentence Transformers, Pinecone, and Ollama adapters
  models/     API schemas
  scripts/    ingestion, evaluation, inspection, and manual tools
  web/        frontend template, CSS, and JavaScript
```

Settings—including model names, document location, allowed frontend origins, and backend port—are centralized in `rag.config` and can be overridden through `.env`.

## Uploading documents

The Documents tab accepts PDF uploads up to 20 MB. An uploaded PDF is validated,
saved under `resources/`, and indexed in the background. Select **Use for
questions** on a document card before asking to restrict semantic and BM25
retrieval to that document. Uploaded documents have document-prefixed chunk IDs,
preventing collisions with existing documents in Pinecone.

The selected document is marked **Used for query** in the UI. Deleting a document
also deletes Pinecone vectors with that document's metadata and rebuilds the
in-memory BM25 index on its next use.

After upgrading to document-prefixed IDs, run
`python -c "from rag.scripts.dataprocessor import reindex_all; reindex_all()"`
once to replace vectors for existing PDFs.
