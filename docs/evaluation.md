# KubeRCA Agent: Automated Evaluation Framework

## 1. Evaluation Methodology

To avoid subjective assessment and ensure strict reproducibility, KubeRCA implements an **Automated Evaluation Benchmark Framework** (`backend/app/evaluation/`).

The evaluation suite runs the autonomous investigation agent against reproducible incident scenarios with known, mathematically defined ground truth.

```
                   ┌───────────────────────────┐
                   │    Ground Truth Catalog   │
                   └─────────────┬─────────────┘
                                 │
                                 ▼
                   ┌───────────────────────────┐
                   │   Evaluation Benchmark    │
                   └─────────────┬─────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
          Root Cause         Evidence      Investigation
           Accuracy          Coverage       Efficiency
                 │               │               │
                 └───────────────┼───────────────┘
                                 │
                                 ▼
                   ┌───────────────────────────┐
                   │   evaluation_report.json  │
                   └───────────────────────────┘
```

---

## 2. The 4 Reproducible Incident Scenarios

### Scenario 1: Memory Leak & OOMKilled (`oom`)
- **Incident Statement**: *"The checkout service is experiencing high 5xx error rate and container restarts."*
- **Ground Truth Root Cause**: Container memory exhaustion caused by unconstrained heap memory leak in checkout-service exceeding the 512Mi limit, resulting in kernel OOM killer termination (exit code 137) and restart backoff.
- **Required Observability Vectors**: Kubernetes (events, pod state) + Prometheus (memory usage) + Loki (JVM OutOfMemoryError).
- **Winning Hypothesis**: `H-OOM` (Score > 0.85).

### Scenario 2: Defective Release Rollout (`bad_deployment`)
- **Incident Statement**: *"Payment service transactions are failing with 100% 500 Internal Server Error following release."*
- **Ground Truth Root Cause**: Application code defect introduced in container image release v2.0.0 (NullPointerException in payment ChargeHandler) triggered immediately following ReplicaSet rollout. Replicas from v1.0.0 were unaffected.
- **Required Observability Vectors**: Kubernetes (deployment history, scaling events) + Logs (NullPointerException stack trace).
- **Winning Hypothesis**: `H-DEPLOY` (Score > 0.80).

### Scenario 3: Database Dependency Outage (`dependency_failure`)
- **Incident Statement**: *"Checkout service experiencing cascading 504 Gateway Timeout errors."*
- **Ground Truth Root Cause**: Downstream PostgreSQL database crashed into CrashLoopBackOff due to corrupted WAL record, rejecting all inbound socket connections on port 5432 and cascading timeouts upstream to checkout and frontend.
- **Required Observability Vectors**: Kubernetes (database pod crashloop) + Logs (connection refused) + Traces (30s timeouts).
- **Winning Hypothesis**: `H-DEP` / `H-DB`.

### Scenario 4: Flagship Multi-Source Incident (`multi_source`)
- **Incident Statement**: *"The checkout service suddenly has a high 5xx error rate, probe failures, and restarts."*
- **Ground Truth Root Cause**: Deployment checkout:v2.2.0 introduced a persistent database connection leak, compounded by a concurrent ConfigMap reduction of max_pool_size to 10, exhausting the HikariCP connection pool and cascading to 503 errors, readiness probe failures, and pod restarts.
- **Required Observability Vectors**: Must correlate **Kubernetes** + **Prometheus** + **Loki** + **Config Changes**.
- **Winning Hypothesis**: `H-DB` (Score > 0.85).

---

## 3. Evaluation Metrics

1. **Root Cause Accuracy**: Measures semantic and factual alignment with ground truth keywords and components ($\ge 75\%$ passing threshold).
2. **Evidence Coverage**: The fraction of required observability sources successfully queried and correlated ($\ge 70\%$ passing threshold).
3. **Investigation Efficiency**: Ratio of useful discriminating queries against acceptable upper bounds ($1 - \frac{\text{unnecessary queries}}{\text{max queries}}$).
4. **False Positive Suppression**: Verifies that mutually incompatible hypotheses (e.g. Node Pressure or Traffic Spike during a bad deployment) are decisively weakened or rejected ($< 5\%$ residual belief).

---

## 4. Running the Evaluation Suite

### CLI Execution
```bash
# Activate virtual environment
source venv/bin/activate  # Or .\venv\Scripts\Activate.ps1 on Windows

# Run benchmark script
python scripts/run_eval.py
```

### Pytest Benchmark Test
```bash
pytest tests/evaluation/test_evaluation_benchmark.py -v
```

### API Endpoint
```bash
curl -X POST http://localhost:8000/api/evaluation/run
```

Outputs are automatically exported to `evaluation_report.json`.
