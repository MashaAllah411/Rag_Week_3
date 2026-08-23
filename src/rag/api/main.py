# ============================================================
# app/main.py
#
# FastAPI application factory.
# Mounts all routers and serves static files + Jinja2 templates.
# ============================================================

import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from rag.config import FRONTEND_ORIGINS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Import routers
from rag.api.routes import ask, evaluate, failures, documents

# ── Build FastAPI app ────────────────────────────────────────

app = FastAPI(
    title="HR Policy RAG — Debugging Retrieval",
    description=(
        "Week 4 · Module 2 — Retrieval & RAG\n\n"
        "Hybrid search, reranking, failure separation, and before/after hit-rate proof.\n\n"
        "**Pipeline:** Query Rewriting → Hybrid Search (BM25 + Pinecone + RRF) "
        "→ Cross-Encoder Reranking → MMR → Grounded LLM Answer"
    ),
    version="4.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS — allow all origins for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files & Templates ─────────────────────────────────
_WEB_DIR = Path(__file__).resolve().parents[1] / "web"
_STATIC_DIR = _WEB_DIR / "static"
_TEMPLATES_DIR = _WEB_DIR / "templates"

if _STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

templates = Jinja2Templates(directory=_TEMPLATES_DIR)

# ── Register API routers ─────────────────────────────────────
app.include_router(ask.router,       prefix="/api",           tags=["Q&A"])
app.include_router(evaluate.router,  prefix="/api/evaluate",  tags=["Evaluation"])
app.include_router(failures.router,  prefix="/api/failures",  tags=["Failure Analysis"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])


# ── Serve SPA ────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def serve_ui(request: Request):
    return templates.TemplateResponse(request, "index.html")


# ── Health check ─────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "service": "RAG Week 4 M2", "version": "4.0.0"}


logger.info("FastAPI app created — HR Policy RAG v4.0.0")
