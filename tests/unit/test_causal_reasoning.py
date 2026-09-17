"""Unit tests for causal graph and RCA generator."""

from backend.app.reasoning.causal_engine import CausalEngine
from backend.app.reasoning.rca_generator import RCAGenerator
from backend.app.models.hypothesis import Hypothesis, HypothesisStatus
from backend.app.models.evidence import Evidence, NormalizedObservation, EvidenceType
from backend.app.models.rca import CausalNodeType


def test_causal_engine_separates_root_cause_from_symptoms():
    hypothesis = Hypothesis(
        id="H-DB",
        category="database",
        description="Database connection pool exhaustion",
        prior_score=0.2,
        current_score=0.90,
        status=HypothesisStatus.CONFIRMED
    )

    evidence = [
        Evidence(id="e1", source="Loki", query="logs", observation=NormalizedObservation(summary="connection pool exhausted")),
        Evidence(id="e2", source="Prometheus", query="prom", observation=NormalizedObservation(summary="active connections 10/10"))
    ]

    causal_chain = CausalEngine.construct_causal_chain(hypothesis, evidence)
    
    # Verify nodes have distinct types
    types = {n.type for n in causal_chain.nodes}
    assert CausalNodeType.ROOT_CAUSE in types
    assert CausalNodeType.SYMPTOM in types
    assert CausalNodeType.TRIGGER in types
    
    # Verify edges exist connecting nodes
    assert len(causal_chain.edges) >= 3


def test_rca_report_generation():
    hypotheses = [
        Hypothesis(id="H-OOM", category="resource", description="OOMKilled", prior_score=0.2, current_score=0.88, status=HypothesisStatus.CONFIRMED),
        Hypothesis(id="H-DB", category="database", description="DB failure", prior_score=0.2, current_score=0.08, status=HypothesisStatus.WEAKENED)
    ]

    evidence_list = [
        Evidence(id="e1", source="Kubernetes", query="k8s", observation=NormalizedObservation(summary="OOMKilled exit code 137"), supports_hypotheses=["H-OOM"]),
        Evidence(id="e2", source="Prometheus", query="prom", observation=NormalizedObservation(summary="memory climbing to 512Mi"), supports_hypotheses=["H-OOM"]),
        Evidence(id="e3", source="Loki", query="logs", observation=NormalizedObservation(summary="OutOfMemoryError in JVM heap"), supports_hypotheses=["H-OOM"])
    ]

    report = RCAGenerator.generate_report(
        investigation_id="inv-test-1",
        incident="Checkout 5xx errors",
        hypotheses=hypotheses,
        evidence_list=evidence_list
    )

    assert report.confidence_score >= 80.0
    assert "Memory Limit Exhaustion" in report.root_cause
    assert len(report.observed_facts) == 3
    assert len(report.alternative_explanations) == 1
    assert len(report.recommended_mitigation) > 0
    assert report.is_sufficient_evidence is True
