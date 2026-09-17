"""Loki Observability Provider (HTTP Client with simulated fallback)."""

import httpx
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from backend.app.observability.base import BaseLokiProvider
from backend.app.observability.simulated_data import ActiveScenarioManager
from backend.app.config import settings


class LokiProvider(BaseLokiProvider):
    """Provides LogQL query execution with live and simulated capabilities."""

    def __init__(self, loki_url: Optional[str] = None):
        self.url = loki_url or settings.LOKI_URL
        self.client = httpx.Client(timeout=5.0)

    def query_logs(self, query: str, limit: int = 50, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[Dict[str, Any]]:
        if not settings.MOCK_MODE:
            try:
                params = {"query": query, "limit": limit}
                if start:
                    params["start"] = str(int(start.timestamp() * 1e9))
                if end:
                    params["end"] = str(int(end.timestamp() * 1e9))
                resp = self.client.get(f"{self.url}/loki/api/v1/query_range", params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for stream in data.get("data", {}).get("result", []):
                        for val in stream.get("values", []):
                            results.append({"timestamp": val[0], "message": val[1], "labels": stream.get("stream")})
                    return results[:limit]
            except Exception:
                pass

        # Simulated fallback
        scenario = ActiveScenarioManager.get_current_scenario()
        logs = scenario.get("logs", [])
        
        # Check if query has regex or literal filter (e.g. |= "error" or |= "Exception")
        filter_match = re.search(r'\|=\s*["\']([^"\']+)["\']', query)
        filter_str = filter_match.group(1).lower() if filter_match else None

        filtered_logs = []
        for log in logs:
            msg = log.get("message", "").lower()
            lvl = log.get("level", "").lower()
            
            if filter_str:
                if filter_str == "error":
                    if lvl in ["error", "fatal"] or "error" in msg or "exception" in msg or "timeout" in msg:
                        filtered_logs.append(log)
                elif filter_str in msg or filter_str in lvl:
                    filtered_logs.append(log)
            else:
                filtered_logs.append(log)

        return filtered_logs[:limit]

    def query_previous_container_logs(self, pod_name: str, container_name: Optional[str] = None, namespace: str = "default", tail_lines: int = 100) -> List[Dict[str, Any]]:
        scenario = ActiveScenarioManager.get_current_scenario()
        logs = scenario.get("logs", [])
        return [log for log in logs if log.get("level") in ["FATAL", "ERROR", "WARN"]][:tail_lines]
