from sentence_transformers import SentenceTransformer
from typing import List

# Load the sentence-transformers model (384-dimension vectors)
model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_chunks(chunks: List[str]) -> List[List[float]]:
    """Embeds chunks using sentence-transformers (all-MiniLM-L6-v2)."""

    print(f"   🔄 Embedding {len(chunks)} chunks locally (no API needed)...")

    # Encode all chunks at once (faster than one-by-one)
    embeddings = model.encode(chunks, show_progress_bar=True)

    # Convert numpy arrays to plain Python lists for Pinecone
    embeddings = [embedding.tolist() for embedding in embeddings]

    print(f"   ✅ Sample embedding (first value): {embeddings[0][0]:.6f}")

    return embeddings


def embed_user_query(query: str) -> List[float]:
    """Embeds a single user query string and returns a flat list of floats."""

    embedding = model.encode(query)
    return embedding.tolist()
