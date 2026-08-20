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
import uvicorn

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  HR Policy RAG -- Week 4 M2")
    print("  Debugging Retrieval: Hybrid, Reranking & Failure Separation")
    print("=" * 60)
    print("\n  UI   ->  http://localhost:8000")
    print("  Docs ->  http://localhost:8000/api/docs")
    print("\n" + "=" * 60 + "\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
