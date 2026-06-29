#!/usr/bin/env python3
"""
Publication-quality benchmark figures for ShieldLab G4 validation paper.
Run from project root:
    python docs/validation/figures/generate_figures.py
"""
import sys, pathlib, csv, json, math, warnings
warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parents[3]
for p in (ROOT / "python", ROOT / "ui"):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch

FIGS = pathlib.Path(__file__).parent
FIGS.mkdir(exist_ok=True)

# ── Import ShieldLab physics ──────────────────────────────────────────────────
from shieldlab.physics.shielding_params import (
    compute_shielding_table, gp_buildup_factor, zeff_energy_dependent,
)
from shieldlab.physics.nist_xcom import get_xcom_compound, get_mac_compound
from shieldlab.physics.nist_estar import electron_stopping_power
from shieldlab.physics.ion_range import (proton_table as _proton_table,
                                          alpha_table as _alpha_table,
                                          heavy_ion_table as _heavy_ion_table)
from shieldlab.physics.shielding_params import compute_fnrcs as _compute_fnrcs

# ── Publication matplotlib style ─────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Times New Roman", "Times", "serif"],
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "legend.framealpha": 0.9,
    "axes.linewidth": 0.8,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "axes.grid": True,
    "grid.linestyle": "--",
    "grid.alpha": 0.35,
    "grid.linewidth": 0.5,
    "lines.linewidth": 1.6,
    "lines.markersize": 5.5,
    "errorbar.capsize": 3,
})

MAT_COLOR = {
    "Lead":      "#d62728",
    "Water":     "#1f77b4",
    "Concrete":  "#2ca02c",
    "Aluminium": "#9467bd",
    "Iron":      "#ff7f0e",
    "Copper":    "#8c564b",
    "Tungsten":  "#e377c2",
    "HDPE":      "#7f7f7f",
    "Bismuth":   "#17becf",
}
MAT_MARK = {
    "Lead": "o", "Water": "s", "Concrete": "^", "Aluminium": "D",
    "Iron": "v", "Copper": "P", "Tungsten": "*", "HDPE": "X", "Bismuth": "h",
}

BRAND = {
    "navy": "#0a376f",
    "primary": "#0d4ea3",
    "secondary": "#1a73d9",
    "light": "#1f86e5",
    "line": "#4c5f79",
    "text": "#1f2f46",
    "panel_a": "#eaf1fb",
    "panel_b": "#deebfb",
    "panel_c": "#eef5ff",
    "panel_d": "#f2f7ff",
}


def add_plain_title(ax_or_fig, title, subtitle=None, *, pad=8, y=None, fontsize=11):
    if hasattr(ax_or_fig, "suptitle"):
        full = title if subtitle is None else f"{title}\n{subtitle}"
        ax_or_fig.suptitle(full, y=1.01 if y is None else y, fontsize=fontsize)
    else:
        full = title if subtitle is None else f"{title}\n{subtitle}"
        ax_or_fig.set_title(full, pad=pad, fontsize=fontsize)

# ── Load validation data ──────────────────────────────────────────────────────
VAL_CSV = ROOT / "docs/validation/validation_report.csv"
val_rows = []
with open(VAL_CSV) as f:
    for r in csv.DictReader(f):
        val_rows.append({
            "mat":   r["Material"],
            "E":     float(r["E_MeV"]),
            "rho":   float(r["density"]),
            "nist":  float(r["NIST_MAC"]),
            "calc":  float(r["Calc_MAC"]),
            "err":   float(r["Rel_err_pct"]),
            "hvl":   float(r["HVL_cm"]),
            "tvl":   float(r["TVL_cm"]),
        })

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 1 — Parity plot (log-log): ShieldLab G4 vs NIST XCOM
# ─────────────────────────────────────────────────────────────────────────────
def fig1_parity():
    fig, ax = plt.subplots(figsize=(5.5, 6.4))

    all_vals = [r["nist"] for r in val_rows] + [r["calc"] for r in val_rows]
    vmin, vmax = min(all_vals) * 0.6, max(all_vals) * 1.8

    # Parity bands
    x_band = np.logspace(math.log10(vmin), math.log10(vmax), 300)
    ax.fill_between(x_band, x_band * 0.95, x_band * 1.05,
                    color="#4dac26", alpha=0.15, label="±5% envelope")
    ax.fill_between(x_band, x_band * 0.98, x_band * 1.02,
                    color="#1a9641", alpha=0.20, label="±2% envelope")
    ax.plot(x_band, x_band, "k--", lw=1.2, label="Perfect agreement")

    # Points
    for mat, color, marker in [(m, MAT_COLOR[m], MAT_MARK[m]) for m in MAT_COLOR]:
        xs = [r["nist"] for r in val_rows if r["mat"] == mat]
        ys = [r["calc"] for r in val_rows if r["mat"] == mat]
        if xs:
            ax.scatter(xs, ys, c=color, marker=marker, s=45, zorder=5,
                       label=mat, edgecolors="white", linewidths=0.4)

    # Bi@60keV annotation
    bi60 = next(r for r in val_rows if r["mat"] == "Bismuth" and r["E"] == 0.06)
    ax.annotate("Bi, 60 keV\n(L-edge region)",
                xy=(bi60["nist"], bi60["calc"]),
                xytext=(bi60["nist"] * 0.12, bi60["calc"] * 1.15),
                fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.8, color="#555"),
                color="#555")

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(vmin, vmax); ax.set_ylim(vmin, vmax)
    ax.set_xlabel(r"NIST XCOM  $\mu/\rho$  (cm$^2$ g$^{-1}$)")
    ax.set_ylabel(r"ShieldLab G4  $\mu/\rho$  (cm$^2$ g$^{-1}$)")
    add_plain_title(ax, "Parity plot: ShieldLab G4 vs. NIST XCOM",
                    "9 materials, 60 keV – 10 MeV (n = 56)", pad=8)
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, -0.14), fontsize=8, ncol=2,
              handletextpad=0.4, columnspacing=0.8)
    ax.set_aspect("equal")
    fig.subplots_adjust(bottom=0.34)
    fig.savefig(FIGS / "fig1_parity.png")
    plt.close(fig)
    print("fig1_parity.png done")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 2 — Deviation analysis: histogram + energy scatter
# ─────────────────────────────────────────────────────────────────────────────
def fig2_deviation():
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))

    errs = [r["err"] for r in val_rows]
    abs_errs = [abs(e) for e in errs]

    # Left: histogram of |Δ%|
    ax = axes[0]
    bins = [0, 0.2, 0.5, 1.0, 1.5, 2.5, 5.0, 20.0]
    counts, edges = np.histogram(abs_errs, bins=bins)
    colors_hist = ["#1a9641" if b < 0.5 else "#ffffb2" if b < 1.5 else "#fdae61" if b < 5.0 else "#d7191c"
                   for b in edges[:-1]]
    ax.bar(range(len(counts)), counts, color=colors_hist, edgecolor="k", linewidth=0.6)
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels([f"{edges[i]:.1f}–{edges[i+1]:.1f}" for i in range(len(counts))],
                       rotation=30, ha="right", fontsize=8)
    ax.set_xlabel(r"$|\Delta(\mu/\rho)|$ (%)")
    ax.set_ylabel("Count (n = 56 points)")
    ax.set_title("(a) Distribution of absolute deviation")
    for i, c in enumerate(counts):
        ax.text(i, c + 0.05, str(c), ha="center", va="bottom", fontsize=8.5)
    # legend patches
    patches = [
        Patch(facecolor="#1a9641", label="< 0.5% (excellent)"),
        Patch(facecolor="#ffffb2", label="0.5–1.5% (acceptable)"),
        Patch(facecolor="#fdae61", label="1.5–5% (moderate)"),
        Patch(facecolor="#d7191c", label="> 5% (edge region)"),
    ]
    ax.legend(handles=patches, fontsize=7.5, loc="upper right")

    # Right: scatter of signed Δ% vs energy, colored by material
    ax = axes[1]
    for mat, color, marker in [(m, MAT_COLOR[m], MAT_MARK[m]) for m in MAT_COLOR]:
        pts = [(r["E"], r["err"]) for r in val_rows if r["mat"] == mat]
        if pts:
            Es, ds = zip(*pts)
            ax.scatter(Es, ds, c=color, marker=marker, s=40, zorder=5,
                       label=mat, edgecolors="white", linewidths=0.4)
    ax.axhline(0, color="k", lw=1.0, ls="-")
    ax.axhline(1.5,  color="#fdae61", lw=1.0, ls="--", alpha=0.85)
    ax.axhline(-1.5, color="#fdae61", lw=1.0, ls="--", alpha=0.85)
    ax.axhline(0.5,  color="#2ca02c", lw=0.8, ls=":", alpha=0.8)
    ax.axhline(-0.5, color="#2ca02c", lw=0.8, ls=":", alpha=0.8)
    ax.set_xscale("log")
    ax.set_xlim(0.04, 12)
    ax.set_xlabel("Photon energy (MeV)")
    ax.set_ylabel(r"$\Delta(\mu/\rho)$ = (Calc $-$ NIST) / NIST × 100 (%)")
    ax.set_title("(b) Signed deviation vs. photon energy")
    ax.legend(loc="upper right", fontsize=7.5, ncol=2,
              handletextpad=0.4, columnspacing=0.6)
    # annotation for Bi edge
    bi60 = next(r for r in val_rows if r["mat"] == "Bismuth" and r["E"] == 0.06)
    ax.annotate("Bi L-edge\n region", xy=(bi60["E"], bi60["err"]),
                xytext=(0.2, bi60["err"] * 0.7), fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    add_plain_title(fig, "Deviation of ShieldLab G4 from NIST XCOM reference values")
    fig.tight_layout()
    fig.savefig(FIGS / "fig2_deviation.png")
    plt.close(fig)
    print("fig2_deviation.png done")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 3 — MAC vs energy curves (log-log) with NIST reference points
# ─────────────────────────────────────────────────────────────────────────────
def fig3_mac_curves():
    # Materials: Lead, Water, Ordinary Concrete, Iron
    materials = {
        "Lead":     ({"Pb": 1.0},                          11.35),
        "Water":    ({"H": 0.1119, "O": 0.8881},           1.00),
        "Concrete": ({"H":0.0221,"C":0.0020,"O":0.6574,"Na":0.0015,"Mg":0.0019,
                      "Al":0.0189,"Si":0.3040,"K":0.0100,"Ca":0.0296,"Fe":0.0041}, 2.35),
        "Iron":     ({"Fe": 1.0},                           7.87),
    }
    E_curve = np.concatenate([
        np.linspace(0.01, 0.099, 30),
        np.linspace(0.10, 0.99, 40),
        np.linspace(1.00, 10.0, 40),
    ])
    # NIST reference points subset (from validation_report.csv)
    nist_pts = {m: [(r["E"], r["nist"]) for r in val_rows if r["mat"] == m]
                for m in materials}

    fig, axes = plt.subplots(2, 2, figsize=(10, 7.5), sharex=False)
    panel_labels = ["(a)", "(b)", "(c)", "(d)"]

    for idx, (mat, (mf, rho)) in enumerate(materials.items()):
        ax = axes[idx // 2][idx % 2]
        # Compute ShieldLab G4 curve
        try:
            df = compute_shielding_table(mf, rho, E_curve)
            mac_col = [c for c in df.columns if "μ/ρ" in c or "mac" in c.lower() or "/ρ" in c][0]
            mac_vals = df[mac_col].values
            ax.plot(E_curve, mac_vals, color=MAT_COLOR[mat], lw=1.8,
                    label="ShieldLab G4")
        except Exception as e:
            print(f"  curve error {mat}: {e}")

        # NIST reference points
        if nist_pts[mat]:
            Ex, Ey = zip(*nist_pts[mat])
            ax.scatter(Ex, Ey, c="k", marker="D", s=28, zorder=6,
                       label="NIST XCOM ref.", edgecolors="white", linewidths=0.3)

        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlim(0.01, 12)
        ax.set_xlabel("Photon energy (MeV)")
        ax.set_ylabel(r"$\mu/\rho$ (cm$^2$ g$^{-1}$)")
        ax.set_title(f"{panel_labels[idx]} {mat}  (ρ = {rho} g cm⁻³)")
        ax.legend(fontsize=8.5)
        ax.xaxis.set_minor_locator(mticker.LogLocator(subs="all"))
        ax.yaxis.set_minor_locator(mticker.LogLocator(subs="all"))

    add_plain_title(fig, "Mass attenuation coefficient $\\mu/\\rho$ vs. photon energy",
                    "ShieldLab G4 (lines) vs. NIST XCOM reference points (◆)")
    fig.tight_layout()
    fig.savefig(FIGS / "fig3_mac_curves.png")
    plt.close(fig)
    print("fig3_mac_curves.png done")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 4 — HVL and TVL vs energy for key shielding materials
# ─────────────────────────────────────────────────────────────────────────────
def fig4_hvl_tvl():
    materials = {
        "Lead":     ({"Pb": 1.0},                          11.35),
        "Iron":     ({"Fe": 1.0},                           7.87),
        "Concrete": ({"H":0.0221,"C":0.0020,"O":0.6574,"Na":0.0015,"Mg":0.0019,
                      "Al":0.0189,"Si":0.3040,"K":0.0100,"Ca":0.0296,"Fe":0.0041}, 2.35),
        "Water":    ({"H": 0.1119, "O": 0.8881},           1.00),
        "HDPE":     ({"H": 0.1437, "C": 0.8563},           0.95),
    }
    E_plot = np.concatenate([np.linspace(0.05, 0.099, 15),
                              np.linspace(0.10, 0.99, 35),
                              np.linspace(1.00, 10.00, 30)])

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    ls_map = {"Lead": "-", "Iron": "--", "Concrete": "-.", "Water": ":", "HDPE": (0,(3,1,1,1))}

    for mat, (mf, rho) in materials.items():
        try:
            df = compute_shielding_table(mf, rho, E_plot)
            hvl_col = [c for c in df.columns if "HVL" in c][0]
            tvl_col = [c for c in df.columns if "TVL" in c][0]
            hvl = df[hvl_col].values
            tvl = df[tvl_col].values
            kw = dict(color=MAT_COLOR[mat], ls=ls_map[mat], lw=1.7, label=mat)
            axes[0].plot(E_plot, hvl, **kw)
            axes[1].plot(E_plot, tvl, **kw)
        except Exception as e:
            print(f"  HVL/TVL error {mat}: {e}")

    # Standard source energy markers
    sources = [("Cs-137\n662 keV", 0.662), ("Co-60\n1.25 MeV", 1.25),
               ("Am-241\n59.5 keV", 0.0595)]
    for lbl, E in sources:
        for ax in axes:
            ax.axvline(E, color="#555", lw=0.7, ls=":", alpha=0.7)

    for ax, title, ylabel in zip(axes,
            ["(a) Half-Value Layer (HVL)", "(b) Tenth-Value Layer (TVL)"],
            ["HVL (cm)", "TVL (cm)"]):
        ax.set_xscale("log")
        ax.set_xlabel("Photon energy (MeV)")
        ax.set_ylabel(ylabel)
        ax.set_title(title, pad=6)
        ax.legend(fontsize=8.5, loc="upper left")
        ax.set_xlim(0.04, 11)

    add_plain_title(fig, "Half-value layer (HVL) and tenth-value layer (TVL) vs. photon energy",
                    "for principal shielding materials (narrow-beam geometry)")
    fig.tight_layout()
    fig.savefig(FIGS / "fig4_hvl_tvl.png")
    plt.close(fig)
    print("fig4_hvl_tvl.png done")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 5 — Literature benchmark materials: computed MAC at standard energies
# ─────────────────────────────────────────────────────────────────────────────
def fig5_benchmarks():
    # Compositions and densities from benchmark_registry.json / study configs
    benchmarks = [
        ("AT70Pb15Cd15\n(Negm 2024a)",
         {"Al":0.1025,"Si":0.0688,"Mg":0.0191,"Fe":0.0345,
          "Ca":0.0114,"O":0.3882,"Pb":0.2197,"Cd":0.1558}, 2.555,
         "10.1088/1402-4896/ad3b48"),
        ("BTC1 metallic glass\n(Negm 2025)",
         {"B":0.0324,"O":0.3874,"Te":0.5802}, 4.373,
         "10.1007/s11664-025-11830-w"),
        ("LCNS5 glass\n(Negm 2023)",
         {"Ca":0.0699,"Li":0.0271,"Ni":0.1460,"Si":0.1742,"O":0.5828}, 2.6251,
         "10.1007/s11664-023-10833-9"),
        ("Mo0.0 phosphate\n(Negm 2020)",
         {"Pb":0.3518,"P":0.1093,"Na":0.0553,"Al":0.0153,"O":0.4683}, 3.697,
         "10.1007/s10854-020-04709-5"),
        ("AT40Fe30Cu30\n(Negm 2023b)",
         {"Al":0.0699,"Si":0.0469,"Mg":0.0130,"Fe":0.1843,"Ca":0.0078,
          "O":0.3662,"Cu":0.3119}, 3.0765,
         "10.1016/j.radphyschem.2023.111398"),
        ("AT40Cd30Ni30\n(Negm 2024b)",
         {"Al":0.0699,"Si":0.0469,"Mg":0.0130,"Cd":0.1800,"Ca":0.0078,
          "O":0.3765,"Ni":0.2059}, 3.107,
         "10.1016/j.radphyschem.2024.112149"),
    ]
    # Energies to compute
    E_std = np.array([0.0595, 0.1220, 0.3560, 0.6620, 1.1732, 1.3325])
    labels_E = ["59.5 keV\n(Am-241)", "122 keV\n(Co-57)", "356 keV\n(Ba-133)",
                "662 keV\n(Cs-137)", "1173 keV\n(Co-60)", "1332 keV\n(Co-60)"]

    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    colors_E = ["#d62728","#e377c2","#9467bd","#1f77b4","#2ca02c","#ff7f0e"]

    for idx, (name, mf, rho, doi) in enumerate(benchmarks):
        ax = axes[idx // 3][idx % 3]
        try:
            df = compute_shielding_table(mf, rho, E_std)
            mac_col = [c for c in df.columns if "μ/ρ" in c or "/ρ" in c][0]
            macs = df[mac_col].values
            bars = ax.bar(range(len(E_std)), macs, color=colors_E,
                          edgecolor="k", linewidth=0.5, width=0.65)
            for bar, v in zip(bars, macs):
                ax.text(bar.get_x() + bar.get_width()/2, v * 1.03,
                        f"{v:.3f}", ha="center", va="bottom", fontsize=7.5, rotation=0)
        except Exception as e:
            print(f"  benchmark error {name}: {e}")

        ax.set_xticks(range(len(E_std)))
        ax.set_xticklabels(labels_E, fontsize=7.5)
        ax.set_ylabel(r"$\mu/\rho$ (cm$^2$ g$^{-1}$)", fontsize=9)
        short_title = name.split("\n")[0]
        ax.set_title(f"{short_title}\nρ = {rho} g cm⁻³", fontsize=9, pad=4)
        ax.set_yscale("log")

    add_plain_title(fig, "ShieldLab G4 computed $\\mu/\\rho$ at standard source energies",
                    "for six literature benchmark materials")
    fig.tight_layout()
    fig.savefig(FIGS / "fig5_benchmarks.png")
    plt.close(fig)
    print("fig5_benchmarks.png done")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 6 — Multi-particle stopping power curves (2×2: e⁻, p, α, heavy-ion)
# ─────────────────────────────────────────────────────────────────────────────
def fig6_stopping():
    fig, axes = plt.subplots(2, 2, figsize=(11, 9.5))

    ion_materials = {
        "Water":  ({"H": 0.1119, "O": 0.8881}, 1.00),
        "Lead":   ({"Pb": 1.0},                11.35),
        "Iron":   ({"Fe": 1.0},                 7.87),
        "HDPE":   ({"H": 0.1437, "C": 0.8563}, 0.95),
    }
    ls_map = {"Water": "-", "Lead": "--", "Iron": "-.", "HDPE": ":"}

    # ── (a) Electron stopping ────────────────────────────────────────────────
    ax = axes[0][0]
    E_el = np.logspace(-2, 1.5, 80)  # 0.01 to ~32 MeV
    el_materials = {
        "Water":     ({"H": 0.1119, "O": 0.8881}, 1.00),
        "Lead":      ({"Pb": 1.0},                11.35),
        "Aluminium": ({"Al": 1.0},                 2.70),
        "Iron":      ({"Fe": 1.0},                 7.87),
    }
    ls_el = {"Water": "-", "Lead": "--", "Aluminium": "-.", "Iron": ":"}
    for mat, (mf, rho) in el_materials.items():
        try:
            _sc, _sr, sp_arr = electron_stopping_power(mf, E_el)
        except Exception as e:
            print(f"  e- error {mat}: {e}")
            sp_arr = np.full_like(E_el, np.nan)
        ax.plot(E_el, sp_arr, color=MAT_COLOR[mat], ls=ls_el[mat],
                lw=1.7, label=mat)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Electron kinetic energy (MeV)")
    ax.set_ylabel(r"$S_\mathrm{tot}$ (MeV cm$^2$ g$^{-1}$)")
    ax.set_title("(a) Electron (β⁻) stopping power\n"
                 "[ICRU Report 37 / ESTAR]", pad=6)
    ax.legend(fontsize=8.5)
    ax.set_xlim(0.008, 35)

    # ── (b) Proton stopping ──────────────────────────────────────────────────
    ax = axes[0][1]
    E_p = np.logspace(-1, 2.7, 80)   # 0.1 to ~500 MeV
    for mat, (mf, rho) in ion_materials.items():
        try:
            _df = _proton_table(mf, rho, E_p)
            sp_arr = _df["S_total (MeV·cm²/g)"].values
        except Exception as e:
            print(f"  proton error {mat}: {e}")
            sp_arr = np.full_like(E_p, np.nan)
        ax.plot(E_p, sp_arr, color=MAT_COLOR[mat], ls=ls_map[mat],
                lw=1.7, label=mat)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Proton kinetic energy (MeV)")
    ax.set_ylabel(r"$S_\mathrm{tot}$ (MeV cm$^2$ g$^{-1}$)")
    ax.set_title("(b) Proton stopping power\n"
                 "[ICRU Report 49 / PSTAR]", pad=6)
    ax.legend(fontsize=8.5)
    ax.set_xlim(0.08, 600)

    # ── (c) Alpha stopping ───────────────────────────────────────────────────
    ax = axes[1][0]
    E_a = np.logspace(-1, 2.0, 80)   # 0.1 to 100 MeV
    for mat, (mf, rho) in ion_materials.items():
        try:
            _df = _alpha_table(mf, rho, E_a)
            sp_arr = _df["S_total (MeV·cm²/g)"].values
        except Exception as e:
            print(f"  alpha error {mat}: {e}")
            sp_arr = np.full_like(E_a, np.nan)
        ax.plot(E_a, sp_arr, color=MAT_COLOR[mat], ls=ls_map[mat],
                lw=1.7, label=mat)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Alpha kinetic energy (MeV)")
    ax.set_ylabel(r"$S_\mathrm{tot}$ (MeV cm$^2$ g$^{-1}$)")
    ax.set_title("(c) Alpha (α) stopping power\n"
                 "[ICRU Report 49 / ASTAR scaling]", pad=6)
    ax.legend(fontsize=8.5)
    ax.set_xlim(0.08, 110)

    # ── (d) Heavy-ion C-12 stopping ──────────────────────────────────────────
    ax = axes[1][1]
    E_hi = np.logspace(0, 3.0, 80)   # 1 to 1000 MeV (total, i.e. 83 MeV/u for C-12)
    for mat, (mf, rho) in ion_materials.items():
        try:
            _df = _heavy_ion_table(mf, rho, E_hi, ion_symbol="C")
            sp_arr = _df["S_total (MeV·cm²/g)"].values
        except Exception as e:
            print(f"  heavy-ion error {mat}: {e}")
            sp_arr = np.full_like(E_hi, np.nan)
        ax.plot(E_hi, sp_arr, color=MAT_COLOR[mat], ls=ls_map[mat],
                lw=1.7, label=mat)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("¹²C ion total kinetic energy (MeV)")
    ax.set_ylabel(r"$S_\mathrm{tot}$ (MeV cm$^2$ g$^{-1}$)")
    ax.set_title("(d) ¹²C heavy-ion stopping power\n"
                 "[Bragg–Kleeman / SRIM scaling]", pad=6)
    ax.legend(fontsize=8.5)
    ax.set_xlim(0.8, 1100)

    add_plain_title(fig, "Stopping power curves for four particle types computed by ShieldLab G4",
                    "β⁻ (ESTAR/ICRU-37), proton (PSTAR/ICRU-49), α (ASTAR), ¹²C heavy-ion (Bragg–Kleeman)")
    fig.tight_layout()
    fig.savefig(FIGS / "fig6_stopping.png")
    plt.close(fig)
    print("fig6_stopping.png done")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 7 — Capability heatmap vs. international programs
# ─────────────────────────────────────────────────────────────────────────────
def fig7_capability():
    programs = ["ShieldLab\nG4", "NIST\nXCOM", "Phy-X\nPSD", "WinXCom", "SRIM", "MCNP6", "FLUKA/\nPHITS"]
    params = [
        "γ/X MAC  (μ/ρ)",
        "HVL / TVL",
        "Buildup factor (GP)",
        "Zeff / Neff",
        "EBF / EABF",
        "FNRCS (neutron removal)",
        "Electron stopping (β⁻)",
        "Proton stopping",
        "Alpha stopping",
        "Heavy-ion stopping",
        "Compton cross-section",
        "H*(10) dose rate",
        "Geant4 MC simulation",
        "Multi-layer geometry",
        "Batch/study workflow",
        "Literature overlay",
    ]
    # 0 = no, 1 = partial/manual, 2 = full
    data = np.array([
        # SL   XCOM  PhyX  WinX  SRIM  MCNP  FLUKA
        [2,    2,    2,    2,    0,    2,    2   ],  # MAC
        [2,    0,    2,    0,    0,    2,    2   ],  # HVL/TVL
        [2,    0,    2,    0,    0,    2,    2   ],  # Buildup GP
        [2,    0,    2,    0,    0,    0,    0   ],  # Zeff/Neff
        [2,    0,    2,    0,    0,    2,    2   ],  # EBF/EABF
        [2,    0,    2,    0,    0,    2,    2   ],  # FNRCS
        [2,    0,    2,    0,    0,    2,    2   ],  # e- stopping
        [2,    0,    2,    0,    2,    2,    2   ],  # p stopping
        [2,    0,    2,    0,    2,    2,    2   ],  # alpha stopping
        [2,    0,    0,    0,    2,    2,    2   ],  # HI stopping
        [2,    2,    2,    0,    0,    2,    2   ],  # Compton
        [2,    0,    0,    0,    0,    2,    2   ],  # H*(10)
        [2,    0,    0,    0,    0,    0,    0   ],  # Geant4 MC
        [2,    0,    0,    0,    0,    2,    2   ],  # Multi-layer
        [2,    0,    0,    0,    0,    2,    2   ],  # Batch workflow
        [2,    0,    0,    0,    0,    0,    0   ],  # Lit overlay
    ], dtype=float)

    cmap = LinearSegmentedColormap.from_list("cap", ["#f4f4f4", "#7fb3d5", "#123b7a"])

    fig, ax = plt.subplots(figsize=(10.2, 7.2))
    im = ax.imshow(data, cmap=cmap, vmin=0, vmax=2, aspect="auto")

    ax.set_xticks(range(len(programs)))
    ax.set_xticklabels(programs, fontsize=9)
    ax.set_yticks(range(len(params)))
    ax.set_yticklabels(params, fontsize=9)
    ax.tick_params(top=False, bottom=True, labeltop=False, labelbottom=True)

    ax.set_xticks(np.arange(-0.5, len(programs), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(params), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.0, alpha=0.9)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Column shading for ShieldLab G4
    ax.add_patch(plt.Rectangle((-0.5, -0.5), 1, len(params),
                                fill=False, edgecolor="#ff7f0e", linewidth=2.5, zorder=3))

    legend_handles = [
        Patch(facecolor="#123b7a", edgecolor="k", label="Full"),
        Patch(facecolor="#7fb3d5", edgecolor="k", label="Partial"),
        Patch(facecolor="#f4f4f4", edgecolor="k", label="None"),
    ]
    fig.legend(handles=legend_handles, loc="upper center", ncol=3,
               fontsize=8.5, framealpha=0.9, bbox_to_anchor=(0.5, 0.98))
    add_plain_title(fig, "Radiation shielding parameter capability comparison",
                    "ShieldLab G4 vs. international reference programs", y=1.03, fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGS / "fig7_capability.png")
    plt.close(fig)
    print("fig7_capability.png done")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 8 — Partial interaction cross-section decomposition (2×2 panels)
# ─────────────────────────────────────────────────────────────────────────────
def fig8_partial_xsec():
    """
    µ/ρ (total) vs. µ_en/ρ (energy-absorption) for 4 material categories.
    The gap between the curves represents the Compton-scattered photon contribution.
    Uses NIST XrayMassCoef element tables (no CGI dependency).
    """
    panels = [
        ("Lead  (high-Z, Z = 82)",
         {"Pb": 1.0},
         "#d62728"),
        ("HDPE  (low-Z polymer)",
         {"H": 0.1437, "C": 0.8563},
         "#7f7f7f"),
        ("BaSO₄ / Barite  (intermediate Z)",
         {"Ba": 0.5877, "S": 0.1374, "O": 0.2749},
         "#9467bd"),
        ("Ordinary Concrete  (complex mixture)",
         {"H":0.0221,"C":0.0020,"O":0.6574,"Na":0.0015,"Mg":0.0019,
          "Al":0.0189,"Si":0.3040,"K":0.0100,"Ca":0.0296,"Fe":0.0041},
         "#2ca02c"),
    ]
    E_arr = np.concatenate([
        np.logspace(-2, np.log10(0.099), 35),
        np.logspace(np.log10(0.10), np.log10(0.99), 40),
        np.logspace(0.0, 1.0, 30),
    ])

    # Dominant-regime boundary energies (approximate, material-independent for this plot)
    E_pe_compton = 0.10   # MeV
    E_compton_pair = 2.0  # MeV

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for idx, (title, mf, _col) in enumerate(panels):
        ax = axes[idx // 2][idx % 2]
        try:
            mac, mac_en = get_mac_compound(mf, E_arr)
            # Scatter contribution = µ/ρ - µ_en/ρ  (photon energy carried away)
            scatter = mac - mac_en

            ax.plot(E_arr, mac,    color="#000000", ls="-",  lw=1.8,
                    label=r"Total  $\mu/\rho$")
            ax.plot(E_arr, mac_en, color="#d62728", ls="--", lw=1.6,
                    label=r"Energy-absorption  $\mu_\mathrm{en}/\rho$")
            ax.fill_between(E_arr, mac_en, mac, color="#1f77b4", alpha=0.18,
                            label=r"Scatter component  $(\mu - \mu_\mathrm{en})/\rho$")

            # Energy-transfer fraction inset curve on twin axis
            ax2 = ax.twinx()
            frac = np.clip(mac_en / mac, 0, 1)
            ax2.plot(E_arr, frac, color="#2ca02c", ls=":", lw=1.3, alpha=0.8)
            ax2.set_ylim(0, 1.1)
            ax2.set_ylabel(r"$\mu_\mathrm{en}/\mu$ (energy fraction)", fontsize=8,
                           color="#2ca02c")
            ax2.tick_params(labelcolor="#2ca02c", labelsize=7)
            # Add invisible proxy for legend
            ax.plot([], [], color="#2ca02c", ls=":", lw=1.3,
                    label=r"$\mu_\mathrm{en}/\mu$ (right axis)")
        except Exception as e:
            print(f"  fig8 error {title}: {e}")

        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlim(0.008, 12)
        ax.set_xlabel("Photon energy (MeV)")
        ax.set_ylabel(r"$\mu/\rho$ or $\mu_\mathrm{en}/\rho$  (cm$^2$ g$^{-1}$)")
        ax.set_title(title, pad=5, fontsize=10)
        ax.legend(fontsize=7.8, loc="upper right", framealpha=0.88)
        ax.xaxis.set_minor_locator(mticker.LogLocator(subs="all", numticks=15))
        ax.yaxis.set_minor_locator(mticker.LogLocator(subs="all", numticks=15))

        # Dominant regime shading
        ylo, yhi = 1e-4, 5e3
        ax.axvspan(0.008,        E_pe_compton,  alpha=0.06, color="#e31a1c", zorder=0)
        ax.axvspan(E_pe_compton, E_compton_pair,alpha=0.06, color="#1f78b4", zorder=0)
        ax.axvspan(E_compton_pair, 12,           alpha=0.06, color="#ff7f00", zorder=0)
        ax.text(0.022, ylo * 12,  "Photo-\nelectric", fontsize=7, color="#c00",  ha="center", va="bottom")
        ax.text(0.50,  ylo * 12,  "Compton\nplateau",  fontsize=7, color="#1f78b4", ha="center", va="bottom")
        ax.text(5.0,   ylo * 12,  "Pair\nprod.",        fontsize=7, color="#d84e00", ha="center", va="bottom")

    add_plain_title(fig,
        "Photon mass attenuation (μ/ρ) vs. energy-absorption (μ_en/ρ) coefficients",
        "NIST XrayMassCoef — four material categories; shaded gap = Compton scatter contribution",
        fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGS / "fig8_partial_xsec.png")
    plt.close(fig)
    print("fig8_partial_xsec.png done")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 9 — G-P Exposure Buildup Factor (EBF) vs. penetration depth
# ─────────────────────────────────────────────────────────────────────────────
def fig9_buildup():
    """ANS-6.4.3 GP buildup factor curves vs. mean free paths for 4 materials."""
    gp_mats = ["Water", "Concrete", "Iron", "Lead"]
    energies = [0.2, 0.662, 1.25, 3.0]
    e_colors = ["#9467bd", "#1f77b4", "#2ca02c", "#d62728"]
    e_labels  = ["0.2 MeV", "0.662 MeV\n(Cs-137)", "1.25 MeV\n(Co-60)", "3.0 MeV"]
    t_arr = np.linspace(0, 20, 200)

    fig, axes = plt.subplots(2, 2, figsize=(10, 7.5), sharey=False)
    mat_colors = [MAT_COLOR["Water"], MAT_COLOR["Concrete"], MAT_COLOR["Iron"], MAT_COLOR["Lead"]]

    for idx, (mat, mc) in enumerate(zip(gp_mats, mat_colors)):
        ax = axes[idx // 2][idx % 2]
        for E, ec, el in zip(energies, e_colors, e_labels):
            B_arr = np.array([gp_buildup_factor(E, t, material=mat) for t in t_arr])
            ax.plot(t_arr, B_arr, color=ec, lw=1.7, label=el)
        ax.axhline(1.0, color="k", lw=0.8, ls="--", alpha=0.5, label="Narrow beam (B=1)")
        ax.set_xlim(0, 20)
        ax.set_xlabel("Penetration depth $\\mu x$ (mean free paths)")
        ax.set_ylabel("Exposure buildup factor $B(E, \\mu x)$")
        ax.set_title(f"({chr(97+idx)}) {mat}", pad=5)
        ax.legend(fontsize=8, loc="upper left")

    add_plain_title(fig, "G-P Exposure Buildup Factor (ANS-6.4.3) vs. penetration depth",
                    "ShieldLab G4 computed at 0.2, 0.662, 1.25, and 3.0 MeV for four shielding materials",
                    fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGS / "fig9_buildup.png")
    plt.close(fig)
    print("fig9_buildup.png done")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 10 — Energy-dependent Zeff for standard and novel materials
# ─────────────────────────────────────────────────────────────────────────────
def fig10_zeff():
    """Z_eff(E) curves for standard + novel shielding materials."""
    materials = {
        # Standard
        "Lead":     ({"Pb": 1.0},                          "-",  MAT_COLOR["Lead"]),
        "Iron":     ({"Fe": 1.0},                          "--", MAT_COLOR["Iron"]),
        "Concrete": ({"H":0.0221,"C":0.0020,"O":0.6574,"Na":0.0015,"Mg":0.0019,
                      "Al":0.0189,"Si":0.3040,"K":0.0100,"Ca":0.0296,"Fe":0.0041},
                     "-.", MAT_COLOR["Concrete"]),
        "Water":    ({"H": 0.1119, "O": 0.8881},          ":",  MAT_COLOR["Water"]),
        "HDPE":     ({"H": 0.1437, "C": 0.8563},          (0,(3,1,1,1)), MAT_COLOR["HDPE"]),
        # Novel glasses
        "BTC1 glass": ({"B":0.0324,"O":0.3874,"Te":0.5802},
                       "-",  "#17becf"),
        "AT70Pb15Cd15": ({"Al":0.1025,"Si":0.0688,"Mg":0.0191,"Fe":0.0345,
                           "Ca":0.0114,"O":0.3882,"Pb":0.2197,"Cd":0.1558},
                          "--", "#bcbd22"),
        "LCNS5 glass":  ({"Ca":0.0699,"Li":0.0271,"Ni":0.1460,"Si":0.1742,"O":0.5828},
                          "-.",  "#e377c2"),
        # New: Barite concrete
        "Barite concrete": ({"H":0.0031,"O":0.3119,"Mg":0.0013,"Al":0.0040,"Si":0.0166,
                              "S":0.1123,"Ca":0.0538,"Fe":0.0474,"Ba":0.4496},
                             ":",  "#8c564b"),
    }
    E_arr = np.logspace(np.log10(0.03), np.log10(8.0), 120)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for name, (mf, ls, col) in materials.items():
        try:
            zeff = zeff_energy_dependent(mf, E_arr)
            ax.plot(E_arr, zeff, color=col, ls=ls, lw=1.7, label=name)
        except Exception as e:
            print(f"  fig10 error {name}: {e}")

    # Regime boundaries
    ax.axvline(0.1, color="#aaa", lw=0.8, ls=":", alpha=0.7)
    ax.axvline(2.0, color="#aaa", lw=0.8, ls=":", alpha=0.7)
    _y_label = 1.5   # safe fixed y in data coords (just above 1 = hydrogen Z_eff floor)
    ax.text(0.045, _y_label, "PE\ndom.",          fontsize=7.5, color="#888", ha="center", va="bottom")
    ax.text(0.45,  _y_label, "Compton\nplateau",  fontsize=7.5, color="#888", ha="center", va="bottom")
    ax.text(3.5,   _y_label, "Pair\nprod.",        fontsize=7.5, color="#888", ha="center", va="bottom")

    ax.set_xscale("log")
    ax.set_xlabel("Photon energy (MeV)")
    ax.set_ylabel(r"Effective atomic number $Z_\mathrm{eff}(E)$")
    ax.set_xlim(0.025, 9)
    ax.legend(fontsize=8.5, ncol=2, loc="upper right", framealpha=0.9,
              handletextpad=0.4, columnspacing=0.8)
    add_plain_title(ax, "Energy-dependent effective atomic number $Z_{\\rm eff}(E)$",
                    "Standard shielding materials and novel glasses — ShieldLab G4", pad=8)
    fig.tight_layout()
    fig.savefig(FIGS / "fig10_zeff.png")
    plt.close(fig)
    print("fig10_zeff.png done")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 11 — Novel vs. standard shielding: HVL comparison (volumetric & mass)
# ─────────────────────────────────────────────────────────────────────────────
def fig11_novel_comparison():
    """HVL and mass-normalised HVL × ρ for standard + novel + extended material set."""
    E_cs137  = 0.662   # Cs-137
    E_co60   = 1.173   # Co-60 (primary line)

    materials = [
        # name, mass_fractions, density, category
        ("Lead",            {"Pb": 1.0},                          11.35, "standard"),
        ("Tungsten",        {"W": 1.0},                           19.30, "standard"),
        ("Iron",            {"Fe": 1.0},                           7.87, "standard"),
        ("Copper",          {"Cu": 1.0},                           8.96, "standard"),
        ("Ordinary\nConcrete",
         {"H":0.0221,"C":0.0020,"O":0.6574,"Na":0.0015,"Mg":0.0019,
          "Al":0.0189,"Si":0.3040,"K":0.0100,"Ca":0.0296,"Fe":0.0041}, 2.35, "standard"),
        ("Barite\nConcrete",
         {"H":0.0031,"O":0.3119,"Mg":0.0013,"Al":0.0040,"Si":0.0166,
          "S":0.1123,"Ca":0.0538,"Fe":0.0474,"Ba":0.4496},           3.35, "extended"),
        ("Borosilicate\nGlass",
         {"H":0.0036,"B":0.0400,"O":0.5395,"Na":0.0281,"Al":0.0177,
          "Si":0.3771,"K":0.0033,"Ca":0.0013,"Fe":0.0094},           2.23, "extended"),
        ("Paraffin\nWax",   {"H": 0.1479, "C": 0.8521},            0.93, "extended"),
        ("Borated\nHDPE",   {"H": 0.1365, "C": 0.8135, "B": 0.0320, "C": 0.8115},
                                                                     0.98, "extended"),
        ("BTC1 Glass",
         {"B":0.0324,"O":0.3874,"Te":0.5802},                      4.373, "novel"),
                ("AT70Pb15Cd15",
         {"Al":0.1025,"Si":0.0688,"Mg":0.0191,"Fe":0.0345,
          "Ca":0.0114,"O":0.3882,"Pb":0.2197,"Cd":0.1558},          2.555, "novel"),
                ("AT40Cd30Ni30",
         {"Al":0.0699,"Si":0.0469,"Mg":0.0130,"Cd":0.1800,"Ca":0.0078,
          "O":0.3765,"Ni":0.2059},                                   3.107, "novel"),
                ("LCNS5 Glass",
         {"Ca":0.0699,"Li":0.0271,"Ni":0.1460,"Si":0.1742,"O":0.5828}, 2.625, "novel"),
                ("Mo0 Phosphate",
         {"Pb":0.3518,"P":0.1093,"Na":0.0553,"Al":0.0153,"O":0.4683}, 3.697, "novel"),
    ]

    # Remove duplicate key issue for borated HDPE — use correct composition
    materials[8] = ("Borated\nHDPE",
                    {"H": 0.1365, "C": 0.8135, "B": 0.0500},
                    0.98, "extended")

    cat_color = {"standard": "#1f77b4", "extended": "#2ca02c", "novel": "#d62728"}
    E_pts = np.array([E_cs137, E_co60])

    names, hvl_cs, hvl_co, mhvl_cs, mhvl_co, cat_list = [], [], [], [], [], []
    for name, mf, rho, cat in materials:
        try:
            df = compute_shielding_table(mf, rho, E_pts)
            hcol = [c for c in df.columns if "HVL" in c][0]
            h_cs = df[hcol].iloc[0]
            h_co = df[hcol].iloc[1]
            names.append(name)
            hvl_cs.append(h_cs)
            hvl_co.append(h_co)
            mhvl_cs.append(h_cs * rho)     # g cm⁻²
            mhvl_co.append(h_co * rho)
            cat_list.append(cat)
        except Exception as e:
            print(f"  fig11 error {name}: {e}")

    x = np.arange(len(names))
    w = 0.38
    bar_colors = [cat_color[c] for c in cat_list]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Panel a: volumetric HVL (cm)
    ax = axes[0]
    b1 = ax.bar(x - w/2, hvl_cs, w, color=bar_colors, edgecolor="k", lw=0.5, alpha=0.88, label="Cs-137 (662 keV)")
    b2 = ax.bar(x + w/2, hvl_co, w, color=bar_colors, edgecolor="k", lw=0.5, alpha=0.55, hatch="//", label="Co-60 (1.17 MeV)")
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=7.5, rotation=35, ha="right")
    ax.set_ylabel("HVL (cm)")
    ax.set_title("(a) Volumetric HVL — smaller = more compact shield", pad=6)
    ax.set_yscale("log")

    # Panel b: mass-normalised HVL × ρ (g cm⁻²)
    ax = axes[1]
    ax.bar(x - w/2, mhvl_cs, w, color=bar_colors, edgecolor="k", lw=0.5, alpha=0.88, label="Cs-137 (662 keV)")
    ax.bar(x + w/2, mhvl_co, w, color=bar_colors, edgecolor="k", lw=0.5, alpha=0.55, hatch="//", label="Co-60 (1.17 MeV)")
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=7.5, rotation=35, ha="right")
    ax.set_ylabel(r"Mass-normalised HVL $\times\,\rho$ (g cm$^{-2}$)")
    ax.set_title("(b) Mass-normalised HVL — smaller = lighter shield per HVL", pad=6)
    ax.set_yscale("log")

    # Shared legend
    legend_patches = [
        Patch(color=cat_color["standard"], label="Standard shields"),
        Patch(color=cat_color["extended"], label="Extended / specialised"),
        Patch(color=cat_color["novel"],    label="Novel materials"),
        Line2D([0],[0], color="k", lw=6, alpha=0.88, label="Cs-137 (662 keV)"),
        Line2D([0],[0], color="k", lw=6, alpha=0.55, label="Co-60 (1.17 MeV)", linestyle="--"),
    ]
    fig.legend(handles=legend_patches, loc="upper center", ncol=5,
               fontsize=8, framealpha=0.9, bbox_to_anchor=(0.5, 1.02))
    add_plain_title(fig, "Shielding merit comparison: volumetric and mass-normalised HVL",
                    "Standard, extended, and novel material classes at Cs-137 and Co-60 energies",
                    y=1.06, fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGS / "fig11_novel_comparison.png")
    plt.close(fig)
    print("fig11_novel_comparison.png done")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 12 — Transmission vs. areal density at Cs-137 and Co-60
# ─────────────────────────────────────────────────────────────────────────────
def fig12_transmission():
    """I/I₀ vs. areal density (g cm⁻²) at 662 keV and 1173 keV."""
    materials = {
        "Lead":         ({"Pb": 1.0},          11.35),
        "Tungsten":     ({"W": 1.0},            19.30),
        "Iron":         ({"Fe": 1.0},            7.87),
        "Concrete":     ({"H":0.0221,"C":0.0020,"O":0.6574,"Na":0.0015,"Mg":0.0019,
                           "Al":0.0189,"Si":0.3040,"K":0.0100,"Ca":0.0296,"Fe":0.0041}, 2.35),
        "Barite\nConc.":({"H":0.0031,"O":0.3119,"Mg":0.0013,"Al":0.0040,"Si":0.0166,
                           "S":0.1123,"Ca":0.0538,"Fe":0.0474,"Ba":0.4496},  3.35),
        "BTC1 Glass":   ({"B":0.0324,"O":0.3874,"Te":0.5802},  4.373),
        "AT70Pb15Cd15": ({"Al":0.1025,"Si":0.0688,"Mg":0.0191,"Fe":0.0345,
                           "Ca":0.0114,"O":0.3882,"Pb":0.2197,"Cd":0.1558},  2.555),
        "HDPE":         ({"H": 0.1437, "C": 0.8563},  0.95),
        "Paraffin":     ({"H": 0.1479, "C": 0.8521},  0.93),
    }
    ls_map = {
        "Lead": "-", "Tungsten": "--", "Iron": "-.", "Concrete": ":",
        "Barite\nConc.": (0,(5,2)), "BTC1 Glass": "-",
        "AT70Pb15Cd15": "--", "HDPE": "-.", "Paraffin": ":"
    }
    extra_colors = {
        "Barite\nConc.": "#8c564b", "BTC1 Glass": "#17becf",
        "AT70Pb15Cd15": "#bcbd22", "Paraffin": "#ff7f0e"
    }

    energies_MeV = [0.662, 1.173]
    titles = ["(a) Cs-137  (662 keV)", "(b) Co-60  (1.173 MeV)"]
    # Areal density axis: 0 → 20 HVL-equivalent for Lead at Cs-137
    # Lead μ/ρ at 662 keV ≈ 0.111 cm²/g  → HVL_mass = ln2/0.111 ≈ 6.24 g/cm²
    max_areal = 80.0  # g cm⁻²

    areal = np.linspace(0, max_areal, 500)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    for ax, E, title in zip(axes, energies_MeV, titles):
        for name, (mf, rho) in materials.items():
            color = extra_colors.get(name, MAT_COLOR.get(name.split("\n")[0], "#555"))
            ls    = ls_map.get(name, "-")
            try:
                mac_arr, _ = get_mac_compound(mf, np.array([E]))
                mac = float(mac_arr[0])
                T   = np.exp(-mac * areal)
                ax.plot(areal, T, color=color, ls=ls, lw=1.7, label=name.replace("\n"," "))
            except Exception as e:
                print(f"  fig12 error {name}: {e}")

        ax.set_xlabel(r"Areal density $\rho\,x$ (g cm$^{-2}$)")
        ax.set_ylabel("Transmitted fraction $I / I_0$")
        ax.set_title(title, pad=6)
        ax.set_yscale("log")
        ax.set_xlim(0, max_areal)
        ax.set_ylim(1e-6, 1.1)
        ax.legend(fontsize=8, loc="lower left", ncol=2,
                  handletextpad=0.4, columnspacing=0.6, framealpha=0.9)
        # HVL markers for Lead (vertical lines at 1,2,...HVL mass thicknesses)
        mac_pb, _ = get_mac_compound({"Pb": 1.0}, np.array([E]))
        hvl_mass  = np.log(2) / float(mac_pb[0])
        for n in range(1, int(max_areal / hvl_mass) + 1):
            ax.axvline(n * hvl_mass, color="#d62728", lw=0.5, ls=":", alpha=0.4)
        ax.text(hvl_mass * 0.5, 1.5e-6, "Pb HVLs →", fontsize=7, color="#d62728", alpha=0.7)

    axes[0].set_ylabel("Transmitted fraction $I / I_0$")
    axes[1].set_ylabel("")
    add_plain_title(fig, "Narrow-beam transmission vs. areal density at Cs-137 and Co-60 energies",
                    "Standard metals, concretes, novel glasses, and hydrogenous materials",
                    fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGS / "fig12_transmission.png")
    plt.close(fig)
    print("fig12_transmission.png done")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 13 — Fast Neutron Removal Cross Section (FNRCS / σ_R)
# ─────────────────────────────────────────────────────────────────────────────
def fig13_fnrcs():
    """
    Dual-panel figure:
      (a) Bar chart of macroscopic removal cross-section σ_R (cm⁻¹) for 12
          representative shielding materials.
      (b) Corresponding HVL and TVL (cm) for fast neutron removal.
    """
    # Materials: name → (mass_fractions, density_g_cm3)
    fn_materials = [
        ("Water",                {"H": 0.1119, "O": 0.8881},                   1.000),
        ("HDPE",                 {"H": 0.1437, "C": 0.8563},                   0.950),
        ("Paraffin",             {"H": 0.1479, "C": 0.8521},                   0.900),
        ("Ordinary Concrete",    {"H":0.0221,"C":0.0020,"O":0.6574,"Na":0.0015,
                                  "Mg":0.0019,"Al":0.0189,"Si":0.3040,
                                  "K":0.0100,"Ca":0.0296,"Fe":0.0041},         2.350),
        ("Barite Concrete",      {"H":0.0069,"O":0.3116,"Mg":0.0008,"Al":0.0039,
                                  "Si":0.0100,"S":0.1041,"Ca":0.0483,
                                  "Fe":0.0484,"Ba":0.4660},                    3.350),
        ("Aluminium",            {"Al": 1.0},                                   2.700),
        ("Iron",                 {"Fe": 1.0},                                   7.870),
        ("Lead",                 {"Pb": 1.0},                                  11.350),
        ("Bismuth",              {"Bi": 1.0},                                   9.750),
        ("PE-Bi₂O₃ (50 wt%)",   {"H":0.0607,"C":0.3611,"O":0.1271,
                                  "Bi":0.4511},                                 3.400),
        ("PbWO₄",                {"Pb":0.4545,"W":0.4042,"O":0.1413},          8.280),
        ("Borated Poly (5%B)",   {"H":0.1290,"C":0.7600,"B":0.0500,
                                  "O":0.0610},                                  0.990),
    ]

    names, sig_R, hvl_vals, tvl_vals = [], [], [], []
    for name, mf, rho in fn_materials:
        try:
            sig = _compute_fnrcs(mf, rho)
            hvl = np.log(2) / sig if sig > 0 else np.nan
            tvl = np.log(10) / sig if sig > 0 else np.nan
        except Exception as e:
            print(f"  fnrcs error {name}: {e}")
            sig, hvl, tvl = np.nan, np.nan, np.nan
        names.append(name)
        sig_R.append(sig)
        hvl_vals.append(hvl)
        tvl_vals.append(tvl)

    # Sort by σ_R descending for readability
    order = sorted(range(len(sig_R)), key=lambda i: sig_R[i] if not np.isnan(sig_R[i]) else -1, reverse=True)
    names    = [names[i]    for i in order]
    sig_R    = [sig_R[i]    for i in order]
    hvl_vals = [hvl_vals[i] for i in order]
    tvl_vals = [tvl_vals[i] for i in order]

    y = np.arange(len(names))
    # color by material type
    def _bar_color(n):
        if "Water" in n or "HDPE" in n or "Poly" in n or "Paraffin" in n:
            return "#1f77b4"
        if "Concrete" in n or "Barite" in n:
            return "#2ca02c"
        if "Iron" in n:
            return "#ff7f0e"
        if "Lead" in n or "Bi" in n or "PbWO₄" in n or "PE-Bi" in n:
            return "#d62728"
        return "#9467bd"
    colors = [_bar_color(n) for n in names]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))

    # ── (a) σ_R bar chart ────────────────────────────────────────────────────
    ax = axes[0]
    bars = ax.barh(y, sig_R, color=colors, edgecolor="k", linewidth=0.5, height=0.65)
    for bar, v in zip(bars, sig_R):
        if not np.isnan(v):
            ax.text(v + 0.002, bar.get_y() + bar.get_height()/2,
                    f"{v:.4f}", va="center", fontsize=8)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel(r"Macroscopic removal cross-section  $\Sigma_R$  (cm$^{-1}$)", fontsize=10)
    ax.set_title("(a)  Fast neutron removal cross-section $\\Sigma_R$", pad=6)
    ax.invert_yaxis()
    # Legend patches
    from matplotlib.patches import Patch as _Patch
    legend_items = [
        _Patch(facecolor="#1f77b4", label="Hydrogenous (H-rich)"),
        _Patch(facecolor="#2ca02c", label="Concrete / mineral"),
        _Patch(facecolor="#ff7f0e", label="Metallic (Fe)"),
        _Patch(facecolor="#d62728", label="High-Z (Pb/Bi)"),
    ]
    ax.legend(handles=legend_items, fontsize=8, loc="lower right")

    # ── (b) HVL / TVL bar chart ───────────────────────────────────────────────
    ax = axes[1]
    w = 0.30
    ax.barh(y - w/2, hvl_vals, height=w, color="#1f77b4", edgecolor="k",
            linewidth=0.5, label="HVL (cm)")
    ax.barh(y + w/2, tvl_vals, height=w, color="#ff7f0e", edgecolor="k",
            linewidth=0.5, label="TVL (cm)")
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("Fast neutron removal HVL / TVL (cm)", fontsize=10)
    ax.set_title("(b)  HVL and TVL for fast neutron removal", pad=6)
    ax.invert_yaxis()
    ax.legend(fontsize=9)

    add_plain_title(fig, "Fast Neutron Removal Cross Section (FNRCS) analysis",
                    "Macroscopic $\\Sigma_R$ and corresponding HVL/TVL for key shielding materials",
                    fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGS / "fig13_fnrcs.png")
    plt.close(fig)
    print("fig13_fnrcs.png done")


def fig_graphical_abstract():
    fig = plt.figure(figsize=(12, 4.8), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.93,
            "ShieldLab G4 unifies analytical shielding calculations and Geant4 transport",
            ha="center", va="center", fontsize=16, fontweight="bold", color=BRAND["navy"])

    boxes = [
        (0.04, 0.20, 0.22, 0.56, "Problem",
                 ["Separate tools for shielding analysis", "Attenuation", "Buildup",
                    "Stopping power", "Neutron removal", "Monte Carlo"], BRAND["panel_a"]),
        (0.31, 0.20, 0.22, 0.56, "Platform",
         ["ShieldLab G4 v1.0.0", "Python analytical engine", "Geant4 11.4 transport",
                    "Offline workflow", "Batch studies"], BRAND["panel_b"]),
        (0.58, 0.20, 0.18, 0.56, "Physics Coverage",
         ["Mass attenuation", "HVL / TVL", "GP buildup", "Zeff", "e⁻, p, α, heavy-ion stopping", "FNRCS"],
                 BRAND["panel_c"]),
        (0.80, 0.20, 0.16, 0.56, "Validation",
         ["56 photon benchmarks", "9 materials", "60 keV to 10 MeV", "0.176% mean deviation",
                    "98.2% within ±2%", "Electron 1.5%; Proton 2.0%"], BRAND["panel_d"]),
    ]

    for x, y, w, h, heading, lines, fill in boxes:
        box = FancyBboxPatch((x, y), w, h,
                             boxstyle="round,pad=0.012,rounding_size=0.02",
                     linewidth=1.2, edgecolor=BRAND["line"], facecolor=fill)
        ax.add_patch(box)
        ax.text(x + w / 2, y + h - 0.07, heading,
            ha="center", va="center", fontsize=12, fontweight="bold", color=BRAND["navy"])
        y0 = y + h - 0.14
        for i, line in enumerate(lines):
            ax.text(x + 0.02, y0 - 0.065 * i, line,
                    ha="left", va="top", fontsize=9.2, color=BRAND["text"])

            arrow_kw = dict(arrowstyle="-|>", lw=1.8, color=BRAND["secondary"])
    ax.annotate("", xy=(0.30, 0.48), xytext=(0.26, 0.48), arrowprops=arrow_kw)
    ax.annotate("", xy=(0.57, 0.48), xytext=(0.53, 0.48), arrowprops=arrow_kw)
    ax.annotate("", xy=(0.79, 0.48), xytext=(0.76, 0.48), arrowprops=arrow_kw)

    footer = FancyBboxPatch((0.08, 0.06), 0.84, 0.08,
                            boxstyle="round,pad=0.01,rounding_size=0.015",
                            linewidth=0, facecolor=BRAND["navy"])
    ax.add_patch(footer)
    ax.text(0.5, 0.10,
            "One integrated environment for shielding design, benchmarking, and verification",
            ha="center", va="center", fontsize=12, color="white", fontweight="bold")

    fig.savefig(FIGS / "graphical_abstract.png")
    plt.close(fig)
    print("graphical_abstract.png done")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating publication figures...")
    fig1_parity()
    fig2_deviation()
    fig3_mac_curves()
    fig4_hvl_tvl()
    fig5_benchmarks()
    fig6_stopping()
    fig7_capability()
    # New figures — extended validations & material categories
    fig8_partial_xsec()
    fig9_buildup()
    fig10_zeff()
    fig11_novel_comparison()
    fig12_transmission()
    fig13_fnrcs()
    fig_graphical_abstract()
    print("All figures saved to:", FIGS)
