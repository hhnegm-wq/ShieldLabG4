"""Generate a publication-ready system architecture figure for Paper 2."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BLUE = "#1f4e79"
LBLUE = "#dbe8f5"
ORANGE = "#c55a11"
LORANGE = "#fbe5d6"
GREEN = "#375623"
LGREEN = "#e2f0d9"
RED = "#c00000"
LRED = "#fde2e2"
GRAY = "#595959"
LGRAY = "#ededed"
PURPLE = "#7030a0"
BLACK = "#000000"
WHITE = "#ffffff"

plt.rcParams.update({
    "axes.facecolor": WHITE,
    "figure.facecolor": WHITE,
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

OUTPUT = Path(__file__).parent.parent.parent / "figures" / "fig01_system_architecture.png"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def add_box(ax, x, y, w, h, title, subtitle="", face=LBLUE, edge=BLUE, title_size=10.8):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.012,rounding_size=0.015",
        facecolor=face,
        edgecolor=edge,
        linewidth=1.8,
        zorder=3,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center",
            fontsize=title_size, fontweight="bold", color=BLACK, zorder=4)
    if subtitle:
        ax.text(x + w / 2, y + h * 0.32, subtitle, ha="center", va="center",
                fontsize=8.8, color="#404040", zorder=4)


def add_lane(ax, y, h, label):
    ax.add_patch(
        FancyBboxPatch(
            (0.05, y), 0.87, h,
            boxstyle="round,pad=0.008,rounding_size=0.010",
            facecolor="#fafafa", edgecolor="#d9d9d9", linewidth=0.9, zorder=0,
        )
    )
    ax.text(0.026, y + h / 2, label, ha="left", va="center", fontsize=9,
            fontweight="bold", color="#666666")


def arrow(ax, x0, y0, x1, y1, color=BLACK, dashed=False, lw=1.8):
    ax.annotate(
        "",
        xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle="->",
            color=color,
            lw=lw,
            linestyle=(0, (5, 4)) if dashed else "solid",
            shrinkA=6,
            shrinkB=6,
            connectionstyle="arc3,rad=0",
        ),
        zorder=5,
    )


def main():
    fig, ax = plt.subplots(figsize=(15.0, 8.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.965, "ShieldLab G4 System Architecture",
            ha="center", va="top", fontsize=18, fontweight="bold")
    ax.text(0.5, 0.928,
            "Shared physics core with synchronous analytics, asynchronous Geant4 execution, and gated release workflow",
            ha="center", va="top", fontsize=10.5, color="#444444")

    add_lane(ax, 0.74, 0.13, "User access")
    add_lane(ax, 0.54, 0.14, "API and middleware")
    add_lane(ax, 0.33, 0.15, "Domain services")
    add_lane(ax, 0.12, 0.14, "Execution and infrastructure")

    add_box(ax, 0.10, 0.775, 0.16, 0.07, "CLI", "cli/")
    add_box(ax, 0.30, 0.775, 0.16, 0.07, "Streamlit UI", "ui/")
    add_box(ax, 0.50, 0.775, 0.16, 0.07, "REST clients", "external consumers")
    add_box(ax, 0.70, 0.775, 0.16, 0.07, "Bicep and az CLI", "deployment surface")

    add_box(ax, 0.19, 0.565, 0.60, 0.088, "FastAPI service", "api/", face="#eef4fb", edge=BLUE, title_size=11.2)
    chips = [
        ("HMAC auth", 0.22),
        ("CORS", 0.32),
        ("Rate limit", 0.41),
        ("Quota", 0.51),
        ("OTel tracing", 0.61),
        ("JSON logs", 0.71),
    ]
    for label, x in chips:
        add_box(ax, x, 0.509, 0.09, 0.047, label, face="#dce8f6", edge=BLUE, title_size=8.0)

    add_box(ax, 0.09, 0.36, 0.18, 0.075, "Python library", "shieldlab/", face=LBLUE, edge=BLUE, title_size=10.5)
    add_box(ax, 0.31, 0.36, 0.18, 0.075, "Geant4 executable", "app/ + src/", face=LORANGE, edge=ORANGE, title_size=10.5)
    add_box(ax, 0.53, 0.36, 0.15, 0.075, "CI gates", "ci / science / release", face=LGREEN, edge=GREEN, title_size=10.5)
    add_box(ax, 0.72, 0.36, 0.14, 0.075, "Figure export", "scripts/figures/", face=LGREEN, edge=GREEN, title_size=10.0)

    add_box(ax, 0.09, 0.145, 0.18, 0.072, "Azure queue", "job envelope", face=LORANGE, edge=ORANGE, title_size=10.2)
    add_box(ax, 0.33, 0.145, 0.15, 0.072, "Worker", "executes Geant4", face=LGRAY, edge=GRAY, title_size=10.2)
    add_box(ax, 0.53, 0.145, 0.13, 0.072, "Poison queue", "failed after 3 dequeues", face=LRED, edge=RED, title_size=9.8)
    add_box(ax, 0.71, 0.145, 0.18, 0.072, "Azure runtime", "private endpoints, VNet, KV, ACR", face="#e7eef7", edge=BLUE, title_size=10.0)

    arrow(ax, 0.18, 0.775, 0.39, 0.65, color=BLUE)
    arrow(ax, 0.38, 0.775, 0.45, 0.65, color=BLUE)
    arrow(ax, 0.58, 0.775, 0.49, 0.65, color=BLUE)
    arrow(ax, 0.78, 0.775, 0.78, 0.217, color=BLUE)

    arrow(ax, 0.39, 0.565, 0.18, 0.435, color=BLUE)
    arrow(ax, 0.49, 0.565, 0.40, 0.435, color=ORANGE)
    arrow(ax, 0.60, 0.565, 0.60, 0.435, color=GREEN)
    arrow(ax, 0.69, 0.565, 0.79, 0.435, color=GREEN)

    arrow(ax, 0.57, 0.565, 0.18, 0.217, color=ORANGE, dashed=True, lw=2.1)
    ax.text(0.345, 0.395, "async Geant4 job submission", fontsize=8.7, color=ORANGE,
            fontweight="bold", style="italic",
            bbox=dict(boxstyle="round,pad=0.16", facecolor=WHITE, edgecolor="none", alpha=0.85))

    arrow(ax, 0.27, 0.181, 0.33, 0.181, color=GRAY)
    arrow(ax, 0.405, 0.217, 0.40, 0.36, color=ORANGE)
    arrow(ax, 0.48, 0.181, 0.53, 0.181, color=RED, dashed=True)

    ax.annotate(
        "",
        xy=(0.94, 0.215), xytext=(0.94, 0.845),
        arrowprops=dict(arrowstyle="<->", color=PURPLE, lw=2.2),
        zorder=5,
    )
    ax.text(0.95, 0.53, "X-Correlation-Id\ntraces request, queue, worker,\nand result retrieval",
            ha="left", va="center", fontsize=9.0, color=PURPLE,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#f3e8ff", edgecolor=PURPLE, linewidth=1.0))

    legend = [
        (BLUE, "Python/API control path"),
        (ORANGE, "Monte Carlo execution path"),
        (GREEN, "Governance and publication path"),
        (RED, "Dead-letter failure path"),
        (PURPLE, "End-to-end correlation span"),
    ]
    legend_positions = [
        (0.11, 0.06),
        (0.34, 0.06),
        (0.59, 0.06),
        (0.11, 0.032),
        (0.34, 0.032),
    ]
    for (color, label), (x, y) in zip(legend, legend_positions):
        ax.plot([x, x + 0.03], [y, y], color=color, lw=3)
        ax.text(x + 0.035, y, label, va="center", fontsize=8.9, color="#222222")

    fig.savefig(str(OUTPUT), facecolor=WHITE, edgecolor="none")
    plt.close(fig)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
