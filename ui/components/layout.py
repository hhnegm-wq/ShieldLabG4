from __future__ import annotations

import html
import re

import streamlit as st

from components.platform_settings import get_platform_settings

# Match a leading emoji / icon glyph (with optional VS-16) at the start of a string.
# Covers: BMP misc symbols & dingbats, geometric shapes, arrows, supplemental
# arrows-B, miscellaneous technical, alphanumerics, plus the SMP emoji blocks.
_LEADING_ICON_RE = re.compile(
    r"^\s*("
    r"[\U0001F000-\U0001FFFF]"          # SMP emoji (faces, objects, symbols)
    r"|[\u2100-\u27FF]"                  # Letterlike, arrows, mathematical, misc tech, misc symbols, dingbats
    r"|[\u2900-\u29FF]"                  # Supplemental arrows-B
    r"|[\u2B00-\u2BFF]"                  # Misc symbols and arrows
    r")\uFE0F?\s*"
)


def _split_icon(title: str) -> tuple[str, str]:
    """Return (icon, clean_title). Icon is empty string when no leading glyph."""
    m = _LEADING_ICON_RE.match(title or "")
    if not m:
        return "", title or ""
    return m.group(1), title[m.end():]


def render_page_hero(
    title: str,
    body: str,
    kicker: str | None = None,
    *,
    centered: bool = False,
    variant: str | None = None,
    logo_src: str | None = None,
    title_icon_src: str | None = None,
) -> None:
    settings = get_platform_settings()
    if not bool(settings.get("show_hero_sections", True)):
        st.title(str(title))
        if body:
            st.caption(str(body))
        return

    icon, clean_title = _split_icon(str(title))
    safe_icon = html.escape(icon)
    safe_title = html.escape(clean_title)
    safe_body = html.escape(str(body))
    safe_kicker = html.escape(str(kicker or "Scientific Platform"))
    safe_logo_src = html.escape(str(logo_src)) if logo_src else ""
    safe_title_icon_src = html.escape(str(title_icon_src)) if title_icon_src else ""

    hero_classes = ["shieldlab-hero"]
    if centered:
        hero_classes.append("shieldlab-hero--centered")
    if variant:
        hero_classes.append(f"shieldlab-hero--{html.escape(str(variant))}")

    icon_html = (
        f'<span class="shieldlab-hero-icon" aria-hidden="true">{safe_icon}</span>'
        if safe_icon
        else ""
    )
    logo_html = (
        '<div class="shieldlab-hero-logo">'
        f'<img src="{safe_logo_src}" alt="ShieldLab G4 logo" />'
        '</div>'
        if safe_logo_src
        else ""
    )
    title_icon_html = (
        f'<img src="{safe_title_icon_src}" alt="" class="shieldlab-hero-title-icon" />'
        if safe_title_icon_src
        else ""
    )

    st.markdown(
        (
            f'<div class="{" ".join(hero_classes)}">'
            f'{logo_html}'
            f'<div class="shieldlab-hero-kicker">{safe_kicker}</div>'
            '<div class="shieldlab-hero-headline">'
            f'{icon_html}'
            f'{title_icon_html}'
            f'<div class="shieldlab-hero-title">{safe_title}</div>'
            '</div>'
            f'<div class="shieldlab-hero-body">{safe_body}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )
