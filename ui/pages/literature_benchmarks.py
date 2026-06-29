"""ShieldLab G4 literature benchmark registry page."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_UI_DIR = Path(__file__).resolve().parent.parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from bootstrap import ensure_project_paths  # noqa: E402

ensure_project_paths()

import config  # noqa: E402
from shieldlab.content import PAGE_COPY  # noqa: E402
from components.layout import render_page_hero  # noqa: E402
from components.enterprise_ui import (
    render_breadcrumb,
    render_kpi_strip,
    render_literature_benchmark_card,
    render_panel_header,
)

copy = PAGE_COPY["literature_benchmarks"]

REGISTRY_PATH = config.PROJECT_ROOT / "docs" / "ref_papers" / "benchmark_registry.json"
INVENTORY_SUMMARY_PATH = config.PROJECT_ROOT / "docs" / "ref_papers" / "paper_inventory_summary.json"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _resolve(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    return config.resolve_project_path(path_text)


def _coverage_frame(values: dict[str, int] | None, label: str) -> pd.DataFrame:
    rows = [{label: key, "Count": value} for key, value in sorted((values or {}).items(), key=lambda item: (-item[1], item[0]))]
    return pd.DataFrame(rows)


registry = _load_json(REGISTRY_PATH)
inventory_summary = _load_json(INVENTORY_SUMMARY_PATH)
entries = registry.get("entries", [])
summary = registry.get("summary", {})

render_page_hero(str(copy["hero_title"]), str(copy["hero_body"]), str(copy["hero_kicker"]))
render_breadcrumb(["ShieldLab G4", "Analysis"], current="Literature Benchmarks")

st.caption(str(copy["caption"]))

ready_ratio = 0.0
if summary.get("curated_entries", 0):
    ready_ratio = float(summary.get("ready_entries", 0)) / float(summary.get("curated_entries", 1))

render_kpi_strip(
    [
        {"label": "Inventory Papers", "value": summary.get("inventory_papers", 0), "trend": "Corpus", "trend_state": "steady", "footnote": "Indexed literature documents"},
        {"label": "Curated Entries", "value": summary.get("curated_entries", 0), "trend": "Registry", "trend_state": "up", "footnote": "Benchmark records prepared"},
        {"label": "Ready", "value": summary.get("ready_entries", 0), "trend": "Executable", "trend_state": "up", "footnote": "Run-ready benchmark studies"},
        {"label": "Provisional", "value": summary.get("provisional_entries", 0), "trend": "Refinement", "trend_state": "warn", "footnote": "Awaiting final paper values"},
        {"label": "Queued", "value": summary.get("queued_entries", 0), "trend": "Pipeline", "trend_state": "neutral", "footnote": "Pending extraction work"},
        {"label": "Ready Ratio", "value": f"{ready_ratio * 100:.1f}%", "trend": "Coverage", "trend_state": "steady", "footnote": "Ready / curated entries"},
    ],
    title="ShieldLab Literature Benchmark Strip",
    subtitle="Benchmark pipeline maturity from raw inventory to run-ready study packs.",
)

st.info(
    "WSL-first execution remains the benchmark runtime path. These studies are written to the same JSON schema used by Run Study, so each curated paper entry can move straight from registry to Geant4 execution."
)
st.caption(str(copy["method_note"]))

tab_registry, tab_ready, tab_coverage, tab_notes = st.tabs([
    "Registry",
    "Runnable Studies",
    "Coverage",
    "Curation Notes",
])

with tab_registry:
    render_panel_header(
        "Registry",
        "Filter and inspect curated benchmark entries with readiness metadata.",
        controls=["Filter", "Inspect", "JSON"],
    )
    status_options = sorted({entry.get("status", "unknown") for entry in entries})
    material_options = sorted({entry.get("material_class", "unknown") for entry in entries})
    radiation_options = sorted({mode for entry in entries for mode in entry.get("radiation_modes", [])})

    f1, f2, f3 = st.columns(3)
    with f1:
        selected_status = st.multiselect("Readiness", status_options, default=status_options)
    with f2:
        selected_materials = st.multiselect("Material Class", material_options, default=material_options)
    with f3:
        selected_radiation = st.multiselect("Radiation", radiation_options, default=radiation_options)

    filtered_entries = [
        entry
        for entry in entries
        if entry.get("status") in selected_status
        and entry.get("material_class") in selected_materials
        and (not selected_radiation or bool(set(entry.get("radiation_modes", [])) & set(selected_radiation)))
    ]

    table_rows = []
    for entry in filtered_entries:
        study_path = entry.get("study_file") or "-"
        table_rows.append(
            {
                "Priority": entry.get("priority"),
                "ID": entry.get("id"),
                "Status": entry.get("status"),
                "Sample": entry.get("sample_id") or "-",
                "Class": entry.get("material_class"),
                "Radiation": ", ".join(entry.get("radiation_modes", [])),
                "Confidence": entry.get("confidence"),
                "Study": study_path,
            }
        )

    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    st.download_button(
        "Download Benchmark Registry",
        REGISTRY_PATH.read_text(encoding="utf-8") if REGISTRY_PATH.exists() else "{}",
        file_name="benchmark_registry.json",
        mime="application/json",
    )

    entry_map = {entry["id"]: entry for entry in filtered_entries}
    selected_id = st.selectbox("Inspect Benchmark", list(entry_map.keys()), index=0 if entry_map else None)
    selected_entry = entry_map.get(selected_id)

    if selected_entry:
        st.markdown("---")
        left, right = st.columns([1.2, 1.0])
        with left:
            st.subheader(str(selected_entry.get("title", selected_entry["id"])))
            st.write(f"DOI: {selected_entry.get('doi') or 'pending'}")
            st.write(f"Sample: {selected_entry.get('sample_id') or 'pending'}")
            st.write(f"Density basis: {selected_entry.get('density_basis')}")
            st.write(f"Composition basis: {selected_entry.get('composition_basis')}")
            st.write(f"Figure targets: {', '.join(selected_entry.get('figure_targets', []))}")
            st.caption(str(selected_entry.get("notes", "")))
        with right:
            st.metric("Readiness", str(selected_entry.get("status", "unknown")).upper())
            density = selected_entry.get("density_g_cm3")
            st.metric("Density (g/cm³)", "-" if density is None else f"{density:.4g}")
            study_file = selected_entry.get("study_file") or "-"
            st.write(f"Study file: {study_file}")
            st.write(f"Paper file: {selected_entry.get('paper_file')}")

        study_path = _resolve(selected_entry.get("study_file"))
        if study_path and study_path.exists():
            with st.expander("Study JSON", expanded=False):
                st.code(study_path.read_text(encoding="utf-8"), language="json")

with tab_ready:
    render_panel_header(
        "Runnable Studies",
        "Ready and provisional studies mapped to executable ShieldLab JSON templates.",
        controls=["Ready", "Provisional", "Study Files"],
    )
    ready_rows = []
    for entry in entries:
        if entry.get("status") not in {"ready", "provisional"}:
            continue
        ready_rows.append(
            {
                "Benchmark": entry.get("id"),
                "Status": entry.get("status"),
                "Paper": entry.get("title"),
                "Sample": entry.get("sample_id") or "-",
                "Density": entry.get("density_g_cm3"),
                "Study File": entry.get("study_file"),
            }
        )
    st.dataframe(pd.DataFrame(ready_rows), use_container_width=True, hide_index=True)

    for entry in entries:
        if entry.get("status") not in {"ready", "provisional"}:
            continue
        study_path = _resolve(entry.get("study_file"))
        exists_label = "present" if study_path and study_path.exists() else "missing"
        render_literature_benchmark_card(
            title=str(entry.get("title", "")),
            meta=f"{entry.get('id')} | {entry.get('sample_id') or 'pending sample'} | {entry.get('study_file')}",
            status=str(entry.get("status", "")),
            notes=str(entry.get("notes", "")),
            exists_label=exists_label,
        )

with tab_coverage:
    render_panel_header(
        "Inventory Coverage",
        "Distribution of material classes, radiation types, figure families, and curation readiness.",
        controls=["Material", "Radiation", "Figure Family"],
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.dataframe(_coverage_frame(inventory_summary.get("material_classes"), "Material Class"), use_container_width=True, hide_index=True)
    with c2:
        st.dataframe(_coverage_frame(inventory_summary.get("radiation_types"), "Radiation"), use_container_width=True, hide_index=True)
    with c3:
        st.dataframe(_coverage_frame(inventory_summary.get("figure_families"), "Figure Family"), use_container_width=True, hide_index=True)

    curated_by_status = _coverage_frame(
        {status: sum(1 for entry in entries if entry.get("status") == status) for status in sorted({entry.get("status") for entry in entries})},
        "Curated Status",
    )
    st.markdown("---")
    st.dataframe(curated_by_status, use_container_width=True, hide_index=True)

with tab_notes:
    render_panel_header(
        "Curation Notes",
        "Operational rules and next extraction priorities for benchmark-quality study generation.",
        controls=["Rules", "Figure Pack", "Next Steps"],
    )
    st.markdown(
        """
        ### Curation rules
        - Ready: density and composition are exact or directly recoverable from paper-reported attenuation values.
        - Provisional: composition is exact, but one measured quantity such as density still uses an engineering estimate.
        - Queued: the paper is strategically important, but the current PDF extraction pass did not recover enough table data for a reliable study JSON.

        ### Figure-pack direction
        - Each benchmark targets paper-grade overlays first: MAC versus energy, HVL/TVL, transmission-thickness, and any particle-specific stopping or neutron metrics the paper reports.
        - The current pack is intentionally weighted toward your own papers before broader literature expansion.

        ### Next curation pressure points
        - Extract measured densities from the CuO/Fe3O4 and CdO/NiO attapulgite tables to promote both studies from provisional to ready.
        - Recover the iron(III)-doped lithium borate sample table for a seventh benchmark that broadens the glass family coverage.
        - Attach paper-derived coefficient rows into the study JSON files where the paper reports explicit MAC or LAC numbers across the energy grid.
        """
    )


