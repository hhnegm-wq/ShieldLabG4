"""Surface component CSS — hero banners, feature/workflow cards, stat blocks.

Part of the ShieldLab G4 governed design-system layer stack.
"""
from __future__ import annotations

from components.style_tokens import *  # noqa: F401, F403

def _build_surface_component_css(font_scale: float, caption_font: str, stat_font: str) -> str:
    """Shared hero and linked-card component styles used across the shell."""
    return f"""
/* ── Hero banner — ShieldLab brand ──────────────────────────── */
/* ISIP uses isip-gradient-hero: linear-gradient(135deg, #064e3b 0%, #1e3a8a 50%, #4c1d95 100%) */
.shieldlab-hero {{
    background:
        radial-gradient(ellipse 75% 50% at 50% -12%, rgba(52,211,153,0.25) 0%, transparent 55%),
        linear-gradient(135deg, {PRIMARY_DARK} 0%, #1e3a8a 55%, #4c1d95 100%) !important;
    border-radius: var(--slg-r-lg) !important;
    border: 1px solid rgba(52,211,153,0.20) !important;
    padding: 1.9rem 2.2rem 2rem !important;
    margin-bottom: 1.3rem !important;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 50px rgba(6,78,59,0.25), 0 0 0 1px rgba(52,211,153,0.10) !important;
}}
.shieldlab-hero::before {{
    content: '';
    position: absolute;
    top: -1px; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent 5%, {GREEN_400} 30%, {PRIMARY_LIGHT} 55%, {GREEN_400} 80%, transparent 95%);
    opacity: 0.85;
}}
.shieldlab-hero-kicker {{
    font-family: 'IBM Plex Mono','JetBrains Mono',monospace;
    font-size: 0.73rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.20em !important;
    text-transform: uppercase !important;
    color: {GREEN_400} !important;
    -webkit-text-fill-color: {GREEN_400} !important;
    margin-bottom: 0.4rem !important;
}}
.shieldlab-hero-title {{
    font-family: 'Space Grotesk','Inter',sans-serif !important;
    font-size: clamp(1.65rem, 2.3vw, 2.15rem) !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
    margin: 0.2rem 0 0.5rem !important;
    background: linear-gradient(135deg, #ffffff 0%, {GREEN_200} 70%, {GREEN_300} 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}}
.shieldlab-hero-body {{
    font-size: 1.0rem !important;
    line-height: 1.65 !important;
    max-width: 64rem !important;
    opacity: 0.88 !important;
    color: {GREEN_200} !important;
    -webkit-text-fill-color: {GREEN_200} !important;
}}
.shieldlab-hero--centered {{
    text-align: center;
}}
.shieldlab-hero--centered .shieldlab-hero-headline {{
    justify-content: center;
}}
.shieldlab-hero--centered .shieldlab-hero-body {{
    margin-left: auto !important;
    margin-right: auto !important;
}}
.shieldlab-hero--brand {{
    border-radius: var(--slg-r-xl) !important;
    padding: 2.2rem 2.8rem 2.5rem !important;
    margin-bottom: 1.5rem !important;
    box-shadow: 0 20px 50px rgba(6,78,59,0.25), 0 0 0 1px rgba(52,211,153,0.10), inset 0 1px 0 rgba(255,255,255,0.07) !important;
}}
.shieldlab-hero-logo {{
    display: flex;
    justify-content: center;
    margin-bottom: 0.9rem;
}}
.shieldlab-hero-logo img {{
    width: min(200px, 55%);
    border-radius: 16px;
    background: rgba(255,255,255,0.97);
    padding: 0.7rem;
    box-shadow: 0 12px 36px rgba(2,26,12,0.50), 0 0 0 1px rgba(52,211,153,0.28);
}}
.shieldlab-hero-title-icon {{
    height: 1.2em;
    width: auto;
    border-radius: 5px;
    flex-shrink: 0;
}}

/* ── Bar strip ───────────────────────────────────────────────── */
.bar-strip {{
    background: var(--slg-grad-primary);
    border: 1px solid {BORDER_GREEN};
    border-radius: var(--slg-r-sm);
    color: {GREEN_50};
    font-weight: 700;
    padding: 0.65rem 0.9rem;
    box-shadow: var(--slg-shadow-sm);
}}

/* ── shieldlab-card — shared surface + depth token ──────────── */
/* Use class="shieldlab-card" for generic panel, or use a modifier below */
.shieldlab-card,
.feature-card,
.section-card,
.workflow-card,
.lit-benchmark-card,
.physics-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: var(--slg-r-md);
    box-shadow: var(--slg-shadow-sm);
    transition: transform 0.20s ease, box-shadow 0.20s ease, border-color 0.20s ease;
}}
.shieldlab-card:hover,
.section-card:hover,
.workflow-card:hover,
.lit-benchmark-card:hover {{
    transform: translateY(-1px);
    box-shadow: var(--slg-shadow-md);
    border-color: {BORDER_GREEN};
}}
/* Generic standalone card */
.shieldlab-card {{ padding: 1.1rem 1.25rem; }}

/* ── Feature cards — ISIP isip-card pattern ─────────────────── */
.feature-card {{
    border-top: 3px solid {PRIMARY};
    padding: 1.25rem 1.4rem;
    height: 100%;
    position: relative; overflow: hidden;
}}
.feature-card:hover {{
    transform: translateY(-3px);
    box-shadow: var(--slg-shadow-lg);
    border-color: {GREEN_200};
}}
.feature-card-title {{ display: block; color: {PRIMARY_DARK}; font-size: {0.95 * font_scale:.3f}rem; font-weight: 700; margin-bottom: 0.35rem; }}
.feature-card-body  {{ display: block; color: {MUTED}; font-size: {caption_font}; line-height: 1.6; margin: 0 0 0.35rem 0; }}

/* ── Stat blocks ─────────────────────────────────────────────── */
.stat-number {{
    font-size: {stat_font};
    font-weight: 800;
    background: var(--slg-grad-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
    font-variant-numeric: tabular-nums;
}}
.stat-label {{
    font-size: {0.78 * font_scale:.3f}rem;
    color: {MUTED};
    -webkit-text-fill-color: {MUTED};
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-top: 3px;
}}

/* ── Section card ────────────────────────────────────────────── */
.section-card {{
    padding: 1.1rem 1.25rem;
    margin-bottom: 0.8rem;
}}

/* ── Physics card ────────────────────────────────────────────── */
.physics-card {{
    border-left: 4px solid {PRIMARY};
    padding: 1.1rem 1.3rem;
}}
.physics-card h4 {{
    color: {PRIMARY_DARK};
    font-size: {0.90 * font_scale:.3f}rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.3rem;
}}

/* ── Sidebar owner card ──────────────────────────────────────── */
.sidebar-owner-card {{
    margin-top: 1rem; padding: 0.9rem 1rem;
    border: 1px solid rgba(255,255,255,0.16);
    border-radius: var(--slg-r-sm);
    background: rgba(255,255,255,0.08);
}}
.sidebar-owner-card-title {{
    font-size: 0.70rem; text-transform: uppercase; letter-spacing: 0.09em;
    color: {GREEN_200}; -webkit-text-fill-color: {GREEN_200};
    margin-bottom: 0.3rem; font-weight: 800;
}}
.sidebar-owner-card-body {{
    font-size: {0.80 * font_scale:.3f}rem; line-height: 1.6;
    color: {GREEN_100}; -webkit-text-fill-color: {GREEN_100};
}}

/* ── Pro badge ───────────────────────────────────────────────── */
.pro-badge {{
    display: inline-block;
    background: var(--slg-grad-primary);
    color: #ffffff; font-size: 0.66rem; font-weight: 800;
    letter-spacing: 0.10em; text-transform: uppercase;
    padding: 2px 9px; border-radius: 20px; margin-left: 6px;
    vertical-align: middle; box-shadow: 0 2px 8px rgba(5,150,105,0.30);
}}

/* ── Workflow cards ──────────────────────────────────────────── */
.workflow-card {{
    border-left: 4px solid {PRIMARY_LIGHT};
    padding: 1.05rem 1.15rem;
}}
.workflow-card .workflow-icon {{ display: block; font-size: 1.7rem; margin-bottom: 0.45rem; line-height: 1; }}
.workflow-card .workflow-title {{
    display: block;
    font-family: 'Space Grotesk','Inter',sans-serif;
    font-weight: 700; color: {INK}; margin-bottom: 0.35rem; font-size: 0.98rem; letter-spacing: -0.01em;
}}
.workflow-card .workflow-body {{ display: block; color: {MUTED}; font-size: 0.86rem; line-height: 1.6; }}

/* ── Clickable card variants (link cards on home dashboard) ─── */
a.feature-card--link, a.workflow-card--link,
a.feature-card--link:visited, a.workflow-card--link:visited {{
    display: flex;
    flex-direction: column;
    text-decoration: none !important;
    color: inherit !important;
    cursor: pointer;
    position: relative;
}}
a.feature-card--link:hover, a.workflow-card--link:hover {{
    border-color: {PRIMARY} !important;
    box-shadow: 0 10px 28px rgba(5, 150, 105, 0.18) !important;
    transform: translateY(-3px);
    text-decoration: none !important;
}}
a.feature-card--link:focus-visible, a.workflow-card--link:focus-visible {{
    outline: 2px solid {PRIMARY};
    outline-offset: 3px;
}}
.feature-card-cta, .workflow-card-cta {{
    display: inline-flex;
    align-items: center;
    margin-top: auto;
    padding-top: 0.6rem;
    color: {PRIMARY};
    font-weight: 700;
    font-size: 0.78rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    opacity: 0.85;
    transition: opacity 0.15s ease, transform 0.15s ease;
}}
a.feature-card--link:hover .feature-card-cta,
a.workflow-card--link:hover .workflow-card-cta {{
    opacity: 1;
    transform: translateX(2px);
}}
"""


