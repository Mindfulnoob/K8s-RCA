"""Evaluation module exports."""

from backend.app.evaluation.framework import EvaluationFramework
from backend.app.evaluation.ground_truth import GROUND_TRUTH_BENCHMARKS

__all__ = ["EvaluationFramework", "GROUND_TRUTH_BENCHMARKS"]
