# ============================================================
# src/rag/mcp/policy_server.py — Policy Document Search MCP Server (Server 1)
#
# PURPOSE:
#   Exposes our policy document retrieval capabilities as a standalone
#   MCP server over JSON-RPC 2.0.
#
# TOOLS EXPOSED:
#   1. search_policy(query)
#   2. get_policy_clause(clause_id) -> Docstring-as-Prompt with Recoverable Errors!
# ============================================================

from __future__ import annotations
import sys
import os
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./src"))

from rag.mcp.protocol import BaseMcpServer

# ── Policy Clauses Database ──────────────────────────────────────────────────
POLICY_CLAUSES = {
    "Section 5.2": "Section 5.2 — Flood and Rising Water Inundation: Damage caused by natural flooding, rising surface waters, or heavy rainfall runoff is strictly excluded from standard coverage.",
    "Section 8.4": "Section 8.4 — Coastal Storm Surge: Coastal tidal surges and hurricane-driven ocean water inundations are excluded unless a specialized coastal flood rider is attached.",
    "Section 10.1": "Section 10.1 — Resignation & Notice Period: Employees submitting voluntary resignation are required to serve a mandatory 4-week (four weeks) written notice period prior to final settlement.",
    "Section 12.1": "Section 12.1 — Mysterious Disappearance & Unexplained Loss: Unexplained inventory stock loss or shortages discovered during audit without verifiable evidence of forced burglary are strictly excluded."
}


def search_policy_handler(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = arguments.get("query", "")
    try:
        from rag.core.retrieval.hybrid_retriever import hybrid_search
        results = hybrid_search(query, top_k=3)
        return [{"id": r["id"], "text": r["text"]} for r in results]
    except Exception:
        # Fallback keyword matching over known policy schedule
        q_lower = query.lower()
        matched = []
        for cid, text in POLICY_CLAUSES.items():
            if any(k in text.lower() for k in q_lower.split()):
                matched.append({"id": cid, "text": text})
        return matched if matched else [{"id": "Section 5.2", "text": POLICY_CLAUSES["Section 5.2"]}]


def get_policy_clause_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    clause_id = arguments.get("clause_id", "").strip()

    # Normalization
    for key, text in POLICY_CLAUSES.items():
        if clause_id.lower() == key.lower() or clause_id.lower() == key.replace("Section ", "sec-").lower():
            return {
                "clause_id": key,
                "status": "FOUND",
                "text": text
            }

    # Recoverable Error Formatting (Docstring-as-prompt actionable error path)
    valid_clauses = list(POLICY_CLAUSES.keys())
    return {
        "error": f"Clause '{clause_id}' not found in policy registry.",
        "status": "RECOVERABLE_INPUT_ERROR",
        "guidance": (
            f"Policy clause IDs must be formatted as 'Section X.Y' (e.g. 'Section 5.2', 'Section 8.4', 'Section 10.1', 'Section 12.1'). "
            f"Available active clauses in this policy are: {', '.join(valid_clauses)}. "
            f"Please verify the clause reference and invoke get_policy_clause with a valid section identifier."
        )
    }


def create_policy_server() -> BaseMcpServer:
    server = BaseMcpServer(server_name="policy-document-server", server_version="1.0.0")

    # Tool 1: search_policy
    server.register_tool(
        name="search_policy",
        description=(
            "Searches insurance policy wording for exclusions, clauses, and coverage limits. "
            "Use this tool when you need to find policy terms, exclusions, or rules related to an incident description. "
            "DO NOT use this tool for fetching claimant records or computing payout math."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search prompt describing the event (e.g. 'flood rising water exclusion')"
                }
            },
            "required": ["query"]
        },
        handler_fn=search_policy_handler
    )

    # Tool 2: get_policy_clause (REWRITTEN AS PROMPT WITH RECOVERABLE ERROR)
    server.register_tool(
        name="get_policy_clause",
        description=(
            "Retrieves the verbatim legal wording and terms for an exact policy clause by identifier. "
            "INSTRUCTIONS FOR ASSISTANT: "
            "1. You MUST supply an exact clause identifier in the format 'Section X.Y' (e.g. 'Section 5.2', 'Section 10.1'). "
            "2. If you do not know the exact section number, call 'search_policy' first to locate the relevant clause ID. "
            "3. If an input error is returned with format guidance, inspect the available clauses listed in the response and retry with the correct section identifier."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "clause_id": {
                    "type": "string",
                    "description": "Exact policy section identifier (e.g. 'Section 5.2', 'Section 8.4', 'Section 10.1')"
                }
            },
            "required": ["clause_id"]
        },
        handler_fn=get_policy_clause_handler
    )

    return server


if __name__ == "__main__":
    server = create_policy_server()
    server.run_stdio()
