# ============================================================
# src/rag/models/schemas.py
#
# Pydantic models for FastAPI request/response validation.
# ============================================================

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal


# ── Q&A & Ingestion ──────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, description="The question to ask against the policy")
    mode: Literal["semantic", "hybrid", "reranked"] = Field(
        default="hybrid",
        description="Retrieval mode: semantic (Pinecone only), hybrid (BM25+RRF), reranked (hybrid + cross-encoder + MMR)"
    )
    top_k: int = Field(default=3, ge=1, le=10, description="Number of chunks to retrieve")
    similarity_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity score")
    use_query_rewriter: bool = Field(default=True, description="Whether to rewrite the query with local LLM before search")
    document_name: Optional[str] = Field(default=None, description="Optional document filename filter")


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


class DocumentInfo(BaseModel):
    filename: str
    title: str
    badge: str
    path: str
    size_kb: float
    pages: int
    status: str = "indexed"
    vector_index: str
    embedding_model: str
    chunking_strategy: str
    suggested_questions: List[Dict[str, str]]


# ── Evaluation & Failure Analysis ────────────────────────────

class EvaluateRequest(BaseModel):
    mode: Literal["semantic", "hybrid"] = Field(default="hybrid", description="Which retrieval mode to evaluate")
    top_k: int = Field(default=3, ge=1, le=10)


class LabelRequest(BaseModel):
    question: str
    label: Literal["retrieval_failure", "generation_failure", "pass"]
    evidence: Optional[str] = None


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


class JudgeEvalRequest(BaseModel):
    query: str
    context: str
    answer: str
    judge_version: Literal["v1", "v2"] = "v2"


class AssertionCheckRequest(BaseModel):
    text: str
    is_denial: bool = False


# ── Agent Triage (Weeks 7 & 8) ───────────────────────────────

class AgentTriageRequest(BaseModel):
    claim_id: str = Field(default="CLM-7001", description="Claim identifier (e.g. CLM-7001)")
    system_type: Literal["agent_loop", "fixed_workflow"] = "agent_loop"
    force_budget_exceed: Optional[Literal["iterations", "tokens", "cost", "timeout"]] = None


class AgentBenchmarkRequest(BaseModel):
    claims: Optional[List[str]] = None


# ── MCP Ecosystem (Week 9) ───────────────────────────────────

class McpToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class McpTriageRequest(BaseModel):
    claim_id: str = "CLM-7002"
    config_filename: Optional[str] = None


class McpConfigSwitchRequest(BaseModel):
    config_filename: str = "mcp_config.json"


# ── Multi-Agent A2A (Week 10) ────────────────────────────────

class SquadTriageRequest(BaseModel):
    claim_id: str = "CLM-7001"


class MultiAgentRaceRequest(BaseModel):
    claims: Optional[List[str]] = None


# ── Observability & Support (Weeks 5 & 11) ───────────────────

class SupportDrillRequest(BaseModel):
    complaint_text: str = "Customer says their water damage claim was denied incorrectly or approved when it should not be."


class ReplayRequest(BaseModel):
    trace_id: str


class CacheBenchmarkRequest(BaseModel):
    num_queries: int = 20
