import { useSimulationStore } from '@/store/useSimulationStore';
import { CheckCircle, XCircle } from 'lucide-react';
import { GUARDRAILS } from '@/types/simulation';

export default function Header() {
  const { phi, status, validation } = useSimulationStore();
  const phiMax = GUARDRAILS.phiMax;
  const progress = Math.min(1, phi / phiMax);
  const phiDisplay = (phi / Math.PI).toFixed(2);

  const statusLabels: Record<string, { text: string; color: string }> = {
    idle: { text: 'Inattiva', color: 'var(--text-muted)' },
    running: { text: 'In Esecuzione', color: 'var(--accent-phase)' },
    paused: { text: 'Pausa', color: 'var(--accent-nuclear)' },
    completed: { text: 'Completata', color: 'var(--accent-valid)' },
    failed: { text: 'Fallita', color: 'var(--accent-warn)' },
  };

  const s = statusLabels[status] || statusLabels.idle;

  return (
    <header
      className="h-16 flex items-center justify-between px-6 shrink-0 z-50"
      style={{
        background: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border-subtle)',
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'var(--accent-phase)' }}>
          <span className="text-lg font-bold" style={{ color: 'var(--bg-primary)' }}>π</span>
        </div>
        <div>
          <h1 className="text-sm font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
            BASE π
          </h1>
          <p className="text-[10px] tracking-widest uppercase" style={{ color: 'var(--text-muted)' }}>
            Simulazione Fusione
          </p>
        </div>
      </div>

      {/* φ Progress */}
      <div className="flex items-center gap-4 flex-1 justify-center max-w-lg">
        <div className="flex items-center gap-2">
          <span className="label-upper">φ</span>
          <span className="metric-value text-lg" style={{ color: 'var(--accent-phase)' }}>
            {phiDisplay}π
          </span>
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>/ 6π</span>
        </div>
        <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{
              width: `${progress * 100}%`,
              background: 'linear-gradient(90deg, var(--accent-phase), var(--accent-coherence))',
              boxShadow: '0 0 10px rgba(0, 240, 200, 0.3)',
            }}
          />
        </div>
        <div
          className="px-2.5 py-0.5 rounded-full text-[11px] font-medium"
          style={{
            background: `${s.color}15`,
            color: s.color,
            border: `1px solid ${s.color}30`,
          }}
        >
          {s.text}
        </div>
      </div>

      {/* Validation Flags */}
      <div className="flex items-center gap-2">
        {[
          { key: 'piAlgebraOperational', label: 'π-Alg' },
          { key: 'noHiddenT', label: 'No-t' },
          { key: 'readoutNonDestructive', label: 'ND-RO' },
          { key: 'guardrailsMet', label: 'Guard' },
        ].map(({ key, label }) => {
          const passed = validation ? (validation as unknown as Record<string, boolean>)[key] : false;
          return (
            <div
              key={key}
              className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium"
              style={{
                background: passed ? 'rgba(16, 185, 129, 0.1)' : 'rgba(61, 61, 92, 0.3)',
                color: passed ? 'var(--accent-valid)' : 'var(--text-muted)',
                border: `1px solid ${passed ? 'rgba(16, 185, 129, 0.2)' : 'var(--border-subtle)'}`,
              }}
              title={key}
            >
              {passed ? <CheckCircle size={10} /> : <XCircle size={10} />}
              {label}
            </div>
          );
        })}
      </div>
    </header>
  );
}
