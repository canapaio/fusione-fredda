import { useState } from 'react';
import { ChevronRight, History, Calculator, Boxes, Waves, ShieldCheck, FlaskConical } from 'lucide-react';

interface SectionProps {
  id: string;
  title: string;
  icon: React.ComponentType<{ size?: number; className?: string; style?: React.CSSProperties }>;
  children: React.ReactNode;
}

function DocSection({ id, title, icon: Icon, children }: SectionProps) {
  const [open, setOpen] = useState(false);
  return (
    <div
      id={id}
      className="rounded-lg overflow-hidden mb-4"
      style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)' }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-5 py-4 text-left"
      >
        <Icon size={18} style={{ color: 'var(--accent-phase)' }} />
        <span className="text-base font-semibold flex-1" style={{ color: 'var(--text-primary)' }}>
          {title}
        </span>
        <ChevronRight
          size={16}
          style={{ color: 'var(--text-muted)', transform: open ? 'rotate(90deg)' : 'rotate(0)', transition: 'transform 0.2s' }}
        />
      </button>
      {open && (
        <div className="px-5 pb-5 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
          <div className="pt-4 docs-content">{children}</div>
        </div>
      )}
    </div>
  );
}

function Equation({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="rounded-lg p-4 my-3 font-mono-data text-sm overflow-x-auto"
      style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', color: 'var(--accent-phase)' }}
    >
      {children}
    </div>
  );
}

export default function DocsView() {
  return (
    <div className="max-w-[900px] mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
          Documentazione
        </h1>
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          Manuale tecnico e riferimento per la simulazione Base π
        </p>
      </div>

      <DocSection id="contesto" title="1. Contesto Storico" icon={History}>
        <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--text-primary)' }}>
          La ricerca sulla fusione fredda nasce nel <strong>1989</strong> con Fleischmann &amp; Pons,
          rapidamente etichettata come pseudoscienza dopo tentativi di replica falliti. Da allora,
          il dibattito si è polarizzato tra rigetto accademico e persistenza di anomalie termiche
          in sistemi Ni-H, Pd-D, Ti-D.
        </p>
        <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--text-primary)' }}>
          Il caso <strong>Rossi/E-Cat</strong> ha alimentato il dibattito: Andrea Rossi propose il
          reattore E-Cat (Ni + H → Cu + energia), ma la comunità scientifica lo respinse per
          mancanza di replicabilità pubblica, "catalizzatore segreto" non divulgato, e rapporti
          isotopici compatibili con miscela commerciale.
        </p>
        <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
          <strong>La nostra posizione</strong>: Non difendiamo né attacchiamo Rossi. Osserviamo che
          la <span style={{ color: 'var(--accent-phase)' }}>geometria è il segreto</span>. Se approcci
          il problema con coordinate euclidee, la barriera di Coulomb resta un muro. Se la pensi in
          <strong> Base π</strong> — dove l'asse è φ, non t — quel muro diventa una porta risonante.
        </p>
      </DocSection>

      <DocSection id="algebra" title="2. Algebra Base π" icon={Calculator}>
        <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--text-primary)' }}>
          <strong>Base π</strong> non è un sistema numerico posizionale. È un manifold computazionale dove:
        </p>
        <ul className="text-sm space-y-2 mb-4" style={{ color: 'var(--text-primary)' }}>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-phase)' }}>●</span>
            L'asse di evoluzione è <code className="px-1.5 py-0.5 rounded text-xs" style={{ background: 'var(--bg-tertiary)', color: 'var(--accent-phase)' }}>φ ∈ [0, kπ]</code>, non il tempo t
          </li>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-phase)' }}>●</span>
            Frequenze, accoppiamenti, soglie sono riferiti a multipli/frazioni di π
          </li>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-phase)' }}>●</span>
            Operazioni = interferenza, modulazione, divergenza di fase su varietà π-modulata
          </li>
        </ul>

        <p className="text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>Equazione Kuramoto π-Modulata:</p>
        <Equation>
          dθ_zrc/dφ = ω_zrc + Σ Jpol·sin(Δθ + π·m) + η_prog(φ)·γ_zrc + TX_zrc(φ)
        </Equation>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs mt-4" style={{ color: 'var(--text-secondary)' }}>
          <div className="rounded-lg p-3" style={{ background: 'var(--bg-tertiary)' }}>
            <strong style={{ color: 'var(--text-primary)' }}>ω_zrc</strong> = f₀·π^α·r/Nr + β·z/Nz
            <br />Frequenza naturale π-modulata
          </div>
          <div className="rounded-lg p-3" style={{ background: 'var(--bg-tertiary)' }}>
            <strong style={{ color: 'var(--text-primary)' }}>Jpol</strong> = J₀·|cos(ψᵢ − ψⱼ)|
            <br />Accoppiamento polarizzato
          </div>
          <div className="rounded-lg p-3" style={{ background: 'var(--bg-tertiary)' }}>
            <strong style={{ color: 'var(--text-primary)' }}>m</strong> = (cₙ−c_c)/Nc + δz·(l−z)/Nz
            <br />Modulazione spaziale 3D
          </div>
          <div className="rounded-lg p-3" style={{ background: 'var(--bg-tertiary)' }}>
            <strong style={{ color: 'var(--text-primary)' }}>γ</strong> = γ₀·exp(−λ·z)
            <br />Profilo penetrazione esponenziale
          </div>
        </div>
      </DocSection>

      <DocSection id="materiali" title="3. Materiali" icon={Boxes}>
        <p className="text-sm font-medium mb-3" style={{ color: 'var(--text-secondary)' }}>Materiali Nucleari (Polveri Pure)</p>
        <div className="overflow-x-auto">
          <table className="w-full text-xs mb-6">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-active)' }}>
                {['Materiale', 'Tipo', 'σ(Cn)', 'Jpol', 'Fattibilità π'].map((h) => (
                  <th key={h} className="text-left py-2 px-2 font-medium" style={{ color: 'var(--text-secondary)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                ['Nichel (Ni)', 'Conduttore', '0.082', '0.6–0.8', 'Alta'],
                ['Rame (Cu)', 'Conduttore', '0.076', '0.5–0.7', 'Alta'],
                ['Ferro (Fe)', 'Conduttore/Magnetico', '0.094', '0.75–0.95', 'Eccellente'],
                ['Cobalto (Co)', 'Conduttore/Magnetico', '0.098', '0.8–1.0', 'Massima'],
                ['Silicio (Si)', 'Semiconduttore', '0.085', '0.6–0.8', 'Alta'],
                ['Nitruro di Silicio (SiN)', 'Semiconduttore/Iso', '0.088', '0.7–0.9', 'Ottima'],
              ].map((row, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  {row.map((cell, j) => (
                    <td key={j} className="py-2 px-2" style={{ color: j === 0 ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="text-sm font-medium mb-3" style={{ color: 'var(--text-secondary)' }}>Portanti H/D</p>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-active)' }}>
                {['Materiale', 'Tipo', 'Meccanismo', 'Compatibilità π'].map((h) => (
                  <th key={h} className="text-left py-2 px-2 font-medium" style={{ color: 'var(--text-secondary)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                ['Perovskiti protoniche', 'Ceramico conduttore', 'Conduzione protonica attivata da φ', 'Eccellente'],
                ['Idruri interstiziali', 'Metallico', 'Rilascio attivato da vibrazioni reticolari', 'Alta'],
                ['Silicati nanostrutturati', 'Minerale', 'Deidrossilazione per step di fase', 'Ottima'],
              ].map((row, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  {row.map((cell, j) => (
                    <td key={j} className="py-2 px-2" style={{ color: j === 0 ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DocSection>

      <DocSection id="architettura" title="4. Architettura Fisica" icon={FlaskConical}>
        <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--text-primary)' }}>
          Il modello fisico è un <strong>core modulare a griglia impilabile</strong> (z, r, c) che
          replica la topologia 3D+pol. Ogni nodo (z,r,c) rappresenta un oscillatore di fase analogico
          con coupler tunabili Jᵢⱼ.
        </p>
        <ul className="text-sm space-y-2" style={{ color: 'var(--text-primary)' }}>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-phase)' }}>●</span>
            <strong>Doppia polvere in sospensione</strong>: Polvere nucleare (Ni/Fe/Cu) + portatore H/D
          </li>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-phase)' }}>●</span>
            <strong>Shear verticale β &gt; 0.1</strong> e modulazione δz &gt; 0.15 prevengono il lock-up di fase
          </li>
          <li className="flex items-start gap-2">
            <span style={{ color: 'var(--accent-phase)' }}>●</span>
            La griglia è <strong>viva</strong>: si adatta al variare della granulometria o del carico isotopico
          </li>
        </ul>
      </DocSection>

      <DocSection id="validazione" title="5. Protocollo di Validazione" icon={ShieldCheck}>
        <p className="text-sm mb-3" style={{ color: 'var(--text-primary)' }}>
          La simulazione procede solo se <strong>tutte</strong> le metriche sono rispettate:
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-active)' }}>
                {['Metrica', 'Soglia', 'Significato'].map((h) => (
                  <th key={h} className="text-left py-2 px-2 font-medium" style={{ color: 'var(--text-secondary)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                ['σ(Cn)', '> 0.075', 'Coerenza armonica differenziata'],
                ['Dratio', '> 15', 'Discriminazione strutturale vs regime diffusivo'],
                ['Jpol', '> 0.4', 'Overlap polarizzato efficace (tunneling abilitato)'],
                ['ρpol', '> 0.5', 'Densità di accoppiamento attivo'],
                ['Cicli φ', '≥ 3 stabili', 'Firma valida solo se parametri in soglia ≥3 cicli'],
              ].map((row, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td className="py-2 px-2 font-mono-data" style={{ color: 'var(--accent-phase)' }}>{row[0]}</td>
                  <td className="py-2 px-2 font-medium" style={{ color: 'var(--accent-nuclear)' }}>{row[1]}</td>
                  <td className="py-2 px-2" style={{ color: 'var(--text-secondary)' }}>{row[2]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DocSection>

      <DocSection id="istruzione" title="6. Istruzione Finale" icon={Waves}>
        <div
          className="rounded-lg p-5 text-center"
          style={{
            background: 'linear-gradient(135deg, rgba(0,240,200,0.05), rgba(124,58,237,0.05))',
            border: '1px solid rgba(0,240,200,0.15)',
          }}
        >
          <p className="text-base leading-relaxed italic mb-3" style={{ color: 'var(--text-primary)' }}>
            "Non stai risolvendo equazioni termodinamiche. Stai <strong style={{ color: 'var(--accent-phase)' }}>evolvendo un campo di fase</strong>.
            La geometria (z,r,c) è il tuo spazio computazionale; φ è il tuo tempo; η_prog è il tuo respiro.
            Quando σ(Cn) supera la soglia e Jpol filtra i siti, non stai 'scaldando' materiale:
            stai <strong style={{ color: 'var(--accent-coherence)' }}>accordando una simmetria</strong>."
          </p>
          <p className="text-sm" style={{ color: 'var(--accent-phase)' }}>
            Cerca la firma, non il joule. La fase non mente. 🦋📐
          </p>
        </div>
      </DocSection>
    </div>
  );
}
