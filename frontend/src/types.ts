export type HypothesisStatus =
  | 'UNTESTED'
  | 'INVESTIGATING'
  | 'SUPPORTED'
  | 'WEAKENED'
  | 'REJECTED'
  | 'CONFIRMED';

export interface Hypothesis {
  id: string;
  category: string;
  description: string;
  prior_score: number;
  current_score: number;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  required_evidence: string[];
  status: HypothesisStatus;
  rationale?: string;
}

export interface NormalizedObservation {
  summary: string;
  metric_name?: string;
  observed_value?: string;
  baseline_value?: string;
  anomaly_detected: boolean;
  details: Record<string, any>;
}

export interface Evidence {
  id: string;
  source: string;
  timestamp: string;
  query: string;
  raw_data?: any;
  observation: NormalizedObservation;
  related_hypotheses: string[];
  supports_hypotheses: string[];
  weakens_hypotheses: string[];
  evidence_type: string;
  reliability: string;
  source_component?: string;
  security_flagged: boolean;
  security_note?: string;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  source: string;
  component: string;
  title: string;
  description: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  related_evidence_id?: string;
  metadata?: Record<string, any>;
}

export interface CausalNode {
  id: string;
  label: string;
  type: 'ROOT_CAUSE' | 'TRIGGER' | 'CONTRIBUTING_FACTOR' | 'SYMPTOM' | 'DOWNSTREAM_EFFECT';
  description: string;
  component: string;
  evidence_ids: string[];
}

export interface CausalEdge {
  source_id: string;
  target_id: string;
  relationship: string;
}

export interface CausalChain {
  nodes: CausalNode[];
  edges: CausalEdge[];
  summary: string;
}

export interface AlternativeExplanation {
  hypothesis_id: string;
  description: string;
  reason_weakened_or_rejected: string;
  residual_probability: number;
}

export interface RCAReport {
  id: string;
  incident: string;
  generated_at: string;
  root_cause: string;
  trigger?: string;
  contributing_factors: string[];
  symptoms: string[];
  confidence_score: number;
  confidence_explanation: string;
  observed_facts: string[];
  hypotheses_evaluated: Hypothesis[];
  supporting_evidence_summaries: string[];
  contradicting_evidence_summaries: string[];
  causal_chain: CausalChain;
  alternative_explanations: AlternativeExplanation[];
  unknowns_and_ambiguities: string[];
  recommended_mitigation: string[];
  recommended_next_investigations: string[];
  timeline: TimelineEvent[];
  multi_source_correlation_summary?: string;
  is_sufficient_evidence: boolean;
}

export interface ReplayFrame {
  step_number: number;
  timestamp: string;
  phase: string;
  active_hypotheses: any[];
  latest_evidence?: any;
  current_thought: string;
  executed_query?: string;
  confidence_at_step: number;
}

export interface InvestigationStep {
  step_number: number;
  timestamp: string;
  status: string;
  decision?: any;
  tool_name?: string;
  arguments?: Record<string, any>;
  tool_output_summary?: string;
  evidence_collected: Evidence[];
  hypotheses_state: Hypothesis[];
  current_focus?: string;
  confidence_score: number;
}

export interface InvestigationState {
  id: string;
  incident: string;
  namespace: string;
  time_range: string;
  status: string;
  start_time: string;
  end_time?: string;
  current_focus?: string;
  confidence: number;
  confidence_explanation?: string;
  observations: string[];
  hypotheses: Hypothesis[];
  queries_executed: string[];
  evidence: Evidence[];
  timeline: TimelineEvent[];
  decisions: any[];
  steps: InvestigationStep[];
  replay_frames: ReplayFrame[];
  rca_report?: RCAReport;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  prompt: string;
  ground_truth: any;
}
