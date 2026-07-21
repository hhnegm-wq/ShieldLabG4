"""Generate a cleaner three-stage CI gate model for Paper 2."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BLACK = "#000000"
WHITE = "#ffffff"
BLUE = "#1f4e79"
LBLUE = "#dbe8f5"
GREEN = "#375623"
LGREEN = "#e2f0d9"
GOLD = "#7f6000"
LGOLD = "#fff2cc"
RED = "#c00000"

plt.rcParams.update({
    "axes.facecolor": WHITE,
    "figure.facecolor": WHITE,
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

OUTPUT = Path(__file__).parent.parent.parent / "figures" / "fig02_ci_gate_model.png"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def box(ax, x, y, w, h, face, edge, title, subtitle, bullets):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.018,rounding_size=0.02",
        facecolor=face,
        edgecolor=edge,
        linewidth=2.0,
        zorder=2,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h - 0.06, title, ha="center", va="center",
            fontsize=12.2, fontweight="bold", color=edge)
    ax.text(x + w / 2, y + h - 0.10, subtitle, ha="center", va="center",
            fontsize=9.2, color=edge, style="italic")
    base_y = y + h - 0.16
    for index, bullet in enumerate(bullets):
        yy = base_y - index * 0.075
        ax.text(x + 0.03, yy, "✓", ha="center", va="center",
            fontsize=12, fontweight="bold", color=edge)
        ax.text(x + 0.055, yy, bullet, ha="left", va="center",
            fontsize=9.8, color=BLACK)


def main():
    fig, ax = plt.subplots(figsize=(14.2, 8.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.965, "ShieldLab G4 Three-Tier CI Gate Model",
            ha="center", va="top", fontsize=18, fontweight="bold")
    ax.text(0.5, 0.928,
            "Development correctness must pass before scientific readiness; both must pass before release readiness.",
            ha="center", va="top", fontsize=10.5, color="#444444")

    box(ax, 0.055, 0.20, 0.26, 0.58, LBLUE, BLUE, "ci_gate", "Development correctness", [
        "import and syntax checks",
        "offline unit tests",
        "deterministic API checks",
        "dependency pin validation",
        "style and lint checks",
    ])
    box(ax, 0.37, 0.20, 0.26, 0.58, LGREEN, GREEN, "science_gate", "Scientific readiness", [
        "benchmark regression thresholds",
        "zero threshold coverage => fail",
        "provenance coverage = 100%",
        "statistical adequacy of runs",
        "NIST/XCOM agreement maintained",
    ])
    box(ax, 0.685, 0.20, 0.26, 0.58, LGOLD, GOLD, "release_gate", "Publication and release readiness", [
        "figure audit in source tree",
        "CycloneDX SBOM generation",
        "dependency vulnerability scan",
        "secret and container scan",
        "CHANGELOG and release assets",
    ])

    for x0, x1, label, color, y_text in [
        (0.315, 0.37, "pass ci_gate first", GREEN, 0.575),
        (0.63, 0.685, "pass science_gate first", GOLD, 0.575),
    ]:
        ax.annotate(
            "",
            xy=(x1, 0.49), xytext=(x0, 0.49),
            arrowprops=dict(arrowstyle="->", lw=2.0, color=color),
            zorder=4,
        )
        ax.text((x0 + x1) / 2, y_text, label, ha="center", va="bottom",
            fontsize=9.0, fontweight="bold", color=color,
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9))

        ax.text(0.185, 0.115, "[FAIL] block pull request", ha="center", va="center",
            fontsize=9.2, color=RED, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#fde2e2", edgecolor=RED))
        ax.text(0.50, 0.115, "[FAIL] block science sign-off", ha="center", va="center",
            fontsize=9.2, color=RED, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#fde2e2", edgecolor=RED))
        ax.text(0.815, 0.115, "[PASS] publish release candidate", ha="center", va="center",
            fontsize=9.2, color="#008a3b", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#e6f5ea", edgecolor="#008a3b"))

    ax.text(0.5, 0.055,
            "Critical rule: zero benchmark-threshold coverage or zero provenance coverage fails science_gate unconditionally.",
            ha="center", va="center", fontsize=10, fontweight="bold", color=GOLD,
            bbox=dict(boxstyle="round,pad=0.30", facecolor="#fff7db", edgecolor=GOLD, linewidth=1.4))

    fig.savefig(str(OUTPUT), facecolor=WHITE, edgecolor="none")
    plt.close(fig)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
