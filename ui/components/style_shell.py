"""Shell component CSS — KPI strips, panel headers, breadcrumbs, status bars,
topbar command bar, user card, and enterprise mode override.

Part of the ShieldLab G4 governed design-system layer stack.
"""
from __future__ import annotations

from components.style_tokens import *  # noqa: F401, F403

def _build_shell_component_css(metric_val: str, small_label: str) -> str:
    """Shared shell primitives for KPI strips, panel headers, breadcrumbs, and status bars."""
    return f"""
/* ── ISIP KPI Strip ───────────────────────────────────────────── */
.sl-enterprise-kpi-wrap {{
    margin: 0.2rem 0 1rem;
}}
.sl-enterprise-kpi-head {{
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 0.6rem;
    margin-bottom: 0.55rem;
}}
.sl-enterprise-kpi-title {{
    font-size: 0.92rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: {INK};
    -webkit-text-fill-color: {INK};
}}
.sl-enterprise-kpi-subtitle {{
    font-size: 0.80rem;
    color: {MUTED};
    -webkit-text-fill-color: {MUTED};
}}
.sl-enterprise-kpi-strip {{
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 0.75rem;
}}
.sl-enterprise-kpi-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 1rem 1.1rem;
    box-shadow: {SHADOW_SM};
    transition: box-shadow 0.25s ease, transform 0.25s ease, border-color 0.25s ease;
    position: relative;
    overflow: hidden;
}}
.sl-enterprise-kpi-card:hover {{
    box-shadow: {SHADOW_LG};
    transform: translateY(-3px);
    border-color: {GREEN_200};
}}
.sl-enterprise-kpi-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, {PRIMARY} 0%, {PRIMARY_LIGHT} 100%);
    border-radius: 12px 12px 0 0;
    opacity: 0.6;
}}
.sl-enterprise-kpi-card-label {{
    font-size: {small_label};
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: {MUTED};
    -webkit-text-fill-color: {MUTED};
    margin-bottom: 0.3rem;
}}
.sl-enterprise-kpi-card-value {{
    font-size: {metric_val};
    font-weight: 800;
    letter-spacing: -0.03em;
    color: {INK};
    -webkit-text-fill-color: {INK};
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
}}
.sl-enterprise-chip {{
    display: inline-flex;
    align-items: center;
    margin-top: 0.45rem;
    border-radius: 9999px;
    padding: 2px 9px;
    font-size: 0.70rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    border: 1px solid transparent;
}}
.sl-enterprise-chip--up {{
    background: {GREEN_50};
    color: {PRIMARY_MID};
    border-color: {GREEN_200};
}}
.sl-enterprise-chip--steady {{
    background: #eff6ff;
    color: {BLUE_600};
    border-color: #bfdbfe;
}}
.sl-enterprise-chip--warn {{
    background: #fffbeb;
    color: #92400e;
    border-color: #fde68a;
}}
.sl-enterprise-chip--neutral {{
    background: #f9fafb;
    color: #374151;
    border-color: {BORDER_MED};
}}
.sl-enterprise-kpi-foot {{
    margin-top: 0.28rem;
    font-size: 0.72rem;
    color: {MUTED_LIGHT};
    -webkit-text-fill-color: {MUTED_LIGHT};
}}

/* ── ISIP Panel Header (CardHeader pattern) ──────────────────── */
.sl-panel-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.8rem;
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 0.75rem 1rem;
    margin: 0.3rem 0 0.8rem;
    box-shadow: {SHADOW_SM};
}}
.sl-panel-copy {{ min-width: 0; }}
.sl-panel-icon-badge {{
    width: 2.2rem;
    height: 2.2rem;
    border-radius: 8px;
    background: {GREEN_50};
    color: {PRIMARY};
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    margin-right: 0.6rem;
    flex-shrink: 0;
}}
.sl-panel-title {{
    font-size: 1.0rem;
    font-weight: 700;
    color: {INK};
    -webkit-text-fill-color: {INK};
    letter-spacing: -0.01em;
}}
.sl-panel-subtitle {{
    font-size: 0.82rem;
    color: {MUTED};
    -webkit-text-fill-color: {MUTED};
    margin-top: 2px;
}}
.sl-panel-legend {{
    display: inline-flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.4rem;
}}
.sl-panel-legend-item {{
    display: inline-flex;
    align-items: center;
    gap: 0.32rem;
    font-size: 0.78rem;
    color: {INK_SOFT};
    font-weight: 500;
}}
.sl-panel-legend-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
}}
.sl-panel-controls {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    flex-wrap: wrap;
}}
.sl-panel-control-chip {{
    border: 1px solid {BORDER_MED};
    background: #f9fafb;
    color: {INK_SOFT};
    -webkit-text-fill-color: {INK_SOFT};
    border-radius: 8px;
    padding: 3px 10px;
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    cursor: default;
    transition: background 0.15s, border-color 0.15s;
}}
.sl-panel-control-chip:hover {{
    background: {GREEN_50};
    border-color: {BORDER_GREEN};
    color: {PRIMARY_MID};
    -webkit-text-fill-color: {PRIMARY_MID};
}}

/* ── Breadcrumb — ISIP clean nav ─────────────────────────────── */
.sl-breadcrumb {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.3rem;
    margin: 0.15rem 0 0.55rem;
    font-size: 0.82rem;
}}
.sl-crumb {{
    color: {MUTED};
    -webkit-text-fill-color: {MUTED};
    font-weight: 500;
}}
.sl-crumb--current {{
    color: {INK};
    -webkit-text-fill-color: {INK};
    font-weight: 700;
}}
.sl-crumb-sep {{
    color: {MUTED_LIGHT};
    -webkit-text-fill-color: {MUTED_LIGHT};
    font-weight: 400;
}}

/* ── Status Pills — ISIP alert colors ───────────────────────── */
.sl-status-bar {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin: 0.1rem 0 0.65rem;
}}
.sl-status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.32rem;
    border-radius: 9999px;
    padding: 3px 11px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    border: 1px solid;
    background: {SURFACE};
}}
.sl-status-pill-label {{
    color: {MUTED};
    -webkit-text-fill-color: {MUTED};
    text-transform: uppercase;
    font-size: 0.68rem;
    letter-spacing: 0.07em;
}}
.sl-status-pill-value {{
    color: {INK_SOFT};
    -webkit-text-fill-color: {INK_SOFT};
    font-weight: 700;
}}
.sl-status-pill--ok      {{ border-color: {GREEN_200};  background: {GREEN_50}; }}
.sl-status-pill--warn    {{ border-color: #fde68a;       background: #fffbeb; }}
.sl-status-pill--info    {{ border-color: #bfdbfe;       background: #eff6ff; }}
.sl-status-pill--neutral {{ border-color: {BORDER_MED};  background: #f9fafb; }}
.sl-status-pill--danger  {{ border-color: #fca5a5;       background: #fef2f2; }}

@media (max-width: 1200px) {{
    .sl-enterprise-kpi-strip {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
}}
@media (max-width: 860px) {{
    .sl-enterprise-kpi-strip {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .sl-panel-header {{ flex-wrap: wrap; }}
    .sl-panel-controls {{ width: 100%; }}
}}
"""




def _build_shell_chrome_css(shell_mode: str = "enterprise") -> str:
    """Topbar, user-card, and hero-icon CSS.
    Appended to _build_shell_component_css output in _build_css.
    """
    css = f"""
/* ── ISIP Shell Top Bar (command bar) ─────────────────────── */
.sl-shell-topbar {{
    display: flex !important;
    align-items: center;
    gap: 1rem;
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-top: 2px solid {PRIMARY};
    border-radius: 12px;
    padding: 0.55rem 0.85rem;
    margin: -0.25rem 0 0.85rem;
    box-shadow: {SHADOW_SM};
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
}}
.sl-shell-search {{
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: #f9fafb;
    border: 1px solid {BORDER_MED};
    border-radius: 9999px;
    padding: 5px 12px;
    flex: 1 1 auto;
    max-width: 420px;
    color: {MUTED};
    -webkit-text-fill-color: {MUTED};
    font-size: 0.85rem;
    transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
}}
.sl-shell-search:hover {{
    background: {GREEN_50};
    border-color: {BORDER_GREEN};
}}
.sl-shell-search-icon {{
    color: {PRIMARY};
    -webkit-text-fill-color: {PRIMARY};
    font-size: 0.95rem;
    font-weight: 700;
}}
.sl-shell-search-text {{
    flex: 1;
    color: {INK};
    -webkit-text-fill-color: {INK};
    background: transparent;
    border: 0;
    outline: 0;
    font: inherit;
    padding: 0;
    min-width: 0;
}}
.sl-shell-search-text::placeholder {{ color: {MUTED_LIGHT}; opacity: 1; }}
.sl-shell-search:focus-within {{
    background: {SURFACE};
    border-color: {PRIMARY};
    box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.18);
}}
label.sl-shell-search {{ cursor: text; }}
.sl-shell-kbd {{
    font-family: 'IBM Plex Mono', monospace;
    background: {SURFACE};
    border: 1px solid {BORDER_MED};
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 0.70rem;
    color: {MUTED};
    -webkit-text-fill-color: {MUTED};
    font-weight: 600;
}}
.sl-shell-actions {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    flex-wrap: wrap;
}}
.sl-shell-btn {{
    display: inline-flex;
    align-items: center;
    border-radius: 9999px;
    padding: 4px 12px;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    border: 1px solid transparent;
    cursor: pointer;
    text-decoration: none;
    transition: transform 0.12s ease, box-shadow 0.12s ease, filter 0.12s ease;
}}
.sl-shell-btn:hover {{ transform: translateY(-1px); box-shadow: {SHADOW_SM}; filter: brightness(1.03); text-decoration: none; }}
.sl-shell-btn:focus-visible {{ outline: 2px solid {PRIMARY}; outline-offset: 2px; }}
.sl-shell-btn:active {{ transform: translateY(0); filter: brightness(0.97); }}
.sl-shell-btn--green  {{ background: {GREEN_50};  color: {PRIMARY_MID};   border-color: {GREEN_200};   }}
.sl-shell-btn--blue   {{ background: #eff6ff;     color: {BLUE_600};      border-color: #bfdbfe;       }}
.sl-shell-btn--violet {{ background: #f5f3ff;     color: #6d28d9;         border-color: #ddd6fe;       }}
.sl-shell-user {{
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.25rem 0.55rem 0.25rem 0.65rem;
    border-left: 1px solid {BORDER_MED};
    margin-left: auto;
    border-radius: 9999px;
    text-decoration: none;
    cursor: pointer;
    transition: background 0.15s ease;
}}
a.sl-shell-user, a.sl-shell-user:visited {{ color: inherit; text-decoration: none; }}
.sl-shell-user:hover {{ background: {GREEN_50}; }}
.sl-shell-user:focus-visible {{ outline: 2px solid {PRIMARY}; outline-offset: 2px; }}
.sl-shell-avatar {{
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    background: var(--slg-grad-green);
    color: #ffffff;
    -webkit-text-fill-color: #ffffff;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.75rem;
    letter-spacing: 0.04em;
    box-shadow: 0 2px 6px rgba(5,150,105,0.30);
}}
.sl-shell-user-meta {{
    display: inline-flex;
    flex-direction: column;
    line-height: 1.15;
}}
.sl-shell-user-meta strong {{
    color: {INK};
    -webkit-text-fill-color: {INK};
    font-size: 0.82rem;
    font-weight: 700;
}}
.sl-shell-user-meta small {{
    color: {MUTED};
    -webkit-text-fill-color: {MUTED};
    font-size: 0.70rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}}

/* ── Sidebar User Card (rendered after nav) — ISIP profile block ── */
/* ISIP: p-4 border-t border-white/10, avatar w-9 h-9 rounded-full,
   from-isip-green-400 to-isip-blue-500, name text-sm font-medium,
   role text-xs text-white/60.
   NOTE: card is wrapped in <p> by Streamlit markdown, so use inline-flex
   and only <span> children to prevent block-in-inline hoisting. */
[data-testid="stSidebar"] [data-testid="stMarkdown"] p:has(> .sl-user-card) {{
    margin: 0 !important;
    padding: 0 !important;
}}
.sl-user-card {{
    display: inline-flex;
    width: 100%;
    align-items: center;
    gap: 0.7rem;
    padding: 0.85rem 0.9rem;
    margin: 0.6rem 0 0;
    background: transparent;
    border: 0;
    border-top: 1px solid rgba(255,255,255,0.10);
    border-radius: 0;
    box-shadow: none;
    transition: background 0.16s ease;
    cursor: pointer;
    text-decoration: none;
    box-sizing: border-box;
}}
a.sl-user-card, a.sl-user-card:visited {{ text-decoration: none; }}
.sl-user-card:hover {{
    background: rgba(255,255,255,0.06);
}}
.sl-user-card:focus-visible {{ outline: 2px solid {GREEN_400}; outline-offset: -2px; }}
.sl-user-avatar {{
    width: 2.25rem;
    height: 2.25rem;
    border-radius: 50%;
    background: linear-gradient(135deg, {GREEN_400} 0%, {BLUE_500} 100%);
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.80rem;
    letter-spacing: 0.02em;
    flex-shrink: 0;
    box-shadow: none;
}}
.sl-user-info {{
    display: inline-flex;
    flex-direction: column;
    min-width: 0;
    line-height: 1.25;
    flex: 1 1 auto;
}}
.sl-user-name {{
    display: block;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: -0.005em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.sl-user-role {{
    color: rgba(255,255,255,0.60) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.60) !important;
    font-size: 0.70rem !important;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    margin-top: 2px;
}}
.sl-user-role-text {{
    color: rgba(255,255,255,0.60) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.60) !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.sl-user-tier-pill {{
    display: inline-block;
    background: rgba(255,255,255,0.16);
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.20);
    border-radius: 9999px;
    padding: 1px 8px;
    font-size: 0.62rem !important;
    font-weight: 800 !important;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}}
.sl-user-tier-pill--pro {{
    background: linear-gradient(135deg, {GOLD_500} 0%, #d97706 100%);
    border-color: rgba(245,158,11,0.50);
    box-shadow: 0 2px 6px rgba(245,158,11,0.30);
}}

/* ── Hero icon badge (replaces emoji-in-gradient-text) ─────── */
.shieldlab-hero-headline {{
    display: flex;
    align-items: center;
    gap: 0.85rem;
    margin: 0.2rem 0 0.5rem;
}}
.shieldlab-hero-icon {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.6rem;
    height: 2.6rem;
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(52,211,153,0.30) 0%, rgba(5,150,105,0.20) 100%);
    border: 1px solid rgba(167,243,208,0.35);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.10), 0 4px 12px rgba(2,26,12,0.35);
    font-size: 1.5rem;
    line-height: 1;
    color: #ffffff;
    -webkit-text-fill-color: initial;
    flex-shrink: 0;
}}
/* Inline title inside headline (override block margin) */
.shieldlab-hero-headline .shieldlab-hero-title {{
    margin: 0 !important;
}}
"""

    if shell_mode != "enterprise":
        # Standard mode — flatten enterprise chrome
        css += """
.sl-shell-topbar     { display: none !important; }
.sl-enterprise-kpi-wrap,
.sl-panel-header     { background: transparent !important; border: none !important;
                       box-shadow: none !important; padding: 0 !important; }
.sl-enterprise-kpi-card { box-shadow: none !important; }
"""

    return css
