import os
import re
import logging
from typing import List, Dict
from fastapi import APIRouter
from pypdf import PdfReader

logger = logging.getLogger(__name__)
router = APIRouter()

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_RESOURCES_DIR = os.path.join(_ROOT, "resources")


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
                "vector_index": os.environ.get("PINECONE_INDEX_NAME", "rag-week-3-py"),
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
        "index_name": os.environ.get("PINECONE_INDEX_NAME", "rag-week-3-py"),
    }

