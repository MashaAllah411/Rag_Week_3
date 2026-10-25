# ============================================================
# src/rag/api/routes/foundations.py
#
# Week 1 foundations lab endpoints: tokens, cost, sampling, embeddings.
# ============================================================

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from rag.services import foundations_service as svc

router = APIRouter()


class TokenizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    context_window: int = Field(default=4096, ge=128, le=2_000_000)


class CostRequest(BaseModel):
    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    requests: int = Field(default=1, ge=1, le=100_000_000)
    input_per_m: float = Field(default=svc.DEFAULT_INPUT_PER_M, ge=0)
    output_per_m: float = Field(default=svc.DEFAULT_OUTPUT_PER_M, ge=0)


class SamplingRequest(BaseModel):
    tokens: List[str] = Field(..., min_length=2, max_length=50)
    logits: List[float] = Field(..., min_length=2, max_length=50)
    temperature: float = Field(default=1.0, ge=0.0, le=5.0)
    top_k: int = Field(default=0, ge=0, le=50)
    top_p: float = Field(default=1.0, gt=0.0, le=1.0)
    draws: int = Field(default=200, ge=1, le=5000)
    seed: Optional[int] = 42


class SimilarityRequest(BaseModel):
    texts: List[str] = Field(..., min_length=2, max_length=12)


@router.post("/tokenize", summary="Count tokens and context-window usage")
async def tokenize(request: TokenizeRequest):
    return svc.tokenize(request.text, request.context_window)


@router.post("/cost", summary="Estimate cost per request from token counts")
async def cost(request: CostRequest):
    return svc.estimate_cost(request.input_tokens, request.output_tokens, request.requests,
                             request.input_per_m, request.output_per_m)


@router.post("/sampling", summary="Temperature / top-k / top-p sampling demo")
async def sampling(request: SamplingRequest):
    try:
        return svc.sampling_distribution(request.tokens, request.logits, request.temperature,
                                         request.top_k, request.top_p, request.draws, request.seed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/similarity", summary="Embedding cosine similarity between texts")
async def similarity(request: SimilarityRequest):
    try:
        return svc.embedding_similarity(request.texts)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {exc}")
