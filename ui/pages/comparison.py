"""Multi-material comparison page.

Compare up to 6 shielding materials side-by-side:
  - MAC, LAC, HVL, TVL, MFP vs energy
  - Transmission vs thickness at a selected energy
  - FNRCS neutron removal
  - Summary ranking table
  - Journal-quality export (PNG/PDF/SVG/EPS/TIFF) with captions
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

_UI_DIR = Path(__file__).resolve().parent.parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from bootstrap import ensure_project_paths  # noqa: E402

ensure_project_paths()

import config  # noqa: E402 - loads project constants

_log = logging.getLogger(__name__)

from shieldlab.viz.style import apply_journal_style, finish_shieldlab_figure, OKABE_ITO
from shieldlab.viz.export import figure_download_buttons
from shieldlab.core.materials import resolve_material_mass_fractions
from shieldlab.core.descriptors import material_descriptors
from shieldlab.physics.shielding_params import (
    compute_shielding_table,
    compute_transmission_vs_thickness,
    compute_fnrcs,
    compute_fnrcs_hvl,
    GP_MATERIALS,
)
from shieldlab.physics.geometry_viz import (
    plot_mac_vs_energy,
    plot_hvl_tvl_vs_energy,
    plot_transmission_vs_thickness,
)
from auth import get_user_tier, render_tier_dev_toggle
from components.pro_gate import pro_only
from components.layout import render_page_hero
from components.enterprise_ui import render_kpi_strip, render_panel_header, render_breadcrumb
from shieldlab.content import PAGE_COPY

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
except Exception:  # pragma: no cover - fallback when runtime internals are unavailable
    get_script_run_ctx = None

apply_journal_style("shieldlab_web")

MAC_COL_CANDIDATES = ("mu/rho (cm^2/g)",)
MAC_EN_COL_CANDIDATES = ("mu_en/rho (cm^2/g)",)
LAC_COL_CANDIDATES = ("mu (cm^-1)",)


def _col(df: pd.DataFrame, *candidates: str) -> str:
    for name in candidates:
        if name in df.columns:
            return name
    raise KeyError(f"None of the candidate columns found: {candidates}")


def _is_bare_mode() -> bool:
    if get_script_run_ctx is None:
        return False
    return get_script_run_ctx() is None


def _build_result(spec: dict, E_arr: np.ndarray, T_arr: np.ndarray, gp_ref: str) -> dict:
    mf = resolve_material_mass_fractions({
        "name": spec["label"],
        "density_g_cm3": spec["density"],
        "formula": spec["formula"],
    })
    df = compute_shielding_table(mf, spec["density"], E_arr, T_arr, gp_material=gp_ref)
    sigma_R = compute_fnrcs(mf, spec["density"])
    hvl_n, tvl_n = compute_fnrcs_hvl(sigma_R)
    desc = material_descriptors(spec["label"], mf, spec["density"])
    return {
        "label": spec["label"],
        "formula": spec["formula"],
        "density": spec["density"],
        "colour": spec["colour"],
        "mf": mf,
        "df": df,
        "mac": df[_col(df, *MAC_COL_CANDIDATES)].to_numpy(),
        "mac_en": df[_col(df, *MAC_EN_COL_CANDIDATES)].to_numpy(),
        "hvl": df["HVL (cm)"].to_numpy(),
        "tvl": df["TVL (cm)"].to_numpy(),
        "lac": df[_col(df, *LAC_COL_CANDIDATES)].to_numpy(),
        "mfp": (1.0 / np.where(df[_col(df, *LAC_COL_CANDIDATES)].to_numpy() > 0,
                                  df[_col(df, *LAC_COL_CANDIDATES)].to_numpy(), 1e-10)),
        "sigma_R": sigma_R,
        "hvl_n": hvl_n,
        "tvl_n": tvl_n,
        "desc": desc,
    }

# Page header
render_tier_dev_toggle()
_tier = get_user_tier()
copy = PAGE_COPY["comparison"]

# Page header
render_page_hero(str(copy["title"]), str(copy["caption"]), "Multi-Material Analysis")
render_breadcrumb(["ShieldLab G4", "Analysis"], current="Material Comparison")

if _tier == "free":
    st.warning(
        f"**{copy['free_warning']}**",
    )

_max_mats = 8 if _tier == "pro" else 2

render_kpi_strip(
    [
        {"label": "Tier Limit", "value": _max_mats, "trend": "Materials", "trend_state": "steady", "footnote": "Max side-by-side materials"},
        {"label": "Color Set", "value": len(OKABE_ITO), "trend": "Accessible", "trend_state": "up", "footnote": "Colorblind-safe palette"},
        {"label": "Photon Metrics", "value": "MAC/LAC", "trend": "Core", "trend_state": "up", "footnote": "Attenuation basis"},
        {"label": "Thickness Curves", "value": "Tx", "trend": "Sweep", "trend_state": "steady", "footnote": "Transmission versus depth"},
        {"label": "Neutron Metric", "value": "FNRCS", "trend": "NGCal", "trend_state": "neutral", "footnote": "Fast neutron removal"},
        {"label": "Export", "value": "PNG/PDF/XLSX", "trend": "Report", "trend_state": "steady", "footnote": "Tier-aware export stack"},
    ],
    title="ShieldLab Comparison Control Strip",
    subtitle="Multi-material photon and neutron benchmarking with export-ready ranking analytics.",
)

st.divider()

st.subheader("1. Define Materials")

_PRESETS: dict[str, dict] = {
    "Lead (Pb)":            {"formula": "Pb",      "density": 11.35},
    "Concrete (ordinary)":  {"formula": "SiO2",    "density": 2.35},
    "Iron (Fe)":            {"formula": "Fe",       "density": 7.87},
    "Water (H2O)":          {"formula": "H2O",     "density": 1.00},
    "Polyethylene (PE)":    {"formula": "C2H4",    "density": 0.94},
    "Bismuth (Bi)":         {"formula": "Bi",      "density": 9.78},
    "Tungsten (W)":         {"formula": "W",       "density": 19.3},
    "Barite concrete":      {"formula": "BaSO4",   "density": 3.20},
    "Paraffin wax":         {"formula": "C25H52",  "density": 0.90},
    "Custom":             {"formula": "",        "density": 1.0},
}

n_mats = int(st.number_input(
    "Number of materials to compare",
    min_value=2, max_value=_max_mats,
    value=min(3, _max_mats), step=1,
    help=f"Free tier: up to 2 materials. Pro: up to 8 materials. Current tier: **{_tier}**.",
))

mat_specs: list[dict] = []

cols_hdr = st.columns([2, 2, 1, 2])
cols_hdr[0].markdown("**Preset / name**")
cols_hdr[1].markdown("**Formula**")
cols_hdr[2].markdown("**ρ (g/cm³)**")
cols_hdr[3].markdown("**Label**")

for i in range(n_mats):
    colour = OKABE_ITO[i % len(OKABE_ITO)]
    c0, c1, c2, c3 = st.columns([2, 2, 1, 2])
    preset_keys = list(_PRESETS.keys())
    default_idx = i % (len(preset_keys) - 1)  # cycle through presets, skip "Custom"
    with c0:
        preset = st.selectbox(
            "Preset", preset_keys, index=default_idx,
            key=f"cmp_preset_{i}", label_visibility="collapsed",
        )
    p = _PRESETS[preset]
    with c1:
        formula = st.text_input(
            "Formula", value=p["formula"],
            key=f"cmp_formula_{i}", label_visibility="collapsed",
        )
    with c2:
        density = st.number_input(
            "?", value=float(p["density"]), min_value=0.001, max_value=30.0,
            format="%.3f", key=f"cmp_rho_{i}", label_visibility="collapsed",
        )
    with c3:
        label = st.text_input(
            "Label",
            value=preset if preset != "Custom" else formula,
            key=f"cmp_label_{i}", label_visibility="collapsed",
        )
    if formula.strip():
        mat_specs.append({
            "label": label.strip() or formula.strip(),
            "formula": formula.strip(),
            "density": float(density),
            "colour": colour,
        })

st.subheader("2. Energy and Thickness Range")
ec1, ec2, ec3, ec4, ec5 = st.columns(5)
with ec1:
    E_min_keV = st.number_input("E min (keV)", value=10.0,  min_value=0.001, format="%.2f")
with ec2:
    E_max_keV = st.number_input("E max (keV)", value=10000.0, min_value=1.0, format="%.1f")
with ec3:
    n_pts = st.number_input("E points", value=60, min_value=5, max_value=500, step=5)
with ec4:
    t_max = st.number_input("Max thickness (cm)", value=20.0, min_value=0.1, format="%.2f")
with ec5:
    gp_ref = st.selectbox("G-P buildup ref", [m for m in GP_MATERIALS if m not in ("Fe","Pb","H2O")])

E_arr = np.logspace(np.log10(E_min_keV * 1e-3), np.log10(E_max_keV * 1e-3), int(n_pts))
T_arr = np.linspace(0.5, float(t_max), 40)

st.divider()
run_btn = st.button(
    "Compare Materials", type="primary",
    disabled=len(mat_specs) < 2, width="stretch",
)

auto_run_bare = _is_bare_mode() and "cmp_results" not in st.session_state and len(mat_specs) >= 2

if (run_btn or auto_run_bare) and len(mat_specs) >= 2:
    # Resolve mass fractions and compute for each material
    results: list[dict] = []
    errors: list[str] = []

    prog = st.progress(0, text="Computing...")
    for idx, spec in enumerate(mat_specs):
        prog.progress((idx) / len(mat_specs), text=f"Computing {spec['label']}...")
        try:
            results.append(_build_result(spec, E_arr, T_arr, gp_ref))
        except Exception as exc:
            errors.append(f"**{spec['label']}**: {exc}")

    prog.progress(1.0, text="Done.")

    if errors:
        for e in errors:
            st.error(e)

    if len(results) < 2:
        if not auto_run_bare:
            st.stop()

    st.session_state["cmp_results"] = results
    st.session_state["cmp_E_arr"]   = E_arr
    st.session_state["cmp_T_arr"]   = T_arr

if "cmp_results" not in st.session_state:
    if auto_run_bare:
        st.session_state["cmp_results"] = []
        st.session_state["cmp_E_arr"] = E_arr
        st.session_state["cmp_T_arr"] = T_arr
    else:
        st.stop()

results: list[dict] = st.session_state.get("cmp_results", [])
E_arr   = st.session_state.get("cmp_E_arr", E_arr)
T_arr   = st.session_state.get("cmp_T_arr", T_arr)

if len(results) < 2 and _is_bare_mode() and len(mat_specs) >= 2:
    _bare_results: list[dict] = []
    for _spec in mat_specs[:2]:
        try:
            _bare_results.append(_build_result(_spec, E_arr, T_arr, gp_ref))
        except Exception:
            _log.debug("Could not build bare-mode comparison result for spec %s", _spec, exc_info=True)
    if len(_bare_results) >= 2:
        results = _bare_results
        st.session_state["cmp_results"] = _bare_results

if len(results) < 2:
    if _is_bare_mode():
        # Phase 0 hardening: previous "Placeholder A/B" fallback removed.
        # Bare-mode rendering must not fabricate scientific data.
        st.session_state["cmp_results"] = []
        st.stop()
    else:
        st.info("Define at least two materials and click Compare Materials.")
        st.stop()

E_keV   = E_arr * 1000

st.divider()
st.markdown(f"## Comparison Results - {', '.join(r['label'] for r in results)}")

render_panel_header(
    "Comparison Analytics Panels",
    "Explore attenuation, layer equivalence, transport curves, neutron shielding, and ranking outputs.",
    legend_items=[("Photon", "#10b981"), ("Neutron", "#f59e0b"), ("Ranking", "#3b82f6")],
    controls=["Charts", "Tables", "Exports"],
)

tab_mac, tab_hvl, tab_trans, tab_neutron, tab_rank, tab_table = st.tabs([
    "MAC / LAC",
    "HVL and TVL",
    "Transmission",
    "Neutron (FNRCS)",
    "Ranking",
    "Full Tables",
])

with tab_mac:
    render_panel_header(
        "Mass and Linear Attenuation Coefficients vs Energy",
        "Side-by-side photon attenuation response across selected materials.",
        controls=["MAC", "LAC", "mu_en/rho"],
    )

    fig_mac, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    ax_mac, ax_lac = axes

    for r in results:
        ax_mac.loglog(E_keV, r["mac"], color=r["colour"], lw=2, label=r["label"])
        ax_lac.loglog(E_keV, r["lac"], color=r["colour"], lw=2, label=r["label"])

    ax_mac.set_xlabel("Energy (keV)")
    ax_mac.set_ylabel("μ/ρ (cm²/g)")
    ax_mac.set_title("Mass Attenuation Coefficient")
    ax_mac.legend(fontsize=8)
    ax_mac.grid(True, which="both", alpha=0.25)

    ax_lac.set_xlabel("Energy (keV)")
    ax_lac.set_ylabel("μ (cm⁻¹)")
    ax_lac.set_title("Linear Attenuation Coefficient")
    ax_lac.legend(fontsize=8)
    ax_lac.grid(True, which="both", alpha=0.25)

    finish_shieldlab_figure(fig_mac)
    labels_str = "_".join(r["label"].replace(" ", "") for r in results)
    caption = (
        f"Mass (left) and linear (right) attenuation coefficients vs photon energy "
        f"for {', '.join(r['label'] for r in results)}. "
        f"Data: NIST XrayMassCoef. Computed with ShieldLab G4."
    )
    figure_download_buttons(fig_mac, basename=f"mac_comparison_{labels_str}",
                             tier=_tier, caption=caption, key_prefix="cmp_mac")
    plt.close(fig_mac)

    # Energy absorption coefficient
    st.markdown("---")
    st.markdown("**Energy-absorption coefficient μen/ρ:**")
    fig_en, ax_en = plt.subplots(figsize=(9, 4))
    for r in results:
        ax_en.loglog(E_keV, r["mac_en"], color=r["colour"], lw=2, label=r["label"])
    ax_en.set_xlabel("Energy (keV)")
    ax_en.set_ylabel("μen/ρ (cm²/g)")
    ax_en.set_title("Energy-Absorption Coefficient")
    ax_en.legend(fontsize=8)
    ax_en.grid(True, which="both", alpha=0.25)
    finish_shieldlab_figure(fig_en)
    figure_download_buttons(fig_en, basename=f"mac_en_comparison_{labels_str}",
                             tier=_tier, caption=caption, key_prefix="cmp_mac_en")
    plt.close(fig_en)

with tab_hvl:
    render_panel_header(
        "Half-Value Layer and Tenth-Value Layer vs Energy",
        "Compare shielding depth performance and mean free path trends.",
        controls=["HVL", "TVL", "MFP"],
    )

    fig_ht, axes_ht = plt.subplots(1, 2, figsize=(12, 4.5))
    ax_hvl, ax_tvl = axes_ht

    for r in results:
        ax_hvl.semilogx(E_keV, r["hvl"], color=r["colour"], lw=2, label=r["label"])
        ax_tvl.semilogx(E_keV, r["tvl"], color=r["colour"], lw=2, label=r["label"])

    ax_hvl.set_xlabel("Energy (keV)")
    ax_hvl.set_ylabel("HVL (cm)")
    ax_hvl.set_title("Half-Value Layer")
    ax_hvl.legend(fontsize=8)
    ax_hvl.grid(True, which="both", alpha=0.25)

    ax_tvl.set_xlabel("Energy (keV)")
    ax_tvl.set_ylabel("TVL (cm)")
    ax_tvl.set_title("Tenth-Value Layer")
    ax_tvl.legend(fontsize=8)
    ax_tvl.grid(True, which="both", alpha=0.25)

    finish_shieldlab_figure(fig_ht)
    ht_caption = (
        f"HVL (left) and TVL (right) vs photon energy for "
        f"{', '.join(r['label'] for r in results)}. "
        f"Computed from NIST MAC data. ShieldLab G4."
    )
    figure_download_buttons(fig_ht, basename=f"hvl_tvl_comparison_{labels_str}",
                             tier=_tier, caption=ht_caption, key_prefix="cmp_hvl")
    plt.close(fig_ht)

    # MFP
    st.markdown("---")
    st.markdown("**Mean Free Path:**")
    fig_mfp, ax_mfp = plt.subplots(figsize=(9, 4))
    for r in results:
        ax_mfp.semilogx(E_keV, r["mfp"], color=r["colour"], lw=2, label=r["label"])
    ax_mfp.set_xlabel("Energy (keV)")
    ax_mfp.set_ylabel("MFP (cm)")
    ax_mfp.set_title("Mean Free Path")
    ax_mfp.legend(fontsize=8)
    ax_mfp.grid(True, which="both", alpha=0.25)
    finish_shieldlab_figure(fig_mfp)
    figure_download_buttons(fig_mfp, basename=f"mfp_comparison_{labels_str}",
                             tier=_tier, caption=ht_caption, key_prefix="cmp_mfp")
    plt.close(fig_mfp)

with tab_trans:
    render_panel_header(
        "Transmission vs Thickness",
        "Interactive energy selections for exponential attenuation curves.",
        controls=["Energy Select", "Curve Set", "Export"],
    )

    # Energy selector
    e_keV_options = [round(float(e), 2) for e in E_keV]
    # Pick a few representative energies by default
    default_energies = [
        min(e_keV_options, key=lambda e: abs(e - 100)),
        min(e_keV_options, key=lambda e: abs(e - 662)),
        min(e_keV_options, key=lambda e: abs(e - 1250)),
    ]
    default_energies = list(dict.fromkeys(default_energies))  # dedup, preserve order

    sel_energies = st.multiselect(
        "Select energies (keV) for T(x) comparison",
        options=e_keV_options,
        default=default_energies,
        max_selections=5,
    )

    if sel_energies:
        x_arr = np.linspace(0, float(T_arr.max()), 200)

        for e_sel in sel_energies:
            e_idx = int(np.argmin(np.abs(E_keV - e_sel)))
            fig_tv, ax_tv = plt.subplots(figsize=(9, 4))

            for r in results:
                mac_sel = float(r["mac"][e_idx])
                lac_sel = mac_sel * r["density"]
                T_narrow = np.exp(-lac_sel * x_arr)
                ax_tv.semilogy(x_arr, T_narrow, color=r["colour"], lw=2, label=r["label"])

            ax_tv.set_xlabel("Thickness (cm)")
            ax_tv.set_ylabel("Transmission (narrow beam)")
            ax_tv.set_title(f"Transmission vs Thickness at {e_sel:.1f} keV")
            ax_tv.legend(fontsize=8)
            ax_tv.grid(True, which="both", alpha=0.25)
            finish_shieldlab_figure(fig_tv)

            tv_caption = (
                f"Narrow-beam transmission vs thickness at {e_sel:.1f} keV for "
                f"{', '.join(r['label'] for r in results)}. ShieldLab G4."
            )
            figure_download_buttons(
                fig_tv,
                basename=f"transmission_comparison_{labels_str}_{e_sel:.0f}keV",
                tier=_tier,
                caption=tv_caption,
                key_prefix=f"cmp_trans_{e_sel:.0f}",
            )
            plt.close(fig_tv)
    else:
        st.info("Select at least one energy above.")

with tab_neutron:
    render_panel_header(
        "Fast Neutron Removal - FNRCS / NGCal",
        "Neutron removal coefficients, equivalent HVL/TVL, and transport decay curves.",
        controls=["Sigma_R", "Table", "Curve"],
    )

    neutron_rows = []
    for r in results:
        neutron_rows.append({
            "Material":       r["label"],
            "ρ (g/cm³)":      f"{r['density']:.3f}",
            "Σ_R (cm⁻¹)":    f"{r['sigma_R']:.4f}",
            "HVL_n (cm)":     f"{r['hvl_n']:.3f}",
            "TVL_n (cm)":     f"{r['tvl_n']:.3f}",
            "MFP_n (cm)":     f"{1/r['sigma_R']:.3f}" if r["sigma_R"] > 0 else "n/a",
        })
    st.dataframe(pd.DataFrame(neutron_rows), width="stretch", hide_index=True)

    # Bar chart: Sigma_R
    fig_fn, ax_fn = plt.subplots(figsize=(8, 3.5))
    labels_list = [r["label"] for r in results]
    sigma_list  = [r["sigma_R"] for r in results]
    colours     = [r["colour"] for r in results]
    bars = ax_fn.bar(labels_list, sigma_list, color=colours, edgecolor="k", linewidth=0.6)
    ax_fn.set_ylabel("Σ_R (cm⁻¹)")
    ax_fn.set_title("Fast Neutron Removal Cross Section")
    ax_fn.bar_label(bars, fmt="%.4f", fontsize=7, padding=2)
    ax_fn.grid(axis="y", alpha=0.3)
    finish_shieldlab_figure(fig_fn)
    fn_caption = (
        f"Fast neutron removal cross section Σ_R for "
        f"{', '.join(r['label'] for r in results)}. "
        f"Computed via NGCal method (Shultis & Faw, 2000). ShieldLab G4."
    )
    figure_download_buttons(fig_fn, basename=f"fnrcs_comparison_{labels_str}",
                             tier=_tier, caption=fn_caption, key_prefix="cmp_fn")
    plt.close(fig_fn)

    # Neutron transmission vs thickness comparison
    st.markdown("---")
    st.markdown("**Neutron transmission vs thickness:**")
    x_n = np.linspace(0, float(T_arr.max()), 200)
    fig_nt, ax_nt = plt.subplots(figsize=(9, 4))
    for r in results:
        if r["sigma_R"] > 0:
            T_n = np.exp(-r["sigma_R"] * x_n)
            ax_nt.semilogy(x_n, T_n, color=r["colour"], lw=2, label=r["label"])
    ax_nt.set_xlabel("Thickness (cm)")
    ax_nt.set_ylabel("Neutron Transmission")
    ax_nt.set_title("Fast Neutron Transmission vs Thickness")
    ax_nt.legend(fontsize=8)
    ax_nt.grid(True, which="both", alpha=0.25)
    finish_shieldlab_figure(fig_nt)
    figure_download_buttons(fig_nt, basename=f"neutron_transmission_comparison_{labels_str}",
                             tier=_tier, caption=fn_caption, key_prefix="cmp_nt")
    plt.close(fig_nt)

with tab_rank:
    render_panel_header(
        "Performance Ranking",
        "Normalized scoring across photon and neutron shielding indicators.",
        controls=["Ranking", "Radar", "Summary"],
    )
    st.caption(
        "Rank by shielding effectiveness at selected energies. "
        "Lower HVL = better photon attenuation. Lower HVL_n = better neutron shielding."
    )

    # Representative energies for ranking
    rank_energies_keV = [100.0, 662.0, 1250.0]
    rank_energies_keV = [
        min(e_keV_options, key=lambda e: abs(e - target))
        for target in rank_energies_keV
    ]

    rank_rows = []
    for r in results:
        row: dict = {
            "Material":   r["label"],
            "ρ (g/cm³)":  f"{r['density']:.3f}",
        }
        for ek in rank_energies_keV:
            ei = int(np.argmin(np.abs(E_keV - ek)))
            row[f"HVL@{ek:.0f}keV (cm)"] = f"{r['hvl'][ei]:.3f}"
            row[f"MAC@{ek:.0f}keV (cm²/g)"] = f"{r['mac'][ei]:.4f}"
        row["Σ_R (cm⁻¹)"]  = f"{r['sigma_R']:.4f}"
        row["HVL_n (cm)"]   = f"{r['hvl_n']:.3f}"
        row["Zeff (n=3.5)"] = f"{r['desc'].get('Zeff_3p5', float('nan')):.3f}"
        rank_rows.append(row)

    df_rank = pd.DataFrame(rank_rows)
    st.dataframe(df_rank, width="stretch", hide_index=True)

    # Radar chart (spider plot) for normalised scores
    st.markdown("---")
    st.markdown("**Normalised performance radar** (higher = better for each axis):")

    metrics_radar = ["MAC@662keV", "HVL@662keV (lower=better)", "Σ_R", "Zeff"]
    try:
        e662_idx = int(np.argmin(np.abs(E_keV - 662.0)))
        radar_vals: list[list[float]] = []
        for r in results:
            mac662 = float(r["mac"][e662_idx])
            hvl662 = float(r["hvl"][e662_idx])
            sigma  = float(r["sigma_R"])
            zeff   = float(r["desc"].get("Zeff_3p5", 1.0))
            radar_vals.append([mac662, 1.0 / max(hvl662, 1e-6), sigma, zeff])

        # Normalise each metric to [0, 1]
        radar_arr = np.array(radar_vals, dtype=float)  # shape (n_mats, 4)
        col_max = radar_arr.max(axis=0)
        col_max[col_max == 0] = 1.0
        radar_norm = radar_arr / col_max

        angles = np.linspace(0, 2 * np.pi, len(metrics_radar), endpoint=False).tolist()
        angles += angles[:1]  # close polygon

        fig_radar, ax_r = plt.subplots(figsize=(5.5, 5.5), subplot_kw=dict(polar=True))
        ax_r.set_theta_offset(np.pi / 2)
        ax_r.set_theta_direction(-1)
        ax_r.set_thetagrids(np.degrees(angles[:-1]),
                            ["MAC (662 keV)", "1/HVL (662 keV)", "Σ_R", "Zeff"],
                            fontsize=9)

        for i, r in enumerate(results):
            vals = radar_norm[i].tolist() + [radar_norm[i][0]]
            ax_r.plot(angles, vals, color=r["colour"], lw=2, label=r["label"])
            ax_r.fill(angles, vals, color=r["colour"], alpha=0.08)

        ax_r.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15), fontsize=8)
        ax_r.set_title("Normalised Shielding Performance", pad=15)
        finish_shieldlab_figure(fig_radar)
        radar_caption = (
            f"Normalised radar chart comparing {', '.join(r['label'] for r in results)} "
            f"across four key shielding metrics. All axes scaled to [0,1] relative to best performer. "
            f"ShieldLab G4."
        )
        figure_download_buttons(fig_radar, basename=f"radar_comparison_{labels_str}",
                                 tier=_tier, caption=radar_caption, key_prefix="cmp_radar")
        plt.close(fig_radar)
    except Exception as exc:
        st.warning(f"Radar chart: {exc}")

with tab_table:
    render_panel_header(
        "Full Shielding Parameter Tables",
        "Detailed per-material coefficient tables with combined exports.",
        controls=["Table", "CSV", "Excel"],
    )

    mat_sel = st.selectbox(
        "Select material",
        options=[r["label"] for r in results],
        key="cmp_table_sel",
    )
    r_sel = next(r for r in results if r["label"] == mat_sel)
    cols_show = ["Energy_keV", _col(r_sel["df"], *MAC_COL_CANDIDATES), _col(r_sel["df"], *MAC_EN_COL_CANDIDATES), _col(r_sel["df"], *LAC_COL_CANDIDATES),
                 "HVL (cm)", "TVL (cm)", "MFP (cm)"]
    st.dataframe(
        r_sel["df"][[c for c in cols_show if c in r_sel["df"].columns]].round(6),
        width="stretch", hide_index=True,
    )

    # Combined CSV export (all materials, key columns)
    st.markdown("---")
    st.markdown("**Download combined summary:**")
    rows_csv = []
    for r in results:
        for i, e_k in enumerate(E_keV):
            rows_csv.append({
                "Material":       r["label"],
                "Density_g_cm3":  r["density"],
                "Energy_keV":     round(e_k, 4),
                "MAC_cm2g":       round(float(r["mac"][i]), 6),
                "MAC_en_cm2g":    round(float(r["mac_en"][i]), 6),
                "LAC_cm":         round(float(r["lac"][i]), 6),
                "HVL_cm":         round(float(r["hvl"][i]), 6),
                "TVL_cm":         round(float(r["tvl"][i]), 6),
                "MFP_cm":         round(float(r["mfp"][i]), 6),
            })
    df_csv = pd.DataFrame(rows_csv)
    csv_bytes = df_csv.to_csv(index=False).encode()
    st.download_button(
        "Download combined CSV",
        data=csv_bytes,
        file_name=f"comparison_{labels_str}.csv",
        mime="text/csv",
    )

    # Excel with one sheet per material + summary sheet
    import io
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        df_rank.to_excel(xw, sheet_name="Summary_Ranking", index=False)
        for r in results:
            sheet = r["label"][:28].replace("/", "_").replace("\\", "_")
            r["df"].to_excel(xw, sheet_name=sheet, index=False)
    buf.seek(0)
    st.download_button(
        "Download Excel (all sheets)",
        data=buf,
        file_name=f"comparison_{labels_str}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        disabled=(_tier == "free"),
        help="Excel export is a Pro feature." if _tier == "free" else "",
    )
    if _tier == "free":
        st.caption("Excel export requires Pro. CSV is always free.")



