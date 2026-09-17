"""Incidents and scenario injection API router."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from backend.app.observability.simulated_data import ActiveScenarioManager, ScenarioCatalog

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/scenarios")
def list_scenarios() -> List[Dict[str, Any]]:
    """Returns metadata for all reproducible failure scenarios."""
    scenarios = [
        {
            "id": "multi_source",
            "name": "Flagship Multi-Source Incident (Rollout + Leak + Pool Exhaustion)",
            "description": "Correlates K8s deployment rollout + Prometheus DB saturation + Loki pool exhaustion logs + ConfigMap limit reduction.",
            "prompt": "The checkout service suddenly has a high 5xx error rate, probe failures, and restarts.",
            "ground_truth": ScenarioCatalog.get_multi_source_scenario()["ground_truth"]
        },
        {
            "id": "oom",
            "name": "Scenario 1: Checkout Service OOMKilled",
            "description": "Container memory leak exceeds 512Mi limit, causing Linux kernel OOM killer termination and restart backoff.",
            "prompt": "The checkout service is experiencing high 5xx error rate and container restarts.",
            "ground_truth": ScenarioCatalog.get_oom_scenario()["ground_truth"]
        },
        {
            "id": "bad_deployment",
            "name": "Scenario 2: Faulty Release Rollout (v2.0.0)",
            "description": "Payment service release v2.0.0 introduced unhandled NullPointerException in ChargeHandler.",
            "prompt": "Payment service transactions are failing with 100% 500 Internal Server Error following release.",
            "ground_truth": ScenarioCatalog.get_bad_deployment_scenario()["ground_truth"]
        },
        {
            "id": "dependency_failure",
            "name": "Scenario 3: PostgreSQL Database Outage",
            "description": "PostgreSQL pod crashed into CrashLoopBackOff, refusing connections and causing cascading timeouts.",
            "prompt": "Checkout service experiencing cascading 504 Gateway Timeout errors.",
            "ground_truth": ScenarioCatalog.get_dependency_failure_scenario()["ground_truth"]
        }
    ]
    return scenarios


@router.post("/{scenario_id}/trigger")
def trigger_scenario(scenario_id: str):
    """Activates a specific scenario in the simulated cluster environment."""
    valid_ids = ["oom", "bad_deployment", "dependency_failure", "multi_source"]
    if scenario_id not in valid_ids:
        raise HTTPException(status_code=400, detail=f"Invalid scenario id. Choose from {valid_ids}")

    ActiveScenarioManager.set_scenario(scenario_id)
    scenario_data = ActiveScenarioManager.get_current_scenario()
    return {
        "status": "success",
        "message": f"Scenario '{scenario_id}' activated successfully.",
        "scenario_name": scenario_data.get("name"),
        "ground_truth": scenario_data.get("ground_truth")
    }


@router.post("/reset")
def reset_incident():
    """Resets to the default flagship multi-source scenario."""
    ActiveScenarioManager.set_scenario("multi_source")
    return {"status": "success", "message": "Incident environment reset to default flagship scenario."}
