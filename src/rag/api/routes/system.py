# ============================================================
# src/rag/api/routes/system.py
#
# System page endpoints: health, environment configuration
# (with secrets strictly masked), model stats, and recent logs.
# ============================================================

import os
import glob
from fastapi import APIRouter
from rag.config import (
    EMBEDDING_MODEL,
    RERANKER_MODEL,
    OLLAMA_MODEL,
    PINECONE_INDEX_NAME,
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


@router.get("/status", summary="Get system status and component health")
async def get_system_status():
    """Returns status of Pinecone, Ollama, embedding model, and file storage."""
    pinecone_key = os.getenv("PINECONE_API_KEY", "")

    # Check Ollama connection
    ollama_ok = False
    try:
        import ollama
        ollama.list()
        ollama_ok = True
    except Exception:
        ollama_ok = False

    # Check Pinecone
    pinecone_ok = bool(pinecone_key and PINECONE_INDEX_NAME)

    # Document stats
    pdf_count = 0
    if os.path.exists(RESOURCES_DIR):
        pdf_count = len(glob.glob(os.path.join(str(RESOURCES_DIR), "*.pdf")))

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
            "pinecone_vector_db": {
                "index_name": PINECONE_INDEX_NAME or "not configured",
                "configured": pinecone_ok
            },
            "embedding_model": {
                "name": EMBEDDING_MODEL,
                "dimensions": 384
            },
            "reranker_model": {
                "name": RERANKER_MODEL
            }
        },
        "storage": {
            "resources_dir": str(RESOURCES_DIR),
            "data_dir": str(DATA_DIR),
            "pdf_documents_count": pdf_count
        },
        "config_masked": {
            "PINECONE_API_KEY": _mask_secret(pinecone_key),
            "PINECONE_INDEX_NAME": PINECONE_INDEX_NAME,
            "OLLAMA_MODEL": OLLAMA_MODEL,
            "EMBEDDING_MODEL": EMBEDDING_MODEL,
            "RERANKER_MODEL": RERANKER_MODEL,
            "RAG_DOCUMENT": os.path.basename(str(DEFAULT_DOCUMENT_PATH)),
            "BACKEND_PORT": BACKEND_PORT,
            "FRONTEND_ORIGINS": FRONTEND_ORIGINS
        }
    }


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
