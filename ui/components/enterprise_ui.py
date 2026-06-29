"""Reusable enterprise UI blocks for ShieldLab G4.

HTML patterns derived from ISIP design system:
  KPICard.tsx, Card.tsx, Header.tsx (D:/projects/ISIP/platform)
CSS classes defined in components/styles.py (ISIP faithful theme).
"""
from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st

from components.platform_settings import get_platform_settings


def enterprise_mode_enabled() -> bool:
    """Return True when enterprise shell mode is active."""
    settings = get_platform_settings()
    return str(settings.get("shell_mode", "enterprise")) == "enterprise"


def render_breadcrumb(items: Iterable[str], current: str | None = None) -> None:
    """Render a compact enterprise breadcrumb above page content."""
    crumbs = [str(item).strip() for item in items if str(item).strip()]
    if current and current.strip():
        crumbs.append(current.strip())
    if not crumbs:
        return
    if not enterprise_mode_enabled():
        st.caption(" › ".join(crumbs))
        return
    nodes: list[str] = []
    last_index = len(crumbs) - 1
    for idx, label in enumerate(crumbs):
        cls = "sl-crumb sl-crumb--current" if idx == last_index else "sl-crumb"
        nodes.append(f'<span class="{cls}">{escape(label)}</span>')
        if idx != last_index:
            nodes.append('<span class="sl-crumb-sep">›</span>')
    st.markdown(
        '<nav class="sl-breadcrumb" aria-label="Breadcrumb">'
        + "".join(nodes)
        + "</nav>",
        unsafe_allow_html=True,
    )


def render_status_bar(items: list[dict[str, object]]) -> None:
    """Render a compact status bar (e.g. environment, build, validation)."""
    cleaned = [item for item in items or [] if item]
    if not cleaned:
        return
    if not enterprise_mode_enabled():
        parts = [f"{item.get('label', '')}: {item.get('value', '')}" for item in cleaned]
        st.caption(" • ".join(parts))
        return
    nodes: list[str] = []
    for item in cleaned:
        state = str(item.get("state", "neutral")).strip().lower() or "neutral"
        label = escape(str(item.get("label", "")))
        value = escape(str(item.get("value", "")))
        nodes.append(
            f'<span class="sl-status-pill sl-status-pill--{escape(state)}">'
            f'<span class="sl-status-pill-label">{label}</span>'
            f'<span class="sl-status-pill-value">{value}</span>'
            "</span>"
        )
    st.markdown(
        '<div class="sl-status-bar">' + "".join(nodes) + "</div>",
        unsafe_allow_html=True,
    )


def render_kpi_strip(
    items: list[dict[str, object]],
    title: str | None = None,
    subtitle: str | None = None,
) -> None:
    """Render a six-card KPI strip with optional trend chips."""
    if not items:
        return

    if not enterprise_mode_enabled():
        if title:
            st.subheader(str(title))
        if subtitle:
            st.caption(str(subtitle))
        cols = st.columns(len(items))
        for col, item in zip(cols, items):
            with col:
                st.metric(str(item.get("label", "Metric")), str(item.get("value", "-")))
        return

    head_html = ""
    if title or subtitle:
        head_html = (
            '<div class="sl-enterprise-kpi-head">'
            f'<div class="sl-enterprise-kpi-title">{escape(str(title or ""))}</div>'
            f'<div class="sl-enterprise-kpi-subtitle">{escape(str(subtitle or ""))}</div>'
            "</div>"
        )

    card_html: list[str] = []
    for item in items[:6]:
        label = escape(str(item.get("label", "Metric")))
        value = escape(str(item.get("value", "-")))
        trend = str(item.get("trend", "")).strip()
        trend_state = str(item.get("trend_state", "neutral")).strip().lower()
        footnote = str(item.get("footnote", "")).strip()
        icon = str(item.get("icon", "")).strip()

        icon_html = ""
        if icon:
            icon_html = (
                '<div style="display:flex;align-items:center;justify-content:space-between;'
                'margin-bottom:0.55rem;">'
                f'<div class="sl-enterprise-kpi-card-label">{label}</div>'
                f'<span style="width:2rem;height:2rem;border-radius:8px;background:#ecfdf5;'
                f'color:#059669;display:inline-flex;align-items:center;'
                f'justify-content:center;font-size:1rem;flex-shrink:0">{escape(icon)}</span>'
                "</div>"
            )
            label_html = ""
        else:
            icon_html = ""
            label_html = f'<div class="sl-enterprise-kpi-card-label">{label}</div>'

        trend_html = ""
        if trend:
            trend_html = (
                f'<span class="sl-enterprise-chip sl-enterprise-chip--{escape(trend_state)}">'
                f"{escape(trend)}"
                "</span>"
            )

        foot_html = (
            f'<div class="sl-enterprise-kpi-foot">{escape(footnote)}</div>'
            if footnote
            else ""
        )

        card_html.append(
            '<article class="sl-enterprise-kpi-card">'
            f"{icon_html}"
            f"{label_html}"
            f'<div class="sl-enterprise-kpi-card-value">{value}</div>'
            f"{trend_html}"
            f"{foot_html}"
            "</article>"
        )

    st.markdown(
        '<section class="sl-enterprise-kpi-wrap">'
        f"{head_html}"
        '<div class="sl-enterprise-kpi-strip">'
        + "".join(card_html)
        + "</div></section>",
        unsafe_allow_html=True,
    )


def render_panel_header(
    title: str,
    subtitle: str | None = None,
    legend_items: list[tuple[str, str]] | None = None,
    controls: list[str] | None = None,
    icon: str | None = None,
) -> None:
    """Render an ISIP-style panel header (CardHeader) with optional legend and chips."""
    if not enterprise_mode_enabled():
        st.subheader(str(title))
        if subtitle:
            st.caption(str(subtitle))
        return

    icon_html = ""
    if icon:
        icon_html = f'<span class="sl-panel-icon-badge">{escape(str(icon))}</span>'

    legend_html = ""
    if legend_items:
        nodes: list[str] = []
        for label, color in legend_items:
            nodes.append(
                '<span class="sl-panel-legend-item">'
                f'<span class="sl-panel-legend-dot" style="background:{escape(str(color))}"></span>'
                f"{escape(str(label))}"
                "</span>"
            )
        legend_html = '<div class="sl-panel-legend">' + "".join(nodes) + "</div>"

    controls_html = ""
    if controls:
        chips = [
            f'<span class="sl-panel-control-chip">{escape(str(control))}</span>'
            for control in controls
        ]
        controls_html = '<div class="sl-panel-controls">' + "".join(chips) + "</div>"

    st.markdown(
        '<div class="sl-panel-header">'
        '<div style="display:flex;align-items:center;gap:0.55rem;min-width:0">'
        f"{icon_html}"
        '<div class="sl-panel-copy">'
        f'<div class="sl-panel-title">{escape(str(title))}</div>'
        f'<div class="sl-panel-subtitle">{escape(str(subtitle or ""))}</div>'
        f"{legend_html}"
        "</div>"
        "</div>"
        f"{controls_html}"
        "</div>",
        unsafe_allow_html=True,
    )


def render_link_card(
    title: str,
    body: str,
    href: str,
    *,
    icon: str | None = None,
    cta: str = "Open ->",
    variant: str = "feature",
) -> None:
    """Render a styled internal navigation card using shared enterprise classes."""
    safe_title = escape(str(title))
    safe_body = escape(str(body))
    safe_href = escape(str(href))
    safe_cta = escape(str(cta))
    safe_icon = escape(str(icon or ""))

    if variant == "workflow":
        icon_html = f'<span class="workflow-icon">{safe_icon}</span>' if safe_icon else ""
        html_block = (
            f'<a class="section-card workflow-card workflow-card--link" href="{safe_href}" '
            f'target="_self" title="Open {safe_title}">'
            f'{icon_html}'
            f'<span class="workflow-title">{safe_title}</span>'
            f'<span class="workflow-body">{safe_body}</span>'
            f'<span class="workflow-card-cta">{safe_cta}</span>'
            '</a>'
        )
    else:
        title_html = safe_title if not safe_icon else f'{safe_icon} {safe_title}'
        html_block = (
            f'<a class="feature-card feature-card--link" href="{safe_href}" '
            f'target="_self" title="Open {safe_title}">'
            f'<span class="feature-card-title">{title_html}</span>'
            f'<span class="feature-card-body">{safe_body}</span>'
            f'<span class="feature-card-cta">{safe_cta}</span>'
            '</a>'
        )

    st.markdown(html_block, unsafe_allow_html=True)


def render_platform_capability_grid(
    capabilities: Iterable[object],
    *,
    title: str,
    subtitle: str,
    columns: int = 4,
) -> None:
    """Render a reusable platform capability grid tied to shared product surfaces."""
    items = list(capabilities)
    if not items:
        return

    render_panel_header(
        title,
        subtitle,
        legend_items=[("Security", "#10b981"), ("Validation", "#3b82f6"), ("Traceability", "#8b5cf6")],
        controls=["Runtime", "Evidence", "Product Surface"],
    )
    cols = st.columns(max(1, columns))
    for idx, capability in enumerate(items):
        with cols[idx % len(cols)]:
            render_link_card(
                getattr(capability, "title"),
                getattr(capability, "body"),
                getattr(capability, "href"),
                icon=getattr(capability, "icon", None),
                cta=getattr(capability, "cta", "Open ->"),
                variant="feature",
            )


def render_path_table(
    rows: Iterable[dict[str, str | None]],
    *,
    runtime: bool = False,
) -> None:
    """Render a shared path/runtime table using the shell's path-row styles."""
    nodes: list[str] = []
    for row in rows:
        label = escape(str(row.get("label", "")))
        value = escape(str(row.get("value", "")))
        badge_class = str(row.get("badge_class", "")).strip()
        badge_text = str(row.get("badge_text", "")).strip()
        badge_html = ""
        if badge_class and badge_text:
            badge_html = f'<span class="{escape(badge_class)}">{escape(badge_text)}</span>'
        nodes.append(
            '<div class="path-row">'
            f'<span class="path-label">{label}</span>'
            f'<span class="path-value">{value}</span>'
            f'{badge_html}'
            '</div>'
        )

    table_class = "slg-path-table slg-path-table--runtime" if runtime else "slg-path-table"
    st.markdown(
        f'<div class="{table_class}">' + "".join(nodes) + '</div>',
        unsafe_allow_html=True,
    )


def render_metric_strip(items: list[tuple[str, str]], columns: int | None = None) -> None:
    """Render compact, stable metric cards for dense scientific values."""
    count = max(1, columns or len(items))
    cards: list[str] = []
    for label, value in items:
        cards.append(
            '<div class="slg-metric-card">'
            f'<div class="slg-metric-card-label">{escape(str(label))}</div>'
            f'<div class="slg-metric-card-value">{escape(str(value))}</div>'
            '</div>'
        )
    st.markdown(
        f'<div class="slg-metric-strip slg-metric-strip--{count}">' + "".join(cards) + '</div>',
        unsafe_allow_html=True,
    )


def render_literature_benchmark_card(
    *,
    title: str,
    meta: str,
    status: str,
    notes: str,
    exists_label: str,
) -> None:
    """Render a benchmark registry card using the shared literature benchmark styles."""
    safe_status = escape(str(status).strip().lower())
    status_label = escape(str(status).strip().upper())
    exists_text = escape(str(exists_label).strip().upper())
    st.markdown(
        (
            '<div class="lit-benchmark-card">'
            '<div class="lit-benchmark-row">'
            '<div>'
            f'<div class="lit-benchmark-title">{escape(str(title))}</div>'
            f'<div class="lit-benchmark-meta">{escape(str(meta))}</div>'
            '</div>'
            f'<div class="lit-benchmark-status lit-benchmark-status--{safe_status}">{status_label} | {exists_text}</div>'
            '</div>'
            f'<div class="lit-benchmark-notes">{escape(str(notes))}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )
