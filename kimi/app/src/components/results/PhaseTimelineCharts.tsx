import { useSimulationStore } from '@/store/useSimulationStore';
import { GUARDRAILS } from '@/types/simulation';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

interface ChartConfig {
  key: string;
  label: string;
  color: string;
  threshold: number;
}

const charts: ChartConfig[] = [
  { key: 'sigmaCn', label: 'σ(Cn) — Coerenza Armonica', color: '#7c3aed', threshold: GUARDRAILS.sigmaCnMin },
  { key: 'dratio', label: 'Dratio — Discriminazione Strutturale', color: '#00f0c8', threshold: GUARDRAILS.dratioMin },
  { key: 'jpol', label: 'Jpol — Overlap Polarizzato', color: '#f59e0b', threshold: GUARDRAILS.jpolMin },
  { key: 'rhopol', label: 'ρpol — Densità Accoppiamento', color: '#3b82f6', threshold: GUARDRAILS.rhopolMin },
];

export default function PhaseTimelineCharts() {
  const { metricsHistory } = useSimulationStore();

  return (
    <div className="card-base p-5">
      <div className="label-upper mb-4">Timeline di Fase</div>
      <div className="space-y-4">
        {charts.map((chart) => (
          <div key={chart.key}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium" style={{ color: chart.color }}>
                {chart.label}
              </span>
              <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
                soglia: {chart.threshold}
              </span>
            </div>
            <ResponsiveContainer width="100%" height={140}>
              <LineChart data={metricsHistory}>
                <XAxis
                  dataKey="phi"
                  tickFormatter={(v: number) => `${(v / Math.PI).toFixed(1)}π`}
                  tick={{ fontSize: 10, fill: '#3d3d5c' }}
                  axisLine={{ stroke: '#1a1a2e' }}
                  tickLine={{ stroke: '#1a1a2e' }}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: '#3d3d5c' }}
                  axisLine={{ stroke: '#1a1a2e' }}
                  tickLine={{ stroke: '#1a1a2e' }}
                  width={40}
                />
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '6px',
                    fontSize: '11px',
                  }}
                  formatter={(value: number) => [value.toFixed(4), chart.key]}
                  labelFormatter={(label: number) => `φ=${(label / Math.PI).toFixed(2)}π`}
                />
                <ReferenceLine
                  y={chart.threshold}
                  stroke="#ef4444"
                  strokeDasharray="4 4"
                  strokeWidth={1}
                />
                <Line
                  type="monotone"
                  dataKey={chart.key}
                  stroke={chart.color}
                  strokeWidth={1.5}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ))}
      </div>
    </div>
  );
}
