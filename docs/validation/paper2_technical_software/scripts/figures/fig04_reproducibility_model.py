"""Generate Figure 4: the five-layer reproducibility model."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BLACK = "#000000"
WHITE = "#ffffff"
COLORS = [
    ("#dbe8f5", "#1f4e79"),
    ("#fbe5d6", "#c55a11"),
    ("#e2f0d9", "#375623"),
    ("#fff2cc", "#7f6000"),
    ("#f3e8ff", "#7030a0"),
]

OUTPUT = Path(__file__).parent.parent.parent / "figures" / "fig04_reproducibility_model.png"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


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

    fig, ax = plt.subplots(figsize=(11.2, 7.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.975, "ShieldLab G4 Five-Layer Reproducibility Model",
            ha="center", va="top", fontsize=18, fontweight="bold")
    ax.text(0.5, 0.915,
            "Each layer adds enough evidence to re-run, audit, review, and defend a reported result.",
            ha="center", va="top", fontsize=10.5, color="#444444")

    layers = [
        ("1. Input reproducibility", "study JSON, material definitions, density, energy grid, seed"),
        ("2. Execution reproducibility", "CLI or API runner, generated macro, physics list, event count"),
        ("3. Output reproducibility", "CSV outputs, layer_dose.csv, manifest.json, figure export metadata"),
        ("4. Review reproducibility", "validation reports, science_gate evidence, manuscript and benchmark pack"),
        ("5. Operational reproducibility", "correlation IDs, JSON logs, queue envelopes, dead-letter artifacts"),
    ]

    y = 0.73
    for idx, ((face, edge), (title, desc)) in enumerate(zip(COLORS, layers)):
        h = 0.12
        patch = FancyBboxPatch(
            (0.11 + idx * 0.02, y - idx * 0.13), 0.70 - idx * 0.04, h,
            boxstyle="round,pad=0.015,rounding_size=0.02",
            facecolor=face, edgecolor=edge, linewidth=2.0,
        )
        ax.add_patch(patch)
        ax.text(0.15 + idx * 0.02, y - idx * 0.13 + 0.075, title,
                ha="left", va="center", fontsize=12.5, fontweight="bold", color=edge)
        ax.text(0.15 + idx * 0.02, y - idx * 0.13 + 0.038, desc,
                ha="left", va="center", fontsize=9.7, color=BLACK)

    ax.annotate("broader audit surface",
                xy=(0.84, 0.20), xytext=(0.84, 0.72),
                ha="center", va="center", fontsize=10, color="#555555",
                rotation=90,
                arrowprops=dict(arrowstyle="->", lw=1.8, color="#555555"))

    ax.text(0.50, 0.07,
            "A result is considered reproducible only when Layers 1-4 are present; Layer 5 extends the same guarantee to cloud-submitted jobs.",
            ha="center", va="center", fontsize=10, fontweight="bold", color="#404040",
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#fafafa", edgecolor="#d0d0d0"))

    fig.savefig(str(OUTPUT), facecolor=WHITE, edgecolor="none")
    plt.close(fig)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
