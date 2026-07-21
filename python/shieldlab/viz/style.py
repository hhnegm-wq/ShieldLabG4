"""Journal-quality matplotlib style presets for ShieldLab G4.

Usage
-----
>>> from shieldlab.viz.style import apply_journal_style
>>> apply_journal_style("shieldlab_web")   # Streamlit display
>>> apply_journal_style("nature")          # journal submission
>>> fig, ax = plt.subplots()
>>> ax.plot(x, y)

Presets
-------
"shieldlab_web"     : ISIP-tuned web display (Streamlit, 16:10, crisp at 1440 px wide)
"nature"            : Nature / Nature family (single-column = 86 mm, double = 178 mm)
"elsevier"          : Elsevier / ScienceDirect (single-col = 90 mm, double = 190 mm)
"ieee"              : IEEE Transactions (single-col = 88 mm, double = 181 mm)
"aps"               : Physical Review journals (single-col = 86 mm, double = 178 mm)
"publication_strict": publication-first preset with conservative typography and line metrics
"default"           : Clean serif-free theme, safe for any journal
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

from shieldlab.metadata import COPYRIGHT_OWNER, PRODUCT_NAME

# ---------------------------------------------------------------------------
# Okabe-Ito colour-blind-safe palette (8 colours)
# https://jfly.uni-koeln.de/color/
# ---------------------------------------------------------------------------
OKABE_ITO = [
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # green
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish-purple
    "#56B4E9",  # sky-blue
    "#F0E442",  # yellow
    "#000000",  # black
]

# ---------------------------------------------------------------------------
# Preset definitions — only the values that differ from the defaults below
# ---------------------------------------------------------------------------
JOURNAL_PRESETS: dict[str, dict] = {
    # ── WEB DISPLAY ────────────────────────────────────────────────
    # ISIP-tuned web-display preset. Full-width (width="stretch") rendering
    # shows this at native screen resolution; dpi only affects save-to-disk export.
    "shieldlab_web": {
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "lines.linewidth": 1.8,
        "lines.markersize": 6,
        "axes.linewidth": 0.9,
        "xtick.major.width": 0.9,
        "ytick.major.width": 0.9,
        "figure.figsize": (8.5, 5.0),
        "figure.dpi": 110,
    },
    "nature": {
        "font.size": 7,
        "axes.titlesize": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
        "legend.fontsize": 6,
        "lines.linewidth": 1.0,
        "axes.linewidth": 0.5,
        "xtick.major.width": 0.5,
        "ytick.major.width": 0.5,
        "figure.figsize": (3.39, 2.54),   # single-column (86 mm × 65 mm)
        "figure.dpi": 300,
    },
    "elsevier": {
        "font.size": 8,
        "axes.titlesize": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "lines.linewidth": 1.2,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "figure.figsize": (3.54, 2.65),   # single-column (90 mm × 67 mm)
        "figure.dpi": 300,
    },
    "ieee": {
        "font.size": 8,
        "axes.titlesize": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "lines.linewidth": 1.2,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "figure.figsize": (3.46, 2.60),   # single-column (88 mm × 66 mm)
        "figure.dpi": 300,
    },
    "aps": {
        "font.size": 8,
        "axes.titlesize": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "lines.linewidth": 1.0,
        "axes.linewidth": 0.5,
        "xtick.major.width": 0.5,
        "ytick.major.width": 0.5,
        "figure.figsize": (3.39, 2.54),
        "figure.dpi": 300,
    },
    "publication_strict": {
        "font.size": 7,
        "axes.titlesize": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
        "legend.fontsize": 6,
        "lines.linewidth": 1.0,
        "axes.linewidth": 0.5,
        "xtick.major.width": 0.5,
        "ytick.major.width": 0.5,
        "savefig.dpi": 600,
        "figure.figsize": (3.39, 2.54),
        "figure.dpi": 300,
    },
    "default": {
        "font.size": 10,
        "axes.titlesize": 10,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "lines.linewidth": 1.5,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "figure.figsize": (6.0, 4.0),
        "figure.dpi": 150,
    },
}

# ---------------------------------------------------------------------------
# Base RC settings shared by all presets
# ---------------------------------------------------------------------------
_BASE_RC: dict = {
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "Liberation Sans"],
    # Figure & axes surfaces
    "figure.facecolor": "white",
    "axes.facecolor": "#fafafa",
    "axes.edgecolor": "#d1d5db",
    # Spines — remove top/right
    "axes.spines.top": False,
    "axes.spines.right": False,
    # Grid — ISIP gray-100 style
    "axes.grid": True,
    "grid.color": "#e5e7eb",
    "grid.alpha": 0.80,
    "grid.linewidth": 0.5,
    "grid.linestyle": "-",
    # Titles & labels
    "axes.titlepad": 9,
    "axes.titleweight": "bold",
    "axes.labelpad": 5,
    "axes.labelcolor": "#374151",
    # Ticks
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.color": "#6b7280",
    "ytick.color": "#6b7280",
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "xtick.minor.width": 0.4,
    "ytick.minor.width": 0.4,
    # Legend
    "legend.frameon": True,
    "legend.framealpha": 0.92,
    "legend.edgecolor": "#e5e7eb",
    "legend.borderpad": 0.6,
    "legend.handlelength": 1.6,
    "legend.labelspacing": 0.45,
    # Save
    "savefig.facecolor": "white",
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "axes.prop_cycle": mpl.cycler(color=OKABE_ITO),
}


def apply_journal_style(preset: str = "default") -> None:
    """Apply a journal-submission matplotlib style globally.

    Parameters
    ----------
    preset : one of "shieldlab_web", "nature", "elsevier", "ieee", "aps",
             "publication_strict", "default"

    The style persists for the lifetime of the Python process (i.e. the
    Streamlit session). Call once at the top of each Streamlit page file.
    """
    key = preset.lower()
    if key not in JOURNAL_PRESETS:
        raise ValueError(
            f"Unknown preset '{preset}'. Choose from: {list(JOURNAL_PRESETS)}"
        )
    rc = {**_BASE_RC, **JOURNAL_PRESETS[key]}
    mpl.rcParams.update(rc)


def finish_shieldlab_figure(fig: plt.Figure, *, pad: float = 1.4) -> None:
    """Apply the standard ShieldLab UI figure polish to a matplotlib figure."""
    fig.set_facecolor("white")
    for ax in fig.get_axes():
        ax.set_facecolor("#fafafa")
        ax.tick_params(which="both", labelcolor="#374151")
        ax.title.set_color("#111827")
        ax.xaxis.label.set_color("#374151")
        ax.yaxis.label.set_color("#374151")
        for spine in ax.spines.values():
            spine.set_edgecolor("#d1d5db")
    fig.tight_layout(pad=pad)


def add_reproducibility_footer(
    fig: plt.Figure,
    version: str = "",
    label: str = "ShieldLab G4",
    owner: str = COPYRIGHT_OWNER,
) -> None:
    """Stamp the bottom-right corner of *fig* with a reproducibility note.

    Includes: app label, version, and UTC timestamp.
    The text is intentionally faint so it does not interfere with the plot.
    """
    import datetime

    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    ver_str = f"v{version}" if version else ""
    base_label = label or PRODUCT_NAME
    owner_str = f" · © {owner}" if owner else ""
    text = f"{base_label} {ver_str}{owner_str} · {ts}"
    fig.text(
        0.99, 0.01,
        text,
        ha="right", va="bottom",
        fontsize=5,
        color="0.55",
        transform=fig.transFigure,
    )
