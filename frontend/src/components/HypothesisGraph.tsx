import React from 'react';
import { GitCommit, Check, X, HelpCircle, Shield, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { Hypothesis, HypothesisStatus } from '../types';

interface HypothesisGraphProps {
  hypotheses: Hypothesis[];
}

export const HypothesisGraph: React.FC<HypothesisGraphProps> = ({ hypotheses }) => {
  const getStatusColor = (status: HypothesisStatus) => {
    switch (status) {
      case 'CONFIRMED':
      case 'SUPPORTED':
        return 'bg-emerald-950 text-emerald-300 border-emerald-700/60 ring-1 ring-emerald-500/20';
      case 'WEAKENED':
        return 'bg-amber-950/40 text-amber-300 border-amber-800/40';
      case 'REJECTED':
        return 'bg-rose-950/40 text-rose-300 border-rose-800/40 opacity-70';
      case 'INVESTIGATING':
        return 'bg-indigo-950/40 text-indigo-300 border-indigo-800/40';
      default:
        return 'bg-slate-900 text-slate-400 border-slate-800';
    }
  };

  const sortedHypotheses = [...hypotheses].sort((a, b) => b.current_score - a.current_score);

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h2 className="text-lg font-bold text-white">Hypothesis Belief Distribution</h2>
        <p className="text-xs text-slate-400 mt-1">
          Probabilistic Bayesian scoring across competing distributed failure explanations. Updated dynamically as multi-source evidence is acquired.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sortedHypotheses.map((h, idx) => {
          const delta = h.current_score - h.prior_score;
          const isLeader = idx === 0;

          return (
            <div
              key={h.id}
              className={`rounded-xl p-5 border transition ${getStatusColor(h.status)} ${
                isLeader ? 'ring-2 ring-emerald-500/40' : ''
              }`}
            >
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-white">
                    {h.id}
                  </span>
                  <span className="text-xs uppercase tracking-wider font-semibold opacity-75">
                    {h.category}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold uppercase px-2 py-0.5 rounded bg-slate-950/80">
                    {h.status}
                  </span>
                </div>
              </div>

              {/* Description */}
              <p className="mt-3 text-sm font-medium text-white leading-snug">
                {h.description}
              </p>

              {/* Score Meter */}
              <div className="mt-4 pt-3 border-t border-slate-800/60">
                <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                  <span className="text-slate-400">Belief Posterior</span>
                  <div className="flex items-center space-x-1.5">
                    <span className="font-bold text-white text-sm">{(h.current_score * 100).toFixed(1)}%</span>
                    {delta > 0.01 ? (
                      <span className="text-emerald-400 flex items-center text-[11px]">
                        <ArrowUpRight className="h-3 w-3" />
                        +{(delta * 100).toFixed(1)}%
                      </span>
                    ) : delta < -0.01 ? (
                      <span className="text-rose-400 flex items-center text-[11px]">
                        <ArrowDownRight className="h-3 w-3" />
                        {(delta * 100).toFixed(1)}%
                      </span>
                    ) : null}
                  </div>
                </div>

                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div
                    className={`h-full transition-all duration-500 ${
                      h.status === 'CONFIRMED' || h.status === 'SUPPORTED'
                        ? 'bg-emerald-500'
                        : h.status === 'WEAKENED'
                        ? 'bg-amber-500'
                        : h.status === 'REJECTED'
                        ? 'bg-rose-500'
                        : 'bg-indigo-500'
                    }`}
                    style={{ width: `${Math.min(Math.max(h.current_score * 100, 4), 100)}%` }}
                  ></div>
                </div>
              </div>

              {/* Required & Observed Evidence */}
              <div className="mt-4 space-y-2 text-xs">
                {h.supporting_evidence.length > 0 && (
                  <div className="flex items-start space-x-1.5 text-emerald-400 font-mono">
                    <Check className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
                    <span>{h.supporting_evidence.length} Supporting Evidence Items</span>
                  </div>
                )}
                {h.contradicting_evidence.length > 0 && (
                  <div className="flex items-start space-x-1.5 text-rose-400 font-mono">
                    <X className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
                    <span>{h.contradicting_evidence.length} Contradicting Telemetry Items</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
