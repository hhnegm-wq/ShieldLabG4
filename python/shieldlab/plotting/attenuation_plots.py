from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _auto_log_axes(ax: plt.Axes, x_values, y_values=None, x_threshold: float = 50.0, y_threshold: float = 100.0) -> None:
    """Switch to log scale when numeric spans cover large dynamic ranges."""
    x_series = pd.Series(x_values).dropna()
    if not x_series.empty and (x_series > 0).all():
        x_span = float(x_series.max()) / float(x_series.min())
        if x_span >= x_threshold:
            ax.set_xscale("log")

    if y_values is not None:
        y_series = pd.Series(y_values).dropna()
        if not y_series.empty and (y_series > 0).all():
            y_span = float(y_series.max()) / float(y_series.min())
            if y_span >= y_threshold:
                ax.set_yscale("log")


def _save_bar_chart(values: dict[str, float], output_path: Path, title: str, ylabel: str) -> Path:
    labels = list(values.keys())
    heights = [values[label] for label in labels]

    fig, ax = plt.subplots(figsize=(6.5, 4.0), constrained_layout=True)
    ax.bar(labels, heights, color=["#2f6f9f", "#9f6b2f", "#5f8f45"][: len(labels)])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, max(1.0, max(heights) * 1.15 if heights else 1.0))
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
    return output_path


def _save_layer_edep(layers: pd.DataFrame, output_path: Path) -> Path | None:
    if layers.empty:
        return None
    fig, ax = plt.subplots(figsize=(7.0, 4.0), constrained_layout=True)
    labels = [f"{row.layer}: {row.material}" for row in layers.itertuples()]
    ax.bar(labels, layers["edep_MeV_per_event"], color="#4f7f61")
    ax.set_title("Layer Energy Deposition")
    ax.set_ylabel("MeV per event")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
    return output_path


def _save_sweep_line_plot(sweep: pd.DataFrame, y_column: str, output_path: Path, title: str, ylabel: str) -> Path:
    fig, ax = plt.subplots(figsize=(7.0, 4.2), constrained_layout=True)
    ax.plot(sweep["energy"], sweep[y_column], marker="o", color="#2f6f9f", linewidth=1.8)
    _auto_log_axes(ax, sweep["energy"], sweep[y_column])
    energy_unit = sweep["energy_unit"].iloc[0] if "energy_unit" in sweep else ""
    ax.set_title(title)
    ax.set_xlabel(f"Energy ({energy_unit})" if energy_unit else "Energy")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3)
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
    return output_path


def _save_reference_overlay(comparison: pd.DataFrame, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(7.0, 4.2), constrained_layout=True)
    ax.plot(
        comparison["energy"],
        comparison["mass_attenuation_cm2_g_simulated"],
        marker="o",
        color="#2f6f9f",
        linewidth=1.8,
        label="ShieldLab-G4",
    )
    ax.plot(
        comparison["energy"],
        comparison["mass_attenuation_cm2_g_reference"],
        marker="s",
        color="#9f6b2f",
        linewidth=1.6,
        label="Reference",
    )
    _auto_log_axes(
        ax,
        comparison["energy"],
        pd.concat(
            [
                comparison["mass_attenuation_cm2_g_simulated"],
                comparison["mass_attenuation_cm2_g_reference"],
            ],
            ignore_index=True,
        ),
    )
    energy_unit = comparison["energy_unit"].iloc[0] if "energy_unit" in comparison else ""
    ax.set_title("Mass Attenuation Reference Comparison")
    ax.set_xlabel(f"Energy ({energy_unit})" if energy_unit else "Energy")
    ax.set_ylabel("Mass attenuation (cm²/g)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
    return output_path


def _save_percent_difference(comparison: pd.DataFrame, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(7.0, 4.2), constrained_layout=True)
    ax.axhline(0.0, color="#333333", linewidth=0.9)
    ax.plot(
        comparison["energy"],
        comparison["mass_attenuation_cm2_g_percent_difference"],
        marker="o",
        color="#4f7f61",
        linewidth=1.8,
    )
    _auto_log_axes(ax, comparison["energy"], None)
    energy_unit = comparison["energy_unit"].iloc[0] if "energy_unit" in comparison else ""
    ax.set_title("Mass Attenuation Percent Difference")
    ax.set_xlabel(f"Energy ({energy_unit})" if energy_unit else "Energy")
    ax.set_ylabel("Difference from reference (%)")
    ax.grid(alpha=0.3)
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
    return output_path


def _save_thickness_sweep_plots(thickness_sweep: pd.DataFrame, figure_dir: Path) -> list[Path]:
    outputs = []

    fig, ax = plt.subplots(figsize=(7.0, 4.2), constrained_layout=True)
    ax.plot(thickness_sweep["thickness_cm"], thickness_sweep["transmission_fraction"],
            marker="o", color="#2f6f9f", linewidth=1.8)
    ax.set_title("Transmission vs Thickness")
    ax.set_xlabel("Thickness (cm)")
    ax.set_ylabel("Transmission fraction")
    ax.set_yscale("log")
    ax.grid(alpha=0.3)
    p = figure_dir / "transmission_vs_thickness.png"
    fig.savefig(p, dpi=220)
    plt.close(fig)
    outputs.append(p)

    fig, ax = plt.subplots(figsize=(7.0, 4.2), constrained_layout=True)
    ax.plot(thickness_sweep["thickness_cm"], thickness_sweep["linear_attenuation_cm_inv"],
            marker="o", color="#9f6b2f", linewidth=1.8)
    ax.set_title("Linear Attenuation vs Thickness (consistency check)")
    ax.set_xlabel("Thickness (cm)")
    ax.set_ylabel("Linear attenuation (cm\u207b\u00b9)")
    ax.grid(alpha=0.3)
    p = figure_dir / "linear_attenuation_vs_thickness.png"
    fig.savefig(p, dpi=220)
    plt.close(fig)
    outputs.append(p)

    fig, ax = plt.subplots(figsize=(7.0, 4.2), constrained_layout=True)
    ax.plot(thickness_sweep["thickness_cm"], thickness_sweep["hvl_cm"],
            marker="o", color="#4f7f61", linewidth=1.8)
    ax.set_title("Half-Value Layer vs Thickness (consistency check)")
    ax.set_xlabel("Thickness (cm)")
    ax.set_ylabel("HVL (cm)")
    ax.grid(alpha=0.3)
    p = figure_dir / "hvl_vs_thickness.png"
    fig.savefig(p, dpi=220)
    plt.close(fig)
    outputs.append(p)

    return outputs


def _save_composition_sweep_plots(comp_sweep: pd.DataFrame, figure_dir: Path) -> list[Path]:
    outputs = []
    compound = comp_sweep["compound"].iloc[0] if "compound" in comp_sweep else "compound"
    x = comp_sweep["compound_fraction"]
    xlabel = f"{compound} weight fraction"

    for y_col, fname, title, ylabel, color in [
        ("mass_attenuation_cm2_g",    "mass_attenuation_vs_composition.png",
         "Mass Attenuation vs Composition",     "Mass attenuation (cm\u00b2/g)",        "#2f6f9f"),
        ("linear_attenuation_cm_inv", "linear_attenuation_vs_composition.png",
         "Linear Attenuation vs Composition",   "Linear attenuation (cm\u207b\u00b9)",   "#9f6b2f"),
        ("hvl_cm",                    "hvl_vs_composition.png",
         "Half-Value Layer vs Composition",     "HVL (cm)",                             "#4f7f61"),
        ("transmission_fraction",     "transmission_vs_composition.png",
         "Transmission vs Composition",         "Transmission fraction",                "#7f4f9f"),
    ]:
        if y_col not in comp_sweep:
            continue
        fig, ax = plt.subplots(figsize=(7.0, 4.2), constrained_layout=True)
        ax.plot(x, comp_sweep[y_col], marker="o", color=color, linewidth=1.8)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
        p = figure_dir / fname
        fig.savefig(p, dpi=220)
        plt.close(fig)
        outputs.append(p)

    return outputs


def create_standard_plots(result_dir: str | Path) -> list[Path]:
    result_path = Path(result_dir)
    figure_dir = result_path / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    # Thickness sweep plots
    thickness_path = result_path / "thickness_sweep_summary.csv"
    if thickness_path.exists():
        thickness_sweep = pd.read_csv(thickness_path)
        if not thickness_sweep.empty:
            return _save_thickness_sweep_plots(thickness_sweep, figure_dir)

    # Composition sweep plots
    comp_path = result_path / "composition_sweep_summary.csv"
    if comp_path.exists():
        comp_sweep = pd.read_csv(comp_path)
        if not comp_sweep.empty:
            return _save_composition_sweep_plots(comp_sweep, figure_dir)

    sweep_path = result_path / "sweep_summary.csv"
    if sweep_path.exists():
        sweep = pd.read_csv(sweep_path)
        outputs = [
            _save_sweep_line_plot(
                sweep,
                "linear_attenuation_cm_inv",
                figure_dir / "linear_attenuation_vs_energy.png",
                "Linear Attenuation vs Energy",
                "Linear attenuation (cm⁻¹)",
            ),
            _save_sweep_line_plot(
                sweep,
                "mass_attenuation_cm2_g",
                figure_dir / "mass_attenuation_vs_energy.png",
                "Mass Attenuation vs Energy",
                "Mass attenuation (cm²/g)",
            ),
            _save_sweep_line_plot(
                sweep,
                "transmission_fraction",
                figure_dir / "transmission_vs_energy.png",
                "Transmission vs Energy",
                "Transmission fraction",
            ),
            _save_sweep_line_plot(
                sweep,
                "hvl_cm",
                figure_dir / "hvl_vs_energy.png",
                "Half-Value Layer vs Energy",
                "HVL (cm)",
            ),
        ]
        comparison_path = result_path / "reference_comparison.csv"
        if comparison_path.exists():
            comparison = pd.read_csv(comparison_path)
            if not comparison.empty and "mass_attenuation_cm2_g_reference" in comparison:
                outputs.extend(
                    [
                        _save_reference_overlay(comparison, figure_dir / "mass_attenuation_reference_overlay.png"),
                        _save_percent_difference(comparison, figure_dir / "mass_attenuation_percent_difference.png"),
                    ]
                )
        return outputs

    summary_path = result_path / "run_summary.csv"
    layers_path = result_path / "layer_energy_deposition.csv"
    if not summary_path.exists():
        return []

    summary = pd.read_csv(summary_path)
    layers = pd.read_csv(layers_path) if layers_path.exists() else pd.DataFrame()
    row = summary.iloc[0]

    outputs = [
        _save_bar_chart(
            {
                "Transmission": float(row["transmission_fraction"]),
                "Reflection": float(row["reflection_fraction"]),
                "Absorption": float(row["absorption_fraction"]),
            },
            figure_dir / "shield_response.png",
            "Shield Response Fractions",
            "Fraction",
        )
    ]

    layer_plot = _save_layer_edep(layers, figure_dir / "layer_energy_deposition.png")
    if layer_plot is not None:
        outputs.append(layer_plot)
    return outputs