"""Loki log query tools."""

from typing import Any, Optional
from pydantic import BaseModel, Field
from backend.app.tools.base import BaseTool
from backend.app.observability.base import BaseLokiProvider


class LogsQuerySchema(BaseModel):
    query: str = Field(description="LogQL query or service filter (e.g. {app='checkout'} |= 'error')")
    limit: int = Field(default=30, description="Max log lines to retrieve (max 100)")


class LogsQueryPreviousContainerSchema(BaseModel):
    pod_name: str = Field(description="Name of the pod that restarted or terminated")
    container_name: Optional[str] = Field(default=None, description="Container name")
    namespace: str = Field(default="default", description="Kubernetes namespace")
    tail_lines: int = Field(default=50, description="Number of lines to read from terminated container log")


class LogsQueryTool(BaseTool):
    name = "logs_query"
    description = "Query recent application and container logs using LogQL to find stack traces, exception messages, and error context."
    schema = LogsQuerySchema

    def __init__(self, provider: BaseLokiProvider):
        super().__init__()
        self.provider = provider

    def _run(self, query: str, limit: int = 30) -> Any:
        return self.provider.query_logs(query=query, limit=limit)


class LogsQueryPreviousContainerTool(BaseTool):
    name = "logs_query_previous_container"
    description = "Query logs of a terminated or crashed container prior to restart to inspect panic messages or crash causes."
    schema = LogsQueryPreviousContainerSchema

    def __init__(self, provider: BaseLokiProvider):
        super().__init__()
        self.provider = provider

    def _run(self, pod_name: str, container_name: Optional[str] = None, namespace: str = "default", tail_lines: int = 50) -> Any:
        return self.provider.query_previous_container_logs(
            pod_name=pod_name,
            container_name=container_name,
            namespace=namespace,
            tail_lines=tail_lines
        )
