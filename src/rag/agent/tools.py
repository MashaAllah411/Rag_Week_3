# ============================================================
# src/rag/agent/tools.py — Tool Registry for Week 7
#
# PURPOSE:
#   Defines 3 distinct tools with ZERO description overlap:
#     1. get_claim(claim_id) -> Fetches claim details & adjuster notes.
#     2. search_policy(query) -> Searches policy exclusions & clauses.
#     3. compute_payout(claim_id, claim_status, gross_amount, deductible)
#        -> THIRD TOOL: Calculates net payout. Uses Enum for claim_status.
# ============================================================

import enum
from typing import Dict, Any, List


class ClaimStatusEnum(str, enum.Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    PENDING_DOCUMENTATION = "PENDING_DOCUMENTATION"


# ── Synthetic Claims Database ─────────────────────────────────────────────────
MOCK_CLAIMS_DB = {
    "CLM-7001": {
        "claim_id": "CLM-7001",
        "claimant": "Alice Miller",
        "incident_type": "Water Pipe Burst",
        "gross_claim_amount": 3500.0,
        "policy_deductible": 500.0,
        "adjuster_notes": "Water pipe burst in kitchen causing cabinet damage. No flood or rising water involved. Recommended approval."
    },
    "CLM-7002": {
        "claim_id": "CLM-7002",
        "claimant": "Robert Vance",
        "incident_type": "Basement Water Damage",
        "gross_claim_amount": 12000.0,
        "policy_deductible": 1000.0,
        "adjuster_notes": "Heavy torrential rainfall caused rising lake water and surface runoff to inundate basement. Excluded flood event under Section 5.2."
    },
    "CLM-7003": {
        "claim_id": "CLM-7003",
        "claimant": "Carlos Gomez",
        "incident_type": "Commercial Vehicle Collision",
        "gross_claim_amount": 8500.0,
        "policy_deductible": 750.0,
        "adjuster_notes": "Delivery van collided with roadside barrier during storm. Driver was authorized. No policy exclusions triggered."
    },
    "CLM-7004": {
        "claim_id": "CLM-7004",
        "claimant": "Diana Prince",
        "incident_type": "Roof Shingle Storm Damage",
        "gross_claim_amount": 4200.0,
        "policy_deductible": 500.0,
        "adjuster_notes": "Windstorm blew off roof shingles causing water seepage into attic. Weather report verifies wind gusts over 50mph."
    },
    "CLM-7005": {
        "claim_id": "CLM-7005",
        "claimant": "Edward Stark",
        "incident_type": "Property Fire",
        "gross_claim_amount": 45000.0,
        "policy_deductible": 2500.0,
        "adjuster_notes": "Electrical short circuit caused warehouse fire. Fire department report attached. Arson ruled out."
    },
    "CLM-7006": {
        "claim_id": "CLM-7006",
        "claimant": "Fiona Gallagher",
        "incident_type": "Storefront Vandalism",
        "gross_claim_amount": 2800.0,
        "policy_deductible": 300.0,
        "adjuster_notes": "Graffiti and shattered window glass on storefront. Police report filed. Covered property damage."
    },
    "CLM-7007": {
        "claim_id": "CLM-7007",
        "claimant": "George Clark",
        "incident_type": "Coastal Storm Surge",
        "gross_claim_amount": 25000.0,
        "policy_deductible": 1500.0,
        "adjuster_notes": "Hurricane surge caused sea water to flood ground floor. Coastal flood exclusion Section 8.4 applies."
    },
    "CLM-7008": {
        "claim_id": "CLM-7008",
        "claimant": "Hannah Abbott",
        "incident_type": "Inventory Theft",
        "gross_claim_amount": 9400.0,
        "policy_deductible": 800.0,
        "adjuster_notes": "Forced entry into retail storage unit after hours. Police report confirms broken lock mechanism."
    },
    "CLM-7009": {
        "claim_id": "CLM-7009",
        "claimant": "Ian Malcolm",
        "incident_type": "Office Computer Equipment Surge",
        "gross_claim_amount": 6100.0,
        "policy_deductible": 500.0,
        "adjuster_notes": "Lightning strike damaged server power supply. Surge protector failed. Covered electrical breakdown."
    },
    "CLM-7010": {
        "claim_id": "CLM-7010",
        "claimant": "Julia Roberts",
        "incident_type": "Unexplained Stock Loss",
        "gross_claim_amount": 15000.0,
        "policy_deductible": 1000.0,
        "adjuster_notes": "Audit revealed missing stock inventory. No forced entry or burglary evidence found. Mysterious disappearance exclusion Section 12.1 applies."
    }
}


# ── TOOL 1: get_claim ─────────────────────────────────────────────────────────
def get_claim(claim_id: str) -> Dict[str, Any]:
    """
    TOOL JOB: Retrieves claim details and adjuster notes for a given claim_id from the database.
    DO NOT use this tool for policy searches or calculating payouts.
    """
    clean_id = claim_id.strip().upper()
    if clean_id in MOCK_CLAIMS_DB:
        return MOCK_CLAIMS_DB[clean_id]
    return {
        "error": f"Claim ID {claim_id} not found.",
        "claim_id": claim_id
    }


# ── TOOL 2: search_policy ─────────────────────────────────────────────────────
def search_policy(query: str) -> List[Dict[str, Any]]:
    """
    TOOL JOB: Searches insurance policy wording for exclusions, clauses, and coverage limits.
    DO NOT use this tool to fetch claim details or compute payout math.
    """
    try:
        from rag.core.retrieval.hybrid_retriever import hybrid_search
        results = hybrid_search(query, top_k=3)
        return [{"id": r["id"], "text": r["text"]} for r in results]
    except Exception:
        # Fallback search results if vector store is offline
        return [
            {"id": "Section 5.2", "text": "Flood and rising water inundation are excluded from standard coverage."},
            {"id": "Section 8.4", "text": "Coastal storm surge flood events are excluded unless a separate flood endorsement is purchased."},
            {"id": "Section 12.1", "text": "Unexplained stock inventory shortages or mysterious disappearances are strictly excluded."}
        ]


# ── TOOL 3: compute_payout (THIRD TOOL WITH ENUM PARAMETER) ───────────────────
def compute_payout(
    claim_id: str,
    claim_status: ClaimStatusEnum,
    gross_amount: float,
    deductible: float
) -> Dict[str, Any]:
    """
    TOOL JOB: Computes the final net payable amount after deducting policy excess based on claim_status.
    DO NOT use this tool to fetch claim records or search policy wording.

    Parameters:
      - claim_id    : Unique claim identifier string
      - claim_status: Enum (APPROVED, DENIED, UNDER_INVESTIGATION, PENDING_DOCUMENTATION)
      - gross_amount: Total claimed damage amount
      - deductible  : Policy excess deductible amount to subtract
    """
    status_str = claim_status.value if isinstance(claim_status, ClaimStatusEnum) else str(claim_status)

    if status_str == ClaimStatusEnum.DENIED.value:
        net_payable = 0.0
        explanation = "Claim DENIED due to policy exclusion. Net payout is $0.00."
    elif status_str == ClaimStatusEnum.APPROVED.value:
        net_payable = max(0.0, float(gross_amount) - float(deductible))
        explanation = f"Claim APPROVED. Gross (${gross_amount:.2f}) minus Deductible (${deductible:.2f}) = Net Payout ${net_payable:.2f}."
    else:
        net_payable = 0.0
        explanation = f"Claim status '{status_str}' requires further review. Payout on hold."

    return {
        "claim_id": claim_id,
        "claim_status": status_str,
        "gross_amount": float(gross_amount),
        "deductible": float(deductible),
        "net_payable": round(net_payable, 2),
        "explanation": explanation
    }


# ── Tool Definitions Metadata for ReAct / Function Calling ──────────────────
TOOL_DEFINITIONS = [
    {
        "name": "get_claim",
        "description": "Retrieves claim details and adjuster notes for a given claim_id from the database. DO NOT use for policy wording or payout calculations.",
        "parameters": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string", "description": "Unique claim ID (e.g. CLM-7001)"}
            },
            "required": ["claim_id"]
        }
    },
    {
        "name": "search_policy",
        "description": "Searches insurance policy wording for exclusions, clauses, and coverage limits. DO NOT use for claim details or payout math.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search prompt (e.g. 'flood rising water exclusion')"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "compute_payout",
        "description": "Calculates the final net payable amount after subtracting policy deductible based on claim_status. DO NOT use for fetching claim records or searching policy text.",
        "parameters": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string", "description": "Unique claim ID (e.g. CLM-7001)"},
                "claim_status": {
                    "type": "string",
                    "enum": ["APPROVED", "DENIED", "UNDER_INVESTIGATION", "PENDING_DOCUMENTATION"],
                    "description": "Status enum decision for the claim"
                },
                "gross_amount": {"type": "number", "description": "Total claimed damage amount"},
                "deductible": {"type": "number", "description": "Policy deductible excess amount"}
            },
            "required": ["claim_id", "claim_status", "gross_amount", "deductible"]
        }
    }
]
