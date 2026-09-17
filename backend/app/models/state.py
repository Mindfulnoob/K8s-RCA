"""Investigation State and Replay models."""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.models.hypothesis import Hypothesis, BeliefUpdate
from backend.app.models.evidence import Evidence
from backend.app.models.timeline import TimelineEvent
from backend.app.models.rca import RCAReport
from backend.app.models.security import SecurityAuditEntry


class InvestigationStatus(str, Enum):
    INITIALIZING = "INITIALIZING"
    INVESTIGATING = "INVESTIGATING"
    HYPOTHESIZING = "HYPOTHESIZING"
    EVALUATING = "EVALUATING"
    SUFFICIENT_EVIDENCE = "SUFFICIENT_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Decision(BaseModel):
    step_number: int
    rationale: str
    chosen_action: str
    target_tool: str
    arguments: Dict[str, Any]
    expected_information_gain: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class InvestigationStep(BaseModel):
    step_number: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str
    decision: Optional[Decision] = None
    tool_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    tool_output_summary: Optional[str] = None
    evidence_collected: List[Evidence] = Field(default_factory=list)
    belief_updates: List[BeliefUpdate] = Field(default_factory=list)
    hypotheses_state: List[Hypothesis] = Field(default_factory=list)
    current_focus: Optional[str] = None
    confidence_score: float = 0.0


class ReplayFrame(BaseModel):
    step_number: int
    timestamp: datetime
    phase: str
    active_hypotheses: List[Dict[str, Any]]
    latest_evidence: Optional[Dict[str, Any]]
    current_thought: str
    executed_query: Optional[str]
    confidence_at_step: float


class InvestigationState(BaseModel):
    id: str
    incident: str
    namespace: str = "default"
    time_range: str = "last 30m"
    status: InvestigationStatus = InvestigationStatus.INITIALIZING
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    current_focus: Optional[str] = "Initial symptom identification"
    confidence: float = 0.0
    confidence_explanation: Optional[str] = None
    
    observations: List[str] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    queries_executed: List[str] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    decisions: List[Decision] = Field(default_factory=list)
    steps: List[InvestigationStep] = Field(default_factory=list)
    replay_frames: List[ReplayFrame] = Field(default_factory=list)
    
    rca_report: Optional[RCAReport] = None
    security_audits: List[SecurityAuditEntry] = Field(default_factory=list)
