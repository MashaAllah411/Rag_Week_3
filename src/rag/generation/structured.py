"""Structured output with validation and retry (Week 2: Pydantic / instructor-style).

The model is asked for JSON matching a Pydantic schema. If the reply does not parse or
validate, the validation error is fed back and the model is asked again, up to a limit.
The loop works with any ``call_model(prompt) -> str`` so it is testable without an LLM.
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator


class ClaimAnswer(BaseModel):
    """The fixed shape every grounded answer must have."""
    answer: str = Field(min_length=1, description="Short answer using only the provided context")
    citations: List[str] = Field(default_factory=list, description="Section or chunk ids that support the answer")
    confidence: Literal["high", "medium", "low"]
    refused: bool = Field(default=False, description="True when the context does not contain the answer")

    @field_validator("citations")
    @classmethod
    def _citations_required_unless_refused(cls, value, info):
        # Grounding rule: an answer that is not a refusal must cite its source.
        if not value and not info.data.get("refused", False) and info.data.get("answer"):
            raise ValueError("citations must not be empty unless refused is true")
        return value


SCHEMA_PROMPT = (
    "Reply with ONLY a JSON object, no prose and no code fences, with exactly these keys:\n"
    '  "answer": string (use only the context),\n'
    '  "citations": array of strings (section or chunk ids that support the answer),\n'
    '  "confidence": one of "high", "medium", "low",\n'
    '  "refused": boolean (true if the context does not contain the answer).\n'
    "If the answer is not in the context set refused=true and citations=[]."
)


def extract_json(raw: str) -> Any:
    """Parse JSON from a model reply, tolerating code fences and leading/trailing prose."""
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S | re.I)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


def validate_output(raw: str) -> Dict[str, Any]:
    """Validate one raw reply. Returns {ok, data|error}."""
    try:
        payload = extract_json(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"Not valid JSON: {exc}"}
    try:
        return {"ok": True, "data": ClaimAnswer.model_validate(payload).model_dump()}
    except ValidationError as exc:
        problems = "; ".join(f"{'.'.join(map(str, e['loc'])) or 'root'}: {e['msg']}" for e in exc.errors())
        return {"ok": False, "error": f"Schema validation failed: {problems}"}


def generate_validated(call_model: Callable[[str], str], question: str, context: str,
                       max_retries: int = 2) -> Dict[str, Any]:
    """Ask, validate, and on failure re-ask with the error. Records every attempt."""
    prompt = f"Context:\n{context}\n\nQuestion: {question}\n\n{SCHEMA_PROMPT}"
    attempts: List[Dict[str, Any]] = []
    for attempt in range(1, max_retries + 2):
        raw = call_model(prompt)
        outcome = validate_output(raw)
        attempts.append({"attempt": attempt, "raw": raw, **{k: v for k, v in outcome.items() if k != "data"}})
        if outcome["ok"]:
            return {"ok": True, "result": outcome["data"], "attempts": attempts}
        prompt = (f"Your previous reply was rejected: {outcome['error']}\n"
                  f"Previous reply:\n{raw}\n\nTry again. Context:\n{context}\n\nQuestion: {question}\n\n{SCHEMA_PROMPT}")
    return {"ok": False, "result": None, "attempts": attempts,
            "error": "Gave up after retries; the caller must fail safely instead of using unvalidated output."}
