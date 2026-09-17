"""Incident Timeline models."""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class EventSource(str, Enum):
    KUBERNETES = "Kubernetes"
    PROMETHEUS = "Prometheus"
    LOKI = "Loki"
    JAEGER = "Jaeger"
    DEPLOYMENT = "Deployment"
    ALERT = "Alert"
    CONFIG = "Config"


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class TimelineEvent(BaseModel):
    id: str
    timestamp: datetime
    source: EventSource
    component: str
    title: str
    description: str
    severity: Severity = Severity.INFO
    related_evidence_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentTimeline(BaseModel):
    events: List[TimelineEvent] = Field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
