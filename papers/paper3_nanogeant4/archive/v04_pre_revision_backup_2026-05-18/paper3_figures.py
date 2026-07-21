from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from shieldlab.viz.style import apply_journal_style, finish_shieldlab_figure


def _load_csv(result_dir: Path, name: str) -> pd.DataFrame:
    path = result_dir / name
    if not path.exists():
        raise FileNotFoundError(f"Missing Paper 3 artifact: {path}")
    return pd.read_csv(path)


def generate_regime_a_figures(result_dir: str | Path) -> dict[str, Path]:
    result_path = Path(result_dir)
    figures_dir = result_path / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    sweep = _load_csv(result_path, "sweep_summary.csv")
    comparison = _load_csv(result_path, "reference_comparison.csv")
    spectrum_summary_path = result_path / "downstream_spectrum_summary.csv"
    spectrum_summary = pd.read_csv(spectrum_summary_path) if spectrum_summary_path.exists() else pd.DataFrame()

    apply_journal_style("publication_strict")

    mac_figure = figures_dir / "paper3_f3_regime_a_mac_vs_xcom.png"
    mac_pdf = figures_dir / "paper3_f3_regime_a_mac_vs_xcom.pdf"
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.plot(
        comparison["energy"],
        comparison["mass_attenuation_cm2_g_simulated"],
        marker="o",
        linewidth=1.8,
        label="Geant4 regime A",
    )
    ax.plot(
        comparison["energy"],
        comparison["mass_attenuation_cm2_g_reference"],
        marker="s",
        linewidth=1.5,
        linestyle="--",
        label="NIST XCOM",
    )
    ax.set_xscale("log")
    ax.set_xlabel("Photon energy (keV)")
    ax.set_ylabel("Mass attenuation coefficient (cm$^2$/g)")
    ax.set_title("Paper 3 F3: Regime-A mass attenuation vs XCOM")
    ax.legend(frameon=True)
    ax.grid(True, which="both", alpha=0.25)
    finish_shieldlab_figure(fig)
    fig.savefig(mac_figure)
    fig.savefig(mac_pdf)
    plt.close(fig)

    transmission_figure = figures_dir / "paper3_regime_a_transmission.png"
    transmission_pdf = figures_dir / "paper3_regime_a_transmission.pdf"
    fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(6.4, 5.6), sharex=True, height_ratios=[2.2, 1.0])
    ax_top.plot(
        sweep["energy"],
        sweep["transmission_fraction"],
        marker="o",
        linewidth=1.8,
        color="#0f766e",
    )
    ax_top.fill_between(
        sweep["energy"],
        sweep["transmission_fraction"] - sweep["transmission_fraction_ci95_half_width"],
        sweep["transmission_fraction"] + sweep["transmission_fraction_ci95_half_width"],
        color="#99f6e4",
        alpha=0.35,
    )
    ax_top.set_xscale("log")
    ax_top.set_ylabel("Transmission fraction")
    ax_top.set_title("Paper 3 regime-A baseline transmission")
    ax_top.grid(True, which="both", alpha=0.25)

    ax_bottom.axhline(0.0, color="#111827", linewidth=1.0, linestyle=":")
    ax_bottom.plot(
        comparison["energy"],
        comparison["mass_attenuation_cm2_g_percent_difference"],
        marker="o",
        linewidth=1.6,
        color="#b45309",
    )
    ax_bottom.set_xscale("log")
    ax_bottom.set_xlabel("Photon energy (keV)")
    ax_bottom.set_ylabel("Delta MAC (%)")
    ax_bottom.grid(True, which="both", alpha=0.25)
    finish_shieldlab_figure(fig)
    fig.savefig(transmission_figure)
    fig.savefig(transmission_pdf)
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
            for energy in chosen:
                subset = gamma_spectrum[gamma_spectrum["incident_energy"] == energy].copy()
                subset["energy_mid_MeV"] = (subset["energy_low_MeV"] * subset["energy_high_MeV"]) ** 0.5
                ax.step(
                    subset["energy_mid_MeV"],
                    subset["count"],
                    where="mid",
                    linewidth=1.6,
                    label=f"{energy:g} keV incident",
                )
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlabel("Downstream gamma energy (MeV)")
            ax.set_ylabel("Counts per log-energy bin")
            ax.set_title("Paper 3 downstream gamma spectrum")
            ax.legend(frameon=True)
            ax.grid(True, which="both", alpha=0.25)
            finish_shieldlab_figure(fig)
            fig.savefig(spectrum_figure)
            fig.savefig(spectrum_pdf)
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

    # ── Style Guide compliant RC (all 4 spines, inward ticks, no grid, white bg) ──
    _GUIDE_RC = {
        "axes.edgecolor": "black", "axes.linewidth": 1.5,
        "axes.spines.top": True, "axes.spines.right": True,
        "axes.spines.left": True, "axes.spines.bottom": True,
        "axes.facecolor": "white", "figure.facecolor": "white",
        "axes.grid": False,
        "xtick.direction": "in", "ytick.direction": "in",
        "xtick.top": True, "ytick.right": True,
        "xtick.major.size": 6, "ytick.major.size": 6,
        "xtick.major.width": 1.2, "ytick.major.width": 1.2,
        "text.color": "black", "axes.labelcolor": "black",
        "xtick.color": "black", "ytick.color": "black",
        "font.family": "DejaVu Sans", "font.size": 11,
        "axes.labelsize": 11, "axes.titlesize": 12,
        "legend.frameon": True, "legend.framealpha": 0.90,
        "legend.edgecolor": "black", "legend.fontsize": 9,
        "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    }
    plt.rcParams.update(_GUIDE_RC)

    # ── Colors: BLUE=A, RED=XCOM dashed, GREEN=B, BLACK-solid=C ──
    _REGIME_COLORS = ["#0000FF", "#009E73", "#D55E00"]  # A=blue, B=green, C=vermillion
    _XCOM_COLOR = "#000000"

    def _style_ax(a: "plt.Axes") -> None:
        for spine in a.spines.values():
            spine.set_visible(True)
            spine.set_edgecolor("black")
            spine.set_linewidth(1.5)
        a.tick_params(axis="both", which="major", direction="in",
                      top=True, right=True, length=6, width=1.2, colors="black", pad=4)

    fig, ax = plt.subplots(figsize=(6.4, 4.4))

    _regime_specs = [
        (regime_a_path, "Regime A (eff. med.)", "o", _REGIME_COLORS[0]),
        (Path(regime_b_dir) if regime_b_dir else None, "Regime B (G4PVParam.)", "^", _REGIME_COLORS[1]),
        (Path(regime_c_dir) if regime_c_dir else None, "Regime C (G4MultiUnion)", "s", _REGIME_COLORS[2]),
    ]

    xcom_plotted = False
    for rdir, label, marker, color in _regime_specs:
        if rdir is None:
            continue
        comp_path = rdir / "reference_comparison.csv"
        if not comp_path.exists():
            continue
        comp = pd.read_csv(comp_path)
        ax.plot(
            comp["energy"],
            comp["mass_attenuation_cm2_g_simulated"],
            marker=marker,
            markersize=5,
            linewidth=1.6,
            linestyle="-",
            color=color,
            label=label,
            zorder=4,
        )
        if not xcom_plotted:
            ax.plot(
                comp["energy"],
                comp["mass_attenuation_cm2_g_reference"],
                marker="",
                linewidth=1.4,
                linestyle="--",
                color=_XCOM_COLOR,
                label="NIST XCOM",
                zorder=3,
            )
            xcom_plotted = True

    ax.set_xscale("log")
    ax.set_xlabel("Photon energy (keV)")
    ax.set_ylabel(r"Mass attenuation coefficient (cm$^2$ g$^{-1}$)")
    ax.legend(loc="upper right", fancybox=False, edgecolor="black",
              framealpha=0.90, fontsize=9)
    _style_ax(ax)

    png_path = out_path / "paper3_cross_regime_mac.png"
    pdf_path = out_path / "paper3_cross_regime_mac.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)

    return {"cross_regime_mac_png": png_path, "cross_regime_mac_pdf": pdf_path}


__all__ = ["generate_regime_a_figures", "generate_regime_comparison_figure"]