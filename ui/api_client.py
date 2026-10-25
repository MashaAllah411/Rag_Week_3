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
        """Delete a document and its ChromaDB vectors."""
        resp = requests.delete(f"{self.base_url}/api/documents/{filename}", timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def reindex_documents(self) -> Dict[str, Any]:
        """Trigger full re-indexing of all documents."""
        resp = requests.post(f"{self.base_url}/api/documents/reindex", timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def inspect_document_chunks(self, filename: str, strategy: str = "fixed",
                                chunk_size: int = 900, chunk_overlap: int = 150) -> Dict[str, Any]:
        """Inspect chunk previews for a document under a chunking strategy (fixed | keyword | semantic)."""
        params = {"strategy": strategy, "chunk_size": chunk_size, "chunk_overlap": chunk_overlap}
        resp = requests.get(f"{self.base_url}/api/documents/{filename}/chunks", params=params, timeout=120.0)
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
        document_name: Optional[str] = None,
        scan_injection: bool = False
    ) -> Dict[str, Any]:
        """Run the full RAG pipeline."""
        payload = {
            "question": question,
            "mode": mode,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "use_query_rewriter": use_query_rewriter,
            "document_name": document_name,
            "scan_injection": scan_injection
        }
        resp = requests.post(f"{self.base_url}/api/ask", json=payload, timeout=120.0)
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

    # ── Generic helpers for the endpoints added in the consolidation pass ──

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, timeout: float = TIMEOUT) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}{path}", params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None,
              timeout: float = TIMEOUT) -> Dict[str, Any]:
        resp = requests.post(f"{self.base_url}{path}", json=payload if payload is not None else {}, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    # ── Week 1: Foundations Lab ──────────────────────────────

    def tokenize(self, text: str, context_window: int = 4096) -> Dict[str, Any]:
        return self._post("/api/foundations/tokenize", {"text": text, "context_window": context_window}, timeout=120.0)

    def estimate_cost(self, input_tokens: int, output_tokens: int, requests_count: int = 1,
                      input_per_m: float = 0.15, output_per_m: float = 0.60) -> Dict[str, Any]:
        return self._post("/api/foundations/cost", {"input_tokens": input_tokens, "output_tokens": output_tokens,
                                                    "requests": requests_count, "input_per_m": input_per_m,
                                                    "output_per_m": output_per_m})

    def sampling_demo(self, tokens: List[str], logits: List[float], temperature: float = 1.0, top_k: int = 0,
                      top_p: float = 1.0, draws: int = 200, seed: Optional[int] = 42) -> Dict[str, Any]:
        return self._post("/api/foundations/sampling", {"tokens": tokens, "logits": logits, "temperature": temperature,
                                                        "top_k": top_k, "top_p": top_p, "draws": draws, "seed": seed})

    def embedding_similarity(self, texts: List[str]) -> Dict[str, Any]:
        return self._post("/api/foundations/similarity", {"texts": texts}, timeout=120.0)

    # ── Weeks 2 & 8: Guardrails, structured output, prompt injection ──

    def injection_demo(self) -> Dict[str, Any]:
        return self._get("/api/guardrails/injection/demo")

    def injection_scan(self, text: str) -> Dict[str, Any]:
        return self._post("/api/guardrails/injection/scan", {"text": text})

    def injection_scan_retrieval(self, question: str, top_k: int = 5, document_name: Optional[str] = None) -> Dict[str, Any]:
        return self._post("/api/guardrails/injection/scan-retrieval",
                          {"question": question, "top_k": top_k, "document_name": document_name}, timeout=120.0)

    def guardrail_tools(self) -> Dict[str, Any]:
        return self._get("/api/guardrails/tools")

    def scope_check(self, question: str, document_name: Optional[str] = None) -> Dict[str, Any]:
        return self._post("/api/guardrails/scope", {"question": question, "document_name": document_name}, timeout=120.0)

    def structured_schema(self) -> Dict[str, Any]:
        return self._get("/api/guardrails/structured/schema")

    def structured_validate(self, raw: str) -> Dict[str, Any]:
        return self._post("/api/guardrails/structured/validate", {"raw": raw})

    def structured_generate(self, question: str, document_name: Optional[str] = None, max_retries: int = 2) -> Dict[str, Any]:
        return self._post("/api/guardrails/structured/generate",
                          {"question": question, "document_name": document_name, "max_retries": max_retries}, timeout=180.0)

    # ── Week 3: chunk-size comparison ────────────────────────

    def compare_chunk_sizes(self, filename: str, query: str, expected_text: str, sizes: List[int]) -> Dict[str, Any]:
        return self._post(f"/api/documents/{filename}/chunk-compare",
                          {"query": query, "expected_text": expected_text, "sizes": sizes}, timeout=120.0)

    # ── Weeks 4 & 6: current-corpus evaluation, judge validation, regression loop ──

    def eval_datasets(self) -> Dict[str, Any]:
        return self._get("/api/evaluate/datasets")

    def insurance_eval_results(self) -> Dict[str, Any]:
        return self._get("/api/evaluate/insurance/results")

    def run_insurance_eval(self, mode: str = "hybrid", top_k: int = 3) -> Dict[str, Any]:
        return self._post("/api/evaluate/insurance/run", {"mode": mode, "top_k": top_k}, timeout=300.0)

    def judge_validation(self) -> Dict[str, Any]:
        return self._get("/api/evaluate/judge-validation")

    def regression_cases(self) -> Dict[str, Any]:
        return self._get("/api/evaluate/regression")

    def run_regression(self) -> Dict[str, Any]:
        return self._post("/api/evaluate/regression/run")

    # ── Week 5: error analysis ───────────────────────────────

    def error_sample(self, n: int = 20, seed: int = 42) -> Dict[str, Any]:
        return self._get("/api/observability/error-analysis/sample", {"n": n, "seed": seed})

    def save_error_note(self, trace_id: str, note: str, category: str = "", severity: int = 3) -> Dict[str, Any]:
        return self._post("/api/observability/error-analysis/notes",
                          {"trace_id": trace_id, "note": note, "category": category, "severity": severity})

    def error_taxonomy(self) -> Dict[str, Any]:
        return self._get("/api/observability/error-analysis/taxonomy")

    def save_prediction(self, text: str) -> Dict[str, Any]:
        return self._post("/api/observability/error-analysis/prediction", {"text": text})

    # ── Week 11: OpenTelemetry export status ─────────────────

    def otel_status(self, limit: int = 30) -> Dict[str, Any]:
        return self._get("/api/observability/otel", {"limit": limit})

    # ── System self-test and Week 12 capstone ────────────────

    def run_selftest(self, deep: bool = False) -> Dict[str, Any]:
        return self._post("/api/system/selftest", params={"deep": str(deep).lower()}, timeout=300.0)

    def run_capstone_suite(self) -> Dict[str, Any]:
        return self._post("/api/capstone/suite", timeout=600.0)

    def capstone_weak_spots(self) -> Dict[str, Any]:
        return self._get("/api/capstone/weak-spots")

    def capstone_demo(self) -> Dict[str, Any]:
        return self._get("/api/capstone/demo")


api = ApiClient()
