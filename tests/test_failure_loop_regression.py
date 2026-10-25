# ============================================================
# tests/test_failure_loop_regression.py — Production Failure → Test Loop
#
# PURPOSE:
#   Implements the Week 11 "Failure-to-Test Loop" requirement.
#   Guards permanently against the regression discovered in the
#   Track D Support Drill (CLM-FAIL-7701):
#   "Claim approved despite adjuster notes proving rising lake water / flood,
#    ignoring Section 5.2 exclusion."
#
# CRITERIA:
#   1. Tests that claims citing rising surface/lake water are strictly DENIED.
#   2. Asserts net_payable is exactly $0.00.
#   3. Asserts Section 5.2 exclusion clause is cited.
#   4. Verifies covered perils (e.g. accidental pipe burst) are NOT false-positively blocked.
# ============================================================

import os
import sys
try:
    import pytest
except ImportError:
    pytest = None

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./src"))

from rag.agent.tools import compute_payout, ClaimStatusEnum
from rag.evaluation.regression import check_exclusion_guardrail, run_all_regression_cases


class TestProductionFailureRegressionLoop:
    """Test suite ensuring the Support Drill failure can never recur."""

    def test_planted_failure_case_clm_fail_7701_is_denied(self):
        """
        REGRESSION TEST FOR CLM-FAIL-7701:
        Verifies that the exact failure scenario from the support drill
        now strictly results in DENIED with $0.00 payout.
        """
        planted_notes = (
            "Heavy torrential rainfall caused rising lake waters and surface runoff "
            "to flood the finished basement with 18 inches of standing water."
        )
        incident_type = "Basement Water Damage"
        gross_amount = 15500.0
        deductible = 1000.0

        # Run guardrail
        coverage_result = check_exclusion_guardrail(planted_notes, incident_type)

        assert coverage_result["status"] == "DENIED", (
            f"Expected claim to be DENIED, but got {coverage_result['status']}"
        )
        assert coverage_result["is_excluded"] is True, "Claim must be marked as excluded"
        assert coverage_result["exclusion_clause"] == "Section 5.2", (
            f"Must cite Section 5.2, got {coverage_result.get('exclusion_clause')}"
        )

        # Verify payout computation
        payout = compute_payout("CLM-FAIL-7701", ClaimStatusEnum.DENIED, gross_amount, deductible)
        assert payout["net_payable"] == 0.0, f"Denied claim must pay $0.00, got {payout['net_payable']}"

    def test_surface_runoff_variation_is_denied(self):
        """Tests linguistic variation of the exclusion (surface runoff from storm)."""
        notes = "Torrential rainfall runoff accumulated against foundation and seeped through window well."
        coverage_result = check_exclusion_guardrail(notes, "Heavy Rain Seepage")

        assert coverage_result["status"] == "DENIED"
        assert coverage_result["exclusion_clause"] == "Section 5.2"

    def test_covered_plumbing_pipe_burst_is_not_false_positively_blocked(self):
        """Ensures that legitimate non-flood water damage (burst copper pipe) is still approved."""
        notes = "Cold snap caused sudden burst pipe in ceiling; fresh water poured into living room."
        coverage_result = check_exclusion_guardrail(notes, "Burst Pipe")

        assert coverage_result["status"] == "APPROVED"
        assert coverage_result["is_excluded"] is False

        payout = compute_payout("CLM-NORM-BURST", ClaimStatusEnum.APPROVED, 4000.0, 500.0)
        assert payout["net_payable"] == 3500.0

    def test_regression_runner_reports_all_cases_passing(self):
        """The shared runner (also used by the UI) agrees with the individual tests."""
        report = run_all_regression_cases()
        assert report["total"] >= 3
        assert report["passed"] == report["total"], report
