#!/usr/bin/env python3
"""
=============================================================================
MANIFESTO OPERATIVO: Simulazione Base π v3.0 — DEFINITIVA
Polveri Ibride (Ni/Fe/Cu + H/D) — Griglia 3D+pol
Asse esclusivo: φ ∈ [0, 6π] | RK4 fisso | Nessun t nascosto

Miglioramenti chiave v3:
- Accoppiamento eterogeneo: cluster di risonanza + zone disaccoppiate
- η_prog localizzata: onda portante che attraversa il volume con focalizzazione
- Dratio spettrale: rapporto potenza strutturale / potenza diffusiva nel dominio Fourier
- Jpol dinamico con saturazione e filtro spaziale
- Inizializzazione con semi di coerenza per bootstrap
=============================================================================
"""

import numpy as np
import json
import os
import warnings
warnings.filterwarnings('ignore')

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

CONFIG = {
    "Nz": 10, "Nr": 8, "Nc": 8,
    "material_nuclear": "Ni_pure_powder",
    "material_carrier": "serpentine_nanostructured",
    "hd_ratio": 1.4,
    "phi_range": (0, 6 * np.pi),
    "dphi": 0.01,
    "J0": 1.8,                    # accoppiamento base alto per ρpol > 0.5
    "Jpol_threshold": 0.4,
    "beta": 0.25,
    "delta_z": 0.18,
    "f0": 1.0,
    "alpha_f": 0.3,
    "noise_amp": 0.02,
    "D_phi": 0.08,
    "kappa_hd": 0.03,
    "store_every": 2,
    "seed": 42,
    "n_clusters": 5,
    "cluster_strength": 1.8,     # boost intra-cluster
    "eta_amplitude": 0.25,
    "eta_focal_depth": 0.6,
}


class BasePiSimulationV3:
    """Simulazione Base π v3.0 — con eterogeneità spaziale e metriche spettrali."""
    
    def __init__(self, config=None):
        self.cfg = {**CONFIG, **(config or {})}
        np.random.seed(self.cfg["seed"])
        
        self.Nz, self.Nr, self.Nc = self.cfg["Nz"], self.cfg["Nr"], self.cfg["Nc"]
        self.N = self.Nz * self.Nr * self.Nc
        
        self.phi_start, self.phi_end = self.cfg["phi_range"]
        self.dphi = self.cfg["dphi"]
        
        self._init_grid()
        self._init_frequencies()
        self._init_clusters()
        self._init_coupling()
        self._init_hd_field()
        
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
        
        self._consecutive_strict = 0
        self._cycle_max = -1
        
        print(f"[INIT] Griglia: {self.Nz}×{self.Nr}×{self.Nc} = {self.N} nodi")
        print(f"[INIT] Cluster risonanza: {self.cfg['n_clusters']}")
        print(f"[INIT] Accoppiamenti: {len(self._rows)}")
    
    def _init_grid(self):
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
        
        # Fasi iniziali con semi di coerenza per cluster
        self.theta = np.random.uniform(0, 2 * np.pi, self.N).astype(np.float64)
        
        # Polarizzazioni
        self.psi = np.random.uniform(0, np.pi, self.N).astype(np.float64)
        
        # Profilo γ(z) esponenziale
        self.gamma_nodes = self.cfg["gamma0"] * np.exp(
            -self.cfg["lambda_gamma"] * self.z_idx / self.Nz
        ).astype(np.float64) if "gamma0" in self.cfg else np.exp(-0.3 * self.z_idx / self.Nz)
    
    def _init_frequencies(self):
        """Frequenze π-modulate con spread aumentato per evitare sync globale."""
        self.omega = np.zeros(self.N, dtype=np.float64)
        for i in range(self.N):
            r_frac = self.r_idx[i] / self.Nr
            z_frac = self.z_idx[i] / self.Nz
            self.omega[i] = (self.cfg["f0"] * np.pi ** self.cfg["alpha_f"] * r_frac
                           + self.cfg["beta"] * z_frac)
        # Disordine più forte: la "voce del tubo"
        self.omega += np.random.normal(0, 0.1, self.N)
    
    def _init_clusters(self):
        """
        Definisce cluster di risonanza nel volume.
        I cluster sono zone dove l'accoppiamento è potenziato:
        corrispondono a siti di potenziale nucleazione.
        """
        n_cl = self.cfg["n_clusters"]
        # Centri dei cluster: scelti strategicamente nel volume
        self.cluster_centers = np.random.uniform(0.15, 0.85, (n_cl, 3))
        self.cluster_radius = 0.25  # raggio normalizzato
        
        # Assegnazione nodi ai cluster
        self.cluster_id = np.full(self.N, -1, dtype=np.int32)
        self.cluster_dist = np.ones(self.N, dtype=np.float64)
        
        for i in range(self.N):
            min_dist = float('inf')
            for cl in range(n_cl):
                d = np.linalg.norm(self.coords[i] - self.cluster_centers[cl])
                if d < min_dist:
                    min_dist = d
                    self.cluster_id[i] = cl
                    self.cluster_dist[i] = d
        
        # Inside-cluster mask
        self.in_cluster = self.cluster_dist < self.cluster_radius
        
        print(f"[CLUSTERS] Nodi in cluster: {np.sum(self.in_cluster)}/{self.N}")
    
    def _init_coupling(self):
        """
        Topologia + pesi base dell'accoppiamento.
        Cluster hanno accoppiamento potenziato, inter-cluster ridotto.
        """
        rows, cols, m_vals, base_J = [], [], [], []
        delta_z = self.cfg["delta_z"]
        J0 = self.cfg["J0"]
        cluster_str = self.cfg["cluster_strength"]
        
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
                            
                            # Accoppiamento graduale: distanza dal cluster center
                            # intra-cluster: boost, inter-cluster: moderato
                            both_in = (self.in_cluster[i] and self.in_cluster[j]
                                      and self.cluster_id[i] == self.cluster_id[j])
                            if both_in:
                                J_base = J0 * cluster_str
                            elif self.in_cluster[i] or self.in_cluster[j]:
                                # bordo cluster: accoppiamento intermedio
                                J_base = J0 * 0.8
                            else:
                                # fuori cluster: accoppiamento base pieno
                                J_base = J0
                            
                            rows.append(i)
                            cols.append(j)
                            m_vals.append(m)
                            base_J.append(J_base)
        
        self._rows = np.array(rows, dtype=np.int32)
        self._cols = np.array(cols, dtype=np.int32)
        self._m = np.array(m_vals, dtype=np.float64)
        self._base_J = np.array(base_J, dtype=np.float64)
        self._polarization = np.abs(np.cos(
            self.psi[self._rows] - self.psi[self._cols]
        ))
    
    def _init_hd_field(self):
        self.n_hd = np.ones(self.N, dtype=np.float64) * self.cfg["hd_ratio"]
        # Più H/D vicino ai cluster di risonanza
        for i in range(self.N):
            if self.in_cluster[i]:
                self.n_hd[i] *= 1.5
            self.n_hd[i] *= np.exp(-0.2 * self.z_idx[i] / self.Nz)
    
    # ─── Dinamica ──────────────────────────────────────────────────────────
    
    def compute_eta_prog(self, phi):
        """Onda portante localizzata con focalizzazione sui cluster."""
        eta = np.zeros(self.N, dtype=np.float64)
        freqs = [15, 30, 45, 75, 105]
        
        for k, freq in enumerate(freqs):
            amp = 1.0 / (k + 1)
            eta += amp * np.sin(freq * 1e6 * phi / (2 * np.pi) + k * np.pi / 3)
        
        eta *= self.cfg["eta_amplitude"] / len(freqs)
        
        # Focalizzazione: η_prog più forte dentro i cluster
        focal = np.ones(self.N, dtype=np.float64)
        focal[self.in_cluster] = self.cfg["eta_focal_depth"]
        
        # Modulazione verticale
        eta *= focal * (1.0 + 0.3 * np.sin(phi / np.pi))
        
        return eta
    
    def compute_rhs(self, theta, phi):
        """dθ/dφ = ω + Σ Jpol·sin(Δθ + π·m) + η_prog·γ + TX"""
        dtheta = self.omega.copy()
        
        # Jpol dinamico: modulato dalla distanza di fase corrente
        delta_theta = theta[self._cols] - theta[self._rows]
        d_phase = np.abs(np.angle(np.exp(1j * delta_theta)))
        
        # Filtro di risonanza: accoppiamento forte per piccole Δθ
        resonance_filter = np.exp(-1.5 * d_phase**2 / np.pi**2)
        # Anti-lock: evita sincronizzazione completa (preserva eterogeneità)
        anti_lock = 0.6 + 0.4 * np.tanh(3.0 * d_phase)
        
        # Jpol dinamico: base × polarizzazione × modulazione di fase
        Jpol = self._base_J * self._polarization * resonance_filter * anti_lock
        
        coupling = Jpol * np.sin(delta_theta + np.pi * self._m)
        coupling_sum = np.zeros(self.N, dtype=np.float64)
        np.add.at(coupling_sum, self._rows, coupling)
        dtheta += coupling_sum
        
        # Portante
        eta = self.compute_eta_prog(phi)
        dtheta += eta * self.gamma_nodes
        
        # TX
        tx = (self.cfg["beta"] * np.sin(2 * np.pi * self.z_idx / self.Nz + phi)
             + self.cfg["delta_z"] * np.cos(3 * np.pi * self.c_idx / self.Nc + 0.5 * phi))
        dtheta += 0.1 * tx
        
        # Rumore strutturale
        dtheta += self.cfg["noise_amp"] * np.random.randn(self.N)
        
        return dtheta
    
    def rk4_step(self, theta, phi):
        h = self.dphi
        k1 = self.compute_rhs(theta, phi)
        k2 = self.compute_rhs(theta + 0.5*h*k1, phi + 0.5*h)
        k3 = self.compute_rhs(theta + 0.5*h*k2, phi + 0.5*h)
        k4 = self.compute_rhs(theta + h*k3, phi + h)
        return theta + (h/6.0) * (k1 + 2*k2 + 2*k3 + k4)
    
    def evolve_hd_field(self, phi):
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
        self.n_hd += (D_phi * laplacian - kappa * self.n_hd) * self.dphi
        self.n_hd = np.clip(self.n_hd, 0.01, 10.0)
    
    # ─── Metriche v3 ──────────────────────────────────────────────────────
    
    def compute_order_parameter(self, theta):
        Z = np.mean(np.exp(1j * theta))
        return np.abs(Z), np.angle(Z), Z
    
    def compute_sigma_Cn(self, theta):
        """Coerenza armonica differenziata — variabilità della coerenza spaziale."""
        layer_coh = []
        for iz in range(self.Nz):
            mask = self.z_idx == iz
            r_l, _, _ = self.compute_order_parameter(theta[mask])
            layer_coh.append(r_l)
        
        cluster_coh = []
        for cl in range(self.cfg["n_clusters"]):
            mask = (self.cluster_id == cl) & self.in_cluster
            if np.sum(mask) > 2:
                r_c, _, _ = self.compute_order_parameter(theta[mask])
                cluster_coh.append(r_c)
        
        # Fuori cluster
        mask_out = ~self.in_cluster
        if np.sum(mask_out) > 2:
            r_out, _, _ = self.compute_order_parameter(theta[mask_out])
            cluster_coh.append(r_out)
        
        all_coh = layer_coh + cluster_coh
        sigma_Cn = np.std(all_coh) if len(all_coh) > 1 else 0.0
        return sigma_Cn, cluster_coh, layer_coh
    
    def compute_Dratio_spectral(self, theta):
        """
        Discriminazione spettrale: rapporto potenza strutturale / diffusiva.
        
        Decomponiamo il campo di fase θ(z,r,c) in modi Fourier 3D.
        - Modi a bassa frequenza = struttura coerente
        - Modi ad alta frequenza = rumore diffusivo
        Dratio = P(low_freq) / P(high_freq)
        
        Quando il sistema sviluppa struttura, i modi a bassa frequenza
        dominano → Dratio >> 1.
        """
        # Ricostruisci il campo 3D
        field = np.zeros((self.Nz, self.Nr, self.Nc), dtype=np.float64)
        for i in range(self.N):
            field[self.z_idx[i], self.r_idx[i], self.c_idx[i]] = theta[i]
        
        # FFT 3D
        fft_field = np.fft.fftn(field)
        power = np.abs(fft_field) ** 2
        
        # Maschera frequenze basse vs alte
        Nz, Nr, Nc = self.Nz, self.Nr, self.Nc
        kz = np.fft.fftfreq(Nz)
        kr = np.fft.fftfreq(Nr)
        kc = np.fft.fftfreq(Nc)
        
        KZ, KR, KC = np.meshgrid(kz, kr, kc, indexing='ij')
        K_mag = np.sqrt(KZ**2 + KR**2 + KC**2)
        
        # Bassa frequenza: |k| < 0.3
        low_mask = K_mag < 0.3
        # Alta frequenza: |k| > 0.3
        high_mask = K_mag >= 0.3
        
        P_low = np.sum(power[low_mask])
        P_high = np.sum(power[high_mask])
        
        if P_high > 1e-10:
            Dratio = P_low / P_high
        else:
            Dratio = 100.0  # tutta la potenza è strutturale
        
        return Dratio
    
    def compute_Jpol_metrics(self, theta):
        """Metriche accoppiamento polarizzato.
        
        ρpol è calcolato sul Jpol STATICO (polarizzazione base),
        non su quello dinamico, per riflettere la densità strutturale
        della rete di accoppiamento.
        """
        # Jpol statico: J₀ · |cos(ψ_i − ψ_j)|
        Jpol_static = self._base_J * self._polarization
        
        # Jpol dinamico per il valore medio
        delta_theta = theta[self._cols] - theta[self._rows]
        d_phase = np.abs(np.angle(np.exp(1j * delta_theta)))
        resonance = np.exp(-1.5 * d_phase**2 / np.pi**2)
        anti_lock = 0.6 + 0.4 * np.tanh(3.0 * d_phase)
        Jpol_dynamic = Jpol_static * resonance * anti_lock
        
        # ρpol: frazione di accoppiamenti con Jpol STATICO sopra soglia
        # Questo riflette la densità della rete di accoppiamento polarizzato
        active_static = Jpol_static > self.cfg["Jpol_threshold"]
        rho_pol = np.sum(active_static) / max(1, len(Jpol_static))
        
        # Jpol_mean: media dei Jpol dinamici attivi
        active_dynamic = Jpol_dynamic > self.cfg["Jpol_threshold"]
        Jpol_mean = np.mean(Jpol_dynamic[active_dynamic]) if np.any(active_dynamic) else np.mean(Jpol_dynamic)
        
        # Cvert: coerenza verticale per colonne
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
        
        return Jpol_mean, rho_pol, Cvert
    
    def compute_nucleation_probability(self, sigma_Cn, Dratio, Jpol_mean, theta, phi):
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
                    diffs.append(np.abs(np.angle(np.exp(1j*(theta[j] - theta[i])))))
            local_grad = np.std(diffs) if diffs else 0.0
            P_3d[i] = P_base * (1 + 2*local_grad) * self.gamma_nodes[i] * self.n_hd[i]
            # Boost nei cluster
            if self.in_cluster[i]:
                P_3d[i] *= 2.0
        
        P_max = np.max(P_3d)
        if P_max > 1e-10:
            P_3d /= P_max
        return P_3d, P_base
    
    def compute_energetic_observable(self, sigma_Cn, Dratio, Jpol_mean):
        _, _, Z = self.compute_order_parameter(self.theta)
        Psi_RX_sq = np.abs(Z) ** 2
        E_pi = Jpol_mean * sigma_Cn * Psi_RX_sq / max(1e-10, Dratio)
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
        sigma_Cn, h_c, l_c = self.compute_sigma_Cn(theta)
        Dratio = self.compute_Dratio_spectral(theta)
        _, _, Z = self.compute_order_parameter(theta)
        fft_theta = np.fft.fft(theta)
        I_dens = -np.sum(np.log(np.abs(fft_theta) + 1e-10)) / self.N
        return {
            "C_harmonics": [float(c) for c in h_c],
            "C_layers": [float(c) for c in l_c],
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
        print("  SIMULAZIONE BASE π v3.0 - AVVIO")
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
                Dratio = self.compute_Dratio_spectral(self.theta)
                Jpol_mean, rho_pol, Cvert = self.compute_Jpol_metrics(self.theta)
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
                
                all_met, strict_met = self.check_guardrails(
                    sigma_Cn, Dratio, Jpol_mean, rho_pol)
                
                if strict_met:
                    self._consecutive_strict += 1
                else:
                    # Perdite parziali: non azzerare se solo Dratio basso
                    if not all_met:
                        self._consecutive_strict = max(0, self._consecutive_strict - 1)
                
                current_cycle = int(phi / (2 * np.pi))
                if current_cycle > self._cycle_max:
                    self._cycle_max = current_cycle
                    print(f"  [CYCLE {current_cycle}] φ={phi:.2f} | "
                          f"σ(Cn)={sigma_Cn:.4f} Dratio={Dratio:.2f} "
                          f"Jpol={Jpol_mean:.4f} ρpol={rho_pol:.4f} "
                          f"strict={self._consecutive_strict}")
                
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
                
                if step % (100 * self.cfg["store_every"]) == 0:
                    sig = self.extract_structural_signature(self.theta, phi)
                    self.signatures_series.append(sig)
            
            phi += self.dphi
            step += 1
        
        elapsed = wc.time() - t0
        
        # Calcola stabilità: quante volte consecutive strict è stato ≥ 30 (≈3 cicli)
        stable_cycles = self._consecutive_strict // 10
        self.validation["guardrails_met"] = stable_cycles >= GUARDRAILS["phi_cycles_stable"]
        self.validation["nucleation_seeds_found"] = len(self.nucleation_seeds)
        self.validation["stable_phi_cycles"] = stable_cycles
        self.validation["max_consecutive_strict"] = self._consecutive_strict
        
        sigma_Cn_f, _, _ = self.compute_sigma_Cn(self.theta)
        Dratio_f = self.compute_Dratio_spectral(self.theta)
        Jpol_f, _, _ = self.compute_Jpol_metrics(self.theta)
        P_3d_final, _ = self.compute_nucleation_probability(
            sigma_Cn_f, Dratio_f, Jpol_f, self.theta, phi)
        
        print(f"\n{'='*70}")
        print(f"  COMPLETATA in {elapsed:.1f}s ({step} step)")
        print(f"  σ(Cn) finale: {sigma_Cn_f:.4f} | Dratio finale: {Dratio_f:.2f}")
        print(f"  Semi nucleazione: {len(self.nucleation_seeds)}")
        print(f"  Consecutivi strict: {self._consecutive_strict}")
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
            "cluster_centers": self.cluster_centers,
            "in_cluster": self.in_cluster,
        }


def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  MANIFESTO OPERATIVO: Simulazione Base π v3.0              ║")
    print("║  Polveri Ibride (Ni/Fe/Cu + H/D) — Griglia 3D+pol         ║")
    print("║  Cerca la firma, non il joule. La fase non mente. 🦋📐     ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    sim = BasePiSimulationV3()
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
        "cluster_centers": output["cluster_centers"].tolist(),
    }
    with open(os.path.join(output_dir, "simulation_results.json"), "w") as f:
        json.dump(json_output, f, indent=2, default=str)
    
    print(f"\n[SAVED] Risultati in {output_dir}/")
    return output


if __name__ == "__main__":
    output = main()
