"""Root Cause Analysis (RCA) models."""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.models.timeline import TimelineEvent
from backend.app.models.hypothesis import Hypothesis


class CausalNodeType(str, Enum):
    ROOT_CAUSE = "ROOT_CAUSE"
    TRIGGER = "TRIGGER"
    CONTRIBUTING_FACTOR = "CONTRIBUTING_FACTOR"
    SYMPTOM = "SYMPTOM"
    DOWNSTREAM_EFFECT = "DOWNSTREAM_EFFECT"


class CausalNode(BaseModel):
    id: str
    label: str
    type: CausalNodeType
    description: str
    component: str
    evidence_ids: List[str] = Field(default_factory=list)


class CausalEdge(BaseModel):
    source_id: str
    target_id: str
    relationship: str  # e.g. "causes", "triggers", "exacerbates"


class CausalChain(BaseModel):
    nodes: List[CausalNode] = Field(default_factory=list)
    edges: List[CausalEdge] = Field(default_factory=list)
    summary: str


class AlternativeExplanation(BaseModel):
    hypothesis_id: str
    description: str
    reason_weakened_or_rejected: str
    residual_probability: float


class RCAReport(BaseModel):
    id: str
    incident: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    root_cause: str
    trigger: Optional[str] = None
    contributing_factors: List[str] = Field(default_factory=list)
    symptoms: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=100.0)
    confidence_explanation: str
    observed_facts: List[str] = Field(default_factory=list)
    hypotheses_evaluated: List[Hypothesis] = Field(default_factory=list)
    supporting_evidence_summaries: List[str] = Field(default_factory=list)
    contradicting_evidence_summaries: List[str] = Field(default_factory=list)
    causal_chain: CausalChain
    alternative_explanations: List[AlternativeExplanation] = Field(default_factory=list)
    unknowns_and_ambiguities: List[str] = Field(default_factory=list)
    recommended_mitigation: List[str] = Field(default_factory=list)
    recommended_next_investigations: List[str] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    multi_source_correlation_summary: Optional[str] = None
    is_sufficient_evidence: bool = True
