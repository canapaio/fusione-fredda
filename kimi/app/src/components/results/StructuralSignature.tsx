import { useEffect, useRef } from 'react';
import { useSimulationStore } from '@/store/useSimulationStore';
import { Fingerprint } from 'lucide-react';

export default function StructuralSignature() {
  const { signature } = useSimulationStore();

  return (
    <div className="card-base p-5">
      <div className="label-upper mb-4 flex items-center gap-2">
        <Fingerprint size={12} />
        Firma Strutturale
      </div>

      {signature ? (
        <div className="space-y-4">
          {/* Correlation coefficients */}
          <div>
            <div className="text-xs mb-2" style={{ color: 'var(--text-secondary)' }}>Coefficienti di Correlazione (C₁..Cₖ)</div>
            <div className="grid grid-cols-4 gap-2">
              {signature.correlations.map((c, i) => (
                <div
                  key={i}
                  className="rounded-lg p-2 text-center"
                  style={{ background: 'var(--bg-tertiary)' }}
                >
                  <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>C{i + 1}</div>
                  <div className="metric-value text-sm" style={{ color: 'var(--accent-phase)' }}>
                    {c.toFixed(4)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Key metrics */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg p-3" style={{ background: 'var(--bg-tertiary)' }}>
              <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Divergenza D</div>
              <div className="metric-value text-lg" style={{ color: 'var(--accent-coherence)' }}>
                {signature.divergence.toFixed(4)}
              </div>
            </div>
            <div className="rounded-lg p-3" style={{ background: 'var(--bg-tertiary)' }}>
              <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Intensità I_dens</div>
              <div className="metric-value text-lg" style={{ color: 'var(--accent-nuclear)' }}>
                {signature.intensity.toFixed(4)}
              </div>
            </div>
            <div className="rounded-lg p-3" style={{ background: 'var(--bg-tertiary)' }}>
              <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>σ(Cn) Finale</div>
              <div className="metric-value text-lg" style={{ color: 'var(--accent-phase)' }}>
                {signature.sigmaCn.toFixed(4)}
              </div>
            </div>
          </div>

          {/* Ψ_RX heatmap */}
          <div>
            <div className="text-xs mb-2" style={{ color: 'var(--text-secondary)' }}>
              Ψ_RX — Firma Piano RX (z=0)
            </div>
            <RXHeatmap data={signature.psiRX} />
          </div>
        </div>
      ) : (
        <div className="text-center py-8">
          <Fingerprint size={32} style={{ color: 'var(--text-muted)' }} className="mx-auto mb-3 opacity-50" />
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            La firma strutturale verrà calcolata al completamento della simulazione.
          </p>
        </div>
      )}
    </div>
  );
}

function RXHeatmap({ data }: { data: Float64Array }) {
  const size = Math.sqrt(data.length);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const cellW = w / size;
    const cellH = h / size;

    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        const val = data[r * size + c];
        const intensity = (val + 1) / 2;
        const hue = intensity * 180 + 160;
        ctx.fillStyle = `hsl(${hue}, 80%, ${30 + intensity * 30}%)`;
        ctx.fillRect(c * cellW, r * cellH, cellW + 1, cellH + 1);
      }
    }
  }, [data, size]);

  return (
    <div className="rounded-lg overflow-hidden" style={{ background: 'var(--bg-grid)' }}>
      <canvas
        ref={canvasRef}
        width={200}
        height={200}
        className="w-full"
        style={{ imageRendering: 'pixelated', maxHeight: '200px' }}
      />
    </div>
  );
}
