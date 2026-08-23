"""Reject invalid or out-of-document questions before retrieval."""
from __future__ import annotations

import re
from dataclasses import dataclass

import ollama

from rag.config import OLLAMA_MODEL

_TOKEN_RE = re.compile(r"[a-zA-Z]{2,}")
_VOWELS = set("aeiou")
_INSURANCE_HINTS = (
    "insur", "polic", "claim", "coverage", "cover", "premium", "vehicle",
    "car", "accident", "damage", "add-on", "add on", "depreciation",
)


@dataclass(frozen=True)
class ScopeDecision:
    allowed: bool
    reason: str


def _is_gibberish(question: str) -> bool:
    """Catch clearly invalid input without calling any external service."""
    tokens = _TOKEN_RE.findall(question.lower())
    if not tokens:
        return True

    def looks_random(token: str) -> bool:
        """Identify long, consonant-heavy token sequences without a dictionary."""
        if len(token) < 5:
            return False
        vowel_ratio = sum(char in _VOWELS for char in token) / len(token)
        consonant_runs = re.findall(r"[^aeiou]+", token)
        longest_consonant_run = max(map(len, consonant_runs), default=0)
        return vowel_ratio <= 0.2 or longest_consonant_run >= 5

    # Reject one or more meaningful-length tokens only when all look random.
    # Examples: "jsadbjhbd" and "jdbhb msansquwdh".
    return all(looks_random(token) for token in tokens)


def check_question_scope(question: str, document_name: str | None = None) -> ScopeDecision:
    """Return whether a question belongs to the configured insurance document.

    Invalid text is rejected immediately. Meaningful text is classified with the
    local Ollama model before the more expensive retrieval pipeline starts.
    If the guard model is unavailable, the question is allowed so a temporary
    Ollama outage cannot incorrectly block valid policy questions.
    """
    if _is_gibberish(question):
        return ScopeDecision(False, "invalid_input")

    # Fast-path clear insurance questions, including common spelling variants
    # such as "Insurence company name".
    if any(term in question.lower() for term in _INSURANCE_HINTS):
        return ScopeDecision(True, "insurance_terms")

    # An uploaded document can cover any subject. Its relevance is established
    # by document-filtered retrieval rather than an insurance-only classifier.
    if document_name and "insurance" not in document_name.lower() and "policy" not in document_name.lower():
        return ScopeDecision(True, "uploaded_document")

    prompt = """You are a strict request router for an insurance-policy RAG system.
Return exactly IN_SCOPE when the question can reasonably be answered from a
private-car insurance policy (coverage, exclusions, claims, premiums, vehicle,
policy terms, add-ons, or insurance definitions). Return exactly OUT_OF_SCOPE
for greetings, general knowledge, programming, unrelated subjects, or requests
that do not concern an insurance policy. Do not answer the question.
"""
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
            options={"temperature": 0},
        )
        decision = response["message"]["content"].strip().upper()
        return ScopeDecision(decision == "IN_SCOPE", "out_of_scope" if decision != "IN_SCOPE" else "in_scope")
    except Exception:
        return ScopeDecision(True, "guard_unavailable")
