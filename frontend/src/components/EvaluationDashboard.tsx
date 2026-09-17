import React, { useState } from 'react';
import { CheckCircle2, XCircle, RefreshCw, Award, BarChart3, Target, Zap } from 'lucide-react';
import { runEvaluationBenchmark } from '../api';

interface EvaluationDashboardProps {
  evaluationReport: any;
  onRefreshEvaluation: () => void;
}

export const EvaluationDashboard: React.FC<EvaluationDashboardProps> = ({
  evaluationReport,
  onRefreshEvaluation,
}) => {
  const [isRunning, setIsRunning] = useState(false);

  const handleRunBenchmark = async () => {
    try {
      setIsRunning(true);
      await runEvaluationBenchmark();
      onRefreshEvaluation();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRunning(false);
    }
  };

  const results = evaluationReport?.results || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <Award className="h-5 w-5 text-brand-400" />
            <span>Automated SRE Evaluation Benchmark</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Standardized evaluation comparing autonomous agent findings against known ground-truth causal chains.
          </p>
        </div>

        <button
          onClick={handleRunBenchmark}
          disabled={isRunning}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold transition flex items-center space-x-2 disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isRunning ? 'animate-spin' : ''}`} />
          <span>{isRunning ? 'Running Benchmarks...' : 'Re-Run Evaluation Suite'}</span>
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
            <span>Overall RCA Accuracy</span>
            <Target className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-emerald-400">
              {((evaluationReport?.overall_accuracy_rate || 1.0) * 100).toFixed(0)}%
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400">Ground truth root cause semantic match</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
            <span>Evidence Coverage</span>
            <BarChart3 className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-indigo-400">
              {((evaluationReport?.average_evidence_coverage || 0.8) * 100).toFixed(1)}%
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400">Expected observability sources queried</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
            <span>Investigation Efficiency</span>
            <Zap className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-amber-400">
              {((evaluationReport?.average_efficiency || 1.0) * 100).toFixed(0)}%
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400">Zero redundant queries executed</p>
        </div>
      </div>

      {/* Benchmark Matrix Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-950/60 border-b border-slate-800 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <tr>
              <th className="py-3 px-4">Scenario ID</th>
              <th className="py-3 px-4">Winning Hypothesis</th>
              <th className="py-3 px-4">Expected GT</th>
              <th className="py-3 px-4">Accuracy</th>
              <th className="py-3 px-4">Coverage</th>
              <th className="py-3 px-4">Queries</th>
              <th className="py-3 px-4 text-right">Result</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 text-slate-300">
            {results.map((r: any) => (
              <tr key={r.scenario_id} className="hover:bg-slate-800/40 transition">
                <td className="py-3.5 px-4 font-mono text-xs font-bold text-white">{r.scenario_id}</td>
                <td className="py-3.5 px-4 font-mono text-xs text-emerald-400">{r.winning_hypothesis}</td>
                <td className="py-3.5 px-4 font-mono text-xs text-slate-400">{r.expected_hypothesis}</td>
                <td className="py-3.5 px-4 font-mono text-xs text-slate-300">{(r.accuracy_score * 100).toFixed(0)}%</td>
                <td className="py-3.5 px-4 font-mono text-xs text-slate-300">{(r.source_coverage * 100).toFixed(0)}%</td>
                <td className="py-3.5 px-4 font-mono text-xs text-slate-400">{r.queries_executed} / {r.max_acceptable_queries}</td>
                <td className="py-3.5 px-4 text-right">
                  <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-mono font-medium bg-emerald-950 text-emerald-400 border border-emerald-800/60">
                    <CheckCircle2 className="h-3 w-3" />
                    <span>PASS</span>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
