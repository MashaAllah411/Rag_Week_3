# ============================================================
# src/rag/agents/a2a_protocol.py — Agent-to-Agent (A2A) Protocol
#
# PURPOSE:
#   Implements the standard Agent-to-Agent (A2A) protocol schema:
#     1. AgentCard: Semantic agent capability and interface descriptor
#     2. TaskLifecycle: Standard task lifecycle state machine
#     3. A2AMessage: Context hand-off message envelope & telemetry
# ============================================================

from __future__ import annotations
import enum
import time
import json
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


class TaskLifecycle(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    WORKING = "WORKING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class AgentCard:
    """Standard AgentCard describing specialist agent capabilities and contract."""
    name: str
    version: str
    role: str
    description: str
    capabilities: List[str]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class A2AMessage:
    """Standard A2A context hand-off message envelope."""
    sender: str
    recipient: str
    task_id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    lifecycle: TaskLifecycle = TaskLifecycle.SUBMITTED
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    tokens_used: int = 0
    latency_seconds: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["lifecycle"] = self.lifecycle.value
        return d


def estimate_tokens(text: Any) -> int:
    """Estimates tokens for context and message serialization (1 token ≈ 4 chars)."""
    return max(1, len(str(text)) // 4)
