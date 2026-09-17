"""Jaeger Observability Provider for distributed tracing."""

import httpx
from typing import Any, Dict, List, Optional
from datetime import datetime
from backend.app.observability.base import BaseJaegerProvider
from backend.app.observability.simulated_data import ActiveScenarioManager
from backend.app.config import settings


class JaegerProvider(BaseJaegerProvider):
    """Provides distributed trace inspection with live and simulated capabilities."""

    def __init__(self, jaeger_url: Optional[str] = None):
        self.url = jaeger_url or settings.JAEGER_URL
        self.client = httpx.Client(timeout=5.0)

    def query_traces(self, service_name: str, operation: Optional[str] = None, limit: int = 10, tags: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        if not settings.MOCK_MODE:
            try:
                params = {"service": service_name, "limit": limit}
                if operation:
                    params["operation"] = operation
                resp = self.client.get(f"{self.url}/api/traces", params=params)
                if resp.status_code == 200:
                    return resp.json().get("data", [])[:limit]
            except Exception:
                pass

        # Simulated fallback
        scenario = ActiveScenarioManager.get_current_scenario()
        traces = scenario.get("traces", [])
        return [t for t in traces if service_name in t.get("service", "")] or traces

    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        scenario = ActiveScenarioManager.get_current_scenario()
        for t in scenario.get("traces", []):
            if t.get("trace_id") == trace_id:
                return t
        return {"trace_id": trace_id, "spans": []}
