"""ShieldLab G4 - Streamlit entry point."""
from __future__ import annotations

import base64
from pathlib import Path
from bootstrap import ensure_project_paths

ensure_project_paths()

import streamlit as st

from shieldlab.metadata import (
    PRODUCT_NAME,
    ownership_lines,
)
from components.platform_settings import get_platform_settings, init_platform_settings
from components.navigation import QUICK_ACTION_SPECS, build_navigation_sections, get_page_spec, page_href
from components.asset_integrity import check_critical_assets
from components.logo import LOGO_PATH
from components.enterprise_ui import enterprise_mode_enabled

_ui_dir = Path(__file__).parent

# Pre-compute base64 logo once for reuse across sidebar + favicon.
_logo_b64: str | None = (
    base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    if LOGO_PATH is not None
    else None
)

# Use the actual logo PNG as the browser-tab favicon when available.
try:
    from PIL import Image as _PILImage
    _page_icon = _PILImage.open(str(LOGO_PATH)) if LOGO_PATH else "🛡️"
except Exception:
    _page_icon = "🛡️"

st.set_page_config(
    page_title="ShieldLab G4",
    page_icon=_page_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from components.styles import inject_css, render_platform_footer
    init_platform_settings()
    inject_css()
except Exception:
    import logging as _logging
    _logging.getLogger(__name__).exception("CSS injection failed — visual theme will be absent")

try:
    from components.chart_theme import apply_all_chart_themes
    apply_all_chart_themes()
except Exception:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "Chart theme application failed — charts will use default styling", exc_info=True
    )


def _render_shell_command_bar() -> None:
    """Render a static enterprise-style command bar above page content."""
    if not enterprise_mode_enabled():
        return
    action_links = "\n".join(
        (
            f'<a class="sl-shell-btn sl-shell-btn--{action.tone}" '
            f'href="{get_page_spec(action.page_key).route}" target="_self" '
            f'title="{action.title}">{action.label}</a>'
        )
        for action in QUICK_ACTION_SPECS
    )
    st.markdown(
        f"""
        <div class="sl-shell-topbar" role="region" aria-label="Platform command bar">
            <label class="sl-shell-search" for="sl-shell-search-input">
                <span class="sl-shell-search-icon" aria-hidden="true">⌕</span>
                <input id="sl-shell-search-input" class="sl-shell-search-text" type="search" placeholder="Search pages, materials, references..." aria-label="Search platform" />
                <span class="sl-shell-kbd" aria-hidden="true">Ctrl K</span>
            </label>
            <nav class="sl-shell-actions" aria-label="Quick actions">
                {action_links}
            </nav>
            <a class="sl-shell-user" href="{page_href('settings')}" target="_self" title="Open platform settings">
                <span class="sl-shell-avatar">SG</span>
                <span class="sl-shell-user-meta">
                    <strong>ShieldLab User</strong>
                    <small>admin</small>
                </span>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

_dir = Path(__file__).parent

# Brand logo: st.logo renders in stSidebarHeader above navigation (Streamlit ≥ 1.32).
# We still call it so Streamlit's collapsed-state mini-logo button works.
if LOGO_PATH is not None:
    st.logo(str(LOGO_PATH), size="large")

_render_shell_command_bar()

# Asset integrity check — show warning only when assets are missing
asset_report = check_critical_assets(_dir)
if asset_report.missing:
    st.sidebar.warning(f"Asset integrity: {len(asset_report.missing)} missing item(s)")
    with st.sidebar.expander("Missing assets", expanded=False):
        for missing in asset_report.missing:
            st.markdown(f"- {missing}")

# Dev tier toggle (only visible when SHIELDLAB_DEV env var is set)
try:
    from auth import render_tier_dev_toggle, get_tier as _get_tier
    render_tier_dev_toggle()
    _tier_label = "Pro" if _get_tier() == "pro" else "Free"
except Exception:
    _tier_label = "Free"

pg = st.navigation(
    build_navigation_sections(_dir / "pages", st.Page)
)

pg.run()

# ISIP-style user/version card — appears at bottom of sidebar after nav.
# IMPORTANT: only <span> children inside the <a> to avoid block-in-inline
# hoisting (which previously caused a phantom empty link above the avatar).
_tier_pill_class = "sl-user-tier-pill sl-user-tier-pill--pro" if _tier_label == "Pro" else "sl-user-tier-pill"
st.sidebar.markdown(
    f'<a class="sl-user-card" href="{page_href("settings")}" target="_self" title="Open platform settings">'
    f'<span class="sl-user-avatar">SG</span>'
    f'<span class="sl-user-info">'
    f'<span class="sl-user-name">{PRODUCT_NAME}</span>'
    f'<span class="sl-user-role">'
    f'<span class="{_tier_pill_class}">{_tier_label}</span>'
    f'<span class="sl-user-role-text">Nuclear Shielding Lab</span>'
    f'</span>'
    f'</span>'
    f'</a>',
    unsafe_allow_html=True,
)

if bool(get_platform_settings().get("show_platform_footer", True)):
    st.divider()
    render_platform_footer()


