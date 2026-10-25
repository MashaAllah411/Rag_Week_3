"""Ingest PDFs into the vector store (read -> chunk -> embed -> store).

Run with ``python -m rag.ingestion.indexer`` to index the configured document.
"""
import logging
import threading
from pathlib import Path
from typing import Any, Dict

from rag.config import DEFAULT_DOCUMENT_PATH, RESOURCES_DIR
from rag.ingestion.pdfreader import read_pdf
from rag.ingestion.chunker import chunk_pages
from rag.core.document_ids import document_id
from rag.storage.embedder import embed_chunks
from rag.storage.vectorstore import count_chunks, delete_document, store_chunks

logger = logging.getLogger(__name__)

# Lightweight, thread-safe progress record surfaced by /api/system/status.
_state_lock = threading.Lock()
_index_state: Dict[str, Any] = {"state": "idle", "current": None, "last_error": None, "documents_done": 0}


def get_index_state() -> Dict[str, Any]:
    with _state_lock:
        return dict(_index_state)


def _set_state(**changes: Any) -> None:
    with _state_lock:
        _index_state.update(changes)


def run(pdf_path=DEFAULT_DOCUMENT_PATH):
    pdf_path = Path(pdf_path)
    pages = read_pdf(str(pdf_path))
    chunks = chunk_pages(pages)
    embeddings = embed_chunks(chunks)
    doc_id = document_id(pdf_path.name)
    metadata = [
        {
            "chunk_id": f"{doc_id}:chunk_{index}",
            "document_id": doc_id,
            "document_name": pdf_path.name,
        }
        for index in range(len(chunks))
    ]
    delete_document(pdf_path.name)
    store_chunks(chunks, embeddings, metadata_list=metadata)
    logger.info("Indexed %s chunks from %s", len(chunks), pdf_path.name)
    return len(chunks)


def reindex_all() -> int:
    """Replace vectors for every PDF in resources with document-aware IDs."""
    total_chunks = 0
    pdfs = sorted(RESOURCES_DIR.glob("*.pdf"))
    _set_state(state="indexing", last_error=None, documents_done=0)
    try:
        for pdf_path in pdfs:
            _set_state(current=pdf_path.name)
            total_chunks += run(pdf_path)
            _set_state(documents_done=get_index_state()["documents_done"] + 1)
    except Exception as exc:
        _set_state(state="error", current=None, last_error=str(exc))
        raise
    _set_state(state="idle", current=None)
    logger.info("Re-indexed %s PDFs (%s chunks)", len(pdfs), total_chunks)
    return total_chunks


def bootstrap_if_empty() -> bool:
    """Index resources/ in the background when the local vector store is empty.

    A fresh ChromaDB store starts empty (unlike the old hosted index), so the API
    calls this once at startup. Returns True if indexing was started.
    """
    try:
        if count_chunks() > 0 or not any(RESOURCES_DIR.glob("*.pdf")):
            return False
    except Exception:
        logger.exception("Vector store unavailable; skipping bootstrap indexing")
        return False

    def _job() -> None:
        try:
            from rag.retrieval.bm25 import reset_bm25_index
            reindex_all()
            reset_bm25_index()
        except Exception:
            logger.exception("Bootstrap indexing failed")

    threading.Thread(target=_job, name="bootstrap-indexer", daemon=True).start()
    logger.info("Vector store is empty - bootstrap indexing started in background")
    return True


if __name__ == "__main__":
    run()
