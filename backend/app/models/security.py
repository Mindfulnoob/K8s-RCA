"""Security Sandbox and Audit models."""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SecurityViolationType(str, Enum):
    FORBIDDEN_VERB = "FORBIDDEN_VERB"
    SECRET_ACCESS_ATTEMPT = "SECRET_ACCESS_ATTEMPT"
    PROMPT_INJECTION_DETECTED = "PROMPT_INJECTION_DETECTED"
    UNAUTHORIZED_NAMESPACE = "UNAUTHORIZED_NAMESPACE"
    PARAMETER_TAMPERING = "PARAMETER_TAMPERING"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


class ToolCallValidation(BaseModel):
    is_valid: bool
    tool_name: str
    arguments: Dict[str, Any]
    violation_type: Optional[SecurityViolationType] = None
    violation_reason: Optional[str] = None
    sanitized_arguments: Optional[Dict[str, Any]] = None


class SecurityAuditEntry(BaseModel):
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    investigation_id: Optional[str] = None
    event_type: str
    action: str
    target_resource: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    blocked: bool = False
    warning_message: Optional[str] = None
