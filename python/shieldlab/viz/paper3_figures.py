from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

BLUE = "#0000FF"
RED = "#FF0000"
GREEN = "#00FF00"
BLACK = "#000000"

SCIENTIFIC_RC: dict = {
    "axes.edgecolor": "black",
    "axes.linewidth": 1.5,
    "axes.spines.top": True,
    "axes.spines.right": True,
    "axes.spines.left": True,
    "axes.spines.bottom": True,
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "axes.grid": False,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "xtick.major.size": 6,
    "ytick.major.size": 6,
    "xtick.major.width": 1.2,
    "ytick.major.width": 1.2,
    "xtick.minor.size": 3,
    "ytick.minor.size": 3,
    "xtick.minor.visible": False,
    "ytick.minor.visible": False,
    "text.color": "black",
    "axes.labelcolor": "black",
    "xtick.color": "black",
    "ytick.color": "black",
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "legend.frameon": True,
    "legend.framealpha": 0.90,
    "legend.edgecolor": "black",
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "patch.linewidth": 0.5,
}


def _apply_scientific_style() -> None:
    plt.rcParams.update(SCIENTIFIC_RC)


def style_axis(ax) -> None:
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor("black")
        spine.set_linewidth(1.5)
    ax.tick_params(
        axis="both",
        which="major",
        direction="in",
        top=True,
        right=True,
        length=6,
        width=1.2,
        colors="black",
        pad=4,
    )


def _save_figure(fig: plt.Figure, output_path: Path) -> None:
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")


def _load_csv(result_dir: Path, name: str) -> pd.DataFrame:
    path = result_dir / name
    if not path.exists():
        raise FileNotFoundError(f"Missing Paper 3 artifact: {path}")
    return pd.read_csv(path)


def _load_mac_series(result_dir: Path) -> pd.DataFrame:
    comp_path = result_dir / "reference_comparison.csv"
    if comp_path.exists():
        comp = pd.read_csv(comp_path)
        return pd.DataFrame(
            {
                "energy": comp["energy"],
                "mass_attenuation_simulated": comp["mass_attenuation_cm2_g_simulated"],
                "mass_attenuation_std": comp.get(
                    "mass_attenuation_std_cm2_g_simulated",
                    pd.Series(np.zeros(len(comp))),
                ),
                "mass_attenuation_reference": comp["mass_attenuation_cm2_g_reference"],
            }
        )

    sweep_path = result_dir / "sweep_summary.csv"
    if sweep_path.exists():
        sweep = pd.read_csv(sweep_path)
        data = {
            "energy": sweep["energy"],
            "mass_attenuation_simulated": sweep["mass_attenuation_cm2_g"],
            "mass_attenuation_std": sweep.get(
                "mass_attenuation_std_cm2_g",
                pd.Series(np.zeros(len(sweep))),
            ),
        }
        if "mass_attenuation_cm2_g_reference" in sweep.columns:
            data["mass_attenuation_reference"] = sweep["mass_attenuation_cm2_g_reference"]
        return pd.DataFrame(data)

    raise FileNotFoundError(f"Missing MAC summary for Paper 3 artifact: {result_dir}")


def _errorbar_series(ax, x, y, y_std, *, color: str, marker: str, label: str) -> None:
    yerr = None
    if y_std is not None:
        yerr = 1.96 * np.asarray(y_std, dtype=float)
    ax.errorbar(
        x,
        y,
        yerr=yerr,
        fmt=f"{marker}-",
        color=color,
        linewidth=1.6,
        markersize=5,
        capsize=3,
        capthick=1.0,
        elinewidth=1.0,
        label=label,
        zorder=4,
    )


def generate_regime_overview_diagram(output_dir: str | Path) -> dict[str, Path]:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    _apply_scientific_style()
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    ax.set_axis_off()

    def add_box(x: float, y: float, w: float, h: float, title: str, body: str, color: str) -> None:
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            linewidth=1.5,
            edgecolor=BLACK,
            facecolor="white",
            transform=ax.transAxes,
        )
        ax.add_patch(patch)
        ax.text(
            x + 0.02,
            y + h - 0.07,
            title,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=12,
            fontweight="bold",
            color=color,
        )
        ax.text(
            x + 0.02,
            y + h - 0.14,
            body,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            color=BLACK,
            linespacing=1.35,
        )

    add_box(
        0.03,
        0.50,
        0.28,
        0.36,
        "Regime A — Effective medium",
        "Single homogeneous `G4Material`\nBulk attenuation default\nO(1) in particle count\nRecommended for macroscopic shielding",
        BLUE,
    )
    add_box(
        0.36,
        0.50,
        0.28,
        0.36,
        "Regime B — Explicit RVE",
        "25 nm spheres via `G4PVParameterised`\n1 µm RVE, N = 2,888\nExplicit validation geometry\nScalable enough for dense RVEs",
        RED,
    )
    add_box(
        0.69,
        0.50,
        0.28,
        0.36,
        "Regime C — Explicit union",
        "25 nm spheres via `G4MultiUnion`\n250 nm RVE, N = 45\nUseful for small-cluster checks\nLimited by voxelizer scaling",
        GREEN,
    )
    add_box(
        0.14,
        0.10,
        0.72,
        0.20,
        "Recommended workflow",
        "Use regime A for production attenuation studies; use regime B to validate explicit microstructure at matched composition; use regime C only as a small-RVE stress test because `G4Voxelizer` becomes impractical for N ≳ 50 on 8 GB hardware.",
        BLACK,
    )

    for x in (0.17, 0.50, 0.83):
        arrow = FancyArrowPatch(
            (x, 0.50),
            (0.50, 0.30),
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=1.2,
            color=BLACK,
            transform=ax.transAxes,
        )
        ax.add_patch(arrow)

    png_path = out_path / "paper3_fig1_regime_map.png"
    pdf_path = out_path / "paper3_fig1_regime_map.pdf"
    _save_figure(fig, png_path)
    _save_figure(fig, pdf_path)
    plt.close(fig)
    return {"figure_1_png": png_path, "figure_1_pdf": pdf_path}


def generate_regime_a_validation_figure(result_dir: str | Path, output_dir: str | Path) -> dict[str, Path]:
    result_path = Path(result_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    _apply_scientific_style()
    comparison = _load_csv(result_path, "reference_comparison.csv")

    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    _errorbar_series(
        ax,
        comparison["energy"],
        comparison["mass_attenuation_cm2_g_simulated"],
        comparison["mass_attenuation_std_cm2_g_simulated"],
        color=BLUE,
        marker="o",
        label="Regime A (30 wt%)",
    )
    ax.plot(
        comparison["energy"],
        comparison["mass_attenuation_cm2_g_reference"],
        linestyle="--",
        linewidth=1.4,
        color=BLACK,
        label="NIST XCOM",
        zorder=3,
    )
    ax.set_xscale("log")
    ax.set_xlabel("Photon energy (keV)")
    ax.set_ylabel(r"Mass attenuation coefficient (cm$^2$ g$^{-1}$)")
    ax.legend(loc="upper right", fancybox=False, edgecolor="black", framealpha=0.90, fontsize=9)
    style_axis(ax)

    png_path = out_path / "paper3_fig2_regime_a_validation.png"
    pdf_path = out_path / "paper3_fig2_regime_a_validation.pdf"
    _save_figure(fig, png_path)
    _save_figure(fig, pdf_path)
    plt.close(fig)
    return {"figure_2_png": png_path, "figure_2_pdf": pdf_path}


def generate_buildup_and_spectrum_figure(result_dir: str | Path, output_dir: str | Path) -> dict[str, Path]:
    result_path = Path(result_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    _apply_scientific_style()
    buildup = _load_csv(result_path, "buildup_observable_summary.csv")
    spectrum = _load_csv(result_path, "downstream_spectrum_summary.csv")

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(10.2, 4.2))

    ax_left.plot(
        buildup["energy"],
        buildup["mc_buildup_observable_count"],
        marker="o",
        linewidth=1.6,
        color=BLUE,
        label="Count buildup",
    )
    ax_left.plot(
        buildup["energy"],
        buildup["mc_buildup_observable_energy"],
        marker="s",
        linewidth=1.6,
        color=RED,
        label="Energy buildup",
    )
    ax_left.axhline(1.0, color=BLACK, linestyle="--", linewidth=1.2, alpha=0.7)
    ax_left.set_xscale("log")
    ax_left.set_xlabel("Photon energy (keV)")
    ax_left.set_ylabel("Monte Carlo buildup observable")
    ax_left.legend(loc="upper right", fancybox=False, edgecolor="black", framealpha=0.90, fontsize=9)
    style_axis(ax_left)

    gamma_spectrum = spectrum[
        (spectrum["channel"] == "total_gamma")
        & (spectrum["particle_name"] == "gamma")
        & (spectrum["count"] > 0)
    ].copy()
    selected_energies = [100.0, 662.0, 1332.0]
    colors = [BLUE, RED, GREEN]
    for color, energy in zip(colors, selected_energies):
        subset = gamma_spectrum[gamma_spectrum["incident_energy"] == energy].copy()
        if subset.empty:
            continue
        subset["energy_mid_MeV"] = (subset["energy_low_MeV"] * subset["energy_high_MeV"]) ** 0.5
        ax_right.step(
            subset["energy_mid_MeV"],
            subset["count"],
            where="mid",
            linewidth=1.5,
            color=color,
            label=f"{energy:g} keV incident",
        )
    ax_right.set_xscale("log")
    ax_right.set_yscale("log")
    ax_right.set_xlabel("Downstream gamma energy (MeV)")
    ax_right.set_ylabel("Counts per bin")
    ax_right.legend(loc="upper right", fancybox=False, edgecolor="black", framealpha=0.90, fontsize=9)
    style_axis(ax_right)

    for ax, label in zip((ax_left, ax_right), ("A", "B")):
        ax.text(0.97, 0.97, f"({label})", transform=ax.transAxes, ha="right", va="top", fontsize=13, fontweight="bold", color=BLACK)

    png_path = out_path / "paper3_fig3_buildup_and_spectrum.png"
    pdf_path = out_path / "paper3_fig3_buildup_and_spectrum.pdf"
    _save_figure(fig, png_path)
    _save_figure(fig, pdf_path)
    plt.close(fig)
    return {"figure_3_png": png_path, "figure_3_pdf": pdf_path}


def generate_multiunion_scalability_figure(output_dir: str | Path) -> dict[str, Path]:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    _apply_scientific_style()
    rve_labels = ["250 nm\nN=45", "500 nm\nN=361", "1 µm\nN=2888"]
    voxel_cells = np.array([729000.0, 376000000.0, 193000000000.0])
    rss_mb = np.array([99.0, 3500.0, 7200.0])
    status = ["Success", "OOM", "OOM"]
    colors = [GREEN, RED, BLACK]
    x = np.arange(len(rve_labels))

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(9.8, 4.2))

    bars_left = ax_left.bar(x, voxel_cells, color=colors, edgecolor=BLACK, linewidth=0.8)
    ax_left.set_yscale("log")
    ax_left.set_xticks(x)
    ax_left.set_xticklabels(rve_labels)
    ax_left.set_ylabel("Estimated voxel cells")
    style_axis(ax_left)

    bars_right = ax_right.bar(x, rss_mb, color=colors, edgecolor=BLACK, linewidth=0.8)
    ax_right.set_yscale("log")
    ax_right.set_xticks(x)
    ax_right.set_xticklabels(rve_labels)
    ax_right.set_ylabel("Observed resident set size (MB)")
    style_axis(ax_right)

    for bar, label in zip(bars_left, status):
        ax_left.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.2, label, ha="center", va="bottom", fontsize=9, color=BLACK)
    for bar, label in zip(bars_right, status):
        prefix = ">" if label == "OOM" and bar.get_height() >= 7200 else ""
        ax_right.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.2, f"{prefix}{label}", ha="center", va="bottom", fontsize=9, color=BLACK)

    for ax, label in zip((ax_left, ax_right), ("A", "B")):
        ax.text(0.97, 0.97, f"({label})", transform=ax.transAxes, ha="right", va="top", fontsize=13, fontweight="bold", color=BLACK)

    png_path = out_path / "paper3_fig4_multiunion_scalability.png"
    pdf_path = out_path / "paper3_fig4_multiunion_scalability.pdf"
    _save_figure(fig, png_path)
    _save_figure(fig, pdf_path)
    plt.close(fig)
    return {"figure_4_png": png_path, "figure_4_pdf": pdf_path}


def generate_regime_a_figures(result_dir: str | Path) -> dict[str, Path]:
    result_path = Path(result_dir)
    figures_dir = result_path / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    sweep = _load_csv(result_path, "sweep_summary.csv")
    comparison = _load_csv(result_path, "reference_comparison.csv")
    spectrum_summary_path = result_path / "downstream_spectrum_summary.csv"
    spectrum_summary = pd.read_csv(spectrum_summary_path) if spectrum_summary_path.exists() else pd.DataFrame()

    _apply_scientific_style()

    mac_figure = figures_dir / "paper3_f3_regime_a_mac_vs_xcom.png"
    mac_pdf = figures_dir / "paper3_f3_regime_a_mac_vs_xcom.pdf"
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.plot(
        comparison["energy"],
        comparison["mass_attenuation_cm2_g_simulated"],
        marker="o",
        linewidth=1.8,
        color=BLUE,
        label="Geant4 regime A",
    )
    ax.plot(
        comparison["energy"],
        comparison["mass_attenuation_cm2_g_reference"],
        linewidth=1.5,
        linestyle="--",
        color=BLACK,
        label="NIST XCOM",
    )
    ax.set_xscale("log")
    ax.set_xlabel("Photon energy (keV)")
    ax.set_ylabel(r"Mass attenuation coefficient (cm$^2$ g$^{-1}$)")
    ax.legend(loc="upper right", fancybox=False, edgecolor="black", framealpha=0.90, fontsize=9)
    style_axis(ax)
    _save_figure(fig, mac_figure)
    _save_figure(fig, mac_pdf)
    plt.close(fig)

    transmission_figure = figures_dir / "paper3_regime_a_transmission.png"
    transmission_pdf = figures_dir / "paper3_regime_a_transmission.pdf"
    fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(6.4, 5.6), sharex=True, height_ratios=[2.2, 1.0])
    ax_top.plot(
        sweep["energy"],
        sweep["transmission_fraction"],
        marker="o",
        linewidth=1.8,
        color=BLUE,
    )
    ax_top.fill_between(
        sweep["energy"],
        sweep["transmission_fraction"] - sweep["transmission_fraction_ci95_half_width"],
        sweep["transmission_fraction"] + sweep["transmission_fraction_ci95_half_width"],
        color=GREEN,
        alpha=0.15,
    )
    ax_top.set_xscale("log")
    ax_top.set_ylabel("Transmission fraction")
    style_axis(ax_top)

    ax_bottom.axhline(0.0, color=BLACK, linewidth=1.2, linestyle="--", alpha=0.7)
    ax_bottom.plot(
        comparison["energy"],
        comparison["mass_attenuation_cm2_g_percent_difference"],
        marker="o",
        linewidth=1.6,
        color=RED,
    )
    ax_bottom.set_xscale("log")
    ax_bottom.set_xlabel("Photon energy (keV)")
    ax_bottom.set_ylabel("Delta MAC (%)")
    style_axis(ax_bottom)
    _save_figure(fig, transmission_figure)
    _save_figure(fig, transmission_pdf)
    plt.close(fig)

    outputs = {
        "figure_f3_png": mac_figure,
        "figure_f3_pdf": mac_pdf,
        "figure_transmission_png": transmission_figure,
        "figure_transmission_pdf": transmission_pdf,
    }

    if not spectrum_summary.empty:
        gamma_spectrum = spectrum_summary[
            (spectrum_summary["channel"] == "total_gamma")
            & (spectrum_summary["particle_name"] == "gamma")
            & (spectrum_summary["count"] > 0)
        ].copy()
        if not gamma_spectrum.empty:
            selected_energies = [100.0, 662.0, 1332.0]
            available = sorted(gamma_spectrum["incident_energy"].unique())
            chosen = [energy for energy in selected_energies if energy in available]
            if not chosen:
                chosen = available[: min(3, len(available))]

            spectrum_figure = figures_dir / "paper3_downstream_gamma_spectrum.png"
            spectrum_pdf = figures_dir / "paper3_downstream_gamma_spectrum.pdf"
            fig, ax = plt.subplots(figsize=(6.4, 4.4))
            colors = [BLUE, RED, GREEN]
            for color, energy in zip(colors, chosen):
                subset = gamma_spectrum[gamma_spectrum["incident_energy"] == energy].copy()
                subset["energy_mid_MeV"] = (subset["energy_low_MeV"] * subset["energy_high_MeV"]) ** 0.5
                ax.step(
                    subset["energy_mid_MeV"],
                    subset["count"],
                    where="mid",
                    linewidth=1.6,
                    color=color,
                    label=f"{energy:g} keV incident",
                )
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlabel("Downstream gamma energy (MeV)")
            ax.set_ylabel("Counts per log-energy bin")
            ax.legend(loc="upper right", fancybox=False, edgecolor="black", framealpha=0.90, fontsize=9)
            style_axis(ax)
            _save_figure(fig, spectrum_figure)
            _save_figure(fig, spectrum_pdf)
            plt.close(fig)
            outputs["figure_spectrum_png"] = spectrum_figure
            outputs["figure_spectrum_pdf"] = spectrum_pdf

    return outputs


def generate_regime_comparison_figure(
    regime_a_dir: str | Path,
    regime_b_dir: str | Path | None = None,
    regime_c_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Path]:
    """Overlay MAC vs XCOM for regimes A, B, C on a single figure (Paper 3 F-cross).

    Regimes B and C are optional — pass None to skip if not yet available.
    Output goes to ``output_dir`` (defaults to ``regime_a_dir/figures/``).
    """
    regime_a_path = Path(regime_a_dir)
    out_path = Path(output_dir) if output_dir else regime_a_path / "figures"
    out_path.mkdir(parents=True, exist_ok=True)

    _apply_scientific_style()

    fig, ax = plt.subplots(figsize=(6.4, 4.4))

    _regime_specs = [
        (regime_a_path, "Regime A (eff. med.)", "o", BLUE),
        (Path(regime_b_dir) if regime_b_dir else None, "Regime B (G4PVParam.)", "^", RED),
        (Path(regime_c_dir) if regime_c_dir else None, "Regime C (G4MultiUnion)", "s", GREEN),
    ]

    xcom_reference = None
    xcom_reference_energy = None
    for rdir, label, marker, color in _regime_specs:
        if rdir is None:
            continue
        comp = _load_mac_series(rdir)
        _errorbar_series(
            ax,
            comp["energy"],
            comp["mass_attenuation_simulated"],
            comp["mass_attenuation_std"],
            color=color,
            marker=marker,
            label=label,
        )
        if xcom_reference is None and "mass_attenuation_reference" in comp.columns:
            xcom_reference = comp["mass_attenuation_reference"]
            xcom_reference_energy = comp["energy"]

    if xcom_reference is not None and xcom_reference_energy is not None:
            ax.plot(
                xcom_reference_energy,
                xcom_reference,
                linewidth=1.4,
                linestyle="--",
                color=BLACK,
                label="NIST XCOM",
                zorder=3,
            )

    ax.set_xscale("log")
    ax.set_xlabel("Photon energy (keV)")
    ax.set_ylabel(r"Mass attenuation coefficient (cm$^2$ g$^{-1}$)")
    ax.legend(loc="upper right", fancybox=False, edgecolor="black",
              framealpha=0.90, fontsize=9)
    style_axis(ax)

    png_path = out_path / "paper3_cross_regime_mac.png"
    pdf_path = out_path / "paper3_cross_regime_mac.pdf"
    _save_figure(fig, png_path)
    _save_figure(fig, pdf_path)

    numbered_png = out_path / "paper3_fig5_cross_regime_mac.png"
    numbered_pdf = out_path / "paper3_fig5_cross_regime_mac.pdf"
    _save_figure(fig, numbered_png)
    _save_figure(fig, numbered_pdf)
    plt.close(fig)

    return {
        "cross_regime_mac_png": png_path,
        "cross_regime_mac_pdf": pdf_path,
        "figure_5_png": numbered_png,
        "figure_5_pdf": numbered_pdf,
    }


def generate_dual_validation_figure(
    bi2o3_result_dir: str | Path,
    wo3_result_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Two-panel Figure 2: (A) Bi₂O₃ and (B) WO₃ Regime A XCOM validation with K-edge annotations."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    _apply_scientific_style()

    bi2o3_path = Path(bi2o3_result_dir)
    wo3_path = Path(wo3_result_dir)

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(10.4, 4.4))

    # ── Panel A: Bi₂O₃ 30 wt% ──────────────────────────────────────────────
    bi2o3_cmp = _load_csv(bi2o3_path, "reference_comparison.csv")
    _errorbar_series(
        ax_a,
        bi2o3_cmp["energy"],
        bi2o3_cmp["mass_attenuation_cm2_g_simulated"],
        bi2o3_cmp["mass_attenuation_std_cm2_g_simulated"],
        color=BLUE,
        marker="o",
        label=r"Geant4 (Bi$_2$O$_3$, 30 wt%)",
    )
    ax_a.plot(
        bi2o3_cmp["energy"],
        bi2o3_cmp["mass_attenuation_cm2_g_reference"],
        linestyle="--",
        linewidth=1.4,
        color=BLACK,
        label="NIST XCOM",
        zorder=3,
    )
    ax_a.axvline(90.5, color=RED, linestyle=":", linewidth=1.3, alpha=0.85, zorder=2)
    trans_a = ax_a.get_xaxis_transform()
    ax_a.text(93, 0.72, "Bi K-edge\n90.5 keV", transform=trans_a,
              ha="left", va="top", fontsize=7.5, color=RED)
    ax_a.set_xscale("log")
    ax_a.set_yscale("log")
    ax_a.set_xlabel("Photon energy (keV)")
    ax_a.set_ylabel(r"$\mu/\rho$ (cm$^2$ g$^{-1}$)")
    ax_a.legend(loc="upper right", fancybox=False, edgecolor="black", framealpha=0.90, fontsize=8)
    style_axis(ax_a)
    ax_a.text(0.04, 0.04, "(A)", transform=ax_a.transAxes, ha="left", va="bottom",
              fontsize=13, fontweight="bold", color=BLACK)

    # ── Panel B: WO₃ φ=0.189 ───────────────────────────────────────────────
    wo3_cmp = _load_csv(wo3_path, "reference_comparison.csv")
    _errorbar_series(
        ax_b,
        wo3_cmp["energy"],
        wo3_cmp["mass_attenuation_cm2_g_simulated"],
        wo3_cmp["mass_attenuation_std_cm2_g_simulated"],
        color=RED,
        marker="s",
        label=r"Geant4 (WO$_3$, $\phi$=0.189)",
    )
    ax_b.plot(
        wo3_cmp["energy"],
        wo3_cmp["mass_attenuation_cm2_g_reference"],
        linestyle="--",
        linewidth=1.4,
        color=BLACK,
        label="NIST XCOM",
        zorder=3,
    )
    ax_b.axvline(69.525, color=BLUE, linestyle=":", linewidth=1.3, alpha=0.85, zorder=2)
    trans_b = ax_b.get_xaxis_transform()
    ax_b.text(72, 0.72, "W K-edge\n69.5 keV", transform=trans_b,
              ha="left", va="top", fontsize=7.5, color=BLUE)
    ax_b.set_xscale("log")
    ax_b.set_yscale("log")
    ax_b.set_xlabel("Photon energy (keV)")
    ax_b.set_ylabel(r"$\mu/\rho$ (cm$^2$ g$^{-1}$)")
    ax_b.legend(loc="upper right", fancybox=False, edgecolor="black", framealpha=0.90, fontsize=8)
    style_axis(ax_b)
    ax_b.text(0.04, 0.04, "(B)", transform=ax_b.transAxes, ha="left", va="bottom",
              fontsize=13, fontweight="bold", color=BLACK)

    png_path = out_path / "paper3_fig2_dual_validation.png"
    pdf_path = out_path / "paper3_fig2_dual_validation.pdf"
    _save_figure(fig, png_path)
    _save_figure(fig, pdf_path)
    plt.close(fig)
    return {"figure_2_png": png_path, "figure_2_pdf": pdf_path}


def generate_kedge_comparison_figure(
    bi2o3_companion_dir: str | Path,
    wo3_result_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Figure 6: Cross-material K-edge MAC comparison overlay (Bi₂O₃ vs WO₃ at φ=0.189)."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    _apply_scientific_style()

    bi2o3_path = Path(bi2o3_companion_dir)
    wo3_path = Path(wo3_result_dir)

    fig, ax = plt.subplots(figsize=(6.4, 4.8))

    # Bi₂O₃ φ=0.189 simulation and XCOM
    bi_cmp = _load_mac_series(bi2o3_path)
    _errorbar_series(ax, bi_cmp["energy"], bi_cmp["mass_attenuation_simulated"],
                     bi_cmp["mass_attenuation_std"],
                     color=BLUE, marker="o", label=r"Bi$_2$O$_3$, $\phi$=0.189 (Geant4)")
    if "mass_attenuation_reference" in bi_cmp.columns:
        ax.plot(bi_cmp["energy"], bi_cmp["mass_attenuation_reference"],
                linestyle="--", linewidth=1.3, color=BLUE, alpha=0.55,
                label=r"Bi$_2$O$_3$ XCOM", zorder=3)

    # WO₃ φ=0.189 simulation and XCOM
    wo3_cmp = _load_mac_series(wo3_path)
    _errorbar_series(ax, wo3_cmp["energy"], wo3_cmp["mass_attenuation_simulated"],
                     wo3_cmp["mass_attenuation_std"],
                     color=RED, marker="s", label=r"WO$_3$, $\phi$=0.189 (Geant4)")
    if "mass_attenuation_reference" in wo3_cmp.columns:
        ax.plot(wo3_cmp["energy"], wo3_cmp["mass_attenuation_reference"],
                linestyle="--", linewidth=1.3, color=RED, alpha=0.55,
                label=r"WO$_3$ XCOM", zorder=3)

    # K-edge annotations
    trans = ax.get_xaxis_transform()
    ax.axvline(69.525, color=RED, linestyle=":", linewidth=1.3, alpha=0.8, zorder=2)
    ax.text(72, 0.78, "W K-edge\n69.5 keV", transform=trans,
            ha="left", va="top", fontsize=8, color=RED)
    ax.axvline(90.5, color=BLUE, linestyle=":", linewidth=1.3, alpha=0.8, zorder=2)
    ax.text(93, 0.60, "Bi K-edge\n90.5 keV", transform=trans,
            ha="left", va="top", fontsize=8, color=BLUE)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Photon energy (keV)")
    ax.set_ylabel(r"$\mu/\rho$ (cm$^2$ g$^{-1}$)")
    ax.legend(loc="upper right", fancybox=False, edgecolor="black", framealpha=0.90, fontsize=8,
              ncol=2)
    style_axis(ax)

    png_path = out_path / "paper3_fig6_kedge_comparison.png"
    pdf_path = out_path / "paper3_fig6_kedge_comparison.pdf"
    _save_figure(fig, png_path)
    _save_figure(fig, pdf_path)
    plt.close(fig)
    return {"figure_6_png": png_path, "figure_6_pdf": pdf_path}


def generate_paper3_figure_suite(
    regime_a_validation_dir: str | Path,
    regime_a_companion_dir: str | Path,
    regime_b_dir: str | Path,
    regime_c_dir: str | Path,
    output_dir: str | Path,
    wo3_result_dir: str | Path | None = None,
) -> dict[str, Path]:
    outputs: dict[str, Path] = {}
    outputs.update(generate_regime_overview_diagram(output_dir))
    if wo3_result_dir is not None:
        outputs.update(generate_dual_validation_figure(regime_a_validation_dir, wo3_result_dir, output_dir))
    else:
        outputs.update(generate_regime_a_validation_figure(regime_a_validation_dir, output_dir))
    outputs.update(generate_buildup_and_spectrum_figure(regime_a_validation_dir, output_dir))
    outputs.update(generate_multiunion_scalability_figure(output_dir))
    outputs.update(
        generate_regime_comparison_figure(
            regime_a_companion_dir,
            regime_b_dir,
            regime_c_dir,
            output_dir,
        )
    )
    if wo3_result_dir is not None:
        outputs.update(generate_kedge_comparison_figure(regime_a_companion_dir, wo3_result_dir, output_dir))
    return outputs


__all__ = [
    "generate_regime_a_figures",
    "generate_regime_overview_diagram",
    "generate_regime_a_validation_figure",
    "generate_dual_validation_figure",
    "generate_kedge_comparison_figure",
    "generate_buildup_and_spectrum_figure",
    "generate_multiunion_scalability_figure",
    "generate_regime_comparison_figure",
    "generate_paper3_figure_suite",
]