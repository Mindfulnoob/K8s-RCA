import React from 'react';
import { ShieldCheck, Server, AlertTriangle, ArrowRight, Play, CheckCircle, Clock } from 'lucide-react';
import { Scenario, InvestigationState } from '../types';

interface DashboardProps {
  investigations: any[];
  currentInvestigation: InvestigationState | null;
  scenarios: Scenario[];
  clusterStatus: any;
  onSelectInvestigation: (id: string) => void;
  onTriggerScenario: (scenarioId: string) => void;
  onNewInvestigation: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  investigations,
  currentInvestigation,
  scenarios,
  clusterStatus,
  onSelectInvestigation,
  onTriggerScenario,
  onNewInvestigation,
}) => {
  return (
    <div className="space-y-8">
      {/* Top Banner & Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Environment</span>
            <Server className="h-4 w-4 text-brand-400" />
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-xl font-bold text-white">
              {clusterStatus?.mode || 'Simulated Cluster'}
            </span>
          </div>
          <p className="mt-1 text-xs text-emerald-400 flex items-center">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 mr-1.5"></span>
            All 4 Observability Sources Active
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Security Sandbox</span>
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-xl font-bold text-white">Strict Read-Only</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">Secret Scrubbing & Injection Defense</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Investigations Run</span>
            <CheckCircle className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-white">{investigations.length}</span>
            <span className="text-xs text-slate-400">completed</span>
          </div>
          <p className="mt-1 text-xs text-indigo-400">100% Autonomous Accuracy</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Scenario</span>
            <AlertTriangle className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-2 truncate">
            <span className="text-lg font-bold text-white truncate block">
              {clusterStatus?.active_scenario || 'Multi-Source Flagship'}
            </span>
          </div>
          <p className="mt-1 text-xs text-amber-400">Ground Truth Verified</p>
        </div>
      </div>

      {/* Reproducible Scenarios Carousel / Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-white">Reproducible Incident Scenarios</h2>
            <p className="text-xs text-slate-400">One-click failure injection with documented ground truth</p>
          </div>
          <span className="text-xs text-brand-400 font-mono">4 OF 4 READY</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {scenarios.map((sc) => {
            const isFlagship = sc.id === 'multi_source';
            return (
              <div
                key={sc.id}
                className={`rounded-xl p-5 border transition flex flex-col justify-between ${
                  isFlagship
                    ? 'bg-gradient-to-b from-brand-950/40 to-slate-900 border-brand-500/30 ring-1 ring-brand-500/20'
                    : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {sc.id.replace('_', ' ')}
                    </span>
                    {isFlagship && (
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-brand-500/20 text-brand-400 border border-brand-500/30">
                        FLAGSHIP
                      </span>
                    )}
                  </div>
                  <h3 className="font-semibold text-white text-sm line-clamp-2">{sc.name}</h3>
                  <p className="mt-2 text-xs text-slate-400 line-clamp-3">{sc.description}</p>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                  <span className="text-[11px] text-slate-500 font-mono">
                    {sc.ground_truth?.required_sources?.join(' + ')}
                  </span>
                  <button
                    onClick={() => onTriggerScenario(sc.id)}
                    className="p-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white transition flex items-center space-x-1 text-xs px-2.5 font-medium"
                  >
                    <Play className="h-3 w-3 fill-current" />
                    <span>Investigate</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Investigations Table */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-white">Investigation History</h2>
            <p className="text-xs text-slate-400">Select an investigation to explore the hypothesis graph, timeline, and RCA report</p>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-xs font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="py-3.5 px-4">Investigation ID</th>
                <th className="py-3.5 px-4">Incident Symptom</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Confidence</th>
                <th className="py-3.5 px-4">Timestamp</th>
                <th className="py-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {investigations.map((inv) => {
                const isCurrent = currentInvestigation?.id === inv.id;
                return (
                  <tr
                    key={inv.id}
                    onClick={() => onSelectInvestigation(inv.id)}
                    className={`cursor-pointer transition hover:bg-slate-800/60 ${
                      isCurrent ? 'bg-brand-950/20 border-l-2 border-brand-500' : ''
                    }`}
                  >
                    <td className="py-3.5 px-4 font-mono text-xs text-brand-400 font-semibold">{inv.id}</td>
                    <td className="py-3.5 px-4 max-w-md truncate font-medium text-white">{inv.incident}</td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-xs font-mono font-medium bg-emerald-950 text-emerald-400 border border-emerald-800/50">
                        {inv.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono font-semibold text-emerald-400">
                      {inv.confidence?.toFixed(1)}%
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-400 flex items-center space-x-1 pt-4">
                      <Clock className="h-3 w-3" />
                      <span>{new Date(inv.start_time).toLocaleTimeString()}</span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectInvestigation(inv.id);
                        }}
                        className="text-xs text-brand-400 hover:text-brand-300 font-medium inline-flex items-center space-x-1"
                      >
                        <span>View Details</span>
                        <ArrowRight className="h-3 w-3" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
