"""Generate Figure 6: correlation and observability flow."""
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
ORANGE = "#c55a11"
LORANGE = "#fbe5d6"
PURPLE = "#7030a0"
LPURPLE = "#f3e8ff"

OUTPUT = Path(__file__).parent.parent.parent / "figures" / "fig06_correlation_observability_flow.png"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def add_box(ax, x, y, w, h, title, subtitle, face, edge):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        facecolor=face, edgecolor=edge, linewidth=2.0,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center",
            fontsize=11.2, fontweight="bold", color=edge)
    ax.text(x + w / 2, y + h * 0.31, subtitle, ha="center", va="center",
            fontsize=8.8, color="#404040", linespacing=1.15)


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

    fig, ax = plt.subplots(figsize=(14.6, 7.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.975, "ShieldLab G4 Correlation and Observability Flow",
            ha="center", va="top", fontsize=18, fontweight="bold")
    ax.text(0.5, 0.935,
            "A single correlation identifier ties together the request path, queue handoff, worker execution, and result retrieval.",
            ha="center", va="top", fontsize=10.5, color="#444444")

    add_box(ax, 0.04, 0.55, 0.20, 0.16, "Client request", "UI, CLI, or REST caller", LBLUE, BLUE)
    add_box(ax, 0.27, 0.55, 0.23, 0.16, "FastAPI ingress", "TracingMiddleware reads\nor creates X-Correlation-Id", LBLUE, BLUE)
    add_box(ax, 0.53, 0.55, 0.20, 0.16, "Queue envelope", "job ID plus\ncorrelation metadata", LORANGE, ORANGE)
    add_box(ax, 0.76, 0.55, 0.20, 0.16, "Worker execution", "Geant4 run, manifest,\nstructured logs", LGREEN, GREEN)

    add_box(ax, 0.16, 0.22, 0.24, 0.14, "OTel spans", "HTTP route, queue submit,\nworker latency, result fetch", LPURPLE, PURPLE)
    add_box(ax, 0.42, 0.22, 0.24, 0.14, "JSON logs", "machine-parsable logs include\ncorrelation_id", LPURPLE, PURPLE)
    add_box(ax, 0.69, 0.22, 0.21, 0.14, "Result manifest", "study hash, seed, git SHA, outputs", LPURPLE, PURPLE)

    for x0, x1 in [(0.23, 0.27), (0.48, 0.52), (0.71, 0.75)]:
        ax.annotate("", xy=(x1, 0.63), xytext=(x0, 0.63),
                    arrowprops=dict(arrowstyle="->", lw=2.2, color="#666666"))

    for x in [0.375, 0.615, 0.845]:
        ax.annotate("", xy=(x, 0.36), xytext=(x, 0.55),
                    arrowprops=dict(arrowstyle="->", lw=1.8, color=PURPLE))

    ax.annotate("", xy=(0.18, 0.29), xytext=(0.12, 0.55),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=PURPLE, connectionstyle="arc3,rad=0.15"))
    ax.annotate("", xy=(0.72, 0.29), xytext=(0.86, 0.55),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=PURPLE, connectionstyle="arc3,rad=-0.12"))

    ax.text(0.50, 0.12,
            "Correlation enables post hoc audit across ingress, queue submission, worker logs,\nand returned results without coupling observability to any single exporter.",
            ha="center", va="center", fontsize=9.6, fontweight="bold", color=PURPLE,
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#faf5ff", edgecolor=PURPLE))

    fig.savefig(str(OUTPUT), facecolor=WHITE, edgecolor="none")
    plt.close(fig)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
