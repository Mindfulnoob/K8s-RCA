"""Prometheus metrics query tools."""

from typing import Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from backend.app.tools.base import BaseTool
from backend.app.observability.base import BasePrometheusProvider


class PrometheusQuerySchema(BaseModel):
    query: str = Field(description="PromQL instant query (e.g. rate(http_requests_total[5m]))")


class PrometheusRangeQuerySchema(BaseModel):
    query: str = Field(description="PromQL range query expression")
    minutes_ago: int = Field(default=30, description="Window size in minutes")
    step: str = Field(default="1m", description="Evaluation resolution step (e.g. 30s, 1m)")


class PrometheusQueryTool(BaseTool):
    name = "prometheus_query"
    description = "Execute an instant PromQL query to inspect current metric values (CPU, memory, connection pools, error rates)."
    schema = PrometheusQuerySchema

    def __init__(self, provider: BasePrometheusProvider):
        super().__init__()
        self.provider = provider

    def _run(self, query: str) -> Any:
        return self.provider.query(query=query)


class PrometheusRangeQueryTool(BaseTool):
    name = "prometheus_range_query"
    description = "Execute a PromQL range query to inspect metric trends, spikes, and saturation over a time window."
    schema = PrometheusRangeQuerySchema

    def __init__(self, provider: BasePrometheusProvider):
        super().__init__()
        self.provider = provider

    def _run(self, query: str, minutes_ago: int = 30, step: str = "1m") -> Any:
        end = datetime.utcnow()
        start = end - timedelta(minutes=minutes_ago)
        return self.provider.range_query(query=query, start=start, end=end, step=step)
