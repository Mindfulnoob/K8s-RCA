import React from 'react';
import { X, Play, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Scenario } from '../types';

interface ScenarioLauncherModalProps {
  isOpen: boolean;
  onClose: () => void;
  scenarios: Scenario[];
  onTriggerScenario: (scenarioId: string) => void;
  isLoading: boolean;
}

export const ScenarioLauncherModal: React.FC<ScenarioLauncherModalProps> = ({
  isOpen,
  onClose,
  scenarios,
  onTriggerScenario,
  isLoading,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-2xl overflow-hidden shadow-2xl">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-amber-400" />
            <h3 className="font-bold text-white text-base">Select & Trigger Incident Scenario</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
          {scenarios.map((sc) => {
            const isFlagship = sc.id === 'multi_source';
            return (
              <div
                key={sc.id}
                className={`p-4 rounded-xl border transition flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 ${
                  isFlagship
                    ? 'bg-brand-950/20 border-brand-500/40 ring-1 ring-brand-500/20'
                    : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold text-slate-300 uppercase">{sc.id}</span>
                    {isFlagship && (
                      <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-brand-500/20 text-brand-400 border border-brand-500/30">
                        FLAGSHIP
                      </span>
                    )}
                  </div>
                  <h4 className="font-semibold text-white text-sm">{sc.name}</h4>
                  <p className="text-xs text-slate-400 line-clamp-2">{sc.description}</p>
                  <p className="text-[11px] font-mono text-brand-400/90 pt-1">
                    Required Telemetry: {sc.ground_truth?.required_sources?.join(' + ')}
                  </p>
                </div>

                <button
                  onClick={() => {
                    onTriggerScenario(sc.id);
                    onClose();
                  }}
                  disabled={isLoading}
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold transition flex items-center space-x-1.5 flex-shrink-0 disabled:opacity-50"
                >
                  <Play className="h-3.5 w-3.5 fill-current" />
                  <span>Trigger Scenario</span>
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
