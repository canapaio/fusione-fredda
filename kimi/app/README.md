# Simulazione Base π — Kimi

Una moderna applicazione web per la simulazione di nucleazione basata sul modello π, sviluppata con React 19, TypeScript, Vite e Three.js.

## 📋 Descrizione

Questo progetto implementa una simulazione interattiva di nucleazione utilizzando integrazione RK4 (Runge-Kutta del 4° ordine) eseguita interamente lato client tramite Web Worker. L'applicazione fornisce visualizzazioni 3D interattive, grafici temporali delle metriche di validazione e un'interfaccia utente completa in italiano.

## ✨ Funzionalità

- **Dashboard Interattiva**: Panoramica dello stato della simulazione con gauge φ, metriche di validazione e anteprima 3D
- **Configurazione Simulazione**: Pannello configurazione parametri con slider, dropdown materiali e input multipli
- **Visualizzazione 3D**: Mappa di nucleazione interattiva realizzata con Three.js e React Three Fiber
- **Grafici Temporali**: 4 grafici stacked line charts per l'evoluzione delle metriche di validazione
- **Web Worker Architecture**: Tutta la computazione RK4 avviene in un worker dedicato per non bloccare la UI
- **State Management**: Zustand per la gestione centralizzata dello stato della simulazione
- **Animazioni Fluide**: Framer Motion per transizioni e animazioni dell'interfaccia

## 🛠️ Stack Tecnologico

### Core
| Package | Versione | Scopo |
|---------|----------|-------|
| React | ^19.2.0 | Framework UI |
| TypeScript | ~5.9.3 | Type safety |
| Vite | ^7.2.4 | Build tool & dev server |

### Styling & UI
| Package | Versione | Scopo |
|---------|----------|-------|
| Tailwind CSS | ^3.4.19 | Utility-first CSS |
| shadcn/ui | - | Componenti UI |
| Framer Motion | ^12.40.0 | Animazioni |
| Lucide React | ^0.562.0 | Icone |

### 3D & Visualizzazione
| Package | Versione | Scopo |
|---------|----------|-------|
| Three.js | ^0.184.0 | Rendering 3D |
| @react-three/fiber | ^9.6.1 | React renderer per Three.js |
| @react-three/drei | ^10.7.7 | Helpers per R3F |
| Recharts | ^2.15.4 | Grafici e timeline |

### State & Utilities
| Package | Versione | Scopo |
|---------|----------|-------|
| Zustand | ^5.0.13 | State management |
| React Router | ^7.6.1 | Routing |
| Zod | ^4.3.5 | Validazione dati |

## 📦 Installazione

```bash
cd app

# Installa le dipendenze
npm install

# Avvia il server di sviluppo
npm run dev

# Build per produzione
npm run build

# Preview della build
npm run preview

# Esegui linting
npm run lint
```

## 🏗️ Architettura

### Directory Structure
```
src/
├── sections/        # Sezioni delle pagine
├── hooks/           # Custom hooks
├── types/           # Definizioni TypeScript
├── components/      # Componenti UI (shadcn + custom)
├── App.tsx          # Root component
├── main.tsx         # Entry point
└── index.css        # Stili globali
```

### Web Worker Architecture

La simulazione RK4 viene eseguita in un Web Worker dedicato (`simulation.worker.ts`):

**Messaggi in input al worker:**
- `INIT`: Inizializza griglia e matrice Jpol sparsa
- `STEP`: Avanza la simulazione di N step
- `RESET`: Resetta lo stato

**Messaggi in output dal worker:**
- `SNAPSHOT`: Snapshot dei dati ogni `storeEvery` step
- `COMPLETE`: Dati finali quando φ=6π o stabilità raggiunta
- `GUARDRAIL_FAIL`: Notifica fallimento validazione
- `PROGRESS`: Aggiornamenti throttlati del progresso

### State Management (Zustand)

Tutti i dati di simulazione risiedono in un singolo store Zustand:
- `config`: Parametri configurabili dall'utente
- `state`: Dati live della simulazione (φ, θ, nHD, jpol, status)
- `metrics`: Time series delle 4 metriche di validazione
- `nucleationMap`: Float64Array per visualizzazione 3D
- `signature`: Firma strutturale calcolata a completamento
- `validation`: Risultati validazione flags
- `log`: Eventi cronologici della simulazione

## 🎨 Componenti Principali

### Layout
- **AppLayout**: Wrapper header + sidebar + main
- **Header**: Gauge φ, badge stato, flags validazione
- **Sidebar**: Navigazione tab e controlli simulazione

### Dashboard Tab
- **DashboardView**: Hero + preview 3D + log attività
- **HeroStatusPanel**: Gauge φ + 4 carte metriche + riepilogo config
- **GridPreview3D**: Anteprima 3D auto-rotante

### Simulazione Tab
- **SimulationView**: Pannello configurazione + viewport
- **ConfigPanel**: Card configurazione raggruppate per sezione
- **ParamSlider**: ~20 istanze per parametri numerici
- **MaterialSelector**: Dropdown materiali nucleante e carrier
- **SimulationViewport**: Timeline + grid viewer + mini grafici

### Risultati Tab
- **ResultsView**: Mappa 3D + timeline + firma strutturale + flags
- **NucleationMap3D**: Voxel point cloud interattivo
- **PhaseTimelineCharts**: 4 grafici stacked line
- **StructuralSignature**: Tabella correlazioni + heatmap Ψ_RX

## 🔧 Configurazione

### Matrice Jpol Sparsa (COO format)

Memorizzata come tre array paralleli: `rowIndices`, `colIndices`, `values` (Int32Array/Float64Array). La matrice è calcolata una volta all'inizializzazione e non viene modificata durante la simulazione.

### Visualizzazione 3D

Il rendering 3D utilizza React ref (non state) per evitare re-render:
- Lo store Zustand contiene `nucleationMap` Float64Array
- Un custom hook `useNucleationData()` scrive direttamente nel mesh Three.js
- Questo bypassa completamente il ciclo di render di React per gli aggiornamenti 3D

## 🌐 Linguaggio

Tutto il testo user-facing (etichette, bottoni, documentazione) è in **italiano**. Variabili, commenti e interfacce TypeScript sono in **inglese** per coerenza con l'ecosistema.

## 📄 License

Vedi il file [LICENSE](../../LICENSE) nella root del progetto.

## 📚 Documentazione

Per dettagli tecnici approfonditi, consultare [tech-spec.md](../tech-spec.md).

---

**Nota**: L'intera simulazione viene eseguita lato client. Non è richiesto alcun backend.
