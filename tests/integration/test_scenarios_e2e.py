"""End-to-end integration tests for all 4 reproducible incident scenarios."""

import pytest
from backend.app.agent.orchestrator import InvestigationOrchestrator
from backend.app.observability.simulated_data import ActiveScenarioManager
from backend.app.models.state import InvestigationStatus
from backend.app.models.rca import CausalNodeType


def test_scenario_1_oom_investigation():
    """Verify Scenario 1 (OOM): Multi-step investigation correctly pinpoints OOMKilled memory limit exhaustion."""
    ActiveScenarioManager.set_scenario("oom")
    orchestrator = InvestigationOrchestrator()

    state = orchestrator.run_full_investigation(
        incident="The checkout service is experiencing high 5xx error rate and container restarts.",
        namespace="default",
        max_steps=8
    )

    assert state.status == InvestigationStatus.COMPLETED
    assert len(state.steps) >= 4
    assert len(state.evidence) >= 3
    assert state.rca_report is not None
    assert state.rca_report.is_sufficient_evidence is True
    assert "Memory Limit Exhaustion" in state.rca_report.root_cause
    assert state.confidence >= 75.0

    # Verify OOM hypothesis won and alternatives weakened
    h_oom = next(h for h in state.hypotheses if h.id == "H-OOM")
    assert h_oom.current_score > 0.70
    assert len(h_oom.supporting_evidence) >= 2

    # Verify timeline and causal chain
    assert len(state.timeline) > 0
    assert any("OOM" in node.label or "Memory" in node.label for node in state.rca_report.causal_chain.nodes)


def test_scenario_2_bad_deployment_investigation():
    """Verify Scenario 2 (Bad Deployment): Identifies code regression introduced in release v2.0.0."""
    ActiveScenarioManager.set_scenario("bad_deployment")
    orchestrator = InvestigationOrchestrator()

    state = orchestrator.run_full_investigation(
        incident="Payment service transactions are failing with 100% 500 Internal Server Error following release.",
        namespace="default",
        max_steps=8
    )

    assert state.status == InvestigationStatus.COMPLETED
    assert state.rca_report is not None
    assert "Release Rollout" in state.rca_report.root_cause or "Deployment" in state.rca_report.root_cause
    
    h_deploy = next(h for h in state.hypotheses if h.id == "H-DEPLOY")
    assert h_deploy.current_score > 0.60
    assert state.confidence >= 70.0


def test_scenario_3_dependency_failure_investigation():
    """Verify Scenario 3 (Dependency Failure): Pinpoints downstream database crash and socket refusal."""
    ActiveScenarioManager.set_scenario("dependency_failure")
    orchestrator = InvestigationOrchestrator()

    state = orchestrator.run_full_investigation(
        incident="Checkout service experiencing cascading 504 Gateway Timeout errors.",
        namespace="default",
        max_steps=8
    )

    assert state.status == InvestigationStatus.COMPLETED
    assert state.rca_report is not None
    assert "Database Outage" in state.rca_report.root_cause or "Database" in state.rca_report.root_cause


def test_scenario_4_multi_source_flagship_investigation():
    """Verify Scenario 4 (Multi-Source Flagship): Correlates Deployment + Prometheus + Loki + K8s."""
    ActiveScenarioManager.set_scenario("multi_source")
    orchestrator = InvestigationOrchestrator()

    state = orchestrator.run_full_investigation(
        incident="The checkout service suddenly has a high 5xx error rate, probe failures, and restarts.",
        namespace="default",
        max_steps=9
    )

    assert state.status == InvestigationStatus.COMPLETED
    assert state.rca_report is not None
    assert state.confidence >= 80.0
    assert "Database Connection" in state.rca_report.root_cause or "Pool Exhaustion" in state.rca_report.root_cause

    # Multi-source validation: must have gathered evidence from at least 3 distinct sources!
    sources = {e.source for e in state.evidence}
    assert len(sources) >= 3
    assert "Kubernetes" in sources
    assert "Prometheus" in sources or "Loki" in sources

    # Check causal chain structure
    nodes = state.rca_report.causal_chain.nodes
    types = {n.type for n in nodes}
    assert CausalNodeType.ROOT_CAUSE in types
    assert CausalNodeType.CONTRIBUTING_FACTOR in types
    assert CausalNodeType.TRIGGER in types
    assert CausalNodeType.SYMPTOM in types

    # Check Replay Frames
    assert len(state.replay_frames) >= 4
    for frame in state.replay_frames:
        assert frame.confidence_at_step >= 0.0
        assert len(frame.active_hypotheses) >= 4
