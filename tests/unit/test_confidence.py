"""Unit tests for transparent confidence calculation."""

from backend.app.reasoning.confidence import ConfidenceCalculator
from backend.app.hypotheses.engine import HypothesisEngine
from backend.app.models.evidence import Evidence, NormalizedObservation, EvidenceType


def test_confidence_calculation_multisource():
    hypotheses = HypothesisEngine.generate_initial_hypotheses("Checkout service incident")
    hypotheses[0].current_score = 0.85
    hypotheses[0].supporting_evidence = ["e1", "e2", "e3"]
    
    # 3 independent sources: K8s, Prometheus, Loki
    evidence_list = [
        Evidence(id="e1", source="Kubernetes", query="k8s", observation=NormalizedObservation(summary="restarts"), supports_hypotheses=[hypotheses[0].id]),
        Evidence(id="e2", source="Prometheus", query="prom", observation=NormalizedObservation(summary="metrics spike"), supports_hypotheses=[hypotheses[0].id]),
        Evidence(id="e3", source="Loki", query="loki", observation=NormalizedObservation(summary="error logs"), supports_hypotheses=[hypotheses[0].id]),
    ]

    conf, explanation = ConfidenceCalculator.calculate_confidence(hypotheses, evidence_list)
    assert conf >= 75.0
    assert "independent sources" in explanation
    assert "Posterior belief" in explanation


def test_confidence_penalizes_contradictions():
    hypotheses = HypothesisEngine.generate_initial_hypotheses("Checkout service incident")
    hypotheses[0].current_score = 0.70
    hypotheses[0].contradicting_evidence = ["c1"]

    evidence_list = [
        Evidence(id="c1", source="Prometheus", query="prom", observation=NormalizedObservation(summary="healthy memory"), weakens_hypotheses=[hypotheses[0].id])
    ]

    conf, explanation = ConfidenceCalculator.calculate_confidence(hypotheses, evidence_list)
    assert conf < 65.0
    assert "contradictions" in explanation
