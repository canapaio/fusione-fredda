export type MaterialNuclear = 'Ni' | 'Cu' | 'Fe' | 'Co' | 'Si' | 'SiN';
export type MaterialCarrier = 'perovskite' | 'idruro' | 'serpentino';
export type SimStatus = 'idle' | 'running' | 'paused' | 'completed' | 'failed';

export interface MaterialNuclearData {
  id: MaterialNuclear;
  name: string;
  type: string;
  drogabilita: string;
  risonanza: string;
  deltaPhi: number;
  sigmaCn: number;
  jpolMin: number;
  jpolMax: number;
  fattibilita: string;
  color: string;
}

export interface MaterialCarrierData {
  id: MaterialCarrier;
  name: string;
  type: string;
  meccanismo: string;
  stabilita: string;
  compatibilita: string;
}

export interface SimulationConfig {
  materialNuclear: MaterialNuclear;
  materialCarrier: MaterialCarrier;
  hdRatio: number;
  temperatureRange: [number, number];
  gridSize: [number, number, number];
  beta: number;
  deltaZ: number;
  etaProgFrequencies: number[];
  gamma0: number;
  gammaLambda: number;
  jpolThreshold: number;
  J0: number;
  f0: number;
  sigmaJ: number;
  Dphi: number;
  kappa: number;
  storeEvery: number;
}

export interface MetricsSnapshot {
  phi: number;
  sigmaCn: number;
  dratio: number;
  jpol: number;
  rhopol: number;
  cvert: number;
}

export interface SimulationState {
  phi: number;
  theta: Float64Array;
  nHD: Float64Array;
  status: SimStatus;
}

export interface ValidationResult {
  piAlgebraOperational: boolean;
  noHiddenT: boolean;
  readoutNonDestructive: boolean;
  guardrailsMet: boolean;
  nucleationSeedsFound: number;
  stablePhiCycles: number;
}

export interface StructuralSignature {
  correlations: number[];
  divergence: number;
  intensity: number;
  sigmaCn: number;
  psiRX: Float64Array;
}

export interface ActivityEvent {
  id: string;
  phi: number;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: number;
}

export interface WorkerMessage {
  type: 'SNAPSHOT' | 'COMPLETE' | 'GUARDRAIL_FAIL' | 'PROGRESS' | 'LOG';
  payload: Record<string, unknown>;
}

export interface WorkerInput {
  type: 'INIT' | 'STEP' | 'RESET' | 'CONFIG';
  payload?: Record<string, unknown>;
}

export const MATERIALS_NUCLEAR: Record<MaterialNuclear, MaterialNuclearData> = {
  Ni: { id: 'Ni', name: 'Nichel (Ni)', type: 'Conduttore', drogabilita: 'Altissima', risonanza: '15-80 MHz / 12-40 THz', deltaPhi: 0.45, sigmaCn: 0.082, jpolMin: 0.6, jpolMax: 0.8, fattibilita: 'Alta', color: '#00f0c8' },
  Cu: { id: 'Cu', name: 'Rame (Cu)', type: 'Conduttore', drogabilita: 'Buona', risonanza: '12-60 MHz / 10-35 THz', deltaPhi: 0.41, sigmaCn: 0.076, jpolMin: 0.5, jpolMax: 0.7, fattibilita: 'Alta', color: '#f59e0b' },
  Fe: { id: 'Fe', name: 'Ferro (Fe)', type: 'Conduttore/Magnetico', drogabilita: 'Eccellente', risonanza: '25-120 MHz / 18-50 THz', deltaPhi: 0.55, sigmaCn: 0.094, jpolMin: 0.75, jpolMax: 0.95, fattibilita: 'Eccellente', color: '#ef4444' },
  Co: { id: 'Co', name: 'Cobalto (Co)', type: 'Conduttore/Magnetico', drogabilita: 'Eccellente', risonanza: '28-130 MHz / 20-55 THz', deltaPhi: 0.58, sigmaCn: 0.098, jpolMin: 0.8, jpolMax: 1.0, fattibilita: 'Massima', color: '#a855f7' },
  Si: { id: 'Si', name: 'Silicio (Si)', type: 'Semiconduttore', drogabilita: 'Droguabile', risonanza: 'Waveguide TE/TM', deltaPhi: 0.48, sigmaCn: 0.085, jpolMin: 0.6, jpolMax: 0.8, fattibilita: 'Alta', color: '#3b82f6' },
  SiN: { id: 'SiN', name: 'Nitruro di Silicio (SiN)', type: 'Semiconduttore/Iso', drogabilita: 'Stabile', risonanza: 'Polarizzazione TE/TM', deltaPhi: 0.46, sigmaCn: 0.088, jpolMin: 0.7, jpolMax: 0.9, fattibilita: 'Ottima', color: '#10b981' },
};

export const MATERIALS_CARRIER: Record<MaterialCarrier, MaterialCarrierData> = {
  perovskite: { id: 'perovskite', name: 'Perovskiti protoniche (BaZrO₃:Y)', type: 'Ceramico conduttore', meccanismo: 'Conduzione protonica attivata da φ', stabilita: '>1000°C', compatibilita: 'Eccellente' },
  idruro: { id: 'idruro', name: 'Idruri interstiziali (TiH₂, ZrH₂)', type: 'Metallico', meccanismo: 'Rilascio attivato da vibrazioni reticolari', stabilita: '~800°C', compatibilita: 'Alta' },
  serpentino: { id: 'serpentino', name: 'Silicati nanostrutturati (Serpentino)', type: 'Minerale', meccanismo: 'Deidrossilazione per step di fase', stabilita: '>800°C', compatibilita: 'Ottima' },
};

export const GUARDRAILS = {
  sigmaCnMin: 0.075,
  dratioMin: 15,
  jpolMin: 0.4,
  rhopolMin: 0.5,
  betaMin: 0.1,
  deltaZMin: 0.15,
  phiCyclesStable: 3,
  dphi: 0.01,
  phiMax: 6 * Math.PI,
};

export const DEFAULT_CONFIG: SimulationConfig = {
  materialNuclear: 'Ni',
  materialCarrier: 'serpentino',
  hdRatio: 1.4,
  temperatureRange: [600, 1200],
  gridSize: [20, 20, 20],
  beta: 0.2,
  deltaZ: 0.15,
  etaProgFrequencies: [15, 30, 45, 75, 105],
  gamma0: 1.0,
  gammaLambda: 0.5,
  jpolThreshold: 0.4,
  J0: 1.0,
  f0: 5.0,
  sigmaJ: 0.1,
  Dphi: 0.1,
  kappa: 0.1,
  storeEvery: 2,
};
