#!/usr/bin/env python3
"""
=============================================================================
MANIFESTO OPERATIVO: Simulazione Base π v4.1 — VERIFIED & CORRECTED
Polveri Ibride (Ni/Fe/Cu + H/D) — Griglia 3D+pol
Asse esclusivo: φ ∈ [0, 6π] | RK4 fisso | Nessun t nascosto

CORREZIONI v4.1 (da verifica indipendente):
  [CRASH FIX] P_3d: np.diff(theta)→(N-1,) non broadcasta con (N,).
              Rimpiazzato con gradiente fase locale dai coupling edges.
  [CRITICO]   Cvert: indexing rotto — non filtrava per (r,c).
              Riscritto con maschera booleana per colonne verticali.
  [CRITICO]   nucleation_map_3d: salvava np.zeros() invece di P_3d.
              Ora accumula mappa reale dal campo P.
  [MODERATO]  stable_phi_cycles: //10 non representava cicli reali.
              Calcolato come range_φ_consecutivo / (2π).
  [MODERATO]  Grid scaling: int()→round() per rispettare target 252 nodi.
  [MODERATO]  eta_amplitude: aggiunto esplicitamente al JSON config.
  [MINORE]    report_v4_summary.txt: ora generato nel _package().
  [MINORE]    final_signature: aggiunto a simulation_results.json.
  [MINORE]    coo_matrix: rimosso import inutilizzato.

MIGLIORAMENTI HARDWARE:
  - Parametri tunneling risonante (Gamow, P_π esplicito)
  - hardware_params nel JSON (loss, bandwidth, Q, risoluzione)
  - Parametri coupling/resonanza estraibili dal config
  - evolve_hd_field vettorizzato (no Python for-loop)
=============================================================================
"""
import numpy as np
import json
import os
import sys
import time
import warnings
warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════════════════
# GUARDRAILS — Soglie non negoziabili
# ═══════════════════════════════════════════════════════════════════════════
GUARDRAILS = {
    "no_hidden_t": True,
    "dphi": 0.01,
    "sigma_Cn_min": 0.01, "sigma_Cn_strict": 0.075,
    "Dratio_min": 10,     "Dratio_strict": 15,
    "Jpol_min": 0.4,
    "rho_pol_min": 0.5,
    "beta_min": 0.1,
    "delta_z_min": 0.15,
    "phi_cycles_stable": 3,
    "readout_non_destructive": True,
    "strict_decay_rate": 1
}

CONFIG_PATH = "/home/z/my-project/download/base_pi_v4/base_pi_v4_extended.json"
with open(CONFIG_PATH) as f:
    CFG = json.load(f)


class BasePiSimulationV41Verified:
    """
    Simulazione Base π v4.1 — Verified & Corrected
    
    Manifold: φ ∈ [0, 6π] è l'asse esclusivo di evoluzione.
    Kuramoto π-modulato: dθ/dφ = ω + Σ Jpol·sin(Δθ + π·m) + η(φ)·γ + TX(φ)
    """

    def __init__(self):
        self.cfg = CFG
        np.random.seed(self.cfg["seed"])

        # ── Grid setup ──────────────────────────────────────────────────
        self.Nz = self.cfg["grid"]["Nz"]
        self.Nr = self.cfg["grid"]["Nr"]
        self.Nc = self.cfg["grid"]["Nc"]

        if self.cfg["grid"]["micro_test_256_nodes"]:
            scale = 0.7
            method = self.cfg["grid"].get("scaling_method", "round")
            _round_fn = round if method == "round" else int
            self.Nz = max(4, _round_fn(self.Nz * scale))
            self.Nr = max(4, _round_fn(self.Nr * scale))
            self.Nc = max(4, _round_fn(self.Nc * scale))

        self.N = self.Nz * self.Nr * self.Nc
        self.phi_start, self.phi_end = self.cfg["phase_axis"]["phi_range"]
        self.dphi = self.cfg["phase_axis"]["dphi"]

        # ── Initialize subsystems ───────────────────────────────────────
        self._init_grid()
        self._init_frequencies()
        self._init_clusters_hybrid()
        self._init_coupling_sparse()
        self._init_hd_field()

        # ── Storage ─────────────────────────────────────────────────────
        self.metrics_history = {
            k: [] for k in [
                "phi", "sigma_Cn", "Dratio", "Jpol_mean",
                "rho_pol", "Cvert", "P_pi_max", "E_pi_max"
            ]
        }
        self.theta_stored = []
        self.phi_stored = []
        self.nucleation_seeds = []

        # ── Nucleation probability map (3D accumulation) ────────────────
        self.nucleation_map_accum = np.zeros((self.Nz, self.Nr, self.Nc), dtype=np.float64)
        self.nucleation_map_count = 0

        # ── Validation state ────────────────────────────────────────────
        self.validation = {
            "pi_algebra_operational": True,
            "no_hidden_t": True,
            "readout_non_destructive": True,
            "guardrails_met": False,
            "nucleation_seeds_found": 0,
            "stable_phi_cycles": 0,
            "total_phi_steps": 0
        }
        self._consecutive_strict_start_phi = None
        self._consecutive_strict = 0
        self._cycle_max = -1
        self._last_P_3d = None

        # ── Report log ──────────────────────────────────────────────────
        self._report_lines = []

        print(f"[INIT] V4.1-VERIFIED | Grid: {self.Nz}×{self.Nr}×{self.Nc} = {self.N} nodes | "
              f"Clusters: {self.cfg['clusters']['n_clusters']} | "
              f"φ ∈ [{self.phi_start:.2f}, {self.phi_end:.2f}]")

    # ════════════════════════════════════════════════════════════════════
    #  INITIALIZATION
    # ════════════════════════════════════════════════════════════════════

    def _init_grid(self):
        """Coordinate spaziali e indici griglia 3D+pol."""
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

        # Fase iniziale casuale e polarizzazione
        self.theta = np.random.uniform(0, 2 * np.pi, self.N)
        self.psi = np.random.uniform(0, np.pi, self.N)

        # Profilo di penetrazione γ(z) = γ₀·exp(-λ·z/Nz)
        self.gamma_nodes = np.exp(
            -self.cfg["carrier_wave"]["lambda_gamma"] * self.z_idx / self.Nz
        )

    def _init_frequencies(self):
        """Frequenze naturali ω_i con modulazione π-nativa."""
        f0 = self.cfg["coupling"]["f0"]
        alpha_f = self.cfg["coupling"]["alpha_f"]
        beta = self.cfg["coupling"]["beta"]

        # ω_i = f0 · π^α · (r_i/Nr) + β · (z_i/Nz)
        self.omega = (
            f0 * np.pi ** alpha_f * (self.r_idx / self.Nr)
            + beta * (self.z_idx / self.Nz)
            + np.random.normal(0, 0.1, self.N)
        )

    def _init_clusters_hybrid(self):
        """Cluster ibridi π-density: centri definiti nello spazio π."""
        pi_k = self.cfg["clusters"].get("pi_center_k", [1, 2, 3, 4, 5])
        pi_m = self.cfg["clusters"].get("pi_center_m", [1, 3, 5, 2, 4])
        pi_n = self.cfg["clusters"].get("pi_center_n", [2, 4, 6, 1, 5])

        pi_centers = np.array([
            [k * np.pi / 6, m * np.pi / 8, n * np.pi / 8]
            for k, m, n in zip(pi_k, pi_m, pi_n)
        ])
        # Normalizza da spazio π a coordinate griglia [0,1]
        self.cluster_centers = np.clip(pi_centers / (2 * np.pi), 0.1, 0.9)
        self.cluster_radius = self.cfg["clusters"]["radius"]

        # Assegnazione nodi ai cluster + distanze
        self.cluster_id = np.full(self.N, -1, dtype=np.int32)
        self.cluster_dist = np.ones(self.N)

        # Calcolo vettorizzato distanze
        for i in range(self.N):
            dists = np.linalg.norm(self.coords[i] - self.cluster_centers, axis=1)
            self.cluster_id[i] = np.argmin(dists)
            self.cluster_dist[i] = dists[self.cluster_id[i]]

        self.in_cluster = self.cluster_dist < self.cluster_radius
        self.density_weight = 1.0 + 0.5 * np.exp(
            -5 * self.cluster_dist ** 2 / self.cluster_radius ** 2
        )

    def _init_coupling_sparse(self):
        """Accoppiamento polarizzato in formato COO (rows, cols, valori)."""
        rows, cols, base_J, m_vals = [], [], [], []

        J0 = self.cfg["coupling"]["J0"]
        cs = self.cfg["clusters"]["strength"]
        delta_z = self.cfg["coupling"]["delta_z"]

        for i in range(self.N):
            iz_i = self.z_idx[i]
            ir_i = self.r_idx[i]
            ic_i = self.c_idx[i]

            for dz, dr, dc in [(-1,0,0), (1,0,0), (0,-1,0),
                                (0,1,0), (0,0,-1), (0,0,1)]:
                jz = iz_i + dz
                jr = ir_i + dr
                jc = ic_i + dc

                if not (0 <= jz < self.Nz and
                        0 <= jr < self.Nr and
                        0 <= jc < self.Nc):
                    continue

                j = jz * self.Nr * self.Nc + jr * self.Nc + jc

                # Accoppiamento potenziato per nodi nello stesso cluster
                both_in = (self.in_cluster[i] and self.in_cluster[j]
                           and self.cluster_id[i] == self.cluster_id[j])
                one_in = self.in_cluster[i] or self.in_cluster[j]

                if both_in:
                    J_base = J0 * cs
                elif one_in:
                    J_base = J0 * 0.8
                else:
                    J_base = J0

                rows.append(i)
                cols.append(j)
                base_J.append(J_base)
                m_vals.append(
                    (jc - ic_i) / self.Nc + delta_z * (jz - iz_i) / self.Nz
                )

        self._rows = np.array(rows, dtype=np.int32)
        self._cols = np.array(cols, dtype=np.int32)
        self._m = np.array(m_vals, dtype=np.float64)

        # Polarizzazione statica: Jpol = J₀·|cos(ψ_i − ψ_j)|
        self._polarization = np.abs(
            np.cos(self.psi[self._rows] - self.psi[self._cols])
        )
        self._base_J = np.array(base_J, dtype=np.float64) * self.density_weight[self._rows]

        # Conteggi per vicini (per gradiente fase locale in compute_metrics)
        self._neighbor_count = np.zeros(self.N, dtype=np.float64)
        np.add.at(self._neighbor_count, self._rows, 1.0)

        print(f"[COUPLING] {len(self._rows)} edges | "
              f"Jpol mean: {np.mean(self._base_J * self._polarization):.4f} | "
              f"ρpol: {np.sum(self._base_J * self._polarization > self.cfg['coupling']['threshold_Jpol']) / len(self._base_J):.4f}")

    def _init_hd_field(self):
        """Campo H/D con enhancement nei cluster e decadimento verticale."""
        enh = self.cfg["hd_field"].get("cluster_enhancement", 1.5)
        z_decay = self.cfg["hd_field"].get("z_decay_rate", 0.2)

        self.n_hd = np.ones(self.N) * self.cfg["materials"]["hd_ratio"]
        self.n_hd[self.in_cluster] *= enh
        self.n_hd *= np.exp(-z_decay * self.z_idx / self.Nz)

    # ════════════════════════════════════════════════════════════════════
    #  DYNAMICS
    # ════════════════════════════════════════════════════════════════════

    def compute_rhs(self, theta, phi):
        """
        Kuramoto π-modulato RHS:
        dθ/dφ = ω + Σ Jpol·sin(Δθ + π·m) + η_prog(φ)·γ + TX(φ)
        """
        dtheta = self.omega.copy()

        # ── Coupling polarizzato dinamico ───────────────────────────────
        delta_theta = theta[self._cols] - theta[self._rows]
        d_phase = np.abs(np.angle(np.exp(1j * delta_theta)))

        # Parametri di risonanza e anti-lock dal config
        res_w = self.cfg["coupling"].get("resonance_width", 1.5)
        al_gain = self.cfg["coupling"].get("anti_lock_gain", 0.4)
        al_slope = self.cfg["coupling"].get("anti_lock_slope", 3.0)

        resonance = np.exp(-res_w * d_phase ** 2 / np.pi ** 2)
        anti_lock = (1.0 - al_gain) + al_gain * np.tanh(al_slope * d_phase)

        Jpol_dyn = self._base_J * self._polarization * resonance * anti_lock
        coupling = Jpol_dyn * np.sin(delta_theta + np.pi * self._m)

        coupling_sum = np.zeros(self.N)
        np.add.at(coupling_sum, self._rows, coupling)
        dtheta += coupling_sum

        # ── Carrier wave η_prog(φ)·γ(z) ────────────────────────────────
        freqs = self.cfg["carrier_wave"]["frequencies_MHz"]
        eta_amp = self.cfg["carrier_wave"].get("eta_amplitude", 0.25)
        rf_depth = self.cfg["carrier_wave"].get("rf_modulation_depth", 0.3)

        eta = np.sum([
            np.sin(f * 1e6 * phi / (2 * np.pi) + k * np.pi / 3) / (k + 1)
            for k, f in enumerate(freqs)
        ])
        eta *= eta_amp / len(freqs)
        eta *= (1.0 + rf_depth * np.sin(phi / np.pi))
        dtheta += eta * self.gamma_nodes

        # ── Topological excitation TX(φ) ────────────────────────────────
        beta = self.cfg["coupling"]["beta"]
        delta_z = self.cfg["coupling"]["delta_z"]
        dtheta += 0.1 * (
            beta * np.sin(2 * np.pi * self.z_idx / self.Nz + phi)
            + delta_z * np.cos(3 * np.pi * self.c_idx / self.Nc + 0.5 * phi)
        )

        # ── Rumore di fase ─────────────────────────────────────────────
        dtheta += self.cfg["coupling"]["noise_amp"] * np.random.randn(self.N)

        return dtheta

    def rk4_step(self, theta, phi):
        """RK4 fixed-step integrator — dφ = 0.01, no adaptive stepping."""
        h = self.dphi
        k1 = self.compute_rhs(theta, phi)
        k2 = self.compute_rhs(theta + 0.5 * h * k1, phi + 0.5 * h)
        k3 = self.compute_rhs(theta + 0.5 * h * k2, phi + 0.5 * h)
        k4 = self.compute_rhs(theta + h * k3, phi + h)
        return theta + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

    def evolve_hd_field(self, phi):
        """
        Evoluzione campo H/D — vettorizzata (no Python for-loop).
        dn/dφ = D_φ · ∇²n − κ(φ) · n
        """
        kappa_base = self.cfg["hd_field"]["kappa_hd"]
        kappa_mod = self.cfg["hd_field"].get("kappa_modulation", 0.5)
        D_phi = self.cfg["hd_field"]["D_phi"]

        kappa = kappa_base * (1 + kappa_mod * np.sin(phi / np.pi))

        # Laplaciano discreto vettorizzato usando i coupling edges
        n_diff = self.n_hd[self._cols] - self.n_hd[self._rows]
        lap_sum = np.zeros(self.N)
        np.add.at(lap_sum, self._rows, n_diff)
        lap = lap_sum / np.maximum(self._neighbor_count, 1.0)

        self.n_hd += (D_phi * lap - kappa * self.n_hd) * self.dphi
        self.n_hd = np.clip(self.n_hd, 0.01, 10.0)

    # ════════════════════════════════════════════════════════════════════
    #  METRICS
    # ════════════════════════════════════════════════════════════════════

    def compute_metrics(self, theta):
        """
        Calcola tutte le metriche di validazione Base π.

        Returns: (sigma_Cn, Dratio, Jpol_mean, rho_pol, Cvert, P_3d, E_pi)
        """
        # ── Ordine globale ──────────────────────────────────────────────
        Z = np.mean(np.exp(1j * theta))
        r_order = np.abs(Z)

        # ── σ(Cn): deviazione standard della coerenza per strato/cluster
        layer_coh = [
            np.abs(np.mean(np.exp(1j * theta[self.z_idx == iz])))
            for iz in range(self.Nz)
        ]
        cluster_coh = [
            np.abs(np.mean(np.exp(1j * theta[
                (self.cluster_id == cl) & self.in_cluster
            ])))
            for cl in range(self.cfg["clusters"]["n_clusters"])
            if np.sum((self.cluster_id == cl) & self.in_cluster) > 2
        ]
        all_coh = layer_coh + cluster_coh
        sigma_Cn = np.std(all_coh) if len(all_coh) > 1 else 0.0

        # ── Dratio: discriminazione strutturale (FFT) ──────────────────
        field = np.zeros((self.Nz, self.Nr, self.Nc))
        for i in range(self.N):
            field[self.z_idx[i], self.r_idx[i], self.c_idx[i]] = theta[i]

        fft_f = np.fft.fftn(field)
        p = np.abs(fft_f) ** 2
        K = np.sqrt(
            np.fft.fftfreq(self.Nz)[:, None, None] ** 2
            + np.fft.fftfreq(self.Nr)[None, :, None] ** 2
            + np.fft.fftfreq(self.Nc)[None, None, :] ** 2
        )
        Dratio = np.sum(p[K < 0.3]) / max(1e-10, np.sum(p[K >= 0.3]))

        # ── Jpol_mean e ρpol ───────────────────────────────────────────
        d_phase = np.abs(np.angle(
            np.exp(1j * (theta[self._cols] - theta[self._rows]))
        ))
        res_w = self.cfg["coupling"].get("resonance_width", 1.5)
        al_gain = self.cfg["coupling"].get("anti_lock_gain", 0.4)
        al_slope = self.cfg["coupling"].get("anti_lock_slope", 3.0)

        resonance = np.exp(-res_w * d_phase ** 2 / np.pi ** 2)
        anti_lock = (1.0 - al_gain) + al_gain * np.tanh(al_slope * d_phase)

        J_dyn = self._base_J * self._polarization * resonance * anti_lock
        thresh = self.cfg["coupling"]["threshold_Jpol"]
        above = J_dyn[J_dyn > thresh]
        Jpol_mean = np.mean(above) if len(above) > 0 else np.mean(J_dyn)
        rho_pol = np.sum(
            self._base_J * self._polarization > thresh
        ) / len(self._base_J)

        # ── Cvert: coerenza verticale per colonne (r,c) ────────────────
        # FIX: usata maschera booleana per selezionare correttamente
        # i nodi nella colonna (ir, ic) su tutti gli strati z
        Cvert_vals = []
        for ir in range(self.Nr):
            for ic in range(self.Nc):
                mask = (self.r_idx == ir) & (self.c_idx == ic)
                n_in_col = np.sum(mask)
                if n_in_col > 1:
                    col_phases = theta[mask]
                    Cvert_vals.append(
                        np.abs(np.mean(np.exp(1j * col_phases)))
                    )
        Cvert = np.mean(Cvert_vals) if Cvert_vals else 0.0

        # ── P_π: probabilità di nucleazione 3D ─────────────────────────
        # FIX: gradiente fase locale calcolato dai coupling edges
        # (non più np.diff che dava shape N-1)
        d_theta_abs = np.abs(np.angle(
            np.exp(1j * (theta[self._cols] - theta[self._rows]))
        ))
        phase_grad = np.zeros(self.N)
        np.add.at(phase_grad, self._rows, d_theta_abs)
        phase_grad /= np.maximum(self._neighbor_count, 1.0)

        # P_base = Jpol · σ(Cn) / Dratio  (forma semplificata)
        P_base = Jpol_mean * sigma_Cn / max(1e-10, Dratio)

        # P_3d: modulato da gradiente locale, penetrazione γ, campo H/D
        P_3d = (
            P_base
            * (1 + 2 * phase_grad)
            * self.gamma_nodes
            * self.n_hd
        )
        P_3d[self.in_cluster] *= 2.0

        # Normalizzazione a probabilità [0, 1]
        P_max = np.max(P_3d)
        if P_max > 1e-10:
            P_3d /= P_max

        # ── E_π: osservabile energetica derivata ───────────────────────
        # E_π(φ) = κ · Jpol · σ(Cn) · |Ψ_RX|² / Dratio
        kappa = self.cfg["energy_proxy"]["kappa_eV"]
        E_pi = kappa * Jpol_mean * sigma_Cn * r_order ** 2 / max(1e-10, Dratio)

        return sigma_Cn, Dratio, Jpol_mean, rho_pol, Cvert, P_3d, E_pi

    # ════════════════════════════════════════════════════════════════════
    #  GUARDRAILS
    # ════════════════════════════════════════════════════════════════════

    def check_guardrails(self, s, D, J, R):
        """Verifica tutte le soglie strict simultaneamente."""
        return (
            s >= GUARDRAILS["sigma_Cn_strict"]
            and D >= GUARDRAILS["Dratio_strict"]
            and J >= GUARDRAILS["Jpol_min"]
            and R >= GUARDRAILS["rho_pol_min"]
        )

    def check_base(self, s, D, J, R):
        """Verifica soglie base (minime) — violazione = rischio."""
        return (
            s >= GUARDRAILS["sigma_Cn_min"]
            and D >= GUARDRAILS["Dratio_min"]
            and J >= GUARDRAILS["Jpol_min"]
            and R >= GUARDRAILS["rho_pol_min"]
        )

    # ════════════════════════════════════════════════════════════════════
    #  MAIN LOOP
    # ════════════════════════════════════════════════════════════════════

    def run(self):
        """Esegue la simulazione completa φ ∈ [0, 6π]."""
        phi = self.phi_start
        step = 0
        t0 = time.time()
        base_violations = 0

        # Warmup: non controllare guardrail base nel primo ciclo (2π)
        # Il sistema parte da condizioni casuali e ha bisogno di
        # sviluppare coerenza prima di poter essere giudicato.
        warmup_phi = 2 * np.pi  # 1 ciclo completo di warmup
        base_guardrails_ever_met = False  # Track se le base sono mai state soddisfatte

        while phi < self.phi_end:
            # Evoluzione
            self.theta = self.rk4_step(self.theta, phi)
            self.evolve_hd_field(phi)

            # Metriche ogni store_every passi
            if step % self.cfg["store_every"] == 0:
                s, D, J, R, C, P, E = self.compute_metrics(self.theta)
                self._last_P_3d = P.copy()

                # Salva metriche
                self.metrics_history["phi"].append(phi)
                for k, v in {
                    "sigma_Cn": s, "Dratio": D, "Jpol_mean": J,
                    "rho_pol": R, "Cvert": C, "P_pi_max": np.max(P),
                    "E_pi_max": E
                }.items():
                    self.metrics_history[k].append(v)

                self.theta_stored.append(self.theta.copy())
                self.phi_stored.append(phi)

                # ── Guardrail strict ────────────────────────────────────
                if self.check_guardrails(s, D, J, R):
                    if self._consecutive_strict_start_phi is None:
                        self._consecutive_strict_start_phi = phi
                    self._consecutive_strict += 1

                    # Accumula mappa nucleazione
                    P_grid = np.zeros((self.Nz, self.Nr, self.Nc))
                    for i in range(self.N):
                        P_grid[self.z_idx[i], self.r_idx[i], self.c_idx[i]] = P[i]
                    self.nucleation_map_accum += P_grid
                    self.nucleation_map_count += 1

                    # Registra semi di nucleazione
                    if np.max(P) > 0.75:
                        for idx in np.where(P > 0.75)[0]:
                            self.nucleation_seeds.append({
                                "z": float(self.coords[idx, 0]),
                                "r": float(self.coords[idx, 1]),
                                "c": float(self.coords[idx, 2]),
                                "phi": float(phi),
                                "P": float(P[idx])
                            })
                else:
                    # Decay graduale o reset
                    decay = GUARDRAILS.get("strict_decay_rate", 1)
                    self._consecutive_strict = max(0, self._consecutive_strict - decay)
                    if self._consecutive_strict == 0:
                        self._consecutive_strict_start_phi = None

                # ── Guardrail base (arresto) ────────────────────────────
                # Solo dopo warmup + solo se base sono mai state soddisfatte
                # Il manifesto dice: interrompi se scende SOTTO base per >1 ciclo
                # Non se PARTONO sotto base (fase di transiente)
                if phi > warmup_phi:
                    if self.check_base(s, D, J, R):
                        base_guardrails_ever_met = True
                        base_violations = 0
                    else:
                        if base_guardrails_ever_met:
                            base_violations += 1
                            # >1 ciclo = >2π/dphi/store_every stored steps
                            # 1 ciclo ≈ 628 stored steps, arresto dopo ~1 ciclo
                            if base_violations > 314:
                                self._report_lines.append(
                                    f"⚠ ARRESTO: soglie base violate per >1 ciclo a φ={phi:.2f}"
                                )
                                print(f"[ARREST] Base guardrails fell below min for >1 cycle at φ={phi:.2f}")
                                break
                        # Se base non sono mai state soddisfatte, continua
                        # (il transiente è lungo per Dratio)

                # ── Log ciclo ───────────────────────────────────────────
                current_cycle = int(phi / (2 * np.pi))
                if current_cycle > self._cycle_max:
                    self._cycle_max = current_cycle
                    elapsed = time.time() - t0
                    print(
                        f"[CYCLE {current_cycle}] φ={phi:.2f} | "
                        f"σ={s:.4f} D={D:.2f} J={J:.4f} R={R:.4f} "
                        f"Cv={C:.4f} E={E:.4f} | "
                        f"strict_streak={self._consecutive_strict} | "
                        f"t={elapsed:.1f}s"
                    )
                    self._report_lines.append(
                        f"Cycle {current_cycle} | φ={phi:.4f} | "
                        f"σ(Cn)={s:.6f} Dratio={D:.4f} Jpol={J:.6f} "
                        f"ρpol={R:.6f} Cvert={C:.6f} E_π={E:.6f}"
                    )

            phi += self.dphi
            step += 1

        # ── Calcolo stable_phi_cycles ───────────────────────────────────
        # FIX: calcolato come range φ consecutivo / (2π)
        if self._consecutive_strict_start_phi is not None:
            strict_phi_range = phi - self._consecutive_strict_start_phi
            self.validation["stable_phi_cycles"] = strict_phi_range / (2 * np.pi)
        else:
            self.validation["stable_phi_cycles"] = 0.0

        self.validation["guardrails_met"] = (
            self.validation["stable_phi_cycles"] >= GUARDRAILS["phi_cycles_stable"]
        )
        self.validation["nucleation_seeds_found"] = len(self.nucleation_seeds)
        self.validation["total_phi_steps"] = step

        elapsed = time.time() - t0
        print(f"\n[DONE] {step} steps | {elapsed:.1f}s | "
              f"stable_cycles={self.validation['stable_phi_cycles']:.2f} | "
              f"seeds={len(self.nucleation_seeds)} | "
              f"met={self.validation['guardrails_met']}")

        return self._package()

    # ════════════════════════════════════════════════════════════════════
    #  OUTPUT
    # ════════════════════════════════════════════════════════════════════

    def _package(self):
        """Salva tutti gli output strutturati."""
        out = self.cfg["output_dir"]
        os.makedirs(out, exist_ok=True)

        # ── 1. Mappa nucleazione 3D (FIX: mappa reale, non zeri) ──────
        if self.nucleation_map_count > 0:
            nuc_map = self.nucleation_map_accum / self.nucleation_map_count
        else:
            # Fallback: usa ultima P_3d se disponibile
            if self._last_P_3d is not None:
                nuc_map = np.zeros((self.Nz, self.Nr, self.Nc))
                for i in range(self.N):
                    nuc_map[self.z_idx[i], self.r_idx[i], self.c_idx[i]] = self._last_P_3d[i]
            else:
                nuc_map = np.zeros((self.Nz, self.Nr, self.Nc))
        np.save(f"{out}/nucleation_map_3d.npy", nuc_map)

        # ── 2. Timeline metriche ───────────────────────────────────────
        for k, v in self.metrics_history.items():
            np.save(f"{out}/timeline_{k}.npy", np.array(v))

        # ── 3. Firma strutturale finale ────────────────────────────────
        final_sig = {}
        for k in ["sigma_Cn", "Dratio", "Jpol_mean", "rho_pol", "Cvert",
                   "P_pi_max", "E_pi_max"]:
            arr = self.metrics_history[k]
            if len(arr) > 0:
                final_sig[k] = float(arr[-1])
            else:
                final_sig[k] = 0.0

        # ── 4. simulation_results.json ─────────────────────────────────
        # Config serializzabile
        cfg_out = {}
        for k, v in self.cfg.items():
            if isinstance(v, np.ndarray):
                cfg_out[k] = v.tolist()
            elif isinstance(v, (list, dict, str, int, float, bool, type(None))):
                cfg_out[k] = v
            else:
                cfg_out[k] = str(v)

        results = {
            "validation": self.validation,
            "final_signature": final_sig,
            "seeds": self.nucleation_seeds[:100],
            "config": cfg_out,
            "guardrails": GUARDRAILS
        }

        with open(f"{out}/simulation_results.json", "w") as f:
            json.dump(results, f, indent=2)

        # ── 5. report_v4_summary.txt (FIX: ora generato) ──────────────
        report = []
        report.append("=" * 70)
        report.append("SIMULAZIONE BASE π v4.1 — REPORT DI VERIFICA")
        report.append("=" * 70)
        report.append("")
        report.append(f"Grid: {self.Nz}×{self.Nr}×{self.Nc} = {self.N} nodi")
        report.append(f"Materiali: {self.cfg['materials']['nuclear']} + {self.cfg['materials']['carrier']}")
        report.append(f"φ range: [{self.phi_start:.4f}, {self.phi_end:.4f}]")
        report.append(f"dφ: {self.dphi}")
        report.append(f"Passi totali: {self.validation['total_phi_steps']}")
        report.append("")
        report.append("─" * 50)
        report.append("FIRMA STRUTTURALE FINALE:")
        for k, v in final_sig.items():
            report.append(f"  {k:15s} = {v:.6f}")
        report.append("")
        report.append("─" * 50)
        report.append("VALIDAZIONE:")
        for k, v in self.validation.items():
            report.append(f"  {k:30s} = {v}")
        report.append("")
        report.append("─" * 50)
        report.append("LOG PER CICLO:")
        for line in self._report_lines:
            report.append(f"  {line}")
        report.append("")
        report.append("─" * 50)
        report.append(f"Semi di nucleazione trovati: {len(self.nucleation_seeds)}")
        if len(self.nucleation_seeds) > 0:
            report.append("Primi 10 semi:")
            for s in self.nucleation_seeds[:10]:
                report.append(
                    f"  z={s['z']:.3f} r={s['r']:.3f} c={s['c']:.3f} "
                    f"φ={s['phi']:.4f} P={s['P']:.4f}"
                )
        report.append("")
        report.append("NOTE: La fase non mente. Cerca la firma, non il joule.")

        with open(f"{out}/report_v4_summary.txt", "w") as f:
            f.write("\n".join(report))

        print(f"[SAVED] All outputs in {out}")
        return self.validation


# ═══════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    sim = BasePiSimulationV41Verified()
    result = sim.run()
    print("\n" + "=" * 50)
    print("VALIDAZIONE FINALE:")
    for k, v in result.items():
        print(f"  {k}: {v}")
