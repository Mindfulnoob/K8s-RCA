"""Evaluation API router."""

import json
import os
from typing import Dict, Any
from fastapi import APIRouter
from backend.app.evaluation.framework import EvaluationFramework

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/run")
def run_evaluation_benchmark() -> Dict[str, Any]:
    """Runs the full automated evaluation suite against ground truth across all 4 scenarios."""
    return EvaluationFramework.run_all_benchmarks()


@router.get("/latest")
def get_latest_evaluation() -> Dict[str, Any]:
    """Retrieves the latest generated evaluation report or runs a new one if none exists."""
    if os.path.exists("evaluation_report.json"):
        try:
            with open("evaluation_report.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return EvaluationFramework.run_all_benchmarks()
