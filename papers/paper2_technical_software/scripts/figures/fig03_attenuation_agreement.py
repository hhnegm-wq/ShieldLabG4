"""
fig03_attenuation_agreement.py
Canonical generator for Figure 3 — ShieldLab G4 vs NIST XCOM attenuation scatter.
Output: ../../figures/fig03_attenuation_agreement.png  (300 DPI, white bg, 4-spine)

Data source: papers/paper2_technical_software/data_validation_report.csv

Run from repo root:
    python papers/paper2_technical_software/scripts/figures/fig03_attenuation_agreement.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from scipy.stats import linregress
from scipy.stats import t as _t_dist

# ── Style constants ──────────────────────────────────────────────────────────
BLUE   = "#0000FF"
RED    = "#FF0000"
GREEN  = "#00AA44"
BLACK  = "#000000"
WHITE  = "#ffffff"

SCIENTIFIC_RC = {
    'axes.edgecolor':     BLACK,  'axes.linewidth':      1.5,
    'axes.spines.top':    True,   'axes.spines.right':   True,
    'axes.spines.left':   True,   'axes.spines.bottom':  True,
    'axes.facecolor':     WHITE,  'figure.facecolor':    WHITE,
    'axes.grid':          False,
    'xtick.direction':    'in',   'ytick.direction':     'in',
    'xtick.top':          True,   'ytick.right':         True,
    'xtick.major.size':   6,      'ytick.major.size':    6,
    'xtick.major.width':  1.2,    'ytick.major.width':   1.2,
    'xtick.minor.size':   3,      'ytick.minor.size':    3,
    'xtick.minor.visible':False,  'ytick.minor.visible': False,
    'text.color':         BLACK,  'axes.labelcolor':     BLACK,
    'xtick.color':        BLACK,  'ytick.color':         BLACK,
    'font.family':        'DejaVu Sans',
    'font.size':          11,     'axes.labelsize':      11,
    'axes.titlesize':     12,     'axes.titleweight':    'bold',
    'legend.frameon':     True,   'legend.framealpha':   0.90,
    'legend.edgecolor':   BLACK,  'legend.fontsize':     9,
    'figure.dpi':         300,    'savefig.dpi':         300,
    'savefig.bbox':       'tight','patch.linewidth':     0.5,
}
plt.rcParams.update(SCIENTIFIC_RC)

HERE = Path(__file__).parent
DATA_CSV = HERE.parent.parent / "data_validation_report.csv"
OUTPUT   = HERE.parent.parent / "figures" / "fig03_attenuation_agreement.png"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# Marker map: one symbol per material
MATERIAL_STYLES = {
    "Lead":      dict(marker='o', color='#1f4e79', label='Lead (Pb)'),
    "Water":     dict(marker='s', color='#2e75b6', label='Water (H₂O)'),
    "Concrete":  dict(marker='^', color='#7f7f7f', label='Concrete'),
    "Aluminium": dict(marker='D', color='#ed7d31', label='Aluminium (Al)'),
    "Iron":      dict(marker='v', color='#c55a11', label='Iron (Fe)'),
    "Copper":    dict(marker='P', color='#833c00', label='Copper (Cu)'),
    "Tungsten":  dict(marker='*', color='#44546a', label='Tungsten (W)'),
    "HDPE":      dict(marker='h', color='#548235', label='HDPE'),
    "Bismuth":   dict(marker='X', color='#7030a0', label='Bismuth (Bi)'),
}


def style_axis(ax):
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor(BLACK)
        spine.set_linewidth(1.5)
    ax.tick_params(axis='both', which='major',
                   direction='in', top=True, right=True,
                   length=6, width=1.2, colors=BLACK, pad=4)


def regression_ci(ax, x, y, color=RED, lw=2.0, ci_alpha=0.12, n_pts=300):
    x, y = np.asarray(x, float), np.asarray(y, float)
    mask = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
    xl, yl = np.log10(x[mask]), np.log10(y[mask])
    n = len(xl)
    if n < 3:
        return
    fit = linregress(xl, yl)
    xp = np.linspace(xl.min(), xl.max(), n_pts)
    yp = fit.intercept + fit.slope * xp
    y_hat = fit.intercept + fit.slope * xl
    s2 = np.sum((yl - y_hat) ** 2) / (n - 2)
    x_mean = xl.mean()
    se = np.sqrt(s2 * (1 / n + (xp - x_mean) ** 2 / np.sum((xl - x_mean) ** 2)))
    t_crit = _t_dist.ppf(0.975, df=n - 2)
    ax.plot(10 ** xp, 10 ** yp, color=color, linewidth=lw, zorder=4,
            label=f'OLS fit (slope={fit.slope:.4f})')
    ax.fill_between(10 ** xp,
                    10 ** (yp - t_crit * se),
                    10 ** (yp + t_crit * se),
                    color=color, alpha=ci_alpha, zorder=3, linewidth=0)
    return fit


def load_data(csv_path: Path):
    import csv
    rows = []
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rows.append({
                    'material': row['Material'],
                    'energy': float(row['E_MeV']),
                    'nist':  float(row['NIST_MAC']),
                    'calc':  float(row['Calc_MAC']),
                    'rel':   float(row['Rel_err_pct']),
                })
            except (ValueError, KeyError):
                continue
    return rows


def main():
    rows = load_data(DATA_CSV)
    n = len(rows)

    nist_all = np.array([r['nist'] for r in rows])
    calc_all = np.array([r['calc'] for r in rows])
    rel_all  = np.array([r['rel']  for r in rows])

    mean_abs = np.mean(np.abs(rel_all))
    max_abs  = np.max(np.abs(rel_all))

    # ── Panel layout: main scatter (left) + residuals (right) ────────────────
    fig = plt.figure(figsize=(13.2, 6.0))
    gs = GridSpec(1, 2, width_ratios=[1.08, 1.0], wspace=0.18, figure=fig)
    ax_main = fig.add_subplot(gs[0, 0])
    ax_res = fig.add_subplot(gs[0, 1])

    # ── Panel A: scatter NIST vs Calc, log-log ─────────────────────────────
    for mat, style in MATERIAL_STYLES.items():
        xs = [r['nist'] for r in rows if r['material'] == mat]
        ys = [r['calc'] for r in rows if r['material'] == mat]
        if xs:
            ax_main.scatter(xs, ys, s=55, marker=style['marker'],
                            color=style['color'], edgecolors=WHITE,
                            linewidth=0.6, zorder=5, label=style['label'])

    # 1:1 reference line
    lo = min(nist_all.min(), calc_all.min()) * 0.7
    hi = max(nist_all.max(), calc_all.max()) * 1.5
    ax_main.plot([lo, hi], [lo, hi], color='gray', linestyle='-',
                 linewidth=1.0, alpha=0.55, zorder=2, label='1:1 line')

    # OLS + 95% CI
    fit = regression_ci(ax_main, nist_all, calc_all, color=RED)

    ax_main.set_xscale('log')
    ax_main.set_yscale('log')
    ax_main.set_xlabel('NIST XCOM  μ/ρ  (cm² g⁻¹)')
    ax_main.set_ylabel('ShieldLab G4  μ/ρ  (cm² g⁻¹)')
    ax_main.set_title('(A)  Calculated vs Reference — log scale', pad=6)

    # Stats annotation
    ax_main.text(0.03, 0.97,
                 f'n = {n}\nMean |Δ| = {mean_abs:.2f}%\nMax |Δ| = {max_abs:.2f}%\n'
                 f'Slope = {fit.slope:.4f} ± {fit.stderr:.4f}\nR² = {fit.rvalue ** 2:.5f}\np = {fit.pvalue:.2e}',
                 transform=ax_main.transAxes, va='top', ha='left',
                 fontsize=8.6, color=BLACK,
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                           edgecolor=BLACK, linewidth=0.8, alpha=0.9))

    ax_main.legend(loc='lower center', bbox_to_anchor=(0.52, 0.02), fontsize=7.2, ncol=2,
                   fancybox=False, edgecolor=BLACK, framealpha=0.92)
    style_axis(ax_main)

    # Panel label
    ax_main.text(0.97, 0.03, '(A)', transform=ax_main.transAxes,
                 ha='right', va='bottom', fontsize=12, fontweight='bold', color=BLACK)

    # ── Panel B: relative error % bar-scatter ────────────────────────────────
    idx_sorted = np.argsort(rel_all)
    x_pos = np.arange(n)

    # Colour by sign
    bar_colors = [RED if r > 0 else BLUE for r in rel_all[idx_sorted]]
    ax_res.bar(x_pos, rel_all[idx_sorted], color=bar_colors,
               edgecolor=BLACK, linewidth=0.4, alpha=0.80, zorder=3)
    ax_res.axhline(0, color=BLACK, linewidth=0.9, zorder=4)
    ax_res.axhline(mean_abs, color=RED, linestyle='--', linewidth=1.2,
                   label=f'Mean |Δ| = {mean_abs:.2f}%', zorder=5)
    ax_res.axhline(-mean_abs, color=RED, linestyle='--', linewidth=1.2, zorder=5)

    ax_res.set_xlabel(f'Data point (sorted by residual, n={n})')
    ax_res.set_ylabel('Relative deviation  Δ  (%)')
    ax_res.set_title('(B)  Relative deviation from NIST XCOM', pad=6)
    ax_res.set_xlim(-0.5, n - 0.5)

    ax_res.legend(loc='upper left', fancybox=False, edgecolor=BLACK, framealpha=0.9)

    # ±2% guide lines
    for lim, lbl in [(2.0, '±2%'), (-2.0, None)]:
        ax_res.axhline(lim, color='#404040', linestyle=':', linewidth=0.9,
                       alpha=0.6, zorder=2)
    ax_res.text(n - 0.5, 2.1, '±2%', ha='right', va='bottom',
                fontsize=7.5, color='#404040', alpha=0.8)

    worst = max(rows, key=lambda row: abs(row['rel']))
    worst_index = int(np.where(idx_sorted == rows.index(worst))[0][0])
    ax_res.annotate(
        f"Bi, {worst['energy']:.2f} MeV\nK-edge outlier",
        xy=(worst_index, worst['rel']),
        xytext=(worst_index - 7, worst['rel'] - 3.0),
        fontsize=7.8,
        ha='right',
        va='top',
        arrowprops=dict(arrowstyle='->', lw=0.9, color=BLACK),
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=BLACK, linewidth=0.7),
    )

    ax_res.text(0.97, 0.03, '(B)', transform=ax_res.transAxes,
                ha='right', va='bottom', fontsize=12, fontweight='bold', color=BLACK)

    style_axis(ax_res)

    fig.tight_layout(pad=1.4)
    fig.savefig(str(OUTPUT), dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"Saved: {OUTPUT}  (n={n}, mean|Δ|={mean_abs:.3f}%, max|Δ|={max_abs:.3f}%)")


if __name__ == "__main__":
    main()
