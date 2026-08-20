# ============================================================
# app/models/schemas.py
#
# Pydantic models for FastAPI request/response validation.
# ============================================================

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


# ── Request Models ───────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, description="The question to ask against the HR Policy")
    mode: Literal["semantic", "hybrid", "reranked"] = Field(
        default="hybrid",
        description="Retrieval mode: semantic (Pinecone only), hybrid (BM25+RRF), reranked (hybrid + cross-encoder)"
    )
    top_k: int = Field(default=3, ge=1, le=10, description="Number of chunks to retrieve")
    similarity_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity score to proceed to LLM")
    use_query_rewriter: bool = Field(default=True, description="Whether to rewrite the query with Llama 3.2 before search")


class EvaluateRequest(BaseModel):
    mode: Literal["semantic", "hybrid"] = Field(default="hybrid", description="Which retrieval mode to evaluate")
    top_k: int = Field(default=3, ge=1, le=10)


class LabelRequest(BaseModel):
    question: str
    label: Literal["retrieval_failure", "generation_failure", "pass"]
    evidence: Optional[str] = None


# ── Response Models ──────────────────────────────────────────

class ChunkResult(BaseModel):
    chunk_id: str
    score: float
    text: str
    semantic_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    rerank_score: Optional[float] = None


class AskResponse(BaseModel):
    question: str
    rewritten_query: Optional[str] = None
    answer: str
    retrieved_chunks: List[ChunkResult]
    mode: str
    confidence: str           # "high" / "low" / "unknown"
    source_document: str = "InsurancePolicy.pdf"
    pipeline_steps: List[str]


class PerQuestionResult(BaseModel):
    question: str
    relevant_chunks: List[str]
    retrieved_ids: List[str]
    hit: int
    recall: float
    reciprocal_rank: float
    failure_type: Optional[str] = None   # "retrieval_failure" | "generation_failure" | None


class EvaluateResponse(BaseModel):
    retriever: str
    top_k: int
    num_questions: int
    hit_rate: float
    recall: float
    mrr: float
    per_question: List[PerQuestionResult]


class FailureLabel(BaseModel):
    question: str
    label: str
    evidence: Optional[str] = None
    auto_labeled: bool = False


class FailuresResponse(BaseModel):
    labels: List[FailureLabel]


class DocumentInfo(BaseModel):
    filename: str
    path: str
    num_pages: Optional[int] = None
    status: str = "indexed"
