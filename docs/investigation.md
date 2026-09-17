# KubeRCA Agent: Investigation Lifecycle & Replay Engine

## 1. Investigation Lifecycle

An investigation proceeds through distinct deterministic phases:

```
[INITIALIZING]
  │ Formulate initial candidate hypotheses
  │ Assign normalized Bayesian prior probabilities
  ▼
[INVESTIGATING]
  │ Dynamic Planner calculates Shannon entropy
  │ Planner selects highest information-gain tool query
  │ Sandboxed tool dispatches read-only query
  │ Secret redaction + Prompt injection defense
  │ Bayesian belief updater updates hypothesis scores
  │ Timeline normalizer merges events
  │ Confidence calculator re-evaluates multi-factor score
  ▼
[STOPPING CONDITION EVALUATION]
  │ Has leader score exceeded threshold (>= 85%)?
  │ Have competing alternatives been weakened?
  │ Have >= 2 independent observability sources been corroborated?
  ├────────► If NO: Continue loop [INVESTIGATING]
  ▼ If YES
[RCA SYNTHESIS & COMPLETION]
  │ Synthesize Directed Causal Graph (DAG)
  │ Categorize Root Cause, Trigger, Contributor, Symptom
  │ Document Observed Facts vs Hypotheses vs Unknowns
  │ Generate Mitigations and Next Investigation Steps
  ▼
[COMPLETED]
```

---

## 2. Investigation Replay Engine

To verify that the agent genuinely investigated rather than generating a static pre-baked response, every step records an immutable `ReplayFrame`:

### Replay Frame Schema
- `step_number`: Chronological step sequence.
- `timestamp`: UTC execution timestamp.
- `phase`: Active tool or cognitive state.
- `active_hypotheses`: Full snapshot of all hypothesis probability scores at that exact step.
- `latest_evidence`: Observation extracted from the tool call.
- `current_thought`: The agent's decision rationale and expected information gain.
- `executed_query`: Capability name and argument signature.
- `confidence_at_step`: Transparent confidence percentage at this step.

Users can use the interactive scrubber slider in the frontend dashboard to step backwards and forwards through an investigation, observing how the agent's beliefs evolved in response to each piece of telemetry.
