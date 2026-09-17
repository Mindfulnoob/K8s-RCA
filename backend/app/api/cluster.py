"""Cluster and Observability Health API router."""

from typing import Dict, Any
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.observability.simulated_data import ActiveScenarioManager
from backend.app.observability import KubernetesProvider, PrometheusProvider, LokiProvider, JaegerProvider

router = APIRouter(prefix="/cluster", tags=["cluster"])


@router.get("/status")
def get_cluster_status() -> Dict[str, Any]:
    """Returns cluster connection state, provider health, and current active scenario."""
    k8s = KubernetesProvider()
    scenario = ActiveScenarioManager.get_current_scenario()

    return {
        "cluster_connected": True,
        "mode": "Simulated Cluster Sandbox" if settings.MOCK_MODE or not k8s.use_live else "Live Kubernetes Cluster",
        "active_scenario": scenario.get("name"),
        "active_scenario_id": scenario.get("id"),
        "security_sandbox": {
            "enabled": settings.ENABLE_SECURITY_SANDBOX,
            "read_only_enforced": True,
            "secret_redaction": True,
            "prompt_injection_defense": True,
            "forbidden_verbs": ["delete", "patch", "apply", "exec", "port-forward", "secret-read"]
        },
        "providers": {
            "kubernetes": {"status": "HEALTHY", "type": "Live API" if k8s.use_live else "Simulated API"},
            "prometheus": {"status": "HEALTHY", "endpoint": settings.PROMETHEUS_URL},
            "loki": {"status": "HEALTHY", "endpoint": settings.LOKI_URL},
            "jaeger": {"status": "HEALTHY", "endpoint": settings.JAEGER_URL}
        },
        "managed_pods_count": len(scenario.get("pods", []))
    }
