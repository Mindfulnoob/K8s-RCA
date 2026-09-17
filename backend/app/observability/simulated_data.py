"""High-fidelity simulated cluster and observability state for reproducible incident scenarios."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class ScenarioCatalog:
    """Manages multi-source data for the 4 reproducible incidents."""

    @staticmethod
    def get_oom_scenario(base_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Scenario 1: Checkout service memory leak -> OOMKilled -> pod restarts -> 5xx errors."""
        now = base_time or datetime.utcnow()
        t_oom = now - timedelta(minutes=5)
        t_restart = now - timedelta(minutes=4)
        t_alert = now - timedelta(minutes=2)

        return {
            "id": "oom",
            "name": "Checkout Memory Leak & OOMKilled",
            "ground_truth": {
                "root_cause": "Container memory exhaustion caused by unconstrained memory leak in checkout-service, exceeding 512Mi limit and triggering kernel OOMKilled.",
                "trigger": "Unbounded cache growth in request handler under moderate load.",
                "symptoms": ["Pod restarts with exit code 137 (OOMKilled)", "Elevated 503 Service Unavailable errors during pod restart cycles", "Readiness probe failures"],
                "required_sources": ["Kubernetes", "Prometheus"]
            },
            "pods": [
                {
                    "name": "checkout-service-67b8d9f4c-x98qz",
                    "namespace": "default",
                    "status": "Running",
                    "ready": False,
                    "restarts": 4,
                    "image": "myregistry.local/checkout:v1.3.4",
                    "resources": {
                        "limits": {"memory": "512Mi", "cpu": "500m"},
                        "requests": {"memory": "256Mi", "cpu": "100m"}
                    },
                    "last_state": {
                        "terminated": {
                            "exit_code": 137,
                            "reason": "OOMKilled",
                            "finished_at": t_oom.isoformat()
                        }
                    },
                    "node": "worker-node-1"
                },
                {
                    "name": "frontend-service-589f8dc58-ab123",
                    "namespace": "default",
                    "status": "Running",
                    "ready": True,
                    "restarts": 0,
                    "image": "myregistry.local/frontend:v1.1.0",
                    "resources": {"limits": {"memory": "256Mi"}},
                    "node": "worker-node-1"
                },
                {
                    "name": "database-postgresql-0",
                    "namespace": "default",
                    "status": "Running",
                    "ready": True,
                    "restarts": 0,
                    "image": "postgres:15-alpine",
                    "resources": {"limits": {"memory": "1Gi"}},
                    "node": "worker-node-2"
                }
            ],
            "deployments": [
                {
                    "name": "checkout-service",
                    "namespace": "default",
                    "replicas": 1,
                    "ready_replicas": 0,
                    "image": "myregistry.local/checkout:v1.3.4",
                    "last_update": (now - timedelta(days=2)).isoformat(),
                    "revision": 1
                }
            ],
            "events": [
                {
                    "timestamp": t_oom.isoformat(),
                    "type": "Warning",
                    "reason": "OOMKilled",
                    "object": "Pod/checkout-service-67b8d9f4c-x98qz",
                    "message": "Pod was terminated due to memory limit exceeding 512Mi (Out of Memory)."
                },
                {
                    "timestamp": t_restart.isoformat(),
                    "type": "Warning",
                    "reason": "BackOff",
                    "object": "Pod/checkout-service-67b8d9f4c-x98qz",
                    "message": "Back-off restarting failed container checkout in pod checkout-service-67b8d9f4c-x98qz"
                },
                {
                    "timestamp": t_alert.isoformat(),
                    "type": "Warning",
                    "reason": "Unhealthy",
                    "object": "Pod/checkout-service-67b8d9f4c-x98qz",
                    "message": "Readiness probe failed: HTTP probe failed with statuscode: 503"
                }
            ],
            "metrics": {
                'container_memory_working_set_bytes{pod=~"checkout.*"}': [
                    {"time": (now - timedelta(minutes=15)).isoformat(), "value": "210000000"},
                    {"time": (now - timedelta(minutes=10)).isoformat(), "value": "360000000"},
                    {"time": (now - timedelta(minutes=6)).isoformat(), "value": "510000000"},
                    {"time": (now - timedelta(minutes=5)).isoformat(), "value": "536870912"},
                    {"time": now.isoformat(), "value": "180000000"}
                ],
                'http_requests_total{status=~"5.*",service="checkout"}': [
                    {"time": (now - timedelta(minutes=15)).isoformat(), "value": "0"},
                    {"time": (now - timedelta(minutes=5)).isoformat(), "value": "42"},
                    {"time": now.isoformat(), "value": "128"}
                ],
                'container_cpu_usage_seconds_total{pod=~"checkout.*"}': [
                    {"time": now.isoformat(), "value": "0.18"}
                ]
            },
            "logs": [
                {"timestamp": (t_oom - timedelta(seconds=20)).isoformat(), "level": "WARN", "message": "Memory heap utilization reached 92% (471MB/512MB)"},
                {"timestamp": (t_oom - timedelta(seconds=5)).isoformat(), "level": "ERROR", "message": "java.lang.OutOfMemoryError: Java heap space - failed to allocate byte buffer"},
                {"timestamp": t_oom.isoformat(), "level": "FATAL", "message": "Process terminated by SIGKILL (Exit code 137)"},
                {"timestamp": (now - timedelta(minutes=1)).isoformat(), "level": "INFO", "message": "Starting checkout service v1.3.4 on port 8080"}
            ],
            "traces": [
                {"trace_id": "tr-oom-01", "service": "checkout", "operation": "POST /checkout", "duration_ms": 5000, "status": 503, "error": True}
            ],
            "dependencies": {
                "nodes": ["frontend", "checkout", "database"],
                "edges": [{"source": "frontend", "target": "checkout"}, {"source": "checkout", "target": "database"}]
            },
            "deployment_history": [
                {"revision": 1, "image": "myregistry.local/checkout:v1.3.4", "updated_at": (now - timedelta(days=2)).isoformat(), "author": "devops"}
            ],
            "config_changes": []
        }

    @staticmethod
    def get_bad_deployment_scenario(base_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Scenario 2: Bad Deployment -> checkout-service:v2.0.0 crashes with NullPointerException on /checkout."""
        now = base_time or datetime.utcnow()
        t_deploy = now - timedelta(minutes=12)
        t_err_start = now - timedelta(minutes=11)

        return {
            "id": "bad_deployment",
            "name": "Faulty Release Rollout (v2.0.0)",
            "ground_truth": {
                "root_cause": "Application regression introduced in release v2.0.0 of payment-service: unhandled NullPointerException in ChargeHandler during payment processing.",
                "trigger": "Deployment rollout of payment-service to image version v2.0.0.",
                "symptoms": ["100% 500 Internal Server Error rate on /charge endpoint immediately following rollout", "Clean pod readiness but application-level fatal exceptions in container logs", "Replicas from v1.0.0 were unaffected"],
                "required_sources": ["Kubernetes", "Logs", "Prometheus"]
            },
            "pods": [
                {
                    "name": "payment-service-8647cbf89-4wkl9",
                    "namespace": "default",
                    "status": "Running",
                    "ready": True,
                    "restarts": 0,
                    "image": "myregistry.local/payment:v2.0.0",
                    "resources": {"limits": {"memory": "512Mi", "cpu": "500m"}},
                    "node": "worker-node-1"
                },
                {
                    "name": "checkout-service-568b9cf99-78zlk",
                    "namespace": "default",
                    "status": "Running",
                    "ready": True,
                    "restarts": 0,
                    "image": "myregistry.local/checkout:v1.4.0",
                    "resources": {"limits": {"memory": "512Mi"}},
                    "node": "worker-node-2"
                }
            ],
            "deployments": [
                {
                    "name": "payment-service",
                    "namespace": "default",
                    "replicas": 1,
                    "ready_replicas": 1,
                    "image": "myregistry.local/payment:v2.0.0",
                    "last_update": t_deploy.isoformat(),
                    "revision": 2
                }
            ],
            "events": [
                {
                    "timestamp": t_deploy.isoformat(),
                    "type": "Normal",
                    "reason": "ScalingReplicaSet",
                    "object": "Deployment/payment-service",
                    "message": "Scaled up replica set payment-service-8647cbf89 to 1"
                },
                {
                    "timestamp": (t_deploy + timedelta(seconds=15)).isoformat(),
                    "type": "Normal",
                    "reason": "ScalingReplicaSet",
                    "object": "Deployment/payment-service",
                    "message": "Scaled down replica set payment-service-75db7fc6b from 1 to 0"
                }
            ],
            "metrics": {
                'http_requests_total{status=~"5.*",service="payment"}': [
                    {"time": (t_deploy - timedelta(minutes=5)).isoformat(), "value": "0"},
                    {"time": t_err_start.isoformat(), "value": "8"},
                    {"time": now.isoformat(), "value": "342"}
                ],
                'http_requests_total{status="200",service="payment"}': [
                    {"time": (t_deploy - timedelta(minutes=5)).isoformat(), "value": "120"},
                    {"time": t_err_start.isoformat(), "value": "2"},
                    {"time": now.isoformat(), "value": "0"}
                ]
            },
            "logs": [
                {"timestamp": (t_deploy + timedelta(seconds=20)).isoformat(), "level": "INFO", "message": "payment-service v2.0.0 initialized successfully on port 8082"},
                {"timestamp": t_err_start.isoformat(), "level": "ERROR", "message": "Exception in thread 'http-nio-8082-exec-1' java.lang.NullPointerException: Cannot invoke 'String.trim()' because 'request.currency' is null"},
                {"timestamp": (t_err_start + timedelta(seconds=2)).isoformat(), "level": "ERROR", "message": "\tat com.payment.service.ChargeHandler.process(ChargeHandler.java:48)"},
                {"timestamp": (now - timedelta(minutes=3)).isoformat(), "level": "ERROR", "message": "Handler dispatch failed; nested exception is java.lang.NullPointerException: currency missing"}
            ],
            "traces": [
                {"trace_id": "tr-bad-deploy-1", "service": "payment", "operation": "POST /charge", "duration_ms": 14, "status": 500, "error": True, "error_message": "java.lang.NullPointerException"}
            ],
            "dependencies": {
                "nodes": ["frontend", "checkout", "payment"],
                "edges": [{"source": "frontend", "target": "checkout"}, {"source": "checkout", "target": "payment"}]
            },
            "deployment_history": [
                {"revision": 1, "image": "myregistry.local/payment:v1.0.0", "updated_at": (now - timedelta(days=5)).isoformat(), "author": "alice"},
                {"revision": 2, "image": "myregistry.local/payment:v2.0.0", "updated_at": t_deploy.isoformat(), "author": "ci-cd-bot"}
            ],
            "config_changes": []
        }

    @staticmethod
    def get_dependency_failure_scenario(base_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Scenario 3: Database pod connection refused / crash -> checkout cascading timeouts."""
        now = base_time or datetime.utcnow()
        t_crash = now - timedelta(minutes=15)
        t_fail = now - timedelta(minutes=14)

        return {
            "id": "dependency_failure",
            "name": "Postgres Database Outage & Cascading Timeouts",
            "ground_truth": {
                "root_cause": "Downstream PostgreSQL database instance crashed and entered CrashLoopBackOff due to corrupted WAL segments, rejecting all socket connections from dependent checkout services.",
                "trigger": "Underlying database container crash during disk sync.",
                "symptoms": ["psycopg2.OperationalError: Connection refused on port 5432", "Cascading HTTP 504 Gateway Timeout in checkout service", "Frontend experiencing 502 Bad Gateway"],
                "required_sources": ["Kubernetes", "Logs", "Traces"]
            },
            "pods": [
                {
                    "name": "database-postgresql-0",
                    "namespace": "default",
                    "status": "CrashLoopBackOff",
                    "ready": False,
                    "restarts": 8,
                    "image": "postgres:15-alpine",
                    "resources": {"limits": {"memory": "1Gi"}},
                    "node": "worker-node-2"
                },
                {
                    "name": "checkout-service-684c8fb9-99mkl",
                    "namespace": "default",
                    "status": "Running",
                    "ready": True,
                    "restarts": 0,
                    "image": "myregistry.local/checkout:v1.4.0",
                    "resources": {"limits": {"memory": "512Mi"}},
                    "node": "worker-node-1"
                }
            ],
            "deployments": [
                {
                    "name": "checkout-service",
                    "namespace": "default",
                    "replicas": 1,
                    "ready_replicas": 1,
                    "image": "myregistry.local/checkout:v1.4.0",
                    "last_update": (now - timedelta(days=10)).isoformat(),
                    "revision": 1
                }
            ],
            "events": [
                {
                    "timestamp": t_crash.isoformat(),
                    "type": "Warning",
                    "reason": "BackOff",
                    "object": "Pod/database-postgresql-0",
                    "message": "Back-off restarting failed container postgresql in pod database-postgresql-0"
                },
                {
                    "timestamp": t_fail.isoformat(),
                    "type": "Warning",
                    "reason": "Unhealthy",
                    "object": "Pod/database-postgresql-0",
                    "message": "Readiness probe failed: dial tcp 10.96.0.15:5432: connect: connection refused"
                }
            ],
            "metrics": {
                'checkout_db_connection_errors_total': [
                    {"time": (t_crash - timedelta(minutes=2)).isoformat(), "value": "0"},
                    {"time": t_fail.isoformat(), "value": "45"},
                    {"time": now.isoformat(), "value": "480"}
                ],
                'http_request_duration_seconds{service="checkout"}': [
                    {"time": (t_crash - timedelta(minutes=5)).isoformat(), "value": "0.08"},
                    {"time": now.isoformat(), "value": "30.0"}
                ]
            },
            "logs": [
                {"timestamp": t_crash.isoformat(), "level": "FATAL", "message": "postgres: PANIC: could not locate a valid checkpoint record in WAL"},
                {"timestamp": t_fail.isoformat(), "level": "ERROR", "message": "checkout.db: psycopg2.OperationalError: could not connect to server: Connection refused on port 5432"},
                {"timestamp": (now - timedelta(minutes=5)).isoformat(), "level": "ERROR", "message": "checkout.service: upstream database unavailable, returning HTTP 504 Gateway Timeout"}
            ],
            "traces": [
                {"trace_id": "tr-dep-fail-1", "service": "checkout", "operation": "db.query", "duration_ms": 30000, "status": 504, "error": True, "error_message": "Connection refused"}
            ],
            "dependencies": {
                "nodes": ["frontend", "checkout", "database-postgresql"],
                "edges": [{"source": "frontend", "target": "checkout"}, {"source": "checkout", "target": "database-postgresql"}]
            },
            "deployment_history": [
                {"revision": 1, "image": "myregistry.local/checkout:v1.4.0", "updated_at": (now - timedelta(days=10)).isoformat(), "author": "bob"}
            ],
            "config_changes": []
        }

    @staticmethod
    def get_multi_source_scenario(base_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Scenario 4 (Flagship): Deployment v2 + ConfigMap change -> DB Connection Leak -> Connection Pool Exhaustion in Prometheus + Loki -> Readiness Probe Failure -> Restarts -> 5xx."""
        now = base_time or datetime.utcnow()
        t_deploy = now - timedelta(minutes=16)
        t_conn_spike = now - timedelta(minutes=12)
        t_log_exhaust = now - timedelta(minutes=10)
        t_5xx_spike = now - timedelta(minutes=8)
        t_probe_fail = now - timedelta(minutes=7)
        t_pod_restart = now - timedelta(minutes=6)
        t_alert = now - timedelta(minutes=5)

        return {
            "id": "multi_source",
            "name": "Flagship Multi-Source Incident: Rollout + Connection Leak + Pool Exhaustion",
            "ground_truth": {
                "root_cause": "Deployment checkout:v2.2.0 introduced a persistent database connection leak (unclosed connections in order persistence flow), which combined with a reduced max_pool_size=10 in configmap, exhausted the connection pool, causing connection timeouts, 5xx errors, readiness probe failures, and pod restarts.",
                "trigger": "Rollout of checkout:v2.2.0 and ConfigMap update pool_size: 10.",
                "contributing_factors": ["ConfigMap reduced DB connection pool ceiling from 50 to 10", "No circuit breaker or timeout fallback configured for acquire requests"],
                "symptoms": ["Active DB connections pegged at maximum pool capacity (10/10)", "Loki logs: 'PoolAcquireTimeoutException: connection pool exhausted'", "Readiness probe failures and kubelet pod restarts"],
                "required_sources": ["Kubernetes", "Prometheus", "Loki", "Deployment"]
            },
            "pods": [
                {
                    "name": "checkout-service-7bb86d654-q2w3e",
                    "namespace": "default",
                    "status": "Running",
                    "ready": False,
                    "restarts": 2,
                    "image": "myregistry.local/checkout:v2.2.0",
                    "resources": {"limits": {"memory": "512Mi", "cpu": "500m"}},
                    "node": "worker-node-1"
                },
                {
                    "name": "database-postgresql-0",
                    "namespace": "default",
                    "status": "Running",
                    "ready": True,
                    "restarts": 0,
                    "image": "postgres:15-alpine",
                    "resources": {"limits": {"memory": "1Gi"}},
                    "node": "worker-node-2"
                }
            ],
            "deployments": [
                {
                    "name": "checkout-service",
                    "namespace": "default",
                    "replicas": 1,
                    "ready_replicas": 0,
                    "image": "myregistry.local/checkout:v2.2.0",
                    "last_update": t_deploy.isoformat(),
                    "revision": 2
                }
            ],
            "events": [
                {
                    "timestamp": t_deploy.isoformat(),
                    "type": "Normal",
                    "reason": "ScalingReplicaSet",
                    "object": "Deployment/checkout-service",
                    "message": "Scaled up replica set checkout-service-7bb86d654 to 1"
                },
                {
                    "timestamp": t_probe_fail.isoformat(),
                    "type": "Warning",
                    "reason": "Unhealthy",
                    "object": "Pod/checkout-service-7bb86d654-q2w3e",
                    "message": "Readiness probe failed: HTTP probe failed with statuscode: 503"
                },
                {
                    "timestamp": t_pod_restart.isoformat(),
                    "type": "Warning",
                    "reason": "BackOff",
                    "object": "Pod/checkout-service-7bb86d654-q2w3e",
                    "message": "Back-off restarting failed container checkout in pod checkout-service-7bb86d654-q2w3e"
                }
            ],
            "metrics": {
                'checkout_db_active_connections': [
                    {"time": (t_deploy - timedelta(minutes=5)).isoformat(), "value": "2"},
                    {"time": t_conn_spike.isoformat(), "value": "6"},
                    {"time": t_log_exhaust.isoformat(), "value": "10"},
                    {"time": now.isoformat(), "value": "10"}
                ],
                'checkout_db_pool_max_capacity': [
                    {"time": now.isoformat(), "value": "10"}
                ],
                'http_requests_total{status=~"5.*",service="checkout"}': [
                    {"time": (t_deploy - timedelta(minutes=5)).isoformat(), "value": "0"},
                    {"time": t_5xx_spike.isoformat(), "value": "18"},
                    {"time": now.isoformat(), "value": "240"}
                ],
                'http_requests_total{status="200",service="checkout"}': [
                    {"time": (t_deploy - timedelta(minutes=5)).isoformat(), "value": "85"},
                    {"time": t_5xx_spike.isoformat(), "value": "12"},
                    {"time": now.isoformat(), "value": "4"}
                ]
            },
            "logs": [
                {"timestamp": (t_deploy + timedelta(seconds=10)).isoformat(), "level": "INFO", "message": "checkout-service:v2.2.0 initialized with DB pool max_size=10"},
                {"timestamp": t_log_exhaust.isoformat(), "level": "ERROR", "message": "com.zaxxer.hikari.pool.HikariPool: HikariPool-1 - Connection is not available, request timed out after 30005ms (active=10, idle=0, waiting=28)"},
                {"timestamp": (t_5xx_spike).isoformat(), "level": "ERROR", "message": "org.springframework.transaction.CannotCreateTransactionException: Could not open JDBC Connection for transaction; nested exception is java.sql.SQLTransientConnectionException: HikariPool-1 - Connection is not available"},
                {"timestamp": (t_alert).isoformat(), "level": "ERROR", "message": "GET /checkout 503 Service Unavailable - upstream database pool saturated"}
            ],
            "traces": [
                {"trace_id": "tr-multi-01", "service": "checkout", "operation": "HikariCP.getConnection", "duration_ms": 30005, "status": 503, "error": True, "error_message": "PoolAcquireTimeoutException: connection pool exhausted"}
            ],
            "dependencies": {
                "nodes": ["frontend", "checkout", "database-postgresql"],
                "edges": [{"source": "frontend", "target": "checkout"}, {"source": "checkout", "target": "database-postgresql"}]
            },
            "deployment_history": [
                {"revision": 1, "image": "myregistry.local/checkout:v2.1.0", "updated_at": (now - timedelta(days=3)).isoformat(), "author": "alice"},
                {"revision": 2, "image": "myregistry.local/checkout:v2.2.0", "updated_at": t_deploy.isoformat(), "author": "charlie"}
            ],
            "config_changes": [
                {"revision": 1, "config_map": "checkout-config", "key": "DB_POOL_MAX", "value": "50", "updated_at": (now - timedelta(days=3)).isoformat()},
                {"revision": 2, "config_map": "checkout-config", "key": "DB_POOL_MAX", "value": "10", "updated_at": t_deploy.isoformat()}
            ]
        }


class ActiveScenarioManager:
    """Singleton maintaining active simulated scenario state across test runs and API requests."""
    _current_scenario_id = "multi_source"
    _base_time = datetime.utcnow()

    @classmethod
    def set_scenario(cls, scenario_id: str):
        cls._current_scenario_id = scenario_id
        cls._base_time = datetime.utcnow()

    @classmethod
    def get_current_scenario(cls) -> Dict[str, Any]:
        if cls._current_scenario_id == "oom":
            return ScenarioCatalog.get_oom_scenario(cls._base_time)
        elif cls._current_scenario_id == "bad_deployment":
            return ScenarioCatalog.get_bad_deployment_scenario(cls._base_time)
        elif cls._current_scenario_id == "dependency_failure":
            return ScenarioCatalog.get_dependency_failure_scenario(cls._base_time)
        else:
            return ScenarioCatalog.get_multi_source_scenario(cls._base_time)
