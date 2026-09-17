"""Evidence data models."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    DIRECT = "DIRECT"
    CORRELATED = "CORRELATED"
    INDIRECT = "INDIRECT"
    NEGATIVE = "NEGATIVE"


class Reliability(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class NormalizedObservation(BaseModel):
    summary: str
    metric_name: Optional[str] = None
    observed_value: Optional[str] = None
    baseline_value: Optional[str] = None
    anomaly_detected: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    id: str
    source: str  # "Kubernetes", "Prometheus", "Loki", "Jaeger", "Config"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    query: str
    raw_data: Optional[Union[Dict[str, Any], List[Any], str]] = None
    observation: NormalizedObservation
    related_hypotheses: List[str] = Field(default_factory=list)
    supports_hypotheses: List[str] = Field(default_factory=list)
    weakens_hypotheses: List[str] = Field(default_factory=list)
    evidence_type: EvidenceType = EvidenceType.DIRECT
    reliability: Reliability = Reliability.HIGH
    source_component: Optional[str] = None
    security_flagged: bool = False
    security_note: Optional[str] = None
