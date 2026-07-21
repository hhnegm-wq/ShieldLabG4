"""Home / Dashboard page."""
from __future__ import annotations

import datetime
import base64
import json
import logging
import sys
from pathlib import Path

_log = logging.getLogger(__name__)

import pandas as pd
import streamlit as st

_UI_DIR = Path(__file__).resolve().parent.parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from bootstrap import ensure_project_paths  # noqa: E402

ensure_project_paths()

from shieldlab.content import PAGE_COPY

from shieldlab.metadata import PRODUCT_NAME
from components.platform_settings import get_platform_settings
from components.navigation import PRIMARY_WORKFLOWS, home_feature_specs, page_href, workflow_stage_specs
from components.platform_capabilities import PLATFORM_CAPABILITIES
from components.enterprise_ui import (
    render_breadcrumb,
    render_kpi_strip,
    render_panel_header,
    render_platform_capability_grid,
    render_status_bar,
    render_link_card,
)
from components.layout import render_page_hero

import config  # noqa: E402

# Note: inject_css() is called by app.py at startup; do not re-inject here.

copy = PAGE_COPY["home"]
settings = get_platform_settings()

from components.logo import LOGO_PATH as _logo_path
_logo_b64: str | None = None
if _logo_path is not None:
    _logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode("ascii")

_title_icon = (
    f'data:image/png;base64,{_logo_b64}'
    if _logo_b64 else ''
)
_logo_src = f'data:image/png;base64,{_logo_b64}' if _logo_b64 else None

render_page_hero(
    PRODUCT_NAME,
    str(copy["hero_body"]),
    str(copy["hero_kicker"]),
    centered=True,
    variant="brand",
    logo_src=_logo_src,
    title_icon_src=_title_icon or None,
)

studies = sorted(config.STUDIES_DIR.glob("*.json")) if config.STUDIES_DIR.exists() else []
result_dirs = (
    [d for d in config.RESULTS_DIR.iterdir() if d.is_dir()]
    if config.RESULTS_DIR.exists()
    else []
)
val_files = (
    sorted(
        config.RESULTS_DIR.glob("*/validation_summary.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if config.RESULTS_DIR.exists()
    else []
)

total_runs = 0
for vf in val_files:
    try:
        total_runs += json.loads(vf.read_text()).get("run_summary_count", 0)
    except Exception:
        _log.debug("Could not read run summary count from %s", vf, exc_info=True)

try:
    from shieldlab.data.compendium import COMPENDIUM
    from shieldlab.data.isotopes import ISOTOPES
    _n_mat = len(COMPENDIUM)
    _n_iso = len(ISOTOPES)
except Exception:
    _log.warning("Compendium/isotope import failed — using fallback counts", exc_info=True)
    _n_mat, _n_iso = 150, 100

if val_files:
    _last_run = datetime.datetime.fromtimestamp(val_files[0].stat().st_mtime).strftime("%b %d %H:%M")
else:
    _last_run = "--"

render_breadcrumb(["ShieldLab G4", "Workspace"], current="Home")
render_status_bar([
    {"label": "Shell", "value": "Active", "state": "ok"},
    {"label": "Validation", "value": f"{len(val_files)} runs", "state": "info"},
    {"label": "Studies", "value": len(studies), "state": "neutral"},
    {"label": "Last Run", "value": _last_run, "state": "neutral"},
])

render_kpi_strip(
    [
        {"label": "Study Configs", "value": len(studies), "trend": "Ready", "trend_state": "steady", "footnote": "JSON studies catalog"},
        {"label": "Result Sets", "value": len(result_dirs), "trend": "Active", "trend_state": "up", "footnote": "Computed output folders"},
        {"label": "Geant4 Runs", "value": total_runs, "trend": "Cumulative", "trend_state": "neutral", "footnote": "Validation run count"},
        {"label": "Last Run", "value": _last_run, "trend": "Recent", "trend_state": "steady", "footnote": "Most recent result timestamp"},
        {"label": "Materials", "value": _n_mat, "trend": "Compendium", "trend_state": "up", "footnote": "Reference material records"},
        {"label": "Isotopes", "value": _n_iso, "trend": "Library", "trend_state": "up", "footnote": "Source isotope entries"},
    ],
    title="ShieldLab Executive Snapshot",
    subtitle="Scientific readiness, execution throughput, and reference coverage in one strip.",
)

render_platform_capability_grid(
    PLATFORM_CAPABILITIES,
    title="Platform Guarantees",
    subtitle="Security, validation, traceability, and methods evidence exposed as first-class product capabilities.",
)

render_panel_header(
    str(copy["features_heading"]),
    "Core ShieldLab capabilities available across simulation, analysis, and reporting.",
    legend_items=[("Simulation", "#10b981"), ("Analysis", "#3b82f6"), ("Governance", "#8b5cf6")],
    controls=["Feature Grid", "Organized", "Platform"],
)

fc = st.columns(4)
for col, (icon, title, desc), spec in zip(fc, copy["features"], home_feature_specs()):
    with col:
        render_link_card(title, desc, spec.route, icon=icon, cta="Open ->", variant="feature")

st.write("")
st.markdown("---")

st.info(str(copy["section_blurb"]))
st.caption(str(copy["disclaimer"]))

render_panel_header(
    str(copy["workflow_heading"]),
    "Top product workflows anchored to canonical task paths instead of ad hoc page inventory.",
    controls=["Workflow 1", "Workflow 2", "Workflow 3"],
)
wc = st.columns(3)
for col, workflow in zip(wc, PRIMARY_WORKFLOWS):
    with col:
        stage_titles = " -> ".join(spec.title for spec in workflow_stage_specs(workflow))
        render_link_card(
            workflow.title,
            f"{workflow.body} Path: {stage_titles}.",
            page_href(workflow.start_page_key),
            icon=workflow.icon,
            cta="Start workflow ->",
            variant="workflow",
        )

st.markdown("---")

if val_files:
    st.subheader("Recent Runs")
    rows = []
    for vf in val_files[:10]:
        try:
            d = json.loads(vf.read_text())
            status_icon = "✅" if d.get("status") == "completed" else "⏳"
            rows.append(
                {
                    "Result Folder": Path(d.get("result_dir", "")).name,
                    "Study File": Path(d.get("study_file", "")).name,
                    "Status": status_icon + " " + d.get("status", ""),
                    "Runs": d.get("run_summary_count", 0),
                    "Figures": len(d.get("figures", [])),
                    "Excel": "yes" if d.get("workbook") else "no",
                }
            )
        except Exception:
            _log.debug("Could not parse run summary entry for table — row will be skipped", exc_info=True)
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
else:
    st.info("No completed runs yet. Go to **Run Study** to execute your first simulation.")

if studies:
    st.markdown("---")
    with st.expander(f"Available Study Configs ({len(studies)})"):
        for s in studies:
            try:
                obj = json.loads(s.read_text(encoding="utf-8"))
                run = obj.get("run", {})
                sweep = (
                    "energy sweep"
                    if "energy_grid" in run
                    else "thickness sweep"
                    if "thickness_grid" in run
                    else "composition sweep"
                    if "composition_sweep" in run
                    else "single run"
                )
                mats = len(obj.get("materials", []))
                st.markdown(
                    f"**{s.name}** &nbsp;|&nbsp; {sweep} &nbsp;|&nbsp; "
                    f"{run.get('histories', '?')} histories &nbsp;|&nbsp; "
                    f"{mats} custom material(s)"
                )
            except Exception:
                _log.debug("Could not parse study config %s — showing name only", s.name, exc_info=True)
                st.markdown(f"**{s.name}**")

st.markdown("---")
with st.expander("NIST Data"):
    _cache_dir = Path(config.PROJECT_ROOT) / "python" / "shieldlab" / "data" / "xcom_cache"
    if _cache_dir.exists():
        _cached_files = list(_cache_dir.glob("*.json")) + list(_cache_dir.glob("*.pkl"))
        _n = len(_cached_files)
        if _n:
            _oldest = min(_cached_files, key=lambda p: p.stat().st_mtime)
            _oldest_dt = datetime.datetime.fromtimestamp(_oldest.stat().st_mtime)
            _total_kb = sum(f.stat().st_size for f in _cached_files) / 1024
            st.markdown(
                f"**{_n} cached file(s)** &nbsp;|&nbsp; "
                f"{_total_kb:.0f} KB total &nbsp;|&nbsp; "
                f"oldest: {_oldest_dt.strftime('%Y-%m-%d')}"
            )
        else:
            st.markdown("Cache is empty - NIST data will be downloaded on first use.")
        if st.button("Clear NIST Cache", key="clear_nist_cache"):
            try:
                shutil.rmtree(_cache_dir)
                _cache_dir.mkdir(parents=True, exist_ok=True)
                st.success("NIST cache cleared. Data will be re-fetched on next calculation.")
            except Exception as _ce:
                st.error(f"Cache clear failed: {_ce}")
    else:
        st.markdown("Cache directory does not exist yet; it will be created on first NIST fetch.")




