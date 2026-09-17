import React, { useState } from 'react';
import { X, Play, ShieldAlert, Cpu } from 'lucide-react';

interface NewInvestigationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStart: (params: { incident: string; namespace: string; provider_type: string; max_steps: number }) => void;
  isLoading: boolean;
}

export const NewInvestigationModal: React.FC<NewInvestigationModalProps> = ({
  isOpen,
  onClose,
  onStart,
  isLoading,
}) => {
  const [incident, setIncident] = useState('The checkout service suddenly has a high 5xx error rate, probe failures, and restarts.');
  const [namespace, setNamespace] = useState('default');
  const [providerType, setProviderType] = useState('mock');
  const [maxSteps, setMaxSteps] = useState(8);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!incident.trim()) return;
    onStart({ incident, namespace, provider_type: providerType, max_steps: maxSteps });
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-lg overflow-hidden shadow-2xl">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Cpu className="h-5 w-5 text-brand-400" />
            <h3 className="font-bold text-white text-base">Start Autonomous Investigation</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-medium">
              Incident Prompt / Alert Symptom
            </label>
            <textarea
              value={incident}
              onChange={(e) => setIncident(e.target.value)}
              rows={3}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-brand-500 font-mono"
              placeholder="Describe the incident symptom (e.g. checkout service experiencing 5xx error rate spike)..."
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-medium">
                Target Namespace
              </label>
              <input
                type="text"
                value={namespace}
                onChange={(e) => setNamespace(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm text-white font-mono focus:outline-none focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5 font-medium">
                LLM Provider Engine
              </label>
              <select
                value={providerType}
                onChange={(e) => setProviderType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm text-white font-mono focus:outline-none focus:border-brand-500"
              >
                <option value="mock">Deterministic Mock (Evaluation Mode)</option>
                <option value="openai">OpenAI (GPT-4o)</option>
                <option value="gemini">Google Gemini (1.5 Pro)</option>
              </select>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1.5">
              <span>Max Investigation Steps: {maxSteps}</span>
              <span>Default: 8</span>
            </div>
            <input
              type="range"
              min={3}
              max={12}
              value={maxSteps}
              onChange={(e) => setMaxSteps(Number(e.target.value))}
              className="w-full accent-brand-500 bg-slate-800 rounded-lg h-2 cursor-pointer"
            />
          </div>

          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex items-start space-x-2 text-xs text-slate-400">
            <ShieldAlert className="h-4 w-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <span>
              The capability-based sandbox will enforce strict read-only execution across all Kubernetes and observability sources.
            </span>
          </div>

          <div className="pt-2 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold transition flex items-center space-x-1.5 disabled:opacity-50"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>{isLoading ? 'Starting...' : 'Start Investigation'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
