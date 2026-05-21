import { create } from 'zustand';
import {
  type SimulationConfig,
  type MetricsSnapshot,
  type ValidationResult,
  type StructuralSignature,
  type ActivityEvent,
  type SimStatus,
  DEFAULT_CONFIG,
} from '@/types/simulation';

interface AppState {
  // Navigation
  activeTab: number;
  sidebarCollapsed: boolean;
  setActiveTab: (tab: number) => void;
  toggleSidebar: () => void;

  // Configuration
  config: SimulationConfig;
  updateConfig: (partial: Partial<SimulationConfig>) => void;
  resetConfig: () => void;

  // Simulation runtime state
  status: SimStatus;
  phi: number;
  currentMetrics: MetricsSnapshot | null;
  metricsHistory: MetricsSnapshot[];
  setStatus: (status: SimStatus) => void;
  setPhi: (phi: number) => void;
  setCurrentMetrics: (metrics: MetricsSnapshot) => void;
  addMetricsSnapshot: (snapshot: MetricsSnapshot) => void;
  clearMetrics: () => void;

  // Nucleation
  nucleationMap: Float64Array | null;
  setNucleationMap: (map: Float64Array | null) => void;

  // Results
  signature: StructuralSignature | null;
  validation: ValidationResult | null;
  setSignature: (sig: StructuralSignature | null) => void;
  setValidation: (val: ValidationResult | null) => void;

  // Activity log
  activityLog: ActivityEvent[];
  addLogEvent: (event: Omit<ActivityEvent, 'id' | 'timestamp'>) => void;
  clearLog: () => void;
}

let logCounter = 0;

export const useSimulationStore = create<AppState>((set) => ({
  // Navigation
  activeTab: 0,
  sidebarCollapsed: false,
  setActiveTab: (tab) => set({ activeTab: tab }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

  // Config
  config: { ...DEFAULT_CONFIG },
  updateConfig: (partial) =>
    set((s) => ({ config: { ...s.config, ...partial } })),
  resetConfig: () => set({ config: { ...DEFAULT_CONFIG } }),

  // Simulation
  status: 'idle',
  phi: 0,
  currentMetrics: null,
  metricsHistory: [],
  setStatus: (status) => set({ status }),
  setPhi: (phi) => set({ phi }),
  setCurrentMetrics: (metrics) => set({ currentMetrics: metrics }),
  addMetricsSnapshot: (snapshot) =>
    set((s) => ({
      metricsHistory: [...s.metricsHistory, snapshot],
      currentMetrics: snapshot,
    })),
  clearMetrics: () =>
    set({ metricsHistory: [], currentMetrics: null, phi: 0 }),

  // Nucleation
  nucleationMap: null,
  setNucleationMap: (map) => set({ nucleationMap: map }),

  // Results
  signature: null,
  validation: null,
  setSignature: (sig) => set({ signature: sig }),
  setValidation: (val) => set({ validation: val }),

  // Activity log
  activityLog: [],
  addLogEvent: (event) =>
    set((s) => ({
      activityLog: [
        {
          ...event,
          id: `evt-${++logCounter}`,
          timestamp: Date.now(),
        },
        ...s.activityLog,
      ].slice(0, 500),
    })),
  clearLog: () => set({ activityLog: [] }),
}));
