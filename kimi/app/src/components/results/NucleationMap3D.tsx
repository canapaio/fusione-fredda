import { useRef, useMemo, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { useSimulationStore } from '@/store/useSimulationStore';

function NucleationVoxels() {
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const { config, nucleationMap } = useSimulationStore();
  const [Nz, Nr, Nc] = config.gridSize;
  const count = Nz * Nr * Nc;

  const dummy = useMemo(() => new THREE.Object3D(), []);
  const color = useMemo(() => new THREE.Color(), []);

  // Generate nucleation probability if not available
  const probData = useMemo(() => {
    if (nucleationMap) return nucleationMap;
    // Synthetic data for preview
    const arr = new Float64Array(count);
    for (let i = 0; i < count; i++) {
      const z = Math.floor(i / (Nr * Nc));
      const r = Math.floor((i % (Nr * Nc)) / Nc);
      const c = i % Nc;
      arr[i] = Math.exp(-((c - Nc / 2) ** 2 + (r - Nr / 2) ** 2 + (z - Nz / 4) ** 2) / (Nc * Nr * Nz * 0.05));
    }
    return arr;
  }, [nucleationMap, count, Nz, Nr, Nc]);

  useFrame(() => {
    if (!meshRef.current) return;

    let idx = 0;
    for (let z = 0; z < Nz; z++) {
      for (let r = 0; r < Nr; r++) {
        for (let c = 0; c < Nc; c++) {
          const prob = probData[idx];
          dummy.position.set(
            (c - Nc / 2) * 0.12,
            (z - Nz / 2) * 0.12,
            (r - Nr / 2) * 0.12
          );
          const scale = 0.04 + prob * 0.08;
          dummy.scale.setScalar(scale);
          dummy.updateMatrix();
          meshRef.current.setMatrixAt(idx, dummy.matrix);

          // Color gradient: black → cyan → purple → amber
          if (prob > 0.75) {
            color.setRGB(1.0, 0.62, 0.04); // amber
          } else if (prob > 0.5) {
            color.setRGB(0.49, 0.23, 0.93); // purple
          } else if (prob > 0.25) {
            color.setRGB(0.0, 0.94, 0.78); // cyan
          } else {
            color.setRGB(0.05, 0.05, 0.08); // near black
          }
          const alpha = Math.max(0.15, prob);
          color.multiplyScalar(alpha);
          meshRef.current.setColorAt(idx, color);
          idx++;
        }
      }
    }
    meshRef.current.instanceMatrix.needsUpdate = true;
    if (meshRef.current.instanceColor) meshRef.current.instanceColor.needsUpdate = true;
  });

  return (
    <instancedMesh ref={meshRef} args={[undefined, undefined, count]}>
      <boxGeometry args={[1, 1, 1]} />
      <meshBasicMaterial toneMapped={false} />
    </instancedMesh>
  );
}

export default function NucleationMap3D() {
  return (
    <div className="card-base p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="label-upper">Mappa 3D Probabilità Nucleazione</div>
        <div className="flex items-center gap-3 text-[10px]" style={{ color: 'var(--text-muted)' }}>
          <span className="flex items-center gap-1">
            <span className="w-3 h-1 rounded" style={{ background: '#050508' }} />0.0
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-1 rounded" style={{ background: '#00f0c8' }} />0.5
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-1 rounded" style={{ background: '#7c3aed' }} />0.8
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-1 rounded" style={{ background: '#f59e0b' }} />1.0
          </span>
        </div>
      </div>
      <div className="rounded-lg overflow-hidden" style={{ height: '400px', background: 'var(--bg-grid)' }}>
        <Canvas camera={{ position: [4, 3, 4], fov: 50 }}>
          <ambientLight intensity={0.3} />
          <pointLight position={[10, 10, 10]} intensity={0.5} />
          <Suspense fallback={null}>
            <NucleationVoxels />
          </Suspense>
          <OrbitControls enablePan={true} enableZoom={true} />
        </Canvas>
      </div>
      <div className="mt-2 text-[10px] text-center" style={{ color: 'var(--text-muted)' }}>
        Ruota per esplorare · Zoom con scroll · Celle con P &gt; 0.75 evidenziate in ambra
      </div>
    </div>
  );
}
