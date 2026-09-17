"""Tools module initialization and registry builder."""

from typing import Optional
from backend.app.security.sandbox import SecuritySandbox
from backend.app.observability import (
    KubernetesProvider,
    PrometheusProvider,
    LokiProvider,
    JaegerProvider,
)
from backend.app.tools.base import BaseTool, ToolResult, ToolRegistry
from backend.app.tools.k8s_tools import (
    K8sListPodsTool,
    K8sGetPodTool,
    K8sGetDeploymentTool,
    K8sGetServiceTool,
    K8sGetEventsTool,
    K8sGetNodesTool,
    K8sGetRestartsTool,
    K8sGetResourceConfigTool,
)
from backend.app.tools.metrics_tools import PrometheusQueryTool, PrometheusRangeQueryTool
from backend.app.tools.logs_tools import LogsQueryTool, LogsQueryPreviousContainerTool
from backend.app.tools.trace_tools import TracesQueryTool
from backend.app.tools.change_tools import (
    DeploymentHistoryTool,
    ConfigChangeHistoryTool,
    DependencyGraphTool,
)


def create_tool_registry(
    sandbox: Optional[SecuritySandbox] = None,
    k8s_provider: Optional[KubernetesProvider] = None,
    prom_provider: Optional[PrometheusProvider] = None,
    loki_provider: Optional[LokiProvider] = None,
    jaeger_provider: Optional[JaegerProvider] = None,
) -> ToolRegistry:
    """Instantiates and registers all permitted tools configured with active providers."""
    sandbox = sandbox or SecuritySandbox()
    k8s = k8s_provider or KubernetesProvider()
    prom = prom_provider or PrometheusProvider()
    loki = loki_provider or LokiProvider()
    jaeger = jaeger_provider or JaegerProvider()

    registry = ToolRegistry(sandbox=sandbox)

    # Kubernetes tools
    registry.register(K8sListPodsTool(k8s))
    registry.register(K8sGetPodTool(k8s))
    registry.register(K8sGetDeploymentTool(k8s))
    registry.register(K8sGetServiceTool(k8s))
    registry.register(K8sGetEventsTool(k8s))
    registry.register(K8sGetNodesTool(k8s))
    registry.register(K8sGetRestartsTool(k8s))
    registry.register(K8sGetResourceConfigTool(k8s))

    # Metrics tools
    registry.register(PrometheusQueryTool(prom))
    registry.register(PrometheusRangeQueryTool(prom))

    # Logs tools
    registry.register(LogsQueryTool(loki))
    registry.register(LogsQueryPreviousContainerTool(loki))

    # Traces tools
    registry.register(TracesQueryTool(jaeger))

    # Change and dependency tools
    registry.register(DeploymentHistoryTool(k8s))
    registry.register(ConfigChangeHistoryTool(k8s))
    registry.register(DependencyGraphTool(k8s))

    return registry


__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    "create_tool_registry",
]
