"""Distributed tracing query tools."""

from typing import Any, Optional, Dict
from pydantic import BaseModel, Field
from backend.app.tools.base import BaseTool
from backend.app.observability.base import BaseJaegerProvider


class TracesQuerySchema(BaseModel):
    service_name: str = Field(description="Service name to inspect traces for (e.g. checkout, payment)")
    operation: Optional[str] = Field(default=None, description="Specific operation or endpoint (e.g. POST /checkout)")
    limit: int = Field(default=10, description="Max traces to retrieve")


class TracesQueryTool(BaseTool):
    name = "traces_query"
    description = "Inspect distributed traces and span waterfalls across services to isolate latency bottlenecks and failing RPC dependencies."
    schema = TracesQuerySchema

    def __init__(self, provider: BaseJaegerProvider):
        super().__init__()
        self.provider = provider

    def _run(self, service_name: str, operation: Optional[str] = None, limit: int = 10) -> Any:
        return self.provider.query_traces(service_name=service_name, operation=operation, limit=limit)
