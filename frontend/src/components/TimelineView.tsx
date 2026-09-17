import React, { useState } from 'react';
import { Clock, AlertTriangle, AlertCircle, Info, Filter, Server } from 'lucide-react';
import { TimelineEvent } from '../types';

interface TimelineViewProps {
  timeline: TimelineEvent[];
}

export const TimelineView: React.FC<TimelineViewProps> = ({ timeline }) => {
  const [filterSource, setFilterSource] = useState<string>('ALL');

  const sources = ['ALL', ...Array.from(new Set(timeline.map((e) => e.source)))];
  const filteredEvents =
    filterSource === 'ALL' ? timeline : timeline.filter((e) => e.source === filterSource);

  const getSeverityIcon = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return <AlertCircle className="h-4 w-4 text-rose-400" />;
      case 'WARNING':
        return <AlertTriangle className="h-4 w-4 text-amber-400" />;
      default:
        return <Info className="h-4 w-4 text-indigo-400" />;
    }
  };

  const getSourceBadgeColor = (source: string) => {
    switch (source) {
      case 'Kubernetes':
        return 'bg-blue-950/60 text-blue-400 border-blue-800/40';
      case 'Prometheus':
        return 'bg-orange-950/60 text-orange-400 border-orange-800/40';
      case 'Loki':
        return 'bg-amber-950/60 text-amber-400 border-amber-800/40';
      case 'Jaeger':
        return 'bg-emerald-950/60 text-emerald-400 border-emerald-800/40';
      case 'Deployment':
        return 'bg-purple-950/60 text-purple-400 border-purple-800/40';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Filter */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white">Multi-Source Incident Timeline</h2>
          <p className="text-xs text-slate-400 mt-1">
            Normalized chronological event sequence correlating Kubernetes events, metric anomalies, log alerts, and rollouts.
          </p>
        </div>

        {/* Source Filter Tabs */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 sm:pb-0">
          <Filter className="h-3.5 w-3.5 text-slate-500 mr-1" />
          {sources.map((src) => (
            <button
              key={src}
              onClick={() => setFilterSource(src)}
              className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition ${
                filterSource === src
                  ? 'bg-brand-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {src}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline River */}
      <div className="relative pl-6 border-l border-slate-800 space-y-6">
        {filteredEvents.map((evt, idx) => (
          <div key={evt.id || idx} className="relative group">
            {/* Timeline Dot */}
            <div className="absolute -left-[31px] top-1.5 h-4 w-4 rounded-full bg-slate-900 border-2 border-slate-700 flex items-center justify-center group-hover:border-brand-500 transition">
              <span className="h-1.5 w-1.5 rounded-full bg-slate-400 group-hover:bg-brand-400"></span>
            </div>

            {/* Event Box */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm group-hover:border-slate-700 transition">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center space-x-2">
                  {getSeverityIcon(evt.severity)}
                  <span className="font-semibold text-white text-sm">{evt.title}</span>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${getSourceBadgeColor(evt.source)}`}>
                    {evt.source}
                  </span>
                </div>
                <div className="flex items-center space-x-1 text-xs font-mono text-slate-400">
                  <Clock className="h-3.5 w-3.5" />
                  <span>{new Date(evt.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>

              <p className="mt-2 text-xs text-slate-300 font-mono bg-slate-950 p-2.5 rounded-md border border-slate-800/80">
                {evt.description}
              </p>

              {evt.component && (
                <div className="mt-2 flex items-center space-x-2 text-[11px] text-slate-500 font-mono">
                  <Server className="h-3 w-3" />
                  <span>Component: {evt.component}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
