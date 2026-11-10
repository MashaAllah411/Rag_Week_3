"""
hr_desk.py

FastAPI routes for Variant C: HR Policy Answer Desk.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter

from rag.agent.hr_tools import MOCK_EMPLOYEE_DB
from rag.agent.hr_agent import run_hr_policy_desk
from rag.evaluation.hr_eval_service import (
    run_hr_eval_suite, get_hr_error_taxonomy, get_hr_trajectory_eval, get_hr_four_part_demo
)

router = APIRouter(prefix="/api/hr", tags=["HR Policy Desk (Variant C)"])


class HRQueryRequest(BaseModel):
    emp_id: str = Field(..., description="Employee ID (e.g. EMP-001)")
    question: str = Field(..., description="The policy query")
    override_year: Optional[int] = Field(None, description="Optional target year override (e.g. 2024)")


@router.get("/employees")
def get_employees():
    """Return all mock employees across India and UK entities."""
    return list(MOCK_EMPLOYEE_DB.values())


@router.post("/ask")
def ask_hr_policy(req: HRQueryRequest):
    """Execute the end-to-end HR Policy Desk loop."""
    return run_hr_policy_desk(emp_id=req.emp_id, question=req.question, override_year=req.override_year)


@router.get("/taxonomy")
def get_error_taxonomy():
    """Return the Week 5 Re-scored Error Taxonomy on the integrated system."""
    return get_hr_error_taxonomy()


@router.get("/trajectory")
def get_trajectory_eval():
    """Return the Week 8 Trajectory Evaluation metrics and outcome-vs-trajectory gap."""
    return get_hr_trajectory_eval()


@router.get("/demo")
def get_four_part_demo():
    """Return the 4-part demo guide, metrics, and hostile questions defense."""
    return get_hr_four_part_demo()


@router.post("/eval/run")
def execute_eval_suite():
    """Run the 25-case evaluation suite with assertions and judge agreement."""
    return run_hr_eval_suite()
