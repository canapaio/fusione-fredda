import { useSimulationStore } from '@/store/useSimulationStore';
import { GUARDRAILS } from '@/types/simulation';
import { Activity, TrendingUp, Shield, GitBranch } from 'lucide-react';

function Sparkline({ data, color, height = 24 }: { data: number[]; color: string; height?: number }) {
  if (data.length < 2) return <div style={{ height }} className="opacity-30" />;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const w = 60;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = height - ((v - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={w} height={height} className="opacity-70">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function HeroStatusPanel() {
  const { phi, status, currentMetrics, metricsHistory, config } = useSimulationStore();
  const phiMax = GUARDRAILS.phiMax;
  const progress = Math.min(1, phi / phiMax);
  const phiDisplay = phi < 0.01 ? '0.00' : (phi / Math.PI).toFixed(2);

  const statusConfig: Record<string, { text: string; bg: string; color: string }> = {
    idle: { text: 'Inattiva', bg: 'rgba(61,61,92,0.3)', color: 'var(--text-muted)' },
    running: { text: 'In Esecuzione', bg: 'rgba(0,240,200,0.1)', color: 'var(--accent-phase)' },
    paused: { text: 'Pausa', bg: 'rgba(245,158,11,0.1)', color: 'var(--accent-nuclear)' },
    completed: { text: 'Completata', bg: 'rgba(16,185,129,0.1)', color: 'var(--accent-valid)' },
    failed: { text: 'Fallita', bg: 'rgba(239,68,68,0.1)', color: 'var(--accent-warn)' },
  };
  const sc = statusConfig[status] || statusConfig.idle;

  // Metric cards data
  const metrics = [
    {
      key: 'sigmaCn',
      label: 'σ(Cn) Coerenza',
      threshold: GUARDRAILS.sigmaCnMin,
      color: 'var(--accent-coherence)',
      icon: Activity,
    },
    {
      key: 'dratio',
      label: 'Dratio Discrim.',
      threshold: GUARDRAILS.dratioMin,
      color: 'var(--accent-phase)',
      icon: TrendingUp,
    },
    {
      key: 'jpol',
      label: 'Jpol Overlap',
      threshold: GUARDRAILS.jpolMin,
      color: 'var(--accent-nuclear)',
      icon: GitBranch,
    },
    {
      key: 'rhopol',
      label: 'ρpol Densità',
      threshold: GUARDRAILS.rhopolMin,
      color: 'var(--accent-portante)',
      icon: Shield,
    },
  ];

  return (
    <div className="card-base p-5">
      <div className="flex flex-col lg:flex-row gap-6 items-center">
        {/* φ Circular Gauge */}
        <div className="flex flex-col items-center shrink-0">
          <div className="relative w-28 h-28">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50" cy="50" r="42"
                fill="none"
                stroke="var(--bg-tertiary)"
                strokeWidth="8"
              />
              <circle
                cx="50" cy="50" r="42"
                fill="none"
                stroke="url(#phiGradient)"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${progress * 264} 264`}
                style={{ filter: 'drop-shadow(0 0 4px rgba(0,240,200,0.3))' }}
              />
              <defs>
                <linearGradient id="phiGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="var(--accent-phase)" />
                  <stop offset="100%" stopColor="var(--accent-coherence)" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="metric-value text-xl text-glow-phase" style={{ color: 'var(--accent-phase)' }}>
                {phiDisplay}π
              </span>
              <span className="text-[9px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                di 6π
              </span>
            </div>
          </div>
          <div
            className="mt-2 px-3 py-1 rounded-full text-[11px] font-medium"
            style={{ background: sc.bg, color: sc.color }}
          >
            {sc.text}
          </div>
        </div>

        {/* Metric Cards */}
        <div className="flex-1 grid grid-cols-2 lg:grid-cols-4 gap-3 w-full">
          {metrics.map((m) => {
            const Icon = m.icon;
            const val = currentMetrics ? (currentMetrics as unknown as Record<string, number>)[m.key] : 0;
            const passed = val > m.threshold;
            const history = metricsHistory.map((s) => (s as unknown as Record<string, number>)[m.key]);

            return (
              <div
                key={m.key}
                className="rounded-lg p-3 card-hover"
                style={{
                  background: 'var(--bg-tertiary)',
                  border: `1px solid ${passed ? m.color + '30' : 'var(--border-subtle)'}`,
                }}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-1.5">
                    <Icon size={12} style={{ color: m.color }} />
                    <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>
                      {m.label}
                    </span>
                  </div>
                  <Sparkline data={history.slice(-50)} color={m.color} />
                </div>
                <div
                  className="metric-value text-2xl"
                  style={{ color: passed ? m.color : 'var(--accent-warn)' }}
                >
                  {typeof val === 'number' ? val.toFixed(3) : '0.000'}
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
                    soglia {m.threshold}
                  </span>
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{
                      background: passed ? 'var(--accent-valid)' : 'var(--accent-warn)',
                      boxShadow: passed ? '0 0 6px var(--accent-valid)' : '0 0 6px var(--accent-warn)',
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Config Summary */}
        <div
          className="shrink-0 rounded-lg p-3 w-full lg:w-44"
          style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)' }}
        >
          <div className="label-upper mb-2">Configurazione</div>
          <div className="space-y-1.5 text-xs" style={{ color: 'var(--text-secondary)' }}>
            <div className="flex justify-between">
              <span>Nucleare</span>
              <span style={{ color: 'var(--text-primary)' }}>{config.materialNuclear}</span>
            </div>
            <div className="flex justify-between">
              <span>Portante</span>
              <span style={{ color: 'var(--text-primary)' }}>{config.materialCarrier}</span>
            </div>
            <div className="flex justify-between">
              <span>Griglia</span>
              <span style={{ color: 'var(--text-primary)' }}>{config.gridSize.join('×')}</span>
            </div>
            <div className="flex justify-between">
              <span>β</span>
              <span style={{ color: 'var(--text-primary)' }}>{config.beta}</span>
            </div>
            <div className="flex justify-between">
              <span>δz</span>
              <span style={{ color: 'var(--text-primary)' }}>{config.deltaZ}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
