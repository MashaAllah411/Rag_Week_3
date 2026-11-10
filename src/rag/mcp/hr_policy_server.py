"""
hr_policy_server.py

Model Context Protocol (MCP) Server for HR Policy Shared Services (Variant C Capstone).
Exposes entity-scoped policy search and employee record lookups over JSON-RPC.
Can be discovered dynamically by the MCP Host.
"""
from __future__ import annotations
from typing import Dict, Any, List

from rag.agent.hr_tools import (
    MOCK_EMPLOYEE_DB, lookup_employee_record, check_leave_balance, escalate_to_hrbp
)
from rag.agent.hr_agent import run_hr_policy_desk


def list_hr_tools() -> List[Dict[str, Any]]:
    """MCP tools/list handler."""
    return [
        {
            "name": "lookup_employee_record",
            "description": "Look up an employee's Grade (1-7), Entity (India or UK), Location, and Tenure. Must be called BEFORE answering policy inquiries.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "emp_id": {"type": "string", "description": "Employee ID (e.g. EMP-001)"}
                },
                "required": ["emp_id"]
            }
        },
        {
            "name": "search_policy_scoped",
            "description": "Search HR policies scoped by Entity (India or UK) and year (2024 or 2025). Entity Annex takes precedence over General Handbook.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The policy question or topic"},
                    "entity": {"type": "string", "enum": ["India", "UK", "Global"], "description": "Applicable entity"},
                    "year": {"type": "integer", "description": "Policy year (2024 or 2025)", "default": 2025}
                },
                "required": ["query", "entity"]
            }
        },
        {
            "name": "check_leave_balance",
            "description": "Check current available leave balance for an employee from the HR record.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "emp_id": {"type": "string", "description": "Employee ID"},
                    "leave_type": {"type": "string", "enum": ["annual", "sick", "casual", "maternity", "paternity"], "default": "annual"}
                },
                "required": ["emp_id"]
            }
        },
        {
            "name": "escalate_to_hrbp",
            "description": "Escalate discretionary, policy-exception, or dispute cases to an HR Business Partner instead of guessing.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "emp_id": {"type": "string", "description": "Employee ID"},
                    "query": {"type": "string", "description": "Employee's query"},
                    "reason": {"type": "string", "description": "Reason for discretionary escalation"}
                },
                "required": ["emp_id", "query", "reason"]
            }
        }
    ]


def call_hr_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tools/call dispatcher for HR tools."""
    if name == "lookup_employee_record":
        return lookup_employee_record(arguments.get("emp_id", ""))
    elif name == "check_leave_balance":
        return check_leave_balance(arguments.get("emp_id", ""), arguments.get("leave_type", "annual"))
    elif name == "escalate_to_hrbp":
        return escalate_to_hrbp(arguments.get("emp_id", ""), arguments.get("query", ""), arguments.get("reason", ""))
    elif name == "search_policy_scoped":
        emp_id = arguments.get("emp_id", "EMP-001")
        # Ensure entity alignment
        query = arguments.get("query", "")
        year = arguments.get("year", 2025)
        res = run_hr_policy_desk(emp_id=emp_id, question=query, override_year=year)
        return {
            "status": res["status"],
            "answer": res["answer"],
            "citations": res["citations"],
            "resolved_entity": res.get("employee_details", {}).get("entity", arguments.get("entity"))
        }
    else:
        return {"error": f"Unknown tool: '{name}'"}
