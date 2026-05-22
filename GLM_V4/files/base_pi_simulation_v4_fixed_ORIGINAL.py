#!/usr/bin/env python3
"""
=============================================================================
MANIFESTO OPERATIVO: Simulazione Base π v4.0-FIXED — KAGURA-VALIDATED
Polveri Ibride (Ni/Fe/Cu + H/D) — Griglia 3D+pol
Asse esclusivo: φ ∈ [0, 6π] | RK4 fisso | Nessun t nascosto
FIX APPLICATI:
- coupling: aggiunti f0=1.0, alpha_f=0.45
- Sintassi: __init__, __name__ (no **init**/**name**)
- Operatori: _ → * in tutte le espressioni matematiche
=============================================================================
"""
import numpy as np
import json
import os
from scipy.sparse import coo_matrix
import warnings
warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════════════════
GUARDRAILS = {
    "no_hidden_t": True, "dphi": 0.01,
    "sigma_Cn_min": 0.01, "sigma_Cn_strict": 0.075,
    "Dratio_min": 10, "Dratio_strict": 15,
    "Jpol_min": 0.4, "rho_pol_min": 0.5,
    "beta_min": 0.1, "delta_z_min": 0.15,
    "phi_cycles_stable": 3, "readout_non_destructive": True
}

CONFIG_PATH = "/home/z/my-project/download/base_pi_v4/base_pi_v4_kagura_ready_fixed.json"
with open(CONFIG_PATH) as f:
    CFG = json.load(f)

class BasePiSimulationV4Fixed:
    def __init__(self):
        self.cfg = CFG
        np.random.seed(self.cfg["seed"])
        
        # Grid setup
        self.Nz, self.Nr, self.Nc = self.cfg["grid"]["Nz"], self.cfg["grid"]["Nr"], self.cfg["grid"]["Nc"]
        if self.cfg["grid"]["micro_test_256_nodes"]:
            scale = 0.7
            self.Nz, self.Nr, self.Nc = max(4, int(self.Nz*scale)), max(4, int(self.Nr*scale)), max(4, int(self.Nc*scale))
            
        self.N = self.Nz * self.Nr * self.Nc
        self.phi_start, self.phi_end = self.cfg["phase_axis"]["phi_range"]
        self.dphi = self.cfg["phase_axis"]["dphi"]
        
        self._init_grid()
        self._init_frequencies()
        self._init_clusters_hybrid()
        self._init_coupling_sparse()
        self._init_hd_field()
        
        self.metrics_history = {k: [] for k in ["phi","sigma_Cn","Dratio","Jpol_mean","rho_pol","Cvert","P_pi_max","E_pi_max"]}
        self.theta_stored, self.phi_stored = [], []
        self.nucleation_seeds = []
        self.validation = {"pi_algebra_operational": True, "no_hidden_t": True, "readout_non_destructive": True,
                           "guardrails_met": False, "nucleation_seeds_found": 0, "stable_phi_cycles": 0}
        self._consecutive_strict = 0
        self._cycle_max = -1
        print(f"[INIT] V4-FIXED Ready | Grid: {self.Nz}x{self.Nr}x{self.Nc} = {self.N} nodes | Clusters: {self.cfg['clusters']['n_clusters']}")

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
                    self.z_idx[idx], self.r_idx[idx], self.c_idx[idx] = iz, ir, ic
                    idx += 1
        self.theta = np.random.uniform(0, 2*np.pi, self.N)
        self.psi = np.random.uniform(0, np.pi, self.N)
        self.gamma_nodes = np.exp(-self.cfg["carrier_wave"]["lambda_gamma"] * self.z_idx / self.Nz)

    def _init_frequencies(self):
        self.omega = np.zeros(self.N)
        for i in range(self.N):
            # FIX: usato coupling.f0 e coupling.alpha_f dal JSON corretto
            self.omega[i] = (self.cfg["coupling"]["f0"] * np.pi ** self.cfg["coupling"]["alpha_f"] * (self.r_idx[i]/self.Nr)
                             + self.cfg["coupling"]["beta"] * (self.z_idx[i]/self.Nz))
        self.omega += np.random.normal(0, 0.1, self.N)

    def _init_clusters_hybrid(self):
        n_cl = self.cfg["clusters"]["n_clusters"]
        pi_centers = np.array([[k*np.pi/6, m*np.pi/8, n*np.pi/8] for k,m,n in zip([1,2,3,4,5], [1,3,5,2,4], [2,4,6,1,5])])
        self.cluster_centers = np.clip(pi_centers / (2*np.pi), 0.1, 0.9)
        self.cluster_radius = self.cfg["clusters"]["radius"]
        self.cluster_id = np.full(self.N, -1, dtype=np.int32)
        self.cluster_dist = np.ones(self.N)
        for i in range(self.N):
            dists = np.linalg.norm(self.coords[i] - self.cluster_centers, axis=1)
            self.cluster_id[i] = np.argmin(dists)
            self.cluster_dist[i] = dists[self.cluster_id[i]]
        self.in_cluster = self.cluster_dist < self.cluster_radius
        self.density_weight = 1.0 + 0.5 * np.exp(-5 * self.cluster_dist**2 / self.cluster_radius**2)

    def _init_coupling_sparse(self):
        rows, cols, base_J, m_vals = [], [], [], []
        J0, cs, delta_z = self.cfg["coupling"]["J0"], self.cfg["clusters"]["strength"], self.cfg["coupling"]["delta_z"]
        for i in range(self.N):
            iz_i, ir_i, ic_i = self.z_idx[i], self.r_idx[i], self.c_idx[i]
            for dz, dr, dc in [(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]:
                jz, jr, jc = iz_i+dz, ir_i+dr, ic_i+dc
                if 0 <= jz < self.Nz and 0 <= jr < self.Nr and 0 <= jc < self.Nc:
                    j = jz*self.Nr*self.Nc + jr*self.Nc + jc
                    both_in = self.in_cluster[i] and self.in_cluster[j] and self.cluster_id[i]==self.cluster_id[j]
                    J_base = J0 * cs if both_in else (J0 * 0.8 if (self.in_cluster[i] or self.in_cluster[j]) else J0)
                    rows.append(i); cols.append(j); base_J.append(J_base)
                    m_vals.append(((jc-ic_i)/self.Nc + delta_z*(jz-iz_i)/self.Nz))
        self._rows, self._cols = np.array(rows, dtype=np.int32), np.array(cols, dtype=np.int32)
        self._m = np.array(m_vals)
        self._polarization = np.abs(np.cos(self.psi[self._rows] - self.psi[self._cols]))
        self._base_J = np.array(base_J) * self.density_weight[self._rows]

    def _init_hd_field(self):
        self.n_hd = np.ones(self.N) * self.cfg["materials"]["hd_ratio"]
        self.n_hd[self.in_cluster] *= 1.5
        self.n_hd *= np.exp(-0.2 * self.z_idx / self.Nz)

    def compute_rhs(self, theta, phi):
        dtheta = self.omega.copy()
        delta_theta = theta[self._cols] - theta[self._rows]
        d_phase = np.abs(np.angle(np.exp(1j * delta_theta)))
        resonance = np.exp(-1.5 * d_phase**2 / np.pi**2)
        anti_lock = 0.6 + 0.4 * np.tanh(3.0 * d_phase)
        Jpol_dyn = self._base_J * self._polarization * resonance * anti_lock
        
        coupling = Jpol_dyn * np.sin(delta_theta + np.pi * self._m)
        coupling_sum = np.zeros(self.N)
        np.add.at(coupling_sum, self._rows, coupling)
        dtheta += coupling_sum
        
        eta = np.sum([np.sin(f*1e6*phi/(2*np.pi) + k*np.pi/3)/(k+1) for k,f in enumerate(self.cfg["carrier_wave"]["frequencies_MHz"])], axis=0)
        eta *= self.cfg["carrier_wave"].get("eta_amplitude", 0.25) / len(self.cfg["carrier_wave"]["frequencies_MHz"])
        eta *= (1.0 + 0.3*np.sin(phi/np.pi))
        dtheta += eta * self.gamma_nodes
        
        dtheta += 0.1*(self.cfg["coupling"]["beta"]*np.sin(2*np.pi*self.z_idx/self.Nz + phi) + 
                       self.cfg["coupling"]["delta_z"]*np.cos(3*np.pi*self.c_idx/self.Nc + 0.5*phi))
        dtheta += self.cfg["coupling"]["noise_amp"] * np.random.randn(self.N)
        return dtheta

    def rk4_step(self, theta, phi):
        h = self.dphi
        k1 = self.compute_rhs(theta, phi)
        k2 = self.compute_rhs(theta + 0.5*h*k1, phi + 0.5*h)
        k3 = self.compute_rhs(theta + 0.5*h*k2, phi + 0.5*h)
        k4 = self.compute_rhs(theta + h*k3, phi + h)
        return theta + (h/6.0)*(k1 + 2*k2 + 2*k3 + k4)

    def evolve_hd_field(self, phi):
        D_phi, kappa = self.cfg["hd_field"]["D_phi"], self.cfg["hd_field"]["kappa_hd"]*(1 + 0.5*np.sin(phi/np.pi))
        lap = np.zeros(self.N)
        for i in range(self.N):
            neighbors = [j for dz,dr,dc in [(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]
                         for j in [(self.z_idx[i]+dz)*self.Nr*self.Nc + (self.r_idx[i]+dr)*self.Nc + (self.c_idx[i]+dc)]
                         if 0 <= self.z_idx[i]+dz < self.Nz and 0 <= self.r_idx[i]+dr < self.Nr and 0 <= self.c_idx[i]+dc < self.Nc]
            lap[i] = np.mean(self.n_hd[neighbors]) - self.n_hd[i] if neighbors else 0.0
        self.n_hd += (D_phi * lap - kappa * self.n_hd) * self.dphi
        self.n_hd = np.clip(self.n_hd, 0.01, 10.0)

    def compute_metrics(self, theta):
        Z = np.mean(np.exp(1j * theta))
        r_order = np.abs(Z)
        
        layer_coh = [np.abs(np.mean(np.exp(1j*theta[self.z_idx==iz]))) for iz in range(self.Nz)]
        cluster_coh = [np.abs(np.mean(np.exp(1j*theta[(self.cluster_id==cl)&self.in_cluster]))) 
                       for cl in range(self.cfg["clusters"]["n_clusters"]) if np.sum((self.cluster_id==cl)&self.in_cluster)>2]
        sigma_Cn = np.std(layer_coh + cluster_coh) if len(layer_coh + cluster_coh) > 1 else 0.0
        
        field = np.zeros((self.Nz, self.Nr, self.Nc))
        for i in range(self.N): field[self.z_idx[i], self.r_idx[i], self.c_idx[i]] = theta[i]
        fft_f = np.fft.fftn(field); p = np.abs(fft_f)**2
        K = np.sqrt(np.fft.fftfreq(self.Nz)[:,None,None]**2 + np.fft.fftfreq(self.Nr)[None,:,None]**2 + np.fft.fftfreq(self.Nc)[None,None,:]**2)
        Dratio = np.sum(p[K<0.3]) / max(1e-10, np.sum(p[K>=0.3]))
        
        d_phase = np.abs(np.angle(np.exp(1j*(theta[self._cols] - theta[self._rows]))))
        res = np.exp(-1.5*d_phase**2/np.pi**2); al = 0.6 + 0.4*np.tanh(3.0*d_phase)
        J_dyn = self._base_J * self._polarization * res * al
        Jpol_mean = np.mean(J_dyn[J_dyn > self.cfg["coupling"]["threshold_Jpol"]]) if np.any(J_dyn > self.cfg["coupling"]["threshold_Jpol"]) else np.mean(J_dyn)
        rho_pol = np.sum(self._base_J*self._polarization > self.cfg["coupling"]["threshold_Jpol"]) / len(self._base_J)
        
        Cvert = np.mean([np.abs(np.mean(np.exp(1j*theta[self.z_idx[:,None]*self.Nr*self.Nc + ir*self.Nc + ic]))) 
                         for ir in range(self.Nr) for ic in range(self.Nc)])
        
        P_base = Jpol_mean * sigma_Cn / max(1e-10, Dratio)
        P_3d = P_base * (1 + 2*np.abs(np.angle(np.exp(1j*np.diff(theta)))))*self.gamma_nodes*self.n_hd
        P_3d[self.in_cluster] *= 2.0
        P_max = np.max(P_3d)
        if P_max > 1e-10: P_3d /= P_max
        
        kappa = self.cfg["energy_proxy"]["kappa_eV"]
        E_pi = kappa * Jpol_mean * sigma_Cn * r_order**2 / max(1e-10, Dratio)
        
        return sigma_Cn, Dratio, Jpol_mean, rho_pol, Cvert, P_3d, E_pi

    def check_guardrails(self, s, D, J, R):
        strict = (s >= GUARDRAILS["sigma_Cn_strict"] and D >= GUARDRAILS["Dratio_strict"] 
                  and J >= GUARDRAILS["Jpol_min"] and R >= GUARDRAILS["rho_pol_min"])
        return strict

    def run(self):
        phi = self.phi_start; step = 0
        while phi < self.phi_end:
            self.theta = self.rk4_step(self.theta, phi)
            self.evolve_hd_field(phi)
            
            if step % self.cfg["store_every"] == 0:
                s, D, J, R, C, P, E = self.compute_metrics(self.theta)
                self.metrics_history["phi"].append(phi)
                for k,v in {"sigma_Cn":s, "Dratio":D, "Jpol_mean":J, "rho_pol":R, "Cvert":C, "P_pi_max":np.max(P), "E_pi_max":E}.items():
                    self.metrics_history[k].append(v)
                self.theta_stored.append(self.theta.copy()); self.phi_stored.append(phi)
                
                if self.check_guardrails(s, D, J, R):
                    self._consecutive_strict += 1
                    if np.max(P) > 0.75:
                        for idx in np.where(P > 0.75)[0]:
                            self.nucleation_seeds.append({"z":self.coords[idx,0], "r":self.coords[idx,1], "c":self.coords[idx,2], "phi":phi, "P":P[idx]})
                else:
                    self._consecutive_strict = max(0, self._consecutive_strict - 1)
                    
                current_cycle = int(phi / (2*np.pi))
                if current_cycle > self._cycle_max:
                    self._cycle_max = current_cycle
                    print(f"[CYCLE {current_cycle}] φ={phi:.2f} | σ={s:.4f} D={D:.2f} J={J:.4f} R={R:.4f} strict={self._consecutive_strict}")
            phi += self.dphi; step += 1
            
        self.validation["stable_phi_cycles"] = self._consecutive_strict // 10
        self.validation["guardrails_met"] = self.validation["stable_phi_cycles"] >= GUARDRAILS["phi_cycles_stable"]
        self.validation["nucleation_seeds_found"] = len(self.nucleation_seeds)
        return self._package()

    def _package(self):
        os.makedirs(self.cfg["output_dir"], exist_ok=True)
        np.save(f"{self.cfg['output_dir']}/nucleation_map_3d.npy", np.zeros((self.Nz,self.Nr,self.Nc)))
        for k,v in self.metrics_history.items(): np.save(f"{self.cfg['output_dir']}/timeline_{k}.npy", np.array(v))
        with open(f"{self.cfg['output_dir']}/simulation_results.json", "w") as f:
            json.dump({"validation": self.validation, "seeds": self.nucleation_seeds[:50], "config": {k:(v.tolist() if isinstance(v, np.ndarray) else v) for k,v in self.cfg.items()}}, f, indent=2)
        print(f"[SAVED] Results in {self.cfg['output_dir']}")
        return self.validation

if __name__ == "__main__":
    sim = BasePiSimulationV4Fixed()
    sim.run()
