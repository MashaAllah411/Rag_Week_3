from pinecone import Pinecone
import os
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables from .env file
load_dotenv()

# Initialize Pinecone client
pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pinecone_client.Index(os.getenv("PINECONE_INDEX_NAME"))


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

        # Generate unique chunk ID based on document name, strategy, and index
        doc_id = meta.get("document_name", "doc").replace(" ", "_")
        strategy = meta.get("chunking_strategy", "default")
        vector_id = f"{doc_id}_{strategy}_{i}"

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
        index.upsert(vectors=batch, namespace=namespace)


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

    results = index.query(
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
