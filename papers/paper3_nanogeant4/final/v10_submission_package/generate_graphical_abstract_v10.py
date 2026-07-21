from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

BLUE = "#0000FF"
RED = "#FF0000"
GREEN = "#00FF00"
BLACK = "#000000"
WHITE = "#FFFFFF"
LIGHT = "#F7F7F7"

plt.rcParams.update(
    {
        "figure.facecolor": WHITE,
        "axes.facecolor": WHITE,
        "savefig.facecolor": WHITE,
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.linewidth": 1.5,
        "axes.edgecolor": BLACK,
        "axes.grid": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    }
)


def add_box(ax, xy: tuple[float, float], width: float, height: float, title: str, lines: list[str], color: str) -> None:
    x, y = xy
    ax.add_patch(Rectangle((x, y), width, height, linewidth=1.5, edgecolor=BLACK, facecolor=WHITE))
    ax.add_patch(Rectangle((x, y + height - 0.08), width, 0.08, linewidth=0, facecolor=color))
    ax.text(x + 0.02, y + height - 0.04, title, ha="left", va="center", color=WHITE, fontsize=12, fontweight="bold")
    ax.text(x + 0.02, y + height - 0.12, "\n".join(lines), ha="left", va="top", color=BLACK, fontsize=8.9, linespacing=1.30)


def add_rve(ax, center: tuple[float, float], color: str, mode: str) -> None:
    cx, cy = center
    ax.add_patch(Rectangle((cx - 0.047, cy - 0.035), 0.094, 0.070, linewidth=1.2, edgecolor=BLACK, facecolor=LIGHT))
    if mode == "A":
        for idx in range(4):
            ax.add_patch(Rectangle((cx - 0.038, cy - 0.024 + idx * 0.016), 0.076, 0.009, linewidth=0, facecolor=color, alpha=0.30 + idx * 0.12))
    else:
        positions = [(-0.032, -0.020), (-0.005, -0.024), (0.025, -0.014), (-0.020, 0.006), (0.012, 0.010), (0.035, 0.024)]
        if mode == "B":
            positions += [(-0.038, 0.026), (0.040, -0.030), (0.000, 0.032)]
        for dx, dy in positions:
            radius = 0.007 if mode == "B" else 0.0085
            ax.add_patch(Circle((cx + dx, cy + dy), radius, linewidth=0.6, edgecolor=WHITE, facecolor=color))


def add_arrow(ax, start: tuple[float, float], end: tuple[float, float], label: str) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=18, linewidth=1.5, color=BLACK))
    ax.text((start[0] + end[0]) / 2, start[1] + 0.035, label, ha="center", va="bottom", fontsize=9, fontweight="bold")


def add_metric(ax, x: float, title: str, value: str, color: str) -> None:
    ax.add_patch(Rectangle((x, 0.08), 0.205, 0.105, linewidth=1.5, edgecolor=BLACK, facecolor=WHITE))
    ax.text(x + 0.012, 0.158, title, ha="left", va="center", fontsize=8.5, color=BLACK, fontweight="bold")
    ax.text(x + 0.012, 0.113, value, ha="left", va="center", fontsize=10.5, color=color, fontweight="bold")


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    fig, ax = plt.subplots(figsize=(11.5, 6.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()

    ax.text(
        0.05,
        0.94,
        "Effective-medium Geant4 predicts K-edge nanocomposite shielding",
        ha="left",
        va="top",
        fontsize=17,
        fontweight="bold",
        color=BLACK,
    )
    ax.text(
        0.05,
        0.885,
        "Six HDPE/high-Z fillers tested across homogeneous, parameterised-RVE, and multi-union-RVE regimes",
        ha="left",
        va="top",
        fontsize=11,
        color=BLACK,
    )

    add_box(ax, (0.05, 0.46), 0.25, 0.28, "Regime A", ["Homogeneous", "G4Material slab", "Production model", "XCOM benchmark"], BLUE)
    add_box(ax, (0.375, 0.46), 0.25, 0.28, "Regime B", ["1 um", "parameterised RVE", "25 nm spheres", "H1 validation path"], RED)
    add_box(ax, (0.70, 0.46), 0.25, 0.28, "Regime C", ["250 nm", "multi-union RVE", "Geometry check", "Finite-RVE caveat"], GREEN)

    add_rve(ax, (0.25, 0.515), BLUE, "A")
    add_rve(ax, (0.575, 0.515), RED, "B")
    add_rve(ax, (0.90, 0.515), GREEN, "C")
    add_arrow(ax, (0.305, 0.60), (0.365, 0.60), "compare")
    add_arrow(ax, (0.63, 0.60), (0.69, 0.60), "stress-test")

    ax.add_patch(Rectangle((0.05, 0.235), 0.90, 0.14, linewidth=1.5, edgecolor=BLACK, facecolor=LIGHT))
    ax.text(0.07, 0.337, "Main decision", ha="left", va="center", fontsize=12, fontweight="bold", color=BLACK)
    ax.text(
        0.07,
        0.292,
        "Use Regime A for macroscopic shielding; use Regime B for explicit validation; reserve Regime C for small-RVE checks.",
        ha="left",
        va="center",
        fontsize=10.5,
        color=BLACK,
    )
    ax.text(
        0.07,
        0.255,
        "Multi-filler explicit RVEs must preserve composition equivalence before claiming H1 validation.",
        ha="left",
        va="center",
        fontsize=10.5,
        color=BLACK,
    )

    add_metric(ax, 0.05, "XCOM validation", "6/6 pass", BLUE)
    add_metric(ax, 0.285, "Mean error", "0.339-0.793%", BLACK)
    add_metric(ax, 0.52, "Regime B H1", "5 binaries pass", RED)
    add_metric(ax, 0.755, "Ternary case", "negative control", GREEN)

    png_path = out_dir / "graphical_abstract_paper3_v10.png"
    pdf_path = out_dir / "graphical_abstract_paper3_v10.pdf"
    svg_path = out_dir / "graphical_abstract_paper3_v10.svg"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor=WHITE)
    fig.savefig(pdf_path, dpi=300, bbox_inches="tight", facecolor=WHITE)
    fig.savefig(svg_path, dpi=300, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    print(png_path)
    print(pdf_path)
    print(svg_path)


if __name__ == "__main__":
    main()
