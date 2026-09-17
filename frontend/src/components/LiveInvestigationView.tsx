import React, { useState } from 'react';
import { Play, ArrowRight, CheckCircle2, AlertCircle, ShieldAlert, Cpu, Terminal, RefreshCw, Layers } from 'lucide-react';
import { InvestigationState, InvestigationStep, Evidence } from '../types';

interface LiveInvestigationViewProps {
  investigation: InvestigationState | null;
  onStepInvestigation: () => void;
  isLoading: boolean;
}

export const LiveInvestigationView: React.FC<LiveInvestigationViewProps> = ({
  investigation,
  onStepInvestigation,
  isLoading,
}) => {
  const [selectedStepIndex, setSelectedStepIndex] = useState<number>(
    investigation?.steps ? investigation.steps.length - 1 : 0
  );

  if (!investigation) {
    return (
      <div className="text-center py-20 bg-slate-900 border border-slate-800 rounded-xl">
        <p className="text-slate-400">No active investigation selected. Start a new investigation or select one from history.</p>
      </div>
    );
  }

  const steps = investigation.steps || [];
  const currentStep = steps[selectedStepIndex] || steps[steps.length - 1];
  const isCompleted = investigation.status === 'COMPLETED';

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                {investigation.id}
              </span>
              <span className="text-xs font-mono text-slate-400">Namespace: {investigation.namespace}</span>
              <span className="text-xs font-mono text-slate-400">• Time: {investigation.time_range}</span>
            </div>
            <h1 className="text-xl font-bold text-white mt-1.5">{investigation.incident}</h1>
            <p className="text-xs text-slate-400 mt-1 flex items-center space-x-2">
              <span className="text-brand-400 font-medium">Focus:</span>
              <span>{investigation.current_focus}</span>
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <div className="text-right">
              <span className="text-xs text-slate-400 block font-mono">CONFIDENCE</span>
              <span className="text-2xl font-bold font-mono text-emerald-400">
                {investigation.confidence.toFixed(1)}%
              </span>
            </div>
            {!isCompleted && (
              <button
                onClick={onStepInvestigation}
                disabled={isLoading}
                className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-sm font-semibold transition flex items-center space-x-2 disabled:opacity-50 shadow-md shadow-brand-600/20"
              >
                {isLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-current" />}
                <span>{isLoading ? 'Investigating...' : 'Step Next'}</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Grid: Steps Sequence + Detail Pane */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Step Sequence Timeline */}
        <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Autonomous Steps</h2>
            <span className="text-xs font-mono text-brand-400">{steps.length} Executed</span>
          </div>

          <div className="space-y-2">
            {steps.map((step, idx) => {
              const isSelected = idx === selectedStepIndex;
              const hasTool = !!step.tool_name;

              return (
                <div
                  key={idx}
                  onClick={() => setSelectedStepIndex(idx)}
                  className={`p-3 rounded-lg border text-xs cursor-pointer transition flex items-start space-x-3 ${
                    isSelected
                      ? 'bg-slate-800/90 border-brand-500/60 ring-1 ring-brand-500/30'
                      : 'bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/40'
                  }`}
                >
                  <div className="mt-0.5">
                    {hasTool ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4 text-brand-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-slate-400 font-semibold">Step {step.step_number}</span>
                      <span className="font-mono text-[10px] text-emerald-400">{step.confidence_score.toFixed(1)}%</span>
                    </div>
                    <p className="font-medium text-white truncate mt-0.5">
                      {step.tool_name || 'RCA Synthesized'}
                    </p>
                    <p className="text-slate-400 text-[11px] truncate mt-0.5">
                      {step.tool_output_summary || 'Evidence evaluated'}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Step Inspector */}
        <div className="lg:col-span-8 space-y-4">
          {currentStep ? (
            <>
              {/* Agent Reasoning & Rationale Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono uppercase tracking-wider text-brand-400 font-semibold flex items-center space-x-1.5">
                    <Cpu className="h-3.5 w-3.5" />
                    <span>Agent Decision & Information Gain</span>
                  </span>
                  <span className="text-xs font-mono text-slate-500">
                    {new Date(currentStep.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-sm text-slate-200 leading-relaxed font-mono bg-slate-950 p-3.5 rounded-lg border border-slate-800">
                  {currentStep.decision?.rationale || currentStep.tool_output_summary || 'Evaluation phase complete.'}
                </p>
              </div>

              {/* Tool Execution Inspector */}
              {currentStep.tool_name && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center space-x-1.5">
                      <Terminal className="h-3.5 w-3.5 text-indigo-400" />
                      <span>Executed Capability: <span className="text-white">{currentStep.tool_name}</span></span>
                    </span>
                    <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono">
                      SANDBOX APPROVED
                    </span>
                  </div>

                  <div className="bg-slate-950 rounded-lg p-3.5 border border-slate-800 font-mono text-xs overflow-x-auto text-slate-300">
                    <div className="text-slate-500 mb-1">// Arguments passed</div>
                    <pre>{JSON.stringify(currentStep.arguments, null, 2)}</pre>
                  </div>
                </div>
              )}

              {/* Evidence Discovered Card */}
              {currentStep.evidence_collected && currentStep.evidence_collected.length > 0 && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center space-x-1.5">
                      <Layers className="h-3.5 w-3.5 text-amber-400" />
                      <span>Extracted Observation</span>
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      Source: {currentStep.evidence_collected[0].source}
                    </span>
                  </div>

                  <div className="bg-slate-950 rounded-lg p-4 border border-slate-800">
                    <p className="text-sm font-semibold text-white">
                      {currentStep.evidence_collected[0].observation.summary}
                    </p>

                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                      {currentStep.evidence_collected[0].supports_hypotheses?.map((h) => (
                        <span key={h} className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-mono">
                          Supports {h}
                        </span>
                      ))}
                      {currentStep.evidence_collected[0].weakens_hypotheses?.map((h) => (
                        <span key={h} className="px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800/60 font-mono">
                          Weakens {h}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12 text-slate-500">Select a step to inspect reasoning.</div>
          )}
        </div>
      </div>
    </div>
  );
};
