"""
generation/llm.py

LLM provider switcher — supports Groq (cloud, fast) and Ollama (local).
Controlled by LLM_PROVIDER env var ("groq" or "ollama").
Falls back to Ollama automatically if Groq key is missing or call fails.
"""
import logging
from rag.config import OLLAMA_MODEL, LLM_PROVIDER, GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a precise document question-answering assistant.

STRICT RULES — follow exactly:
1. Answer ONLY using the provided Context below.
2. Do NOT use your general knowledge.
3. Do NOT guess, invent, or combine unsupported information.
4. If the Context does not contain enough information to answer the question, respond EXACTLY with:
   "I don't have enough context in the uploaded documents to answer this question."
5. Keep your answer concise, accurate, and factual.
6. Always cite which section, rule, or part of the context supports your answer.

Context:
{context}"""


def _query_groq(query: str, context: str) -> str:
    """Call Groq cloud API (fast, free tier up to 100K tokens/day)."""
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT.format(context=context)},
            {"role": "user",   "content": f"Question: {query}"},
        ],
        temperature=0.2,
        max_tokens=1024,
    )
    return response.choices[0].message.content


def _query_ollama(query: str, context: str) -> str:
    """Call local Ollama (fallback)."""
    import ollama
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT.format(context=context)},
            {"role": "user",   "content": f"Question: {query}"},
        ],
        options={"temperature": 0.2},
    )
    return response["message"]["content"]


def query_llm_with_context(query: str, context: str) -> str:
    """
    Generates a grounded answer using Groq (if LLM_PROVIDER=groq and key set)
    or Ollama (local fallback).

    STRICT GROUNDING:
      - The LLM MUST only use the provided context.
      - If the answer is not in the context, it says so explicitly.
      - No hallucination, no general knowledge, no invention of facts.
    """
    provider = LLM_PROVIDER.lower().strip()

    if provider == "groq" and GROQ_API_KEY:
        try:
            logger.info("[LLM] Using Groq (%s)", GROQ_MODEL)
            return _query_groq(query, context)
        except Exception as e:
            logger.warning("[LLM] Groq failed (%s), falling back to Ollama", e)
            return _query_ollama(query, context)

    # Default / fallback: Ollama
    logger.info("[LLM] Using Ollama (%s)", OLLAMA_MODEL)
    return _query_ollama(query, context)
