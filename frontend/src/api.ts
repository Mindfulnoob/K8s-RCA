import { InvestigationState, RCAReport, Scenario } from './types';

const API_BASE = '/api';

export async function fetchClusterStatus(): Promise<any> {
  const res = await fetch(`${API_BASE}/cluster/status`);
  if (!res.ok) throw new Error('Failed to fetch cluster status');
  return res.json();
}

export async function fetchScenarios(): Promise<Scenario[]> {
  const res = await fetch(`${API_BASE}/incidents/scenarios`);
  if (!res.ok) throw new Error('Failed to fetch scenarios');
  return res.json();
}

export async function triggerScenario(scenarioId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/incidents/${scenarioId}/trigger`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to trigger scenario');
  return res.json();
}

export async function fetchInvestigations(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/investigations`);
  if (!res.ok) throw new Error('Failed to list investigations');
  return res.json();
}

export async function fetchInvestigation(id: string): Promise<InvestigationState> {
  const res = await fetch(`${API_BASE}/investigations/${id}`);
  if (!res.ok) throw new Error('Failed to fetch investigation');
  return res.json();
}

export async function startInvestigation(params: {
  incident: string;
  namespace?: string;
  provider_type?: string;
  max_steps?: number;
}): Promise<InvestigationState> {
  const res = await fetch(`${API_BASE}/investigations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      incident: params.incident,
      namespace: params.namespace || 'default',
      provider_type: params.provider_type || 'mock',
      max_steps: params.max_steps || 8,
      run_to_completion: true,
    }),
  });
  if (!res.ok) throw new Error('Failed to start investigation');
  return res.json();
}

export async function stepInvestigation(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/investigations/${id}/step`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to execute investigation step');
  return res.json();
}

export async function fetchEvaluationReport(): Promise<any> {
  const res = await fetch(`${API_BASE}/evaluation/latest`);
  if (!res.ok) throw new Error('Failed to fetch evaluation report');
  return res.json();
}

export async function runEvaluationBenchmark(): Promise<any> {
  const res = await fetch(`${API_BASE}/evaluation/run`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to run benchmark');
  return res.json();
}
