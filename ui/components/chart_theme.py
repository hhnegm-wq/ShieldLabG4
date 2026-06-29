"""ShieldLab G4 brand theming for matplotlib, Altair, and Plotly charts.

Keeps the entire platform visually consistent with the v2 modern theme defined in
`ui/components/styles.py`. Safe to import; each apply_* function silently no-ops
if the corresponding plotting library is not installed.
"""
from __future__ import annotations

import logging as _logging_mod

_log = _logging_mod.getLogger(__name__)

# Brand tokens mirroring the CSS :root variables in styles.py — ISIP green palette
PRIMARY        = "#059669"   # ISIP green-600
PRIMARY_2      = "#10b981"   # ISIP green-500
PRIMARY_DEEP   = "#064e3b"   # ISIP green-900
ACCENT         = "#34d399"   # ISIP green-400
INK            = "#111827"   # ISIP gray-900
INK_SOFT       = "#1f2937"   # ISIP gray-800
MUTED          = "#6b7280"   # ISIP gray-500
SURFACE        = "#ffffff"
GRID           = "rgba(5,150,105,0.08)"
GRID_HEX       = "#e5e7eb"   # ISIP gray-200

# Ordered qualitative palette — green-led, high-contrast for scientific figures
SHIELDLAB_PALETTE = [
    "#059669",   # primary green
    "#3b82f6",   # blue  (clear secondary)
    "#f59e0b",   # amber
    "#8b5cf6",   # violet
    "#ef4444",   # red
    "#10b981",   # emerald light
    "#0ea5e9",   # sky
    "#475569",   # slate
]

# Sequential colorscale for heatmaps / continuous data — green scale
SHIELDLAB_SEQUENTIAL = [
    [0.00, "#f0fdf4"],
    [0.20, "#a7f3d0"],
    [0.40, "#34d399"],
    [0.60, "#10b981"],
    [0.80, "#059669"],
    [1.00, "#064e3b"],
]

_FONT_STACK = ["Inter", "Segoe UI", "Helvetica Neue", "Arial", "sans-serif"]


def apply_matplotlib_theme() -> None:
    """Apply ShieldLab brand styling to matplotlib globally."""
    try:
        import matplotlib as mpl
        from cycler import cycler
    except Exception:
        return
    mpl.rcParams.update({
        "font.family": _FONT_STACK,
        "font.size": 10.5,
        "axes.titlesize": 12,
        "axes.titleweight": "600",
        "axes.titlecolor": INK,
        "axes.labelsize": 10.5,
        "axes.labelcolor": INK_SOFT,
        "axes.labelweight": "500",
        "axes.edgecolor": "#c7e3d0",
        "axes.linewidth": 0.9,
        "axes.facecolor": SURFACE,
        "axes.grid": True,
        "axes.grid.axis": "both",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.color": GRID_HEX,
        "grid.linestyle": "-",
        "grid.linewidth": 0.7,
        "grid.alpha": 0.9,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.frameon": False,
        "legend.fontsize": 9.5,
        "legend.labelcolor": INK,
        "figure.facecolor": SURFACE,
        "figure.edgecolor": SURFACE,
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "savefig.facecolor": SURFACE,
        "savefig.bbox": "tight",
        "lines.linewidth": 1.9,
        "lines.markersize": 5.5,
        "patch.edgecolor": "none",
        "axes.prop_cycle": cycler(color=SHIELDLAB_PALETTE),
    })


def apply_altair_theme() -> None:
    """Register and enable a ShieldLab Altair theme (used by st.line_chart)."""
    try:
        import altair as alt
    except Exception:
        return

    def _theme():
        return {
            "config": {
                "background": SURFACE,
                "view": {"stroke": "transparent"},
                "font": "Inter",
                "title": {
                    "font": "Space Grotesk, Inter, sans-serif",
                    "fontSize": 14,
                    "fontWeight": 700,
                    "color": INK,
                    "anchor": "start",
                    "offset": 12,
                },
                "axis": {
                    "labelFont": "Inter",
                    "labelFontSize": 11,
                    "labelColor": INK_SOFT,
                    "titleFont": "Inter",
                    "titleFontSize": 11,
                    "titleColor": INK,
                    "titleFontWeight": 600,
                    "domainColor": "#c7e3d0",
                    "tickColor": "#c7e3d0",
                    "gridColor": GRID_HEX,
                    "gridOpacity": 0.9,
                    "labelPadding": 4,
                },
                "legend": {
                    "labelFont": "Inter",
                    "labelColor": INK,
                    "titleFont": "Inter",
                    "titleColor": INK,
                    "titleFontWeight": 600,
                    "symbolType": "circle",
                    "padding": 6,
                },
                "range": {
                    "category": SHIELDLAB_PALETTE,
                    "ordinal": {"scheme": "greens"},
                    "ramp": {"scheme": "greens"},
                    "heatmap": {"scheme": "greens"},
                },
                "line": {"strokeWidth": 2.4, "strokeCap": "round"},
                "point": {"size": 60, "filled": True},
                "bar": {"cornerRadiusTopLeft": 3, "cornerRadiusTopRight": 3},
                "area": {"opacity": 0.45},
            }
        }

    try:
        alt.themes.register("shieldlab", _theme)
        alt.themes.enable("shieldlab")
    except Exception:
        _log.warning("Altair ShieldLab theme registration failed — charts will use default Altair styling", exc_info=True)


def apply_plotly_theme() -> None:
    """Register and set a ShieldLab Plotly template as the default."""
    try:
        import plotly.io as pio
        import plotly.graph_objects as go
    except Exception:
        return

    template = go.layout.Template(
        layout=go.Layout(
            font=dict(family="Inter, Segoe UI, sans-serif", size=12, color=INK),
            title=dict(
                font=dict(family="Space Grotesk, Inter, sans-serif", size=16, color=INK),
                x=0.02, xanchor="left", y=0.96,
            ),
            paper_bgcolor=SURFACE,
            plot_bgcolor=SURFACE,
            colorway=SHIELDLAB_PALETTE,
            margin=dict(l=56, r=24, t=56, b=48),
            hoverlabel=dict(
                bgcolor=INK, bordercolor=INK,
                font=dict(family="Inter", color="#ffffff", size=12),
            ),
            legend=dict(
                bgcolor="rgba(255,255,255,0)",
                bordercolor="rgba(0,0,0,0)",
                font=dict(color=INK),
            ),
            xaxis=dict(
                gridcolor=GRID_HEX, zerolinecolor=GRID_HEX,
                linecolor="#c7e3d0", ticks="outside", tickcolor="#c7e3d0",
                title=dict(font=dict(color=INK_SOFT, size=12)),
                tickfont=dict(color=INK_SOFT, size=11),
            ),
            yaxis=dict(
                gridcolor=GRID_HEX, zerolinecolor=GRID_HEX,
                linecolor="#c7e3d0", ticks="outside", tickcolor="#c7e3d0",
                title=dict(font=dict(color=INK_SOFT, size=12)),
                tickfont=dict(color=INK_SOFT, size=11),
            ),
            colorscale=dict(sequential=SHIELDLAB_SEQUENTIAL),
        )
    )
    try:
        pio.templates["shieldlab"] = template
        pio.templates.default = "plotly_white+shieldlab"
    except Exception:
        _log.warning("Plotly ShieldLab template registration failed — charts will use default Plotly styling", exc_info=True)


def apply_all_chart_themes() -> None:
    """Apply matplotlib, Altair, and Plotly ShieldLab themes (safe to call once at startup)."""
    apply_matplotlib_theme()
    apply_altair_theme()
    apply_plotly_theme()
