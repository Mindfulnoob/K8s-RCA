import React, { useState } from 'react';
import { FileText, Copy, Check, ShieldCheck, AlertCircle, ArrowRight, CornerDownRight, HelpCircle, Activity } from 'lucide-react';
import { RCAReport } from '../types';

interface RCAReportViewProps {
  report: RCAReport | null;
}

export const RCAReportView: React.FC<RCAReportViewProps> = ({ report }) => {
  const [copied, setCopied] = useState(false);

  if (!report) {
    return (
      <div className="text-center py-20 bg-slate-900 border border-slate-800 rounded-xl">
        <p className="text-slate-400">No RCA report generated yet. Run an investigation to synthesize root-cause analysis.</p>
      </div>
    );
  }

  const handleCopyMarkdown = () => {
    const md = `
# ROOT CAUSE ANALYSIS (RCA) REPORT

**Incident:** ${report.incident}
**Generated At:** ${new Date(report.generated_at).toLocaleString()}
**Confidence:** ${report.confidence_score}%

---

## 1. ROOT CAUSE
${report.root_cause}

## 2. CONFIDENCE & VALIDATION
${report.confidence_explanation}

## 3. MULTI-SOURCE CORRELATION
${report.multi_source_correlation_summary || 'Correlated across independent observability telemetry.'}

## 4. CAUSAL CHAIN
${report.causal_chain?.nodes?.map((n) => `- [${n.type}] ${n.label}: ${n.description}`).join('\n')}

## 5. OBSERVED FACTS
${report.observed_facts?.map((f) => `- ${f}`).join('\n')}

## 6. ALTERNATIVE EXPLANATIONS CONSIDERED
${report.alternative_explanations?.map((a) => `- **${a.hypothesis_id}:** ${a.description}\n  *Weakened:* ${a.reason_weakened_or_rejected}`).join('\n')}

## 7. UNKNOWNS & AMBIGUITIES
${report.unknowns_and_ambiguities?.map((u) => `- ${u}`).join('\n')}

## 8. RECOMMENDED ACTIONS & MITIGATIONS
${report.recommended_mitigation?.map((m) => `- [ ] ${m}`).join('\n')}
    `.trim();

    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Executive Summary Card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-brand-950/40 border border-brand-500/30 rounded-xl p-6 shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <span className="text-xs font-mono uppercase tracking-wider text-brand-400 font-bold px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">
              IDENTIFIED ROOT CAUSE
            </span>
            <h1 className="text-2xl font-bold text-white mt-2 leading-snug">
              {report.root_cause}
            </h1>
          </div>

          <div className="flex items-center space-x-3">
            <div className="bg-slate-950/80 p-3 rounded-lg border border-slate-800 text-right">
              <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 block">CONFIDENCE</span>
              <span className="text-3xl font-bold font-mono text-emerald-400">{report.confidence_score}%</span>
            </div>
            <button
              onClick={handleCopyMarkdown}
              className="p-3 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition flex items-center space-x-1.5"
            >
              {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
              <span>{copied ? 'Copied!' : 'Export MD'}</span>
            </button>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-800/80">
          <p className="text-xs text-slate-300 font-mono leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
            {report.confidence_explanation}
          </p>
        </div>
      </div>

      {/* Multi-Source Correlation Banner */}
      {report.multi_source_correlation_summary && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-start space-x-3">
          <Activity className="h-5 w-5 text-indigo-400 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Multi-Source Correlation Synthesis</h3>
            <p className="text-xs text-slate-300 font-mono mt-1">{report.multi_source_correlation_summary}</p>
          </div>
        </div>
      )}

      {/* Causal Chain Visualization */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
          Directed Causal Chain (DAG)
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {report.causal_chain?.nodes?.map((node, idx) => {
            const isRoot = node.type === 'ROOT_CAUSE';
            const isTrigger = node.type === 'TRIGGER';
            const isContributor = node.type === 'CONTRIBUTING_FACTOR';

            return (
              <div
                key={node.id}
                className={`p-4 rounded-xl border relative flex flex-col justify-between ${
                  isRoot
                    ? 'bg-rose-950/30 border-rose-600/50 ring-1 ring-rose-500/20'
                    : isTrigger
                    ? 'bg-amber-950/30 border-amber-600/50'
                    : isContributor
                    ? 'bg-purple-950/30 border-purple-600/50'
                    : 'bg-slate-950 border-slate-800'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                      {node.type.replace('_', ' ')}
                    </span>
                    <span className="text-[11px] font-mono text-slate-500">#{idx + 1}</span>
                  </div>
                  <h4 className="font-bold text-white text-sm">{node.label}</h4>
                  <p className="text-xs text-slate-300 mt-1">{node.description}</p>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-800/80 text-[11px] font-mono text-slate-400 truncate">
                  Component: {node.component}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Two Column Section: Observed Facts & Alternative Explanations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Observed Facts */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3">
            Ground-Truth Observed Facts
          </h3>
          <ul className="space-y-2 text-xs text-slate-200 font-mono">
            {report.observed_facts?.map((fact, idx) => (
              <li key={idx} className="bg-slate-950 p-2.5 rounded-md border border-slate-800 flex items-start space-x-2">
                <span className="text-brand-400 font-bold">•</span>
                <span>{fact}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Alternative Explanations */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3">
            Alternative Explanations & Rejection Reasons
          </h3>
          <div className="space-y-2 text-xs">
            {report.alternative_explanations?.map((alt) => (
              <div key={alt.hypothesis_id} className="bg-slate-950 p-3 rounded-md border border-slate-800">
                <div className="flex items-center justify-between font-mono mb-1">
                  <span className="font-bold text-slate-200">{alt.hypothesis_id}: {alt.description}</span>
                  <span className="text-slate-500">{(alt.residual_probability * 100).toFixed(1)}% residual</span>
                </div>
                <p className="text-slate-400 font-mono text-[11px] mt-1 text-amber-300/80">
                  {alt.reason_weakened_or_rejected}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Unknowns and Recommended Mitigations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
            <HelpCircle className="h-4 w-4 text-amber-400" />
            <span>Unknowns & Ambiguities</span>
          </h3>
          <ul className="space-y-2 text-xs text-slate-300 font-mono">
            {report.unknowns_and_ambiguities?.map((unk, idx) => (
              <li key={idx} className="bg-slate-950 p-2.5 rounded-md border border-slate-800">
                {unk}
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-1.5">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>Recommended Mitigations</span>
          </h3>
          <ul className="space-y-2 text-xs text-emerald-300 font-mono">
            {report.recommended_mitigation?.map((mit, idx) => (
              <li key={idx} className="bg-slate-950 p-2.5 rounded-md border border-slate-800 flex items-start space-x-2">
                <span className="text-emerald-500 font-bold">✓</span>
                <span>{mit}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
