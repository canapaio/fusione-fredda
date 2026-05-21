import { useSimulationStore } from '@/store/useSimulationStore';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Info, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

const typeConfig = {
  info: { icon: Info, color: 'var(--accent-portante)' },
  success: { icon: CheckCircle, color: 'var(--accent-valid)' },
  warning: { icon: AlertTriangle, color: 'var(--accent-nuclear)' },
  error: { icon: XCircle, color: 'var(--accent-warn)' },
};

export default function ActivityLog() {
  const { activityLog } = useSimulationStore();

  return (
    <div className="card-base p-4 h-[320px] flex flex-col">
      <div className="label-upper mb-3 flex items-center gap-2">
        <span>Log Attività</span>
        <span
          className="px-1.5 py-0.5 rounded text-[10px]"
          style={{ background: 'var(--bg-tertiary)', color: 'var(--text-muted)' }}
        >
          {activityLog.length}
        </span>
      </div>
      <ScrollArea className="flex-1 -mx-1">
        <div className="space-y-1 px-1">
          {activityLog.length === 0 && (
            <div className="text-center py-8 text-xs" style={{ color: 'var(--text-muted)' }}>
              Nessun evento registrato
            </div>
          )}
          {activityLog.map((evt) => {
            const tc = typeConfig[evt.type];
            const Icon = tc.icon;
            const phiStr = evt.phi < 0.01 ? '0.00' : (evt.phi / Math.PI).toFixed(2);
            return (
              <div
                key={evt.id}
                className="flex items-start gap-2 p-2 rounded-md"
                style={{ background: 'var(--bg-tertiary)' }}
              >
                <Icon size={12} className="mt-0.5 shrink-0" style={{ color: tc.color }} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                    {evt.message}
                  </p>
                  <p className="text-[10px] mt-0.5 font-mono-data" style={{ color: 'var(--text-muted)' }}>
                    φ={phiStr}π
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
