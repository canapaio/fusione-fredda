#!/usr/bin/env python3
"""
Visualizzazioni professionali per la Simulazione Base π v3.0
Genera: timeline metriche, mappa nucleazione 3D, firma strutturale, heatmap
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import json
import os

# Font setup per italiano
fm.fontManager.addfont('/usr/share/fonts/truetype/chinese/SarasaMonoSC-Regular.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Sarasa Mono SC']
plt.rcParams['axes.unicode_minus'] = False

# Palette professionale
PALETTE = {
    'bg': '#F8FAFC',
    'text': '#243447',
    'accent_blue': '#4C6EF5',
    'accent_teal': '#3AAFA9',
    'accent_amber': '#EE7733',
    'accent_red': '#CC3311',
    'accent_purple': '#7C3AED',
    'grid': '#E2E8F0',
    'threshold': '#EF4444',
    'success': '#10B981',
}

output_dir = "/home/z/my-project/download"

# ═══════════════════════════════════════════════════════════════════════════
# CARICAMENTO DATI
# ═══════════════════════════════════════════════════════════════════════════

phi = np.load(os.path.join(output_dir, "timeline_phi.npy"))
sigma_Cn = np.load(os.path.join(output_dir, "timeline_sigma_Cn.npy"))
Dratio = np.load(os.path.join(output_dir, "timeline_Dratio.npy"))
Jpol = np.load(os.path.join(output_dir, "timeline_Jpol_mean.npy"))
rho_pol = np.load(os.path.join(output_dir, "timeline_rho_pol.npy"))
Cvert = np.load(os.path.join(output_dir, "timeline_Cvert.npy"))
P_max = np.load(os.path.join(output_dir, "timeline_P_pi_max.npy"))
E_max = np.load(os.path.join(output_dir, "timeline_E_pi_max.npy"))

nucleation_map = np.load(os.path.join(output_dir, "nucleation_map_3d.npy"))

with open(os.path.join(output_dir, "simulation_results.json")) as f:
    results = json.load(f)

# φ normalizzato in cicli
phi_cycles = phi / (2 * np.pi)

# ═══════════════════════════════════════════════════════════════════════════
# FIGURA 1: TIMELINE DELLE METRICHE CHIAVE
# ═══════════════════════════════════════════════════════════════════════════

fig, axes = plt.subplots(3, 2, figsize=(16, 14), facecolor=PALETTE['bg'])
fig.suptitle('Simulazione Base π — Timeline Metriche di Fase\n'
             'Polveri Ibride Ni + Serpentino Nanostrutturato  |  φ ∈ [0, 6π]',
             fontsize=16, fontweight='bold', color=PALETTE['text'], y=0.98)

metric_data = [
    (sigma_Cn, 'σ(Cn) — Coerenza Armonica', 0.075, PALETTE['accent_blue']),
    (Dratio, 'Dratio — Discriminazione Strutturale', 15, PALETTE['accent_teal']),
    (Jpol, 'Jpol — Accoppiamento Polarizzato', 0.4, PALETTE['accent_amber']),
    (rho_pol, 'ρpol — Densità Accoppiamento Attivo', 0.5, PALETTE['accent_purple']),
    (Cvert, 'Cvert — Coerenza Verticale', None, PALETTE['accent_red']),
    (P_max, 'Pπ max — Probabilità Nucleazione', 0.75, '#009988'),
]

for idx, (data, title, threshold, color) in enumerate(metric_data):
    ax = axes[idx // 2, idx % 2]
    ax.set_facecolor(PALETTE['bg'])
    
    ax.plot(phi_cycles, data, color=color, linewidth=1.2, alpha=0.85)
    
    if threshold is not None:
        ax.axhline(y=threshold, color=PALETTE['threshold'], linestyle='--',
                   linewidth=1.0, alpha=0.7, label=f'Soglia: {threshold}')
        # Evidenzia regioni sopra soglia
        above = data >= threshold
        ax.fill_between(phi_cycles, 0, data, where=above,
                        color=color, alpha=0.15)
    
    ax.set_title(title, fontsize=12, fontweight='bold', color=PALETTE['text'], pad=8)
    ax.set_xlabel('Cicli φ', fontsize=10, color=PALETTE['text'])
    ax.set_ylabel(title.split('—')[0].strip(), fontsize=10, color=PALETTE['text'])
    ax.grid(True, alpha=0.15, color=PALETTE['grid'])
    ax.tick_params(colors=PALETTE['text'], labelsize=9)
    
    for spine in ax.spines.values():
        spine.set_color(PALETTE['grid'])
    
    if threshold is not None:
        ax.legend(fontsize=9, loc='best', framealpha=0.8)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(os.path.join(output_dir, "fig1_timeline_metriche.png"), dpi=200,
            facecolor=PALETTE['bg'], bbox_inches='tight')
plt.close()
print("[SAVED] fig1_timeline_metriche.png")

# ═══════════════════════════════════════════════════════════════════════════
# FIGURA 2: OSSERVABILE ENERGETICO E FASE DI NUCLEAZIONE
# ═══════════════════════════════════════════════════════════════════════════

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), facecolor=PALETTE['bg'])
fig.suptitle('Simulazione Base π — Osservabile Energetico e Firma di Nucleazione',
             fontsize=14, fontweight='bold', color=PALETTE['text'], y=0.98)

# Eπ
ax1.set_facecolor(PALETTE['bg'])
ax1.plot(phi_cycles, E_max, color=PALETTE['accent_amber'], linewidth=1.2, alpha=0.85)
ax1.fill_between(phi_cycles, 0, E_max, color=PALETTE['accent_amber'], alpha=0.12)
ax1.set_title('Eπ(φ) — Osservabile Energetico Derivato  (NON energia reale)',
              fontsize=12, fontweight='bold', color=PALETTE['text'])
ax1.set_xlabel('Cicli φ', fontsize=10, color=PALETTE['text'])
ax1.set_ylabel('Eπ', fontsize=10, color=PALETTE['text'])
ax1.grid(True, alpha=0.15, color=PALETTE['grid'])
ax1.tick_params(colors=PALETTE['text'], labelsize=9)
for spine in ax1.spines.values():
    spine.set_color(PALETTE['grid'])

# Firma combinata: σ(Cn) × Dratio normalizzata
combined = sigma_Cn * Dratio / np.max(sigma_Cn * Dratio + 1e-10)
ax2.set_facecolor(PALETTE['bg'])
ax2.plot(phi_cycles, combined, color=PALETTE['accent_teal'], linewidth=1.3,
         label='σ(Cn)·Dratio (normalizzata)')
ax2.plot(phi_cycles, sigma_Cn / np.max(sigma_Cn), color=PALETTE['accent_blue'],
         linewidth=0.9, alpha=0.6, linestyle='--', label='σ(Cn) (normalizzata)')
ax2.plot(phi_cycles, Dratio / np.max(Dratio), color=PALETTE['accent_red'],
         linewidth=0.9, alpha=0.6, linestyle=':', label='Dratio (normalizzata)')
ax2.set_title('Firma Strutturale Combinata  σ(Cn)·Dratio',
              fontsize=12, fontweight='bold', color=PALETTE['text'])
ax2.set_xlabel('Cicli φ', fontsize=10, color=PALETTE['text'])
ax2.set_ylabel('Ampiezza normalizzata', fontsize=10, color=PALETTE['text'])
ax2.legend(fontsize=9, loc='best', framealpha=0.8)
ax2.grid(True, alpha=0.15, color=PALETTE['grid'])
ax2.tick_params(colors=PALETTE['text'], labelsize=9)
for spine in ax2.spines.values():
    spine.set_color(PALETTE['grid'])

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(os.path.join(output_dir, "fig2_energetico_firma.png"), dpi=200,
            facecolor=PALETTE['bg'], bbox_inches='tight')
plt.close()
print("[SAVED] fig2_energetico_firma.png")

# ═══════════════════════════════════════════════════════════════════════════
# FIGURA 3: HEATMAP NUCLEAZIONE 3D (proiezioni)
# ═══════════════════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), facecolor=PALETTE['bg'])
fig.suptitle('Mappa di Probabilità di Nucleazione H/D — Proiezioni 3D',
             fontsize=14, fontweight='bold', color=PALETTE['text'], y=1.02)

# Proiezione Z-R (media su C)
proj_zr = np.mean(nucleation_map, axis=2)
im0 = axes[0].imshow(proj_zr, aspect='auto', cmap='YlOrRd', origin='lower',
                      interpolation='bilinear')
axes[0].set_title('Proiezione Z–R  (media su C)', fontsize=11, fontweight='bold',
                  color=PALETTE['text'])
axes[0].set_xlabel('Riga (r)', fontsize=10, color=PALETTE['text'])
axes[0].set_ylabel('Strato Z', fontsize=10, color=PALETTE['text'])
plt.colorbar(im0, ax=axes[0], shrink=0.8, pad=0.02, label='Pπ nucleazione')

# Proiezione Z-C (media su R)
proj_zc = np.mean(nucleation_map, axis=1)
im1 = axes[1].imshow(proj_zc, aspect='auto', cmap='YlOrRd', origin='lower',
                      interpolation='bilinear')
axes[1].set_title('Proiezione Z–C  (media su R)', fontsize=11, fontweight='bold',
                  color=PALETTE['text'])
axes[1].set_xlabel('Colonna (c)', fontsize=10, color=PALETTE['text'])
axes[1].set_ylabel('Strato Z', fontsize=10, color=PALETTE['text'])
plt.colorbar(im1, ax=axes[1], shrink=0.8, pad=0.02, label='Pπ nucleazione')

# Proiezione R-C (media su Z)
proj_rc = np.mean(nucleation_map, axis=0)
im2 = axes[2].imshow(proj_rc, aspect='auto', cmap='YlOrRd', origin='lower',
                      interpolation='bilinear')
axes[2].set_title('Proiezione R–C  (media su Z)', fontsize=11, fontweight='bold',
                  color=PALETTE['text'])
axes[2].set_xlabel('Colonna (c)', fontsize=10, color=PALETTE['text'])
axes[2].set_ylabel('Riga (r)', fontsize=10, color=PALETTE['text'])
plt.colorbar(im2, ax=axes[2], shrink=0.8, pad=0.02, label='Pπ nucleazione')

for ax in axes:
    ax.tick_params(colors=PALETTE['text'], labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(PALETTE['grid'])

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "fig3_heatmap_nucleazione.png"), dpi=200,
            facecolor=PALETTE['bg'], bbox_inches='tight')
plt.close()
print("[SAVED] fig3_heatmap_nucleazione.png")

# ═══════════════════════════════════════════════════════════════════════════
# FIGURA 4: FIRMA STRUTTURALE (radar + bar)
# ═══════════════════════════════════════════════════════════════════════════

sig = results['final_signature']

fig = plt.figure(figsize=(16, 7), facecolor=PALETTE['bg'])
ax_radar = fig.add_subplot(121, polar=True)
ax_bar = fig.add_subplot(122)

# --- Radar chart: coerenze armoniche + strati ---
categories = [f'C_h{i+1}' for i in range(len(sig['C_harmonics']))] + \
             [f'L{z+1}' for z in range(min(6, len(sig['C_layers'])))]
values = sig['C_harmonics'] + sig['C_layers'][:6]

N_cat = len(categories)
angles = np.linspace(0, 2 * np.pi, N_cat, endpoint=False).tolist()
values_plot = values + [values[0]]  # close the polygon
angles += angles[:1]

ax_radar.set_facecolor(PALETTE['bg'])
ax_radar.set_theta_offset(np.pi / 2)
ax_radar.set_theta_direction(-1)
ax_radar.set_rlabel_position(0)

ax_radar.plot(angles, values_plot, 'o-', linewidth=2, color=PALETTE['accent_blue'],
              markersize=4)
ax_radar.fill(angles, values_plot, alpha=0.25, color=PALETTE['accent_blue'])
ax_radar.set_xticks(angles[:-1])
ax_radar.set_xticklabels(categories, fontsize=8, color=PALETTE['text'])
ax_radar.set_title('Firma Strutturale S\nCoerenze Armoniche e per Strato',
                   fontsize=12, fontweight='bold', color=PALETTE['text'], pad=20)
ax_radar.grid(True, alpha=0.2)

# --- Bar chart: parametri firma ---
param_names = ['σ(Cn)', 'Dratio/100', 'Ψ_RX', 'I_dens']
param_values = [
    sig['sigma_Cn'],
    sig['D'] / 100,  # scalato per visualizzazione
    sig['Psi_RX_amp'],
    min(abs(sig['I_dens']), 10)  # cap per visualizzazione
]

bars = ax_bar.bar(param_names, param_values,
                  color=[PALETTE['accent_blue'], PALETTE['accent_teal'],
                         PALETTE['accent_amber'], PALETTE['accent_purple']],
                  alpha=0.85, edgecolor='white', linewidth=0.5)
ax_bar.set_facecolor(PALETTE['bg'])
ax_bar.set_title('Parametri della Firma Strutturale Finale',
                 fontsize=12, fontweight='bold', color=PALETTE['text'])
ax_bar.set_ylabel('Valore', fontsize=10, color=PALETTE['text'])
ax_bar.grid(True, axis='y', alpha=0.15, color=PALETTE['grid'])
ax_bar.tick_params(colors=PALETTE['text'], labelsize=10)
for spine in ax_bar.spines.values():
    spine.set_color(PALETTE['grid'])

# Labels sopra le barre
for bar, val in zip(bars, [sig['sigma_Cn'], sig['D'], sig['Psi_RX_amp'], sig['I_dens']]):
    ax_bar.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
               f'{val:.3f}', ha='center', va='bottom', fontsize=9,
               color=PALETTE['text'], fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "fig4_firma_strutturale.png"), dpi=200,
            facecolor=PALETTE['bg'], bbox_inches='tight')
plt.close()
print("[SAVED] fig4_firma_strutturale.png")

# ═══════════════════════════════════════════════════════════════════════════
# FIGURA 5: GUARDRAIL E VALIDAZIONE
# ═══════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(14, 6), facecolor=PALETTE['bg'])

# Normalizza tutte le metriche rispetto alle soglie
norm_sigma = sigma_Cn / 0.075
norm_Dratio = Dratio / 15
norm_Jpol = Jpol / 0.4
norm_rhopol = rho_pol / 0.5

ax.set_facecolor(PALETTE['bg'])
ax.plot(phi_cycles, norm_sigma, color=PALETTE['accent_blue'], linewidth=1.2,
        label='σ(Cn) / 0.075', alpha=0.85)
ax.plot(phi_cycles, norm_Dratio, color=PALETTE['accent_teal'], linewidth=1.2,
        label='Dratio / 15', alpha=0.85)
ax.plot(phi_cycles, norm_Jpol, color=PALETTE['accent_amber'], linewidth=1.2,
        label='Jpol / 0.4', alpha=0.85)
ax.plot(phi_cycles, norm_rhopol, color=PALETTE['accent_purple'], linewidth=1.2,
        label='ρpol / 0.5', alpha=0.85)

# Soglia unitaria
ax.axhline(y=1.0, color=PALETTE['threshold'], linestyle='--', linewidth=1.5,
           alpha=0.8, label='Soglia unitaria (1.0)')

# Zona di validazione
ax.fill_between(phi_cycles, 0, 1.0, color=PALETTE['threshold'], alpha=0.06,
                label='Zona sotto soglia')

# Evidenzia regioni dove TUTTE le metriche sono sopra soglia
all_above = (norm_sigma >= 1.0) & (norm_Dratio >= 1.0) & (norm_Jpol >= 1.0) & (norm_rhopol >= 1.0)
ax.fill_between(phi_cycles, 0, 5, where=all_above,
                color=PALETTE['success'], alpha=0.12, label='Tutti guardrail soddisfatti')

ax.set_title('Simulazione Base π — Guardrail Dinamici (Metriche Normalizzate alle Soglie)',
             fontsize=13, fontweight='bold', color=PALETTE['text'])
ax.set_xlabel('Cicli φ', fontsize=11, color=PALETTE['text'])
ax.set_ylabel('Rapporto metrica / soglia', fontsize=11, color=PALETTE['text'])
ax.legend(fontsize=9, loc='upper left', framealpha=0.9, ncol=2)
ax.grid(True, alpha=0.15, color=PALETTE['grid'])
ax.set_ylim(0, min(5, np.max(norm_Dratio) * 1.1))
ax.tick_params(colors=PALETTE['text'], labelsize=9)
for spine in ax.spines.values():
    spine.set_color(PALETTE['grid'])

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "fig5_guardrail_validazione.png"), dpi=200,
            facecolor=PALETTE['bg'], bbox_inches='tight')
plt.close()
print("[SAVED] fig5_guardrail_validazione.png")

# ═══════════════════════════════════════════════════════════════════════════
# FIGURA 6: SLICE STRATO Z (mappa nucleazione per ogni strato)
# ═══════════════════════════════════════════════════════════════════════════

Nz = nucleation_map.shape[0]
n_rows = 2
n_cols = (Nz + 1) // 2

fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 7), facecolor=PALETTE['bg'])
fig.suptitle('Mappa Nucleazione H/D per Strato Z — Pπ(z, r, c)',
             fontsize=14, fontweight='bold', color=PALETTE['text'], y=1.02)

vmax = np.max(nucleation_map)

for iz in range(Nz):
    ax = axes[iz // n_cols, iz % n_cols]
    im = ax.imshow(nucleation_map[iz], aspect='auto', cmap='hot', origin='lower',
                   interpolation='bilinear', vmin=0, vmax=vmax)
    ax.set_title(f'Z = {iz}', fontsize=10, fontweight='bold', color=PALETTE['text'])
    ax.tick_params(colors=PALETTE['text'], labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(PALETTE['grid'])

# Nascondi assi vuoti
for idx in range(Nz, n_rows * n_cols):
    axes[idx // n_cols, idx % n_cols].set_visible(False)

# Colorbar unica
fig.subplots_adjust(right=0.92)
cbar_ax = fig.add_axes([0.94, 0.15, 0.015, 0.7])
cbar = fig.colorbar(im, cax=cbar_ax)
cbar.set_label('Pπ nucleazione', fontsize=10, color=PALETTE['text'])
cbar.ax.tick_params(colors=PALETTE['text'], labelsize=9)

plt.tight_layout(rect=[0, 0, 0.92, 0.98])
plt.savefig(os.path.join(output_dir, "fig6_slice_nucleazione.png"), dpi=200,
            facecolor=PALETTE['bg'], bbox_inches='tight')
plt.close()
print("[SAVED] fig6_slice_nucleazione.png")

# ═══════════════════════════════════════════════════════════════════════════
# RIEPILOGO
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("  VISUALIZZAZIONI GENERATE")
print("="*60)
print(f"  fig1_timeline_metriche.png    — Timeline 6 metriche chiave")
print(f"  fig2_energetico_firma.png      — Eπ e firma strutturale")
print(f"  fig3_heatmap_nucleazione.png   — Proiezioni 3D mappa nucleazione")
print(f"  fig4_firma_strutturale.png     — Radar + bar firma strutturale")
print(f"  fig5_guardrail_validazione.png — Guardrail normalizzati")
print(f"  fig6_slice_nucleazione.png     — Slice per strato Z")
print("="*60)
