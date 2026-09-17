"""CLI script to run automated SRE investigation benchmarks."""

import sys
import os
import json

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.evaluation.framework import EvaluationFramework


def main():
    print("=" * 70)
    print("  RUNNING AUTONOMOUS KUBERNETES RCA AGENT BENCHMARK SUITE")
    print("=" * 70)

    report = EvaluationFramework.run_all_benchmarks(output_file="evaluation_report.json")

    print(f"\nTotal Scenarios Evaluated: {report['total_scenarios_tested']}")
    print(f"Overall RCA Accuracy:      {report['overall_accuracy_rate']*100:.1f}%")
    print(f"Average Evidence Coverage: {report['average_evidence_coverage']*100:.1f}%")
    print(f"Average Efficiency Score:  {report['average_efficiency']*100:.1f}%\n")

    print("-" * 70)
    print(f"{'Scenario':<20} | {'Winner':<10} | {'Expected':<10} | {'Conf':<6} | {'Accuracy'}")
    print("-" * 70)
    for r in report["results"]:
        status_mark = "[PASS]" if r["is_accurate"] else "[FAIL]"
        print(f"{r['scenario_id']:<20} | {r['winning_hypothesis']:<10} | {r['expected_hypothesis']:<10} | {r['confidence_score']:<5.1f}% | {status_mark}")
    print("-" * 70)
    print("\nComplete report written to: evaluation_report.json\n")


if __name__ == "__main__":
    main()
