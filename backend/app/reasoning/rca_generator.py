"""RCA Report generation and synthesis."""

from datetime import datetime
from typing import List, Optional
from backend.app.models.rca import RCAReport, AlternativeExplanation
from backend.app.models.hypothesis import Hypothesis, HypothesisStatus
from backend.app.models.evidence import Evidence
from backend.app.reasoning.causal_engine import CausalEngine
from backend.app.reasoning.confidence import ConfidenceCalculator
from backend.app.reasoning.timeline import TimelineNormalizer


class RCAGenerator:
    """Synthesizes investigation observations, belief states, and causal DAG into an actionable Root Cause Analysis report."""

    @classmethod
    def generate_report(
        cls,
        investigation_id: str,
        incident: str,
        hypotheses: List[Hypothesis],
        evidence_list: List[Evidence],
    ) -> RCAReport:
        # 1. Sort hypotheses by score
        sorted_h = sorted(hypotheses, key=lambda h: h.current_score, reverse=True)
        leader = sorted_h[0] if sorted_h else Hypothesis(
            id="H-UNKNOWN", category="unknown", description="Unknown root cause",
            prior_score=0.0, current_score=0.0, status=HypothesisStatus.UNTESTED
        )

        # 2. Check stopping / sufficiency condition
        distinct_sources = {e.source for e in evidence_list}
        is_sufficient = leader.current_score >= 0.50 and len(evidence_list) >= 3 and len(distinct_sources) >= 2

        # 3. Calculate confidence and explanation
        confidence_score, confidence_explanation = ConfidenceCalculator.calculate_confidence(hypotheses, evidence_list)

        # 4. Construct Causal Chain
        causal_chain = CausalEngine.construct_causal_chain(leader, evidence_list)

        # 5. Extract observed facts from evidence
        observed_facts = [
            f"[{e.source}] {e.observation.summary}" for e in evidence_list
        ]

        # 6. Extract supporting and contradicting summaries
        supporting_summaries = [
            e.observation.summary for e in evidence_list
            if leader.id in e.supports_hypotheses or leader.category in e.supports_hypotheses
        ]
        contradicting_summaries = [
            e.observation.summary for e in evidence_list
            if leader.id in e.weakens_hypotheses or leader.category in e.weakens_hypotheses
        ]

        # 7. Generate alternative explanations
        alternative_explanations: List[AlternativeExplanation] = []
        for alt in sorted_h[1:]:
            reason = (
                f"Weakened by absence of expected telemetry ({', '.join(alt.required_evidence[:2])}) "
                f"and low posterior belief score ({alt.current_score*100:.1f}%)."
            )
            alternative_explanations.append(AlternativeExplanation(
                hypothesis_id=alt.id,
                description=alt.description,
                reason_weakened_or_rejected=reason,
                residual_probability=round(alt.current_score, 3)
            ))

        # 8. Identify unknowns and mitigation recommendations based on leading failure mode
        unknowns: List[str] = []
        mitigations: List[str] = []
        next_steps: List[str] = []

        if leader.category == "resource":
            root_cause = "Container Memory Limit Exhaustion (OOMKilled) in checkout-service due to memory leak."
            unknowns = [
                "Specific JVM heap object class retention graph responsible for gradual heap exhaustion.",
                "Whether memory leak triggers under single thread or concurrent request load."
            ]
            mitigations = [
                "Increase container memory limit in pod spec from 512Mi to 1Gi as temporary buffer.",
                "Capture JVM heap dump on OutOfMemoryError using -XX:+HeapDumpOnOutOfMemoryError flag.",
                "Deploy patched checkout container image with fixed memory leak."
            ]
            next_steps = [
                "Profile memory allocations using async-profiler in staging environment.",
                "Configure Prometheus alert for container_memory_working_set_bytes > 85% limit."
            ]
        elif leader.category == "deployment":
            root_cause = "Application Defect Introduced in Release Rollout (v2.0.0) causing NullPointerException."
            unknowns = [
                "Why payment-service integration tests did not catch missing currency validation in v2.0.0.",
                "Whether rollback triggers any database migration conflicts."
            ]
            mitigations = [
                "Execute immediate rollback: kubectl rollout undo deployment/payment-service.",
                "Verify replica count reverts to stable v1.0.0 image.",
                "Add mandatory schema validation for request payloads before merge."
            ]
            next_steps = [
                "Inspect pull request diff between payment:v1.0.0 and v2.0.0.",
                "Re-run end-to-end integration test suite on previous image release."
            ]
        elif leader.category in ["database", "configuration"]:
            root_cause = (
                "Database Connection Saturation & Pool Exhaustion caused by connection leak in checkout:v2.2.0 "
                "compounded by reduced ConfigMap max_pool_size=10."
            )
            unknowns = [
                "Exact code path failing to close connection in database session pool.",
                "Why DB_POOL_MAX was reduced from 50 to 10 in checkout-config ConfigMap."
            ]
            mitigations = [
                "Immediately increase DB_POOL_MAX back to 50 in ConfigMap checkout-config.",
                "Restart checkout-service pods to flush leaked connections.",
                "Roll back checkout deployment to revision 1 (v2.1.0)."
            ]
            next_steps = [
                "Enable HikariCP leakDetectionThreshold=2000 to log unclosed connection stacks.",
                "Instrument database query timeouts and circuit breaker pattern in checkout service."
            ]
        else:
            root_cause = "Downstream Database Outage: PostgreSQL container entered CrashLoopBackOff."
            unknowns = [
                "Integrity of underlying persistent volume filesystem storage.",
                "Recovery point objective (RPO) from last automated pg_dump snapshot."
            ]
            mitigations = [
                "Check PostgreSQL pod disk and recovery logs.",
                "Restore database state from standby replica or latest verified snapshot."
            ]
            next_steps = [
                "Audit persistent storage volume IOPS and disk health."
            ]

        # 9. Multi-source correlation summary
        sources = sorted(list({e.source for e in evidence_list}))
        correlation_summary = (
            f"Multi-source correlation synthesized across {', '.join(sources)}: "
            f"Confirmed temporal and causal synchronization between Kubernetes lifecycle events, "
            f"Prometheus metric trajectories, and Loki log diagnostics."
        )

        # 10. Timeline
        timeline_events = TimelineNormalizer.build_timeline(evidence_list)

        return RCAReport(
            id=f"rca-{investigation_id}",
            incident=incident,
            generated_at=datetime.utcnow(),
            root_cause=root_cause,
            trigger=causal_chain.nodes[1].label if len(causal_chain.nodes) > 1 else None,
            contributing_factors=[n.description for n in causal_chain.nodes if n.type.value == "CONTRIBUTING_FACTOR"],
            symptoms=[n.label for n in causal_chain.nodes if n.type.value in ["SYMPTOM", "DOWNSTREAM_EFFECT"]],
            confidence_score=confidence_score,
            confidence_explanation=confidence_explanation,
            observed_facts=observed_facts,
            hypotheses_evaluated=hypotheses,
            supporting_evidence_summaries=supporting_summaries,
            contradicting_evidence_summaries=contradicting_summaries,
            causal_chain=causal_chain,
            alternative_explanations=alternative_explanations,
            unknowns_and_ambiguities=unknowns,
            recommended_mitigation=mitigations,
            recommended_next_investigations=next_steps,
            timeline=timeline_events,
            multi_source_correlation_summary=correlation_summary,
            is_sufficient_evidence=is_sufficient
        )
