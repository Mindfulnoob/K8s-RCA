import React from 'react';
import { Shield, Play, RotateCcw, Activity, Layers, GitCommit, FileText, CheckCircle2 } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  clusterStatus: any;
  onOpenNewModal: () => void;
  onOpenScenarioModal: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  clusterStatus,
  onOpenNewModal,
  onOpenScenarioModal,
}) => {
  const tabs = [
    { id: 'dashboard', label: 'Investigations', icon: Layers },
    { id: 'live', label: 'Live Investigation', icon: Activity },
    { id: 'hypotheses', label: 'Hypothesis Graph', icon: GitCommit },
    { id: 'timeline', label: 'Incident Timeline', icon: Activity },
    { id: 'rca', label: 'RCA Report', icon: FileText },
    { id: 'replay', label: 'Step Replay', icon: RotateCcw },
    { id: 'evaluation', label: 'Evaluation', icon: CheckCircle2 },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
            <div className="h-9 w-9 bg-brand-600 rounded-lg flex items-center justify-center shadow-lg shadow-brand-500/20">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-white tracking-tight">KubeRCA</span>
                <span className="text-xs px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 font-mono font-medium border border-brand-500/20">AGENT</span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">Autonomous Kubernetes Root-Cause Analysis</p>
            </div>
          </div>

          {/* Nav Tabs */}
          <nav className="hidden md:flex space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-800 text-brand-400 border border-slate-700'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Actions & Status */}
          <div className="flex items-center space-x-3">
            {/* Security Sandbox Badge */}
            <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-950/40 text-emerald-400 text-xs font-mono border border-emerald-800/50">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>READ-ONLY SANDBOX</span>
            </div>

            {/* Launch Scenario Button */}
            <button
              onClick={onOpenScenarioModal}
              className="px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium border border-slate-700 transition flex items-center space-x-1.5"
            >
              <Play className="h-3.5 w-3.5 text-amber-400" />
              <span>Scenarios</span>
            </button>

            {/* New Investigation Button */}
            <button
              onClick={onOpenNewModal}
              className="px-3.5 py-1.5 rounded-md bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium shadow-sm transition flex items-center space-x-1.5"
            >
              <span>+ New Investigation</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
