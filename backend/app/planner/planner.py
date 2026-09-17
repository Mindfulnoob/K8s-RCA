"""Dynamic Information-Gain Investigation Planner."""

import math
from typing import Dict, Any, List, Optional, Set
from backend.app.models.hypothesis import Hypothesis, HypothesisStatus
from backend.app.models.evidence import Evidence
from backend.app.models.state import Decision


class DynamicPlanner:
    """Plans the next optimal observability investigation step to maximize information gain."""

    TOOL_COSTS: Dict[str, float] = {
        "k8s_list_pods": 1.0,
        "k8s_get_pod": 1.0,
        "k8s_get_events": 1.2,
        "k8s_get_restarts": 1.0,
        "k8s_get_deployment": 1.1,
        "deployment_history": 1.5,
        "config_change_history": 1.5,
        "prometheus_query": 2.0,
        "prometheus_range_query": 2.5,
        "logs_query": 2.2,
        "logs_query_previous_container": 2.4,
        "traces_query": 3.0,
        "dependency_graph": 1.2,
    }

    @classmethod
    def calculate_entropy(cls, hypotheses: List[Hypothesis]) -> float:
        """Computes Shannon entropy (uncertainty) of current belief distribution."""
        entropy = 0.0
        for h in hypotheses:
            p = max(h.current_score, 1e-6)
            entropy -= p * math.log2(p)
        return entropy

    @classmethod
    def select_next_action(
        cls,
        step_number: int,
        incident: str,
        namespace: str,
        hypotheses: List[Hypothesis],
        evidence_history: List[Evidence],
        executed_queries: List[str],
    ) -> Optional[Decision]:
        """Selects the highest-utility investigation action while avoiding redundant queries."""
        # 1. Check if sufficient evidence or confidence is already reached
        leading_hypothesis = max(hypotheses, key=lambda h: h.current_score, default=None)
        if leading_hypothesis and leading_hypothesis.current_score >= 0.88 and len(evidence_history) >= 4:
            sources = {e.source for e in evidence_history}
            if len(sources) >= 2:
                return None  # Sufficient evidence reached!

        # 2. Extract services mentioned or default
        target_service = "checkout"
        for candidate in ["payment", "checkout", "frontend", "database"]:
            if candidate in incident.lower():
                target_service = candidate
                break

        # 3. Identify which observability sources have been queried
        sources_queried = {e.source for e in evidence_history}
        executed_set = set(executed_queries)

        # 4. Generate candidate queries based on current hypothesis ranking
        candidate_actions: List[Dict[str, Any]] = []

        # Step 1: Baseline inspection if not done
        if "k8s_list_pods" not in executed_set:
            candidate_actions.append({
                "tool": "k8s_list_pods",
                "args": {"namespace": namespace},
                "rationale": "Enumerate pods, readiness status, and restart counts across the namespace to establish baseline health.",
                "gain": 5.5,
                "target_h": "ALL"
            })

        # Step 2: Events check if not done
        if "k8s_get_events" not in executed_set:
            candidate_actions.append({
                "tool": "k8s_get_events",
                "args": {"namespace": namespace, "limit": 30},
                "rationale": "Query Kubernetes warning events to detect OOMKilled, probe failures, or container restarts.",
                "gain": 4.8,
                "target_h": "H-OOM, H-DEPLOY"
            })

        # Step 3: Deployment history check
        if "deployment_history" not in executed_set:
            candidate_actions.append({
                "tool": "deployment_history",
                "args": {"name": f"{target_service}-service", "namespace": namespace},
                "rationale": f"Inspect revision history for {target_service}-service to verify if a new release triggered the issue.",
                "gain": 3.8,
                "target_h": "H-DEPLOY"
            })

        # Step 4: Application error logs
        log_query_key = f"logs_query:{target_service}"
        if log_query_key not in executed_set and "logs_query" not in executed_set:
            candidate_actions.append({
                "tool": "logs_query",
                "args": {"query": f'{{app="{target_service}"}} |= "error"', "limit": 30},
                "rationale": f"Query application logs for {target_service} to capture stack traces, exception classes, and error root causes.",
                "gain": 4.0,
                "target_h": "H-DEPLOY, H-DB"
            })

        # Step 5: Prometheus metrics inspection
        prom_conn_key = "prometheus_query:db_conn"
        if prom_conn_key not in executed_set and "prometheus_query" not in executed_set:
            candidate_actions.append({
                "tool": "prometheus_query",
                "args": {"query": f'{target_service}_db_active_connections'},
                "rationale": f"Check Prometheus active database connections for {target_service} to test connection saturation hypothesis.",
                "gain": 3.7,
                "target_h": "H-DB"
            })

        prom_mem_key = "prometheus_query:mem"
        if prom_mem_key not in executed_set:
            candidate_actions.append({
                "tool": "prometheus_query",
                "args": {"query": f'container_memory_working_set_bytes{{pod=~"{target_service}.*"}}'},
                "rationale": f"Inspect container memory working set bytes to verify whether limits were exceeded.",
                "gain": 3.6,
                "target_h": "H-OOM"
            })

        # Step 6: Config change history
        config_key = "config_change_history"
        if config_key not in executed_set:
            candidate_actions.append({
                "tool": "config_change_history",
                "args": {"name": f"{target_service}-config", "namespace": namespace},
                "rationale": f"Check ConfigMap and environment modifications for {target_service} around the incident window.",
                "gain": 3.2,
                "target_h": "H-CONFIG"
            })

        # Step 7: Distributed Traces
        trace_key = f"traces_query:{target_service}"
        if trace_key not in executed_set and "traces_query" not in executed_set:
            candidate_actions.append({
                "tool": "traces_query",
                "args": {"service_name": target_service, "limit": 10},
                "rationale": f"Inspect Jaeger trace waterfalls to localize RPC latency and pinpoint failing downstream dependencies.",
                "gain": 3.4,
                "target_h": "H-DEP"
            })

        # Step 8: Previous container logs if restarts occurred
        prev_log_key = "logs_query_previous_container"
        if prev_log_key not in executed_set and any(e.source == "Kubernetes" and "restart" in e.observation.summary.lower() for e in evidence_history):
            candidate_actions.append({
                "tool": "logs_query_previous_container",
                "args": {"pod_name": f"{target_service}-service", "namespace": namespace},
                "rationale": "Extract termination log of the previously crashed container to retrieve panic message before restart.",
                "gain": 3.9,
                "target_h": "H-OOM, H-DEPLOY"
            })

        if not candidate_actions:
            return None

        # 5. Score candidates by information gain minus cost, with a bonus for unrepresented sources
        scored_candidates = []
        for cand in candidate_actions:
            tool_name = cand["tool"]
            cost = cls.TOOL_COSTS.get(tool_name, 1.0)
            gain = cand["gain"]

            # Multi-source bonus for unqueried sources
            if "k8s" in tool_name and "Kubernetes" not in sources_queried:
                gain += 2.0
            if "prometheus" in tool_name and "Prometheus" not in sources_queried:
                gain += 2.0
            if "logs" in tool_name and "Loki" not in sources_queried:
                gain += 2.0
            if "trace" in tool_name and "Jaeger" not in sources_queried:
                gain += 1.5

            net_utility = gain / (1.0 + 0.2 * cost)
            scored_candidates.append((net_utility, cand))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        best_gain, best_cand = scored_candidates[0]

        return Decision(
            step_number=step_number,
            rationale=best_cand["rationale"],
            chosen_action=f"Execute {best_cand['tool']} to evaluate {best_cand['target_h']}",
            target_tool=best_cand["tool"],
            arguments=best_cand["args"],
            expected_information_gain=f"Estimated utility {best_gain:.2f} targeting {best_cand['target_h']}"
        )
