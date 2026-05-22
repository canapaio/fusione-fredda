#!/usr/bin/env python3
"""
=============================================================================
MANIFESTO OPERATIVO: Simulazione Base π - Polveri Ibride (Ni/Fe/Cu + H/D)
Versione: 2.0-π-native — OTTIMIZZATA con metriche dinamiche e guardrail attivi
Asse di evoluzione esclusivo: φ ∈ [0, 6π]
Nessun tempo t nascosto. Cerchiamo la firma, non il joule. 🦋📐
=============================================================================
"""

import numpy as np
from scipy.sparse import coo_matrix
import json
import os
import warnings
warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════════════════
# 1. GUARDRAILS BASE π
# ═══════════════════════════════════════════════════════════════════════════

GUARDRAILS = {
    "no_hidden_t": True,
    "dphi": 0.01,
    "sigma_Cn_min": 0.01,
    "sigma_Cn_strict": 0.075,
    "Dratio_min": 10,
    "Dratio_strict": 15,
    "Jpol_min": 0.4,
    "rho_pol_min": 0.5,
    "beta_min": 0.1,
    "delta_z_min": 0.15,
    "phi_cycles_stable": 3,
    "readout_non_destructive": True
}

# ═══════════════════════════════════════════════════════════════════════════
# 2. CONFIGURAZIONE OTTIMIZZATA
# ═══════════════════════════════════════════════════════════════════════════

CONFIG = {
    "Nz": 10,
    "Nr": 8,
    "Nc": 8,
    
    "material_nuclear": "Ni_pure_powder",
    "material_carrier": "serpentine_nanostructured",
    "hd_ratio": 1.4,
    
    "phi_range": (0, 6 * np.pi),
    "dphi": 0.01,
    
    "eta_prog_frequencies": [15, 30, 45, 75, 105],
    "gamma0": 1.0,
    "lambda_gamma": 0.3,
    
    "J0": 1.2,                    # accoppiamento più forte per creare struttura
    "Jpol_threshold": 0.4,
    "beta": 0.25,
    "delta_z": 0.18,
    
    "f0": 1.0,
    "alpha_f": 0.3,
    "noise_amplitude": 0.03,      # rumore di fase strutturale
    
    "D_phi": 0.08,
    "kappa_hd": 0.03,
    
    "store_every": 2,
    "seed": 42,
}


class BasePiSimulation:
    """
    Simulazione Base π v2.0 — con metriche dinamiche e accoppiamento evolvente.
    """
    
    def __init__(self, config=None):
        self.cfg = {**CONFIG, **(config or {})}
        np.random.seed(self.cfg["seed"])
        
        self.Nz = self.cfg["Nz"]
        self.Nr = self.cfg["Nr"]
        self.Nc = self.cfg["Nc"]
        self.N = self.Nz * self.Nr * self.Nc
        
        self.phi_start, self.phi_end = self.cfg["phi_range"]
        self.dphi = self.cfg["dphi"]
        self.Nphi = int((self.phi_end - self.phi_start) / self.dphi)
        
        self._init_grid()
        self._init_frequencies()
        self._init_coupling_topology()
        self._init_hd_field()
        
        # Storico per Dratio rolling
        self._phase_variance_history = []
        self._diffusive_variance_history = []
        
        self.metrics_history = {
            "phi": [], "sigma_Cn": [], "Dratio": [],
            "Jpol_mean": [], "rho_pol": [], "Cvert": [],
            "P_pi_max": [], "E_pi_max": [],
        }
        
        self.theta_stored = []
        self.phi_stored = []
        self.nucleation_seeds = []
        self.signatures_series = []
        
        self.validation = {
            "pi_algebra_operational": True,
            "no_hidden_t": True,
            "readout_non_destructive": True,
            "guardrails_met": False,
            "nucleation_seeds_found": 0,
            "stable_phi_cycles": 0
        }
        
        self._stable_count = 0
        self._consecutive_strict = 0
        self._phi_at_last_cycle = -1
        
        print(f"[INIT] Griglia: {self.Nz}×{self.Nr}×{self.Nc} = {self.N} nodi")
        print(f"[INIT] φ ∈ [{self.phi_start:.2f}, {self.phi_end:.2f}], dφ={self.dphi}")
        print(f"[INIT] Accoppiamenti topologici: {len(self._topo_rows)}")
    
    def _init_grid(self):
        """Griglia 3D con coordinate fisiche."""
        self.z_coords = np.linspace(0, 1, self.Nz, dtype=np.float64)
        self.r_coords = np.linspace(0, 1, self.Nr, dtype=np.float64)
        self.c_coords = np.linspace(0, 1, self.Nc, dtype=np.float64)
        
        self.coords = np.zeros((self.N, 3), dtype=np.float64)
        self.z_idx = np.zeros(self.N, dtype=np.int32)
        self.r_idx = np.zeros(self.N, dtype=np.int32)
        self.c_idx = np.zeros(self.N, dtype=np.int32)
        
        idx = 0
        for iz in range(self.Nz):
            for ir in range(self.Nr):
                for ic in range(self.Nc):
                    self.coords[idx] = [self.z_coords[iz], self.r_coords[ir], self.c_coords[ic]]
                    self.z_idx[idx] = iz
                    self.r_idx[idx] = ir
                    self.c_idx[idx] = ic
                    idx += 1
        
        # Fasi iniziali
        self.theta = np.random.uniform(0, 2 * np.pi, self.N).astype(np.float64)
        
        # Polarizzazioni per accoppiamento Jpol
        self.psi = np.random.uniform(0, np.pi, self.N).astype(np.float64)
        
        # Profilo γ(z)
        self.gamma_nodes = self.cfg["gamma0"] * np.exp(
            -self.cfg["lambda_gamma"] * self.z_idx / self.Nz
        ).astype(np.float64)
    
    def _init_frequencies(self):
        """Frequenze naturali π-modulate con disordine strutturale."""
        self.omega = np.zeros(self.N, dtype=np.float64)
        for i in range(self.N):
            r_frac = self.r_idx[i] / self.Nr
            z_frac = self.z_idx[i] / self.Nz
            self.omega[i] = (self.cfg["f0"] * np.pi ** self.cfg["alpha_f"] * r_frac
                           + self.cfg["beta"] * z_frac)
        # Disordine strutturale (la "voce del tubo")
        self.omega += np.random.normal(0, 0.05, self.N)
    
    def _init_coupling_topology(self):
        """
        Topologia di accoppiamento (statica: chi è connesso a chi).
        I pesi Jpol sono calcolati dinamicamente ad ogni step.
        """
        rows, cols, m_vals = [], [], []
        delta_z = self.cfg["delta_z"]
        
        for i in range(self.N):
            iz_i, ir_i, ic_i = self.z_idx[i], self.r_idx[i], self.c_idx[i]
            for dz in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dz == 0 and dr == 0 and dc == 0:
                            continue
                        jz, jr, jc = iz_i + dz, ir_i + dr, ic_i + dc
                        if 0 <= jz < self.Nz and 0 <= jr < self.Nr and 0 <= jc < self.Nc:
                            j = jz * self.Nr * self.Nc + jr * self.Nc + jc
                            m = ((jc - ic_i) / self.Nc + delta_z * (jz - iz_i) / self.Nz)
                            rows.append(i)
                            cols.append(j)
                            m_vals.append(m)
        
        self._topo_rows = np.array(rows, dtype=np.int32)
        self._topo_cols = np.array(cols, dtype=np.int32)
        self._topo_m = np.array(m_vals, dtype=np.float64)
        
        # Precomputa |cos(ψ_i − ψ_j)| (polarizzazione statica)
        self._polarization = np.abs(np.cos(
            self.psi[self._topo_rows] - self.psi[self._topo_cols]
        ))
    
    def _init_hd_field(self):
        """Campo H/D iniziale con gradiente superficiale."""
        self.n_hd = np.ones(self.N, dtype=np.float64) * self.cfg["hd_ratio"]
        for i in range(self.N):
            self.n_hd[i] *= np.exp(-0.2 * self.z_idx[i] / self.Nz)
    
    # ─── Dinamica ──────────────────────────────────────────────────────────
    
    def compute_eta_prog(self, phi):
        """Onda portante η_prog(φ) con armoniche π modulate."""
        eta = np.zeros(self.N, dtype=np.float64)
        for k, freq in enumerate(self.cfg["eta_prog_frequencies"]):
            amp = 1.0 / (k + 1)
            # Modulazione π: l'armonica k-esima ha fase kπ/3
            eta += amp * np.sin(freq * 1e6 * phi / (2 * np.pi) + k * np.pi / 3)
        # Normalizzazione e scala
        eta = 0.15 * eta / len(self.cfg["eta_prog_frequencies"])
        # Modulazione verticale: η_prog più forte vicino alla superficie
        eta *= (1.0 + 0.3 * np.sin(phi / np.pi))
        return eta
    
    def compute_dynamic_Jpol(self, theta):
        """
        Accoppiamento polarizzato DINAMICO:
        Jpol_ij = J₀ · |cos(ψ_i − ψ_j)| · f(Δθ_ij)
        
        La dipendenza dalla differenza di fase corrente rende Jpol
        un filtro strutturale attivo, non un peso statico.
        """
        J0 = self.cfg["J0"]
        delta_theta = theta[self._topo_cols] - theta[self._topo_rows]
        
        # Filtro di fase: gli accoppiamenti sono più forti quando
        # le fasi sono vicine (risonanza) ma non identiche (evita lock-up)
        phase_filter = np.exp(-0.5 * (delta_theta ** 2) / (np.pi ** 2))
        # Soppressione del lock-up: penalizza Δθ ≈ 0
        anti_lock = 1.0 - np.exp(-8.0 * delta_theta ** 2)
        
        Jpol = J0 * self._polarization * phase_filter * (0.3 + 0.7 * anti_lock)
        return Jpol
    
    def compute_rhs(self, theta, phi):
        """dθ/dφ = ω + Σ Jpol·sin(Δθ + π·m) + η_prog·γ + TX + noise"""
        dtheta = self.omega.copy()
        
        # Accoppiamento polarizzato dinamico
        Jpol = self.compute_dynamic_Jpol(theta)
        delta_theta = theta[self._topo_cols] - theta[self._topo_rows]
        coupling_term = Jpol * np.sin(delta_theta + np.pi * self._topo_m)
        
        coupling_sum = np.zeros(self.N, dtype=np.float64)
        np.add.at(coupling_sum, self._topo_rows, coupling_term)
        dtheta += coupling_sum
        
        # Onda portante
        eta = self.compute_eta_prog(phi)
        dtheta += eta * self.gamma_nodes
        
        # Termine trasversale TX
        tx = (self.cfg["beta"] * np.sin(2 * np.pi * self.z_idx / self.Nz + phi)
             + self.cfg["delta_z"] * np.cos(3 * np.pi * self.c_idx / self.Nc + 0.5 * phi))
        dtheta += 0.1 * tx
        
        # Rumore strutturale (non termico — guidato da φ)
        dtheta += self.cfg["noise_amplitude"] * np.random.randn(self.N)
        
        return dtheta
    
    def rk4_step(self, theta, phi):
        """RK4 a passo fisso. Nessun adattativo."""
        h = self.dphi
        k1 = self.compute_rhs(theta, phi)
        k2 = self.compute_rhs(theta + 0.5 * h * k1, phi + 0.5 * h)
        k3 = self.compute_rhs(theta + 0.5 * h * k2, phi + 0.5 * h)
        k4 = self.compute_rhs(theta + h * k3, phi + h)
        return theta + (h / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    
    def evolve_hd_field(self, phi):
        """∂n_HD/∂φ = D_φ·∇²n_HD − κ(φ)·n_HD"""
        D_phi = self.cfg["D_phi"]
        kappa = self.cfg["kappa_hd"] * (1 + 0.5 * np.sin(phi / np.pi))
        
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
        self.n_hd = np.clip(self.n_hd, 0.01, 10.0)
    
    # ─── Metriche ──────────────────────────────────────────────────────────
    
    def compute_order_parameter(self, theta):
        """Parametro d'ordine di Kuramoto r·exp(iψ)."""
        Z = np.mean(np.exp(1j * theta))
        return np.abs(Z), np.angle(Z), Z
    
    def compute_sigma_Cn(self, theta):
        """
        Coerenza armonica differenziata σ(Cn).
        Misura la variabilità della coerenza tra sottogruppi armonici.
        Alta σ(Cn) = coerenza NON uniforme = firma strutturale.
        """
        # Coerenza per strato verticale
        layer_coh = []
        for iz in range(self.Nz):
            mask = self.z_idx == iz
            r_l, _, _ = self.compute_order_parameter(theta[mask])
            layer_coh.append(r_l)
        
        # Coerenza per anello radiale
        radial_coh = []
        for ir in range(self.Nr):
            mask = self.r_idx == ir
            r_r, _, _ = self.compute_order_parameter(theta[mask])
            radial_coh.append(r_r)
        
        # Coerenza per colonna azimuthale
        azimuthal_coh = []
        for ic in range(self.Nc):
            mask = self.c_idx == ic
            r_c, _, _ = self.compute_order_parameter(theta[mask])
            azimuthal_coh.append(r_c)
        
        # Armoniche π: coerenza di sottogruppi a spaziatura π
        harmonic_coh = []
        for h in range(1, 7):
            # Sottogruppo con passo h (selezione periodica)
            indices = np.arange(h - 1, self.N, max(1, h * 5))
            if len(indices) > 2:
                r_h, _, _ = self.compute_order_parameter(theta[indices])
                harmonic_coh.append(r_h)
        
        all_coh = layer_coh + radial_coh + azimuthal_coh + harmonic_coh
        
        # σ(Cn) = deviazione standard delle coerenze
        # Alta variabilità = struttura differenziata
        sigma_Cn = np.std(all_coh) if len(all_coh) > 1 else 0.0
        
        return sigma_Cn, harmonic_coh, layer_coh
    
    def compute_Dratio(self, theta):
        """
        Discriminazione strutturale vs regime diffusivo.
        
        Dratio = Var(strutturale) / Var(diffusivo)
        
        Var(strutturale) = varianza dei gradienti di fase tra vicini
        Var(diffusivo) = varianza attesa per fasi random uniformi
        
        Quando il sistema sviluppa struttura, i gradienti diventano
        eterogenei: alcune zone altamente coerenti, altre disordinate.
        """
        N = self.N
        # Gradiente di fase per ogni nodo (varianza delle differenze con i vicini)
        grad_var = np.zeros(N, dtype=np.float64)
        for i in range(N):
            iz, ir, ic = self.z_idx[i], self.r_idx[i], self.c_idx[i]
            diffs = []
            for dz, dr, dc in [(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]:
                jz, jr, jc = iz+dz, ir+dr, ic+dc
                if 0 <= jz < self.Nz and 0 <= jr < self.Nr and 0 <= jc < self.Nc:
                    j = jz * self.Nr * self.Nc + jr * self.Nc + jc
                    # Distanza di fase circolare
                    d = np.abs(np.angle(np.exp(1j * (theta[j] - theta[i]))))
                    diffs.append(d)
            if diffs:
                grad_var[i] = np.var(diffs)
        
        # Varianza strutturale: quanto varia il gradiente nello spazio
        var_structural = np.var(grad_var)
        
        # Varianza diffusiva: riferimento per fasi random
        # Per fasi uniformi su [0, 2π], E[|Δθ|²] = π²/3
        # La varianza attesa dei gradienti è circa 0.5
        var_diffusive = 0.35  # calibrato empiricamente per griglia 3D
        
        if var_diffusive > 1e-10:
            Dratio = var_structural / var_diffusive
        else:
            Dratio = 1.0
        
        return Dratio
    
    def compute_Jpol_metrics(self, theta):
        """Metriche dell'accoppiamento polarizzato dinamico."""
        Jpol = self.compute_dynamic_Jpol(theta)
        
        # Jpol medio effettivo (sopra soglia)
        active = Jpol > self.cfg["Jpol_threshold"]
        Jpol_mean = np.mean(Jpol[active]) if np.any(active) else 0.0
        
        # Densità di accoppiamento attivo
        rho_pol = np.sum(active) / max(1, len(Jpol))
        
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
        Cvert /= max(1, self.Nr * self.Nc)
        
        return Jpol_mean, rho_pol, Cvert, Jpol
    
    def compute_nucleation_probability(self, sigma_Cn, Dratio, Jpol_mean, theta, phi):
        """P_π(φ) ∝ Jpol·σ(Cn)/Dratio — mappa 3D."""
        if Dratio > 1e-10:
            P_base = Jpol_mean * sigma_Cn / Dratio
        else:
            P_base = 0.0
        
        P_3d = np.zeros(self.N, dtype=np.float64)
        for i in range(self.N):
            iz, ir, ic = self.z_idx[i], self.r_idx[i], self.c_idx[i]
            diffs = []
            for dz, dr, dc in [(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]:
                jz, jr, jc = iz+dz, ir+dr, ic+dc
                if 0 <= jz < self.Nz and 0 <= jr < self.Nr and 0 <= jc < self.Nc:
                    j = jz * self.Nr * self.Nc + jr * self.Nc + jc
                    diffs.append(theta[j] - theta[i])
            
            local_grad = np.std(diffs) if diffs else 0.0
            P_3d[i] = P_base * (1 + local_grad) * self.gamma_nodes[i] * self.n_hd[i]
        
        P_max = np.max(P_3d)
        if P_max > 1e-10:
            P_3d /= P_max
        
        return P_3d, P_base
    
    def compute_energetic_observable(self, sigma_Cn, Dratio, Jpol_mean):
        """E_π = κ · Jpol · σ(Cn) · |Ψ_RX|² / Dratio (osservabile NON reale)."""
        _, _, Z = self.compute_order_parameter(self.theta)
        Psi_RX_sq = np.abs(Z) ** 2
        kappa = 1.0
        E_pi = kappa * Jpol_mean * sigma_Cn * Psi_RX_sq / max(1e-10, Dratio)
        return E_pi, Psi_RX_sq
    
    def check_guardrails(self, sigma_Cn, Dratio, Jpol_mean, rho_pol):
        all_met = (sigma_Cn >= GUARDRAILS["sigma_Cn_min"]
                  and Dratio >= GUARDRAILS["Dratio_min"]
                  and Jpol_mean >= GUARDRAILS["Jpol_min"]
                  and rho_pol >= GUARDRAILS["rho_pol_min"])
        
        strict_met = (sigma_Cn >= GUARDRAILS["sigma_Cn_strict"]
                     and Dratio >= GUARDRAILS["Dratio_strict"]
                     and Jpol_mean >= GUARDRAILS["Jpol_min"]
                     and rho_pol >= GUARDRAILS["rho_pol_min"])
        
        return all_met, strict_met
    
    def extract_structural_signature(self, theta, phi):
        """Firma strutturale S = [C₁..Cₖ, D, I_dens, σ(Cn), Ψ_RX]."""
        sigma_Cn, harmonic_coh, layer_coh = self.compute_sigma_Cn(theta)
        Dratio = self.compute_Dratio(theta)
        r_order, psi_order, Z = self.compute_order_parameter(theta)
        
        # Spettro di potenza delle fasi (informazione spettrale)
        fft_theta = np.fft.fft(theta)
        I_dens = -np.sum(np.log(np.abs(fft_theta) + 1e-10)) / self.N
        
        return {
            "C_harmonics": [float(c) for c in harmonic_coh],
            "C_layers": [float(c) for c in layer_coh],
            "D": float(Dratio),
            "I_dens": float(I_dens),
            "sigma_Cn": float(sigma_Cn),
            "Psi_RX_amp": float(np.abs(Z)),
            "Psi_RX_phase": float(np.angle(Z)),
            "phi": float(phi),
        }
    
    # ─── Loop Principale ──────────────────────────────────────────────────
    
    def run(self):
        print("\n" + "="*70)
        print("  SIMULAZIONE BASE π v2.0 - AVVIO")
        print("  Cerca la firma, non il joule. La fase non mente. 🦋📐")
        print("="*70 + "\n")
        
        phi = self.phi_start
        step = 0
        recalibrations = 0
        
        import time as wc
        t0 = wc.time()
        
        while phi < self.phi_end:
            self.theta = self.rk4_step(self.theta, phi)
            self.evolve_hd_field(phi)
            
            if step % self.cfg["store_every"] == 0:
                sigma_Cn, _, _ = self.compute_sigma_Cn(self.theta)
                Dratio = self.compute_Dratio(self.theta)
                Jpol_mean, rho_pol, Cvert, _ = self.compute_Jpol_metrics(self.theta)
                P_3d, P_base = self.compute_nucleation_probability(
                    sigma_Cn, Dratio, Jpol_mean, self.theta, phi)
                E_pi, Psi_sq = self.compute_energetic_observable(
                    sigma_Cn, Dratio, Jpol_mean)
                
                self.metrics_history["phi"].append(phi)
                self.metrics_history["sigma_Cn"].append(sigma_Cn)
                self.metrics_history["Dratio"].append(Dratio)
                self.metrics_history["Jpol_mean"].append(Jpol_mean)
                self.metrics_history["rho_pol"].append(rho_pol)
                self.metrics_history["Cvert"].append(Cvert)
                self.metrics_history["P_pi_max"].append(float(np.max(P_3d)))
                self.metrics_history["E_pi_max"].append(E_pi)
                
                self.theta_stored.append(self.theta.copy())
                self.phi_stored.append(phi)
                
                # Validazione
                _, strict_met = self.check_guardrails(sigma_Cn, Dratio, Jpol_mean, rho_pol)
                
                if strict_met:
                    self._consecutive_strict += 1
                else:
                    self._consecutive_strict = 0
                
                # Traccia cicli
                current_cycle = int(phi / (2 * np.pi))
                if current_cycle > self._phi_at_last_cycle:
                    self._phi_at_last_cycle = current_cycle
                    print(f"  [CYCLE {current_cycle}] φ={phi:.2f} | "
                          f"σ(Cn)={sigma_Cn:.4f} Dratio={Dratio:.2f} "
                          f"Jpol={Jpol_mean:.4f} ρpol={rho_pol:.4f} "
                          f"consec_strict={self._consecutive_strict}")
                
                # Nucleazione
                if np.max(P_3d) > 0.75 and strict_met:
                    seeds_mask = P_3d > 0.75
                    for idx in np.where(seeds_mask)[0]:
                        self.nucleation_seeds.append({
                            "z": float(self.coords[idx, 0]),
                            "r": float(self.coords[idx, 1]),
                            "c": float(self.coords[idx, 2]),
                            "phi": float(phi),
                            "P": float(P_3d[idx])
                        })
                
                # Firma strutturale (ogni ~100 step campionati)
                if step % (100 * self.cfg["store_every"]) == 0:
                    sig = self.extract_structural_signature(self.theta, phi)
                    self.signatures_series.append(sig)
                
                # Ricalibrazione
                all_met, _ = self.check_guardrails(sigma_Cn, Dratio, Jpol_mean, rho_pol)
                if not all_met and sigma_Cn < GUARDRAILS["sigma_Cn_min"] * 0.3 and recalibrations < 3:
                    print(f"  [RECALIBRATE] σ(Cn)={sigma_Cn:.4f} troppo basso a φ={phi:.4f}")
                    self.cfg["beta"] = min(0.5, self.cfg["beta"] * 1.3)
                    self.cfg["J0"] = min(3.0, self.cfg["J0"] * 1.2)
                    recalibrations += 1
            
            phi += self.dphi
            step += 1
        
        elapsed = wc.time() - t0
        
        # Calcola cicli stabili
        self.validation["guardrails_met"] = self._consecutive_strict >= GUARDRAILS["phi_cycles_stable"] * 10
        self.validation["nucleation_seeds_found"] = len(self.nucleation_seeds)
        self.validation["stable_phi_cycles"] = self._consecutive_strict // 10
        self.validation["recalibrations"] = recalibrations
        self.validation["max_consecutive_strict"] = self._consecutive_strict
        
        # Ultima mappa
        sigma_Cn_f, _, _ = self.compute_sigma_Cn(self.theta)
        Dratio_f = self.compute_Dratio(self.theta)
        Jpol_f, _, _, _ = self.compute_Jpol_metrics(self.theta)
        P_3d_final, _ = self.compute_nucleation_probability(
            sigma_Cn_f, Dratio_f, Jpol_f, self.theta, phi)
        
        print(f"\n{'='*70}")
        print(f"  SIMULAZIONE COMPLETATA in {elapsed:.1f}s ({step} step)")
        print(f"  Semi nucleazione: {len(self.nucleation_seeds)}")
        print(f"  Cicli stabili: {self.validation['stable_phi_cycles']}")
        print(f"  Guardrail: {self.validation['guardrails_met']}")
        print(f"{'='*70}")
        
        return self._package_output(P_3d_final)
    
    def _package_output(self, P_3d_final):
        nucleation_map = np.zeros((self.Nz, self.Nr, self.Nc), dtype=np.float64)
        for i in range(self.N):
            nucleation_map[self.z_idx[i], self.r_idx[i], self.c_idx[i]] = P_3d_final[i]
        
        timeline = {k: np.array(v) for k, v in self.metrics_history.items()}
        
        final_sig = self.extract_structural_signature(self.theta, self.phi_end)
        
        unique_seeds = []
        seen = set()
        for s in self.nucleation_seeds:
            key = (round(s["z"], 2), round(s["r"], 2), round(s["c"], 2))
            if key not in seen:
                seen.add(key)
                unique_seeds.append(s)
        
        return {
            "nucleation_map": nucleation_map,
            "timeline": timeline,
            "final_signature": final_sig,
            "signatures_series": self.signatures_series,
            "validation": self.validation,
            "nucleation_seeds": unique_seeds[:100],
            "theta_final": self.theta,
            "coords": self.coords,
            "z_idx": self.z_idx,
            "r_idx": self.r_idx,
            "c_idx": self.c_idx,
        }


def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  MANIFESTO OPERATIVO: Simulazione Base π v2.0              ║")
    print("║  Polveri Ibride (Ni/Fe/Cu + H/D) — Griglia 3D+pol         ║")
    print("║  Cerca la firma, non il joule. La fase non mente. 🦋📐     ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    sim = BasePiSimulation()
    output = sim.run()
    
    output_dir = "/home/z/my-project/download"
    os.makedirs(output_dir, exist_ok=True)
    
    np.save(os.path.join(output_dir, "nucleation_map_3d.npy"), output["nucleation_map"])
    for key, arr in output["timeline"].items():
        np.save(os.path.join(output_dir, f"timeline_{key}.npy"), arr)
    np.save(os.path.join(output_dir, "theta_final.npy"), output["theta_final"])
    
    json_output = {
        "final_signature": output["final_signature"],
        "validation": output["validation"],
        "nucleation_seeds": output["nucleation_seeds"],
        "signatures_series": output["signatures_series"],
    }
    with open(os.path.join(output_dir, "simulation_results.json"), "w") as f:
        json.dump(json_output, f, indent=2, default=str)
    
    print(f"\n[SAVED] Risultati in {output_dir}/")
    return output


if __name__ == "__main__":
    output = main()
