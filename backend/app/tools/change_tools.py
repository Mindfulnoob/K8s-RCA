"""Deployment, configuration change history, and dependency graph tools."""

from typing import Any, Optional
from pydantic import BaseModel, Field
from backend.app.tools.base import BaseTool
from backend.app.observability.base import BaseKubernetesProvider


class DeploymentHistorySchema(BaseModel):
    name: str = Field(description="Deployment name to check revision history for")
    namespace: str = Field(default="default", description="Kubernetes namespace")


class ConfigChangeHistorySchema(BaseModel):
    name: str = Field(description="Resource or config name")
    namespace: str = Field(default="default", description="Kubernetes namespace")


class DependencyGraphSchema(BaseModel):
    namespace: str = Field(default="default", description="Kubernetes namespace")


class DeploymentHistoryTool(BaseTool):
    name = "deployment_history"
    description = "Inspect deployment revisions, rollout timestamps, image tag changes, and authors."
    schema = DeploymentHistorySchema

    def __init__(self, provider: BaseKubernetesProvider):
        super().__init__()
        self.provider = provider

    def _run(self, name: str, namespace: str = "default") -> Any:
        return self.provider.get_deployment_history(name=name, namespace=namespace)


class ConfigChangeHistoryTool(BaseTool):
    name = "config_change_history"
    description = "Inspect recent ConfigMap, Secret reference, and environment variable changes."
    schema = ConfigChangeHistorySchema

    def __init__(self, provider: BaseKubernetesProvider):
        super().__init__()
        self.provider = provider

    def _run(self, name: str, namespace: str = "default") -> Any:
        return self.provider.get_config_change_history(name=name, namespace=namespace)


class DependencyGraphTool(BaseTool):
    name = "dependency_graph"
    description = "Retrieve the architecture topology showing service-to-service and service-to-database dependency edges."
    schema = DependencyGraphSchema

    def __init__(self, provider: BaseKubernetesProvider):
        super().__init__()
        self.provider = provider

    def _run(self, namespace: str = "default") -> Any:
        return self.provider.get_dependency_graph(namespace=namespace)
