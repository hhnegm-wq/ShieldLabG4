"""ShieldLab G4 — ISIP-faithful visual theme injector.

This module is the single public entry-point for stylesheet injection.
CSS is assembled from governed design-system layers:

  style_tokens.py        — color/shadow/scale constants
  style_surface.py       — hero banners, feature/workflow cards, stat blocks
  style_data_display.py  — tables, benchmark cards, chart framing
  style_shell.py         — KPI strips, topbar, user card, enterprise chrome
"""
from __future__ import annotations

import streamlit as st

from shieldlab.metadata import COPYRIGHT_OWNER, PRODUCT_NAME, platform_footer_text
from components.platform_settings import get_platform_settings
from components.style_tokens import (  # noqa: F401
    GREEN_50, GREEN_100, GREEN_200, GREEN_300, GREEN_400,
    PRIMARY, PRIMARY_LIGHT, PRIMARY_MID, PRIMARY_MED, PRIMARY_DARK,
    BLUE_500, BLUE_600, PURPLE_500, GOLD_500,
    SURFACE, SURFACE_2, SURFACE_3,
    INK, INK_SOFT, MUTED, MUTED_LIGHT,
    BG_PAGE, BG_PAGE_END,
    BORDER, BORDER_MED, BORDER_GREEN, BORDER_GREEN2,
    SHADOW_SM, SHADOW_MD, SHADOW_LG,
    DANGER, SUCCESS, WARN,
    _FONT_SCALE, _WIDTH_SCALE, _DENSITY,
)
from components.style_surface import _build_surface_component_css
from components.style_data_display import _build_data_display_css
from components.style_shell import _build_shell_component_css, _build_shell_chrome_css


def _build_css(settings: dict[str, object]) -> str:  # noqa: PLR0912
    font_scale   = _FONT_SCALE.get(str(settings.get("font_size",       "medium")), 1.0)
    width        = _WIDTH_SCALE.get(str(settings.get("content_width",  "wide")),   "1480px")
    density      = _DENSITY.get(str(settings.get("content_density", "comfortable")), _DENSITY["comfortable"])

    body_font    = f"{1.00 * font_scale:.3f}rem"
    h1_font      = f"clamp(1.75rem, 2.3vw, {2.2 * font_scale:.2f}rem)"
    h2_font      = f"clamp(1.25rem, 1.6vw, {1.5 * font_scale:.2f}rem)"
    h3_font      = f"{1.10 * font_scale:.3f}rem"
    metric_val   = f"{1.25 * font_scale:.3f}rem"
    sidebar_font = f"{0.83 * font_scale:.3f}rem"
    caption_font = f"{0.83 * font_scale:.3f}rem"
    table_font   = f"{0.86 * font_scale:.3f}rem"
    stat_font    = f"{2.2  * font_scale:.3f}rem"
    small_label  = f"{0.72 * font_scale:.3f}rem"

    shell_mode = str(settings.get("shell_mode", "enterprise"))

    shell_css = _build_shell_component_css(metric_val, small_label) + _build_shell_chrome_css(shell_mode)
    return f"""<style>
/* ====================================================================
   ShieldLab G4 · ISIP Visual System
   Tokens: D:/projects/ISIP/platform/src/app/globals.css
           D:/projects/ISIP/platform/tailwind.config.js
   Components: KPICard, Card, DataTable, Tabs, Sidebar, Header
   ==================================================================== */

/* Fonts — ISIP uses Inter (body), system for sans. We add Space Grotesk for
   display headings and IBM Plex Mono for code, matching ISIP's next.js layout */
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;0,14..32,800&family=Space+Grotesk:wght@500;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* CSS variables — ISIP :root block */
:root {{
    --isip-green-50:  {GREEN_50};
    --isip-green-100: {GREEN_100};
    --isip-green-200: {GREEN_200};
    --isip-green-300: {GREEN_300};
    --isip-green-400: {GREEN_400};
    --isip-green-500: {PRIMARY_LIGHT};
    --isip-green-600: {PRIMARY};
    --isip-green-700: {PRIMARY_MED};
    --isip-green-800: {PRIMARY_MID};
    --isip-green-900: {PRIMARY_DARK};
    --isip-blue-500:  {BLUE_500};
    --isip-blue-600:  {BLUE_600};
    --isip-purple-500:{PURPLE_500};
    --isip-gold-500:  {GOLD_500};
    /* Surfaces */
    --slg-bg:         {BG_PAGE};
    --slg-surface:    {SURFACE};
    --slg-surface-2:  {SURFACE_2};
    --slg-surface-3:  {SURFACE_3};
    /* Typography */
    --slg-ink:        {INK};
    --slg-ink-soft:   {INK_SOFT};
    --slg-muted:      {MUTED};
    --slg-muted-lt:   {MUTED_LIGHT};
    /* Borders */
    --slg-border:     {BORDER};
    --slg-border-md:  {BORDER_MED};
    --slg-border-g:   {BORDER_GREEN};
    --slg-border-g2:  {BORDER_GREEN2};
    /* Shadows */
    --slg-shadow-sm:  {SHADOW_SM};
    --slg-shadow-md:  {SHADOW_MD};
    --slg-shadow-lg:  {SHADOW_LG};
    /* Gradients */
    --slg-grad-primary:  linear-gradient(135deg, {PRIMARY_DARK} 0%, {PRIMARY} 45%, {PRIMARY_LIGHT} 100%);
    --slg-grad-sidebar:  linear-gradient(180deg, {PRIMARY_DARK} 0%, {PRIMARY_MID} 40%, {PRIMARY_MED} 100%);
    --slg-grad-green:    linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_LIGHT} 100%);
    --slg-grad-hero:     linear-gradient(135deg, {PRIMARY_DARK} 0%, #1e3a8a 50%, #4c1d95 100%);
    /* Radii */
    --slg-r-sm: 8px;
    --slg-r-md: 12px;
    --slg-r-lg: 16px;
    --slg-r-xl: 20px;
}}

/* ── Global reset ─────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; }}
html, body, [class*="css"] {{
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: {body_font};
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
    font-feature-settings: 'cv11','ss01','ss03','tnum';
}}
h1, h2, h3, h4, h5, h6,
.shieldlab-hero-title,
.stat-number, .sl-enterprise-kpi-card-value,
[data-testid="stHeading"] h1, [data-testid="stHeading"] h2,
[data-testid="stHeading"] h3, [data-testid="stHeading"] h4,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {{
    font-family: 'Space Grotesk', 'Inter', system-ui, sans-serif !important;
    letter-spacing: -0.02em;
}}
code, pre, kbd, samp,
.stCode, [data-testid="stCode"],
.path-value, .lit-benchmark-meta {{
    font-family: 'IBM Plex Mono', 'JetBrains Mono', 'Cascadia Mono', ui-monospace, monospace;
}}

/* ── App background — ISIP body gradient ─────────────────────── */
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(to bottom, {BG_PAGE}, {BG_PAGE_END});
}}
[data-testid="stAppViewContainer"] > .main {{
    background:
        radial-gradient(ellipse 70% 42% at 100% 0%,  rgba(5,150,105,0.07) 0%, transparent 55%),
        radial-gradient(ellipse 55% 35% at 0%   2%,  rgba(16,185,129,0.05) 0%, transparent 50%),
        linear-gradient(180deg, {BG_PAGE} 0%, {BG_PAGE_END} 100%);
}}

/* ── Streamlit native header — make transparent so the shell topbar
       sits flush at the top. Deploy button + overflow menu are hidden
       in enterprise mode (not relevant to users). ── */
[data-testid="stHeader"] {{
    background: transparent !important;
    height: 2.25rem !important;
    min-height: 0 !important;
}}
[data-testid="stHeader"]::before {{ display: none !important; }}
[data-testid="stToolbar"] {{ right: 0.25rem; top: 0.25rem; }}
[data-testid="stDecoration"] {{ display: none !important; }}
/* Hide the "Deploy" button and ⋮ overflow menu — not useful in production */
[data-testid="stDeployButton"],
[data-testid="stToolbarActionButtonLabel"],
button[kind="header"] {{
    display: none !important;
}}

/* ── Block container ─────────────────────────────────────────── */
.main .block-container {{
    padding-top:    {density['block_top']};
    padding-bottom: {density['block_bottom']};
    max-width: {width};
}}

/* ── Scrollbar — ISIP green gradient thumb ───────────────────── */
::-webkit-scrollbar          {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-track    {{ background: {BG_PAGE_END}; border-radius: 4px; }}
::-webkit-scrollbar-thumb    {{ background: linear-gradient(180deg, {PRIMARY_LIGHT} 0%, {PRIMARY} 100%);
                                border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: linear-gradient(180deg, {PRIMARY} 0%, {PRIMARY_MED} 100%); }}

/* ── Sidebar — ISIP isip-sidebar-gradient (faithful) ─────────── */
/* ISIP source: linear-gradient(180deg,#064e3b 0%, #065f46 40%, #047857 100%);
   w-64 (256px), border-r border-white/10, no extra shadow. */
section[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"],
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {PRIMARY_DARK} 0%, {PRIMARY_MID} 40%, {PRIMARY_MED} 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: none !important;
}}
/* Remove decorative radial overlays — ISIP has flat gradient */
section[data-testid="stSidebar"]::before,
[data-testid="stSidebar"] > div::before {{
    content: none !important;
    display: none !important;
}}
/* All sidebar text inherits green-50 by default */
section[data-testid="stSidebar"] *,
[data-testid="stSidebar"] * {{
    color: {GREEN_50};
}}

/* ── Sidebar header (logo area) — ISIP wordmark via CSS injection ──
 * Hide the raw logo image (it's a white-background PNG that clashes with the
 * dark green gradient) and replace the header content with an ISIP-style
 * brand strip: shield SVG + "ShieldLab." wordmark + tagline. */
[data-testid="stSidebarHeader"] {{
    position: relative !important;
    min-height: 4rem !important;
    padding: 0.75rem 0.9rem !important;
    border-bottom: 1px solid rgba(255,255,255,0.10) !important;
    margin-bottom: 0.35rem !important;
    background: transparent !important;
    display: flex !important;
    align-items: center !important;
}}
/* Hide the raw <img> logo (white background looks wrong on green gradient) */
[data-testid="stSidebarHeader"] [data-testid="stLogo"],
[data-testid="stSidebarHeader"] img {{
    display: none !important;
}}
/* Inject brand icon (shield SVG) + wordmark via pseudo-elements.
 * NOTE: %23 = '#' URL-encoded. */
[data-testid="stSidebarHeader"]::before {{
    content: "";
    display: inline-block;
    flex-shrink: 0;
    width: 2.2rem;
    height: 2.2rem;
    border-radius: 10px;
    background:
        url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'/></svg>") center / 60% 60% no-repeat,
        linear-gradient(135deg, {GREEN_400} 0%, {PRIMARY} 100%);
    box-shadow: 0 4px 10px rgba(5,150,105,0.30), inset 0 1px 0 rgba(255,255,255,0.20);
    margin-right: 0.7rem;
}}
[data-testid="stSidebarHeader"]::after {{
    content: "ShieldLab.\\A Nuclear Shielding Intelligence";
    white-space: pre;
    font-family: 'Space Grotesk', 'Inter', sans-serif;
    font-weight: 800;
    font-size: 1.05rem;
    line-height: 1.15;
    letter-spacing: -0.02em;
    color: #ffffff;
    -webkit-text-fill-color: #ffffff;
    flex: 1 1 auto;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
}}
/* Keep the collapse button visible — pin top-right so it doesn't split the wordmark */
[data-testid="stSidebarHeader"] [data-testid="stSidebarCollapseButton"] {{
    position: absolute !important;
    top: 0.45rem !important;
    right: 0.45rem !important;
    z-index: 2 !important;
    margin: 0 !important;
}}
[data-testid="stSidebarHeader"] [data-testid="stSidebarCollapseButton"] button {{
    background: rgba(255,255,255,0.10) !important;
    color: rgba(255,255,255,0.85) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    width: 1.85rem !important;
    height: 1.85rem !important;
    padding: 0 !important;
}}
[data-testid="stSidebarHeader"] [data-testid="stSidebarCollapseButton"] button:hover {{
    background: rgba(255,255,255,0.18) !important;
    color: #ffffff !important;
}}
/* Add right padding to header so wordmark doesn't go under the pinned collapse button */
[data-testid="stSidebarHeader"] {{
    padding-right: 2.6rem !important;
}}
[data-testid="stSidebarHeader"]::after {{
    padding-right: 0.2rem;
}}

/* ── Section group headers ("Simulation", "Analysis", …)
       ISIP equivalent: subtle uppercase divider. */
[data-testid="stNavSectionHeader"] {{
    padding: 0.85rem 0.9rem 0.35rem !important;
    margin: 0.35rem 0 0.15rem !important;
    background: transparent !important;
    border: 0 !important;
    border-top: 1px solid rgba(255,255,255,0.08) !important;
    color: rgba(255,255,255,0.55) !important;
    font-family: 'Space Grotesk', 'Inter', sans-serif !important;
    font-size: 0.66rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    cursor: pointer;
}}
[data-testid="stNavSectionHeader"] p,
[data-testid="stNavSectionHeader"] span {{
    color: rgba(255,255,255,0.55) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.55) !important;
    font-size: 0.66rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}}
[data-testid="stNavSectionHeader"]:hover p,
[data-testid="stNavSectionHeader"]:hover span {{
    color: rgba(255,255,255,0.85) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.85) !important;
}}
[data-testid="stNavSectionHeader"] [data-testid="stIconMaterial"] {{
    color: rgba(255,255,255,0.45) !important;
    font-size: 1.05rem !important;
}}

/* ── Nav link list rhythm */
[data-testid="stSidebarNav"] ul {{
    padding: 0 0.55rem !important;
    margin: 0 !important;
    list-style: none !important;
}}
[data-testid="stSidebarNav"] li {{
    margin: 2px 0 !important;
    padding: 0 !important;
    list-style: none !important;
}}

/* ── Nav link — ISIP: flex gap-3 px-3 py-2.5 rounded-lg
       inactive: text-white/70, hover: bg-white/10 text-white
       active:   bg-white/15 text-white */
[data-testid="stSidebarNavLink"],
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {{
    display: flex !important;
    align-items: center !important;
    gap: 0.7rem !important;
    padding: 0.55rem 0.75rem !important;
    border-radius: 8px !important;
    border: 0 !important;
    border-left: 0 !important;
    background: transparent !important;
    color: rgba(255,255,255,0.72) !important;
    font-weight: 500 !important;
    font-size: {sidebar_font} !important;
    line-height: 1.2 !important;
    text-decoration: none !important;
    transition: background-color 0.16s ease, color 0.16s ease !important;
    position: relative;
}}
[data-testid="stSidebarNavLink"] p,
[data-testid="stSidebarNavLink"] span {{
    color: inherit !important;
    -webkit-text-fill-color: currentColor !important;
    font-weight: inherit !important;
    margin: 0 !important;
}}
/* Material Symbols icons — clean monochrome ISIP/lucide aesthetic */
[data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {{
    flex-shrink: 0;
    width: 1.25rem;
    height: 1.25rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined' !important;
    font-size: 1.25rem !important;
    line-height: 1 !important;
    color: rgba(255,255,255,0.72) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.72) !important;
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    transition: color 0.16s ease, font-variation-settings 0.16s ease;
}}
/* Legacy emoji icons (if any remain) — keep small/aligned */
[data-testid="stSidebarNavLink"] [data-testid="stIconEmoji"] {{
    flex-shrink: 0;
    width: 1.25rem;
    height: 1.25rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.05rem !important;
    line-height: 1 !important;
    opacity: 0.95;
}}
[data-testid="stSidebarNavLink"]:hover {{
    background: rgba(255,255,255,0.10) !important;
    color: #ffffff !important;
}}
[data-testid="stSidebarNavLink"]:hover [data-testid="stIconMaterial"] {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}}
[data-testid="stSidebarNavLink"]:hover [data-testid="stIconEmoji"] {{ opacity: 1; }}

/* Active item — ISIP bg-white/15, white text, gold icon */
[data-testid="stSidebarNavLink"][aria-current="page"],
[data-testid="stSidebarNavLink"].active,
[data-testid="stSidebarNavLink"][aria-selected="true"] {{
    background: rgba(255,255,255,0.15) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06) !important;
}}
[data-testid="stSidebarNavLink"][aria-current="page"] [data-testid="stIconMaterial"],
[data-testid="stSidebarNavLink"][aria-selected="true"] [data-testid="stIconMaterial"] {{
    color: {GOLD_500} !important;
    -webkit-text-fill-color: {GOLD_500} !important;
    font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}}
[data-testid="stSidebarNavLink"][aria-current="page"] [data-testid="stIconEmoji"],
[data-testid="stSidebarNavLink"][aria-selected="true"] [data-testid="stIconEmoji"] {{
    filter: drop-shadow(0 0 6px rgba(245,158,11,0.45));
    opacity: 1;
}}
/* Subtle left rail accent for active (3px gold) — ISIP refinement */
[data-testid="stSidebarNavLink"][aria-current="page"]::before,
[data-testid="stSidebarNavLink"][aria-selected="true"]::before {{
    content: "";
    position: absolute;
    left: 0;
    top: 18%;
    bottom: 18%;
    width: 3px;
    border-radius: 0 3px 3px 0;
    background: {GOLD_500};
}}

/* Sidebar form labels (selectboxes, sliders) */
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stSlider label {{
    color: rgba(255,255,255,0.85) !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}}

/* Sidebar scrollbar — slim, subtle */
[data-testid="stSidebarNav"],
[data-testid="stSidebarContent"] {{
    scrollbar-width: thin;
    scrollbar-color: rgba(255,255,255,0.20) transparent;
}}
[data-testid="stSidebarNav"]::-webkit-scrollbar,
[data-testid="stSidebarContent"]::-webkit-scrollbar {{ width: 5px; }}
[data-testid="stSidebarNav"]::-webkit-scrollbar-track,
[data-testid="stSidebarContent"]::-webkit-scrollbar-track  {{ background: transparent; }}
[data-testid="stSidebarNav"]::-webkit-scrollbar-thumb,
[data-testid="stSidebarContent"]::-webkit-scrollbar-thumb  {{
    background: rgba(255,255,255,0.18);
    border-radius: 6px;
}}
[data-testid="stSidebarNav"]::-webkit-scrollbar-thumb:hover,
[data-testid="stSidebarContent"]::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.32); }}

/* Sidebar collapse/expand button (Streamlit chevron) */
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapsedControl"] button {{
    color: rgba(255,255,255,0.75) !important;
    background: rgba(255,255,255,0.06) !important;
    border-radius: 8px !important;
    transition: background 0.16s ease, color 0.16s ease !important;
}}
[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="stSidebarCollapsedControl"] button:hover {{
    background: rgba(255,255,255,0.14) !important;
    color: #ffffff !important;
}}

/* ── Typography — ISIP heading hierarchy ──────────────────────── */
h1 {{
    font-size: {h1_font} !important;
    font-weight: 800 !important;
    color: {INK} !important;
    -webkit-text-fill-color: {INK} !important;
    /* gradient display text for page h1s */
    background: var(--slg-grad-primary) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    margin-bottom: 0.35rem !important;
}}
[data-testid="stHeadingWithActionElements"] h1,
[data-testid="stHeading"] h1 {{
    background: var(--slg-grad-primary) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}}
h2 {{
    font-size: {h2_font} !important;
    font-weight: 700 !important;
    color: {INK} !important;
    -webkit-text-fill-color: {INK} !important;
    border-bottom: 1px solid {BORDER_MED} !important;
    padding-bottom: 0.45rem !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.9rem !important;
}}
[data-testid="stHeading"] h2 {{
    color: {INK} !important;
    -webkit-text-fill-color: {INK} !important;
}}
h3 {{
    font-size: {h3_font} !important;
    font-weight: 700 !important;
    color: {PRIMARY_DARK} !important;
    -webkit-text-fill-color: {PRIMARY_DARK} !important;
    margin-top: 1.1rem !important;
    margin-bottom: 0.5rem !important;
}}
h3::after {{
    content: "";
    display: block;
    width: 2rem;
    height: 2px;
    margin-top: 0.28rem;
    border-radius: 999px;
    background: var(--slg-grad-green);
}}
[data-testid="stHeading"] h3 {{
    color: {PRIMARY_DARK} !important;
    -webkit-text-fill-color: {PRIMARY_DARK} !important;
}}
/* Body text */
.main p,
.main li,
.main [data-testid="stMarkdownContainer"] p,
.main [data-testid="stCaptionContainer"] p {{
    color: {INK_SOFT} !important;
    -webkit-text-fill-color: {INK_SOFT} !important;
    font-size: {body_font} !important;
}}

/* ── Metric cards — ISIP KPICard / StatCard pattern ─────────── */
[data-testid="metric-container"] {{
    background: {SURFACE} !important;
    border: 1px solid {BORDER} !important;
    border-top: 3px solid {PRIMARY} !important;
    border-radius: var(--slg-r-md) !important;
    padding: 1rem 1.1rem 0.85rem !important;
    box-shadow: var(--slg-shadow-sm) !important;
    transition: box-shadow 0.22s ease, transform 0.22s ease, border-color 0.22s ease !important;
}}
[data-testid="metric-container"]:hover {{
    box-shadow: var(--slg-shadow-md) !important;
    transform: translateY(-2px) !important;
    border-top-color: {PRIMARY_LIGHT} !important;
}}
[data-testid="metric-container"] [data-testid="stMetricLabel"],
[data-testid="metric-container"] label {{
    font-size: {small_label} !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: {MUTED} !important;
    -webkit-text-fill-color: {MUTED} !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: {metric_val} !important;
    font-weight: 800 !important;
    color: {INK} !important;
    -webkit-text-fill-color: {INK} !important;
    letter-spacing: -0.02em !important;
    line-height: 1.2 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
    word-break: break-word !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] p,
[data-testid="metric-container"] [data-testid="stMetricValue"] div {{
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
    word-break: break-word !important;
}}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {{
    font-size: {0.78 * font_scale:.3f}rem !important;
    margin-top: 0.18rem !important;
}}

/* ── Tabs — ISIP underline variant ──────────────────────────── */
/* Container: border-b border-gray-200 */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0 !important;
    border-bottom: 2px solid {BORDER_MED} !important;
    background: transparent !important;
    padding-bottom: 0 !important;
    margin-bottom: 0.2rem !important;
}}
/* Inactive tab: text-gray-500 hover:text-gray-700 */
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    padding: {density['tab_pad']} !important;
    font-size: {caption_font} !important;
    font-weight: 500 !important;
    color: {MUTED} !important;
    -webkit-text-fill-color: {MUTED} !important;
    letter-spacing: 0.01em !important;
    margin-bottom: -2px !important;
    box-shadow: none !important;
    transition: color 0.15s ease, border-color 0.15s ease, background 0.15s ease !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
    background: rgba(5,150,105,0.05) !important;
    color: {INK_SOFT} !important;
    -webkit-text-fill-color: {INK_SOFT} !important;
    border-bottom-color: {BORDER_MED} !important;
}}
.stTabs [data-baseweb="tab"] p,
.stTabs [data-baseweb="tab"] span {{ color: inherit !important; -webkit-text-fill-color: inherit !important; font-weight: inherit !important; }}
/* Active tab: border-b-2 border-isip-green-600 text-isip-green-600 */
.stTabs [aria-selected="true"] {{
    background: transparent !important;
    color: {PRIMARY} !important;
    -webkit-text-fill-color: {PRIMARY} !important;
    border-bottom: 2px solid {PRIMARY} !important;
    font-weight: 700 !important;
    box-shadow: none !important;
}}
.stTabs [aria-selected="true"] p,
.stTabs [aria-selected="true"] span,
.stTabs [aria-selected="true"] div {{
    color: {PRIMARY} !important;
    -webkit-text-fill-color: {PRIMARY} !important;
}}
/* Tab content panel — breathing room below the tab bar */
.stTabs [data-baseweb="tab-panel"] {{
    padding-top: 1rem !important;
}}

/* ── Buttons — ISIP isip-btn-primary pattern ─────────────────── */
.stButton > button {{
    transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, border-color 0.18s ease;
    white-space: nowrap !important;
}}
.stButton > button:active {{ transform: scale(0.97) !important; }}
/* primary: bg-isip-green-600 hover:bg-isip-green-700 text-white rounded-lg shadow-sm */
.stButton > button[kind="primary"] {{
    background: {PRIMARY} !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: none !important;
    border-radius: var(--slg-r-sm) !important;
    font-weight: 700 !important;
    padding: 0.55rem 1.3rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.08), 0 4px 10px rgba(5,150,105,0.25) !important;
    letter-spacing: 0.01em !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: {PRIMARY_MED} !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.10), 0 8px 18px rgba(5,150,105,0.30) !important;
    transform: translateY(-1px) !important;
}}
/* secondary */
.stButton > button[kind="secondary"] {{
    background: {SURFACE} !important;
    color: {PRIMARY_DARK} !important;
    -webkit-text-fill-color: {PRIMARY_DARK} !important;
    border: 1.5px solid {BORDER_GREEN} !important;
    border-radius: var(--slg-r-sm) !important;
    font-weight: 600 !important;
}}
.stButton > button[kind="secondary"]:hover {{
    background: {GREEN_50} !important;
    border-color: {PRIMARY} !important;
    box-shadow: 0 0 0 3px rgba(5,150,105,0.12) !important;
}}
/* default / tertiary */
.stButton > button:not([kind="primary"]):not([kind="secondary"]) {{
    background: {SURFACE} !important;
    border: 1px solid {BORDER_MED} !important;
    border-radius: var(--slg-r-sm) !important;
    color: {INK_SOFT} !important;
    -webkit-text-fill-color: {INK_SOFT} !important;
    font-weight: 500 !important;
}}
.stButton > button:not([kind="primary"]):not([kind="secondary"]):hover {{
    background: {GREEN_50} !important;
    border-color: {BORDER_GREEN} !important;
    color: {PRIMARY_DARK} !important;
    -webkit-text-fill-color: {PRIMARY_DARK} !important;
}}
.stButton > button:disabled {{
    opacity: 0.45 !important;
}}
.stDownloadButton > button {{
    background: {SURFACE} !important;
    color: {PRIMARY_DARK} !important;
    -webkit-text-fill-color: {PRIMARY_DARK} !important;
    border: 1.5px solid {BORDER_GREEN} !important;
    border-radius: var(--slg-r-sm) !important;
    font-weight: 600 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease !important;
}}
.stDownloadButton > button:hover {{
    background: {GREEN_50} !important;
    border-color: {PRIMARY} !important;
    box-shadow: 0 0 0 3px rgba(5,150,105,0.12) !important;
}}
.stDownloadButton > button:disabled {{
    opacity: 0.45 !important;
}}

/* ── Input controls — ISIP form fields ──────────────────────── */
/* Outer wrapper carries border / radius (modern Streamlit puts border here) */
[data-testid="stTextInputRootElement"],
[data-testid="stNumberInputContainer"],
div[data-baseweb="input"],
div[data-baseweb="textarea"] {{
    background: {SURFACE} !important;
    border: 1.5px solid {BORDER_MED} !important;
    border-radius: var(--slg-r-sm) !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
    overflow: hidden !important;
}}
[data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stNumberInputContainer"]:focus-within,
div[data-baseweb="input"]:focus-within,
div[data-baseweb="textarea"]:focus-within {{
    border-color: {PRIMARY} !important;
    box-shadow: 0 0 0 3px rgba(5,150,105,0.15) !important;
}}
/* Inner input element strips its own borders */
[data-baseweb="base-input"],
[data-baseweb="base-input"] input,
[data-baseweb="base-input"] textarea,
.stTextInput input, .stNumberInput input, .stTextArea textarea {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: {INK_SOFT} !important;
    -webkit-text-fill-color: {INK_SOFT} !important;
    font-size: {body_font} !important;
}}
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {{
    background: {SURFACE} !important;
    color: {INK_SOFT} !important;
    -webkit-text-fill-color: {INK_SOFT} !important;
    border: 1.5px solid {BORDER_MED} !important;
    border-radius: var(--slg-r-sm) !important;
    font-size: {body_font} !important;
    transition: border-color 0.15s, box-shadow 0.15s;
}}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color: {PRIMARY} !important;
    box-shadow: 0 0 0 3px rgba(5,150,105,0.15) !important;
    outline: none !important;
}}
/* Select controls */
.main .stSelectbox > div > div > div,
.main div[data-baseweb="select"] > div,
div[data-baseweb="select"] > div {{
    background: {SURFACE} !important;
    border: 1.5px solid {BORDER_MED} !important;
    border-radius: var(--slg-r-sm) !important;
    color: {INK_SOFT} !important;
    -webkit-text-fill-color: {INK_SOFT} !important;
    min-height: 40px !important;
}}
.main div[data-baseweb="select"]:focus-within > div,
.main .stSelectbox > div > div:focus-within > div {{
    border-color: {PRIMARY} !important;
    box-shadow: 0 0 0 3px rgba(5,150,105,0.15) !important;
}}
/* All text inside selects */
div[data-baseweb="select"] input,
div[data-baseweb="select"] span,
[data-baseweb="select"] [role="combobox"],
div[data-baseweb="input"] input {{
    color: {INK_SOFT} !important;
    -webkit-text-fill-color: {INK_SOFT} !important;
    background: transparent !important;
}}
div[data-baseweb="select"] svg {{ fill: {MUTED} !important; color: {MUTED} !important; }}
/* Dropdown menus */
[data-baseweb="popover"],
[data-baseweb="select"] [role="listbox"],
[data-baseweb="menu"] {{
    background: {SURFACE} !important;
    border: 1px solid {BORDER_MED} !important;
    border-radius: var(--slg-r-md) !important;
    box-shadow: var(--slg-shadow-md) !important;
}}
[data-baseweb="menu"] *             {{ color: {INK_SOFT} !important; }}
[data-baseweb="option"]:hover,
[data-baseweb="menu"] li:hover      {{ background: {GREEN_50} !important; color: {PRIMARY_DARK} !important; }}
/* Tags / multiselect chips */
[data-baseweb="tag"] {{
    background: {GREEN_50} !important;
    border: 1px solid {GREEN_200} !important;
    border-radius: 6px !important;
    margin: 0.1rem 0.25rem 0.1rem 0 !important;
}}
[data-baseweb="tag"] span {{
    color: {PRIMARY_MID} !important;
    -webkit-text-fill-color: {PRIMARY_MID} !important;
    font-size: 0.80rem !important;
    font-weight: 600 !important;
}}
/* Labels */
.main .stSelectbox label,
.main .stTextInput label,
.main .stNumberInput label,
.main .stTextArea label,
.main .stDateInput label,
.main .stRadio label,
.main .stCheckbox label {{
    color: {INK} !important;
    -webkit-text-fill-color: {INK} !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.01em !important;
    display: block !important;
    margin-bottom: 0.3rem !important;
}}
[data-testid="stCheckbox"] label {{ color: {INK_SOFT} !important; -webkit-text-fill-color: {INK_SOFT} !important; font-size: {caption_font}; }}
[data-testid="stRadio"] label    {{ color: {INK_SOFT} !important; -webkit-text-fill-color: {INK_SOFT} !important; font-size: {caption_font}; }}
/* Slider */
[data-testid="stSlider"] [role="slider"] {{
    background: {PRIMARY} !important;
    box-shadow: 0 0 0 3px rgba(5,150,105,0.20) !important;
}}
/* Number input stepper buttons */
[data-testid="stNumberInput"] button {{
    background: {GREEN_50} !important;
    color: {PRIMARY_DARK} !important;
    -webkit-text-fill-color: {PRIMARY_DARK} !important;
    border: 1px solid {GREEN_200} !important;
    border-radius: 6px !important;
}}
[data-testid="stNumberInput"] button:hover {{
    background: {GREEN_100} !important;
    border-color: {PRIMARY} !important;
}}

/* ── Expander — ISIP Card default variant ─────────────────────── */
details {{
    background: {SURFACE} !important;
    border: 1px solid {BORDER} !important;
    border-radius: var(--slg-r-md) !important;
    box-shadow: var(--slg-shadow-sm) !important;
    margin-bottom: 0.65rem;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}}
details:hover {{
    border-color: {BORDER_GREEN} !important;
    box-shadow: var(--slg-shadow-md) !important;
}}
details summary {{
    background: linear-gradient(90deg, {GREEN_50} 0%, rgba(236,253,245,0) 100%) !important;
    color: {INK} !important;
    -webkit-text-fill-color: {INK} !important;
    border-left: 3px solid {PRIMARY} !important;
    padding: {density['exp_pad']} !important;
    border-radius: var(--slg-r-sm) !important;
    font-weight: 650 !important;
    cursor: pointer;
    transition: background 0.15s ease;
}}
details summary:hover {{
    background: linear-gradient(90deg, {GREEN_100} 0%, {GREEN_50} 60%, rgba(236,253,245,0) 100%) !important;
}}
details summary p,
details summary span {{ color: {INK} !important; -webkit-text-fill-color: {INK} !important; }}
[data-testid="stExpander"] details {{ border-color: {BORDER} !important; }}
[data-testid="stExpander"] details summary {{ border-radius: var(--slg-r-sm) !important; }}

/* ── DataTable / DataFrame — ISIP DataTable pattern ─────────── */
[data-testid="stDataFrame"] table {{
    background: {SURFACE} !important;
    border-collapse: collapse;
    font-size: {table_font};
    border-radius: var(--slg-r-sm);
    overflow: hidden;
}}
/* Header: bg-gradient from isip-green-600 to isip-green-900 text-white */
[data-testid="stDataFrame"] th {{
    background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 700 !important;
    font-size: {0.78 * font_scale:.3f}rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    padding: 9px 11px !important;
    border-bottom: none !important;
}}
[data-testid="stDataFrame"] td {{
    color: {INK_SOFT} !important;
    -webkit-text-fill-color: {INK_SOFT} !important;
    border-bottom: 1px solid {BORDER} !important;
    font-variant-numeric: tabular-nums;
    padding: 7px 11px !important;
    font-size: {table_font};
}}
/* Even row: rgba(isip-green-50, 0.5) */
[data-testid="stDataFrame"] tr:nth-child(even) td {{ background: rgba(236,253,245,0.50) !important; }}
/* Hover row: isip-green-100 */
[data-testid="stDataFrame"] tr:hover td {{ background: {GREEN_100} !important; }}

/* ── Alert banners — ISIP notification cards ─────────────────── */
[data-testid="stAlert"] {{
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0.4rem 0 !important;
}}
[data-testid="stAlertContainer"] {{
    background: {SURFACE} !important;
    border: 1px solid {BORDER_MED} !important;
    border-left: 4px solid {BORDER_MED} !important;
    border-radius: var(--slg-r-md) !important;
    box-shadow: var(--slg-shadow-sm) !important;
    padding: 0.85rem 1rem !important;
}}
[data-testid="stAlertContainer"] * {{
    color: {INK_SOFT} !important;
    -webkit-text-fill-color: {INK_SOFT} !important;
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {{
    border-left-color: {BLUE_500} !important;
    background: linear-gradient(90deg, #eff6ff 0%, {SURFACE} 70%) !important;
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {{
    border-left-color: {GOLD_500} !important;
    background: linear-gradient(90deg, #fffbeb 0%, {SURFACE} 70%) !important;
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {{
    border-left-color: {PRIMARY} !important;
    background: linear-gradient(90deg, {GREEN_50} 0%, {SURFACE} 70%) !important;
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {{
    border-left-color: {DANGER} !important;
    background: linear-gradient(90deg, #fef2f2 0%, {SURFACE} 70%) !important;
}}
/* Alert icon tinting per kind */
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) svg    {{ fill: {BLUE_500} !important; color: {BLUE_500} !important; }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) svg {{ fill: {GOLD_500} !important; color: {GOLD_500} !important; }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) svg {{ fill: {PRIMARY} !important; color: {PRIMARY} !important; }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) svg   {{ fill: {DANGER} !important; color: {DANGER} !important; }}

/* ── Divider ─────────────────────────────────────────────────── */
hr {{
    border: none !important;
    height: 1px !important;
    background: {BORDER_MED} !important;
    margin: 1.5rem 0 !important;
}}

/* ── Code blocks ─────────────────────────────────────────────── */
code {{
    background: {GREEN_50} !important;
    color: {PRIMARY_DARK} !important;
    border: 1px solid {GREEN_200} !important;
    border-radius: 5px !important;
    padding: 1px 6px !important;
    font-size: {caption_font};
}}
pre {{
    background: #0b1a2c !important;
    color: #d1fae5 !important;
    border-radius: var(--slg-r-sm) !important;
    border-left: 3px solid {PRIMARY} !important;
    padding: 0.9rem 1.1rem !important;
}}
pre code {{ background: transparent !important; color: inherit !important; border: none !important; }}

/* ── Progress ────────────────────────────────────────────────── */
[data-testid="stProgressBar"] > div > div {{
    background: linear-gradient(90deg, {PRIMARY} 0%, {PRIMARY_LIGHT} 100%) !important;
}}
[data-testid="stSpinner"] {{ color: {PRIMARY} !important; }}

{_build_surface_component_css(font_scale, caption_font, stat_font)}

{_build_data_display_css(font_scale, caption_font)}

/* ── Platform footer ─────────────────────────────────────────── */
.platform-footer {{
    margin-top: 2.2rem;
    padding: 1.1rem 1.4rem;
    background: var(--slg-grad-primary) !important;
    border-radius: var(--slg-r-md) !important;
    color: {GREEN_100} !important;
    -webkit-text-fill-color: {GREEN_100} !important;
    font-size: {sidebar_font};
    line-height: 1.7;
    box-shadow: var(--slg-shadow-sm) !important;
}}
.platform-footer strong {{ color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; font-weight: 700; }}
.platform-footer a       {{ color: {GREEN_300} !important; -webkit-text-fill-color: {GREEN_300} !important; text-decoration: none; }}
.platform-footer a:hover {{ color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; text-decoration: underline; }}

/* ── Accessibility ───────────────────────────────────────────── */
:focus-visible {{
    outline: 2px solid {PRIMARY} !important;
    outline-offset: 2px !important;
    border-radius: 6px !important;
}}
@media (prefers-reduced-motion: reduce) {{
    *, *::before, *::after {{ animation-duration: 0.001ms !important; transition-duration: 0.001ms !important; }}
}}

/* ── Subtle entry animation ──────────────────────────────────── */
@keyframes slgFadeUp {{ from {{ opacity: 0; transform: translateY(5px); }} to {{ opacity: 1; transform: translateY(0); }} }}
.main .block-container > div {{ animation: slgFadeUp 0.30s ease-out both; }}
@media (prefers-reduced-motion: reduce) {{ .main .block-container > div {{ animation: none !important; }} }}

/* Section anchor offset */
h2[id], h3[id] {{ scroll-margin-top: 88px; }}

/* ── Keep all form controls high-contrast ───────────────────── */
.main .stSelectbox > div > div > div,
.main div[data-baseweb="select"] > div,
.main div[data-baseweb="input"] > div,
.main .stTextInput input,
.main .stNumberInput input,
.main .stTextArea textarea,
.main .stDateInput input {{
    background: {SURFACE} !important;
    color: {INK_SOFT} !important;
    -webkit-text-fill-color: {INK_SOFT} !important;
    border-color: {BORDER_MED} !important;
}}
.main div[data-baseweb="select"] input,
.main div[data-baseweb="select"] span {{
    color: {INK_SOFT} !important;
    -webkit-text-fill-color: {INK_SOFT} !important;
}}
[data-baseweb="menu"] {{ background: {SURFACE} !important; color: {INK_SOFT} !important; }}
[data-baseweb="menu"] * {{ color: {INK_SOFT} !important; -webkit-text-fill-color: {INK_SOFT} !important; }}

{shell_css}
</style>"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def inject_css() -> None:
    """Inject the full ISIP-faithful ShieldLab G4 stylesheet."""
    settings = get_platform_settings()
    st.markdown(_build_css(settings), unsafe_allow_html=True)


def render_platform_footer() -> None:
    """Render the standard ShieldLab G4 platform footer."""
    if not bool(get_platform_settings().get("show_platform_footer", True)):
        return
    st.markdown(
        (
            '<div class="platform-footer">'
            f'<strong>{PRODUCT_NAME}</strong><br>'
            f'{platform_footer_text()}<br>'
            f'Platform stewardship and scientific ownership: {COPYRIGHT_OWNER}.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )
