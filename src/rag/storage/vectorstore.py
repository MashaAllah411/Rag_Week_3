"""Vector storage layer (Week 3: Qdrant / Chroma / pgvector -> Chroma).

Open-source, embedded and persistent: no account, API key or network needed.
Replaces the hosted Pinecone store while keeping the same call contract:

    store_chunks(chunks, embeddings, namespace="", metadata_list=None)
    search_chunks(query_vector, top_k=4, namespace="", filter=None) -> [{id, score, text, metadata}]
    delete_document(document_name, namespace="")

Scores are cosine similarities in 0..1 (higher is better). Metadata filters use
the same ``{"field": {"$eq": value}}`` syntax the retrieval code already sends.
The previous Pinecone implementation is archived in legacy/pinecone/.
"""
from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from rag.config import VECTOR_STORE_COLLECTION, VECTOR_STORE_DIR

logger = logging.getLogger(__name__)

_UPSERT_BATCH = 500


class VectorStore(ABC):
    """Interface every vector backend implements."""

    name: str = "abstract"

    @abstractmethod
    def store(self, chunks: List[str], embeddings: List[List[float]], namespace: str = "",
              metadata_list: Optional[List[Dict[str, Any]]] = None) -> None: ...

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 4, namespace: str = "",
               filter: Optional[Dict[str, Any]] = None) -> List[dict]: ...

    @abstractmethod
    def delete_document(self, document_name: str, namespace: str = "") -> None: ...

    @abstractmethod
    def count(self, namespace: str = "") -> int: ...

    @abstractmethod
    def status(self) -> Dict[str, Any]: ...


def _clean_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Chroma metadata values must be str/int/float/bool; drop None, stringify the rest."""
    cleaned: Dict[str, Any] = {}
    for key, value in meta.items():
        if value is None:
            continue
        cleaned[key] = value if isinstance(value, (str, int, float, bool)) else str(value)
    return cleaned


class ChromaVectorStore(VectorStore):
    """ChromaDB persistent client, cosine distance (HNSW)."""

    name = "chromadb"

    def __init__(self, path: str, collection: str):
        self._path = str(path)
        self._collection_prefix = collection
        self._client = None
        self._lock = threading.Lock()

    def _get_client(self):
        if self._client is None:
            with self._lock:
                if self._client is None:
                    import chromadb
                    from chromadb.config import Settings
                    self._client = chromadb.PersistentClient(
                        path=self._path, settings=Settings(anonymized_telemetry=False)
                    )
        return self._client

    def _collection(self, namespace: str = ""):
        name = self._collection_prefix if not namespace else f"{self._collection_prefix}__{namespace}"
        return self._get_client().get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})

    def store(self, chunks, embeddings, namespace="", metadata_list=None):
        col = self._collection(namespace)
        ids, docs, vecs, metas = [], [], [], []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            meta: Dict[str, Any] = {"chunk_index": i}
            if metadata_list and i < len(metadata_list):
                meta.update(metadata_list[i])
            # Must match the deterministic BM25 corpus ID so RRF can fuse both rankings.
            ids.append(str(meta.get("chunk_id", f"chunk_{i}")))
            docs.append(chunk)
            vecs.append(list(embedding))
            metas.append(_clean_metadata(meta))
        for start in range(0, len(ids), _UPSERT_BATCH):
            end = start + _UPSERT_BATCH
            col.upsert(ids=ids[start:end], documents=docs[start:end],
                       embeddings=vecs[start:end], metadatas=metas[start:end])

    def search(self, query_vector, top_k=4, namespace="", filter=None):
        col = self._collection(namespace)
        total = col.count()
        if total == 0:
            return []
        result = col.query(
            query_embeddings=[list(query_vector)],
            n_results=min(top_k, total),
            where=filter or None,
            include=["documents", "metadatas", "distances"],
        )
        out: List[dict] = []
        for cid, text, meta, dist in zip(result["ids"][0], result["documents"][0],
                                         result["metadatas"][0], result["distances"][0]):
            out.append({
                "id": cid,
                "score": round(max(0.0, min(1.0, 1.0 - float(dist))), 4),
                "text": text or "",
                "metadata": dict(meta or {}),
            })
        return out

    def delete_document(self, document_name, namespace=""):
        self._collection(namespace).delete(where={"document_name": {"$eq": document_name}})

    def count(self, namespace=""):
        return self._collection(namespace).count()

    def status(self):
        import chromadb
        col = self._collection()
        return {
            "backend": self.name,
            "version": getattr(chromadb, "__version__", "unknown"),
            "path": self._path,
            "collection": col.name,
            "chunks": col.count(),
            "distance": "cosine",
        }


_store: Optional[VectorStore] = None
_store_lock = threading.Lock()


def get_vector_store() -> VectorStore:
    """Process-wide singleton store."""
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = ChromaVectorStore(str(VECTOR_STORE_DIR), VECTOR_STORE_COLLECTION)
    return _store


# ── Functional API used by ingestion / retrieval / evaluation ──────────────

def store_chunks(chunks: List[str], embeddings: List[List[float]], namespace: str = "",
                 metadata_list: Optional[List[Dict[str, Any]]] = None) -> None:
    get_vector_store().store(chunks, embeddings, namespace=namespace, metadata_list=metadata_list)


def search_chunks(query_vector: List[float], top_k: int = 4, namespace: str = "",
                  filter: Optional[Dict[str, Any]] = None) -> List[dict]:
    """Return ``[{id, score, text, metadata}]`` ordered best-first."""
    return get_vector_store().search(query_vector, top_k=top_k, namespace=namespace, filter=filter)


def delete_document(document_name: str, namespace: str = "") -> None:
    """Remove existing vectors for a document before it is re-indexed."""
    get_vector_store().delete_document(document_name, namespace=namespace)


def count_chunks(namespace: str = "") -> int:
    return get_vector_store().count(namespace=namespace)


def vector_store_status() -> Dict[str, Any]:
    return get_vector_store().status()
