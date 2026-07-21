from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

NAVY = "#1F4E79"
RUST = "#B8572D"
TEAL = "#1F7A68"
GOLD = "#C58A1E"
SLATE = "#5B6573"
LIGHT_BG = "#F4F7FB"
CARD_BG = "#FFFFFF"
INK = "#101418"
MUTED = "#516173"

SCIENTIFIC_RC = {
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
    "xtick.minor.visible": False,
    "ytick.minor.visible": False,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
}

plt.rcParams.update(SCIENTIFIC_RC)


def add_panel(ax, x, y, w, h, facecolor=CARD_BG, edgecolor="#D6DDE6", linewidth=1.2, radius=0.03):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.012,rounding_size={radius}",
        linewidth=linewidth,
        edgecolor=edgecolor,
        facecolor=facecolor,
        transform=ax.transAxes,
    )
    ax.add_patch(patch)
    return patch


def add_chip(ax, x, y, text, color, textcolor="white"):
    chip = FancyBboxPatch(
        (x, y),
        0.12,
        0.045,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        linewidth=0,
        edgecolor=color,
        facecolor=color,
        transform=ax.transAxes,
    )
    ax.add_patch(chip)
    ax.text(
        x + 0.06,
        y + 0.0225,
        text,
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=8.5,
        fontweight="bold",
        color=textcolor,
    )


def add_card(ax, x, y, w, h, title, subtitle, body_lines, accent, chip_text, mode):
    add_panel(ax, x, y, w, h)
    ax.add_patch(
        Rectangle((x, y + h - 0.028), w, 0.028, transform=ax.transAxes, facecolor=accent, edgecolor="none")
    )
    ax.text(x + 0.02, y + h - 0.05, title, transform=ax.transAxes, ha="left", va="top", fontsize=12.5, fontweight="bold", color=INK)
    ax.text(x + 0.02, y + h - 0.095, subtitle, transform=ax.transAxes, ha="left", va="top", fontsize=9.5, color=accent, fontweight="bold")
    ax.text(
        x + 0.02,
        y + h - 0.145,
        "\n".join(body_lines),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.9,
        color=MUTED,
        linespacing=1.35,
    )
    add_chip(ax, x + 0.02, y + 0.025, chip_text, accent)
    draw_schematic(ax, x + w - 0.12, y + 0.08, accent, mode)


def draw_schematic(ax, x, y, accent, mode):
    frame = Rectangle((x, y), 0.09, 0.12, transform=ax.transAxes, facecolor="#FBFCFE", edgecolor="#CAD3DE", linewidth=1.0)
    ax.add_patch(frame)
    beam = FancyArrowPatch((x - 0.03, y + 0.06), (x + 0.005, y + 0.06), arrowstyle="-|>", mutation_scale=12, linewidth=1.2, color=INK, transform=ax.transAxes)
    ax.add_patch(beam)

    if mode == "A":
        for idx in range(4):
            band = Rectangle((x + 0.012, y + 0.018 + idx * 0.022), 0.066, 0.012, transform=ax.transAxes, facecolor=accent, edgecolor="none", alpha=0.22 + idx * 0.08)
            ax.add_patch(band)
    elif mode == "B":
        centers = [
            (0.022, 0.028), (0.045, 0.028), (0.068, 0.028),
            (0.022, 0.058), (0.045, 0.058), (0.068, 0.058),
            (0.022, 0.088), (0.045, 0.088), (0.068, 0.088),
        ]
        for dx, dy in centers:
            circle = Circle((x + dx, y + dy), 0.008, transform=ax.transAxes, facecolor=accent, edgecolor="white", linewidth=0.4, alpha=0.9)
            ax.add_patch(circle)
    else:
        centers = [(0.026, 0.038), (0.043, 0.034), (0.061, 0.046), (0.033, 0.064), (0.055, 0.067), (0.046, 0.088)]
        for dx, dy in centers:
            circle = Circle((x + dx, y + dy), 0.011, transform=ax.transAxes, facecolor=accent, edgecolor="white", linewidth=0.5, alpha=0.88)
            ax.add_patch(circle)


def add_metric(ax, x, title, value, accent):
    add_panel(ax, x, 0.105, 0.19, 0.10, facecolor="#FFFFFF", edgecolor="#D9E1EA", linewidth=1.0, radius=0.022)
    ax.text(x + 0.018, 0.182, title, transform=ax.transAxes, ha="left", va="top", fontsize=8.1, color=MUTED, fontweight="bold")
    ax.text(x + 0.018, 0.142, value, transform=ax.transAxes, ha="left", va="top", fontsize=11.8, color=accent, fontweight="bold")


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    fig, ax = plt.subplots(figsize=(11.5, 6.5))
    ax.set_axis_off()
    fig.patch.set_facecolor(LIGHT_BG)

    header = FancyBboxPatch(
        (0.03, 0.83),
        0.94,
        0.12,
        boxstyle="round,pad=0.015,rounding_size=0.03",
        linewidth=0,
        edgecolor="none",
        facecolor="#DCEAF7",
        transform=ax.transAxes,
    )
    ax.add_patch(header)

    ax.text(
        0.05,
        0.925,
        "Graphical Abstract: Geant4 Modelling Regimes for Nanocomposite Shielding",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=16,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.05,
        0.875,
        "Matched-composition HDPE/Bi2O3 benchmark: production model, explicit validation RVE, and union stress test.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        color=SLATE,
    )

    add_card(
        ax,
        0.03,
        0.40,
        0.28,
        0.34,
        "Regime A",
        "Effective-medium transport",
        [
            "Homogeneous G4Material slab",
            "Fastest route for bulk attenuation",
            "Use as the production shielding model",
        ],
        NAVY,
        "Production",
        "A",
    )
    add_card(
        ax,
        0.36,
        0.40,
        0.28,
        0.34,
        "Regime B",
        "Explicit parameterised RVE",
        [
            "1 um RVE with 2,888 explicit spheres",
            "Best scalable explicit geometry",
            "Use to validate the bulk approximation",
        ],
        RUST,
        "Validate",
        "B",
    )
    add_card(
        ax,
        0.69,
        0.40,
        0.28,
        0.34,
        "Regime C",
        "Explicit union-cluster RVE",
        [
            "250 nm RVE with 45-sphere cluster",
            "Useful only for small union stress tests",
            "Limited by voxelizer memory growth",
        ],
        TEAL,
        "Stress test",
        "C",
    )

    for x0, x1, label in ((0.31, 0.36, "check"), (0.64, 0.69, "bound")):
        arrow = FancyArrowPatch(
            (x0, 0.57),
            (x1, 0.57),
            arrowstyle="-|>",
            mutation_scale=15,
            linewidth=1.3,
            color=INK,
            transform=ax.transAxes,
        )
        ax.add_patch(arrow)
        ax.text((x0 + x1) / 2, 0.60, label, transform=ax.transAxes, ha="center", va="bottom", fontsize=8.5, color=MUTED, fontweight="bold")

    add_panel(ax, 0.03, 0.07, 0.94, 0.24, facecolor="#ECF4FB", edgecolor="#D6E4F0", linewidth=1.1, radius=0.03)
    ax.text(
        0.05,
        0.275,
        "Main result and workflow decision",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=12.5,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.05,
        0.225,
        "All three regimes stayed within the pre-registered 3% agreement window at 30-150 keV.\n"
        "Recommended workflow: A for production attenuation, B for explicit validation, and C only for small-union stress tests.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.8,
        color=INK,
        linespacing=1.45,
    )

    add_metric(ax, 0.05, "XCOM check", "0.549% mean error", NAVY)
    add_metric(ax, 0.28, "Cross-regime gate", "< 3% deviation", RUST)
    add_metric(ax, 0.51, "Explicit scalability", "2,888 spheres feasible", TEAL)
    add_metric(ax, 0.74, "Union limit", "~45 spheres on 8 GB", GOLD)

    png_path = out_dir / "graphical_abstract_paper3.png"
    pdf_path = out_dir / "graphical_abstract_paper3.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor=LIGHT_BG, edgecolor="none")
    fig.savefig(pdf_path, dpi=300, bbox_inches="tight", facecolor=LIGHT_BG, edgecolor="none")
    plt.close(fig)
    print(png_path)
    print(pdf_path)


if __name__ == "__main__":
    main()
