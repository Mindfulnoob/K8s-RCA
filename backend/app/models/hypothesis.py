"""Hypothesis data models."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class HypothesisStatus(str, Enum):
    UNTESTED = "UNTESTED"
    INVESTIGATING = "INVESTIGATING"
    SUPPORTED = "SUPPORTED"
    WEAKENED = "WEAKENED"
    REJECTED = "REJECTED"
    CONFIRMED = "CONFIRMED"


class Hypothesis(BaseModel):
    id: str
    category: str  # e.g. "deployment", "database", "resource", "network", "configuration"
    description: str
    prior_score: float = Field(ge=0.0, le=1.0, default=0.2)
    current_score: float = Field(ge=0.0, le=1.0, default=0.2)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    required_evidence: List[str] = Field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.UNTESTED
    rationale: Optional[str] = None


class BeliefUpdate(BaseModel):
    hypothesis_id: str
    old_score: float
    new_score: float
    delta: float
    trigger_evidence_id: str
    rationale: str
