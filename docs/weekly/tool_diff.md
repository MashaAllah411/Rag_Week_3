# Week 7 Tool Registry Diff & Metadata Specification

## 1. Tool Overview & Job Separation

| Tool Name | Exactly One Job | Parameter Types | Description Overlap |
|---|---|---|---|
| `get_claim` | Fetches claim record & adjuster notes | `claim_id: string` | None (Database retrieval only) |
| `search_policy` | Searches policy wording for exclusions | `query: string` | None (Vector policy search only) |
| `compute_payout` | **THIRD TOOL**: Computes net payout amount | `claim_id: string`, `claim_status: Enum`, `gross_amount: float`, `deductible: float` | None (Math & status evaluation only) |

---

## 2. Third Tool Specification (`compute_payout`)

### Enum Specification
```python
class ClaimStatusEnum(str, enum.Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    PENDING_DOCUMENTATION = "PENDING_DOCUMENTATION"
```

### JSON Schema Metadata Definition
```json
{
  "name": "compute_payout",
  "description": "Calculates the final net payable amount after subtracting policy deductible based on claim_status. DO NOT use for fetching claim records or searching policy text.",
  "parameters": {
    "type": "object",
    "properties": {
      "claim_id": {
        "type": "string",
        "description": "Unique claim ID (e.g. CLM-7001)"
      },
      "claim_status": {
        "type": "string",
        "enum": ["APPROVED", "DENIED", "UNDER_INVESTIGATION", "PENDING_DOCUMENTATION"],
        "description": "Status enum decision for the claim"
      },
      "gross_amount": {
        "type": "number",
        "description": "Total claimed damage amount"
      },
      "deductible": {
        "type": "number",
        "description": "Policy deductible excess amount"
      }
    },
    "required": ["claim_id", "claim_status", "gross_amount", "deductible"]
  }
}
```
