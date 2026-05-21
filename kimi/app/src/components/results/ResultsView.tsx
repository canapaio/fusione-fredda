import { useState, useMemo } from 'react';
import { useSimulationStore } from '@/store/useSimulationStore';
import { GUARDRAILS } from '@/types/simulation';
import { CheckCircle, XCircle, AlertTriangle, BarChart3, Shield } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import NucleationMap3D from './NucleationMap3D';
import PhaseTimelineCharts from './PhaseTimelineCharts';
import StructuralSignature from './StructuralSignature';

export default function ResultsView() {
  const { validation, nucleationMap, status } = useSimulationStore();

  if (status !== 'completed' && status !== 'failed' && !nucleationMap) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <BarChart3 size={48} style={{ color: 'var(--text-muted)' }} className="mb-4 opacity-50" />
        <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
          Nessun Risultato Disponibile
        </h2>
        <p className="text-sm max-w-md" style={{ color: 'var(--text-secondary)' }}>
          Esegui una simulazione dalla pagina "Simulazione" per generare risultati.
          I dati includeranno la mappa 3D di nucleazione, le timeline di fase e la firma strutturale.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 3D Nucleation Map */}
      <NucleationMap3D />

      {/* Phase Timeline Charts */}
      <PhaseTimelineCharts />

      {/* Bottom row: Structural Signature + Validation Flags */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <StructuralSignature />

        {/* Validation Flags */}
        <div className="card-base p-5">
          <div className="label-upper mb-4 flex items-center gap-2">
            <Shield size={12} />
            Flag di Validazione
          </div>
          <div className="grid grid-cols-2 gap-3">
            {validation ? (
              <>
                <ValidationFlagCard
                  label="π-Algebra Operazionale"
                  description="Tutte le operazioni usano algebra π-native"
                  passed={validation.piAlgebraOperational}
                />
                <ValidationFlagCard
                  label="Nessun t Nascosto"
                  description="Asse di integrazione esclusivamente φ"
                  passed={validation.noHiddenT}
                />
                <ValidationFlagCard
                  label="Readout Non Distruttivo"
                  description="Campionamento senza collasso di stato"
                  passed={validation.readoutNonDestructive}
                />
                <ValidationFlagCard
                  label="Guardrail Soddisfatti"
                  description={`Metriche stabili per ≥${GUARDRAILS.phiCyclesStable} cicli φ`}
                  passed={validation.guardrailsMet}
                />
              </>
            ) : (
              <>
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="rounded-lg p-4 animate-pulse" style={{ background: 'var(--bg-tertiary)' }}>
                    <div className="h-4 w-3/4 rounded" style={{ background: 'var(--border-subtle)' }} />
                  </div>
                ))}
              </>
            )}
          </div>
          {validation && (
            <div className="mt-4 pt-3 space-y-2 text-xs" style={{ color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)' }}>
              <div className="flex justify-between">
                <span>Semi di nucleazione trovati</span>
                <span className="metric-value" style={{ color: 'var(--accent-phase)' }}>
                  {validation.nucleationSeedsFound}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Cicli φ stabili</span>
                <span className="metric-value" style={{ color: 'var(--accent-phase)' }}>
                  {validation.stablePhiCycles}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Derived Energy (Optional) */}
      <DerivedEnergySection />
    </div>
  );
}

function ValidationFlagCard({ label, description, passed }: { label: string; description: string; passed: boolean }) {
  return (
    <div
      className="rounded-lg p-3 flex items-start gap-3"
      style={{
        background: passed ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
        border: `1px solid ${passed ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`,
      }}
    >
      {passed ? (
        <CheckCircle size={18} className="shrink-0 mt-0.5" style={{ color: 'var(--accent-valid)' }} />
      ) : (
        <XCircle size={18} className="shrink-0 mt-0.5" style={{ color: 'var(--accent-warn)' }} />
      )}
      <div>
        <div className="text-sm font-medium" style={{ color: passed ? 'var(--accent-valid)' : 'var(--accent-warn)' }}>
          {passed ? 'True' : 'False'}
        </div>
        <div className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>{label}</div>
        <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-secondary)' }}>{description}</div>
      </div>
    </div>
  );
}

function DerivedEnergySection() {
  const { metricsHistory, signature } = useSimulationStore();
  const [showEnergy, setShowEnergy] = useState(false);

  const energyData = useMemo(() => {
    if (!signature) return [];
    const kappa = 1.0;
    return metricsHistory.map((m) => ({
      phi: m.phi,
      energy: kappa * m.jpol * m.sigmaCn * Math.abs(signature.psiRX[0]) / (m.dratio + 1),
    }));
  }, [metricsHistory, signature]);

  return (
    <div className="card-base p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="label-upper flex items-center gap-2">
          <BarChart3 size={12} />
          Osservabile Energetico Derivato (Opzionale)
        </div>
        <button
          onClick={() => setShowEnergy(!showEnergy)}
          className="text-[11px] px-2 py-1 rounded"
          style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}
        >
          {showEnergy ? 'Nascondi' : 'Mostra'}
        </button>
      </div>
      <div
        className="rounded-lg p-3 mb-3 text-xs flex items-center gap-2"
        style={{ background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.15)', color: 'var(--accent-nuclear)' }}
      >
        <AlertTriangle size={14} />
        <strong>Disclaimer:</strong> E_π(φ) è un osservabile matematico — non energia fisica reale.
      </div>
      {showEnergy && energyData.length > 0 && (
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={energyData}>
            <defs>
              <linearGradient id="energyGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="phi" tickFormatter={(v: number) => `${(v / Math.PI).toFixed(1)}π`} tick={{ fontSize: 10, fill: '#3d3d5c' }} />
            <YAxis tick={{ fontSize: 10, fill: '#3d3d5c' }} />
            <Tooltip
              contentStyle={{ background: '#0a0a12', border: '1px solid #1a1a2e', borderRadius: '6px', fontSize: '11px' }}
              formatter={(value: number) => [value.toFixed(6), 'E_π']}
              labelFormatter={(label: number) => `φ=${(label / Math.PI).toFixed(2)}π`}
            />
            <Area type="monotone" dataKey="energy" stroke="#f59e0b" fill="url(#energyGrad)" strokeWidth={1.5} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
