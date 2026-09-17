"""Ground truth definitions for automated SRE investigation benchmarks."""

from typing import Dict, Any, List

GROUND_TRUTH_BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "oom": {
        "incident_prompt": "The checkout service is experiencing high 5xx error rate and container restarts.",
        "expected_root_cause_keywords": ["memory", "oomkilled", "limit", "exhaustion", "leak"],
        "expected_causal_nodes": ["Memory Leak", "Memory Limit", "OOMKilled", "503"],
        "required_sources": ["Kubernetes", "Prometheus", "Loki"],
        "expected_winning_hypothesis": "H-OOM",
        "forbidden_hypotheses": ["H-TRAFFIC", "H-NODE"],
        "max_acceptable_queries": 8
    },
    "bad_deployment": {
        "incident_prompt": "Payment service transactions are failing with 100% 500 Internal Server Error following release.",
        "expected_root_cause_keywords": ["release", "rollout", "deployment", "nullpointerexception", "v2.0.0"],
        "expected_causal_nodes": ["Defective Release", "Rollout", "NullPointerException", "500"],
        "required_sources": ["Kubernetes", "Logs", "Config"],
        "expected_winning_hypothesis": "H-DEPLOY",
        "forbidden_hypotheses": ["H-OOM", "H-NODE"],
        "max_acceptable_queries": 8
    },
    "dependency_failure": {
        "incident_prompt": "Checkout service experiencing cascading 504 Gateway Timeout errors.",
        "expected_root_cause_keywords": ["database", "outage", "postgres", "connection refused", "crashloop"],
        "expected_causal_nodes": ["Database Instance Crash", "Connection Refusal", "504", "502"],
        "required_sources": ["Kubernetes", "Logs", "Jaeger"],
        "expected_winning_hypothesis": "H-DEP",
        "forbidden_hypotheses": ["H-OOM", "H-DEPLOY"],
        "max_acceptable_queries": 8
    },
    "multi_source": {
        "incident_prompt": "The checkout service suddenly has a high 5xx error rate, probe failures, and restarts.",
        "expected_root_cause_keywords": ["database connection", "pool", "exhaustion", "leak", "saturation", "db_pool_max"],
        "expected_causal_nodes": ["Database Connection Leak", "Reduced Max Pool Size", "Saturation", "PoolAcquireTimeout", "Restarts"],
        "required_sources": ["Kubernetes", "Prometheus", "Loki", "Config"],
        "expected_winning_hypothesis": "H-DB",
        "forbidden_hypotheses": ["H-TRAFFIC", "H-NODE"],
        "max_acceptable_queries": 9
    }
}
