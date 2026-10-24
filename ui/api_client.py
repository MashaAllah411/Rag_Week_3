"""
ui/api_client.py

HTTP API client for the Streamlit UI.
CRITICAL ARCHITECTURAL RULE:
The UI NEVER imports backend internals; it interacts with the RAG system
exclusively through this HTTP API client.
"""
from __future__ import annotations
import os
import requests
from typing import Dict, Any, List, Optional

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = 45.0  # seconds


class ApiClient:
    """Synchronous HTTP client for FastAPI backend endpoints."""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url

    # ── Health & System ──────────────────────────────────────

    def get_health(self) -> Dict[str, Any]:
        """Check /health endpoint."""
        resp = requests.get(f"{self.base_url}/health", timeout=5.0)
        resp.raise_for_status()
        return resp.json()

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and component health."""
        resp = requests.get(f"{self.base_url}/api/system/status", timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def get_system_logs(self, lines: int = 100) -> Dict[str, Any]:
        """Fetch recent backend and frontend logs."""
        resp = requests.get(f"{self.base_url}/api/system/logs", params={"lines": lines}, timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    # ── Documents ────────────────────────────────────────────

    def list_documents(self) -> Dict[str, Any]:
        """List indexed documents in resources/."""
        resp = requests.get(f"{self.base_url}/api/documents", timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def upload_document(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Upload and start background indexing for a PDF."""
        files = {"file": (filename, file_bytes, "application/pdf")}
        resp = requests.post(f"{self.base_url}/api/documents/upload", files=files, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def delete_document(self, filename: str) -> Dict[str, Any]:
        """Delete a document and its Pinecone vectors."""
        resp = requests.delete(f"{self.base_url}/api/documents/{filename}", timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def reindex_documents(self) -> Dict[str, Any]:
        """Trigger full re-indexing of all documents."""
        resp = requests.post(f"{self.base_url}/api/documents/reindex", timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def inspect_document_chunks(self, filename: str) -> Dict[str, Any]:
        """Inspect chunk previews for a document."""
        resp = requests.get(f"{self.base_url}/api/documents/{filename}/chunks", timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    # ── Search & Q&A ─────────────────────────────────────────

    def ask(
        self,
        question: str,
        mode: str = "hybrid",
        top_k: int = 3,
        similarity_threshold: float = 0.0,
        use_query_rewriter: bool = True,
        document_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run the full RAG pipeline."""
        payload = {
            "question": question,
            "mode": mode,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "use_query_rewriter": use_query_rewriter,
            "document_name": document_name
        }
        resp = requests.post(f"{self.base_url}/api/ask", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    # ── Agent Loops (Weeks 7 & 8) ────────────────────────────

    def list_claims(self) -> Dict[str, Any]:
        """List all 10 synthetic insurance claims."""
        resp = requests.get(f"{self.base_url}/api/agent/claims", timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def run_agent_triage(
        self,
        claim_id: str,
        system_type: str = "agent_loop",
        force_budget_exceed: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run ReAct Agent or Fixed Workflow claim triage."""
        payload = {
            "claim_id": claim_id,
            "system_type": system_type,
            "force_budget_exceed": force_budget_exceed
        }
        resp = requests.post(f"{self.base_url}/api/agent/triage", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def run_agent_benchmark(self, claims: Optional[List[str]] = None) -> Dict[str, Any]:
        """Race ReAct Agent vs Fixed Workflow across claims."""
        payload = {"claims": claims}
        resp = requests.post(f"{self.base_url}/api/agent/benchmark", json=payload, timeout=60.0)
        resp.raise_for_status()
        return resp.json()

    # ── MCP Ecosystem (Week 9) ───────────────────────────────

    def get_mcp_servers(self) -> Dict[str, Any]:
        """Get connected MCP servers and discovered tools."""
        resp = requests.get(f"{self.base_url}/api/mcp/servers", timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool via MCP JSON-RPC 2.0."""
        payload = {"tool_name": tool_name, "arguments": arguments}
        resp = requests.post(f"{self.base_url}/api/mcp/call", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def run_mcp_triage(self, claim_id: str, config_filename: Optional[str] = None) -> Dict[str, Any]:
        """Run claim triage over MCP servers."""
        payload = {"claim_id": claim_id, "config_filename": config_filename}
        resp = requests.post(f"{self.base_url}/api/mcp/triage", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def switch_mcp_config(self, config_filename: str) -> Dict[str, Any]:
        """Switch active MCP configuration file."""
        payload = {"config_filename": config_filename}
        resp = requests.post(f"{self.base_url}/api/mcp/config", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    # ── Multi-Agent Squad (Week 10) ──────────────────────────

    def get_multi_agent_cards(self) -> Dict[str, Any]:
        """List Agent Cards for the squad."""
        resp = requests.get(f"{self.base_url}/api/multi-agent/agents", timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def run_squad_triage(self, claim_id: str) -> Dict[str, Any]:
        """Run triage using Claims Squad via A2A protocol."""
        payload = {"claim_id": claim_id}
        resp = requests.post(f"{self.base_url}/api/multi-agent/triage", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def run_multi_agent_benchmark(self, claims: Optional[List[str]] = None) -> Dict[str, Any]:
        """Race Single Agent vs Multi-Agent Squad."""
        payload = {"claims": claims}
        resp = requests.post(f"{self.base_url}/api/multi-agent/benchmark", json=payload, timeout=60.0)
        resp.raise_for_status()
        return resp.json()

    # ── Evaluation & Quality ─────────────────────────────────

    def get_eval_metrics(self) -> Dict[str, Any]:
        """Get before/after retrieval metrics."""
        resp = requests.get(f"{self.base_url}/api/evaluate/metrics", timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def get_eval_results(self, mode: str) -> Dict[str, Any]:
        """Get precomputed evaluation results for mode."""
        resp = requests.get(f"{self.base_url}/api/evaluate/results/{mode}", timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def trigger_live_evaluation(self, mode: str, top_k: int = 3) -> Dict[str, Any]:
        """Trigger background evaluation run."""
        payload = {"mode": mode, "top_k": top_k}
        resp = requests.post(f"{self.base_url}/api/evaluate/run", json=payload, timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def get_failures(self) -> Dict[str, Any]:
        """Get all failure labels and human overrides."""
        resp = requests.get(f"{self.base_url}/api/failures", timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def save_failure_label(self, question: str, label: str, evidence: Optional[str] = None) -> Dict[str, Any]:
        """Persist a human failure label override."""
        payload = {"question": question, "label": label, "evidence": evidence}
        resp = requests.post(f"{self.base_url}/api/failures/label", json=payload, timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def check_assertions(self, text: str, is_denial: bool = False) -> Dict[str, Any]:
        """Run 4 deterministic regex assertions."""
        payload = {"text": text, "is_denial": is_denial}
        resp = requests.post(f"{self.base_url}/api/evaluate/assertions", json=payload, timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def evaluate_judge(self, query: str, context: str, answer: str, judge_version: str = "v2") -> Dict[str, Any]:
        """Run LLM Judge V1 or V2."""
        payload = {"query": query, "context": context, "answer": answer, "judge_version": judge_version}
        resp = requests.post(f"{self.base_url}/api/evaluate/judge", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    # ── Observability & Support ──────────────────────────────

    def list_traces(self, limit: int = 50, trace_type: str = "production") -> Dict[str, Any]:
        """List recent request traces."""
        params = {"limit": limit, "trace_type": trace_type}
        resp = requests.get(f"{self.base_url}/api/observability/traces", params=params, timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def get_trace_details(self, trace_id: str) -> Dict[str, Any]:
        """Get detailed trace with spans."""
        resp = requests.get(f"{self.base_url}/api/observability/traces/{trace_id}", timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def replay_trace(self, trace_id: str) -> Dict[str, Any]:
        """Replay trace from context."""
        payload = {"trace_id": trace_id}
        resp = requests.post(f"{self.base_url}/api/observability/replay", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def run_support_drill(self, complaint_text: str) -> Dict[str, Any]:
        """Run support triage drill on 100 traces."""
        payload = {"complaint_text": complaint_text}
        resp = requests.post(f"{self.base_url}/api/observability/drill", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def run_cache_benchmark(self, num_queries: int = 20) -> Dict[str, Any]:
        """Run semantic cache cost benchmark."""
        payload = {"num_queries": num_queries}
        resp = requests.post(f"{self.base_url}/api/observability/cache-benchmark", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()


api = ApiClient()
