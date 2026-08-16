from pinecone import Pinecone
import os
from dotenv import load_dotenv
from typing import List

# Load environment variables from .env file
load_dotenv()

# Initialize Pinecone client
pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pinecone_client.Index(os.getenv("PINECONE_INDEX_NAME"))


def store_in_pinecone(
    chunks: List[str],
    embeddings: List[List[float]],
    namespace: str = ""
):
    vectors_to_upsert = []

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        vector_data = {
            "id": f"chunk_{i}",
            "values": embedding,
            "metadata": {
                "text": chunk,
                "chunk_index": i
            }
        }

        vectors_to_upsert.append(vector_data)

    # Upsert vectors in batches (Pinecone recommends batch size of 100)
    batch_size = 100

    for i in range(0, len(vectors_to_upsert), batch_size):
        batch = vectors_to_upsert[i:i + batch_size]
        index.upsert(vectors=batch, namespace=namespace)


# ============================================================
# PHASE 1 — CHANGED: search_in_pinecone now returns a
# structured list of dicts instead of a plain joined string.
#
# WHY: So the caller (queryprocessor.py) can:
#   1. Display chunk IDs and scores for debugging
#   2. Build the context string itself
#   3. Use chunk IDs for evaluation later (Phase 3)
#
# RETURN FORMAT:
#   [
#       {"id": "chunk_15", "score": 0.8123, "text": "..."},
#       {"id": "chunk_8",  "score": 0.7642, "text": "..."},
#   ]
# ============================================================
def search_in_pinecone(
    query_vector: List[float],
    top_k: int = 4,
    namespace: str = ""
) -> List[dict]:
    """
    Queries Pinecone with the given vector.

    Returns a structured list of dicts, each containing:
      - id    : the chunk ID stored in Pinecone (e.g. "chunk_15")
      - score : cosine similarity score (0.0 to 1.0)
      - text  : the original chunk text
    """

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace
    )

    retrieval_results = []

    for match in results.matches:
        retrieval_results.append({
            "id":    match.id,
            "score": round(match.score, 4),
            "text":  match.metadata.get("text", "")
        })

    return retrieval_results
