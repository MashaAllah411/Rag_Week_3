# ============================================================
# src/rag/api/routes/system.py
#
# System page endpoints: component health, the live open-source tool report,
# a self-test that exercises each tool for real, environment configuration
# (secrets strictly masked), and recent logs.
# ============================================================

import os
import glob
import time
from fastapi import APIRouter
from rag.config import (
    EMBEDDING_MODEL,
    RERANKER_MODEL,
    OLLAMA_MODEL,
    VECTOR_STORE_COLLECTION,
    VECTOR_STORE_DIR,
    OTEL_SERVICE_NAME,
    OTEL_EXPORTER_OTLP_ENDPOINT,
    BACKEND_PORT,
    FRONTEND_ORIGINS,
    DEFAULT_DOCUMENT_PATH,
    DATA_DIR,
    RESOURCES_DIR
)

router = APIRouter()


def _mask_secret(secret: str | None) -> str:
    """Masks secret so only first 4 and last 4 characters are visible."""
    if not secret:
        return "not set"
    if len(secret) <= 8:
        return "****"
    return secret[:4] + "*" * (len(secret) - 8) + secret[-4:]


def _ollama_reachable() -> bool:
    try:
        import ollama
        ollama.list()
        return True
    except Exception:
        return False


def _vector_store_info() -> dict:
    try:
        from rag.storage.vectorstore import vector_store_status
        info = vector_store_status()
        info["reachable"] = True
        return info
    except Exception as exc:
        return {"backend": "chromadb", "reachable": False, "error": f"{type(exc).__name__}: {exc}",
                "chunks": 0, "collection": VECTOR_STORE_COLLECTION, "path": str(VECTOR_STORE_DIR)}


@router.get("/status", summary="Get system status and component health")
async def get_system_status():
    """Component health plus the live open-source stack (what is loaded, not just configured)."""
    from rag.ingestion.pdfreader import ocr_status
    from rag.ingestion.indexer import get_index_state
    from rag.observability.otel import tracing_status
    from rag.storage import embedder
    from rag.retrieval import reranker

    ollama_ok = _ollama_reachable()
    vs = _vector_store_info()
    ocr = ocr_status()
    tracing = tracing_status()
    index_state = get_index_state()

    pdf_count = 0
    if os.path.exists(RESOURCES_DIR):
        pdf_count = len(glob.glob(os.path.join(str(RESOURCES_DIR), "*.pdf")))

    open_source_stack = [
        {"capability": "Vector store", "tool": "ChromaDB", "replaces": "Pinecone (hosted SaaS)", "week": 3,
         "license": "Apache-2.0", "active": vs["reachable"],
         "detail": f"{vs.get('chunks', 0)} chunks in collection '{vs.get('collection')}' ({vs.get('path')})"
                   if vs["reachable"] else vs.get("error", "unreachable")},
        {"capability": "Tracing", "tool": "OpenTelemetry SDK", "replaces": "custom span dataclass (OTel-'compatible' only)",
         "week": 11, "license": "Apache-2.0", "active": tracing["active"],
         "detail": ("exporters: " + ", ".join(e["type"] for e in tracing["exporters"]) +
                    f" | {tracing['spans_exported']} spans exported this run") if tracing["active"]
                   else (tracing.get("error") or "SDK not installed")},
        {"capability": "OCR", "tool": ocr["engine"], "replaces": "already open source (no swap needed)", "week": 3,
         "license": "Apache-2.0", "active": ocr["available"],
         "detail": f"version {ocr.get('version', '?')}" if ocr["available"] else "Tesseract executable not found - OCR disabled"},
        {"capability": "Embeddings", "tool": f"sentence-transformers / {EMBEDDING_MODEL}", "replaces": "already open source",
         "week": 3, "license": "Apache-2.0", "active": True,
         "detail": "model loaded in memory" if embedder.is_loaded() else "loads on first use"},
        {"capability": "Reranker", "tool": f"Cross-encoder / {RERANKER_MODEL}", "replaces": "already open source",
         "week": 4, "license": "Apache-2.0", "active": True,
         "detail": "model loaded in memory" if reranker.is_loaded() else "loads on first use"},
        {"capability": "Keyword search", "tool": "rank-bm25 (BM25Okapi)", "replaces": "already open source",
         "week": 4, "license": "Apache-2.0", "active": True, "detail": "in-memory index built from PDFs"},
        {"capability": "LLM", "tool": f"Ollama / {OLLAMA_MODEL}", "replaces": "already open source (local)",
         "week": 2, "license": "MIT (Ollama), model licence varies", "active": ollama_ok,
         "detail": "reachable" if ollama_ok else "Ollama not running - run `ollama serve` and `ollama pull " + OLLAMA_MODEL + "`"},
    ]

    return {
        "status": "healthy",
        "backend": {
            "version": "2.0.0",
            "port": BACKEND_PORT,
            "status": "running"
        },
        "components": {
            "ollama_llm": {
                "model": OLLAMA_MODEL,
                "reachable": ollama_ok
            },
            "vector_store": {
                "backend": vs.get("backend"),
                "collection": vs.get("collection"),
                "chunks": vs.get("chunks", 0),
                "reachable": vs["reachable"],
            },
            "embedding_model": {
                "name": EMBEDDING_MODEL,
                "dimensions": 384
            },
            "reranker_model": {
                "name": RERANKER_MODEL
            },
            "ocr": ocr,
            "tracing": tracing,
        },
        "indexing": index_state,
        "open_source_stack": open_source_stack,
        "storage": {
            "resources_dir": str(RESOURCES_DIR),
            "data_dir": str(DATA_DIR),
            "pdf_documents_count": pdf_count
        },
        "config_masked": {
            "VECTOR_STORE_DIR": str(VECTOR_STORE_DIR),
            "VECTOR_STORE_COLLECTION": VECTOR_STORE_COLLECTION,
            "OLLAMA_MODEL": OLLAMA_MODEL,
            "EMBEDDING_MODEL": EMBEDDING_MODEL,
            "RERANKER_MODEL": RERANKER_MODEL,
            "OTEL_SERVICE_NAME": OTEL_SERVICE_NAME,
            "OTEL_EXPORTER_OTLP_ENDPOINT": OTEL_EXPORTER_OTLP_ENDPOINT or "not set (local JSONL only)",
            "RAG_DOCUMENT": os.path.basename(str(DEFAULT_DOCUMENT_PATH)),
            "BACKEND_PORT": BACKEND_PORT,
            "FRONTEND_ORIGINS": FRONTEND_ORIGINS
        }
    }


@router.post("/selftest", summary="Exercise each open-source tool for real")
async def run_selftest(deep: bool = False):
    """Runs a real round-trip through each tool. `deep=true` also loads the cross-encoder reranker."""
    from rag.services.health_service import run_selftest as _run
    return _run(deep=deep)


@router.get("/logs", summary="Get recent application logs")
async def get_system_logs(lines: int = 100):
    """Returns the most recent log entries from logs/ directory."""
    log_dir = "logs"
    entries = []
    if os.path.exists(log_dir):
        log_files = glob.glob(os.path.join(log_dir, "*.log"))
        for lf in log_files:
            fname = os.path.basename(lf)
            try:
                with open(lf, "r", encoding="utf-8", errors="ignore") as f:
                    file_lines = f.readlines()
                    tail = file_lines[-lines:]
                    entries.append({
                        "file": fname,
                        "lines": [l.strip() for l in tail if l.strip()]
                    })
            except Exception:
                continue

    return {"logs": entries}
