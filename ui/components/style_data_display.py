"""Data-display component CSS — path tables, lit-benchmark cards, chart frames.

Part of the ShieldLab G4 governed design-system layer stack.
"""
from __future__ import annotations

from components.style_tokens import *  # noqa: F401, F403

def _build_data_display_css(font_scale: float, caption_font: str) -> str:
    """Shared styles for path tables, benchmark cards, and chart frames."""
    return f"""
/* ── Path / settings table ───────────────────────────────────── */
.path-row {{
    display: grid; grid-template-columns: 200px 1fr auto; gap: 0.75rem;
    align-items: center; padding: 0.55rem 0.9rem;
    border-bottom: 1px solid {BORDER}; font-size: {caption_font};
}}
.path-row:nth-child(even) {{ background: {SURFACE_2}; }}
.path-row:last-child {{ border-bottom: none; }}
.path-label {{
    min-width: 10rem; font-weight: 700; color: {PRIMARY_DARK};
    text-transform: uppercase; font-size: {0.78 * font_scale:.3f}rem; letter-spacing: 0.05em;
}}
.path-value {{
    flex: 1; font-family: 'IBM Plex Mono','JetBrains Mono',monospace;
    font-size: {0.82 * font_scale:.3f}rem; color: {INK_SOFT}; word-break: break-all;
}}
.path-badge-ok   {{ display: inline-block; background: {GREEN_50};  color: {PRIMARY_MED}; font-size: 0.68rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; border: 1px solid {GREEN_200}; white-space: nowrap; }}
.path-badge-miss {{ display: inline-block; background: #fef2f2; color: {DANGER}; font-size: 0.68rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; border: 1px solid #fca5a5; white-space: nowrap; }}

.slg-path-table {{
    border: 1px solid {BORDER}; border-radius: var(--slg-r-sm); overflow: hidden;
    margin-top: 0.5rem; background: {SURFACE}; box-shadow: var(--slg-shadow-sm);
}}
.slg-path-table .path-row:nth-child(even) {{ background: {SURFACE_2}; }}
.slg-path-table .path-label {{ color: {INK}; -webkit-text-fill-color: {INK}; font-size: 0.85rem; letter-spacing: 0.01em; }}
.slg-path-table .path-value {{ color: {INK_SOFT}; -webkit-text-fill-color: {INK_SOFT}; }}

/* ── Literature benchmark cards ──────────────────────────────── */
.lit-benchmark-card {{
    border-left: 4px solid {PRIMARY_LIGHT};
    padding: 1rem 1.15rem;
    margin-bottom: 0.85rem;
}}
.lit-benchmark-row {{ display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; }}
.lit-benchmark-title {{
    font-family: 'Space Grotesk','Inter',sans-serif;
    font-weight: 700; color: {INK}; margin-bottom: 0.18rem; letter-spacing: -0.01em;
}}
.lit-benchmark-meta {{ font-size: 0.85rem; color: {MUTED}; }}
.lit-benchmark-status {{
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em;
    padding: 4px 10px; border-radius: 9999px; white-space: nowrap; height: fit-content;
    background: {GREEN_50}; color: {PRIMARY_DARK}; border: 1px solid {GREEN_200};
}}
.lit-benchmark-status--ready       {{ background: {GREEN_50}; color: {PRIMARY_MED}; border-color: {GREEN_200}; }}
.lit-benchmark-status--provisional {{ background: #fffbeb; color: #92400e; border-color: #fde68a; }}
.lit-benchmark-status--queued      {{ background: #f9fafb; color: #374151; border-color: {BORDER_MED}; }}
.lit-benchmark-notes {{ margin-top: 0.6rem; font-size: 0.90rem; color: {INK_SOFT}; line-height: 1.55; }}

/* ── Charts — ISIP card framing ─────────────────────────────── */
[data-testid="stPlotlyChart"],
[data-testid="stPyplotChart"] {{
    background: {SURFACE} !important;
    border: 1px solid {BORDER} !important;
    border-radius: var(--slg-r-md) !important;
    box-shadow: var(--slg-shadow-sm) !important;
    padding: 0.5rem !important;
}}

/* ── Scientific metric strip (render_metric_strip) ───────────── */
.slg-metric-strip {{
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    gap: 0.85rem !important;
    margin: 0.75rem 0 1rem !important;
}}
.slg-metric-strip--1 {{ grid-template-columns: 1fr !important; }}
.slg-metric-strip--2 {{ grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }}
.slg-metric-strip--3 {{ grid-template-columns: repeat(3, minmax(0, 1fr)) !important; }}
.slg-metric-strip--4 {{ grid-template-columns: repeat(4, minmax(0, 1fr)) !important; }}
.slg-metric-strip--5 {{ grid-template-columns: repeat(5, minmax(0, 1fr)) !important; }}
.slg-metric-strip--6 {{ grid-template-columns: repeat(6, minmax(0, 1fr)) !important; }}
.slg-metric-card {{
    background: {SURFACE} !important;
    border: 1px solid {BORDER} !important;
    border-top: 3px solid {PRIMARY} !important;
    border-radius: var(--slg-r-md) !important;
    padding: 0.85rem 1rem !important;
    box-shadow: var(--slg-shadow-sm) !important;
    min-width: 0 !important;
}}
.slg-metric-card-label {{
    color: {MUTED} !important;
    -webkit-text-fill-color: {MUTED} !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    margin-bottom: 0.25rem !important;
}}
.slg-metric-card-value {{
    color: {PRIMARY_DARK} !important;
    -webkit-text-fill-color: {PRIMARY_DARK} !important;
    font-family: 'Space Grotesk','Inter',system-ui,sans-serif !important;
    font-size: clamp(1.05rem, 1.55vw, 1.35rem) !important;
    font-weight: 700 !important;
    line-height: 1.22 !important;
    letter-spacing: 0 !important;
    overflow-wrap: anywhere !important;
}}
@media (max-width: 900px) {{
    .slg-metric-strip {{ grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }}
}}
@media (max-width: 560px) {{
    .slg-metric-strip {{ grid-template-columns: 1fr !important; }}
}}
"""


