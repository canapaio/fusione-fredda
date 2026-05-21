import HeroStatusPanel from './HeroStatusPanel';
import ActivityLog from './ActivityLog';
import GridPreview3D from './GridPreview3D';

export default function DashboardView() {
  return (
    <div className="space-y-6">
      {/* Hero Status */}
      <HeroStatusPanel />

      {/* Middle row: 3D Preview + Activity Log */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GridPreview3D />
        <ActivityLog />
      </div>
    </div>
  );
}
