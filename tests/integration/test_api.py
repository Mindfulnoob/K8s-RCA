"""Integration tests for FastAPI REST endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert "version" in data


def test_cluster_status_endpoint():
    resp = client.get("/api/cluster/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cluster_connected"] is True
    assert "providers" in data
    assert data["security_sandbox"]["read_only_enforced"] is True


def test_incidents_scenarios_and_trigger():
    scenarios_resp = client.get("/api/incidents/scenarios")
    assert scenarios_resp.status_code == 200
    scenarios = scenarios_resp.json()
    assert len(scenarios) == 4
    
    # Trigger bad_deployment scenario
    trigger_resp = client.post("/api/incidents/bad_deployment/trigger")
    assert trigger_resp.status_code == 200
    assert trigger_resp.json()["status"] == "success"


def test_investigation_lifecycle_api():
    # 1. Start investigation
    payload = {
        "incident": "Checkout service experiencing cascading 504 Gateway Timeout errors.",
        "namespace": "default",
        "time_range": "last 30m",
        "provider_type": "mock",
        "max_steps": 6,
        "run_to_completion": True
    }
    create_resp = client.post("/api/investigations", json=payload)
    assert create_resp.status_code == 200
    state = create_resp.json()
    inv_id = state["id"]
    assert state["status"] in ["COMPLETED", "SUFFICIENT_EVIDENCE"]
    assert len(state["steps"]) > 0

    # 2. Get state
    get_resp = client.get(f"/api/investigations/{inv_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == inv_id

    # 3. Get timeline
    timeline_resp = client.get(f"/api/investigations/{inv_id}/timeline")
    assert timeline_resp.status_code == 200
    assert isinstance(timeline_resp.json(), list)

    # 4. Get report
    report_resp = client.get(f"/api/investigations/{inv_id}/report")
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert "root_cause" in report
    assert report["confidence_score"] > 0.0

    # 5. Get replay frames
    replay_resp = client.get(f"/api/investigations/{inv_id}/replay")
    assert replay_resp.status_code == 200
    assert len(replay_resp.json()) > 0


def test_evaluation_api_run():
    resp = client.post("/api/evaluation/run")
    assert resp.status_code == 200
    eval_data = resp.json()
    assert eval_data["total_scenarios_tested"] == 4
    assert eval_data["overall_accuracy_rate"] >= 0.75
    assert len(eval_data["results"]) == 4
