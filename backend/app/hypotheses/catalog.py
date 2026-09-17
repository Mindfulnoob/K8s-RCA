"""Hypothesis Catalog of common SRE distributed system failure archetypes."""

from typing import Dict, List, Any
from backend.app.models.hypothesis import Hypothesis, HypothesisStatus


STANDARD_HYPOTHESIS_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "bad_deployment": {
        "id": "H-DEPLOY",
        "category": "deployment",
        "description": "Recent code or container image release introduced an unhandled application defect, regression, or crash.",
        "required_evidence": [
            "Deployment revision timestamp correlates with incident start",
            "Error logs show unhandled code exception or stack trace from new image version",
            "Previous revision pods do not exhibit the same failure"
        ],
        "discriminating_queries": ["deployment_history", "k8s_get_deployment", "logs_query"]
    },
    "database_failure": {
        "id": "H-DB",
        "category": "database",
        "description": "Downstream database saturation, connection pool exhaustion, or service unavailability causing query timeouts.",
        "required_evidence": [
            "Active database connection metrics approaching or exceeding capacity pool limit",
            "Application logs indicating connection timeout or pool acquisition failure",
            "Database pod or service reporting non-ready endpoints or crashlooping"
        ],
        "discriminating_queries": ["prometheus_query", "logs_query", "k8s_get_pod"]
    },
    "oom_killed": {
        "id": "H-OOM",
        "category": "resource",
        "description": "Application memory leak or inadequate memory limit causing Linux kernel OOM killer termination (exit code 137).",
        "required_evidence": [
            "Pod last state shows terminated reason OOMKilled with exit code 137",
            "Prometheus memory working set bytes climbing to the configured memory limit",
            "Kubernetes warning events indicating BackOff and OOMKilled"
        ],
        "discriminating_queries": ["k8s_get_events", "k8s_get_pod", "prometheus_range_query", "logs_query_previous_container"]
    },
    "configuration_change": {
        "id": "H-CONFIG",
        "category": "configuration",
        "description": "Recent ConfigMap, Secret, or environment variable modification caused invalid runtime parameters or pool limits.",
        "required_evidence": [
            "ConfigMap or Secret change history shows modification within incident window",
            "Application behavior or concurrency constraints altered after config update"
        ],
        "discriminating_queries": ["config_change_history", "k8s_get_resource_config", "logs_query"]
    },
    "dependency_outage": {
        "id": "H-DEP",
        "category": "dependency",
        "description": "External or internal microservice dependency (RPC, API, payment, cache) is down, timed out, or returning errors.",
        "required_evidence": [
            "Distributed traces show error spans originating in downstream service",
            "Downstream service pods failing health checks or unavailable endpoints"
        ],
        "discriminating_queries": ["traces_query", "dependency_graph", "k8s_get_service"]
    },
    "node_pressure": {
        "id": "H-NODE",
        "category": "infrastructure",
        "description": "Underlying Kubernetes node resource starvation, memory pressure, disk pressure, or kubelet eviction.",
        "required_evidence": [
            "Node status conditions report MemoryPressure, DiskPressure, or PIDPressure",
            "Multiple unrelated pods on same node experiencing eviction or throttling"
        ],
        "discriminating_queries": ["k8s_get_nodes", "k8s_get_events"]
    },
    "traffic_spike": {
        "id": "H-TRAFFIC",
        "category": "traffic",
        "description": "Sudden surge in request rate exceeding provisioned service capacity or triggering upstream rate limiting.",
        "required_evidence": [
            "Prometheus request rate metric showing significant anomalous increase above baseline",
            "Pod CPU utilization saturated across all replicas without crashing"
        ],
        "discriminating_queries": ["prometheus_query", "prometheus_range_query"]
    }
}
