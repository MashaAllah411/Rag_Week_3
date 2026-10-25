"""Regression tests for the multi-agent squad service key mismatch.

ClaimsSquadManager returns final_status / a2a_transcripts / total_cost / latency_seconds.
The service and UI read final_decision / hand_offs / total_cost_usd / total_latency_seconds,
so the A2A transcript was blank and every squad race result scored as failed with zero cost.
"""
from fastapi.testclient import TestClient

from rag.api.main import app

client = TestClient(app)


def test_squad_triage_exposes_final_decision_and_hand_offs():
    r = client.post("/api/multi-agent/triage", json={"claim_id": "CLM-7002"}).json()
    assert r["final_decision"]["status"] in ("APPROVED", "DENIED")
    assert len(r["hand_offs"]) == 2                      # policy specialist + payout specialist
    assert {h["recipient"] for h in r["hand_offs"]} == {"policy-coverage-specialist", "payout-calculation-specialist"}
    assert all(h["tokens_used"] > 0 for h in r["hand_offs"])
    assert "Policy Specialist Hand-Off" in r["transcript_markdown"]
    assert "None" not in r["transcript_markdown"].split("**Final Verdict**")[1].splitlines()[0]


def test_squad_race_scores_real_results():
    r = client.post("/api/multi-agent/benchmark", json={"claims": ["CLM-7001", "CLM-7002"]}).json()
    squad = r["multi_agent_squad"]
    assert squad["passed"] == 2 and squad["total_tokens"] > 0 and squad["total_cost_usd"] > 0
    assert all(item["status"] in ("APPROVED", "DENIED") for item in squad["items"])
