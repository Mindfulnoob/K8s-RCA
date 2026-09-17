"""Unit tests for the tool registry and execution."""

import pytest
from backend.app.tools import create_tool_registry
from backend.app.observability.simulated_data import ActiveScenarioManager


def test_tool_registry_contains_all_required_tools():
    registry = create_tool_registry()
    names = registry.list_tool_names()
    
    assert "k8s_list_pods" in names
    assert "k8s_get_pod" in names
    assert "k8s_get_events" in names
    assert "prometheus_query" in names
    assert "logs_query" in names
    assert "traces_query" in names
    assert "deployment_history" in names
    assert "dependency_graph" in names
    assert len(names) == 16


def test_tool_execution_with_simulated_data():
    ActiveScenarioManager.set_scenario("oom")
    registry = create_tool_registry()
    
    # 1. Test k8s_list_pods
    res = registry.execute("k8s_list_pods", {"namespace": "default"})
    assert res.success is True
    assert isinstance(res.output, list)
    assert any("checkout-service" in p["name"] for p in res.output)

    # 2. Test k8s_get_events
    events_res = registry.execute("k8s_get_events", {"namespace": "default"})
    assert events_res.success is True
    assert any(e["reason"] == "OOMKilled" for e in events_res.output)

    # 3. Test prometheus_query
    prom_res = registry.execute("prometheus_query", {"query": 'container_memory_working_set_bytes{pod=~"checkout.*"}'})
    assert prom_res.success is True
    assert prom_res.output["status"] == "success"

    # 4. Test logs_query
    logs_res = registry.execute("logs_query", {"query": '{app="checkout"} |= "OutOfMemoryError"'})
    assert logs_res.success is True
    assert len(logs_res.output) > 0
