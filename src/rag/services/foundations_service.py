"""Week 1 foundations lab: tokens, cost per token, context window, sampling, embeddings.

Everything here is computed for real from open-source parts already in the app (the
embedding model's tokenizer and vectors, plain numpy for sampling). Nothing is mocked.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional

import numpy as np

# Illustrative price defaults ($ per 1M tokens) for a small hosted model; editable in the UI.
# Local Ollama models cost $0 per token (you pay in hardware/time instead).
DEFAULT_INPUT_PER_M = 0.15
DEFAULT_OUTPUT_PER_M = 0.60


def tokenize(text: str, context_window: int = 4096) -> Dict[str, Any]:
    """Split text into tokens with the embedding model's real WordPiece tokenizer."""
    method = "WordPiece (sentence-transformers tokenizer)"
    try:
        from rag.storage.embedder import _get_model
        tokens = _get_model().tokenizer.tokenize(text)
    except Exception as exc:  # model not downloadable offline: fall back, and say so
        tokens = re.findall(r"\w+|[^\w\s]", text)
        method = f"regex fallback (tokenizer unavailable: {type(exc).__name__})"
    count = len(tokens)
    return {
        "method": method,
        "tokens": tokens[:500],
        "truncated": count > 500,
        "token_count": count,
        "characters": len(text),
        "chars_per_token": round(len(text) / count, 2) if count else 0.0,
        "words": len(text.split()),
        "context_window": context_window,
        "context_used_pct": round(100.0 * count / context_window, 2) if context_window else 0.0,
        "note": "Hosted models use their own tokenizers (BPE); counts differ but behave the same way: more text = more tokens = more cost.",
    }


def estimate_cost(input_tokens: int, output_tokens: int, requests: int = 1,
                  input_per_m: float = DEFAULT_INPUT_PER_M, output_per_m: float = DEFAULT_OUTPUT_PER_M) -> Dict[str, Any]:
    per_request = input_tokens / 1e6 * input_per_m + output_tokens / 1e6 * output_per_m
    return {
        "per_request_usd": round(per_request, 8),
        "total_usd": round(per_request * requests, 6),
        "requests": requests,
        "input_share_pct": round(100.0 * (input_tokens / 1e6 * input_per_m) / per_request, 1) if per_request else 0.0,
        "assumed_prices_per_million": {"input": input_per_m, "output": output_per_m},
    }


def sampling_distribution(tokens: List[str], logits: List[float], temperature: float = 1.0,
                          top_k: int = 0, top_p: float = 1.0, draws: int = 200, seed: Optional[int] = 42) -> Dict[str, Any]:
    """Turn next-token scores into probabilities and sample from them.

    temperature -> sharpens (<1) or flattens (>1) the distribution; temperature 0 = greedy.
    top_k / top_p -> drop unlikely tokens before sampling.
    """
    if len(tokens) != len(logits) or not tokens:
        raise ValueError("tokens and logits must be non-empty and the same length")
    scores = np.array(logits, dtype=float)
    greedy = temperature <= 0
    scaled = scores if greedy else scores / temperature
    scaled = scaled - scaled.max()
    probs = np.exp(scaled)
    probs = probs / probs.sum()
    if greedy:
        probs = np.zeros_like(probs)
        probs[int(np.argmax(scores))] = 1.0

    keep = np.ones(len(tokens), dtype=bool)
    order = np.argsort(-probs)
    if top_k and top_k > 0:
        keep[order[top_k:]] = False
    if top_p < 1.0:
        cumulative, cutoff = 0.0, len(order)
        for i, idx in enumerate(order):
            cumulative += probs[idx]
            if cumulative >= top_p:
                cutoff = i + 1
                break
        keep[order[cutoff:]] = False
    filtered = np.where(keep, probs, 0.0)
    filtered = filtered / filtered.sum()

    rng = np.random.default_rng(seed)
    sampled = rng.choice(len(tokens), size=max(1, draws), p=filtered)
    counts = np.bincount(sampled, minlength=len(tokens))
    entropy = -float(np.sum([p * math.log2(p) for p in filtered if p > 0]))
    return {
        "mode": "greedy" if greedy else "sampled",
        "rows": [
            {"token": t, "probability": round(float(probs[i]), 4), "kept": bool(keep[i]),
             "final_probability": round(float(filtered[i]), 4), "drawn": int(counts[i])}
            for i, t in enumerate(tokens)
        ],
        "entropy_bits": round(entropy, 3),
        "distinct_tokens_drawn": int((counts > 0).sum()),
    }


def embedding_similarity(texts: List[str]) -> Dict[str, Any]:
    """Embed texts with the app's real embedding model and return the cosine-similarity matrix."""
    from rag.storage.embedder import embed_texts
    vectors = np.array(embed_texts(texts), dtype=float)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    unit = vectors / np.where(norms == 0, 1, norms)
    matrix = unit @ unit.T
    return {
        "dimensions": int(vectors.shape[1]),
        "matrix": [[round(float(v), 4) for v in row] for row in matrix],
        "texts": texts,
        "note": "Similar meaning scores near 1 even with different words; unrelated text scores near 0.",
    }
