"""Generate Figure 7: validation and governance coverage map."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

WHITE = "#ffffff"
BLACK = "#000000"
BLUE = "#1f4e79"
LBLUE = "#dbe8f5"
GREEN = "#375623"
LGREEN = "#e2f0d9"
GOLD = "#7f6000"
LGOLD = "#fff2cc"
GRAY = "#666666"

OUTPUT = Path(__file__).parent.parent.parent / "figures" / "fig07_validation_coverage_map.png"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def label_box(ax, x, y, w, h, text, face, edge, fs=10.2, weight="bold"):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor=face, edgecolor=edge, linewidth=1.8,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight=weight, color=edge if weight == "bold" else BLACK,
            linespacing=1.15)


def main():
    plt.rcParams.update({
        "axes.facecolor": WHITE,
        "figure.facecolor": WHITE,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })

    fig, ax = plt.subplots(figsize=(15.0, 7.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.975, "ShieldLab G4 Validation and Governance Coverage Map",
            ha="center", va="top", fontsize=18, fontweight="bold")
    ax.text(0.5, 0.935,
            "The test suite and release workflow are partitioned so software correctness, scientific validity, and release readiness are checked at different decision points.",
            ha="center", va="top", fontsize=10.5, color="#444444")

    label_box(ax, 0.06, 0.78, 0.22, 0.08, "Code surfaces", LBLUE, BLUE)
    label_box(ax, 0.33, 0.78, 0.26, 0.08, "Test surfaces", LGREEN, GREEN)
    label_box(ax, 0.63, 0.78, 0.19, 0.08, "Gate owners", LGOLD, GOLD)
    label_box(ax, 0.85, 0.78, 0.11, 0.08, "Outcome", "#f5f5f5", GRAY)

    rows = [
        ("Python library, API, UI", "unit, API, UI smoke tests", "ci_gate", "PR merge"),
        ("Benchmarks, manifests, seeds", "benchmark regression and provenance checks", "science_gate", "science sign-off"),
        ("Figures, SBOM, security assets", "figure audit, dependency and container scans", "release_gate", "release candidate"),
    ]
    ys = [0.63, 0.47, 0.31]
    colors = [(LBLUE, BLUE), (LGREEN, GREEN), (LGOLD, GOLD)]

    for (surface, tests, gate, outcome), y, (face, edge) in zip(rows, ys, colors):
        label_box(ax, 0.06, y, 0.22, 0.10, surface, face, edge, fs=10.4, weight="normal")
        label_box(ax, 0.33, y, 0.26, 0.10, tests, face, edge, fs=9.9, weight="normal")
        label_box(ax, 0.63, y, 0.19, 0.10, gate, face, edge, fs=11.0)
        label_box(ax, 0.85, y, 0.11, 0.10, outcome, "#f5f5f5", GRAY, fs=9.6, weight="normal")
        ax.annotate("", xy=(0.33, y + 0.05), xytext=(0.28, y + 0.05),
                    arrowprops=dict(arrowstyle="->", lw=1.8, color=edge))
        ax.annotate("", xy=(0.63, y + 0.05), xytext=(0.59, y + 0.05),
                    arrowprops=dict(arrowstyle="->", lw=1.8, color=edge))
        ax.annotate("", xy=(0.85, y + 0.05), xytext=(0.82, y + 0.05),
                    arrowprops=dict(arrowstyle="->", lw=1.8, color=edge))

    ax.text(0.50, 0.15,
            "This partitioning prevents routine software checks from being confused with benchmark validity\nor publication readiness, which is the central governance claim of the platform.",
            ha="center", va="center", fontsize=9.6, fontweight="bold", color="#404040",
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#fafafa", edgecolor="#d0d0d0"))

    fig.savefig(str(OUTPUT), facecolor=WHITE, edgecolor="none")
    plt.close(fig)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()