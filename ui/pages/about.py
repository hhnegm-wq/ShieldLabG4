"""ShieldLab G4 ownership, legal, and platform governance page."""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_UI_DIR = Path(__file__).resolve().parent.parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from bootstrap import ensure_project_paths  # noqa: E402

ensure_project_paths()

from shieldlab import __version__
from shieldlab.content import PAGE_COPY
from shieldlab.metadata import (
    CONTACT_EMAILS,
    CONTACT_PHONE,
    COPYRIGHT_OWNER,
    LEGAL_DISCLAIMER,
    PLATFORM_SCOPE,
    PRODUCT_NAME,
    PRODUCT_SUBTITLE,
    PRODUCT_TAGLINE,
    SUPPORT_SLA,
    copyright_notice,
)
from components.platform_capabilities import PLATFORM_CAPABILITIES
from components.platform_settings import get_platform_settings
from components.layout import render_page_hero
from components.enterprise_ui import (
    render_breadcrumb,
    render_kpi_strip,
    render_panel_header,
    render_platform_capability_grid,
    render_status_bar,
)

copy = PAGE_COPY["about"]
settings = get_platform_settings()

render_page_hero(str(copy["title"]), str(copy["caption"]), "Platform Governance")

render_breadcrumb(["ShieldLab G4", "Reference"], current="About & Legal")
render_kpi_strip(
    [
        {"label": "Version", "value": __version__, "trend": "Release", "trend_state": "up", "footnote": "Current platform version"},
        {"label": "Product", "value": PRODUCT_NAME, "trend": "Brand", "trend_state": "steady", "footnote": "Official product name"},
        {"label": "Owner", "value": COPYRIGHT_OWNER, "trend": "Governance", "trend_state": "neutral", "footnote": "Copyright holder"},
        {"label": "Support SLA", "value": SUPPORT_SLA, "trend": "Service", "trend_state": "steady", "footnote": "Response commitment"},
        {"label": "Tagline", "value": PRODUCT_TAGLINE, "trend": "Identity", "trend_state": "neutral", "footnote": "Platform positioning"},
        {"label": "Contacts", "value": str(len(CONTACT_EMAILS)), "trend": "Channels", "trend_state": "steady", "footnote": "Active support emails"},
    ],
    title="ShieldLab Governance Strip",
    subtitle="Ownership, version, support, and platform identity at a glance.",
)

render_platform_capability_grid(
    PLATFORM_CAPABILITIES,
    title="Operational Guarantees",
    subtitle="Canonical product-facing view of the controls and evidence that support platform trust.",
)

hero_left, hero_right = st.columns([2, 1])
with hero_left:
    st.markdown(f"**{PRODUCT_SUBTITLE}**")
    st.write(PLATFORM_SCOPE)
with hero_right:
    st.metric("Version", __version__)
    st.metric("Owner", COPYRIGHT_OWNER)

st.divider()

st.subheader("Ownership")
st.write(copyright_notice())
st.write(str(copy["ownership_text"]))

st.subheader("Contact")
for contact_line in [CONTACT_EMAILS[0], CONTACT_EMAILS[1], CONTACT_PHONE]:
    st.write(contact_line)
st.caption(SUPPORT_SLA)

st.subheader("Platform Scope")
st.write(str(copy["platform_scope_text"]))

st.subheader("Legal Disclaimer")
st.warning(LEGAL_DISCLAIMER)

st.subheader("Operational Position")
for line in copy["operational_position"]:
    st.markdown(f"- {line}")

st.subheader("Governance Notes")
for line in copy["governance_notes"]:
    st.markdown(f"- {line}")

st.subheader(str(copy["citation_policy_title"]))
st.write(str(copy["citation_policy_intro"]))
for line in copy["citation_policy_points"]:
    st.markdown(f"- {line}")
st.code(str(copy["citation_example"]).format(version=__version__), language="text")

