# ============================================================
# src/rag/api/main.py
#
# FastAPI application factory for Insurance RAG Stack.
# Mounts all API routers: ask, documents, evaluate, failures,
# agent, mcp, multi_agent, observability, and system.
# ============================================================

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    system,
    foundations,
    guardrails,
    capstone,
)

# ── Startup / shutdown ───────────────────────────────────────

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialise tracing and index resources/ into the local vector store if it is empty."""
    try:
        from rag.observability.otel import init_tracing
        init_tracing()
    except Exception:
        logger.exception("Tracing initialisation failed (continuing without OpenTelemetry)")
    try:
        from rag.ingestion.indexer import bootstrap_if_empty
        bootstrap_if_empty()
    except Exception:
        logger.exception("Bootstrap indexing could not start")
    yield


# ── Build FastAPI app ────────────────────────────────────────

app = FastAPI(
    lifespan=lifespan,
    title="Insurance Policy & Claims RAG Platform",
    description=(
        "Production-Style RAG Application covering Weeks 1–11:\n\n"
        "- **Retrieval & RAG**: Hybrid search (BM25 + ChromaDB via RRF), Cross-Encoder reranking, MMR, Scope Guard, Query Rewriting\n"
        "- **Agent Loops**: ReAct Agent with 4 budgets vs Fixed Workflow\n"
        "- **MCP Protocol**: JSON-RPC 2.0 dynamic tool discovery & server orchestration\n"
        "- **Multi-Agent Squad**: Manager + Policy Specialist + Payout Specialist A2A protocol\n"
        "- **Observability & QA**: OpenTelemetry spans per request step, support triage drill, semantic caching, failure-to-test loop"
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
app.include_router(foundations.router,   prefix="/api/foundations",  tags=["Foundations Lab (Week 1)"])
app.include_router(guardrails.router,    prefix="/api/guardrails",   tags=["Guardrails & Structured Output (Weeks 2, 8)"])
app.include_router(capstone.router,      prefix="/api/capstone",     tags=["Capstone (Week 12)"])


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
