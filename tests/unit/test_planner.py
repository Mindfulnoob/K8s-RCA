"""Unit tests for the dynamic investigation planner."""

from backend.app.planner.planner import DynamicPlanner
from backend.app.hypotheses.engine import HypothesisEngine
from backend.app.models.evidence import Evidence, NormalizedObservation, EvidenceType


def test_planner_selects_unexecuted_tools():
    hypotheses = HypothesisEngine.generate_initial_hypotheses("Checkout service 5xx errors")
    executed = []
    evidence_history = []

    # First step should prioritize baseline pods listing
    decision1 = DynamicPlanner.select_next_action(
        step_number=1,
        incident="Checkout service 5xx errors",
        namespace="default",
        hypotheses=hypotheses,
        evidence_history=evidence_history,
        executed_queries=executed
    )
    assert decision1 is not None
    assert decision1.target_tool in ["k8s_list_pods", "k8s_get_events"]

    # If k8s_list_pods and k8s_get_events are executed, should explore other sources (Prometheus, Loki)
    executed.extend(["k8s_list_pods", "k8s_get_events"])
    evidence_history.append(Evidence(
        id="ev-1",
        source="Kubernetes",
        query="k8s_list_pods",
        observation=NormalizedObservation(summary="Pod restarts detected"),
        evidence_type=EvidenceType.DIRECT
    ))

    decision2 = DynamicPlanner.select_next_action(
        step_number=2,
        incident="Checkout service 5xx errors",
        namespace="default",
        hypotheses=hypotheses,
        evidence_history=evidence_history,
        executed_queries=executed
    )
    assert decision2 is not None
    assert decision2.target_tool not in ["k8s_list_pods", "k8s_get_events"]


def test_planner_stops_when_sufficient_evidence_reached():
    hypotheses = HypothesisEngine.generate_initial_hypotheses("Checkout service 5xx errors")
    # Simulate high confidence leader with multi-source evidence
    hypotheses[0].current_score = 0.92

    evidence_history = [
        Evidence(id="e1", source="Kubernetes", query="k8s", observation=NormalizedObservation(summary="obs1")),
        Evidence(id="e2", source="Prometheus", query="prom", observation=NormalizedObservation(summary="obs2")),
        Evidence(id="e3", source="Loki", query="loki", observation=NormalizedObservation(summary="obs3")),
        Evidence(id="e4", source="Deployment", query="deploy", observation=NormalizedObservation(summary="obs4")),
    ]

    decision = DynamicPlanner.select_next_action(
        step_number=5,
        incident="Checkout service 5xx errors",
        namespace="default",
        hypotheses=hypotheses,
        evidence_history=evidence_history,
        executed_queries=["k8s_list_pods", "prometheus_query", "logs_query", "deployment_history"]
    )
    # Should stop (return None) because confidence is high and multi-source evidence is gathered
    assert decision is None
