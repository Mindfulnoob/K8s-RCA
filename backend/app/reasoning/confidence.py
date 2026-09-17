"""Transparent, multi-factor confidence scoring engine."""

from typing import List, Tuple, Set
from backend.app.models.hypothesis import Hypothesis
from backend.app.models.evidence import Evidence, Reliability


class ConfidenceCalculator:
    """Calculates an explainable 0-100% confidence rating based on multi-source evidence diversity and consistency."""

    @classmethod
    def calculate_confidence(
        cls,
        hypotheses: List[Hypothesis],
        evidence_list: List[Evidence],
    ) -> Tuple[float, str]:
        if not hypotheses or not evidence_list:
            return 10.0, "Investigation initialized. Insufficient evidence gathered to establish confidence."

        # 1. Leading hypothesis and runner-up
        sorted_h = sorted(hypotheses, key=lambda h: h.current_score, reverse=True)
        leader = sorted_h[0]
        runner_up = sorted_h[1] if len(sorted_h) > 1 else None
        
        # Base confidence from Bayesian belief
        base_confidence = leader.current_score * 50.0

        # 2. Source diversity bonus (+7.5% per distinct independent source, max 30%)
        distinct_sources: Set[str] = {e.source for e in evidence_list}
        diversity_bonus = min(len(distinct_sources) * 7.5, 30.0)

        # 3. Direct evidence support bonus (+4.0% per supporting observation, max 20%)
        direct_support_count = sum(
            1 for e in evidence_list
            if leader.id in e.supports_hypotheses or leader.category in e.supports_hypotheses
        )
        support_bonus = min(direct_support_count * 4.0, 20.0)

        # 4. Multi-source correlation bonus: if evidence spans both metrics AND logs AND k8s
        correlation_bonus = 0.0
        if {"Prometheus", "Loki"}.issubset(distinct_sources) or ({"Kubernetes", "Prometheus"}.issubset(distinct_sources) and len(evidence_list) >= 3):
            correlation_bonus = 8.0

        # 5. Separation bonus if leader decisively outscores runner-up
        separation_bonus = 0.0
        if runner_up:
            margin = leader.current_score - runner_up.current_score
            if margin > 0.40:
                separation_bonus = 8.0
            elif margin > 0.20:
                separation_bonus = 4.0

        # 6. Contradiction penalty (-12% per active contradiction on leader)
        contradiction_penalty = len(leader.contradicting_evidence) * 12.0

        raw_total = base_confidence + diversity_bonus + support_bonus + correlation_bonus + separation_bonus - contradiction_penalty
        final_confidence = round(max(min(raw_total, 96.0), 10.0), 1)

        sources_str = ", ".join(sorted(distinct_sources))
        explanation = (
            f"Confidence calculated at {final_confidence}% for leading hypothesis '{leader.id}' ({leader.category}): "
            f"Posterior belief {leader.current_score*100:.1f}%; corroborated across {len(distinct_sources)} independent "
            f"sources ({sources_str}); supported by {len(leader.supporting_evidence)} validated evidence observations; "
            f"{len(leader.contradicting_evidence)} active contradictions; runner-up margin {leader.current_score - (runner_up.current_score if runner_up else 0):.2f}."
        )

        return final_confidence, explanation
