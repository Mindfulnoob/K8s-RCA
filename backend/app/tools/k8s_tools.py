"""Kubernetes safe read-only inspection tools."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.tools.base import BaseTool
from backend.app.observability.base import BaseKubernetesProvider


# Schemas
class ListPodsSchema(BaseModel):
    namespace: str = Field(default="default", description="Kubernetes namespace to list pods from")
    label_selector: Optional[str] = Field(default=None, description="Optional label selector query (e.g. app=checkout)")


class GetPodSchema(BaseModel):
    pod_name: str = Field(description="Exact pod name or prefix")
    namespace: str = Field(default="default", description="Kubernetes namespace")


class GetDeploymentSchema(BaseModel):
    name: str = Field(description="Deployment name (e.g. checkout-service)")
    namespace: str = Field(default="default", description="Kubernetes namespace")


class GetServiceSchema(BaseModel):
    name: str = Field(description="Service name (e.g. checkout, database)")
    namespace: str = Field(default="default", description="Kubernetes namespace")


class GetEventsSchema(BaseModel):
    namespace: str = Field(default="default", description="Kubernetes namespace")
    involved_object: Optional[str] = Field(default=None, description="Filter events for specific object (e.g. checkout-service)")
    limit: int = Field(default=30, description="Max events to return (max 100)")


class GetNodesSchema(BaseModel):
    pass


class GetRestartsSchema(BaseModel):
    namespace: str = Field(default="default", description="Kubernetes namespace")


class GetResourceConfigSchema(BaseModel):
    resource_type: str = Field(description="Type of resource: Pod, Deployment, Service, ConfigMap")
    resource_name: str = Field(description="Name of resource")
    namespace: str = Field(default="default", description="Kubernetes namespace")


# Tool implementations
class K8sListPodsTool(BaseTool):
    name = "k8s_list_pods"
    description = "List running pods, readiness status, restart counts, and container specs in a namespace."
    schema = ListPodsSchema

    def __init__(self, provider: BaseKubernetesProvider):
        super().__init__()
        self.provider = provider

    def _run(self, namespace: str = "default", label_selector: Optional[str] = None) -> Any:
        return self.provider.list_pods(namespace=namespace, label_selector=label_selector)


class K8sGetPodTool(BaseTool):
    name = "k8s_get_pod"
    description = "Inspect detailed status, container state, termination reasons (e.g. OOMKilled), and limits of a pod."
    schema = GetPodSchema

    def __init__(self, provider: BaseKubernetesProvider):
        super().__init__()
        self.provider = provider

    def _run(self, pod_name: str, namespace: str = "default") -> Any:
        return self.provider.get_pod(pod_name=pod_name, namespace=namespace)


class K8sGetDeploymentTool(BaseTool):
    name = "k8s_get_deployment"
    description = "Get deployment metadata, replica counts, ready replicas, and current image version."
    schema = GetDeploymentSchema

    def __init__(self, provider: BaseKubernetesProvider):
        super().__init__()
        self.provider = provider

    def _run(self, name: str, namespace: str = "default") -> Any:
        return self.provider.get_deployment(name=name, namespace=namespace)


class K8sGetServiceTool(BaseTool):
    name = "k8s_get_service"
    description = "Inspect service endpoints, target ports, and cluster routing configuration."
    schema = GetServiceSchema

    def __init__(self, provider: BaseKubernetesProvider):
        super().__init__()
        self.provider = provider

    def _run(self, name: str, namespace: str = "default") -> Any:
        return self.provider.get_service(name=name, namespace=namespace)


class K8sGetEventsTool(BaseTool):
    name = "k8s_get_events"
    description = "Retrieve warning and normal Kubernetes cluster events (e.g., OOMKilled, BackOff, FailedReadinessProbe)."
    schema = GetEventsSchema

    def __init__(self, provider: BaseKubernetesProvider):
        super().__init__()
        self.provider = provider

    def _run(self, namespace: str = "default", involved_object: Optional[str] = None, limit: int = 30) -> Any:
        return self.provider.get_events(namespace=namespace, involved_object=involved_object, limit=limit)


class K8sGetNodesTool(BaseTool):
    name = "k8s_get_nodes"
    description = "Get Kubernetes node statuses, memory/disk pressures, and capacity conditions."
    schema = GetNodesSchema

    def __init__(self, provider: BaseKubernetesProvider):
        super().__init__()
        self.provider = provider

    def _run(self) -> Any:
        return self.provider.get_nodes()


class K8sGetRestartsTool(BaseTool):
    name = "k8s_get_restarts"
    description = "Get all pods in a namespace that have suffered recent container crashes or restarts."
    schema = GetRestartsSchema

    def __init__(self, provider: BaseKubernetesProvider):
        super().__init__()
        self.provider = provider

    def _run(self, namespace: str = "default") -> Any:
        return self.provider.get_restarts(namespace=namespace)


class K8sGetResourceConfigTool(BaseTool):
    name = "k8s_get_resource_config"
    description = "Read metadata and configuration specifications for non-secret Kubernetes resources."
    schema = GetResourceConfigSchema

    def __init__(self, provider: BaseKubernetesProvider):
        super().__init__()
        self.provider = provider

    def _run(self, resource_type: str, resource_name: str, namespace: str = "default") -> Any:
        return self.provider.get_resource_config(resource_type=resource_type, resource_name=resource_name, namespace=namespace)
