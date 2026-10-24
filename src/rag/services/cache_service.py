"""
cache_service.py

Service layer orchestrating:
- Semantic Cache (dual-layer exact + cosine similarity)
- Smart Model Routing
- Cost optimization benchmarks before vs after
"""
from __future__ import annotations
from typing import Dict, Any, Optional

from rag.cache.semantic_cache import SemanticCache, benchmark_cost_optimization

_cache_instance = SemanticCache(similarity_threshold=0.88)


def get_cache() -> SemanticCache:
    """Return application semantic cache instance."""
    return _cache_instance


def check_cache(query: str) -> Optional[Dict[str, Any]]:
    """Check cache for query hit."""
    return _cache_instance.get(query)


def store_in_cache(query: str, response: Dict[str, Any], cost_usd: float = 0.0002):
    """Store query and result in cache."""
    _cache_instance.put(query, response, original_cost_usd=cost_usd)


def run_cache_benchmark(num_queries: int = 20) -> Dict[str, Any]:
    """
    Run the cost-control benchmark.
    Simulates production query traffic and measures cost reduction percentage (>= 35% expected).
    """
    return benchmark_cost_optimization(num_queries=num_queries)
