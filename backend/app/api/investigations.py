"""Investigation API endpoints."""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from backend.app.models.state import InvestigationState, InvestigationStep, ReplayFrame
from backend.app.models.hypothesis import Hypothesis
from backend.app.models.evidence import Evidence
from backend.app.models.timeline import TimelineEvent
from backend.app.models.rca import RCAReport
from backend.app.agent.orchestrator import InvestigationOrchestrator
from backend.app.agent.llm_provider import get_llm_provider
from backend.app.storage.db import InvestigationStore

router = APIRouter(prefix="/investigations", tags=["investigations"])


class StartInvestigationRequest(BaseModel):
    incident: str = Field(description="Incident description or alert summary")
    namespace: str = Field(default="default", description="Kubernetes namespace")
    time_range: str = Field(default="last 30m", description="Time window for analysis")
    provider_type: Optional[str] = Field(default="mock", description="LLM provider: mock, openai, gemini")
    max_steps: int = Field(default=8, ge=2, le=15)
    run_to_completion: bool = Field(default=True, description="Whether to execute until RCA or step manually")


@router.post("", response_model=InvestigationState)
def start_investigation(req: StartInvestigationRequest):
    """Starts a new autonomous investigation."""
    provider = get_llm_provider(req.provider_type)
    orchestrator = InvestigationOrchestrator(llm_provider=provider)
    
    if req.run_to_completion:
        state = orchestrator.run_full_investigation(
            incident=req.incident,
            namespace=req.namespace,
            max_steps=req.max_steps
        )
    else:
        state = orchestrator.initialize_investigation(
            incident=req.incident,
            namespace=req.namespace,
            time_range=req.time_range
        )

    InvestigationStore.save(state)
    return state


@router.get("", response_model=List[Dict[str, Any]])
def list_investigations():
    """Lists all stored investigations."""
    return InvestigationStore.list_all()


@router.get("/{investigation_id}", response_model=InvestigationState)
def get_investigation(investigation_id: str):
    """Retrieves full investigation state."""
    state = InvestigationStore.get(investigation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return state


@router.post("/{investigation_id}/step", response_model=InvestigationStep)
def step_investigation(investigation_id: str):
    """Executes a single step in an ongoing investigation."""
    state = InvestigationStore.get(investigation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Investigation not found")

    orchestrator = InvestigationOrchestrator()
    step = orchestrator.run_step(state)
    InvestigationStore.save(state)
    return step


@router.get("/{investigation_id}/timeline", response_model=List[TimelineEvent])
def get_timeline(investigation_id: str):
    """Gets the normalized chronological incident timeline."""
    state = InvestigationStore.get(investigation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return state.timeline


@router.get("/{investigation_id}/hypotheses", response_model=List[Hypothesis])
def get_hypotheses(investigation_id: str):
    """Gets current belief states and evidence mappings for all hypotheses."""
    state = InvestigationStore.get(investigation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return state.hypotheses


@router.get("/{investigation_id}/evidence", response_model=List[Evidence])
def get_evidence(investigation_id: str):
    """Gets all collected multi-source evidence items."""
    state = InvestigationStore.get(investigation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return state.evidence


@router.get("/{investigation_id}/replay", response_model=List[ReplayFrame])
def get_replay(investigation_id: str):
    """Gets step-by-step investigation replay frames."""
    state = InvestigationStore.get(investigation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return state.replay_frames


@router.get("/{investigation_id}/report", response_model=RCAReport)
def get_report(investigation_id: str):
    """Gets the synthesized Root Cause Analysis report."""
    state = InvestigationStore.get(investigation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Investigation not found")
    if not state.rca_report:
        orchestrator = InvestigationOrchestrator()
        state.rca_report = orchestrator.llm_provider.generate_rca(state)
        InvestigationStore.save(state)
    return state.rca_report
