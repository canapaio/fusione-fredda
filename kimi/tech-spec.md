# Tech Spec — Simulazione Base π

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| react | ^19.0.0 | UI framework |
| react-dom | ^19.0.0 | DOM renderer |
| vite | ^6.0.0 | Build tool |
| @vitejs/plugin-react | ^4.4.0 | Vite React integration |
| typescript | ^5.7.0 | Type safety |
| tailwindcss | ^4.0.0 | Styling |
| @tailwindcss/vite | ^4.0.0 | Tailwind Vite plugin |
| three | ^0.172.0 | 3D nucleation map |
| @react-three/fiber | ^9.0.0 | React Three.js renderer |
| @react-three/drei | ^9.0.0 | R3F helpers (OrbitControls, Text) |
| recharts | ^2.15.0 | Timeline charts, metric plots |
| framer-motion | ^12.0.0 | Panel animations, transitions |
| zustand | ^5.0.0 | State management |
| lucide-react | ^0.460.0 | Icons |
| @fontsource-variable/inter | ^5.0.0 | Primary font |
| @fontsource-variable/jetbrains-mono | ^5.0.0 | Monospace font |

No additional shadcn/ui components beyond those already installed by the init script.

---

## Component Inventory

### Layout (shared across all tabs)

| Component | Source | Reuse |
|-----------|--------|-------|
| AppLayout | Custom | Single — wraps header + sidebar + main |
| Header | Custom | Single — φ gauge, status badges, flags |
| Sidebar | Custom | Single — nav tabs, simulation controls |
| PiProgressGauge | Custom | Single — circular φ progress in header |
| ValidationFlagsBar | Custom | Single — 4 flag badges in header |

### Dashboard Tab

| Component | Source | Reuse |
|-----------|--------|-------|
| DashboardView | Custom | Single — hero + preview + log |
| HeroStatusPanel | Custom | Single — φ gauge + 4 metric cards + config summary |
| MetricSparkCard | Custom | 4 instances — one per validation metric |
| Sparkline | Custom | 4 instances — tiny SVG chart (60×20px) |
| GridPreview3D | Custom (Three.js) | Single — auto-rotating preview, shared renderer with Results |
| ActivityLog | Custom | Single — scrollable event list |

### Simulazione Tab

| Component | Source | Reuse |
|-----------|--------|-------|
| SimulationView | Custom | Single — config panel + viewport |
| ConfigPanel | Custom | Single — scrollable, grouped parameter cards |
| ConfigCard | Custom | 5 instances — collapsible section wrapper |
| MaterialSelector | Custom | 2 instances — nuclear + carrier dropdowns with rich options |
| ParamSlider | Custom | ~20 instances — labeled slider with value display |
| DualRangeSlider | Custom | Single — temperature range (custom, not shadcn) |
| FrequencyChips | Custom | Single — multi-select chip input for η_prog frequencies |
| SimulationViewport | Custom | Single — timeline strip + grid viewer + mini charts |
| TimelineStrip | Custom | Single — horizontal scrollable φ history bars |
| GridSliceViewer | Custom (Canvas 2D) | Single — z-layer cross-section, colored by phase or probability |
| MiniChartGrid | Custom | Single — 2×2 mini recharts for live metrics |

### Risultati Tab

| Component | Source | Reuse |
|-----------|--------|-------|
| ResultsView | Custom | Single — 3D map + timelines + signature + flags |
| NucleationMap3D | Custom (Three.js) | Single — interactive voxel point cloud |
| PhaseTimelineCharts | Custom (Recharts) | Single — 4 stacked line charts |
| StructuralSignature | Custom | Single — correlation table + Ψ_RX heatmap |
| ValidationFlagCards | Custom | 4 instances — large status cards |
| DerivedEnergyChart | Custom (Recharts) | Single — optional filled area chart |

### Documentazione Tab

| Component | Source | Reuse |
|-----------|--------|-------|
| DocsView | Custom | Single — scrollable content sections |
| DocSection | Custom | 6 instances — collapsible/scrollable sections |
| StyledTable | Custom | 2 instances — material tables |

### Reusable Components

| Component | Source | Used By |
|-----------|--------|---------|
| SimulationWorker | Web Worker | SimulationView — all RK4 computation |

---

## Animation Implementation

| Animation | Library | Implementation | Complexity |
|-----------|---------|----------------|------------|
| Tab content switch (fade out/in) | framer-motion | AnimatePresence wrapping content area | Low |
| Config card expand/collapse | framer-motion | animate height, chevron rotation | Low |
| Metric value flash on update | CSS transition | Text-shadow + color pulse (200ms) | Low |
| Validation badge pulse | CSS keyframes | Box-shadow glow oscillation on state change | Low |
| 3D map cell highlight pulse | Three.js | Continuous opacity oscillation (0.6→1→0.6, 2s) in useFrame | Medium |
| φ progress gauge fill | framer-motion | SVG stroke-dashoffset animated by φ value | Medium |
| Grid slice crossfade | Canvas 2D | Fade between z-layers via composite alpha | Medium |
| Sidebar collapse/expand | framer-motion | Width + opacity animation (300ms) | Low |
| Timeline strip cursor | framer-motion | translateX driven by current φ | Low |
| Nucleation map hover tooltip | Three.js + HTML | Raycaster hit detection + absolutely positioned div | Medium |
| Mini chart data stream | recharts | Incremental data append, no re-mount | Low |

---

## State & Logic Plan

### Simulation State (Zustand store)

All simulation data lives in a single Zustand store to avoid prop-drilling across tabs:

- **config**: `SimulationConfig` — user-editable parameters, persisted to localStorage
- **state**: `SimulationState` — live simulation data (φ, θ, nHD, jpol, status)
- **metrics**: `MetricsSnapshot[]` — time series of all 4 validation metrics
- **nucleationMap**: `Float64Array | null` — final P_π(φ) for 3D visualization
- **signature**: `StructuralSignature | null` — computed after completion
- **validation**: `ValidationResult | null` — final validation flags
- **log**: `ActivityEvent[]` — chronological simulation events

The store exposes actions: `initialize()`, `start()`, `pause()`, `reset()`, `updateConfig(partial)`, `receiveWorkerMessage(data)`.

### Web Worker Architecture

The entire RK4 simulation runs in a dedicated Web Worker (`simulation.worker.ts`) to avoid blocking the UI thread:

**Worker input messages**:
- `INIT`: config object → worker creates grid, computes Jpol sparse matrix (COO), initializes θ randomly
- `STEP`: number of steps to advance → worker performs RK4 integration, computes metrics, returns snapshot
- `RESET`: clear all state

**Worker output messages** (postMessage back to main thread):
- `SNAPSHOT`: { phi, theta, metrics, nucleationProb, logEvent } — sent every `storeEvery` steps
- `COMPLETE`: { finalMetrics, nucleationMap, signature, validation } — when φ=6π or stable cycles reached
- `GUARDRAIL_FAIL`: { metric, value, threshold, phi } — when validation fails
- `PROGRESS`: { phi, percentComplete } — throttled progress updates

The worker maintains its own Float64Arrays for θ, nHD, and the sparse Jpol structure. No React state in the worker.

### Sparse Jpol Matrix (COO format)

Stored as three parallel arrays: `rowIndices`, `colIndices`, `values` — all Int32Array/Float64Array. This avoids object overhead and enables O(Nnz) operations. The matrix is computed once at initialization and never modified during simulation (per manifesto: structural disorder is "the voice of the tube").

### 3D Visualization Data Flow

The Three.js nucleation map receives data via a React ref (not state) to avoid re-renders:
- The Zustand store holds the `nucleationMap` Float64Array
- A custom hook `useNucleationData()` subscribes to store changes and writes directly to the Three.js instanced mesh via `mesh.instanceMatrix` and `mesh.instanceColor`
- This bypasses React's render cycle entirely for 3D updates

---

## Other Key Decisions

### Grid Viewer: Canvas 2D, not WebGL

The 2D z-layer slice viewer uses HTML5 Canvas 2D (not a second Three.js scene) because:
- It's a simple colored grid — overkill for WebGL
- Canvas 2D allows pixel-perfect control for heatmap coloring
- No additional library needed — keeps bundle smaller

### Recharts over D3 for Timelines

Recharts is chosen over raw D3 for the 4 timeline charts because:
- Declarative React API — fits the component model
- Built-in tooltips, axes, responsive containers
- Sufficient performance for ~600 data points (φ steps / storeEvery)
- If performance becomes an issue, data can be decimated (every Nth point)

### No Backend Required

The entire simulation runs client-side in the Web Worker. No server is needed because:
- The RK4 integration is purely mathematical — no external data sources
- Float64Array operations in modern JS engines are fast enough for grids up to ~50³
- For larger grids, the user can reduce grid size or increase storeEvery

### Language Strategy

All user-facing UI text is in Italian (labels, buttons, documentation). Code variables, comments, and TypeScript interfaces remain in English for consistency with the broader ecosystem.
