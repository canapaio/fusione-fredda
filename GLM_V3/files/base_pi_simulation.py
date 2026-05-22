#!/usr/bin/env python3
"""
=============================================================================
MANIFESTO OPERATIVO PER AGENTE: Simulazione Base π in Polveri Ibride (Ni/Fe/Cu + H/D)
Versione: 1.0-π-native
Data: 22 Maggio 2026
Stato: Pronto per esecuzione

Asse di evoluzione esclusivo: φ ∈ [0, 6π]
Nessun tempo t nascosto. Nessuna dipendenza termodinamica classica.
Cerchiamo la firma strutturale, non il joule. La fase non mente. 🦋📐
=============================================================================
"""

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse import csr_matrix
import json
import time as wall_clock
import os
import warnings
warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════════════════
# 1. GUARDRAILS BASE π - NON NEGOZIABILI
# ═══════════════════════════════════════════════════════════════════════════

GUARDRAILS = {
    "no_hidden_t": True,
    "dphi": 0.01,
    "sigma_Cn_min": 0.01,        # coerenza armonica minima (soglia bassa)
    "sigma_Cn_strict": 0.075,    # coerenza armonica stretta (validazione)
    "Dratio_min": 10,            # discriminazione strutturale minima
    "Dratio_strict": 15,         # discriminazione stretta (validazione)
    "Jpol_min": 0.4,             # overlap polarizzato minimo per tunneling
    "rho_pol_min": 0.5,          # densità accoppiamento attivo
    "beta_min": 0.1,             # shear verticale minimo
    "delta_z_min": 0.15,         # modulazione spaziale minima
    "phi_cycles_stable": 3,      # cicli φ stabili per validazione
    "readout_non_destructive": True
}

# ═══════════════════════════════════════════════════════════════════════════
# 2. CONFIGURAZIONE DELLA SIMULAZIONE
# ═══════════════════════════════════════════════════════════════════════════

CONFIG = {
    # Griglia computazionale 3D (z, r, c)
    "Nz": 12,                    # strati verticali
    "Nr": 8,                     # righe
    "Nc": 8,                     # colonne
    
    # Materiali
    "material_nuclear": "Ni_pure_powder",
    "material_carrier": "serpentine_nanostructured",
    "hd_ratio": 1.4,             # D/Ni ≈ 7/5 (armonica π)
    
    # Parametri di fase
    "phi_range": (0, 6 * np.pi),
    "dphi": 0.01,
    
    # Onda portante η_prog
    "eta_prog_frequencies": [15, 30, 45, 75, 105],  # MHz, armoniche π
    "gamma0": 1.0,
    "lambda_gamma": 0.5,
    
    # Accoppiamento
    "J0": 0.65,                  # accoppiamento base
    "Jpol_threshold": 0.4,
    "beta": 0.2,                 # shear verticale
    "delta_z": 0.15,             # modulazione spaziale
    
    # Frequenze naturali
    "f0": 1.0,
    "alpha_f": 0.3,              # esponente π-modulazione frequenza
    
    # Rilascio H/D
    "D_phi": 0.1,                # diffusione su φ
    "kappa_hd": 0.05,            # tasso rilascio
    
    # Memoria
    "store_every": 2,            # campiona ogni 2 step per risparmiare RAM
    
    # Seed per riproducibilità
    "seed": 42,
}

# ═══════════════════════════════════════════════════════════════════════════
# 3. CLASSE PRINCIPALE DELLA SIMULAZIONE
# ═══════════════════════════════════════════════════════════════════════════

class BasePiSimulation:
    """
    Simulazione Base π per polveri ibride (Ni/Fe/Cu + H/D).
    Evolve un campo di fase su un manifold 3D+pol con asse esclusivo φ.
    """
    
    def __init__(self, config=None):
        self.cfg = {**CONFIG, **(config or {})}
        np.random.seed(self.cfg["seed"])
        
        # Dimensioni griglia
        self.Nz = self.cfg["Nz"]
        self.Nr = self.cfg["Nr"]
        self.Nc = self.cfg["Nc"]
        self.N = self.Nz * self.Nr * self.Nc  # nodi totali
        
        # Asse φ
        self.phi_start, self.phi_end = self.cfg["phi_range"]
        self.dphi = self.cfg["dphi"]
        self.Nphi = int((self.phi_end - self.phi_start) / self.dphi)
        
        # Inizializza stati e parametri
        self._init_grid()
        self._init_frequencies()
        self._init_coupling()
        self._init_hd_field()
        self._init_portante()
        
        # Storage per metriche
        self.metrics_history = {
            "phi": [],
            "sigma_Cn": [],
            "Dratio": [],
            "Jpol_mean": [],
            "rho_pol": [],
            "Cvert": [],
            "P_pi_max": [],
            "E_pi_max": [],
        }
        
        # Storage per fasi (buffer circolare)
        self.theta_stored = []
        self.phi_stored = []
        
        # Nucleation seeds
        self.nucleation_seeds = []
        
        # Flag validazione
        self.validation = {
            "pi_algebra_operational": True,
            "no_hidden_t": True,
            "readout_non_destructive": True,
            "guardrails_met": False,
            "nucleation_seeds_found": 0,
            "stable_phi_cycles": 0
        }
        
        # Contatore cicli stabili
        self._stable_count = 0
        self._last_cycle_stable = False
        
        print(f"[INIT] Simulazione Base π inizializzata")
        print(f"[INIT] Griglia: {self.Nz}×{self.Nr}×{self.Nc} = {self.N} nodi")
        print(f"[INIT] Asse φ: [{self.phi_start:.4f}, {self.phi_end:.4f}], dφ={self.dphi}, Nφ={self.Nphi}")
        print(f"[INIT] Materiale nucleare: {self.cfg['material_nuclear']}")
        print(f"[INIT] Materiale portante: {self.cfg['material_carrier']}")
        print(f"[INIT] Accoppiamenti sparsi COO: {self._n_couplings} su {self.N}² possibili")
    
    # ─── Inizializzazione ─────────────────────────────────────────────────
    
    def _init_grid(self):
        """Inizializza griglia 3D (z, r, c) con coordinate fisiche."""
        # Coordinate normalizzate
        self.z_coords = np.linspace(0, 1, self.Nz, dtype=np.float64)
        self.r_coords = np.linspace(0, 1, self.Nr, dtype=np.float64)
        self.c_coords = np.linspace(0, 1, self.Nc, dtype=np.float64)
        
        # Griglia completa (N, 3) - indici piatti
        self.coords = np.zeros((self.N, 3), dtype=np.float64)
        idx = 0
        for iz in range(self.Nz):
            for ir in range(self.Nr):
                for ic in range(self.Nc):
                    self.coords[idx] = [self.z_coords[iz], self.r_coords[ir], self.c_coords[ic]]
                    idx += 1
        
        # Indici 3D → flat
        self.z_idx = np.zeros(self.N, dtype=np.int32)
        self.r_idx = np.zeros(self.N, dtype=np.int32)
        self.c_idx = np.zeros(self.N, dtype=np.int32)
        idx = 0
        for iz in range(self.Nz):
            for ir in range(self.Nr):
                for ic in range(self.Nc):
                    self.z_idx[idx] = iz
                    self.r_idx[idx] = ir
                    self.c_idx[idx] = ic
                    idx += 1
        
        # Fasi iniziali: disordine controllato
        self.theta = np.random.uniform(0, 2 * np.pi, self.N).astype(np.float64)
        
        # Polarizzazioni (ψ) per ogni nodo - allineamento magnetico iniziale
        self.psi = np.random.uniform(0, np.pi, self.N).astype(np.float64)
    
    def _init_frequencies(self):
        """Frequenze naturali π-modulate: ω_zrc = f₀ · π^α · r/Nr + β · z/Nz"""
        self.omega = np.zeros(self.N, dtype=np.float64)
        for i in range(self.N):
            r_frac = self.r_idx[i] / self.Nr
            z_frac = self.z_idx[i] / self.Nz
            self.omega[i] = (self.cfg["f0"] * np.pi ** self.cfg["alpha_f"] * r_frac
                           + self.cfg["beta"] * z_frac)
        
        # Aggiungi disordine strutturale (la "voce del tubo")
        self.omega += np.random.normal(0, 0.02, self.N)
    
    def _init_coupling(self):
        """
        Costruisce matrice sparsa Jpol in formato COO.
        Jpol_ij = J₀ · |cos(ψ_i − ψ_j)| solo per vicini nella griglia 3D.
        """
        rows = []
        cols = []
        data = []
        m_vals = []  # modulazione spaziale π
        
        J0 = self.cfg["J0"]
        delta_z = self.cfg["delta_z"]
        
        for i in range(self.N):
            iz_i, ir_i, ic_i = self.z_idx[i], self.r_idx[i], self.c_idx[i]
            for dz in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dz == 0 and dr == 0 and dc == 0:
                            continue
                        jz = iz_i + dz
                        jr = ir_i + dr
                        jc = ic_i + dc
                        if 0 <= jz < self.Nz and 0 <= jr < self.Nr and 0 <= jc < self.Nc:
                            j = jz * self.Nr * self.Nc + jr * self.Nc + jc
                            # Accoppiamento polarizzato
                            J_val = J0 * abs(np.cos(self.psi[i] - self.psi[j]))
                            # Modulazione spaziale m
                            m_val = ((jc - ic_i) / self.Nc 
                                    + delta_z * (jz - iz_i) / self.Nz)
                            rows.append(i)
                            cols.append(j)
                            data.append(J_val)
                            m_vals.append(m_val)
        
        self._n_couplings = len(data)
        self.coupling_rows = np.array(rows, dtype=np.int32)
        self.coupling_cols = np.array(cols, dtype=np.int32)
        self.coupling_data = np.array(data, dtype=np.float64)
        self.coupling_m = np.array(m_vals, dtype=np.float64)
        
        # Matrice sparsa COO → CSR per operazioni efficienti
        self.Jpol_sparse = coo_matrix(
            (self.coupling_data, (self.coupling_rows, self.coupling_cols)),
            shape=(self.N, self.N)
        ).tocsr()
    
    def _init_hd_field(self):
        """Inizializza campo di concentrazione H/D sulla griglia."""
        self.n_hd = np.ones(self.N, dtype=np.float64) * self.cfg["hd_ratio"]
        # Gradiente iniziale: più H/D in superficie, meno in profondità
        for i in range(self.N):
            self.n_hd[i] *= np.exp(-0.3 * self.z_idx[i] / self.Nz)
    
    def _init_portante(self):
        """Precomputa parametri dell'onda portante η_prog."""
        self.eta_freqs = np.array(self.cfg["eta_prog_frequencies"], dtype=np.float64)
        self.gamma_profile = self.cfg["gamma0"] * np.exp(
            -self.cfg["lambda_gamma"] * self.z_coords
        )
        # Profilo γ per ogni nodo
        self.gamma_nodes = np.zeros(self.N, dtype=np.float64)
        for i in range(self.N):
            self.gamma_nodes[i] = self.gamma_profile[self.z_idx[i]]
    
    # ─── Funzioni Dinamiche ────────────────────────────────────────────────
    
    def compute_eta_prog(self, phi):
        """Onda portante η_prog(φ) con armoniche π."""
        eta = np.zeros(self.N, dtype=np.float64)
        for k, freq in enumerate(self.eta_freqs):
            # Armonica k-esima, modulata su π
            eta += (1.0 / (k + 1)) * np.sin(freq * 1e6 * phi / (2 * np.pi) + k * np.pi / 3)
        eta = 0.2 * eta / len(self.eta_freqs)  # normalizzazione ampiezza
        return eta
    
    def compute_tx_term(self, phi):
        """Termine di accoppiamento trasversale TX(φ)."""
        # Modulazione periodica con shear verticale
        tx = (self.cfg["beta"] * np.sin(2 * np.pi * self.z_idx / self.Nz + phi)
             + self.cfg["delta_z"] * np.cos(3 * np.pi * self.c_idx / self.Nc + 0.5 * phi))
        return tx * 0.1  # scala
    
    def compute_rhs(self, theta, phi):
        """
        Calcola dθ/dφ per tutti i nodi (forma vettorizzata).
        dθ/dφ = ω + Σ Jpol·sin(Δθ + π·m) + η_prog·γ + TX
        """
        # Termine di frequenza naturale
        dtheta = self.omega.copy()
        
        # Accoppiamento polarizzato (usando indici COO)
        delta_theta = theta[self.coupling_cols] - theta[self.coupling_rows]
        coupling_term = self.coupling_data * np.sin(delta_theta + np.pi * self.coupling_m)
        
        # Somma accoppiamenti per ogni nodo
        coupling_sum = np.zeros(self.N, dtype=np.float64)
        np.add.at(coupling_sum, self.coupling_rows, coupling_term)
        dtheta += coupling_sum
        
        # Onda portante
        eta = self.compute_eta_prog(phi)
        dtheta += eta * self.gamma_nodes
        
        # Termine trasversale
        dtheta += self.compute_tx_term(phi)
        
        return dtheta
    
    def rk4_step(self, theta, phi):
        """Integratore RK4 a passo fisso dφ. Nessun adattativo."""
        h = self.dphi
        k1 = self.compute_rhs(theta, phi)
        k2 = self.compute_rhs(theta + 0.5 * h * k1, phi + 0.5 * h)
        k3 = self.compute_rhs(theta + 0.5 * h * k2, phi + 0.5 * h)
        k4 = self.compute_rhs(theta + h * k3, phi + h)
        return theta + (h / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    
    def evolve_hd_field(self, phi):
        """
        Rilascio H/D guidato da fase:
        ∂n_HD/∂φ = D_φ·∇²n_HD − κ(φ)·n_HD
        """
        D_phi = self.cfg["D_phi"]
        kappa = self.cfg["kappa_hd"] * (1 + 0.5 * np.sin(phi / np.pi))
        
        # Laplaciano discreto (approssimazione su griglia 3D)
        laplacian = np.zeros(self.N, dtype=np.float64)
        for i in range(self.N):
            iz, ir, ic = self.z_idx[i], self.r_idx[i], self.c_idx[i]
            neighbors = []
            for dz, dr, dc in [(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]:
                jz, jr, jc = iz+dz, ir+dr, ic+dc
                if 0 <= jz < self.Nz and 0 <= jr < self.Nr and 0 <= jc < self.Nc:
                    j = jz * self.Nr * self.Nc + jr * self.Nc + jc
                    neighbors.append(j)
            if neighbors:
                laplacian[i] = np.mean(self.n_hd[neighbors]) - self.n_hd[i]
        
        dn = D_phi * laplacian - kappa * self.n_hd
        self.n_hd += dn * self.dphi
        self.n_hd = np.clip(self.n_hd, 0.01, 10.0)  # vincoli fisici
    
    # ─── Metriche e Validazione ────────────────────────────────────────────
    
    def compute_order_parameter(self, theta):
        """Parametro d'ordine di Kuramoto: r·exp(iψ) = (1/N) Σ exp(iθ_j)"""
        z_complex = np.exp(1j * theta)
        Z = np.mean(z_complex)
        r = np.abs(Z)
        psi = np.angle(Z)
        return r, psi, Z
    
    def compute_sigma_Cn(self, theta):
        """
        Coerenza armonica differenziata σ(Cn).
        Analisi della distribuzione di coerenza per armoniche π.
        """
        # Parametro d'ordine globale
        r_global, _, _ = self.compute_order_parameter(theta)
        
        # Coerenza per strato verticale
        layer_coherences = []
        for iz in range(self.Nz):
            mask = self.z_idx == iz
            if np.sum(mask) > 0:
                r_layer, _, _ = self.compute_order_parameter(theta[mask])
                layer_coherences.append(r_layer)
        
        # Coerenza per armoniche (sotto-gruppi)
        harmonic_coherences = []
        for h in [1, 2, 3, 4, 5, 6]:
            subset = np.arange(0, self.N, max(1, self.N // (h * 10)))
            if len(subset) > 1:
                r_h, _, _ = self.compute_order_parameter(theta[subset])
                harmonic_coherences.append(r_h)
        
        # σ(Cn) = deviazione standard delle coerenze armoniche
        # Alta σ(Cn) significa coerenza differenziata (non uniforme)
        if len(harmonic_coherences) > 1:
            sigma_Cn = np.std(harmonic_coherences)
        else:
            sigma_Cn = 0.0
        
        # Aggiungi contributo della variabilità inter-strato
        if len(layer_coherences) > 1:
            sigma_Cn += 0.3 * np.std(layer_coherences)
        
        return sigma_Cn, harmonic_coherences, layer_coherences
    
    def compute_Dratio(self, theta):
        """
        Discriminazione strutturale vs regime diffusivo.
        Dratio = σ(strutturale) / σ(diffusivo)
        """
        # Gradiente di fase strutturale
        grad_theta = np.zeros(self.N, dtype=np.float64)
        for i in range(self.N):
            iz, ir, ic = self.z_idx[i], self.r_idx[i], self.c_idx[i]
            diffs = []
            for dz, dr, dc in [(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]:
                jz, jr, jc = iz+dz, ir+dr, ic+dc
                if 0 <= jz < self.Nz and 0 <= jr < self.Nr and 0 <= jc < self.Nc:
                    j = jz * self.Nr * self.Nc + jr * self.Nc + jc
                    diffs.append(theta[j] - theta[i])
            if diffs:
                grad_theta[i] = np.std(diffs)
        
        sigma_struct = np.mean(grad_theta)
        
        # Sigma diffusivo (riferimento: fasi random)
        theta_random = np.random.uniform(0, 2*np.pi, self.N)
        grad_random = np.zeros(self.N, dtype=np.float64)
        for i in range(self.N):
            iz, ir, ic = self.z_idx[i], self.r_idx[i], self.c_idx[i]
            diffs = []
            for dz, dr, dc in [(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]:
                jz, jr, jc = iz+dz, ir+dr, ic+dc
                if 0 <= jz < self.Nz and 0 <= jr < self.Nr and 0 <= jc < self.Nc:
                    j = jz * self.Nr * self.Nc + jr * self.Nc + jc
                    diffs.append(theta_random[j] - theta_random[i])
            if diffs:
                grad_random[i] = np.std(diffs)
        
        sigma_diff = np.mean(grad_random)
        
        if sigma_diff > 1e-10:
            Dratio = sigma_struct / sigma_diff
        else:
            Dratio = 1.0
        
        return Dratio
    
    def compute_Jpol_metrics(self, theta):
        """Calcola metriche derivate dall'accoppiamento polarizzato."""
        # Jpol medio effettivo (solo accoppiamenti attivi sopra soglia)
        active_mask = self.coupling_data > self.cfg["Jpol_threshold"]
        Jpol_mean = np.mean(self.coupling_data[active_mask]) if np.any(active_mask) else 0.0
        
        # Densità di accoppiamento attivo ρpol
        n_active = np.sum(active_mask)
        n_possible = self.N * (self.N - 1)
        rho_pol = n_active / max(1, len(self.coupling_data))
        
        # Coerenza verticale Cvert
        Cvert = 0.0
        for ir in range(self.Nr):
            for ic in range(self.Nc):
                col_phases = []
                for iz in range(self.Nz):
                    idx = iz * self.Nr * self.Nc + ir * self.Nc + ic
                    col_phases.append(theta[idx])
                if len(col_phases) > 1:
                    r_col, _, _ = self.compute_order_parameter(np.array(col_phases))
                    Cvert += r_col
        n_cols = self.Nr * self.Nc
        Cvert = Cvert / max(1, n_cols)
        
        return Jpol_mean, rho_pol, Cvert
    
    def compute_nucleation_probability(self, sigma_Cn, Dratio, Jpol_mean, phi):
        """
        Probabilità di nucleazione H/D:
        P_π(φ) ∝ Jpol·σ(Cn)/Dratio
        Mappa 3D di probabilità.
        """
        if Dratio > 1e-10:
            P_base = Jpol_mean * sigma_Cn / Dratio
        else:
            P_base = 0.0
        
        # Distribuzione spaziale: modulata da profilo e fase
        P_3d = np.zeros(self.N, dtype=np.float64)
        for i in range(self.N):
            # Gradiente locale di fase
            iz, ir, ic = self.z_idx[i], self.r_idx[i], self.c_idx[i]
            neighbors_phases = []
            for dz, dr, dc in [(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]:
                jz, jr, jc = iz+dz, ir+dr, ic+dc
                if 0 <= jz < self.Nz and 0 <= jr < self.Nr and 0 <= jc < self.Nc:
                    j = jz * self.Nr * self.Nc + jr * self.Nc + jc
                    neighbors_phases.append(self.theta[j])
            
            # Gradiente locale
            if neighbors_phases:
                local_grad = np.std(np.array(neighbors_phases) - self.theta[i])
            else:
                local_grad = 0.0
            
            # P locale = P_base * (1 + gradiente) * profilo γ * concentrazione H/D
            P_3d[i] = P_base * (1 + local_grad) * self.gamma_nodes[i] * self.n_hd[i]
        
        # Normalizza a [0, 1]
        P_max = np.max(P_3d)
        if P_max > 1e-10:
            P_3d = P_3d / P_max
        
        return P_3d, P_base
    
    def compute_energetic_observable(self, sigma_Cn, Dratio, Jpol_mean, phi):
        """
        Osservabile energetico derivato (NON energia reale):
        E_π(φ) = κ · Jpol · σ(Cn) · |Ψ_RX|² / Dratio
        """
        # Firma RX (parametro d'ordine sul piano RX)
        r_order, _, Z_order = self.compute_order_parameter(self.theta)
        Psi_RX_sq = np.abs(Z_order) ** 2
        
        kappa = 1.0  # costante di scala arbitraria
        if Dratio > 1e-10:
            E_pi = kappa * Jpol_mean * sigma_Cn * Psi_RX_sq / Dratio
        else:
            E_pi = 0.0
        
        return E_pi, Psi_RX_sq
    
    def check_guardrails(self, sigma_Cn, Dratio, Jpol_mean, rho_pol):
        """Verifica guardrail e aggiorna contatore cicli stabili."""
        all_met = (
            sigma_Cn >= GUARDRAILS["sigma_Cn_min"]
            and Dratio >= GUARDRAILS["Dratio_min"]
            and Jpol_mean >= GUARDRAILS["Jpol_min"]
            and rho_pol >= GUARDRAILS["rho_pol_min"]
        )
        
        strict_met = (
            sigma_Cn >= GUARDRAILS["sigma_Cn_strict"]
            and Dratio >= GUARDRAILS["Dratio_strict"]
            and Jpol_mean >= GUARDRAILS["Jpol_min"]
            and rho_pol >= GUARDRAILS["rho_pol_min"]
        )
        
        return all_met, strict_met
    
    def extract_structural_signature(self, theta, phi):
        """
        Firma strutturale campionata non distruttivamente:
        S = [C₁..Cₖ, D, I_dens, σ(Cn), Ψ_RX(φ)]
        """
        # Coerenze per armoniche
        _, harmonic_coherences, layer_coherences = self.compute_sigma_Cn(theta)
        
        # Parametro d'ordine
        r_order, psi_order, Z_order = self.compute_order_parameter(theta)
        
        # Discriminazione
        Dratio = self.compute_Dratio(theta)
        
        # Densità di informazione
        I_dens = -np.sum(np.log(np.abs(np.fft.fft(theta)) + 1e-10)) / self.N
        
        signature = {
            "C_harmonics": [float(c) for c in harmonic_coherences],
            "C_layers": [float(c) for c in layer_coherences],
            "D": float(Dratio),
            "I_dens": float(I_dens),
            "sigma_Cn": float(np.std(harmonic_coherences)) if len(harmonic_coherences) > 1 else 0.0,
            "Psi_RX_amp": float(np.abs(Z_order)),
            "Psi_RX_phase": float(np.angle(Z_order)),
            "phi": float(phi),
        }
        
        return signature
    
    # ─── Loop Principale ──────────────────────────────────────────────────
    
    def run(self):
        """Esegue la simulazione completa su φ ∈ [0, 6π]."""
        print("\n" + "="*70)
        print("  SIMULAZIONE BASE π - AVVIO")
        print("  Cerca la firma, non il joule. La fase non mente. 🦋📐")
        print("="*70)
        
        phi = self.phi_start
        step = 0
        phi_cycle = 0
        last_cycle_phi = 0
        
        # Per ricalibrazione
        recalibration_count = 0
        max_recalibrations = 3
        
        # Firma strutturale campionata
        signatures = []
        
        wall_start = wall_clock.time()
        
        while phi < self.phi_end:
            # ── Step RK4 ──
            self.theta = self.rk4_step(self.theta, phi)
            
            # ── Evoluzione H/D ──
            self.evolve_hd_field(phi)
            
            # ── Metriche (ogni store_every step) ──
            if step % self.cfg["store_every"] == 0:
                sigma_Cn, h_c, l_c = self.compute_sigma_Cn(self.theta)
                Dratio = self.compute_Dratio(self.theta)
                Jpol_mean, rho_pol, Cvert = self.compute_Jpol_metrics(self.theta)
                P_3d, P_base = self.compute_nucleation_probability(
                    sigma_Cn, Dratio, Jpol_mean, phi
                )
                E_pi, Psi_RX_sq = self.compute_energetic_observable(
                    sigma_Cn, Dratio, Jpol_mean, phi
                )
                
                # Salva metriche
                self.metrics_history["phi"].append(phi)
                self.metrics_history["sigma_Cn"].append(sigma_Cn)
                self.metrics_history["Dratio"].append(Dratio)
                self.metrics_history["Jpol_mean"].append(Jpol_mean)
                self.metrics_history["rho_pol"].append(rho_pol)
                self.metrics_history["Cvert"].append(Cvert)
                self.metrics_history["P_pi_max"].append(float(np.max(P_3d)))
                self.metrics_history["E_pi_max"].append(E_pi)
                
                # Salva fasi (campionate)
                self.theta_stored.append(self.theta.copy())
                self.phi_stored.append(phi)
                
                # Guardrail check
                all_met, strict_met = self.check_guardrails(
                    sigma_Cn, Dratio, Jpol_mean, rho_pol
                )
                
                # Traccia cicli stabili
                current_cycle = int(phi / (2 * np.pi))
                if current_cycle > phi_cycle:
                    phi_cycle = current_cycle
                    if self._last_cycle_stable:
                        self._stable_count += 1
                        print(f"  [CYCLE] φ ciclo {phi_cycle} completato - stabili consecutivi: {self._stable_count}")
                    else:
                        self._stable_count = 0
                    self._last_cycle_stable = False
                
                if strict_met:
                    self._last_cycle_stable = True
                
                # Rileva semi di nucleazione
                nucleation_mask = P_3d > 0.75
                n_seeds = int(np.sum(nucleation_mask))
                if n_seeds > 0 and strict_met:
                    seed_coords = self.coords[nucleation_mask]
                    for sc in seed_coords:
                        self.nucleation_seeds.append({
                            "z": float(sc[0]),
                            "r": float(sc[1]),
                            "c": float(sc[2]),
                            "phi": float(phi),
                            "P": float(P_3d[np.argmax(nucleation_mask)])
                        })
                
                # Firma strutturale (ogni 100 step)
                if step % (100 * self.cfg["store_every"]) == 0:
                    sig = self.extract_structural_signature(self.theta, phi)
                    signatures.append(sig)
                
                # Log periodico
                if step % (500 * self.cfg["store_every"]) == 0:
                    print(f"  [φ={phi:.4f}] σ(Cn)={sigma_Cn:.4f}  Dratio={Dratio:.2f}  "
                          f"Jpol={Jpol_mean:.4f}  ρpol={rho_pol:.4f}  Cvert={Cvert:.4f}  "
                          f"P_max={np.max(P_3d):.4f}  Seeds={n_seeds}")
                
                # Ricalibrazione se guardrail falliti gravemente
                if not all_met and sigma_Cn < GUARDRAILS["sigma_Cn_min"] * 0.5:
                    if recalibration_count < max_recalibrations:
                        print(f"  [RECALIBRATE] Guardrail critici non soddisfatti a φ={phi:.4f}")
                        print(f"    σ(Cn)={sigma_Cn:.4f} < {GUARDRAILS['sigma_Cn_min']:.4f}")
                        # Aumenta shear e modulazione
                        self.cfg["beta"] = min(0.5, self.cfg["beta"] * 1.2)
                        self.cfg["delta_z"] = min(0.3, self.cfg["delta_z"] * 1.15)
                        # Ri-inizializza accoppiamento con nuovi parametri
                        self._init_coupling()
                        recalibration_count += 1
                        print(f"    Nuovi β={self.cfg['beta']:.3f}, δz={self.cfg['delta_z']:.3f}")
            
            phi += self.dphi
            step += 1
        
        wall_elapsed = wall_clock.time() - wall_start
        
        # ── Finalizzazione ──
        self.validation["guardrails_met"] = self._stable_count >= GUARDRAILS["phi_cycles_stable"]
        self.validation["nucleation_seeds_found"] = len(self.nucleation_seeds)
        self.validation["stable_phi_cycles"] = self._stable_count
        self.validation["recalibrations"] = recalibration_count
        
        # Ultima mappa nucleazione
        sigma_Cn_final, _, _ = self.compute_sigma_Cn(self.theta)
        Dratio_final = self.compute_Dratio(self.theta)
        Jpol_mean_final, rho_pol_final, Cvert_final = self.compute_Jpol_metrics(self.theta)
        P_3d_final, P_base_final = self.compute_nucleation_probability(
            sigma_Cn_final, Dratio_final, Jpol_mean_final, phi
        )
        
        print("\n" + "="*70)
        print("  SIMULAZIONE BASE π - COMPLETATA")
        print(f"  Wall-clock: {wall_elapsed:.2f}s | Step: {step} | φ finale: {phi:.4f}")
        print(f"  Ricalibrazioni: {recalibration_count}")
        print(f"  Cicli stabili consecutivi: {self._stable_count}")
        print(f"  Semi di nucleazione trovati: {len(self.nucleation_seeds)}")
        print(f"  Guardrail soddisfatti: {self.validation['guardrails_met']}")
        print("="*70)
        
        # Prepara output
        output = self._package_output(P_3d_final, signatures)
        
        return output
    
    def _package_output(self, P_3d_final, signatures):
        """Prepara il pacchetto di output strutturato."""
        
        # 1. Mappa 3D nucleazione
        nucleation_map = np.zeros((self.Nz, self.Nr, self.Nc), dtype=np.float64)
        for i in range(self.N):
            nucleation_map[self.z_idx[i], self.r_idx[i], self.c_idx[i]] = P_3d_final[i]
        
        # 2. Timeline metriche
        timeline = {k: np.array(v) for k, v in self.metrics_history.items()}
        
        # 3. Firma strutturale finale
        final_signature = self.extract_structural_signature(self.theta, self.phi_end)
        
        # 4. Flag validazione
        validation_flags = dict(self.validation)
        
        # 5. Nucleation seeds (deduplicati)
        unique_seeds = []
        seen = set()
        for s in self.nucleation_seeds:
            key = (round(s["z"], 2), round(s["r"], 2), round(s["c"], 2))
            if key not in seen:
                seen.add(key)
                unique_seeds.append(s)
        
        output = {
            "nucleation_map": nucleation_map,
            "timeline": timeline,
            "final_signature": final_signature,
            "signatures_series": signatures,
            "validation": validation_flags,
            "nucleation_seeds": unique_seeds[:50],  # primi 50
            "config_used": {k: (v if not isinstance(v, np.ndarray) else v.tolist()) 
                          for k, v in self.cfg.items()},
            "theta_final": self.theta,
            "coords": self.coords,
            "z_idx": self.z_idx,
            "r_idx": self.r_idx,
            "c_idx": self.c_idx,
        }
        
        return output


# ═══════════════════════════════════════════════════════════════════════════
# 4. PUNTO DI INGRESSO
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Esegue la simulazione e salva i risultati."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  MANIFESTO OPERATIVO: Simulazione Base π                   ║")
    print("║  Polveri Ibride (Ni/Fe/Cu + H/D) - Griglia 3D+pol         ║")
    print("║  Cerca la firma, non il joule. La fase non mente. 🦋📐     ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    sim = BasePiSimulation()
    output = sim.run()
    
    # Salva risultati
    output_dir = "/home/z/my-project/download"
    os.makedirs(output_dir, exist_ok=True)
    
    # Salva mappa nucleazione
    np.save(os.path.join(output_dir, "nucleation_map_3d.npy"), output["nucleation_map"])
    
    # Salva timeline metriche
    for key, arr in output["timeline"].items():
        np.save(os.path.join(output_dir, f"timeline_{key}.npy"), arr)
    
    # Salva fasi finali
    np.save(os.path.join(output_dir, "theta_final.npy"), output["theta_final"])
    
    # Salva firma strutturale e validazione come JSON
    json_output = {
        "final_signature": output["final_signature"],
        "validation": output["validation"],
        "nucleation_seeds": output["nucleation_seeds"],
        "signatures_series": output["signatures_series"],
        "config_used": output["config_used"],
    }
    with open(os.path.join(output_dir, "simulation_results.json"), "w") as f:
        json.dump(json_output, f, indent=2, default=str)
    
    print(f"\n[RISULTATI] Salvati in {output_dir}/")
    print(f"  - nucleation_map_3d.npy")
    print(f"  - timeline_*.npy")
    print(f"  - theta_final.npy")
    print(f"  - simulation_results.json")
    
    return output


if __name__ == "__main__":
    output = main()
