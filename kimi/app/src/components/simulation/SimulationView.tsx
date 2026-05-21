import { useState, useRef, useEffect, useCallback } from 'react';
import { useSimulationStore } from '@/store/useSimulationStore';
import { MATERIALS_NUCLEAR, MATERIALS_CARRIER, GUARDRAILS, type SimulationConfig } from '@/types/simulation';
import {
  ChevronDown,
  ChevronUp,
  Cpu,
  Box,
  Waves,
  Settings2,
  SlidersHorizontal,
  Plus,
  X,
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

// Collapsible config card
function ConfigCard({ title, icon: Icon, defaultOpen = false, children }: {
  title: string; icon: React.ComponentType<{ size?: number; className?: string; style?: React.CSSProperties }>; defaultOpen?: boolean; children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-lg overflow-hidden" style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)' }}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2.5 text-sm font-medium"
        style={{ color: 'var(--text-primary)' }}
      >
        <div className="flex items-center gap-2">
          <Icon size={14} style={{ color: 'var(--accent-phase)' }} />
          {title}
        </div>
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
      {open && <div className="px-3 pb-3 space-y-3">{children}</div>}
    </div>
  );
}

// Labeled slider component
function ParamSlider({ label, value, min, max, step, onChange, unit = '', warning }: {
  label: string; value: number; min: number; max: number; step: number;
  onChange: (v: number) => void; unit?: string; warning?: (v: number) => boolean;
}) {
  const isWarn = warning ? warning(value) : false;
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{label}</span>
        <span className="metric-value text-xs" style={{ color: isWarn ? 'var(--accent-warn)' : 'var(--accent-phase)' }}>
          {value}{unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
        style={{
          background: `linear-gradient(to right, var(--accent-phase) ${((value - min) / (max - min)) * 100}%, var(--bg-grid) ${((value - min) / (max - min)) * 100}%)`,
          accentColor: 'var(--accent-phase)',
        }}
      />
    </div>
  );
}

// Material selector with rich options
function MaterialSelector({ label, value, options, onChange }: {
  label: string; value: string; options: Record<string, any>;
  onChange: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    function handleClick(e: MouseEvent) { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const selected = options[value];

  return (
    <div ref={ref} className="relative">
      <label className="text-xs block mb-1" style={{ color: 'var(--text-secondary)' }}>{label}</label>
      <button
        onClick={() => setOpen(!open)}
        className="w-full input-base flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          {'color' in (selected || {}) && (selected as { color: string }).color && (
            <div className="w-2.5 h-2.5 rounded-full" style={{ background: (selected as { color: string }).color }} />
          )}
          <span className="text-xs">{(selected as { name: string })?.name || value}</span>
        </div>
        <ChevronDown size={12} />
      </button>
      {open && (
        <div
          className="absolute z-50 w-full mt-1 rounded-lg py-1 max-h-48 overflow-y-auto"
          style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-active)', boxShadow: '0 8px 32px rgba(0,0,0,0.4)' }}
        >
          {Object.entries(options).map(([key, opt]) => (
            <button
              key={key}
              onClick={() => { onChange(key); setOpen(false); }}
              className="w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-white/5 transition-colors"
            >
              {'color' in opt && opt.color && (
                <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: opt.color as string }} />
              )}
              <span className="text-xs" style={{ color: 'var(--text-primary)' }}>{(opt as { name: string }).name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Mini chart for live metrics
function MiniChart({ data, dataKey, color, threshold, label }: {
  data: any[]; dataKey: string; color: string; threshold: number; label: string;
}) {
  return (
    <div className="rounded-lg p-2" style={{ background: 'var(--bg-tertiary)' }}>
      <div className="flex justify-between items-center mb-1">
        <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>{label}</span>
        <span className="metric-value text-[10px]" style={{ color }}>
          {data.length > 0 ? (data[data.length - 1] as unknown as Record<string, number>)[dataKey]?.toFixed(3) : '0.000'}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={80}>
        <LineChart data={data}>
          <XAxis dataKey="phi" hide />
          <YAxis domain={['auto', 'auto']} hide />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              fontSize: '10px',
            }}
            formatter={(value: number) => [value.toFixed(4), dataKey]}
            labelFormatter={(label: number) => `φ=${(label / Math.PI).toFixed(2)}π`}
          />
          <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={1.5} dot={false} isAnimationActive={false} />
          {/* Threshold line */}
          <Line type="step" dataKey={() => threshold} stroke="#ef4444" strokeWidth={0.5} strokeDasharray="3 3" dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// 2D Grid slice viewer
function GridSliceViewer() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { config, status } = useSimulationStore();
  const [zLayer, setZLayer] = useState(0);
  const [viewMode, setViewMode] = useState<'phase' | 'probability'>('phase');
  const animationRef = useRef<number>(0);

  const [Nz, Nr, Nc] = config.gridSize;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      const w = canvas.width;
      const h = canvas.height;
      const cellW = w / Nc;
      const cellH = h / Nr;

      ctx.fillStyle = '#0d0d18';
      ctx.fillRect(0, 0, w, h);

      for (let r = 0; r < Nr; r++) {
        for (let c = 0; c < Nc; c++) {
          const x = c * cellW;
          const y = r * cellH;

          if (viewMode === 'phase') {
            // Synthetic phase visualization
            const phase = Math.sin((c / Nc) * Math.PI * 2 + (zLayer / Nz) * Math.PI) * Math.cos((r / Nr) * Math.PI * 2);
            const hue = ((phase + 1) / 2) * 360;
            ctx.fillStyle = `hsl(${hue}, 70%, 40%)`;
          } else {
            // Probability heatmap
            const prob = Math.exp(-((c - Nc / 2) ** 2 + (r - Nr / 2) ** 2) / (Nc * Nr * 0.1)) * (1 - zLayer / Nz);
            const intensity = Math.min(1, prob);
            if (intensity > 0.75) {
              ctx.fillStyle = `rgba(245, 158, 11, ${intensity})`;
            } else if (intensity > 0.5) {
              ctx.fillStyle = `rgba(0, 240, 200, ${intensity})`;
            } else {
              ctx.fillStyle = `rgba(0, 240, 200, ${intensity * 0.5})`;
            }
          }

          ctx.fillRect(x + 0.5, y + 0.5, cellW - 1, cellH - 1);
        }
      }

      // Grid lines
      ctx.strokeStyle = 'rgba(255,255,255,0.03)';
      ctx.lineWidth = 0.5;
      for (let c = 0; c <= Nc; c++) {
        ctx.beginPath();
        ctx.moveTo(c * cellW, 0);
        ctx.lineTo(c * cellW, h);
        ctx.stroke();
      }
      for (let r = 0; r <= Nr; r++) {
        ctx.beginPath();
        ctx.moveTo(0, r * cellH);
        ctx.lineTo(w, r * cellH);
        ctx.stroke();
      }
    };

    if (status === 'running') {
      const animate = () => {
        draw();
        animationRef.current = requestAnimationFrame(animate);
      };
      animate();
      return () => cancelAnimationFrame(animationRef.current);
    } else {
      draw();
    }
  }, [zLayer, viewMode, Nz, Nr, Nc, status]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>
            Strato z={zLayer}
          </span>
          <input
            type="range" min={0} max={Nz - 1} value={zLayer}
            onChange={(e) => setZLayer(parseInt(e.target.value))}
            className="w-24 h-1"
          />
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => setViewMode('phase')}
            className="px-2 py-0.5 rounded text-[10px] font-medium transition-colors"
            style={{
              background: viewMode === 'phase' ? 'var(--accent-phase)' : 'var(--bg-tertiary)',
              color: viewMode === 'phase' ? 'var(--bg-primary)' : 'var(--text-secondary)',
            }}
          >
            Fase
          </button>
          <button
            onClick={() => setViewMode('probability')}
            className="px-2 py-0.5 rounded text-[10px] font-medium transition-colors"
            style={{
              background: viewMode === 'probability' ? 'var(--accent-nuclear)' : 'var(--bg-tertiary)',
              color: viewMode === 'probability' ? 'var(--bg-primary)' : 'var(--text-secondary)',
            }}
          >
            Probabilità
          </button>
        </div>
      </div>
      <canvas
        ref={canvasRef}
        width={400}
        height={400}
        className="w-full flex-1 rounded-lg"
        style={{ background: 'var(--bg-grid)', imageRendering: 'pixelated' }}
      />
    </div>
  );
}

// Main Simulation View
export default function SimulationView() {
  const { config, updateConfig, metricsHistory } = useSimulationStore();
  const [freqInput, setFreqInput] = useState('');

  const addFrequency = useCallback(() => {
    const f = parseFloat(freqInput);
    if (!isNaN(f) && f > 0 && !config.etaProgFrequencies.includes(f)) {
      updateConfig({ etaProgFrequencies: [...config.etaProgFrequencies, f] });
      setFreqInput('');
    }
  }, [freqInput, config.etaProgFrequencies, updateConfig]);

  const removeFrequency = useCallback((f: number) => {
    updateConfig({ etaProgFrequencies: config.etaProgFrequencies.filter((x) => x !== f) });
  }, [config.etaProgFrequencies, updateConfig]);

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-140px)]">
      {/* Configuration Panel */}
      <div className="w-full lg:w-[380px] shrink-0 overflow-y-auto space-y-3 pr-1">
        <ConfigCard title="Materiali" icon={Box} defaultOpen>
          <MaterialSelector
            label="Materiale Nucleare"
            value={config.materialNuclear}
            options={MATERIALS_NUCLEAR as unknown as Record<string, { name: string; color: string }>}
            onChange={(v) => updateConfig({ materialNuclear: v as SimulationConfig['materialNuclear'] })}
          />
          <MaterialSelector
            label="Materiale Portante H/D"
            value={config.materialCarrier}
            options={MATERIALS_CARRIER as unknown as Record<string, { name: string; color: string }>}
            onChange={(v) => updateConfig({ materialCarrier: v as SimulationConfig['materialCarrier'] })}
          />
          <ParamSlider label="Rapporto H/D" value={config.hdRatio} min={0.5} max={3.0} step={0.1}
            onChange={(v) => updateConfig({ hdRatio: v })} />
          <div>
            <label className="text-xs block mb-1" style={{ color: 'var(--text-secondary)' }}>Range Temperatura (°C)</label>
            <div className="flex gap-2">
              <input type="number" value={config.temperatureRange[0]}
                onChange={(e) => updateConfig({ temperatureRange: [parseInt(e.target.value), config.temperatureRange[1]] })}
                className="input-base w-full text-xs" />
              <input type="number" value={config.temperatureRange[1]}
                onChange={(e) => updateConfig({ temperatureRange: [config.temperatureRange[0], parseInt(e.target.value)] })}
                className="input-base w-full text-xs" />
            </div>
          </div>
        </ConfigCard>

        <ConfigCard title="Geometria Griglia" icon={Cpu}>
          <div className="grid grid-cols-3 gap-2">
            {(['z', 'r', 'c'] as const).map((dim, i) => (
              <div key={dim}>
                <label className="text-xs block mb-1" style={{ color: 'var(--text-secondary)' }}>{dim.toUpperCase()}</label>
                <input
                  type="number" min={5} max={100}
                  value={config.gridSize[i]}
                  onChange={(e) => {
                    const newSize = [...config.gridSize] as [number, number, number];
                    newSize[i] = parseInt(e.target.value) || 5;
                    updateConfig({ gridSize: newSize });
                  }}
                  className="input-base w-full text-xs"
                />
              </div>
            ))}
          </div>
          <ParamSlider label="Shear Verticale β" value={config.beta} min={0} max={1} step={0.01}
            onChange={(v) => updateConfig({ beta: v })} warning={(v) => v < GUARDRAILS.betaMin} />
          <ParamSlider label="Modulazione Spaziale δz" value={config.deltaZ} min={0} max={0.5} step={0.01}
            onChange={(v) => updateConfig({ deltaZ: v })} warning={(v) => v < GUARDRAILS.deltaZMin} />
        </ConfigCard>

        <ConfigCard title="Onda Portante" icon={Waves}>
          <div>
            <label className="text-xs block mb-1" style={{ color: 'var(--text-secondary)' }}>Frequenze η_prog (MHz)</label>
            <div className="flex flex-wrap gap-1 mb-2">
              {config.etaProgFrequencies.map((f) => (
                <span key={f} className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px]"
                  style={{ background: 'var(--bg-secondary)', color: 'var(--accent-phase)', border: '1px solid var(--border-subtle)' }}>
                  {f}
                  <button onClick={() => removeFrequency(f)}><X size={10} /></button>
                </span>
              ))}
            </div>
            <div className="flex gap-1">
              <input
                type="number" placeholder="Aggiungi MHz" value={freqInput}
                onChange={(e) => setFreqInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addFrequency()}
                className="input-base flex-1 text-xs"
              />
              <button onClick={addFrequency} className="btn-secondary px-2">
                <Plus size={14} />
              </button>
            </div>
          </div>
          <ParamSlider label="Profilo γ₀" value={config.gamma0} min={0.1} max={5} step={0.1}
            onChange={(v) => updateConfig({ gamma0: v })} />
          <ParamSlider label="Profilo λ" value={config.gammaLambda} min={0.1} max={2} step={0.05}
            onChange={(v) => updateConfig({ gammaLambda: v })} />
          <ParamSlider label="Soglia Jpol" value={config.jpolThreshold} min={0} max={1.5} step={0.05}
            onChange={(v) => updateConfig({ jpolThreshold: v })} />
        </ConfigCard>

        <ConfigCard title="Integrazione" icon={Settings2}>
          <div className="grid grid-cols-2 gap-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
            <div>Range φ: <span style={{ color: 'var(--text-primary)' }}>[0, 6π]</span></div>
            <div>Passo dφ: <span style={{ color: 'var(--text-primary)' }}>0.01</span></div>
          </div>
          <ParamSlider label="Storico ogni N step" value={config.storeEvery} min={1} max={10} step={1}
            onChange={(v) => updateConfig({ storeEvery: v })} />
        </ConfigCard>

        <ConfigCard title="Parametri Avanzati" icon={SlidersHorizontal}>
          <ParamSlider label="J₀" value={config.J0} min={0.1} max={2} step={0.05}
            onChange={(v) => updateConfig({ J0: v })} />
          <ParamSlider label="f₀" value={config.f0} min={1} max={10} step={0.1}
            onChange={(v) => updateConfig({ f0: v })} />
          <ParamSlider label="σJ (disordine)" value={config.sigmaJ} min={0} max={0.5} step={0.01}
            onChange={(v) => updateConfig({ sigmaJ: v })} />
          <ParamSlider label="D_φ" value={config.Dphi} min={0.01} max={0.5} step={0.01}
            onChange={(v) => updateConfig({ Dphi: v })} />
          <ParamSlider label="κ" value={config.kappa} min={0.01} max={0.5} step={0.01}
            onChange={(v) => updateConfig({ kappa: v })} />
        </ConfigCard>
      </div>

      {/* Simulation Viewport */}
      <div className="flex-1 flex flex-col gap-4 min-h-0">
        {/* Grid slice viewer */}
        <div className="card-base p-4 flex-1 min-h-0">
          <GridSliceViewer />
        </div>

        {/* Mini charts */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 shrink-0">
          <MiniChart data={metricsHistory} dataKey="sigmaCn" color="#7c3aed" threshold={GUARDRAILS.sigmaCnMin} label="σ(Cn)" />
          <MiniChart data={metricsHistory} dataKey="dratio" color="#00f0c8" threshold={GUARDRAILS.dratioMin} label="Dratio" />
          <MiniChart data={metricsHistory} dataKey="jpol" color="#f59e0b" threshold={GUARDRAILS.jpolMin} label="Jpol" />
          <MiniChart data={metricsHistory} dataKey="rhopol" color="#3b82f6" threshold={GUARDRAILS.rhopolMin} label="ρpol" />
        </div>
      </div>
    </div>
  );
}
