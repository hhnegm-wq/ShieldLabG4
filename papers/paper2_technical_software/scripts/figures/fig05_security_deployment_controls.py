"""Generate Figure 5: deployment security and audit controls."""
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
ORANGE = "#c55a11"
LORANGE = "#fbe5d6"
GREEN = "#375623"
LGREEN = "#e2f0d9"
PURPLE = "#7030a0"
LPURPLE = "#f3e8ff"

OUTPUT = Path(__file__).parent.parent.parent / "figures" / "fig05_security_deployment_controls.png"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def panel(ax, x, y, w, h, title, bullets, face, edge):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        facecolor=face, edgecolor=edge, linewidth=2.0,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h - 0.06, title, ha="center", va="center",
            fontsize=12.2, fontweight="bold", color=edge)
    for idx, bullet in enumerate(bullets):
        yy = y + h - 0.12 - idx * 0.085
        ax.text(x + 0.03, yy, "•", ha="center", va="center", fontsize=14, color=edge)
        ax.text(x + 0.05, yy, bullet, ha="left", va="center", fontsize=9.6, color=BLACK)


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

    fig, ax = plt.subplots(figsize=(11.8, 7.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.975, "ShieldLab G4 Deployment Security and Audit Controls",
            ha="center", va="top", fontsize=18, fontweight="bold")
    ax.text(0.5, 0.935,
            "The hardened deployment path combines authenticated ingress, quota enforcement, worker isolation, and private Azure resources.",
            ha="center", va="top", fontsize=10.5, color="#444444")

    panel(ax, 0.07, 0.50, 0.38, 0.30, "Ingress", [
        "Entra ID or HMAC-authenticated callers",
        "CORS allowlist for browser clients",
        "Schema validation before job creation",
    ], LBLUE, BLUE)
    panel(ax, 0.55, 0.50, 0.38, 0.30, "API safeguards", [
        "Rate limiting before quota accounting",
        "QuotaMiddleware for jobs/day and CPU-min/day",
        "HTTP 429 with Retry-After metadata",
    ], LORANGE, ORANGE)
    panel(ax, 0.07, 0.18, 0.38, 0.30, "Worker isolation", [
        "Queue-triggered execution only",
        "Managed identity for storage access",
        "Poison queue after repeated failure",
    ], LGREEN, GREEN)
    panel(ax, 0.55, 0.18, 0.38, 0.30, "Private Azure services", [
        "Private endpoints for blob and queue",
        "VNet integration for app runtime",
        "Deny-by-default storage ACLs",
    ], LPURPLE, PURPLE)

    ax.annotate("", xy=(0.55, 0.65), xytext=(0.45, 0.65),
                arrowprops=dict(arrowstyle="->", lw=2.0, color="#666666"))
    ax.annotate("", xy=(0.26, 0.48), xytext=(0.26, 0.50),
                arrowprops=dict(arrowstyle="->", lw=2.0, color="#666666"))
    ax.annotate("", xy=(0.74, 0.48), xytext=(0.74, 0.50),
                arrowprops=dict(arrowstyle="->", lw=2.0, color="#666666"))
    ax.annotate("", xy=(0.55, 0.33), xytext=(0.45, 0.33),
                arrowprops=dict(arrowstyle="->", lw=2.0, color="#666666"))

    ax.text(0.50, 0.11, "Optional public endpoint with authenticated ingress", ha="center", va="center",
            fontsize=10, fontweight="bold", color=BLUE)
    ax.text(0.50, 0.05,
            "X-Correlation-Id spans request, queue submission, worker execution, structured logs, and result retrieval.",
            ha="center", va="center", fontsize=10, fontweight="bold", color=PURPLE,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#faf5ff", edgecolor=PURPLE))

    fig.savefig(str(OUTPUT), facecolor=WHITE, edgecolor="none")
    plt.close(fig)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()