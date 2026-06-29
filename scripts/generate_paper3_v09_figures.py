from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import gridspec
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "paper3"
OUT_DIR = RESULTS / "figures" / "v09"


@dataclass(frozen=True)
class MaterialSpec:
    key: str
    label: str
    short_label: str
    a_dir: str
    b_dir: str
    c_dir: str
    density: float
    color: str
    marker: str
    k_edges: tuple[tuple[float, str], ...]
    h1_equivalent: bool = True


MATERIALS: tuple[MaterialSpec, ...] = (
    MaterialSpec(
        key="bi2o3",
        label=r"HDPE/Bi$_2$O$_3$",
        short_label=r"Bi$_2$O$_3$",
        a_dir="regime_a_hdpe_bi2o3_phi0p189",
        b_dir="regime_b_hdpe_bi2o3",
        c_dir="regime_c_hdpe_bi2o3",
        density=2.452,
        color="#0072B2",
        marker="o",
        k_edges=((90.526, "Bi K"),),
    ),
    MaterialSpec(
        key="wo3",
        label=r"HDPE/WO$_3$",
        short_label=r"WO$_3$",
        a_dir="regime_a_hdpe_wo3_phi0p189",
        b_dir="regime_b_hdpe_wo3",
        c_dir="regime_c_hdpe_wo3",
        density=2.124,
        color="#D55E00",
        marker="s",
        k_edges=((69.525, "W K"),),
    ),
    MaterialSpec(
        key="bawo4",
        label=r"HDPE/BaWO$_4$",
        short_label=r"BaWO$_4$",
        a_dir="regime_a_hdpe_bawo4_phi0p189",
        b_dir="regime_b_hdpe_bawo4",
        c_dir="regime_c_hdpe_bawo4",
        density=1.927,
        color="#009E73",
        marker="^",
        k_edges=((37.441, "Ba K"), (69.525, "W K")),
    ),
    MaterialSpec(
        key="ternary",
        label=r"HDPE/Bi$_2$O$_3$/WO$_3$",
        short_label=r"Bi$_2$O$_3$/WO$_3$",
        a_dir="regime_a_hdpe_bi2o3_wo3_ternary",
        b_dir="regime_b_hdpe_bi2o3_wo3_ternary",
        c_dir="regime_c_hdpe_bi2o3_wo3_ternary",
        density=2.366,
        color="#CC79A7",
        marker="D",
        k_edges=((69.525, "W K"), (90.526, "Bi K")),
        h1_equivalent=False,
    ),
    MaterialSpec(
        key="gd2o3",
        label=r"HDPE/Gd$_2$O$_3$",
        short_label=r"Gd$_2$O$_3$",
        a_dir="regime_a_hdpe_gd2o3_phi0p189",
        b_dir="regime_b_hdpe_gd2o3",
        c_dir="regime_c_hdpe_gd2o3",
        density=2.107,
        color="#E69F00",
        marker="v",
        k_edges=((50.239, "Gd K"),),
    ),
    MaterialSpec(
        key="pbwo4",
        label=r"HDPE/PbWO$_4$",
        short_label=r"PbWO$_4$",
        a_dir="regime_a_hdpe_pbwo4_phi0p189",
        b_dir="regime_b_hdpe_pbwo4",
        c_dir="regime_c_hdpe_pbwo4",
        density=2.369,
        color="#56B4E9",
        marker="P",
        k_edges=((69.525, "W K"), (88.005, "Pb K")),
    ),
)


ENERGIES_10 = np.array([30, 50, 80, 100, 150, 356, 511, 662, 1173, 1332], dtype=float)
H1_ENERGIES = np.array([30, 50, 80, 100, 150], dtype=float)


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.family": "DejaVu Sans",
            "font.size": 8.2,
            "axes.labelsize": 9.0,
            "axes.titlesize": 9.4,
            "axes.titleweight": "bold",
            "axes.linewidth": 1.1,
            "axes.edgecolor": "black",
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "xtick.major.size": 5,
            "ytick.major.size": 5,
            "xtick.major.width": 1.0,
            "ytick.major.width": 1.0,
            "legend.frameon": True,
            "legend.edgecolor": "black",
            "legend.framealpha": 0.92,
            "legend.fancybox": False,
            "legend.fontsize": 7.4,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def style_axis(ax: plt.Axes) -> None:
    ax.tick_params(axis="both", which="major", direction="in", top=True, right=True)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.1)
        spine.set_color("black")


def save_figure(fig: plt.Figure, stem: str) -> dict[str, str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "png": OUT_DIR / f"{stem}.png",
        "pdf": OUT_DIR / f"{stem}.pdf",
        "svg": OUT_DIR / f"{stem}.svg",
    }
    fig.savefig(paths["png"], dpi=450, bbox_inches="tight", facecolor="white")
    fig.savefig(paths["pdf"], bbox_inches="tight", facecolor="white")
    fig.savefig(paths["svg"], bbox_inches="tight", facecolor="white")
    return {fmt: str(path.relative_to(ROOT)) for fmt, path in paths.items()}


def load_regime_a(spec: MaterialSpec) -> pd.DataFrame:
    path = RESULTS / spec.a_dir / "reference_comparison.csv"
    df = pd.read_csv(path).copy()
    return pd.DataFrame(
        {
            "energy": df["energy"].astype(float),
            "sim": df["mass_attenuation_cm2_g_simulated"].astype(float),
            "std": df.get("mass_attenuation_std_cm2_g_simulated", pd.Series(np.zeros(len(df)))).astype(float),
            "ref": df["mass_attenuation_cm2_g_reference"].astype(float),
            "delta": df["mass_attenuation_cm2_g_percent_difference"].astype(float),
        }
    )


def load_regime_sweep(spec: MaterialSpec, regime: str) -> pd.DataFrame:
    directory = spec.b_dir if regime == "B" else spec.c_dir
    path = RESULTS / directory / "sweep_summary.csv"
    df = pd.read_csv(path).copy()
    if "mass_attenuation_cm2_g" in df.columns:
        sim = df["mass_attenuation_cm2_g"].astype(float)
    elif "mass_attenuation_cm2_g_simulated" in df.columns:
        sim = df["mass_attenuation_cm2_g_simulated"].astype(float)
    else:
        sim = df["linear_attenuation_cm_inv"].astype(float) / spec.density
    if "mass_attenuation_std_cm2_g" in df.columns:
        std = df["mass_attenuation_std_cm2_g"].astype(float)
    elif "mass_attenuation_std_cm2_g_simulated" in df.columns:
        std = df["mass_attenuation_std_cm2_g_simulated"].astype(float)
    elif "linear_attenuation_std_cm_inv" in df.columns:
        std = df["linear_attenuation_std_cm_inv"].astype(float) / spec.density
    else:
        std = pd.Series(np.zeros(len(df)))
    out = pd.DataFrame({"energy": df["energy"].astype(float), "sim": sim, "std": std})
    out["attenuated"] = np.rint(df["events"].astype(float) * (1.0 - df["transmission_fraction"].astype(float)))
    return out


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        0.02,
        0.96,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=11,
        fontweight="bold",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 1.5},
    )


def draw_k_edges(ax: plt.Axes, spec: MaterialSpec, *, top: float = 0.90) -> None:
    transform = ax.get_xaxis_transform()
    for i, (energy, label) in enumerate(spec.k_edges):
        ax.axvline(energy, color=spec.color, linestyle=":", linewidth=1.1, alpha=0.78, zorder=1)
        ax.text(
            energy * (1.03 + 0.05 * i),
            top - 0.10 * i,
            f"{label}\n{energy:.1f} keV",
            transform=transform,
            ha="left",
            va="top",
            fontsize=6.4,
            color=spec.color,
        )


def figure_1_xcom_validation() -> dict[str, str]:
    fig, axes = plt.subplots(2, 3, figsize=(10.6, 6.25), sharex=True)
    for ax, spec, label in zip(axes.flat, MATERIALS, ["A", "B", "C", "D", "E", "F"]):
        data = load_regime_a(spec)
        mean_abs = data["delta"].abs().mean()
        max_abs = data["delta"].abs().max()
        ax.errorbar(
            data["energy"],
            data["sim"],
            yerr=1.96 * data["std"],
            color=spec.color,
            marker=spec.marker,
            markersize=4.6,
            linewidth=1.4,
            capsize=2.5,
            label="Geant4",
            zorder=3,
        )
        ax.plot(data["energy"], data["ref"], color="black", linestyle="--", linewidth=1.25, label="NIST XCOM", zorder=2)
        draw_k_edges(ax, spec, top=0.83)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(spec.label)
        ax.text(
            0.97,
            0.94,
            f"mean {mean_abs:.3f}%\nmax {max_abs:.3f}%",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=6.9,
            bbox={"facecolor": "white", "edgecolor": "0.75", "linewidth": 0.45, "alpha": 0.88, "pad": 1.4},
        )
        ax.set_xlim(27, 1500)
        style_axis(ax)
        panel_label(ax, label)
    for ax in axes[:, 0]:
        ax.set_ylabel(r"$\mu/\rho$ (cm$^2$ g$^{-1}$)")
    for ax in axes[-1, :]:
        ax.set_xlabel("Photon energy (keV)")
    axes[0, 0].legend(loc="lower left", fontsize=7.1)
    fig.suptitle("Regime A effective-medium validation against NIST XCOM", fontsize=11.3, fontweight="bold", y=0.992)
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    outputs = save_figure(fig, "paper3_v09_fig1_six_material_xcom_validation")
    plt.close(fig)
    return outputs


def figure_2_kedge_landscape() -> dict[str, str]:
    fig = plt.figure(figsize=(9.6, 6.05))
    gs = gridspec.GridSpec(2, 2, figure=fig, height_ratios=(2.35, 1.05), width_ratios=(1.0, 0.035), hspace=0.36, wspace=0.035)
    ax_top = fig.add_subplot(gs[0, 0])
    ax_bottom = fig.add_subplot(gs[1, 0])
    cax = fig.add_subplot(gs[1, 1])
    delta_rows = []
    for spec in MATERIALS:
        data = load_regime_a(spec)
        ax_top.plot(
            data["energy"],
            data["sim"],
            color=spec.color,
            marker=spec.marker,
            markersize=4.8,
            linewidth=1.65,
            label=spec.short_label,
        )
        delta_rows.append(data.set_index("energy").loc[ENERGIES_10, "delta"].to_numpy(dtype=float))
    ax_top.axvspan(30, 150, color="#F0F0F0", zorder=0, alpha=0.7)
    global_edges = [(37.441, "Ba K"), (50.239, "Gd K"), (69.525, "W K"), (88.005, "Pb K"), (90.526, "Bi K")]
    transform = ax_top.get_xaxis_transform()
    for idx, (energy, label) in enumerate(global_edges):
        ax_top.axvline(energy, color="0.25", linestyle=":", linewidth=1.0, alpha=0.7)
        ax_top.text(energy * 1.01, 0.95 - idx * 0.08, f"{label}\n{energy:.1f}", transform=transform, fontsize=6.8, va="top")
    ax_top.set_xscale("log")
    ax_top.set_yscale("log")
    ax_top.set_xlim(27, 1500)
    ax_top.set_ylabel(r"Regime A $\mu/\rho$ (cm$^2$ g$^{-1}$)")
    ax_top.legend(loc="upper right", ncol=3, fontsize=7.1)
    ax_top.set_title("K-edge attenuation landscape across six filler chemistries")
    style_axis(ax_top)
    panel_label(ax_top, "A")

    delta = np.vstack(delta_rows)
    im = ax_bottom.imshow(delta, cmap="RdBu_r", norm=TwoSlopeNorm(vmin=-3.0, vcenter=0.0, vmax=3.0), aspect="auto")
    ax_bottom.set_yticks(np.arange(len(MATERIALS)))
    ax_bottom.set_yticklabels([spec.short_label for spec in MATERIALS])
    ax_bottom.set_xticks(np.arange(len(ENERGIES_10)))
    ax_bottom.set_xticklabels([f"{e:g}" for e in ENERGIES_10])
    ax_bottom.set_xlabel("Photon energy (keV)")
    ax_bottom.set_title("Regime A percent difference relative to NIST XCOM")
    for y in range(delta.shape[0]):
        for x in range(delta.shape[1]):
            value = delta[y, x]
            ax_bottom.text(x, y, f"{value:+.1f}", ha="center", va="center", fontsize=6.8, color="black")
    for spine in ax_bottom.spines.values():
        spine.set_linewidth(1.1)
        spine.set_color("black")
    panel_label(ax_bottom, "B")
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label("Delta vs XCOM (%)")
    outputs = save_figure(fig, "paper3_v09_fig2_kedge_landscape_delta_heatmap")
    plt.close(fig)
    return outputs


def ratio_matrix(regime: str) -> np.ndarray:
    rows = []
    for spec in MATERIALS:
        a = load_regime_a(spec).set_index("energy")
        r = load_regime_sweep(spec, regime).set_index("energy")
        rows.append((r.loc[H1_ENERGIES, "sim"] / a.loc[H1_ENERGIES, "sim"]).to_numpy(dtype=float))
    return np.vstack(rows)


def draw_ratio_heatmap(ax: plt.Axes, data: np.ndarray, title: str) -> None:
    clipped = np.clip(data, 0.92, 1.08)
    im = ax.imshow(clipped, cmap="RdBu", norm=TwoSlopeNorm(vmin=0.92, vcenter=1.0, vmax=1.08), aspect="auto")
    ax.set_title(title)
    ax.set_xticks(np.arange(len(H1_ENERGIES)))
    ax.set_xticklabels([f"{e:g}" for e in H1_ENERGIES])
    ax.set_yticks(np.arange(len(MATERIALS)))
    ax.set_yticklabels([spec.short_label + (r"$^*$" if not spec.h1_equivalent else "") for spec in MATERIALS])
    ax.set_xlabel("Photon energy (keV)")
    for y, spec in enumerate(MATERIALS):
        for x in range(len(H1_ENERGIES)):
            value = data[y, x]
            is_gate_fail = abs(value - 1.0) > 0.03 and spec.h1_equivalent
            color = "white" if value < 0.94 or value > 1.06 else "black"
            weight = "bold" if is_gate_fail else "normal"
            ax.text(x, y, f"{value:.3f}", ha="center", va="center", fontsize=7.3, color=color, fontweight=weight)
    ternary_index = next(i for i, spec in enumerate(MATERIALS) if not spec.h1_equivalent)
    ax.add_patch(Rectangle((-0.5, ternary_index - 0.5), len(H1_ENERGIES), 1.0, fill=False, edgecolor="black", linewidth=1.1))
    for spine in ax.spines.values():
        spine.set_linewidth(1.1)
        spine.set_color("black")
    return im


def figure_3_cross_regime_heatmaps() -> dict[str, str]:
    fig = plt.figure(figsize=(9.8, 3.85))
    gs = gridspec.GridSpec(1, 3, figure=fig, width_ratios=(1, 1, 0.04), wspace=0.18)
    axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])]
    cax = fig.add_subplot(gs[0, 2])
    data_b = ratio_matrix("B")
    data_c = ratio_matrix("C")
    im = draw_ratio_heatmap(axes[0], data_b, "Regime B / Regime A")
    draw_ratio_heatmap(axes[1], data_c, "Regime C / Regime A")
    axes[0].set_ylabel("Material")
    axes[1].set_yticklabels([])
    panel_label(axes[0], "A")
    panel_label(axes[1], "B")
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label("Ratio to Regime A\n(clipped 0.92-1.08)")
    fig.suptitle("Cross-regime H1 agreement at 30-150 keV", fontsize=11.3, fontweight="bold", y=0.985)
    fig.text(0.095, 0.035, r"$^*$Ternary explicit-RVE cases spatialise Bi$_2$O$_3$ only; shown as a non-H1-equivalent hybrid stress test.", fontsize=7.4)
    outputs = save_figure(fig, "paper3_v09_fig3_cross_regime_ratio_heatmaps")
    plt.close(fig)
    return outputs


def figure_4_explicit_rve_agreement() -> dict[str, str]:
    fig, axes = plt.subplots(2, 3, figsize=(10.6, 6.25), sharex=True)
    for ax, spec, label in zip(axes.flat, MATERIALS, ["A", "B", "C", "D", "E", "F"]):
        a = load_regime_a(spec)
        b = load_regime_sweep(spec, "B")
        c = load_regime_sweep(spec, "C")
        if not spec.h1_equivalent:
            ax.set_facecolor("#F7F7F7")
        ax.plot(a["energy"], a["sim"], color="black", linewidth=1.35, label="A reference", zorder=2)
        ax.errorbar(
            b["energy"],
            b["sim"],
            yerr=1.96 * b["std"],
            color="#0072B2",
            marker="^",
            linestyle="none",
            markersize=4.2,
            capsize=2.0,
            label="B 1 um RVE",
            zorder=3,
        )
        ax.errorbar(
            c["energy"],
            c["sim"],
            yerr=1.96 * c["std"],
            color="#D55E00",
            marker="s",
            linestyle="none",
            markersize=4.0,
            capsize=2.0,
            label="C 250 nm RVE",
            zorder=4,
        )
        draw_k_edges(ax, spec, top=0.82)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(27, 1500)
        ax.set_title(spec.label)
        style_axis(ax)
        panel_label(ax, label)
        if not spec.h1_equivalent:
            ax.text(
                0.98,
                0.05,
                "hybrid ternary\ngeometry",
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=6.8,
                bbox={"facecolor": "white", "edgecolor": "black", "linewidth": 0.5, "alpha": 0.9},
            )
    for ax in axes[:, 0]:
        ax.set_ylabel(r"$\mu/\rho$ (cm$^2$ g$^{-1}$)")
    for ax in axes[-1, :]:
        ax.set_xlabel("Photon energy (keV)")
    axes[0, 0].legend(loc="lower left", fontsize=7.1)
    fig.suptitle("Explicit-RVE attenuation compared with matched Regime A baseline", fontsize=11.3, fontweight="bold", y=0.992)
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    outputs = save_figure(fig, "paper3_v09_fig4_explicit_rve_agreement")
    plt.close(fig)
    return outputs


def main() -> None:
    apply_style()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "figure_1": figure_1_xcom_validation(),
        "figure_2": figure_2_kedge_landscape(),
        "figure_3": figure_3_cross_regime_heatmaps(),
        "figure_4": figure_4_explicit_rve_agreement(),
    }
    manifest = OUT_DIR / "paper3_v09_figure_manifest.json"
    manifest.write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
    for figure, formats in outputs.items():
        print(f"{figure}:")
        for fmt, rel_path in formats.items():
            print(f"  {fmt}: {rel_path}")
    print(f"manifest: {manifest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()