# KubeRCA Agent: Architecture & System Design

## 1. Executive Summary

The **KubeRCA Agent** is an autonomous Site Reliability Engineering (SRE) root-cause analysis system designed for Kubernetes environments. Rather than acting as a static LLM wrapper that blindly executes `kubectl describe` and passes raw output to a language model, KubeRCA implements an **iterative, hypothesis-driven cognitive investigation loop**. 

It dynamically selects diagnostic queries across multiple independent observability vectors (Kubernetes cluster state, Prometheus time-series metrics, Loki log streams, and Jaeger distributed traces), updates probabilistic belief states using Bayesian principles, and synthesizes a defensible, explainable causal graph.

```
                ┌──────────────────────┐
                │    Incident Input    │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Investigation Agent  │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Evidence Manager     │
                └──────────┬───────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    Kubernetes          Metrics            Logs
     Adapter           Adapter            Adapter
          │                │                │
          ▼                ▼                ▼
      K8s API          Prometheus          Loki
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                     Evidence Store
                           │
                           ▼
                   Hypothesis Engine
                           │
                           ▼
                  Investigation Planner
                           │
                           ▼
                     RCA Generator
```

---

## 2. The Cognitive Investigation Loop

The central engine iterates through the following sequence until reaching a high-confidence stopping condition:

1. **Incident Intake**: Receives an alert or symptom summary (e.g., *"The checkout service suddenly has a high 5xx error rate, probe failures, and restarts"*).
2. **Hypothesis Initialization**: Instantiates 5 to 7 plausible distributed failure modes from the SRE Catalog (Bad Deployment, Database Exhaustion, Pod OOM, Configuration Change, Dependency Outage, Node Pressure, Traffic Spike) with normalized Bayesian prior probabilities ($P(H_i) \approx \frac{1}{N}$).
3. **Dynamic Planning**: Calculates the Shannon entropy of the active belief distribution and evaluates candidate tools by expected information gain minus query execution cost, prioritizing unexplored observability vectors.
4. **Sandboxed Tool Execution**: Dispatches queries through the capability-based security layer. Destructive verbs (`delete`, `patch`, `apply`, `exec`, `secret-read`) are strictly blocked.
5. **Untrusted Data Isolation & Evidence Normalization**: Observability output is scanned for prompt injection markers, enclosed in structured `<untrusted_evidence>` containers, scanned for secrets/passwords, and transformed into structured `Evidence` records.
6. **Bayesian Belief Updating**: Multiplies hypothesis priors by evidence likelihood ratios ($L > 1.0$ for direct/correlated supporting telemetry; $L < 1.0$ for contradicting telemetry) and normalizes posteriors across all competing hypotheses.
7. **Convergence & Sufficiency Check**: Determines whether the leading hypothesis exceeds the confidence threshold ($\ge 85\%$) with multi-source corroboration, or if more queries are required.
8. **RCA Synthesis**: Synthesizes a directed causal graph distinguishing Root Cause, Trigger, Contributing Factors, and operational Symptoms.

---

## 3. Core Subsystems

### 3.1 Observability Provider Abstraction
To ensure portability across live production clusters, Kind/Minikube environments, and headless CI pipelines, all monitoring sources adhere to abstract interfaces:
- **`BaseKubernetesProvider`**: Safe pod inspections, replica counts, event logs, restarts, and deployment revision histories.
- **`BasePrometheusProvider`**: PromQL instant vector evaluations and range queries.
- **`BaseLokiProvider`**: LogQL stream filters, pattern extractions, and terminated container log queries.
- **`BaseJaegerProvider`**: Distributed trace spans and latency breakdown waterfalls.

Each provider features both a live HTTP/client driver and a high-fidelity in-memory sandbox engine containing seeded telemetry for all 4 reproducible incident scenarios.

### 3.2 Hypothesis Engine & Bayesian Belief Updating
Given evidence $E$, posterior probability $P(H_k | E)$ is updated as:
$$P(H_k | E) = \frac{P(H_k) \cdot L(E | H_k)}{\sum_{j} P(H_j) \cdot L(E | H_j)}$$
- Direct supporting evidence (e.g. `OOMKilled` exit code 137 for $H_{OOM}$, or `NullPointerException` for $H_{DEPLOY}$): $L = 3.6$
- Correlated supporting evidence (e.g. probe failures for $H_{DB}$): $L = 2.2$
- Direct contradiction (e.g. 0 pod restarts contradicts $H_{OOM}$): $L = 0.20$

### 3.3 Dynamic Investigation Planner
The planner avoids static script runs. At each step, it chooses an action $A^*$ maximizing net expected utility:
$$A^* = \arg\max_{A} \frac{\text{InformationGain}(A) + \text{DiversityBonus}(A)}{1.0 + 0.2 \cdot \text{Cost}(A)}$$
- Avoids re-querying identical endpoints (redundancy pruning).
- Grants bonuses to unqueried observability sources to force multi-source cross-validation.

### 3.4 Directed Causal Graph (DAG) Synthesis
The engine separates causal layers:
- **Root Cause**: The foundational defect (e.g. unclosed connection leak in release v2.2.0).
- **Contributing Factor**: Exacerbating constraints (e.g. DB_POOL_MAX reduced from 50 to 10 in ConfigMap).
- **Trigger**: The activation event (e.g. rollout to production traffic).
- **Symptoms**: Observed operational telemetry (e.g. active DB connections 10/10, 503 errors, readiness probe failures, pod restarts).

### 3.5 Transparent Confidence Scoring
Confidence is not an arbitrary LLM hallucination. It is calculated via an explicit multi-factor formula:
$$\text{Confidence} = \min\left(\text{LeaderBelief} \times 50 + \text{DiversityBonus} + \text{SupportBonus} + \text{CorrelationBonus} + \text{SeparationBonus} - \text{ContradictionPenalty}, 96\%\right)$$
Every report includes a human-readable justification breaking down the exact variables.
