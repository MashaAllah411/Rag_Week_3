"""
providers.py

Provider interfaces and lightweight adapters that wrap the existing modules.
This allows a single place to change implementations (e.g., swap ChromaDB for FAISS)
without touching pipeline orchestration.
"""
from typing import List, Callable, Any, Dict


class EmbeddingProvider:
    def embed_user_query(self, query: str) -> List[float]:
        raise NotImplementedError()

    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        raise NotImplementedError()


class VectorStoreProvider:
    def store(self, chunks: List[str], embeddings: List[List[float]], namespace: str = "", metadata_list: List[Dict[str, Any]] = None):
        raise NotImplementedError()

    def search(self, query_vector: List[float], top_k: int = 4, namespace: str = "", filter: Dict[str, Any] = None) -> List[dict]:
        raise NotImplementedError()


class LLMProvider:
    def query_with_context(self, query: str, context: str) -> str:
        raise NotImplementedError()


# --- Adapters that wrap the current implementation ---

def get_embedding_provider() -> EmbeddingProvider:
    """Return an EmbeddingProvider that wraps embedder.py."""
    class _Provider(EmbeddingProvider):
        def __init__(self):
            from rag.storage.embedder import embed_user_query as _embed_user_query
            from rag.storage.embedder import embed_chunks as _embed_chunks
            self._embed_user_query = _embed_user_query
            self._embed_chunks = _embed_chunks

        def embed_user_query(self, query: str) -> List[float]:
            return self._embed_user_query(query)

        def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
            return self._embed_chunks(chunks)

    return _Provider()


def get_vectorstore_provider() -> VectorStoreProvider:
    class _Provider(VectorStoreProvider):
        def __init__(self):
            from rag.storage.vectorstore import store_chunks as _store
            from rag.storage.vectorstore import search_chunks as _search
            self._store = _store
            self._search = _search

        def store(self, chunks: List[str], embeddings: List[List[float]], namespace: str = "", metadata_list: List[Dict[str, Any]] = None):
            return self._store(chunks, embeddings, namespace=namespace, metadata_list=metadata_list)

        def search(self, query_vector: List[float], top_k: int = 4, namespace: str = "", filter: Dict[str, Any] = None) -> List[dict]:
            return self._search(query_vector, top_k=top_k, namespace=namespace, filter=filter)

    return _Provider()


def get_llm_provider() -> LLMProvider:
    class _Provider(LLMProvider):
        def __init__(self):
            from rag.generation.llm import query_llm_with_context as _q
            self._q = _q

        def query_with_context(self, query: str, context: str) -> str:
            return self._q(query, context)

    return _Provider()


def get_hybrid_retriever():
    """Light wrapper returning the hybrid_search function from hybrid_retriever."""
    from rag.retrieval.hybrid_retriever import hybrid_search as _hybrid
    return _hybrid


def get_query_rewriter():
    from rag.core.query_rewriter import rewrite_query as _rw
    return _rw


def get_reranker():
    from rag.retrieval.reranker import rerank_chunks as _rr
    return _rr


def get_mmr():
    from rag.retrieval.mmr import apply_mmr as _mmr
    return _mmr
