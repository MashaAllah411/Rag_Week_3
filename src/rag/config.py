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
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_ORIGINS = [item.strip() for item in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if item.strip()]
