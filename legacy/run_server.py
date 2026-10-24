# ============================================================
# run_server.py  -- Entry point
#
# Usage:
#   python run_server.py
#
# Opens:  http://localhost:8000
# Docs:   http://localhost:8000/api/docs
# ============================================================

import sys
import io
from pathlib import Path
import uvicorn

# Make the src-layout package runnable directly from a fresh checkout.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from rag.config import BACKEND_PORT

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  HR Policy RAG -- Week 4 M2")
    print("  Debugging Retrieval: Hybrid, Reranking & Failure Separation")
    print("=" * 60)
    print(f"\n  UI   ->  http://localhost:{BACKEND_PORT}")
    print(f"  Docs ->  http://localhost:{BACKEND_PORT}/api/docs")
    print("\n" + "=" * 60 + "\n")

    uvicorn.run(
        "rag.api.main:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=True,
        reload_excludes=[".venv", "__pycache__", "*.pyc"],
        log_level="info",
    )
