import { useEffect } from 'react';
import { useSimulationStore } from '@/store/useSimulationStore';
import AppLayout from '@/components/shared/AppLayout';
import DashboardView from '@/components/dashboard/DashboardView';
import SimulationView from '@/components/simulation/SimulationView';
import ResultsView from '@/components/results/ResultsView';
import DocsView from '@/components/docs/DocsView';

function App() {
  const { activeTab } = useSimulationStore();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key >= '1' && e.key <= '4') {
        useSimulationStore.getState().setActiveTab(parseInt(e.key) - 1);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <AppLayout>
      {activeTab === 0 && <DashboardView />}
      {activeTab === 1 && <SimulationView />}
      {activeTab === 2 && <ResultsView />}
      {activeTab === 3 && <DocsView />}
    </AppLayout>
  );
}

export default App;
