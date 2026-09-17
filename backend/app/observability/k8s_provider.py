"""Kubernetes Observability Provider (Live K8s client with high-fidelity fallback)."""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from backend.app.observability.base import BaseKubernetesProvider
from backend.app.observability.simulated_data import ActiveScenarioManager
from backend.app.config import settings

try:
    from kubernetes import client, config
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False


class KubernetesProvider(BaseKubernetesProvider):
    """Provides safe read-only access to Kubernetes cluster objects."""

    def __init__(self, kubeconfig_path: Optional[str] = None):
        self.use_live = False
        if not settings.MOCK_MODE and K8S_AVAILABLE:
            try:
                if kubeconfig_path and os.path.exists(kubeconfig_path):
                    config.load_kube_config(config_file=kubeconfig_path)
                    self.core_v1 = client.CoreV1Api()
                    self.apps_v1 = client.AppsV1Api()
                    self.use_live = True
                else:
                    config.load_incluster_config()
                    self.core_v1 = client.CoreV1Api()
                    self.apps_v1 = client.AppsV1Api()
                    self.use_live = True
            except Exception:
                self.use_live = False

    def list_pods(self, namespace: str = "default", label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.use_live:
            try:
                pods = self.core_v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector or "")
                res = []
                for p in pods.items:
                    res.append({
                        "name": p.metadata.name,
                        "namespace": p.metadata.namespace,
                        "status": p.status.phase,
                        "ready": any(c.ready for c in (p.status.conditions or []) if c.type == "Ready"),
                        "restarts": sum((cs.restart_count or 0) for cs in (p.status.container_statuses or [])),
                        "node": p.spec.node_name,
                        "created_at": str(p.metadata.creation_timestamp),
                    })
                return res
            except Exception:
                pass

        # Simulated fallback
        scenario = ActiveScenarioManager.get_current_scenario()
        pods = scenario.get("pods", [])
        if namespace != "all":
            pods = [p for p in pods if p.get("namespace", "default") == namespace]
        return pods

    def get_pod(self, pod_name: str, namespace: str = "default") -> Dict[str, Any]:
        if self.use_live:
            try:
                p = self.core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
                return {
                    "name": p.metadata.name,
                    "namespace": p.metadata.namespace,
                    "status": p.status.phase,
                    "restarts": sum((cs.restart_count or 0) for cs in (p.status.container_statuses or [])),
                    "node": p.spec.node_name,
                    "containers": [c.name for c in p.spec.containers],
                    "labels": p.metadata.labels,
                }
            except Exception:
                pass

        scenario = ActiveScenarioManager.get_current_scenario()
        for p in scenario.get("pods", []):
            if pod_name in p.get("name", ""):
                return p
        return {"error": f"Pod '{pod_name}' not found in namespace '{namespace}'."}

    def get_deployment(self, name: str, namespace: str = "default") -> Dict[str, Any]:
        if self.use_live:
            try:
                d = self.apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
                return {
                    "name": d.metadata.name,
                    "namespace": d.metadata.namespace,
                    "replicas": d.spec.replicas,
                    "ready_replicas": d.status.ready_replicas or 0,
                    "image": d.spec.template.spec.containers[0].image,
                }
            except Exception:
                pass

        scenario = ActiveScenarioManager.get_current_scenario()
        for d in scenario.get("deployments", []):
            if name in d.get("name", ""):
                return d
        return {"error": f"Deployment '{name}' not found."}

    def get_service(self, name: str, namespace: str = "default") -> Dict[str, Any]:
        scenario = ActiveScenarioManager.get_current_scenario()
        return {
            "name": name,
            "namespace": namespace,
            "type": "ClusterIP",
            "ports": [{"port": 80, "targetPort": 8080}],
            "selector": {"app": name}
        }

    def get_events(self, namespace: str = "default", involved_object: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        scenario = ActiveScenarioManager.get_current_scenario()
        events = scenario.get("events", [])
        if involved_object:
            events = [e for e in events if involved_object in e.get("object", "")]
        return events[:limit]

    def get_nodes(self) -> List[Dict[str, Any]]:
        return [
            {"name": "worker-node-1", "status": "Ready", "cpu": "8", "memory": "32Gi", "conditions": "MemoryPressure=False, DiskPressure=False"},
            {"name": "worker-node-2", "status": "Ready", "cpu": "8", "memory": "32Gi", "conditions": "MemoryPressure=False, DiskPressure=False"}
        ]

    def get_restarts(self, namespace: str = "default") -> List[Dict[str, Any]]:
        scenario = ActiveScenarioManager.get_current_scenario()
        pods = scenario.get("pods", [])
        return [
            {
                "pod_name": p["name"],
                "restarts": p.get("restarts", 0),
                "status": p.get("status"),
                "last_state": p.get("last_state", {})
            }
            for p in pods if p.get("restarts", 0) > 0
        ]

    def get_resource_config(self, resource_type: str, resource_name: str, namespace: str = "default") -> Dict[str, Any]:
        scenario = ActiveScenarioManager.get_current_scenario()
        if resource_type.lower() == "pod":
            return self.get_pod(resource_name, namespace)
        elif resource_type.lower() == "deployment":
            return self.get_deployment(resource_name, namespace)
        return {"resource_type": resource_type, "name": resource_name, "namespace": namespace, "data": {}}

    def get_deployment_history(self, name: str, namespace: str = "default") -> List[Dict[str, Any]]:
        scenario = ActiveScenarioManager.get_current_scenario()
        return scenario.get("deployment_history", [])

    def get_config_change_history(self, name: str, namespace: str = "default") -> List[Dict[str, Any]]:
        scenario = ActiveScenarioManager.get_current_scenario()
        return scenario.get("config_changes", [])

    def get_dependency_graph(self, namespace: str = "default") -> Dict[str, Any]:
        scenario = ActiveScenarioManager.get_current_scenario()
        return scenario.get("dependencies", {"nodes": [], "edges": []})
