import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { useSimulationStore } from '@/store/useSimulationStore';

function PhasePoints({ gridSize, theta }: { gridSize: [number, number, number]; theta: Float64Array | null }) {
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const [Nz, Nr, Nc] = gridSize;
  const count = Nz * Nr * Nc;

  const dummy = useMemo(() => new THREE.Object3D(), []);
  const color = useMemo(() => new THREE.Color(), []);

  useFrame(() => {
    if (!meshRef.current) return;
    let idx = 0;
    for (let z = 0; z < Nz; z++) {
      for (let r = 0; r < Nr; r++) {
        for (let c = 0; c < Nc; c++) {
          dummy.position.set(
            (c - Nc / 2) * 0.15,
            (z - Nz / 2) * 0.15,
            (r - Nr / 2) * 0.15
          );
          dummy.scale.setScalar(0.06);
          dummy.updateMatrix();
          meshRef.current.setMatrixAt(idx, dummy.matrix);

          // Color by phase θ (hue = θ / 2π)
          const phase = theta && idx < theta.length ? theta[idx] : Math.random() * Math.PI * 2;
          color.setHSL(phase / (2 * Math.PI), 0.7, 0.4);
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
      <sphereGeometry args={[1, 8, 8]} />
      <meshBasicMaterial />
    </instancedMesh>
  );
}

export default function GridPreview3D() {
  const { config, status } = useSimulationStore();
  const [Nz, Nr, Nc] = config.gridSize;

  // Generate synthetic phase data for preview when idle
  const previewTheta = useMemo(() => {
    const arr = new Float64Array(Nz * Nr * Nc);
    for (let i = 0; i < arr.length; i++) {
      arr[i] = Math.random() * 2 * Math.PI;
    }
    return arr;
  }, [Nz, Nr, Nc]);

  return (
    <div className="card-base p-4 h-[320px] flex flex-col">
      <div className="label-upper mb-3">Anteprima Griglia 3D</div>
      <div className="flex-1 rounded-lg overflow-hidden" style={{ background: 'var(--bg-grid)' }}>
        <Canvas camera={{ position: [3, 2, 3], fov: 50 }}>
          <ambientLight intensity={0.5} />
          <PhasePoints gridSize={config.gridSize} theta={status === 'running' ? null : previewTheta} />
          <OrbitControls autoRotate autoRotateSpeed={1} enableZoom={false} enablePan={false} />
        </Canvas>
      </div>
      <div className="flex items-center justify-between mt-2 text-[10px]" style={{ color: 'var(--text-muted)' }}>
        <span>Colore = fase θ</span>
        <span>{Nz}×{Nr}×{Nc} celle</span>
      </div>
    </div>
  );
}
