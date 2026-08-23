from sentence_transformers import SentenceTransformer
from typing import List
from rag.config import EMBEDDING_MODEL

# Lazy-load the sentence-transformers model to avoid heavy import-time work.
_model = None

def _get_model():
    global _model
    if _model is None:
        print("[EMBEDDER] Loading sentence-transformers model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print("[EMBEDDER] Model loaded.")
    return _model


def embed_chunks(chunks: List[str]) -> List[List[float]]:
    """Embeds chunks using sentence-transformers (all-MiniLM-L6-v2)."""

    model = _get_model()
    print(f"   🔄 Embedding {len(chunks)} chunks locally (no API needed)...")

    # Encode all chunks at once (faster than one-by-one)
    embeddings = model.encode(chunks, show_progress_bar=True)

    # Convert numpy arrays to plain Python lists for Pinecone
    embeddings = [embedding.tolist() for embedding in embeddings]

    if embeddings and embeddings[0]:
        print(f"   ✅ Sample embedding (first value): {embeddings[0][0]:.6f}")

    return embeddings


def embed_user_query(query: str) -> List[float]:
    """Embeds a single user query string and returns a flat list of floats."""

    model = _get_model()
    embedding = model.encode(query)
    return embedding.tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed texts without progress output; used by MMR."""
    return [vector.tolist() for vector in _get_model().encode(texts)]
