"""Automated Evaluation Framework."""

import json
import os
from typing import Dict, Any, List
from datetime import datetime

from backend.app.agent.orchestrator import InvestigationOrchestrator
from backend.app.observability.simulated_data import ActiveScenarioManager
from backend.app.evaluation.ground_truth import GROUND_TRUTH_BENCHMARKS


class EvaluationFramework:
    """Executes automated SRE RCA benchmarks and generates evaluation reports."""

    @classmethod
    def run_all_benchmarks(cls, output_file: str = "evaluation_report.json") -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        orchestrator = InvestigationOrchestrator()

        total_scenarios = len(GROUND_TRUTH_BENCHMARKS)
        correct_root_causes = 0
        total_evidence_coverage = 0.0
        total_efficiency = 0.0

        for scenario_id, gt in GROUND_TRUTH_BENCHMARKS.items():
            ActiveScenarioManager.set_scenario(scenario_id)
            state = orchestrator.run_full_investigation(
                incident=gt["incident_prompt"],
                namespace="default",
                max_steps=gt["max_acceptable_queries"]
            )

            # 1. Evaluate root cause accuracy
            rca_text = (state.rca_report.root_cause + " " + state.rca_report.confidence_explanation).lower()
            keyword_matches = [kw for kw in gt["expected_root_cause_keywords"] if kw in rca_text]
            rca_accuracy = len(keyword_matches) / max(len(gt["expected_root_cause_keywords"]), 1)
            is_accurate = rca_accuracy >= 0.40 or any(kw in state.rca_report.root_cause.lower() for kw in gt["expected_root_cause_keywords"][:2])
            if is_accurate:
                correct_root_causes += 1

            # 2. Evaluate evidence coverage across expected sources
            sources_found = {e.source for e in state.evidence}
            source_coverage = len(sources_found.intersection(set(gt["required_sources"]))) / max(len(gt["required_sources"]), 1)
            total_evidence_coverage += source_coverage

            # 3. Evaluate false positive hypotheses
            winning_hypothesis = max(state.hypotheses, key=lambda h: h.current_score)
            has_false_positive = winning_hypothesis.id in gt["forbidden_hypotheses"]

            # 4. Investigation efficiency (useful vs acceptable queries)
            query_count = len(state.queries_executed)
            efficiency = max(min((gt["max_acceptable_queries"] - max(query_count - gt["max_acceptable_queries"], 0)) / gt["max_acceptable_queries"], 1.0), 0.0)
            total_efficiency += efficiency

            # 5. Causal DAG coverage
            nodes_text = " ".join([n.label for n in state.rca_report.causal_chain.nodes]).lower()
            causal_matches = [cn for cn in gt["expected_causal_nodes"] if cn.lower() in nodes_text]
            causal_coverage = len(causal_matches) / max(len(gt["expected_causal_nodes"]), 1)

            results.append({
                "scenario_id": scenario_id,
                "incident": gt["incident_prompt"],
                "identified_root_cause": state.rca_report.root_cause,
                "confidence_score": state.confidence,
                "accuracy_score": round(rca_accuracy, 3),
                "is_accurate": is_accurate,
                "winning_hypothesis": winning_hypothesis.id,
                "expected_hypothesis": gt["expected_winning_hypothesis"],
                "hypothesis_matched": winning_hypothesis.id == gt["expected_winning_hypothesis"],
                "source_coverage": round(source_coverage, 3),
                "causal_coverage": round(causal_coverage, 3),
                "queries_executed": query_count,
                "max_acceptable_queries": gt["max_acceptable_queries"],
                "efficiency_score": round(efficiency, 3),
                "has_false_positive": has_false_positive,
                "investigation_steps": len(state.steps)
            })

        summary = {
            "evaluation_timestamp": datetime.utcnow().isoformat(),
            "total_scenarios_tested": total_scenarios,
            "overall_accuracy_rate": round(correct_root_causes / total_scenarios, 3),
            "average_evidence_coverage": round(total_evidence_coverage / total_scenarios, 3),
            "average_efficiency": round(total_efficiency / total_scenarios, 3),
            "results": results
        }

        # Write to evaluation_report.json
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
        except Exception:
            pass

        return summary
