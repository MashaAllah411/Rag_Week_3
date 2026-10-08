# Model Error Recovery Transcript — Before vs. After Docstring-as-Prompt

## 1. Overview & Tool Rewritten

- **Tool Name:** `get_policy_clause` (on `policy-document-server`)
- **Failing User Request:** Requesting clause `"sec-99"` or `"Section 99"` (a non-existent or malformed policy section identifier).

---

## 2. BEFORE: Opaque Failure (Generic Error Code)

### Tool Docstring & Implementation (BEFORE):
```python
def get_policy_clause(clause_id: str):
    """Fetches a policy clause."""
    if clause_id not in POLICY_CLAUSES:
        return {"error_code": 3, "message": "Lookup failed."}
    return {"text": POLICY_CLAUSES[clause_id]}
```

### Transcript (BEFORE Mitigation):
```text
[User]: "What is the policy exclusion under clause sec-99?"

[Model]: Calling tool get_policy_clause(clause_id="sec-99")

[MCP Server Response]:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"error_code\": 3, \"message\": \"Lookup failed.\"}"
      }
    ],
    "isError": true
  }
}

[Model Final Output]:
"I attempted to look up clause sec-99, but the system returned Error 3: Lookup failed. I cannot assist you further because the claims lookup service is unavailable or broken."
```
*Failure Analysis: The model could not tell if the service was down, if the format was wrong, or which valid clauses exist. It gave up immediately.*

---

## 3. AFTER: Docstring-as-Prompt & Recoverable Error Path

### Tool Docstring & Implementation (AFTER):
```python
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
```

### Recoverable MCP Error Payload:
```json
{
  "error": "Clause 'sec-99' not found in policy registry.",
  "status": "RECOVERABLE_INPUT_ERROR",
  "guidance": "Policy clause IDs must be formatted as 'Section X.Y' (e.g. 'Section 5.2', 'Section 8.4', 'Section 10.1', 'Section 12.1'). Available active clauses in this policy are: Section 5.2, Section 8.4, Section 10.1, Section 12.1. Please verify the clause reference and invoke get_policy_clause with a valid section identifier."
}
```

### Transcript (AFTER Mitigation):
```text
[User]: "What is the policy exclusion under clause sec-99?"

[Model Lap 1]: Calling tool get_policy_clause(clause_id="sec-99")

[MCP Server Response]:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"error\": \"Clause 'sec-99' not found in policy registry.\", \"status\": \"RECOVERABLE_INPUT_ERROR\", \"guidance\": \"Policy clause IDs must be formatted as 'Section X.Y' (e.g. 'Section 5.2', 'Section 8.4', 'Section 10.1', 'Section 12.1'). Available active clauses in this policy are: Section 5.2, Section 8.4, Section 10.1, Section 12.1. Please verify the clause reference and invoke get_policy_clause with a valid section identifier.\"}"
      }
    ],
    "isError": true
  }
}

[Model Lap 2 (Recovered)]:
"The clause identifier 'sec-99' is invalid. The system provided the active clause schedule: Section 5.2 (Flood), Section 8.4 (Storm Surge), Section 10.1 (Resignation Notice), and Section 12.1 (Mysterious Loss). Let me search the policy for the relevant terms instead."

[Model Lap 2 Tool Call]: Calling tool search_policy(query="water damage flood exclusion")

[MCP Server Response]:
[{"id": "Section 5.2", "text": "Damage caused by natural flooding or rising surface water is strictly excluded."}]

[Model Final Output]:
"Clause 'sec-99' does not exist. However, based on the policy schedule, standard water damage exclusions fall under **Section 5.2** (Flood and Rising Water Inundation), which excludes damage from rising surface waters."
```
*Success Analysis: The actionable guidance in the error payload allowed the agent to self-correct in Lap 2, search for the correct clause, and deliver an accurate answer without aborting or hallucinating.*
