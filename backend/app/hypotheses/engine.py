"""Hypothesis generation and Bayesian belief updating engine."""

from typing import List
from backend.app.models.hypothesis import Hypothesis, HypothesisStatus, BeliefUpdate
from backend.app.models.evidence import Evidence, EvidenceType
from backend.app.hypotheses.catalog import STANDARD_HYPOTHESIS_TEMPLATES


class HypothesisEngine:
    """Manages competing hypotheses and updates probabilistic belief states based on multi-source evidence."""

    @classmethod
    def generate_initial_hypotheses(cls, incident: str) -> List[Hypothesis]:
        """Generates initial competing hypotheses for an incident with normalized priors."""
        incident_lower = incident.lower()
        selected_keys = ["bad_deployment", "database_failure", "oom_killed", "configuration_change", "dependency_outage"]
        
        if "node" in incident_lower or "evict" in incident_lower:
            selected_keys.append("node_pressure")
        if "traffic" in incident_lower or "spike" in incident_lower or "load" in incident_lower:
            selected_keys.append("traffic_spike")
            
        initial_prior = 1.0 / len(selected_keys)
        hypotheses = []

        for key in selected_keys:
            tmpl = STANDARD_HYPOTHESIS_TEMPLATES[key]
            hypotheses.append(Hypothesis(
                id=tmpl["id"],
                category=tmpl["category"],
                description=tmpl["description"],
                prior_score=round(initial_prior, 3),
                current_score=round(initial_prior, 3),
                supporting_evidence=[],
                contradicting_evidence=[],
                required_evidence=tmpl["required_evidence"],
                status=HypothesisStatus.INVESTIGATING,
                rationale="Initialized as candidate failure mode for incident."
            ))

        return hypotheses

    @classmethod
    def update_beliefs(cls, hypotheses: List[Hypothesis], evidence: Evidence) -> List[BeliefUpdate]:
        """Performs Bayesian belief updating across hypotheses given new multi-source evidence."""
        updates: List[BeliefUpdate] = []
        unnormalized_scores = []

        # 1. Compute likelihood multipliers
        for h in hypotheses:
            old_score = h.current_score
            likelihood = 1.0

            is_supporting = (h.id in evidence.supports_hypotheses or h.category in evidence.supports_hypotheses)
            is_weakening = (h.id in evidence.weakens_hypotheses or h.category in evidence.weakens_hypotheses)

            obs_text = (evidence.observation.summary + " " + str(evidence.observation.details)).lower()

            # Direct evidence boosts
            if is_supporting:
                likelihood = 3.6 if evidence.evidence_type == EvidenceType.DIRECT else 2.2
                if evidence.id not in h.supporting_evidence:
                    h.supporting_evidence.append(evidence.id)
            elif is_weakening:
                likelihood = 0.20 if evidence.evidence_type == EvidenceType.DIRECT else 0.40
                if evidence.id not in h.contradicting_evidence:
                    h.contradicting_evidence.append(evidence.id)

            unnorm = max(old_score * likelihood, 0.005)
            unnormalized_scores.append(unnorm)

        # 2. Normalize posterior scores to sum to 1.0
        total_score = sum(unnormalized_scores) or 1.0
        for idx, h in enumerate(hypotheses):
            old_score = h.current_score
            new_score = round(unnormalized_scores[idx] / total_score, 4)
            h.current_score = new_score
            delta = round(new_score - old_score, 4)

            # 3. Update status based on score threshold
            if new_score >= 0.70:
                h.status = HypothesisStatus.SUPPORTED
            elif new_score >= 0.88:
                h.status = HypothesisStatus.CONFIRMED
            elif new_score <= 0.05:
                h.status = HypothesisStatus.REJECTED
            elif new_score < 0.20:
                h.status = HypothesisStatus.WEAKENED
            else:
                h.status = HypothesisStatus.INVESTIGATING

            updates.append(BeliefUpdate(
                hypothesis_id=h.id,
                old_score=old_score,
                new_score=new_score,
                delta=delta,
                trigger_evidence_id=evidence.id,
                rationale=f"Belief updated by {evidence.source} evidence ({old_score:.2f} -> {new_score:.2f})."
            ))

        return updates
