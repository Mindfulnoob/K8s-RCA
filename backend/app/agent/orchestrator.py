"""Autonomous Investigation Loop Orchestrator."""

import uuid
import copy
from typing import Optional, Dict, Any, List
from datetime import datetime

from backend.app.config import settings
from backend.app.models.state import (
    InvestigationState, InvestigationStep, ReplayFrame, Decision, InvestigationStatus
)
from backend.app.models.hypothesis import HypothesisStatus
from backend.app.hypotheses.engine import HypothesisEngine
from backend.app.reasoning.confidence import ConfidenceCalculator
from backend.app.reasoning.timeline import TimelineNormalizer
from backend.app.tools import create_tool_registry, ToolRegistry
from backend.app.security.sandbox import SecuritySandbox
from backend.app.agent.llm_provider import get_llm_provider, BaseLLMProvider


class InvestigationOrchestrator:
    """Manages the autonomous hypothesis-driven investigation lifecycle."""

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        sandbox: Optional[SecuritySandbox] = None,
    ):
        self.sandbox = sandbox or SecuritySandbox()
        self.tool_registry = tool_registry or create_tool_registry(sandbox=self.sandbox)
        self.llm_provider = llm_provider or get_llm_provider()

    def initialize_investigation(
        self,
        incident: str,
        namespace: str = "default",
        time_range: str = "last 30m",
        investigation_id: Optional[str] = None,
    ) -> InvestigationState:
        inv_id = investigation_id or f"inv-{uuid.uuid4().hex[:8]}"
        initial_hypotheses = HypothesisEngine.generate_initial_hypotheses(incident)

        state = InvestigationState(
            id=inv_id,
            incident=incident,
            namespace=namespace,
            time_range=time_range,
            status=InvestigationStatus.INVESTIGATING,
            start_time=datetime.utcnow(),
            hypotheses=initial_hypotheses,
            current_focus="Formulating candidate failure hypotheses and establishing cluster baseline.",
            confidence=15.0,
            confidence_explanation="Initial hypothesis candidates generated. Beginning multi-source queries."
        )

        # Record initial frame
        state.replay_frames.append(ReplayFrame(
            step_number=0,
            timestamp=datetime.utcnow(),
            phase="INITIALIZATION",
            active_hypotheses=[h.model_dump() for h in state.hypotheses],
            latest_evidence=None,
            current_thought=f"Incident received: '{incident}'. Formulated {len(initial_hypotheses)} competing hypotheses.",
            executed_query=None,
            confidence_at_step=state.confidence
        ))

        return state

    def run_step(self, state: InvestigationState) -> InvestigationStep:
        """Executes one dynamic step in the investigation loop."""
        step_number = len(state.steps) + 1

        # 1. Ask planner / LLM for next decision
        decision = self.llm_provider.plan_next_step(state, step_number)

        # 2. Check stopping condition
        if decision is None or step_number > settings.MAX_INVESTIGATION_STEPS:
            # Investigation finished - generate RCA
            state.rca_report = self.llm_provider.generate_rca(state)
            if state.rca_report.is_sufficient_evidence:
                state.status = InvestigationStatus.COMPLETED
            else:
                state.status = InvestigationStatus.INSUFFICIENT_EVIDENCE

            state.end_time = datetime.utcnow()
            state.confidence = state.rca_report.confidence_score
            state.confidence_explanation = state.rca_report.confidence_explanation
            state.current_focus = "Investigation completed. RCA report synthesized."

            completion_step = InvestigationStep(
                step_number=step_number,
                timestamp=datetime.utcnow(),
                status="COMPLETED",
                decision=decision,
                tool_name=None,
                tool_output_summary="Sufficient evidence acquired. Investigation concluded with RCA generation.",
                hypotheses_state=state.hypotheses,
                current_focus=state.current_focus,
                confidence_score=state.confidence
            )
            state.steps.append(completion_step)
            return completion_step

        # 3. Record decision
        state.decisions.append(decision)
        state.current_focus = f"Testing {decision.target_tool}: {decision.rationale}"
        query_sig = f"{decision.target_tool}:{json_safe_str(decision.arguments)}"
        state.queries_executed.append(decision.target_tool)

        # 4. Execute tool via capability-based sandbox
        tool_result = self.tool_registry.execute(decision.target_tool, decision.arguments)
        
        if tool_result.security_flagged and tool_result.security_note:
            state.security_audits.extend(self.sandbox.audit_log)

        # 5. Extract structured evidence
        evidence = self.llm_provider.extract_evidence(
            tool_name=decision.target_tool,
            arguments=decision.arguments,
            raw_output=tool_result.output,
            hypotheses=state.hypotheses,
            security_flagged=tool_result.security_flagged
        )
        state.evidence.append(evidence)
        state.observations.append(f"[{evidence.source}] {evidence.observation.summary}")

        # 6. Bayesian belief update across hypotheses
        belief_updates = HypothesisEngine.update_beliefs(state.hypotheses, evidence)

        # 7. Recalculate confidence & update timeline
        confidence, conf_expl = ConfidenceCalculator.calculate_confidence(state.hypotheses, state.evidence)
        state.confidence = confidence
        state.confidence_explanation = conf_expl
        state.timeline = TimelineNormalizer.build_timeline(state.evidence)

        # 8. Record step and replay frame
        step = InvestigationStep(
            step_number=step_number,
            timestamp=datetime.utcnow(),
            status="INVESTIGATING",
            decision=decision,
            tool_name=decision.target_tool,
            arguments=decision.arguments,
            tool_output_summary=evidence.observation.summary,
            evidence_collected=[evidence],
            belief_updates=belief_updates,
            hypotheses_state=copy.deepcopy(state.hypotheses),
            current_focus=state.current_focus,
            confidence_score=state.confidence
        )
        state.steps.append(step)

        state.replay_frames.append(ReplayFrame(
            step_number=step_number,
            timestamp=datetime.utcnow(),
            phase=decision.target_tool,
            active_hypotheses=[h.model_dump() for h in state.hypotheses],
            latest_evidence=evidence.model_dump(),
            current_thought=decision.rationale,
            executed_query=decision.chosen_action,
            confidence_at_step=confidence
        ))

        return step

    def run_full_investigation(
        self,
        incident: str,
        namespace: str = "default",
        max_steps: int = 10,
    ) -> InvestigationState:
        """Runs the complete investigation loop until stopping condition or max steps."""
        state = self.initialize_investigation(incident=incident, namespace=namespace)
        
        while state.status == InvestigationStatus.INVESTIGATING and len(state.steps) < max_steps:
            self.run_step(state)

        # Final check if loop exited without generating RCA
        if not state.rca_report:
            state.rca_report = self.llm_provider.generate_rca(state)
            state.status = InvestigationStatus.COMPLETED
            state.end_time = datetime.utcnow()

        return state


def json_safe_str(obj: Any) -> str:
    try:
        import json
        return json.dumps(obj, sort_keys=True)
    except Exception:
        return str(obj)
