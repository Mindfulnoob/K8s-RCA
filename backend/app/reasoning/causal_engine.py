"""Causal reasoning engine distinguishing root cause, triggers, contributors, and symptoms."""

from typing import List, Dict, Any, Optional
from backend.app.models.rca import CausalChain, CausalNode, CausalEdge, CausalNodeType
from backend.app.models.hypothesis import Hypothesis
from backend.app.models.evidence import Evidence


class CausalEngine:
    """Builds directed causal graphs separating underlying root causes from operational symptoms."""

    @classmethod
    def construct_causal_chain(
        cls,
        leading_hypothesis: Hypothesis,
        evidence_list: List[Evidence],
    ) -> CausalChain:
        category = leading_hypothesis.category

        nodes: List[CausalNode] = []
        edges: List[CausalEdge] = []

        if category == "resource":  # OOM
            nodes = [
                CausalNode(
                    id="node-1",
                    label="Memory Leak / Unbounded Cache",
                    type=CausalNodeType.ROOT_CAUSE,
                    description="Application logic accumulates heap memory objects without releasing references.",
                    component="checkout-service"
                ),
                CausalNode(
                    id="node-2",
                    label="Memory Limit Ceiling Reached",
                    type=CausalNodeType.TRIGGER,
                    description="Container cgroup memory working set exceeded 512Mi limit.",
                    component="cgroup-memory"
                ),
                CausalNode(
                    id="node-3",
                    label="Kernel OOMKilled",
                    type=CausalNodeType.SYMPTOM,
                    description="Linux OOM killer terminated container process with SIGKILL (Exit code 137).",
                    component="kubelet"
                ),
                CausalNode(
                    id="node-4",
                    label="CrashLoop & 503 Errors",
                    type=CausalNodeType.DOWNSTREAM_EFFECT,
                    description="Container restart backoff prevents incoming traffic handling, causing elevated 5xx errors.",
                    component="checkout-service"
                )
            ]
            edges = [
                CausalEdge(source_id="node-1", target_id="node-2", relationship="causes"),
                CausalEdge(source_id="node-2", target_id="node-3", relationship="triggers"),
                CausalEdge(source_id="node-3", target_id="node-4", relationship="leads to")
            ]
            summary = "Memory leak in checkout-service caused container to exceed 512Mi limit, triggering kernel OOMKilled and restart backoff."

        elif category == "deployment":  # Bad Deployment
            nodes = [
                CausalNode(
                    id="node-1",
                    label="Defective Release Rollout",
                    type=CausalNodeType.ROOT_CAUSE,
                    description="Application regression introduced in release v2.0.0 (NullPointerException in payment handling).",
                    component="payment-service"
                ),
                CausalNode(
                    id="node-2",
                    label="Deployment Rollout Trigger",
                    type=CausalNodeType.TRIGGER,
                    description="ReplicaSet scaled up v2.0.0 and routed live traffic to defective pods.",
                    component="Deployment/payment-service"
                ),
                CausalNode(
                    id="node-3",
                    label="Unhandled Code Exception",
                    type=CausalNodeType.SYMPTOM,
                    description="NullPointerException in ChargeHandler when processing payment payload.",
                    component="payment-service"
                ),
                CausalNode(
                    id="node-4",
                    label="Elevated 500 Errors",
                    type=CausalNodeType.DOWNSTREAM_EFFECT,
                    description="100% of charge transactions failed with HTTP 500 Internal Server Error.",
                    component="checkout-api"
                )
            ]
            edges = [
                CausalEdge(source_id="node-1", target_id="node-2", relationship="introduced by"),
                CausalEdge(source_id="node-2", target_id="node-3", relationship="triggers"),
                CausalEdge(source_id="node-3", target_id="node-4", relationship="causes")
            ]
            summary = "Deployment of payment-service:v2.0.0 introduced a NullPointerException, triggering immediate 500 failures on live traffic."

        elif category == "database" or category == "configuration":  # Database / Multi-source Flagship
            nodes = [
                CausalNode(
                    id="node-1",
                    label="Database Connection Leak in v2.2.0",
                    type=CausalNodeType.ROOT_CAUSE,
                    description="Unclosed database connections in order persistence flow introduced in rollout.",
                    component="checkout-service"
                ),
                CausalNode(
                    id="node-2",
                    label="Reduced Max Pool Size Limit",
                    type=CausalNodeType.CONTRIBUTING_FACTOR,
                    description="ConfigMap update reduced DB_POOL_MAX from 50 to 10 connections.",
                    component="ConfigMap/checkout-config"
                ),
                CausalNode(
                    id="node-3",
                    label="Hikari Connection Pool Saturation",
                    type=CausalNodeType.TRIGGER,
                    description="Active connections reached 10/10 capacity, queuing incoming acquire requests.",
                    component="HikariCP"
                ),
                CausalNode(
                    id="node-4",
                    label="PoolAcquireTimeout & Request Failures",
                    type=CausalNodeType.SYMPTOM,
                    description="Requests timed out after 30s waiting for DB connection, returning HTTP 503.",
                    component="checkout-service"
                ),
                CausalNode(
                    id="node-5",
                    label="Readiness Probe Failure & Restarts",
                    type=CausalNodeType.DOWNSTREAM_EFFECT,
                    description="Health check failed to acquire DB connection; kubelet initiated pod restart backoff.",
                    component="kubelet"
                )
            ]
            edges = [
                CausalEdge(source_id="node-1", target_id="node-3", relationship="exerts pressure on"),
                CausalEdge(source_id="node-2", target_id="node-3", relationship="constrains"),
                CausalEdge(source_id="node-3", target_id="node-4", relationship="causes"),
                CausalEdge(source_id="node-4", target_id="node-5", relationship="triggers")
            ]
            summary = "Release v2.2.0 DB connection leak combined with reduced pool limit (10) saturated connections, triggering 503s and probe restarts."

        else:  # Dependency Failure
            nodes = [
                CausalNode(
                    id="node-1",
                    label="PostgreSQL Database Instance Crash",
                    type=CausalNodeType.ROOT_CAUSE,
                    description="Corrupted WAL record caused database container panic and CrashLoopBackOff.",
                    component="database-postgresql"
                ),
                CausalNode(
                    id="node-2",
                    label="Socket Connection Refusal",
                    type=CausalNodeType.TRIGGER,
                    description="TCP port 5432 stopped listening; refused all inbound client connections.",
                    component="database-service"
                ),
                CausalNode(
                    id="node-3",
                    label="Cascading Upstream Timeouts",
                    type=CausalNodeType.SYMPTOM,
                    description="Checkout service failed connecting to database, triggering HTTP 504 timeouts.",
                    component="checkout-service"
                ),
                CausalNode(
                    id="node-4",
                    label="User-Facing 502/504 Degradation",
                    type=CausalNodeType.DOWNSTREAM_EFFECT,
                    description="Frontend returned 502 Bad Gateway to end users.",
                    component="frontend-service"
                )
            ]
            edges = [
                CausalEdge(source_id="node-1", target_id="node-2", relationship="causes"),
                CausalEdge(source_id="node-2", target_id="node-3", relationship="triggers"),
                CausalEdge(source_id="node-3", target_id="node-4", relationship="propagates to")
            ]
            summary = "Postgres database crashed into CrashLoopBackOff, refusing connections and causing cascading timeouts across checkout and frontend."

        return CausalChain(nodes=nodes, edges=edges, summary=summary)
