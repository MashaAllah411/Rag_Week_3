# ============================================================
# eval_assertions.py — Deterministic Rule Assertions (Week 6)
#
# PURPOSE:
#   Implements 4 deterministic Python regex assertions that take
#   formatting and rule criteria OUT of the LLM Judge:
#     1. assert_claim_number_format : CLM-YYYY-NNNNN or CLM-XXXXX
#     2. assert_date_of_loss_present: YYYY-MM-DD or parseable date
#     3. assert_numeric_deductible  : Numeric amount (e.g. 500.00)
#     4. assert_exclusion_clause_cited: Section/Clause cited on denial
# ============================================================

import re
from typing import Dict, Any


def assert_claim_number_format(text: str) -> bool:
    """
    Asserts that the text contains a valid claim number formatted as:
    CLM-YYYY-NNNNN or CLM-XXXXX (e.g. CLM-2026-00101 or CLM-12345).
    """
    pattern = r'\bCLM-\d{4}-\d{5}\b|\bCLM-\d{4,8}\b'
    return bool(re.search(pattern, text, flags=re.IGNORECASE))


def assert_date_of_loss_present(text: str) -> bool:
    """
    Asserts that a valid date of loss/incident is present (YYYY-MM-DD or Month DD, YYYY).
    """
    pattern = r'\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'
    return bool(re.search(pattern, text, flags=re.IGNORECASE))


def assert_numeric_deductible(text: str) -> bool:
    """
    Asserts that an excess or deductible amount is present as a numeric figure (e.g., $500.00, 250, 0.00).
    """
    pattern = r'\b\$?\d+(?:,\d{3})*(?:\.\d{2})?\b'
    return bool(re.search(pattern, text))


def assert_exclusion_clause_cited(text: str, is_denial_or_fallback: bool = True) -> bool:
    """
    Asserts that whenever a denial or fallback is stated, an exclusion clause ID
    or policy section (e.g., Section 10.1, Clause 2010.4, Out of Scope, Section 5.x) is cited.
    """
    if not is_denial_or_fallback:
        return True

    pattern = r'\b(?:Section|Clause|Article|Paragraph|Rule|Out of Scope)\s+(?:\d+(?:\.\d+)*|[A-Z0-9.\-]+)\b|\bOut of Scope\b|\bSection\s+\d+\b'
    return bool(re.search(pattern, text, flags=re.IGNORECASE))


def run_all_assertions(eval_item: Dict[str, Any], answer_text: str) -> Dict[str, Any]:
    """
    Runs all 4 deterministic assertions against the generated text / metadata.

    Returns:
        {
            "all_passed": bool,
            "claim_number_pass": bool,
            "date_of_loss_pass": bool,
            "deductible_pass": bool,
            "exclusion_clause_pass": bool
        }
    """
    # Create full verification text combining metadata & output
    combined_text = f"Claim ID: {eval_item.get('claim_number', '')} | Date: {eval_item.get('date_of_loss', '')} | Deductible: ${eval_item.get('deductible_amount', '')} | Exclusion: {eval_item.get('exclusion_clause', '')} | Output: {answer_text}"

    claim_pass = assert_claim_number_format(combined_text)
    date_pass = assert_date_of_loss_present(combined_text)
    deduct_pass = assert_numeric_deductible(combined_text)
    
    is_denial = "don't know" in answer_text.lower() or "not covered" in answer_text.lower() or eval_item.get("exclusion_clause") != "N/A"
    clause_pass = assert_exclusion_clause_cited(combined_text, is_denial_or_fallback=is_denial)

    all_passed = claim_pass and date_pass and deduct_pass and clause_pass

    return {
        "all_passed": all_passed,
        "claim_number_pass": claim_pass,
        "date_of_loss_pass": date_pass,
        "deductible_pass": deduct_pass,
        "exclusion_clause_pass": clause_pass
    }
