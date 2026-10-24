# ============================================================
# src/rag/api/main.py
#
# FastAPI application factory for Insurance RAG Stack.
# Mounts all API routers: ask, documents, evaluate, failures,
# agent, mcp, multi_agent, observability, and system.
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
from rag.api.routes import (
    ask,
    evaluate,
    failures,
    documents,
    agent,
    mcp,
    multi_agent,
    observability,
    system
)

# ── Build FastAPI app ────────────────────────────────────────

app = FastAPI(
    title="Insurance Policy & Claims RAG Platform",
    description=(
        "Production-Style RAG Application covering Weeks 1–11:\n\n"
        "- **Retrieval & RAG**: Hybrid search (BM25 + Pinecone via RRF), Cross-Encoder reranking, MMR, Scope Guard, Query Rewriting\n"
        "- **Agent Loops**: ReAct Agent with 4 budgets vs Fixed Workflow\n"
        "- **MCP Protocol**: JSON-RPC 2.0 dynamic tool discovery & server orchestration\n"
        "- **Multi-Agent Squad**: Manager + Policy Specialist + Payout Specialist A2A protocol\n"
        "- **Observability & QA**: Granular OpenTelemetry spans, support triage drill, semantic caching, failure-to-test loop"
    ),
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS — allow configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files & Templates (Legacy SPA preserved) ─────────
_WEB_DIR = Path(__file__).resolve().parents[1] / "web"
_STATIC_DIR = _WEB_DIR / "static"
_TEMPLATES_DIR = _WEB_DIR / "templates"

if _STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

if _TEMPLATES_DIR.is_dir():
    templates = Jinja2Templates(directory=_TEMPLATES_DIR)

    @app.get("/legacy-web", include_in_schema=False)
    async def serve_legacy_ui(request: Request):
        return templates.TemplateResponse(request, "index.html")


# ── Register API routers ─────────────────────────────────────
app.include_router(ask.router,           prefix="/api",              tags=["Search & Q&A"])
app.include_router(documents.router,     prefix="/api/documents",    tags=["Documents"])
app.include_router(evaluate.router,      prefix="/api/evaluate",     tags=["Evaluation & Judge"])
app.include_router(failures.router,      prefix="/api/failures",     tags=["Failure Analysis"])
app.include_router(agent.router,         prefix="/api/agent",        tags=["Agent Loops & Benchmark"])
app.include_router(mcp.router,           prefix="/api/mcp",          tags=["MCP Ecosystem"])
app.include_router(multi_agent.router,   prefix="/api/multi-agent",  tags=["Multi-Agent Squad"])
app.include_router(observability.router, prefix="/api/observability",tags=["Observability & Caching"])
app.include_router(system.router,        prefix="/api/system",       tags=["System"])


# ── Root & Health check ──────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    return {
        "service": "Insurance Policy & Claims RAG Platform",
        "version": "2.0.0",
        "status": "online",
        "docs": "/api/docs",
        "health": "/health"
    }


@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "service": "Insurance Policy & Claims RAG Platform",
        "version": "2.0.0"
    }


logger.info("FastAPI app initialized — Insurance Policy & Claims RAG Platform v2.0.0")
