"""
tests/test_health_smoke.py

Smoke test verifying all FastAPI routers, endpoints, and health status
using Starlette TestClient (no live port listening required).
"""
import pytest
from fastapi.testclient import TestClient
from rag.api.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify GET /health returns status 200 and ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_root_endpoint():
    """Verify GET / returns service info."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"


def test_system_status_endpoint():
    """Verify GET /api/system/status returns masked config and component info."""
    resp = client.get("/api/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "components" in data
    assert "config_masked" in data
    # Secrets must never be echoed: any secret-looking setting is absent or masked.
    for name, value in data["config_masked"].items():
        if any(word in name.upper() for word in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            assert value in ("not set", "****") or "*" in str(value)
    # The live open-source stack report is present and names each tool.
    tools = {item["tool"].split(" ")[0] for item in data["open_source_stack"]}
    assert {"ChromaDB", "OpenTelemetry"} <= tools
    # No hosted vector service remains in the live components or configuration.
    assert "pinecone" not in str(data["components"]).lower()
    assert "pinecone" not in str(data["config_masked"]).lower()


def test_documents_list_endpoint():
    """Verify GET /api/documents returns document library."""
    resp = client.get("/api/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert "documents" in data
    assert "count" in data


def test_agent_claims_endpoint():
    """Verify GET /api/agent/claims returns 10 synthetic claims."""
    resp = client.get("/api/agent/claims")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 10
    assert any(c["claim_id"] == "CLM-7001" for c in data["claims"])


def test_agent_triage_simulation():
    """Verify POST /api/agent/triage executes workflow and evaluates trajectory."""
    payload = {
        "claim_id": "CLM-7001",
        "system_type": "fixed_workflow"
    }
    resp = client.post("/api/agent/triage", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["claim_id"] == "CLM-7001"
    assert data["passed"] is True
    assert "trajectory_evaluation" in data


def test_mcp_servers_endpoint():
    """Verify GET /api/mcp/servers discovers tools dynamically."""
    resp = client.get("/api/mcp/servers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["servers_count"] >= 1
    assert data["total_tools_count"] >= 1


def test_multi_agent_cards_endpoint():
    """Verify GET /api/multi-agent/agents returns the 3 squad cards."""
    resp = client.get("/api/multi-agent/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 3
    names = [a["name"] for a in data["agents"]]
    assert "claims-squad-manager" in names
    assert "policy-coverage-specialist" in names
    assert "payout-calculation-specialist" in names


def test_evaluate_metrics_endpoint():
    """Verify GET /api/evaluate/metrics returns before/after improvement data."""
    resp = client.get("/api/evaluate/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "before" in data
    assert "after" in data
    assert "improvement" in data


def test_deterministic_assertions_endpoint():
    """Verify POST /api/evaluate/assertions checks regex rules."""
    text = "Claim CLM-2024-00123 on 2024-05-15 is APPROVED for $3,500.00."
    resp = client.post("/api/evaluate/assertions", json={"text": text, "is_denial": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["claim_number_format"] is True
    assert data["date_of_loss_present"] is True
    assert data["numeric_deductible_present"] is True
