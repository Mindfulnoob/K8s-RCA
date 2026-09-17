"""LLM Provider Abstraction Layer (Mock, OpenAI, Gemini)."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import httpx

from backend.app.config import settings
from backend.app.models.state import Decision, InvestigationState
from backend.app.models.hypothesis import Hypothesis
from backend.app.models.evidence import Evidence, EvidenceType, Reliability, NormalizedObservation
from backend.app.models.rca import RCAReport
from backend.app.planner.planner import DynamicPlanner
from backend.app.reasoning.rca_generator import RCAGenerator
from backend.app.agent.prompts import SYSTEM_INVESTIGATION_PROMPT, DECISION_SCHEMA_PROMPT

logger = logging.getLogger("agent.llm")


class BaseLLMProvider(ABC):
    """Abstract interface for LLM-driven reasoning and decision making."""

    @abstractmethod
    def plan_next_step(
        self,
        state: InvestigationState,
        step_number: int,
    ) -> Optional[Decision]:
        pass

    @abstractmethod
    def extract_evidence(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        raw_output: Any,
        hypotheses: List[Hypothesis],
        security_flagged: bool = False,
    ) -> Evidence:
        pass

    @abstractmethod
    def generate_rca(self, state: InvestigationState) -> RCAReport:
        pass


class MockProvider(BaseLLMProvider):
    """Deterministic, high-fidelity investigation reasoning engine that runs without external API keys."""

    def plan_next_step(
        self,
        state: InvestigationState,
        step_number: int,
    ) -> Optional[Decision]:
        return DynamicPlanner.select_next_action(
            step_number=step_number,
            incident=state.incident,
            namespace=state.namespace,
            hypotheses=state.hypotheses,
            evidence_history=state.evidence,
            executed_queries=state.queries_executed
        )

    def extract_evidence(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        raw_output: Any,
        hypotheses: List[Hypothesis],
        security_flagged: bool = False,
    ) -> Evidence:
        ev_id = f"ev-{tool_name}-{datetime.utcnow().strftime('%H%M%S%f')[:10]}"
        source = "Kubernetes"
        if "prometheus" in tool_name:
            source = "Prometheus"
        elif "logs" in tool_name:
            source = "Loki"
        elif "trace" in tool_name:
            source = "Jaeger"
        elif "deployment" in tool_name or "config" in tool_name:
            source = "Config"

        summary = f"Observation gathered from {tool_name}"
        supports = []
        weakens = []
        evidence_type = EvidenceType.DIRECT
        reliability = Reliability.HIGH

        if tool_name == "k8s_list_pods":
            pods = raw_output if isinstance(raw_output, list) else []
            restarting = [p for p in pods if p.get("restarts", 0) > 0]
            unready = [p for p in pods if not p.get("ready", True)]
            if restarting:
                summary = f"Detected {len(restarting)} restarting pods: {', '.join(p['name'] for p in restarting)}."
                supports.extend(["H-OOM", "H-DB"])
            else:
                summary = f"Found {len(pods)} running pods; all healthy with 0 restarts."
                weakens.extend(["H-OOM", "H-NODE"])

        elif tool_name == "k8s_get_events":
            events = raw_output if isinstance(raw_output, list) else []
            oom_events = [e for e in events if "oom" in e.get("reason", "").lower() or "oom" in e.get("message", "").lower()]
            probe_events = [e for e in events if "unhealthy" in e.get("reason", "").lower() or "probe" in e.get("message", "").lower()]
            scaling_events = [e for e in events if "scalingreplicaset" in e.get("reason", "").lower() or "scaled" in e.get("message", "").lower()]
            
            if oom_events:
                summary = f"Discovered {len(oom_events)} OOMKilled container events: {oom_events[0].get('message')}."
                supports.append("H-OOM")
                weakens.extend(["H-DB", "H-DEPLOY", "H-TRAFFIC", "H-NODE"])
            elif scaling_events:
                summary = f"Kubernetes events confirm deployment rollout: {scaling_events[0].get('message')}."
                supports.append("H-DEPLOY")
            elif probe_events:
                summary = f"Kubernetes warning events show readiness probe failures: {probe_events[0].get('message')}."
                supports.extend(["H-DB", "H-DEPLOY"])

        elif tool_name == "deployment_history":
            history = raw_output if isinstance(raw_output, list) else []
            if len(history) > 1:
                latest = history[-1]
                summary = f"Deployment revision {latest.get('revision')} updated to image '{latest.get('image')}' at {latest.get('updated_at')}."
                supports.append("H-DEPLOY")
            else:
                summary = "Deployment revision history shows no recent rollouts in incident window."
                weakens.append("H-DEPLOY")

        elif tool_name == "config_change_history":
            changes = raw_output if isinstance(raw_output, list) else []
            if changes:
                summary = f"ConfigMap change detected: {changes[-1].get('key')} updated to '{changes[-1].get('value')}'."
                supports.extend(["H-CONFIG", "H-DB"])
                weakens.extend(["H-OOM", "H-NODE"])
            else:
                summary = "No recent ConfigMap or Secret changes detected."
                weakens.append("H-CONFIG")

        elif tool_name == "prometheus_query":
            q = arguments.get("query", "")
            val = "0"
            try:
                results = raw_output.get("data", {}).get("result", [])
                if results and len(results) > 0:
                    val = str(results[0].get("value", [0, "0"])[1])
            except Exception:
                pass

            if "connection" in q:
                if float(val) >= 8.0:
                    summary = f"Prometheus indicates database active connections reached {val}/10 capacity saturation limit."
                    supports.append("H-DB")
                    weakens.extend(["H-OOM", "H-TRAFFIC", "H-NODE"])
                else:
                    summary = f"Prometheus indicates database active connections normal ({val})."
                    weakens.append("H-DB")
            elif "memory" in q:
                if float(val) > 400000000:
                    summary = f"Prometheus memory metric shows steady ramp up ({int(float(val)/1024/1024)}MB) to limit prior to container termination."
                    supports.append("H-OOM")
                    weakens.extend(["H-DB", "H-TRAFFIC"])
                else:
                    summary = f"Prometheus memory usage normal ({val})."
                    weakens.append("H-OOM")
            else:
                summary = f"Metric query '{q}' returned value {val}."

        elif tool_name == "logs_query":
            logs = raw_output if isinstance(raw_output, list) else []
            err_logs = [l for l in logs if any(k in l.get("message", "").lower() for k in ["exception", "error", "oom", "hikari", "exhausted", "refused", "timeout"])]
            
            if any("hikari" in l.get("message", "").lower() or "connection pool" in l.get("message", "").lower() for l in err_logs):
                summary = "Logs reveal HikariCP PoolAcquireTimeoutException: connection pool exhausted (active=10, idle=0)."
                supports.extend(["H-DB", "H-CONFIG"])
                weakens.extend(["H-OOM", "H-NODE", "H-TRAFFIC"])
            elif any("nullpointerexception" in l.get("message", "").lower() for l in err_logs):
                summary = "Application logs show java.lang.NullPointerException in ChargeHandler during payment processing."
                supports.append("H-DEPLOY")
                weakens.extend(["H-OOM", "H-DB", "H-NODE", "H-TRAFFIC"])
            elif any("outofmemory" in l.get("message", "").lower() or "byte buffer" in l.get("message", "").lower() for l in err_logs):
                summary = "Application log shows java.lang.OutOfMemoryError in JVM heap."
                supports.append("H-OOM")
                weakens.extend(["H-DB", "H-DEPLOY", "H-TRAFFIC", "H-NODE"])
            elif any("connection refused" in l.get("message", "").lower() for l in err_logs):
                summary = "Logs reveal psycopg2.OperationalError: could not connect to server: Connection refused on port 5432."
                supports.extend(["H-DEP", "H-DB"])
                weakens.extend(["H-OOM", "H-DEPLOY", "H-TRAFFIC"])
            else:
                summary = f"Application logs queried ({len(logs)} entries retrieved)."

        elif tool_name == "traces_query":
            traces = raw_output if isinstance(raw_output, list) else []
            err_traces = [t for t in traces if t.get("error")]
            if err_traces:
                op = str(err_traces[0].get("operation", "")).lower()
                if "hikaricp" in op or "db" in op or "database" in op:
                    summary = f"Distributed trace shows HikariCP database pool acquire failure ({err_traces[0].get('duration_ms')}ms) returning 503."
                    supports.append("H-DB")
                else:
                    summary = f"Distributed trace shows HTTP {err_traces[0].get('status')} error in {err_traces[0].get('service')} during {err_traces[0].get('operation')} ({err_traces[0].get('duration_ms')}ms)."
                    supports.append("H-DEP")
            else:
                summary = "Trace waterfall indicates normal service-to-service RPC latency."

        return Evidence(
            id=ev_id,
            source=source,
            timestamp=datetime.utcnow(),
            query=f"{tool_name}({arguments})",
            raw_data=raw_output if isinstance(raw_output, (dict, list)) else {"output": raw_output},
            observation=NormalizedObservation(
                summary=summary,
                anomaly_detected=len(supports) > 0,
                details={"tool": tool_name, "args": arguments}
            ),
            related_hypotheses=[h.id for h in hypotheses],
            supports_hypotheses=supports,
            weakens_hypotheses=weakens,
            evidence_type=evidence_type,
            reliability=reliability,
            source_component=arguments.get("pod_name") or arguments.get("name") or arguments.get("service_name"),
            security_flagged=security_flagged,
            security_note="Untrusted data scanned and isolated" if security_flagged else None
        )

    def generate_rca(self, state: InvestigationState) -> RCAReport:
        return RCAGenerator.generate_report(
            investigation_id=state.id,
            incident=state.incident,
            hypotheses=state.hypotheses,
            evidence_list=state.evidence
        )


class OpenAIProvider(BaseLLMProvider):
    """Integrates OpenAI GPT-4o with tool calling and fallback to MockProvider."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.fallback = MockProvider()

    def plan_next_step(self, state: InvestigationState, step_number: int) -> Optional[Decision]:
        if not self.api_key:
            return self.fallback.plan_next_step(state, step_number)
        
        try:
            evidence_summary = "\n".join([f"- [{e.source}] {e.observation.summary}" for e in state.evidence])
            hypo_summary = "\n".join([f"- {h.id} ({h.category}): score={h.current_score:.2f} [{h.status}]" for h in state.hypotheses])
            
            messages = [
                {"role": "system", "content": SYSTEM_INVESTIGATION_PROMPT},
                {"role": "user", "content": f"Incident: {state.incident}\nEvidence collected:\n{evidence_summary}\nHypotheses:\n{hypo_summary}\n\n{DECISION_SCHEMA_PROMPT}"}
            ]

            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }

            resp = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=20.0)
            if resp.status_code == 200:
                data = resp.json()
                content = json.loads(data["choices"][0]["message"]["content"])
                if content.get("target_tool") in DynamicPlanner.TOOL_COSTS:
                    return Decision(
                        step_number=step_number,
                        rationale=content.get("rationale", "LLM reasoning"),
                        chosen_action=content.get("chosen_action", "Execute query"),
                        target_tool=content.get("target_tool"),
                        arguments=content.get("arguments", {}),
                        expected_information_gain=content.get("expected_information_gain", "Information gain")
                    )
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}. Falling back to deterministic planner.")

        return self.fallback.plan_next_step(state, step_number)

    def extract_evidence(self, tool_name: str, arguments: Dict[str, Any], raw_output: Any, hypotheses: List[Hypothesis], security_flagged: bool = False) -> Evidence:
        return self.fallback.extract_evidence(tool_name, arguments, raw_output, hypotheses, security_flagged)

    def generate_rca(self, state: InvestigationState) -> RCAReport:
        return self.fallback.generate_rca(state)


class GeminiProvider(BaseLLMProvider):
    """Integrates Google Gemini with fallback to MockProvider."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.fallback = MockProvider()

    def plan_next_step(self, state: InvestigationState, step_number: int) -> Optional[Decision]:
        if not self.api_key:
            return self.fallback.plan_next_step(state, step_number)
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            prompt = f"{SYSTEM_INVESTIGATION_PROMPT}\nIncident: {state.incident}\nEvidence count: {len(state.evidence)}\n{DECISION_SCHEMA_PROMPT}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            resp = httpx.post(url, json=payload, timeout=20.0)
            if resp.status_code == 200:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                content = json.loads(text)
                if content.get("target_tool") in DynamicPlanner.TOOL_COSTS:
                    return Decision(
                        step_number=step_number,
                        rationale=content.get("rationale", "Gemini reasoning"),
                        chosen_action=content.get("chosen_action", "Execute query"),
                        target_tool=content.get("target_tool"),
                        arguments=content.get("arguments", {}),
                        expected_information_gain=content.get("expected_information_gain", "Information gain")
                    )
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}. Falling back to deterministic planner.")

        return self.fallback.plan_next_step(state, step_number)

    def extract_evidence(self, tool_name: str, arguments: Dict[str, Any], raw_output: Any, hypotheses: List[Hypothesis], security_flagged: bool = False) -> Evidence:
        return self.fallback.extract_evidence(tool_name, arguments, raw_output, hypotheses, security_flagged)

    def generate_rca(self, state: InvestigationState) -> RCAReport:
        return self.fallback.generate_rca(state)


def get_llm_provider(provider_type: Optional[str] = None) -> BaseLLMProvider:
    choice = (provider_type or settings.LLM_PROVIDER).lower()
    if choice == "openai":
        return OpenAIProvider()
    elif choice == "gemini":
        return GeminiProvider()
    return MockProvider()
