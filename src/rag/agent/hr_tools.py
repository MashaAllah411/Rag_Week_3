"""
hr_tools.py

Variant C Capstone tools for HR Shared Services (India & UK entities):
1. lookup_employee_record: Resolves Grade (1-7), Entity (India/UK), Tenure BEFORE answering.
2. check_leave_balance: Returns current remaining balance for specific leave type.
3. escalate_to_hrbp: Hands off discretionary or policy-exception queries to HR Business Partner.
"""
from __future__ import annotations
import uuid
from typing import Dict, Any, Optional

# Mock Employee Record Database
# Strictly partitioned by Entity (India vs UK) and Grade Bands (1-7)
MOCK_EMPLOYEE_DB: Dict[str, Dict[str, Any]] = {
    "EMP-001": {
        "emp_id": "EMP-001",
        "name": "Arun Kumar",
        "grade": 3,
        "grade_title": "Senior Specialist",
        "entity": "India",
        "location": "Chennai",
        "tenure_years": 2.5,
        "probation_completed": True,
        "leave_balances": {
            "annual": 14,
            "sick": 8,
            "casual": 4,
            "paternity": 15
        }
    },
    "EMP-002": {
        "emp_id": "EMP-002",
        "name": "Sarah Jenkins",
        "grade": 6,
        "grade_title": "Director",
        "entity": "UK",
        "location": "London",
        "tenure_years": 5.2,
        "probation_completed": True,
        "leave_balances": {
            "annual": 22,
            "sick": 10,
            "maternity": 52
        }
    },
    "EMP-003": {
        "emp_id": "EMP-003",
        "name": "Priya Sharma",
        "grade": 4,
        "grade_title": "Team Lead",
        "entity": "India",
        "location": "Bengaluru",
        "tenure_years": 1.5,
        "probation_completed": True,
        "leave_balances": {
            "annual": 8,
            "sick": 6,
            "maternity": 26
        }
    },
    "EMP-004": {
        "emp_id": "EMP-004",
        "name": "David Smith",
        "grade": 2,
        "grade_title": "Junior Associate",
        "entity": "UK",
        "location": "Manchester",
        "tenure_years": 0.2,
        "probation_completed": False,
        "leave_balances": {
            "annual": 0,
            "sick": 3
        }
    },
    "EMP-005": {
        "emp_id": "EMP-005",
        "name": "Vikram Patel",
        "grade": 5,
        "grade_title": "Senior Manager",
        "entity": "India",
        "location": "Mumbai",
        "tenure_years": 4.1,
        "probation_completed": True,
        "leave_balances": {
            "annual": 16,
            "sick": 7
        }
    },
    "EMP-006": {
        "emp_id": "EMP-006",
        "name": "Elena Rostova",
        "grade": 7,
        "grade_title": "Vice President",
        "entity": "UK",
        "location": "London",
        "tenure_years": 8.0,
        "probation_completed": True,
        "leave_balances": {
            "annual": 25,
            "sick": 12
        }
    }
}


def lookup_employee_record(emp_id: str) -> Dict[str, Any]:
    """
    Tool 1: Resolves employee grade, entity, location, and tenure.
    CRITICAL: Grade band comes from employee record, NEVER guessed from documents.
    """
    clean_id = emp_id.strip().upper()
    if clean_id not in MOCK_EMPLOYEE_DB:
        return {
            "status": "error",
            "error": f"Employee ID '{emp_id}' not found in HR directory.",
            "emp_id": emp_id
        }
    rec = MOCK_EMPLOYEE_DB[clean_id]
    return {
        "status": "success",
        "emp_id": rec["emp_id"],
        "name": rec["name"],
        "grade": rec["grade"],
        "grade_title": rec["grade_title"],
        "entity": rec["entity"],
        "location": rec["location"],
        "tenure_years": rec["tenure_years"],
        "probation_completed": rec["probation_completed"]
    }


def check_leave_balance(emp_id: str, leave_type: str = "annual") -> Dict[str, Any]:
    """
    Tool 2: Looks up available accrued leave balance for an employee.
    """
    clean_id = emp_id.strip().upper()
    if clean_id not in MOCK_EMPLOYEE_DB:
        return {
            "status": "error",
            "error": f"Employee ID '{emp_id}' not found in HR directory."
        }
    rec = MOCK_EMPLOYEE_DB[clean_id]
    lt = leave_type.lower().strip()
    balances = rec.get("leave_balances", {})
    balance = balances.get(lt, 0)
    return {
        "status": "success",
        "emp_id": rec["emp_id"],
        "leave_type": lt,
        "available_balance_days": balance
    }


def escalate_to_hrbp(emp_id: str, query: str, reason: str) -> Dict[str, Any]:
    """
    Tool 3: Hands off discretionary, policy-exception, or dispute cases to an HR Business Partner.
    HR is not asking for a confident guess on discretionary items.
    """
    ticket_id = f"HRBP-{uuid.uuid4().hex[:6].upper()}"
    return {
        "status": "ESCALATED_TO_HRBP",
        "ticket_id": ticket_id,
        "emp_id": emp_id,
        "query": query,
        "reason": reason,
        "assigned_queue": "HR Shared Services Senior Escalations",
        "sla_hours": 24,
        "message": f"Query has been escalated to HRBP under reference {ticket_id}. Discretionary exceptions require case-by-case approval."
    }
