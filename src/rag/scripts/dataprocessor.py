"""Ingest the configured document into Pinecone.

Run with ``python -m rag.scripts.dataprocessor`` after configuring Pinecone.
"""
import logging
from pathlib import Path
from rag.config import DEFAULT_DOCUMENT_PATH, RESOURCES_DIR
from rag.core.ingest.pdfreader import read_pdf
from rag.core.ingest.chunker import chunk_pages
from rag.core.document_ids import document_id
from rag.infra.embedder import embed_chunks
from rag.infra.vectorstore import delete_document_from_pinecone, store_in_pinecone

logger = logging.getLogger(__name__)


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
    delete_document_from_pinecone(pdf_path.name)
    store_in_pinecone(chunks, embeddings, metadata_list=metadata)
    logger.info("Indexed %s chunks from %s", len(chunks), pdf_path.name)
    return len(chunks)


def reindex_all() -> int:
    """Replace vectors for every PDF in resources with document-aware IDs."""
    total_chunks = 0
    for pdf_path in sorted(RESOURCES_DIR.glob("*.pdf")):
        total_chunks += run(pdf_path)
    logger.info("Re-indexed %s PDFs (%s chunks)", len(list(RESOURCES_DIR.glob("*.pdf"))), total_chunks)
    return total_chunks
 


if __name__ == "__main__":
    run()
