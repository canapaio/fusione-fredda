import { useSimulationStore } from '@/store/useSimulationStore';
import {
  LayoutDashboard,
  Play,
  BarChart3,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Pause,
  RotateCcw,
  Settings,
} from 'lucide-react';
import { useCallback, useRef, useEffect } from 'react';

const tabs = [
  { id: 0, label: 'Dashboard', icon: LayoutDashboard },
  { id: 1, label: 'Simulazione', icon: Settings },
  { id: 2, label: 'Risultati', icon: BarChart3 },
  { id: 3, label: 'Documentazione', icon: BookOpen },
];

export default function Sidebar() {
  const { activeTab, setActiveTab, sidebarCollapsed, toggleSidebar, status, setStatus, clearMetrics } =
    useSimulationStore();
  const workerRef = useRef<Worker | null>(null);

  // Initialize worker
  useEffect(() => {
    const worker = new Worker(new URL('@/workers/simulation.worker.ts', import.meta.url), {
      type: 'module',
    });
    workerRef.current = worker;

    worker.onmessage = (e) => {
      const { type, payload } = e.data;
      const store = useSimulationStore.getState();

      switch (type) {
        case 'INIT_DONE':
          store.addLogEvent({
            phi: 0,
            type: 'info',
            message: `Simulazione inizializzata: griglia ${payload.gridSize.join('×')}, ${payload.nnz} accoppiamenti`,
          });
          break;
        case 'SNAPSHOT':
          store.setPhi(payload.metrics.phi);
          store.addMetricsSnapshot(payload.metrics);
          break;
        case 'PROGRESS':
          store.setPhi(payload.phi);
          break;
        case 'GUARDRAIL_FAIL': {
          store.setStatus('failed');
          const m = payload.metrics;
          store.addLogEvent({
            phi: payload.phi,
            type: 'error',
            message: `Guardrail fallito: σ(Cn)=${m.sigmaCn.toFixed(3)}, Dratio=${m.dratio.toFixed(1)}, Jpol=${m.jpol.toFixed(3)}`,
          });
          break;
        }
        case 'COMPLETE': {
          store.setStatus('completed');
          store.setPhi(payload.phi);
          store.setNucleationMap(new Float64Array(payload.nucleationMap));
          store.setSignature(payload.signature);
          store.setValidation(payload.validation);
          store.addLogEvent({
            phi: payload.phi,
            type: 'success',
            message: `Simulazione completata: ${payload.validation.nucleationSeedsFound} semi di nucleazione trovati`,
          });
          break;
        }
      }
    };

    return () => worker.terminate();
  }, []);

  const handleInit = useCallback(() => {
    const store = useSimulationStore.getState();
    const cfg = store.config;
    workerRef.current?.postMessage({
      type: 'INIT',
      payload: { config: cfg },
    });
    store.setStatus('idle');
    store.clearMetrics();
    store.setNucleationMap(null);
    store.setSignature(null);
    store.setValidation(null);
    store.addLogEvent({
      phi: 0,
      type: 'info',
      message: 'Inizializzazione richiesta...',
    });
  }, []);

  const handleStart = useCallback(() => {
    const store = useSimulationStore.getState();
    if (store.status === 'idle' || store.status === 'paused') {
      store.setStatus('running');
      store.addLogEvent({
        phi: store.phi,
        type: 'info',
        message: 'Simulazione avviata',
      });
      // Run batches of steps
      const runBatch = () => {
        const s = useSimulationStore.getState();
        if (s.status !== 'running') return;
        workerRef.current?.postMessage({ type: 'STEP', payload: { steps: 50 } });
        requestAnimationFrame(runBatch);
      };
      runBatch();
    }
  }, []);

  const handlePause = useCallback(() => {
    setStatus('paused');
    useSimulationStore.getState().addLogEvent({
      phi: useSimulationStore.getState().phi,
      type: 'warning',
      message: 'Simulazione in pausa',
    });
  }, [setStatus]);

  const handleReset = useCallback(() => {
    setStatus('idle');
    clearMetrics();
    workerRef.current?.postMessage({ type: 'RESET' });
    useSimulationStore.getState().addLogEvent({
      phi: 0,
      type: 'info',
      message: 'Simulazione resettata',
    });
  }, [setStatus, clearMetrics]);

  return (
    <aside
      className="fixed left-0 top-16 bottom-0 flex flex-col z-40 transition-all duration-300"
      style={{
        width: sidebarCollapsed ? '64px' : '240px',
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-subtle)',
      }}
    >
      {/* Collapse toggle */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-4 w-6 h-6 rounded-full flex items-center justify-center z-50"
        style={{
          background: 'var(--bg-tertiary)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {sidebarCollapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
      </button>

      {/* Navigation */}
      <nav className="flex-1 pt-4 px-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 transition-all duration-200 relative"
              style={{
                background: isActive ? 'rgba(0, 240, 200, 0.08)' : 'transparent',
                color: isActive ? 'var(--accent-phase)' : 'var(--text-secondary)',
              }}
            >
              {isActive && (
                <div
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full"
                  style={{ background: 'var(--accent-phase)' }}
                />
              )}
              <Icon size={18} />
              {!sidebarCollapsed && (
                <span className="text-sm font-medium">{tab.label}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Simulation controls - only on Simulation tab */}
      {activeTab === 1 && (
        <div className="px-3 pb-4">
          {!sidebarCollapsed && (
            <div className="label-upper mb-2 text-center">Controlli</div>
          )}
          <div className={`flex ${sidebarCollapsed ? 'flex-col' : 'flex-row'} gap-1.5`}>
            <button
              onClick={handleInit}
              className="flex-1 btn-secondary flex items-center justify-center py-2"
              title="Inizializza"
            >
              <RotateCcw size={14} />
            </button>
            {status === 'running' ? (
              <button
                onClick={handlePause}
                className="flex-1 btn-primary flex items-center justify-center py-2"
                style={{ background: 'var(--accent-nuclear)' }}
                title="Pausa"
              >
                <Pause size={14} />
              </button>
            ) : (
              <button
                onClick={handleStart}
                className="flex-1 btn-primary flex items-center justify-center py-2"
                title="Avvia"
              >
                <Play size={14} />
              </button>
            )}
            <button
              onClick={handleReset}
              className="flex-1 flex items-center justify-center py-2 rounded-lg"
              style={{
                border: '1px solid var(--accent-warn)',
                color: 'var(--accent-warn)',
                background: 'transparent',
              }}
              title="Reset"
            >
              <RotateCcw size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      {!sidebarCollapsed && (
        <div className="px-4 pb-4 text-center">
          <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
            v1.0-π-native
          </p>
        </div>
      )}
    </aside>
  );
}
