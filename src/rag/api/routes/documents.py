import io
import os
import re
import logging
from typing import List, Dict
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pypdf import PdfReader
from rag.config import RESOURCES_DIR, PINECONE_INDEX_NAME

logger = logging.getLogger(__name__)
router = APIRouter()

_RESOURCES_DIR = str(RESOURCES_DIR)
_MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def _get_suggested_questions(filename: str) -> List[Dict[str, str]]:
    """Return tailored quick questions based on document context."""
    fname_lower = filename.lower()
    if "insurance" in fname_lower or "car" in fname_lower or "policy" in fname_lower:
        return [
            {"label": "IDV Depreciation?", "query": "What is the schedule of depreciation for fixing IDV of the vehicle?"},
            {"label": "Zero Dep Cover?", "query": "What are the rules and exclusions for Depreciation Reimbursement add-on cover?"},
            {"label": "Engine Guard?", "query": "What damages are covered under the Engine Guard add-on?"},
            {"label": "Personal Accident?", "query": "What is the compensation scale for Owner-Driver personal accident cover?"},
            {"label": "Roadside Assistance?", "query": "What services are provided under Basic Road-Side Assistance?"},
            {"label": "Consumables Cover?", "query": "What items are included under Cover for Consumables?"},
        ]
    elif "hr" in fname_lower:
        return [
            {"label": "Working hours?", "query": "What are the official working hours for staff?"},
            {"label": "Notice period?", "query": "How many weeks notice must a staff member give when resigning?"},
            {"label": "Recalled leave?", "query": "What happens if a staff member is recalled from annual leave?"},
            {"label": "Remote work?", "query": "What is the policy on remote work and leave?"},
        ]
    else:
        return [
            {"label": "Summary?", "query": "What is the main summary and purpose of this document?"},
            {"label": "Key terms?", "query": "What are the key definitions and terms explained in this document?"},
            {"label": "Exceptions?", "query": "What are the general exceptions and limitations mentioned?"},
            {"label": "Procedures?", "query": "What are the main rules, conditions, and procedures outlined?"},
        ]


def _format_display_title(filename: str) -> str:
    """Format a filename into a human-readable title."""
    name = os.path.splitext(filename)[0]
    # Split camelCase or PascalCase or snake_case / kebab-case
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+', name)
    if words:
        return " ".join(w.capitalize() for w in words)
    return name.replace("_", " ").replace("-", " ").title()


@router.get("", summary="List indexed documents")
async def list_documents():
    """
    Returns all documents located in the resources directory with metadata,
    pages, status, and dynamic suggested questions.
    """
    docs = []
    active_doc = None

    if os.path.isdir(_RESOURCES_DIR):
        pdf_files = [f for f in os.listdir(_RESOURCES_DIR) if f.lower().endswith(".pdf")]
        for fname in pdf_files:
            fpath = os.path.join(_RESOURCES_DIR, fname)
            size_kb = round(os.path.getsize(fpath) / 1024, 1)
            num_pages = 0
            try:
                reader = PdfReader(fpath)
                num_pages = len(reader.pages)
            except Exception as e:
                logger.warning(f"Could not read page count for {fname}: {e}")

            display_title = _format_display_title(fname)
            questions = _get_suggested_questions(fname)

            doc_info = {
                "filename": fname,
                "title": display_title,
                "badge": display_title if len(display_title) <= 16 else display_title[:14] + "..",
                "path": fpath,
                "size_kb": size_kb,
                "pages": num_pages,
                "status": "indexed",
                "vector_index": PINECONE_INDEX_NAME or "not configured",
                "embedding_model": "all-MiniLM-L6-v2",
                "chunking_strategy": "fixed-size (900 chars, 150 overlap)",
                "suggested_questions": questions,
            }
            docs.append(doc_info)

    if docs:
        active_doc = docs[0]

    return {
        "active_document": active_doc,
        "documents": docs,
        "count": len(docs),
        "vector_db": "Pinecone",
        "index_name": PINECONE_INDEX_NAME or "not configured",
    }


@router.post("/upload", status_code=202, summary="Upload and index a PDF document")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Store a PDF in resources and index it in the background."""
    filename = os.path.basename(file.filename or "")
    if not filename or not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files can be uploaded.")

    content = await file.read()
    if not content or len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Upload must be a non-empty PDF smaller than 20 MB.")
    try:
        PdfReader(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The uploaded file is not a readable PDF.") from exc

    os.makedirs(_RESOURCES_DIR, exist_ok=True)
    destination = os.path.join(_RESOURCES_DIR, filename)
    if os.path.exists(destination):
        raise HTTPException(status_code=409, detail="A document with this filename already exists.")
    with open(destination, "xb") as output:
        output.write(content)

    def index_upload(path: str) -> None:
        try:
            from rag.scripts.dataprocessor import run
            from rag.core.retrieval.bm25 import reset_bm25_index
            run(path)
            reset_bm25_index()
            logger.info("Uploaded document indexed: %s", filename)
        except Exception:
            logger.exception("Failed to index uploaded document: %s", filename)

    background_tasks.add_task(index_upload, destination)
    return {"status": "indexing", "filename": filename, "message": "Upload saved. Indexing has started."}


@router.delete("/{filename}", summary="Delete a document and its indexed chunks")
async def delete_document(filename: str):
    """Delete one locally stored PDF and all Pinecone vectors linked to it."""
    safe_filename = os.path.basename(filename)
    if safe_filename != filename or not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid document filename.")

    document_path = os.path.join(_RESOURCES_DIR, safe_filename)
    if not os.path.isfile(document_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        from rag.infra.vectorstore import delete_document_from_pinecone
        from rag.core.retrieval.bm25 import reset_bm25_index
        delete_document_from_pinecone(safe_filename)
        os.remove(document_path)
        reset_bm25_index()
    except Exception as exc:
        logger.exception("Failed to delete document: %s", safe_filename)
        raise HTTPException(status_code=500, detail="Could not remove the document and its indexed chunks.") from exc

    return {"status": "deleted", "filename": safe_filename}

