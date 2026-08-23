from pinecone import Pinecone
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
from rag.config import PINECONE_INDEX_NAME

# Load environment variables from .env file
load_dotenv()

# Lazy initialize Pinecone client and index to avoid import-time failures
_pinecone_client = None
_index = None


def _get_index():
    global _pinecone_client, _index
    if _index is not None:
        return _index

    api_key = os.getenv("PINECONE_API_KEY")
    index_name = PINECONE_INDEX_NAME
    if not api_key or not index_name:
        raise RuntimeError("PINECONE_API_KEY and PINECONE_INDEX_NAME must be set in environment")

    _pinecone_client = Pinecone(api_key=api_key)
    _index = _pinecone_client.Index(index_name)
    return _index


def store_in_pinecone(
    chunks: List[str],
    embeddings: List[List[float]],
    namespace: str = "",
    metadata_list: List[Dict[str, Any]] = None
):
    vectors_to_upsert = []

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        meta = {
            "text": chunk,
            "chunk_index": i
        }
        if metadata_list and i < len(metadata_list):
            meta.update(metadata_list[i])

        # Must match the deterministic BM25 corpus ID for RRF fusion.
        vector_id = meta.get("chunk_id", f"chunk_{i}")

        vector_data = {
            "id": vector_id,
            "values": embedding,
            "metadata": meta
        }

        vectors_to_upsert.append(vector_data)

    # Upsert vectors in batches (Pinecone recommends batch size of 100)
    batch_size = 100

    for i in range(0, len(vectors_to_upsert), batch_size):
        batch = vectors_to_upsert[i:i + batch_size]
        idx = _get_index()
        idx.upsert(vectors=batch, namespace=namespace)


def delete_document_from_pinecone(document_name: str, namespace: str = "") -> None:
    """Remove existing vectors for a document before it is re-indexed."""
    _get_index().delete(filter={"document_name": {"$eq": document_name}}, namespace=namespace)


def search_in_pinecone(
    query_vector: List[float],
    top_k: int = 4,
    namespace: str = "",
    filter: Dict[str, Any] = None
) -> List[dict]:
    """
    Queries Pinecone with the given vector, optionally applying metadata filters.

    Returns a structured list of dicts, each containing:
      - id    : the chunk ID stored in Pinecone
      - score : cosine similarity score (0.0 to 1.0)
      - text  : the original chunk text
      - metadata: other key-value pairs
    """

    idx = _get_index()
    results = idx.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace,
        filter=filter
    )

    retrieval_results = []

    for match in results.matches:
        retrieval_results.append({
            "id":    match.id,
            "score": round(match.score, 4),
            "text":  match.metadata.get("text", ""),
            "metadata": match.metadata
        })

    return retrieval_results
