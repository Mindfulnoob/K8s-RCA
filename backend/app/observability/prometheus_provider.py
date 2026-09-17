"""Prometheus Observability Provider (HTTP Client with simulated fallback)."""

import httpx
from typing import Any, Dict, List, Optional
from datetime import datetime
from backend.app.observability.base import BasePrometheusProvider
from backend.app.observability.simulated_data import ActiveScenarioManager
from backend.app.config import settings


class PrometheusProvider(BasePrometheusProvider):
    """Provides PromQL query execution with live and simulated capabilities."""

    def __init__(self, prometheus_url: Optional[str] = None):
        self.url = prometheus_url or settings.PROMETHEUS_URL
        self.client = httpx.Client(timeout=5.0)

    def query(self, query: str, time: Optional[datetime] = None) -> Dict[str, Any]:
        if not settings.MOCK_MODE:
            try:
                params = {"query": query}
                if time:
                    params["time"] = time.isoformat()
                resp = self.client.get(f"{self.url}/api/v1/query", params=params)
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                pass

        # Simulated fallback matching PromQL query strings
        scenario = ActiveScenarioManager.get_current_scenario()
        metrics = scenario.get("metrics", {})
        
        # Match query prefix or substrings
        for q_key, series in metrics.items():
            core_name = q_key.split("{")[0].strip()
            if core_name in query or q_key in query:
                latest = series[-1] if series else {"time": datetime.utcnow().isoformat(), "value": "0"}
                return {
                    "status": "success",
                    "data": {
                        "resultType": "vector",
                        "result": [
                            {
                                "metric": {"query": query},
                                "value": [datetime.utcnow().timestamp(), str(latest["value"])]
                            }
                        ]
                    }
                }

        # Default simulated empty or zero response
        return {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"query": query},
                        "value": [datetime.utcnow().timestamp(), "0"]
                    }
                ]
            }
        }

    def range_query(self, query: str, start: datetime, end: datetime, step: str = "30s") -> Dict[str, Any]:
        if not settings.MOCK_MODE:
            try:
                params = {
                    "query": query,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "step": step
                }
                resp = self.client.get(f"{self.url}/api/v1/query_range", params=params)
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                pass

        scenario = ActiveScenarioManager.get_current_scenario()
        metrics = scenario.get("metrics", {})
        
        for q_key, series in metrics.items():
            core_name = q_key.split("{")[0].strip()
            if core_name in query or q_key in query:
                values = [[datetime.fromisoformat(item["time"]).timestamp(), str(item["value"])] for item in series]
                return {
                    "status": "success",
                    "data": {
                        "resultType": "matrix",
                        "result": [
                            {
                                "metric": {"query": query},
                                "values": values
                            }
                        ]
                    }
                }

        return {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": []
            }
        }
