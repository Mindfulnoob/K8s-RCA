import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Dashboard } from './components/Dashboard';
import { LiveInvestigationView } from './components/LiveInvestigationView';
import { HypothesisGraph } from './components/HypothesisGraph';
import { TimelineView } from './components/TimelineView';
import { RCAReportView } from './components/RCAReportView';
import { ReplayViewer } from './components/ReplayViewer';
import { EvaluationDashboard } from './components/EvaluationDashboard';
import { NewInvestigationModal } from './components/NewInvestigationModal';
import { ScenarioLauncherModal } from './components/ScenarioLauncherModal';
import {
  fetchClusterStatus,
  fetchScenarios,
  fetchInvestigations,
  fetchInvestigation,
  startInvestigation,
  stepInvestigation,
  triggerScenario,
  fetchEvaluationReport,
} from './api';
import { InvestigationState, Scenario } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [investigations, setInvestigations] = useState<any[]>([]);
  const [currentInvestigation, setCurrentInvestigation] = useState<InvestigationState | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [clusterStatus, setClusterStatus] = useState<any>(null);
  const [evaluationReport, setEvaluationReport] = useState<any>(null);

  const [isNewModalOpen, setIsNewModalOpen] = useState<boolean>(false);
  const [isScenarioModalOpen, setIsScenarioModalOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const [status, scList, invList, evalRep] = await Promise.all([
        fetchClusterStatus().catch(() => null),
        fetchScenarios().catch(() => []),
        fetchInvestigations().catch(() => []),
        fetchEvaluationReport().catch(() => null),
      ]);

      setClusterStatus(status);
      setScenarios(scList);
      setInvestigations(invList);
      setEvaluationReport(evalRep);

      if (invList && invList.length > 0 && !currentInvestigation) {
        const fullState = await fetchInvestigation(invList[0].id);
        setCurrentInvestigation(fullState);
      }
    } catch (err) {
      console.error('Failed to load initial data:', err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectInvestigation = async (id: string) => {
    try {
      setIsLoading(true);
      const state = await fetchInvestigation(id);
      setCurrentInvestigation(state);
      setActiveTab('live');
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartInvestigation = async (params: {
    incident: string;
    namespace: string;
    provider_type: string;
    max_steps: number;
  }) => {
    try {
      setIsLoading(true);
      const newState = await startInvestigation(params);
      setCurrentInvestigation(newState);
      setIsNewModalOpen(false);
      setActiveTab('live');
      await loadData();
    } catch (e) {
      console.error('Error starting investigation:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStepInvestigation = async () => {
    if (!currentInvestigation) return;
    try {
      setIsLoading(true);
      await stepInvestigation(currentInvestigation.id);
      const updated = await fetchInvestigation(currentInvestigation.id);
      setCurrentInvestigation(updated);
      await loadData();
    } catch (e) {
      console.error('Error stepping investigation:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTriggerScenario = async (scenarioId: string) => {
    try {
      setIsLoading(true);
      await triggerScenario(scenarioId);
      const sc = scenarios.find((s) => s.id === scenarioId);
      if (sc) {
        const newState = await startInvestigation({
          incident: sc.prompt,
          namespace: 'default',
          provider_type: 'mock',
          max_steps: 8,
        });
        setCurrentInvestigation(newState);
        setActiveTab('live');
        await loadData();
      }
    } catch (e) {
      console.error('Error triggering scenario:', e);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        clusterStatus={clusterStatus}
        onOpenNewModal={() => setIsNewModalOpen(true)}
        onOpenScenarioModal={() => setIsScenarioModalOpen(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <Dashboard
            investigations={investigations}
            currentInvestigation={currentInvestigation}
            scenarios={scenarios}
            clusterStatus={clusterStatus}
            onSelectInvestigation={handleSelectInvestigation}
            onTriggerScenario={handleTriggerScenario}
            onNewInvestigation={() => setIsNewModalOpen(true)}
          />
        )}

        {activeTab === 'live' && (
          <LiveInvestigationView
            investigation={currentInvestigation}
            onStepInvestigation={handleStepInvestigation}
            isLoading={isLoading}
          />
        )}

        {activeTab === 'hypotheses' && (
          <HypothesisGraph hypotheses={currentInvestigation?.hypotheses || []} />
        )}

        {activeTab === 'timeline' && (
          <TimelineView timeline={currentInvestigation?.timeline || []} />
        )}

        {activeTab === 'rca' && (
          <RCAReportView report={currentInvestigation?.rca_report || null} />
        )}

        {activeTab === 'replay' && (
          <ReplayViewer replayFrames={currentInvestigation?.replay_frames || []} />
        )}

        {activeTab === 'evaluation' && (
          <EvaluationDashboard
            evaluationReport={evaluationReport}
            onRefreshEvaluation={loadData}
          />
        )}
      </main>

      <footer className="border-t border-slate-900 py-4 text-center text-xs font-mono text-slate-500">
        KubeRCA Agent • Autonomous Multi-Source Root Cause Analysis for Kubernetes • Read-Only Sandbox Protected
      </footer>

      {/* Modals */}
      <NewInvestigationModal
        isOpen={isNewModalOpen}
        onClose={() => setIsNewModalOpen(false)}
        onStart={handleStartInvestigation}
        isLoading={isLoading}
      />

      <ScenarioLauncherModal
        isOpen={isScenarioModalOpen}
        onClose={() => setIsScenarioModalOpen(false)}
        scenarios={scenarios}
        onTriggerScenario={handleTriggerScenario}
        isLoading={isLoading}
      />
    </div>
  );
};
