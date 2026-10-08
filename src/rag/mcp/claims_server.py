# ============================================================
# src/rag/mcp/claims_server.py — Claims Platform MCP Server (Server 2)
#
# PURPOSE:
#   Simulates the Claims Platform Team's standalone MCP server.
#   Exposes claim triage data and adjuster notes over JSON-RPC 2.0.
#
# TOOLS EXPOSED:
#   1. get_claim_status(claim_id)
#   2. get_adjuster_notes(claim_id)
# ============================================================

from __future__ import annotations
import sys
import os
from typing import Dict, Any

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./src"))

from rag.mcp.protocol import BaseMcpServer
from rag.agent.tools import MOCK_CLAIMS_DB


def get_claim_status_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    claim_id = arguments.get("claim_id", "").strip().upper()
    if claim_id in MOCK_CLAIMS_DB:
        rec = MOCK_CLAIMS_DB[claim_id]
        return {
            "claim_id": rec["claim_id"],
            "claimant": rec["claimant"],
            "incident_type": rec["incident_type"],
            "gross_claim_amount": rec["gross_claim_amount"],
            "policy_deductible": rec["policy_deductible"],
            "status": "OPEN_IN_TRIAGE"
        }
    return {
        "error": f"Claim '{claim_id}' not found.",
        "status": "NOT_FOUND",
        "guidance": "Claim numbers must follow format 'CLM-7001' through 'CLM-7010'."
    }


def get_adjuster_notes_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    claim_id = arguments.get("claim_id", "").strip().upper()
    if claim_id in MOCK_CLAIMS_DB:
        rec = MOCK_CLAIMS_DB[claim_id]
        return {
            "claim_id": rec["claim_id"],
            "adjuster_notes": rec["adjuster_notes"],
            "incident_type": rec["incident_type"],
            "notes_length": len(rec["adjuster_notes"])
        }
    return {
        "error": f"Adjuster notes for claim '{claim_id}' not found.",
        "status": "NOT_FOUND",
        "guidance": "Please verify the claim identifier before requesting adjuster notes."
    }


def create_claims_server() -> BaseMcpServer:
    server = BaseMcpServer(server_name="claims-platform-server", server_version="1.0.0")

    # Tool 1: get_claim_status
    server.register_tool(
        name="get_claim_status",
        description=(
            "Retrieves financial amounts, claimant information, and current processing status for an insurance claim. "
            "DO NOT use this tool to search policy text or read adjuster narrative notes."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "claim_id": {
                    "type": "string",
                    "description": "Unique claim identifier (e.g. 'CLM-7001')"
                }
            },
            "required": ["claim_id"]
        },
        handler_fn=get_claim_status_handler
    )

    # Tool 2: get_adjuster_notes
    server.register_tool(
        name="get_adjuster_notes",
        description=(
            "Retrieves detailed adjuster investigation notes and incident observations for a given claim. "
            "Use this tool to discover evidence, causation details, or potential exclusion triggers. "
            "DO NOT use this tool for calculating payouts or searching general policy wording."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "claim_id": {
                    "type": "string",
                    "description": "Unique claim identifier (e.g. 'CLM-7001', 'CLM-7002')"
                }
            },
            "required": ["claim_id"]
        },
        handler_fn=get_adjuster_notes_handler
    )

    return server


if __name__ == "__main__":
    server = create_claims_server()
    server.run_stdio()
