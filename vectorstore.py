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


def search_in_pinecone(
    query_vector: List[float],
    top_k: int = 4,
    namespace: str = ""
) -> str:
    """Queries Pinecone with the given vector and returns top matching chunks as a single context string."""

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace
    )

    print(f"   ✅ Found {len(results.matches)} matching chunks\n")

    matched_chunks = []

    for i, match in enumerate(results.matches):
        text = match.metadata.get("text", "")
        score = round(match.score, 4)
        print(f"   📄 Chunk {i+1} (score: {score}): {text[:80]}...")
        matched_chunks.append(text)

    # Join all matched chunks into a single context string for the LLM
    return "\n\n---\n\n".join(matched_chunks)
