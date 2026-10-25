"""Central application settings and repository paths."""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPOSITORY_ROOT / ".env")
DATA_DIR = REPOSITORY_ROOT / "data"
RESOURCES_DIR = REPOSITORY_ROOT / "resources"
DEFAULT_DOCUMENT_PATH = RESOURCES_DIR / os.getenv("RAG_DOCUMENT", "InsurancePolicy.pdf")
BASELINE_RESULTS_PATH = DATA_DIR / "baseline_results.json"
HYBRID_RESULTS_PATH = DATA_DIR / "hybrid_results.json"
EVALUATION_DATASET_PATH = DATA_DIR / "evaluation_dataset.json"
FAILURE_LABELS_PATH = DATA_DIR / "failure_labels.json"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
# Vector store (ChromaDB, embedded + persistent; replaces the hosted Pinecone service)
VECTOR_STORE_DIR = Path(os.getenv("VECTOR_STORE_DIR", str(DATA_DIR / "vectorstore")))
if not VECTOR_STORE_DIR.is_absolute():
    VECTOR_STORE_DIR = REPOSITORY_ROOT / VECTOR_STORE_DIR
VECTOR_STORE_COLLECTION = os.getenv("VECTOR_STORE_COLLECTION", "insurance_rag")
# Tracing (OpenTelemetry SDK). Set OTEL_EXPORTER_OTLP_ENDPOINT to also ship spans to
# any OTLP collector (e.g. self-hosted Arize Phoenix / Jaeger); local JSONL export is always on.
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "insurance-rag")
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
OTEL_SPANS_PATH = REPOSITORY_ROOT / "traces" / "otel_spans.jsonl"
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_ORIGINS = [item.strip() for item in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if item.strip()]
