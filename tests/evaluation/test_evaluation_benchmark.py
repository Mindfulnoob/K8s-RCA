"""Evaluation benchmark test suite."""

import os
from backend.app.evaluation.framework import EvaluationFramework


def test_evaluation_framework_generates_report():
    report = EvaluationFramework.run_all_benchmarks(output_file="evaluation_report.json")
    
    assert report["total_scenarios_tested"] == 4
    assert report["overall_accuracy_rate"] >= 0.75
    assert report["average_evidence_coverage"] >= 0.70
    assert report["average_efficiency"] >= 0.70
    assert os.path.exists("evaluation_report.json")
