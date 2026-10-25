"""Live self-tests: exercise each open-source tool for real (not just check configuration).

Shared by the System page (/api/system/selftest) and the Capstone suite.
"""
import time

from rag.config import EMBEDDING_MODEL


def _timed(name: str, fn) -> dict:
    start = time.time()
    try:
        result = fn()
        ok, detail = bool(result.get("ok")), result.get("detail", "")
    except Exception as exc:
        ok, detail = False, f"{type(exc).__name__}: {exc}"
    return {"check": name, "ok": ok, "detail": detail, "ms": round((time.time() - start) * 1000, 1)}


def _check_vector_store() -> dict:
    """Write two vectors to a scratch namespace, query, then delete them."""
    from rag.storage.vectorstore import store_chunks, search_chunks, delete_document, count_chunks
    vecs = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]]
    meta = [{"chunk_id": "selftest:a", "document_name": "selftest.pdf"},
            {"chunk_id": "selftest:b", "document_name": "selftest.pdf"}]
    delete_document("selftest.pdf", namespace="selftest")
    store_chunks(["alpha", "beta"], vecs, namespace="selftest", metadata_list=meta)
    hits = search_chunks([1.0, 0.0, 0.0, 0.0], top_k=1, namespace="selftest",
                         filter={"document_name": {"$eq": "selftest.pdf"}})
    delete_document("selftest.pdf", namespace="selftest")
    ok = bool(hits) and hits[0]["id"] == "selftest:a" and count_chunks(namespace="selftest") == 0
    return {"ok": ok, "detail": f"stored 2, nearest={hits[0]['id'] if hits else None} score={hits[0]['score'] if hits else None}, cleaned up"}


def _check_embedder() -> dict:
    from rag.storage.embedder import embed_user_query
    vec = embed_user_query("self test")
    return {"ok": len(vec) == 384, "detail": f"{EMBEDDING_MODEL} -> {len(vec)} dimensions"}


def _check_reranker() -> dict:
    from rag.retrieval.reranker import rerank_chunks
    out = rerank_chunks("water damage", [{"id": "a", "text": "Flood damage is excluded."},
                                         {"id": "b", "text": "Office hours are 9 to 5."}], top_k=2)
    return {"ok": len(out) == 2 and out[0]["id"] == "a", "detail": f"top={out[0]['id']} score={out[0].get('rerank_score')}"}


def _check_ocr() -> dict:
    from rag.ingestion.pdfreader import ocr_selftest
    return ocr_selftest()


def _check_tracing() -> dict:
    from rag.observability.otel import self_test
    return self_test()


def run_selftest(deep: bool = False) -> dict:
    """Runs a real round-trip through each tool. `deep=True` also loads the cross-encoder reranker."""
    checks = [
        _timed("Vector store (ChromaDB write/query/delete)", _check_vector_store),
        _timed("OpenTelemetry span export", _check_tracing),
        _timed("OCR (Tesseract reads rendered text)", _check_ocr),
        _timed("Embeddings (sentence-transformers)", _check_embedder),
    ]
    if deep:
        checks.append(_timed("Reranker (cross-encoder)", _check_reranker))
    return {"passed": sum(c["ok"] for c in checks), "total": len(checks), "checks": checks}
