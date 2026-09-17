"""Unit tests for hypothesis generation and Bayesian belief updates."""

from backend.app.hypotheses.engine import HypothesisEngine
from backend.app.models.evidence import Evidence, EvidenceType, Reliability, NormalizedObservation
from backend.app.models.hypothesis import HypothesisStatus


def test_generate_initial_hypotheses():
    hypotheses = HypothesisEngine.generate_initial_hypotheses("Checkout service 5xx error rate spike")
    assert len(hypotheses) >= 5
    ids = [h.id for h in hypotheses]
    assert "H-DEPLOY" in ids
    assert "H-DB" in ids
    assert "H-OOM" in ids
    
    # Check that prior probabilities sum to approximately 1.0
    total_prior = sum(h.prior_score for h in hypotheses)
    assert abs(total_prior - 1.0) < 0.05


def test_bayesian_belief_update_supporting():
    hypotheses = HypothesisEngine.generate_initial_hypotheses("Checkout service 5xx error rate spike")
    initial_oom_score = next(h.current_score for h in hypotheses if h.id == "H-OOM")

    # Introduce direct OOMKilled evidence
    evidence = Evidence(
        id="ev-1",
        source="Kubernetes",
        query="k8s_get_events",
        observation=NormalizedObservation(
            summary="Pod was terminated due to memory limit exceeding 512Mi (OOMKilled exit code 137).",
            anomaly_detected=True
        ),
        supports_hypotheses=["H-OOM"],
        weakens_hypotheses=["H-DEPLOY", "H-DB"],
        evidence_type=EvidenceType.DIRECT,
        reliability=Reliability.HIGH
    )

    updates = HypothesisEngine.update_beliefs(hypotheses, evidence)
    updated_oom = next(h for h in hypotheses if h.id == "H-OOM")
    
    # OOM belief should have substantially increased
    assert updated_oom.current_score > initial_oom_score
    assert updated_oom.current_score > 0.45
    assert updated_oom.status in [HypothesisStatus.SUPPORTED, HypothesisStatus.INVESTIGATING]
    assert "ev-1" in updated_oom.supporting_evidence

    # Sum of current scores should remain 1.0
    assert abs(sum(h.current_score for h in hypotheses) - 1.0) < 0.01
