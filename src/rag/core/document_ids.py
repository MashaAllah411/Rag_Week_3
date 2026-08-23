"""Stable identifiers shared by ingestion, retrieval, and the UI."""
from __future__ import annotations

import re
from pathlib import Path


def document_id(filename: str | Path) -> str:
    stem = Path(filename).stem.lower()
    return re.sub(r"[^a-z0-9]+", "-", stem).strip("-") or "document"
