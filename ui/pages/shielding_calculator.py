"""Shielding calculator with XCOM, Phy-X, EpiXS, and NGCal tools.

Covers:
    XCOM  - photon cross-section components (coherent, Compton, photoelectric, pair)
    Phy-X - MAC, LAC, HVL, TVL, MFP, Zeff, Neff, electron density, EBF, EABF, RPE
    EpiXS - energy-absorption MAC, kerma, dose rate
    NGCal - fast neutron removal cross section (FNRCS), neutron HVL/TVL
"""
from __future__ import annotations

import io
import json
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
_UI_DIR = Path(__file__).resolve().parent.parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from bootstrap import ensure_project_paths  # noqa: E402

ensure_project_paths()

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
except Exception:  # pragma: no cover - fallback when runtime internals are unavailable
    get_script_run_ctx = None

import config  # noqa: E402 - loads project constants

from shieldlab.viz.style import apply_journal_style, finish_shieldlab_figure
from shieldlab.viz.export import figure_download_buttons
from shieldlab.viz.captions import auto_caption
from shieldlab.content import PAGE_COPY
from auth import get_user_tier, render_tier_dev_toggle
from components.error_reporter import render_error_reporter
from components.layout import render_page_hero
from components.enterprise_ui import render_breadcrumb, render_kpi_strip, render_metric_strip, render_panel_header
apply_journal_style("shieldlab_web")

from shieldlab.core.materials import resolve_material_mass_fractions
from shieldlab.core.descriptors import material_descriptors
from shieldlab.io.descriptor_schema import descriptor_mapping_to_rows
from shieldlab.physics.shielding_params import (
    STANDARD_SOURCES, XCOM_ENERGY_GRID, GP_MATERIALS,
    compute_shielding_table, compute_transmission_vs_thickness,
    compute_multilayer, compute_fnrcs, compute_fnrcs_hvl,
    gp_buildup_factor, mean_atomic_molar_mass, zeff_energy_dependent,
    compute_zeq,
)

# Particles
_PARTICLES = {
    "gamma":        ("gamma",   "photon"),
    "electron e-":       ("e-",      "charged"),
    "positron e+":       ("e+",      "charged"),
    "proton (p)":        ("proton",  "charged"),
    "alpha":         ("alpha",   "charged"),
    "neutron (n)":       ("neutron", "neutral"),
    "mu- (muon)":        ("mu-",     "charged"),
    "X-ray (photon)":    ("gamma",   "photon"),
}

_PHOTON_PARTICLES = {"gamma", "e+"}  # positron also creates 511 keV photons
MAC_COL_CANDIDATES = ("μ/ρ (cm²/g)", "mu/rho (cm^2/g)", "?/? (cm�/g)")
MAC_EN_COL_CANDIDATES = ("μen/ρ (cm²/g)", "mu_en/rho (cm^2/g)", "?en/? (cm�/g)")
LAC_COL_CANDIDATES = ("μ (cm⁻¹)", "mu (cm^-1)", "? (cm?�)")
ACS_COL_CANDIDATES = ("ACS (cm²/atom)", "ACS (cm^2/atom)", "ACS (cm�/atom)")
ECS_COL_CANDIDATES = ("ECS (cm²/elec)", "ECS (cm^2/elec)", "ECS (cm�/elec)")
MFP_X_COL_CANDIDATES = ("μx (MFP)", "mu*x (MFP)", "?x (MFP)")


def _is_bare_mode() -> bool:
    if get_script_run_ctx is None:
        return False
    return get_script_run_ctx() is None


def _pick_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str:
    for col in candidates:
        if col in df.columns:
            return col
    raise KeyError(f"None of the expected columns found: {candidates}")


def _composer_physics_note(mode: str) -> str:
    notes = {
        "formula": "Physics model: stoichiometric parsing of the chemical formula, then conversion to elemental mass fractions using tabulated atomic weights.",
        "mass_fractions": "Physics model: direct elemental mass fractions are used as entered, after validation that the fractions form a physical composition.",
        "formula_mass_fractions": "Physics model: compound weight fractions are normalised, each compound is expanded to elemental mass fractions, then the mixture rule is applied.",
        "mixture": "Physics model: phase weight fractions are normalised and each phase contributes to the final elemental composition through the same mixture rule used in shielding calculations.",
        "nanocomposite": "Physics model: matrix and filler weight fractions are combined into one weighted phase mixture, then expanded to elemental mass fractions before descriptor evaluation.",
        "volume_fractions": "Physics model: each phase is converted from volume fraction to effective mass contribution using $w_i \\propto \\rho_i \\phi_i$, then expanded to elemental mass fractions.",
    }
    return notes.get(mode, "")


def _phase_preview_rows(material_dict: dict) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if material_dict.get("formula_mass_fractions"):
        fractions = {str(key): float(value) for key, value in material_dict["formula_mass_fractions"].items()}
        total = sum(fractions.values())
        for formula, value in fractions.items():
            rows.append({
                "Phase": formula,
                "Input": f"{value:.4f}",
                "Normalised share": f"{value / total:.4f}",
                "Basis": "weight fraction",
            })
    elif material_dict.get("mixture"):
        phases = material_dict["mixture"]
        total = sum(float(phase["weight_fraction"]) for phase in phases)
        for phase in phases:
            value = float(phase["weight_fraction"])
            rows.append({
                "Phase": str(phase["formula"]),
                "Input": f"{value:.4f}",
                "Normalised share": f"{value / total:.4f}",
                "Basis": "weight fraction",
            })
    elif material_dict.get("nanocomposite"):
        nc = material_dict["nanocomposite"]
        phases = [
            {"label": f"Matrix: {nc['matrix']['formula']}", "value": float(nc["matrix"]["weight_fraction"])}
        ]
        phases.extend(
            {"label": f"Filler: {filler['formula']}", "value": float(filler["weight_fraction"])}
            for filler in nc.get("fillers") or []
        )
        total = sum(phase["value"] for phase in phases)
        for phase in phases:
            rows.append({
                "Phase": phase["label"],
                "Input": f"{phase['value']:.4f}",
                "Normalised share": f"{phase['value'] / total:.4f}",
                "Basis": "weight fraction",
            })
    elif material_dict.get("volume_fractions"):
        phases = material_dict["volume_fractions"]
        mass_proxies = [float(phase["density_g_cm3"]) * float(phase["volume_fraction"]) for phase in phases]
        total = sum(mass_proxies)
        for phase, proxy in zip(phases, mass_proxies):
            rows.append({
                "Phase": str(phase["formula"]),
                "Input": f"rho*phi = {proxy:.4f}",
                "Normalised share": f"{proxy / total:.4f}",
                "Basis": "mass proxy from volume fraction",
            })
    return rows

render_tier_dev_toggle()
_tier = get_user_tier()
copy = PAGE_COPY["shielding_calculator"]

render_page_hero(str(copy["title"]), str(copy["caption"]), "Analytical Shielding Physics")
render_breadcrumb(["ShieldLab G4", "Analysis"], current="Shielding Calculator")
st.info(
    str(copy["data_source"]),
)

render_kpi_strip(
    [
        {"label": "Physics Engines", "value": "4", "trend": "XCOM+", "trend_state": "up", "footnote": "XCOM, Phy-X, EpiXS, NGCal"},
        {"label": "Particles", "value": len(_PARTICLES), "trend": "Configured", "trend_state": "steady", "footnote": "Gamma, charged, neutron modes"},
        {"label": "Standard Sources", "value": len(STANDARD_SOURCES), "trend": "Library", "trend_state": "up", "footnote": "Reference isotope entries"},
        {"label": "Energy Grid", "value": len(XCOM_ENERGY_GRID), "trend": "Dense", "trend_state": "steady", "footnote": "Default interpolation nodes"},
        {"label": "G-P References", "value": len(GP_MATERIALS), "trend": "Buildup", "trend_state": "neutral", "footnote": "Photon buildup material refs"},
        {"label": "Tier", "value": _tier.upper(), "trend": "Session", "trend_state": "neutral", "footnote": "Current capability profile"},
    ],
    title="ShieldLab Analytical Control Strip",
    subtitle="Cross-sections, buildup, descriptors, multilayer transport, and publication export in one workspace.",
)

# Mobile viewport guard
if st.session_state.get("_mobile_banner", True):
        # Keep guidance deterministic and avoid deprecated embedded html components.
    st.warning(
        str(copy["mobile_warning"]),
    )
    st.session_state["_mobile_banner"] = False  # show only once per session

st.divider()

with st.expander(str(copy["section_material"]), expanded=True):
    st.markdown(str(copy["material_blurb"]))

    with st.expander(str(copy["section_compendium"]), expanded=False):
        try:
            from shieldlab.data.compendium import list_names, get_by_name
            _comp_cats  = ["(all)", "shielding", "tissue", "construction",
                           "detector", "gas", "polymer", "other"]
            _comp_cat   = st.selectbox("Category", _comp_cats, key="comp_cat",
                                        help="Filter materials by category")
            _comp_names = list_names(None if _comp_cat == "(all)" else _comp_cat)
            _comp_sel   = st.selectbox("Material", [""] + _comp_names,
                                        format_func=lambda x: x or "-- select --",
                                        key="comp_sel")
            if _comp_sel:
                _cm = get_by_name(_comp_sel)
                if _cm:
                    st.caption(
                        f"**Formula:** {_cm['formula'] or 'mixture'}  |  "
                        f"**Density:** {_cm['density']} g/cm³  |  "
                        f"**Ref:** {_cm['reference']}"
                    )
                    if st.button("Load into calculator", key="comp_load_btn"):
                        st.session_state["_comp_loaded"] = _cm
                        st.rerun()
        except Exception as _ce:
            st.caption(f"COMPENDIUM unavailable: {_ce}")

    # Apply a previously loaded COMPENDIUM entry
    _comp_loaded = st.session_state.pop("_comp_loaded", None)

    _MODE_HELP = {
        "formula":               "Single compound  (e.g. PbWO4, Bi2O3, BaSO4, H2O)",
        "mass_fractions":        "Elemental mass fractions  (e.g. Pb:0.85, O:0.10, S:0.05)",
        "formula_mass_fractions":"Compounds by weight  (e.g. PbO:0.6, B2O3:0.2, SiO2:0.2)",
        "mixture":               "Compounds mixed by weight fraction",
        "nanocomposite":         "Polymer matrix + nanoparticle fillers",
        "volume_fractions":      "Phases by volume fraction and bulk density",
    }

    c_mode, c_name, c_dens = st.columns([2, 2, 1])
    with c_mode:
        comp_mode = st.selectbox("Composition mode", list(_MODE_HELP.keys()),
                                  format_func=lambda m: f"{m} - {_MODE_HELP[m].split('(')[0].strip()}")
    st.caption(f"**{comp_mode}**: {_MODE_HELP[comp_mode]}")
    st.info(_composer_physics_note(comp_mode))
    with c_name:
        _default_name = (_comp_loaded["name"] if _comp_loaded else "MyMaterial")
        mat_name = st.text_input("Material name", value=_default_name,
                                  help="Label used in results and export.")
    with c_dens:
        _default_rho = float(_comp_loaded["density"]) if _comp_loaded else 2.0
        density = st.number_input("Density (g/cm³)", value=_default_rho,
                                   min_value=0.001, max_value=30.0, format="%.4f",
                       help="Bulk density of the shield material (g/cm³).")

    # If a COMPENDIUM entry was loaded, pre-fill the mass_fractions text area
    _comp_mf_default = ""
    if _comp_loaded and _comp_loaded.get("mass_fracs"):
        _comp_mf_default = "\n".join(
            f"{el}: {wf}" for el, wf in _comp_loaded["mass_fracs"].items()
        )

    mat_dict_raw: dict | None = None
    mat_input_err: str | None = None

    if comp_mode == "formula":
        formula_in = st.text_input("Chemical formula", value="Pb",
                                    help="Hill notation: Pb, H2O, PbWO4, Bi2O3, BaSO4")
        if formula_in.strip():
            mat_dict_raw = {"name": mat_name, "density_g_cm3": density,
                             "formula": formula_in.strip()}

    elif comp_mode == "mass_fractions":
        st.markdown("Element : fraction (must sum to 1.0). Example: `Pb: 0.85, O: 0.10, S: 0.05`")
        _mf_default = _comp_mf_default if _comp_mf_default else "Pb: 0.85\nO: 0.10\nS: 0.05"
        mf_text = st.text_area("Elemental mass fractions", value=_mf_default,
                                height=110)
        mf_d = {}
        try:
            for tok in mf_text.replace("\n", ",").split(","):
                tok = tok.strip()
                if not tok: continue
                el, v = tok.split(":")
                mf_d[el.strip()] = float(v.strip())
            total = sum(mf_d.values())
            if abs(total - 1.0) > 0.01:
                mat_input_err = f"Fractions sum to {total:.4f}; must equal 1.0."
            elif mf_d:
                mat_dict_raw = {"name": mat_name, "density_g_cm3": density,
                                 "mass_fractions": mf_d}
        except Exception as exc:
            mat_input_err = f"Parse error: {exc}"

    elif comp_mode == "formula_mass_fractions":
        st.markdown("Formula : weight fraction (sum = 1.0). Example: `PbO: 0.60, B2O3: 0.20, SiO2: 0.20`")
        fmf_text = st.text_area("Compound weight fractions",
                                 value="PbO: 0.60\nB2O3: 0.20\nSiO2: 0.20", height=110)
        fmf_d = {}
        try:
            for tok in fmf_text.replace("\n", ",").split(","):
                tok = tok.strip()
                if not tok: continue
                f, v = tok.split(":")
                fmf_d[f.strip()] = float(v.strip())
            total = sum(fmf_d.values())
            if abs(total - 1.0) > 0.01:
                mat_input_err = f"Fractions sum to {total:.4f}; must equal 1.0."
            elif fmf_d:
                mat_dict_raw = {"name": mat_name, "density_g_cm3": density,
                                 "formula_mass_fractions": fmf_d}
        except Exception as exc:
            mat_input_err = f"Parse error: {exc}"

    elif comp_mode == "mixture":
        n = int(st.number_input("Number of phases", 2, 10, 2, step=1))
        phases = []
        hdr = st.columns([3, 2]); hdr[0].markdown("**Formula**"); hdr[1].markdown("**Weight fraction**")
        for i in range(n):
            c1, c2 = st.columns([3, 2])
            f = c1.text_input(f"Formula {i+1}", value=["C2H4","Bi2O3"][i] if i<2 else "", key=f"sc_mx_f{i}")
            v = c2.number_input(f"wt {i+1}", value=round(1.0/n, 4),
                                min_value=0.0001, max_value=0.9999, format="%.4f", key=f"sc_mx_v{i}")
            if f.strip(): phases.append({"formula": f.strip(), "weight_fraction": float(v)})
        total = sum(p["weight_fraction"] for p in phases)
        if abs(total - 1.0) > 0.01:
            mat_input_err = f"Weight fractions sum to {total:.4f}; must equal 1.0."
        elif phases:
            mat_dict_raw = {"name": mat_name, "density_g_cm3": density, "mixture": phases}

    elif comp_mode == "nanocomposite":
        c1, c2 = st.columns([3, 2])
        mx_f  = c1.text_input("Matrix formula", value="C2H4")
        mx_wf = c2.number_input("Matrix wt fraction", value=0.70, min_value=0.01, max_value=0.99, format="%.4f")
        n_fill = int(st.number_input("Number of fillers", 1, 5, 1, step=1))
        fillers = []
        remaining = round(1.0 - mx_wf, 6)
        for i in range(n_fill):
            c1, c2 = st.columns([3, 2])
            ff = c1.text_input(f"Filler {i+1}", value="Bi2O3", key=f"sc_nc_f{i}")
            fv = c2.number_input(f"Filler wt {i+1}", value=round(remaining/n_fill, 4),
                                 min_value=0.0001, max_value=0.9999, format="%.4f", key=f"sc_nc_v{i}")
            fillers.append({"formula": ff.strip(), "weight_fraction": float(fv)})
        total = mx_wf + sum(f["weight_fraction"] for f in fillers)
        if abs(total - 1.0) > 0.01:
            mat_input_err = f"Weight fractions sum to {total:.4f}; must equal 1.0."
        elif mx_f.strip():
            mat_dict_raw = {"name": mat_name, "density_g_cm3": density,
                             "nanocomposite": {"matrix": {"formula": mx_f.strip(), "weight_fraction": float(mx_wf)},
                                               "fillers": fillers}}

    elif comp_mode == "volume_fractions":
        n_vf = int(st.number_input("Number of phases", 2, 8, 2, step=1))
        defaults = [("C2H4", 0.94, 0.60), ("BaSO4", 4.50, 0.40)]
        vf_phases = []
        for i in range(n_vf):
            d = defaults[i] if i < len(defaults) else ("", 1.0, round(1.0/n_vf, 4))
            c1, c2, c3 = st.columns([3, 2, 2])
            f   = c1.text_input(f"Formula {i+1}", value=d[0], key=f"sc_vf_f{i}")
            rho = c2.number_input(f"? {i+1}", value=d[1], min_value=0.001, format="%.3f", key=f"sc_vf_r{i}")
            vv  = c3.number_input(f"vol {i+1}", value=d[2], min_value=0.0001, max_value=0.9999,
                                  format="%.4f", key=f"sc_vf_v{i}")
            if f.strip():
                vf_phases.append({"formula": f.strip(), "density_g_cm3": float(rho), "volume_fraction": float(vv)})
        total = sum(p["volume_fraction"] for p in vf_phases)
        if abs(total - 1.0) > 0.01:
            mat_input_err = f"Volume fractions sum to {total:.4f}; must equal 1.0."
        elif vf_phases:
            mat_dict_raw = {"name": mat_name, "density_g_cm3": density, "volume_fractions": vf_phases}

    if mat_input_err:
        st.error(f"Input error: {mat_input_err}")

    # Resolve mass fractions
    mass_fractions: dict[str, float] | None = None
    if mat_dict_raw and not mat_input_err:
        try:
            phase_rows = _phase_preview_rows(mat_dict_raw)
            if phase_rows:
                st.markdown("**Effective phase mixing used in the physics model**")
                st.dataframe(pd.DataFrame(phase_rows), use_container_width=True, hide_index=True)

            mass_fractions = resolve_material_mass_fractions(mat_dict_raw)

            rows = [{
                "Element": el,
                "Mass Fraction": f"{wf:.6f}",
                "wt %": f"{wf * 100:.3f}",
            } for el, wf in sorted(mass_fractions.items(), key=lambda x: -x[1])]
            st.markdown("**Elemental Mass Fractions**")
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=220)

            desc = material_descriptors(mat_name, mass_fractions, density)
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Density", f"{density:.3f} g/cm³")
            c2.metric("Zeff (n=3.5)", f"{desc['Zeff_3p5']:.3f}")
            c3.metric("Molar mass", f"{desc['molar_mass_g_mol']:.2f} g/mol")
            c4.metric("Neff (e⁻/cm³)", f"{desc['Neff_electrons_cm3']:.3e}")
            c5.metric("Mean Z", f"{desc['average_Z']:.2f}")
        except Exception as exc:
            st.warning(f"Descriptor preview: {exc}")

with st.expander(str(copy["section_source"]), expanded=True):
    pc1, pc2 = st.columns([2, 3])
    with pc1:
        p_label = st.selectbox("Particle / Radiation Type", list(_PARTICLES.keys()))
        p_g4name, p_type = _PARTICLES[p_label]

    with pc2:
        energy_mode = st.radio(
            "Energy input method",
            ["Standard source", "Single energy", "Energy range", "Custom list"],
            horizontal=True,
        )

    energies_MeV: np.ndarray | None = None
    energy_display: str = ""

    if energy_mode == "Standard source":
        src_choice = st.selectbox("Standard source", list(STANDARD_SOURCES.keys()))
        src_lines = STANDARD_SOURCES[src_choice]
        energies_MeV = np.array([e for e, _ in src_lines])
        intensities   = np.array([i for _, i in src_lines])
        energy_display = f"{src_choice}"
        df_src = pd.DataFrame({
            'Energy (MeV)': energies_MeV,
            'Energy (keV)': energies_MeV * 1000,
            'Relative Intensity': intensities,
        })
        st.dataframe(df_src, use_container_width=True, hide_index=True, height=120)

    elif energy_mode == "Single energy":
        ec1, ec2 = st.columns([2, 1])
        with ec1:
            single_E = st.number_input("Energy value", value=662.0, min_value=0.001, format="%.4f")
        with ec2:
            single_unit = st.selectbox("Unit", ["keV", "MeV", "eV"])
        conv = {'keV': 1e-3, 'MeV': 1.0, 'eV': 1e-6}[single_unit]
        energies_MeV = np.array([single_E * conv])
        energy_display = f"{single_E:.2f} {single_unit}"

    elif energy_mode == "Energy range":
        rc1, rc2, rc3, rc4 = st.columns([2, 2, 1, 1])
        with rc1:
            E_min = st.number_input("Min energy (keV)", value=10.0, min_value=0.001, format="%.3f")
        with rc2:
            E_max = st.number_input("Max energy (keV)", value=10000.0, min_value=0.01, format="%.3f")
        with rc3:
            n_pts = st.number_input("N points", value=50, min_value=5, max_value=500, step=5)
        with rc4:
            log_lin = st.radio("Scale", ["Log", "Linear"], horizontal=True)
        if log_lin == "Log":
            energies_MeV = np.logspace(np.log10(E_min * 1e-3), np.log10(E_max * 1e-3), int(n_pts))
        else:
            energies_MeV = np.linspace(E_min * 1e-3, E_max * 1e-3, int(n_pts))
        energy_display = f"{E_min:.0f}-{E_max:.0f} keV ({int(n_pts)} pts)"

    elif energy_mode == "Custom list":
        st.markdown("Enter energies one per line or comma-separated. Units: **MeV** unless you append keV.")
        custom_text = st.text_area("Custom energies",
                                    value="0.059\n0.140\n0.365\n0.662\n1.173\n1.332",
                                    height=130)
        parsed = []
        for tok in custom_text.replace("\n", ",").split(","):
            tok = tok.strip()
            if not tok: continue
            try:
                if tok.lower().endswith("kev"):
                    parsed.append(float(tok[:-3].strip()) * 1e-3)
                elif tok.lower().endswith("mev"):
                    parsed.append(float(tok[:-3].strip()))
                else:
                    parsed.append(float(tok))
            except ValueError:
                pass
        energies_MeV = np.array(sorted(set(parsed))) if parsed else None
        if energies_MeV is not None:
            energy_display = f"{len(energies_MeV)} custom energies"

    if p_type == "neutral" and p_g4name == "neutron":
        st.warning(str(copy["neutron_warning"]))

with st.expander(str(copy["section_shield"]), expanded=True):
    sc1, sc2 = st.columns([2, 3])
    with sc1:
        geom_type = st.radio("Geometry", ["Slab (parallel beam)", "Slab (broad beam)"],
                              horizontal=True)
        gp_mat_choice = st.selectbox(
            "Buildup factor reference material (G-P method)",
            [m for m in GP_MATERIALS if m not in ('Fe', 'Pb', 'H2O')],
            help="Used when computing EBF (exposure buildup factor). "
                 "Choose the material that best matches your shield composition.",
        )

    with sc2:
        thickness_mode = st.radio("Thickness input", ["Single", "Grid"], horizontal=True)
        if thickness_mode == "Single":
            t_val = st.number_input("Shield thickness (cm)", value=5.0, min_value=0.001, format="%.4f")
            thicknesses_cm = np.array([t_val])
        else:
            tc1, tc2, tc3 = st.columns(3)
            with tc1:
                t_min = st.number_input("Min (cm)", value=0.5, min_value=0.001, format="%.3f")
            with tc2:
                t_max = st.number_input("Max (cm)", value=20.0, min_value=0.01, format="%.3f")
            with tc3:
                n_t = st.number_input("N points", value=20, min_value=3, max_value=200, step=1)
            thicknesses_cm = np.linspace(t_min, t_max, int(n_t))

    # Multi-layer builder
    st.markdown(str(copy["multilayer_stack_label"]))
    if "sc_layers" not in st.session_state:
        st.session_state.sc_layers = [{"name": "Layer 1", "formula": "Pb",
                                        "density_g_cm3": 11.35, "thickness_cm": 5.0}]

    def _render_layer_row(i: int, lyr: dict) -> dict:
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2.15, 2.15, 1.4], gap="large")
        with c1:
            lyr["name"] = st.text_input("Name", value=lyr["name"], key=f"sc_l_n{i}",
                                         label_visibility="collapsed")
        with c2:
            lyr["formula"] = st.text_input("Formula/NIST", value=lyr.get("formula", ""),
                                            key=f"sc_l_f{i}", label_visibility="collapsed",
                                            help="Chemical formula for MAC lookup")
        with c3:
            lyr["density_g_cm3"] = st.number_input("ρ (g/cm³)", value=lyr["density_g_cm3"],
                                                     min_value=0.001, format="%.3f",
                                                     key=f"sc_l_d{i}", label_visibility="collapsed")
        with c4:
            lyr["thickness_cm"] = st.number_input("thick cm", value=lyr["thickness_cm"],
                                                    min_value=0.001, format="%.4f",
                                                    key=f"sc_l_t{i}", label_visibility="collapsed")
        with c5:
            if st.button("✕", key=f"sc_l_rm{i}", help="Remove layer", use_container_width=True):
                return None
        return lyr

    hdr = st.columns([3, 2, 2.15, 2.15, 1.4], gap="large")
    for h, t in zip(hdr, ["Name", "Formula", "Density (g/cm³)", "Thickness (cm)", ""]):
        h.markdown(f"**{t}**")

    new_layers = []
    for i, lyr in enumerate(st.session_state.sc_layers):
        result = _render_layer_row(i, lyr)
        if result is not None:
            new_layers.append(result)
    st.session_state.sc_layers = new_layers

    if st.button("+ Add layer", use_container_width=True):
        st.session_state.sc_layers.append({"name": f"Layer {len(st.session_state.sc_layers)+1}",
                                             "formula": "Fe", "density_g_cm3": 7.87,
                                             "thickness_cm": 2.0})
        st.rerun()

st.divider()
calc_ready = (mass_fractions is not None) and (energies_MeV is not None) and (not mat_input_err)

c_btn, c_hint = st.columns([1, 4])
with c_btn:
    calc_btn = st.button(str(copy["calc_button"]), type="primary", use_container_width=True,
                          disabled=not calc_ready)
with c_hint:
    if not calc_ready:
        st.warning(str(copy["calc_not_ready"]))
    else:
        st.success(str(copy["calc_ready_msg"]).format(mat_name=mat_name, density=density, energy_display=energy_display))

if calc_btn and calc_ready:
    st.session_state['calc_state'] = {
        'mass_fractions': mass_fractions,
        'density': density,
        'mat_name': mat_name,
        'energies_MeV': energies_MeV,
        'thicknesses_cm': thicknesses_cm,
        'gp_mat': gp_mat_choice,
        'particle': p_g4name,
        'p_type': p_type,
        'energy_display': energy_display,
    }

if "_loaded_session" in st.session_state:
    _restored = st.session_state.pop("_loaded_session")
    _cs_restored = _restored.get("calc_state", _restored if isinstance(_restored, dict) else {})
    if _cs_restored and "mass_fractions" in _cs_restored:
        # normalise numpy arrays (JSON round-trip converts them to lists)
        for _arr_key in ("energies_MeV", "thicknesses_cm"):
            if _arr_key in _cs_restored and not hasattr(_cs_restored[_arr_key], "shape"):
                import numpy as _np_r
                _cs_restored[_arr_key] = _np_r.array(_cs_restored[_arr_key])
        st.session_state["calc_state"] = _cs_restored
        st.success(str(copy["session_restored"]))
        st.rerun()

if "calc_state" not in st.session_state and calc_ready:
    st.session_state["calc_state"] = {
        "mass_fractions": mass_fractions,
        "density": density,
        "mat_name": mat_name,
        "energies_MeV": energies_MeV,
        "thicknesses_cm": thicknesses_cm,
        "gp_mat": gp_mat_choice,
        "particle": p_g4name,
        "p_type": p_type,
        "energy_display": energy_display,
    }

if 'calc_state' not in st.session_state:
    if _is_bare_mode():
        st.session_state["calc_state"] = {
            "mass_fractions": mass_fractions or {"Pb": 1.0},
            "density": density if density > 0 else 11.35,
            "mat_name": mat_name or "Pb",
            "energies_MeV": np.array(energies_MeV if energies_MeV is not None else [0.662]),
            "thicknesses_cm": np.array(thicknesses_cm if thicknesses_cm is not None else [1.0]),
            "gp_mat": gp_mat_choice,
            "particle": p_g4name,
            "p_type": p_type,
            "energy_display": energy_display or "662.00 keV",
        }
    else:
        st.stop()

cs = st.session_state.get('calc_state', {})
mf         = cs.get('mass_fractions', {"Pb": 1.0})
rho        = float(cs.get('density', 11.35))
name       = str(cs.get('mat_name', 'Pb'))
E_arr      = np.asarray(cs.get('energies_MeV', [0.662]))
T_arr      = np.asarray(cs.get('thicknesses_cm', [1.0]))
gp_mat     = str(cs.get('gp_mat', gp_mat_choice))
particle   = str(cs.get('particle', p_g4name))
p_type     = str(cs.get('p_type', p_type))
e_display  = str(cs.get('energy_display', '662.00 keV'))

st.markdown("## " + str(copy["results_heading"]).format(name=name, rho=rho, e_display=e_display))

import importlib
import shieldlab.physics.geometry_viz as geometry_viz

geometry_viz = importlib.reload(geometry_viz)
plot_shielding_geometry = geometry_viz.plot_shielding_geometry
plot_mac_vs_energy = geometry_viz.plot_mac_vs_energy
plot_hvl_tvl_vs_energy = geometry_viz.plot_hvl_tvl_vs_energy
plot_transmission_vs_thickness = geometry_viz.plot_transmission_vs_thickness

geo_layers = [{"name": name, "thickness_cm": float(T_arr.mean()),
               "density_g_cm3": rho}]
fig_geo = plot_shielding_geometry(geo_layers, particle=particle, energy_label=e_display)
figure_download_buttons(
    fig_geo,
    basename=f"geometry_{name.replace(' ', '_')}",
    tier=_tier,
    caption=auto_caption("geometry", layer_names=[name], particle=particle, energy_label=e_display),
    key_prefix="geo",
)
plt_mod = __import__('matplotlib.pyplot', fromlist=['close'])
plt_mod.close(fig_geo)

if p_type == "neutral" and particle == "neutron":
    st.subheader(str(copy["neutron_subheader"]))
    sigma_R = compute_fnrcs(mf, rho)
    hvl_n, tvl_n = compute_fnrcs_hvl(sigma_R)
    mfp_n = 1.0 / sigma_R if sigma_R > 0 else float('inf')

    render_metric_strip([
        ("Σ_R", f"{sigma_R:.4f} cm⁻¹"),
        ("HVLₙ", f"{hvl_n:.3f} cm"),
        ("TVLₙ", f"{tvl_n:.3f} cm"),
        ("MFPₙ", f"{mfp_n:.3f} cm"),
    ], columns=4)

    T_n = np.exp(-sigma_R * T_arr)
    df_n = pd.DataFrame({
        'Thickness (cm)': T_arr,
        'Sigma_R*x (MFP)': sigma_R * T_arr,
        'Transmission': T_n,
        'RPE (%)': (1 - T_n) * 100,
    })
    st.dataframe(df_n.round(6), use_container_width=True, hide_index=True)

    # Plot
    fig_n, ax_n = __import__('matplotlib.pyplot', fromlist=['subplots']).subplots(figsize=(8, 4))
    ax_n.semilogy(T_arr, T_n, 'b-', lw=2)
    ax_n.set_xlabel('Thickness (cm)'); ax_n.set_ylabel('Transmission')
    ax_n.set_title(f'Fast Neutron Transmission - {name}')
    ax_n.grid(alpha=0.3)
    figure_download_buttons(
        fig_n,
        basename=f"neutron_transmission_{name.replace(' ', '_')}",
        tier=_tier,
        caption=auto_caption("fnrcs", material=name, density=rho),
        key_prefix="fnrcs",
    )
    plt_mod.close(fig_n)

    # FNRCS per-element table
    from shieldlab.physics.shielding_params import FNRCS_BARNS
    from shieldlab.physics.nist_xcom import ATOMIC_MASS
    NA = 6.02214076e23
    rows_fn = []
    for sym, wf in sorted(mf.items(), key=lambda x: -x[1]):
        sb = FNRCS_BARNS.get(sym, None)
        A  = ATOMIC_MASS.get(sym, None)
        if sb and A:
            contrib = wf * (NA / A) * sb * 1e-24 * rho
            rows_fn.append({
                'Element': sym, 'wt fraction': f"{wf:.4f}",
                'sigma_f,R (barn)': f"{sb:.3f}",
                'A (g/mol)': f"{A:.3f}",
                'Σ_R contribution (cm⁻¹)': f"{contrib:.5f}",
            })
    st.subheader(str(copy["neutron_element_subheader"]))
    st.dataframe(pd.DataFrame(rows_fn), use_container_width=True, hide_index=True)

else:
    with st.spinner(str(copy["calc_spinner"])):
        try:
            df_shield = compute_shielding_table(mf, rho, E_arr, T_arr, gp_material=gp_mat)
            calc_ok = True
        except Exception as exc:
            render_error_reporter(exc, context=f"calc: {mat_name} @ {energy_display}")
            calc_ok = False

    if not calc_ok:
        st.stop()

    # MAC columns for quick access
    _mac_col = _pick_col(df_shield, MAC_COL_CANDIDATES)
    _mac_en_col = _pick_col(df_shield, MAC_EN_COL_CANDIDATES)
    _lac_col = _pick_col(df_shield, LAC_COL_CANDIDATES)
    mac_arr    = df_shield[_mac_col].to_numpy()
    mac_en_arr = df_shield[_mac_en_col].to_numpy()
    hvl_arr    = df_shield['HVL (cm)'].to_numpy()
    tvl_arr    = df_shield['TVL (cm)'].to_numpy()
    lac_arr    = df_shield[_lac_col].to_numpy()

    (tab_params, tab_xcom, tab_desc,
     tab_trans, tab_plots, tab_multi,
     tab_estar, tab_ion,
     tab_kn, tab_inv, tab_export) = st.tabs([
        str(copy["tab_phyx"]),
        str(copy["tab_xcom"]),
        str(copy["tab_descriptors"]),
        str(copy["tab_transmission"]),
        str(copy["tab_plots"]),
        str(copy["tab_multilayer"]),
        str(copy["tab_estar"]),
        str(copy["tab_ion"]),
        str(copy["tab_klein_nishina"]),
        str(copy["tab_inverse"]),
        str(copy["tab_export"]),
    ])

    render_panel_header(
        "Analytical Output Panels",
        "Navigate parameter tables, transport curves, multilayer analysis, and export-grade visualizations.",
        legend_items=[("Photon", "#10b981"), ("Neutron", "#f59e0b"), ("Descriptors", "#3b82f6")],
        controls=["Tables", "Plots", "Exports"],
    )

    with tab_params:
        render_panel_header(str(copy["phyx_subheader"]), str(copy["phyx_caption"]), controls=["Phy-X", "Table", "Zeff(E)"])
        st.caption(str(copy["phyx_caption"]))

        # Core attenuation table
        core_cols = ['Energy_keV', _mac_col, _mac_en_col, _lac_col,
                     'HVL (cm)', 'TVL (cm)', 'MFP (cm)']
        st.dataframe(
            df_shield[core_cols].round(6),
            use_container_width=True, hide_index=True,
        )

        # Extended Phy-X parameters (energy-dependent)
        _acs_col = next((c for c in ACS_COL_CANDIDATES if c in df_shield.columns), None)
        _ecs_col = next((c for c in ECS_COL_CANDIDATES if c in df_shield.columns), None)
        ext_base_cols = ['Energy_keV', 'Zeff', 'Neff (el/g)', 'Ceff (S/m)', 'R']
        if _acs_col:
            ext_base_cols.append(_acs_col)
        if _ecs_col:
            ext_base_cols.append(_ecs_col)
        ext_cols = [c for c in ext_base_cols if c in df_shield.columns]
        if len(ext_cols) > 1:
            with st.expander(str(copy["phyx_extended_expander"]), expanded=True):
                st.caption(str(copy["phyx_extended_caption"]))
                fmt_ext = {c: '{:.4e}' for c in ext_cols if any(x in c for x in ('ACS', 'ECS', 'Neff'))}
                fmt_ext.update({c: '{:.4f}' for c in ext_cols if c not in fmt_ext})
                st.dataframe(
                    df_shield[ext_cols].style.format(fmt_ext),
                    use_container_width=True, hide_index=True,
                )
                if len(E_arr) > 1 and 'Zeff' in df_shield.columns:
                    import matplotlib.pyplot as _plt
                    _fig_z, _ax_z = _plt.subplots(figsize=(9, 3.2))
                    _ax_z.semilogx(df_shield['Energy_keV'], df_shield['Zeff'], 'r-o',
                                   lw=1.5, ms=3, label='Zeff(E)')
                    _ax_z.set_xlabel('Energy (keV)'); _ax_z.set_ylabel('Zeff (MAC-weighted)')
                    _ax_z.set_title(f'Effective Atomic Number vs Energy - {name}')
                    _ax_z.grid(alpha=0.3)
                    finish_shieldlab_figure(_fig_z)
                    figure_download_buttons(
                        _fig_z,
                        basename=f"zeff_{name.replace(' ', '_')}",
                        tier=_tier,
                        caption=f"Effective atomic number Z\u1d07ff(E) of {name} (\u03c1\u2009=\u2009{rho:.3f}\u2009g\u2009cm\u207b\u00b3) vs photon energy computed with ShieldLab G4.",
                        key_prefix="zeff",
                    )
                    _plt.close(_fig_z)

        # Per-thickness transmission sub-table
        if T_arr.size > 0:
            st.markdown("**Transmission & Buildup at each thickness:**")
            t_cols = [c for c in df_shield.columns
                      if c.startswith('T @') or c.startswith('RPE%') or c.startswith('EBF')]
            if t_cols:
                st.dataframe(
                    df_shield[['Energy_keV'] + t_cols].round(6),
                    use_container_width=True, hide_index=True,
                )

        # Summary metrics at first energy
        if len(E_arr) == 1:
            e0 = float(E_arr[0] * 1000)
            m0 = float(mac_arr[0])
            h0 = float(hvl_arr[0])
            tv0= float(tvl_arr[0])
            la0= float(lac_arr[0])
            mfp0 = float(1 / la0) if la0 > 0 else float('inf')
            render_metric_strip([
                (f"μ/ρ @ {e0:.0f} keV", f"{m0:.4f} cm²/g"),
                ("μ (cm⁻¹)", f"{la0:.4f}"),
                ("HVL", f"{h0:.3f} cm"),
                ("TVL", f"{tv0:.3f} cm"),
                ("MFP", f"{mfp0:.3f} cm"),
            ], columns=5)

    with tab_xcom:
        render_panel_header(str(copy["xcom_subheader"]), str(copy["xcom_caption"]), controls=["XCOM", "Components", "Zeq"])
        st.caption(str(copy["xcom_caption"]))

        fetch_xcom = st.button(str(copy["xcom_fetch_button"]), type="secondary")
        if fetch_xcom or st.session_state.get('xcom_data_ready'):
            with st.spinner(str(copy["xcom_fetch_spinner"])):
                try:
                    from shieldlab.physics.nist_xcom import get_xcom_compound
                    xcom_data = get_xcom_compound(mf, E_arr)
                    st.session_state['xcom_data_ready'] = True
                    st.session_state['xcom_cache'] = xcom_data
                except Exception as exc:
                    st.error(f"XCOM fetch failed: {exc}")
                    xcom_data = None

        xcom_data = st.session_state.get('xcom_cache')
        if xcom_data:
            cols_show = ['coherent_cm2g', 'incoherent_cm2g', 'photoelectric_cm2g',
                         'pair_nuclear_cm2g', 'pair_electron_cm2g',
                         'total_with_coherent_cm2g', 'total_without_coherent_cm2g']
            rename = {
                'coherent_cm2g': 'Coherent (cm²/g)',
                'incoherent_cm2g': 'Compton (cm²/g)',
                'photoelectric_cm2g': 'Photo-electric (cm²/g)',
                'pair_nuclear_cm2g': 'Pair-nuclear (cm²/g)',
                'pair_electron_cm2g': 'Pair-electron (cm²/g)',
                'total_with_coherent_cm2g': 'Total+Coh (cm²/g)',
                'total_without_coherent_cm2g': 'Total-Coh (cm²/g)',
            }
            df_xc = pd.DataFrame({'Energy_keV': E_arr * 1000})
            for c in cols_show:
                if c in xcom_data:
                    df_xc[rename[c]] = xcom_data[c]
            st.dataframe(df_xc.round(6), use_container_width=True, hide_index=True)

            # XCOM plot
            fig_xcom = plot_mac_vs_energy(
                E_arr, mac_arr, mac_en_arr,
                material_name=name,
                xcom_components=xcom_data,
            )
            figure_download_buttons(
                fig_xcom,
                basename=f"xcom_{name.replace(' ', '_')}",
                tier=_tier,
                caption=auto_caption("xcom", material=name, density=rho),
                key_prefix="xcom",
            )
            plt_mod.close(fig_xcom)

            st.markdown("---")
            st.markdown("**Equivalent Atomic Number (Zeq) and R ratio**")
            st.caption(str(copy["xcom_zeq_caption"]))
            if st.button(str(copy["xcom_zeq_button"]), key="zeq_btn"):
                with st.spinner(str(copy["xcom_zeq_spinner"])):
                    try:
                        _c = xcom_data.get('incoherent_cm2g',             np.zeros(len(E_arr)))
                        _t = xcom_data.get('total_without_coherent_cm2g', np.ones(len(E_arr)))
                        _R, _Zeq = compute_zeq(mf, E_arr, xcom_compton=_c, xcom_total_nc=_t)
                        st.session_state['zeq_data'] = {'R': _R, 'Zeq': _Zeq}
                    except Exception as _exc:
                        st.error(f"Zeq error: {_exc}")
            _zeq = st.session_state.get('zeq_data')
            if _zeq is not None:
                df_zeq = pd.DataFrame({
                    'Energy_keV':        E_arr * 1000,
                    'R (Compton/Total)':  _zeq['R'],
                    'Zeq':                _zeq['Zeq'],
                })
                st.dataframe(df_zeq.round(5), use_container_width=True, hide_index=True)
                if len(E_arr) > 1:
                    import matplotlib.pyplot as _pltZ
                    _fz, _axz = _pltZ.subplots(1, 2, figsize=(12, 3.5))
                    _axz[0].semilogx(E_arr * 1000, _zeq['R'], 'b-', lw=2)
                    _axz[0].set_xlabel('Energy (keV)'); _axz[0].set_ylabel('R = Compton/Total')
                    _axz[0].set_title(f'Compton-to-Total Ratio - {name}'); _axz[0].grid(alpha=0.3)
                    _axz[1].semilogx(E_arr * 1000, _zeq['Zeq'], 'r-', lw=2)
                    _axz[1].set_xlabel('Energy (keV)'); _axz[1].set_ylabel('Zeq')
                    _axz[1].set_title(f'Equivalent Atomic Number - {name}'); _axz[1].grid(alpha=0.3)
                    finish_shieldlab_figure(_fz)
                    figure_download_buttons(
                        _fz,
                        basename=f"zeq_{name.replace(' ', '_')}",
                        tier=_tier,
                        caption=auto_caption("xcom", material=name, density=rho),
                        key_prefix="zeq",
                    )
                    _pltZ.close(_fz)
        else:
            # Simple MAC plot even without full XCOM
            fig_mac = plot_mac_vs_energy(E_arr, mac_arr, mac_en_arr, material_name=name)
            figure_download_buttons(
                fig_mac,
                basename=f"mac_{name.replace(' ', '_')}",
                tier=_tier,
                caption=auto_caption("mac", material=name, density=rho),
                key_prefix="mac_simple",
            )
            plt_mod.close(fig_mac)
            st.info("Click **Fetch Full XCOM Data** to get all 7 cross-section components from NIST.")

    with tab_desc:
        render_panel_header(str(copy["tab_desc_subheader"]), "Material descriptor extraction and neutron removal summaries.", controls=["Descriptors", "Composition", "FNRCS"])
        try:
            desc_all = material_descriptors(name, mf, rho)

            d_rows = [
                {"Parameter": "Density (g/cm³)",                  "Value": f"{desc_all['density_g_cm3']:.4f}"},
                {"Parameter": "M_eff (mean atomic molar mass, g/mol)", "Value": f"{desc_all['molar_mass_g_mol']:.4f}"},
                {"Parameter": "Mean atomic Z",                       "Value": f"{desc_all['average_Z']:.4f}"},
                {"Parameter": "Zeff (n=3.5, static power law)",    "Value": f"{desc_all['Zeff_3p5']:.4f}"},
                {"Parameter": "Zeff (n=2.94, Mayneord, static)",   "Value": f"{desc_all.get('Zeff_2p94', desc_all['Zeff_3p5']):.4f}"},
                {"Parameter": "Neff (el/g, static)",               "Value": f"{desc_all.get('Neff_per_gram', float('nan')):.4e}"},
                {"Parameter": "Neff (el/cm³, static)",             "Value": f"{desc_all['Neff_electrons_cm3']:.4e}"},
                {"Parameter": "Electron density (el/cm³)",         "Value": f"{desc_all['electron_density_cm3']:.4e}"},
            ]
            st.dataframe(pd.DataFrame(d_rows), use_container_width=True, hide_index=True)

            # Elemental composition table: Wi (mass) + Fi (mole) fractions
            st.markdown("**Elemental composition:**")
            _mf_dict = desc_all.get('mole_fractions', {})
            el_rows = []
            for el, wf in sorted(mf.items(), key=lambda x: -x[1]):
                fi = _mf_dict.get(el, float('nan'))
                el_rows.append({
                    "Element": el,
                    "Wi (weight fraction)": f"{wf:.6f}",
                    "Wi %": f"{wf*100:.3f}",
                    "Fi (mole fraction)": f"{fi:.6f}" if np.isfinite(fi) else "N/A",
                    "Fi %": f"{fi*100:.3f}" if np.isfinite(fi) else "N/A",
                })
            st.dataframe(pd.DataFrame(el_rows), use_container_width=True, hide_index=True)

            # FNRCS
            sigma_R = compute_fnrcs(mf, rho)
            hvl_n, tvl_n = compute_fnrcs_hvl(sigma_R)
            st.markdown("**Fast Neutron Removal (NGCal):**")
            render_metric_strip([
                ("Σ_R", f"{sigma_R:.5f} cm⁻¹"),
                ("HVLₙ", f"{hvl_n:.3f} cm"),
                ("TVLₙ", f"{tvl_n:.3f} cm"),
            ], columns=3)

        except Exception as exc:
            st.warning(f"Descriptor error: {exc}")

    with tab_trans:
        render_panel_header(str(copy["tab_trans_subheader"]), "Transmission curves and HVL/TVL behavior across energy and thickness.", controls=["Curves", "Table", "HVL/TVL"])

        # Energy selector
        e_keV_list = (E_arr * 1000).tolist()
        if len(e_keV_list) == 1:
            e_sel_keV = e_keV_list[0]
        else:
            e_sel_keV = st.selectbox(
                "Select energy for T(x) curve",
                e_keV_list,
                format_func=lambda e: f"{e:.2f} keV",
            )

        e_idx = int(np.argmin(np.abs(E_arr * 1000 - e_sel_keV)))
        mac_sel = float(mac_arr[e_idx])

        # Thickness range for plot
        x_arr = np.linspace(0, float(T_arr.max()) * 1.5 + 0.1, 200)
        df_tv = compute_transmission_vs_thickness(mac_sel, rho, x_arr,
                                                   float(E_arr[e_idx]), gp_mat)

        c_plot, c_table = st.columns([3, 2])
        with c_plot:
            fig_tv = plot_transmission_vs_thickness(
                x_arr,
                df_tv['T (narrow beam)'].to_numpy(),
                df_tv['T (with buildup)'].to_numpy(),
                material_name=name,
                energy_label=f"{e_sel_keV:.1f} keV",
            )
            figure_download_buttons(
                fig_tv,
                basename=f"transmission_{name.replace(' ', '_')}_{e_sel_keV:.0f}keV",
                tier=_tier,
                caption=auto_caption("transmission", material=name, density=rho, energy_keV=e_sel_keV),
                key_prefix="trans",
            )
            plt_mod.close(fig_tv)

        with c_table:
            _mx_col = next((c for c in MFP_X_COL_CANDIDATES if c in df_tv.columns), "μx (MFP)")
            st.dataframe(
                df_tv[['Thickness (cm)', _mx_col, 'T (narrow beam)',
                        'T (with buildup)', 'RPE% (narrow)', 'EBF']].round(5),
                use_container_width=True, hide_index=True, height=380,
            )

        # HVL/TVL vs energy plot
        if len(E_arr) > 1:
            st.markdown("---")
            st.markdown("**HVL and TVL vs Energy:**")
            fig_ht = plot_hvl_tvl_vs_energy(E_arr, hvl_arr, tvl_arr, material_name=name)
            figure_download_buttons(
                fig_ht,
                basename=f"hvl_tvl_{name.replace(' ', '_')}",
                tier=_tier,
                caption=auto_caption("hvl_tvl", material=name, density=rho),
                key_prefix="hvl_trans",
            )
            plt_mod.close(fig_ht)

    with tab_plots:
        render_panel_header(str(copy["tab_plots_subheader"]), "Publication-oriented plot selector with direct export hooks.", controls=["Select", "Render", "Export"])

        plot_choice = st.multiselect(
            "Select plots to display",
            ["MAC vs Energy", "HVL & TVL vs Energy", "LAC vs Energy",
             "MFP vs Energy", "Transmission vs Energy (at selected thickness)"],
            default=["MAC vs Energy", "HVL & TVL vs Energy"],
        )

        if "MAC vs Energy" in plot_choice and len(E_arr) > 1:
            fig_m = plot_mac_vs_energy(E_arr, mac_arr, mac_en_arr, material_name=name)
            figure_download_buttons(
                fig_m,
                basename=f"mac_{name.replace(' ', '_')}",
                tier=_tier,
                caption=auto_caption("mac", material=name, density=rho),
                key_prefix="mac_plots",
            )
            plt_mod.close(fig_m)

        if "HVL & TVL vs Energy" in plot_choice and len(E_arr) > 1:
            fig_ht2 = plot_hvl_tvl_vs_energy(E_arr, hvl_arr, tvl_arr, material_name=name)
            figure_download_buttons(
                fig_ht2,
                basename=f"hvl_tvl_{name.replace(' ', '_')}",
                tier=_tier,
                caption=auto_caption("hvl_tvl", material=name, density=rho),
                key_prefix="hvl_plots",
            )
            plt_mod.close(fig_ht2)

        if "LAC vs Energy" in plot_choice and len(E_arr) > 1:
            import matplotlib.pyplot as plt_
            fig_l, ax_l = plt_.subplots(figsize=(9, 4))
            ax_l.loglog(E_arr * 1000, lac_arr, 'g-', lw=2)
            ax_l.set_xlabel('Energy (keV)'); ax_l.set_ylabel('μ (cm⁻¹)')
            ax_l.set_title(f'Linear Attenuation Coefficient - {name}')
            ax_l.grid(alpha=0.3, which='both')
            figure_download_buttons(
                fig_l,
                basename=f"lac_{name.replace(' ', '_')}",
                tier=_tier,
                caption=f"Linear attenuation coefficient \u03bc(E) of {name} (\u03c1\u2009=\u2009{rho:.3f}\u2009g\u2009cm\u207b\u00b3) computed with ShieldLab G4.",
                key_prefix="lac",
            )
            plt_.close(fig_l)

        if "MFP vs Energy" in plot_choice and len(E_arr) > 1:
            import matplotlib.pyplot as plt_
            mfp_arr = 1.0 / np.where(lac_arr > 0, lac_arr, 1e-10)
            fig_mfp, ax_mfp = plt_.subplots(figsize=(9, 4))
            ax_mfp.loglog(E_arr * 1000, mfp_arr, 'm-', lw=2)
            ax_mfp.set_xlabel('Energy (keV)'); ax_mfp.set_ylabel('MFP (cm)')
            ax_mfp.set_title(f'Mean Free Path - {name}')
            ax_mfp.grid(alpha=0.3, which='both')
            figure_download_buttons(
                fig_mfp,
                basename=f"mfp_{name.replace(' ', '_')}",
                tier=_tier,
                caption=f"Mean free path MFP(E) = 1/\u03bc(E) of {name} (\u03c1\u2009=\u2009{rho:.3f}\u2009g\u2009cm\u207b\u00b3) computed with ShieldLab G4.",
                key_prefix="mfp",
            )
            plt_.close(fig_mfp)

        if "Transmission vs Energy (at selected thickness)" in plot_choice and len(E_arr) > 1:
            t_sel = st.select_slider("Thickness for T(E) plot (cm)",
                                      options=[round(x, 4) for x in T_arr.tolist()],
                                      value=float(T_arr[len(T_arr)//2]))
            T_e = np.exp(-lac_arr * t_sel)
            import matplotlib.pyplot as plt_
            fig_te, ax_te = plt_.subplots(figsize=(9, 4))
            ax_te.semilogx(E_arr * 1000, T_e * 100, 'b-', lw=2)
            ax_te.set_xlabel('Energy (keV)'); ax_te.set_ylabel('Transmission (%)')
            ax_te.set_title(f'Transmission vs Energy - {name} ({t_sel:.2f} cm)')
            ax_te.set_ylim(-2, 102); ax_te.grid(alpha=0.3)
            figure_download_buttons(
                fig_te,
                basename=f"trans_energy_{name.replace(' ', '_')}",
                tier=_tier,
                caption=auto_caption("transmission", material=name, density=rho),
                key_prefix="trans_energy",
            )
            plt_.close(fig_te)

    with tab_multi:
        st.subheader(str(copy["tab_multi_subheader"]))

        layers_ok = all(lyr.get("formula") for lyr in st.session_state.sc_layers)
        if not layers_ok:
            st.info("Fill in the formula column for each layer in Section 3 above.")
        else:
            # Energy for multilayer
            if len(E_arr) == 1:
                e_ml_keV = float(E_arr[0] * 1000)
            else:
                e_ml_keV = st.selectbox(
                    "Energy (keV) for multi-layer calculation",
                    (E_arr * 1000).tolist(),
                    format_func=lambda e: f"{e:.2f} keV",
                    key="ml_e_sel",
                )
            e_ml_MeV = e_ml_keV / 1000.0

            # Resolve mass fractions for each layer
            multilayer_defs = []
            for lyr in st.session_state.sc_layers:
                try:
                    lyr_mf = resolve_material_mass_fractions(
                        {"name": lyr["name"], "density_g_cm3": lyr["density_g_cm3"],
                         "formula": lyr["formula"]}
                    )
                    multilayer_defs.append({
                        'name': lyr['name'],
                        'mass_fractions': lyr_mf,
                        'density_g_cm3': lyr['density_g_cm3'],
                        'thickness_cm': lyr['thickness_cm'],
                    })
                except Exception as exc:
                    st.warning(f"Layer '{lyr['name']}': {exc}")

            if multilayer_defs:
                with st.spinner("Computing multi-layer attenuation..."):
                    try:
                        ml_result = compute_multilayer(multilayer_defs, e_ml_MeV)
                        T_ml = ml_result['T_total']
                        RPE_ml = ml_result['RPE_total']
                        render_metric_strip([
                            ("Total transmission", f"{T_ml:.6f}"),
                            ("RPE", f"{RPE_ml:.3f}%"),
                            ("Attenuation factor", f"{1/T_ml:.2e}x"),
                        ], columns=3)

                        # Per-layer table
                        df_ml = pd.DataFrame(ml_result['layers'])
                        st.dataframe(df_ml.round(5), use_container_width=True, hide_index=True)

                        # Multilayer geometry figure
                        geo_multi_layers = [
                            {"name": lyr['name'], "thickness_cm": lyr['thickness_cm'],
                             "density_g_cm3": lyr['density_g_cm3']}
                            for lyr in multilayer_defs
                        ]
                        fig_ml_geo = plot_shielding_geometry(
                            geo_multi_layers, particle=particle,
                            energy_label=f"{e_ml_keV:.0f} keV",
                        )
                        layer_names_ml = [lyr['name'] for lyr in multilayer_defs]
                        figure_download_buttons(
                            fig_ml_geo,
                            basename=f"multilayer_geometry_{name.replace(' ', '_')}",
                            tier=_tier,
                            caption=auto_caption("multilayer", layer_names=layer_names_ml, particle=particle, energy_label=f"{e_ml_keV:.0f} keV"),
                            key_prefix="ml_geo",
                        )
                        plt_mod.close(fig_ml_geo)
                    except Exception as exc:
                        st.error(f"Multi-layer error: {exc}")

    with tab_estar:
        st.subheader(str(copy["tab_estar_subheader"]))
        st.caption(
            "Bethe-Bloch formula (ICRU 37) with Sternheimer density effect. "
            "Collision + radiative stopping, CSDA range. "
            "Results typically within 2 % of NIST ESTAR for low-Z materials."
        )
        from shieldlab.physics.nist_estar import electron_table as _electron_table

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            e_emin = st.number_input("E min (MeV)", value=0.01, min_value=1e-4,
                                     max_value=50.0, format="%.4f", key="estar_emin")
            e_emax = st.number_input("E max (MeV)", value=15.0, min_value=0.01,
                                     max_value=1000.0, format="%.2f", key="estar_emax")
        with col_e2:
            e_npts = st.number_input("Energy points", value=30, min_value=5,
                                     max_value=200, step=5, key="estar_npts")

        if st.button("Compute ESTAR", type="primary", key="btn_estar"):
            with st.spinner("Computing electron stopping powers..."):
                try:
                    e_energies = np.logspace(
                        np.log10(float(e_emin)), np.log10(float(e_emax)), int(e_npts)
                    )
                    df_estar = _electron_table(mf, rho, e_energies)
                    st.session_state["df_estar"] = df_estar
                except Exception as exc:
                    st.error(f"ESTAR error: {exc}")
                    st.session_state.pop("df_estar", None)

        if "df_estar" in st.session_state:
            df_estar = st.session_state["df_estar"]
            st.dataframe(df_estar.style.format("{:.4g}"), use_container_width=True)

            import matplotlib.pyplot as plt_estar_mod
            fig_es, (ax_sp, ax_rng) = plt_estar_mod.subplots(1, 2, figsize=(12, 4))
            e_col = "Energy (MeV)"
            _s_coll_col = next((c for c in ("S_coll (MeV·cm²/g)", "S_coll (MeV cm^2/g)", "S_coll (MeV�cm�/g)") if c in df_estar.columns), None)
            _s_rad_col = next((c for c in ("S_rad (MeV·cm²/g)", "S_rad (MeV cm^2/g)", "S_rad (MeV�cm�/g)") if c in df_estar.columns), None)
            _s_total_col = next((c for c in ("S_total (MeV·cm²/g)", "S_total (MeV cm^2/g)", "S_total (MeV�cm�/g)") if c in df_estar.columns), None)
            _csda_g_col = next((c for c in ("CSDA range (g/cm²)", "CSDA Range (g/cm^2)", "CSDA Range (g/cm�)") if c in df_estar.columns), None)

            ax_sp.loglog(df_estar[e_col], df_estar[_s_coll_col],
                         label="S_coll", lw=2)
            ax_sp.loglog(df_estar[e_col], df_estar[_s_rad_col],
                         label="S_rad", lw=2, ls="--")
            ax_sp.loglog(df_estar[e_col], df_estar[_s_total_col],
                         label="S_total", lw=2, ls=":")
            ax_sp.set_xlabel("Energy (MeV)")
            ax_sp.set_ylabel("Stopping Power (MeV·cm²/g)")
            ax_sp.set_title("Electron Stopping Power")
            ax_sp.legend(fontsize=9)
            ax_sp.grid(True, which="both", alpha=0.3)

            ax_rng.loglog(df_estar[e_col], df_estar[_csda_g_col],
                          color="green", lw=2, label="CSDA Range")
            ax_rng.set_xlabel("Energy (MeV)")
            ax_rng.set_ylabel("CSDA Range (g/cm²)")
            ax_rng.set_title("CSDA Range")
            ax_rng.legend(fontsize=9)
            ax_rng.grid(True, which="both", alpha=0.3)

            finish_shieldlab_figure(fig_es)
            figure_download_buttons(
                fig_es,
                basename=f"estar_{name.replace(' ', '_')}",
                tier=_tier,
                caption=auto_caption("estar", material=name, density=rho),
                key_prefix="estar",
            )
            plt_estar_mod.close(fig_es)

    with tab_ion:
        st.subheader(str(copy["tab_ion_subheader"]))
        st.caption(
            "Bethe-Bloch (ICRU 49) + ZBL nuclear stopping + Ziegler effective charge. "
            "Proton and alpha in compounds via Bragg-Kleeman compound mean excitation energy."
        )
        from shieldlab.physics.ion_range import (
            proton_table as _proton_table,
            alpha_table  as _alpha_table,
        )

        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1:
            ion_type = st.selectbox("Ion type", ["Proton", "Alpha"],
                                    key="ion_type")
        with col_i2:
            ion_emin = st.number_input("E min (MeV)", value=0.1, min_value=1e-3,
                                       max_value=100.0, format="%.3f", key="ion_emin")
            ion_emax = st.number_input("E max (MeV)", value=30.0, min_value=0.01,
                                       max_value=1000.0, format="%.1f", key="ion_emax")
        with col_i3:
            ion_npts = st.number_input("Energy points", value=30, min_value=5,
                                       max_value=200, step=5, key="ion_npts")

        if st.button("Compute Ion Range", type="primary", key="btn_ion"):
            with st.spinner("Computing ion stopping powers..."):
                try:
                    ion_energies = np.logspace(
                        np.log10(float(ion_emin)), np.log10(float(ion_emax)), int(ion_npts)
                    )
                    if ion_type == "Proton":
                        df_ion = _proton_table(mf, rho, ion_energies)
                    else:
                        df_ion = _alpha_table(mf, rho, ion_energies)
                    st.session_state["df_ion"] = df_ion
                    st.session_state["df_ion_type"] = ion_type
                except Exception as exc:
                    st.error(f"Ion range error: {exc}")
                    st.session_state.pop("df_ion", None)

        if "df_ion" in st.session_state:
            df_ion = st.session_state["df_ion"]
            ion_label = st.session_state.get("df_ion_type", "Ion")

            # Accuracy disclaimer for low-energy rows
            if (df_ion['Energy (MeV)'] < 0.1).any():
                st.warning(
                    "⚠️ **Accuracy note:** One or more energies are below 100 keV. "
                    "The analytical Bethe-ZBL model has accuracy of ±10–20% in this regime. "
                    "For high-accuracy sub-100 keV results, use SRIM or PSTAR directly.",
                    icon="⚠️",
                )

            st.dataframe(df_ion.style.format("{:.4g}"), use_container_width=True)

            import matplotlib.pyplot as plt_ion_mod
            fig_ion, (ax_isp, ax_irng) = plt_ion_mod.subplots(1, 2, figsize=(12, 4))
            e_col_i = "Energy (MeV)"
            sp_col  = next((c for c in ("S_total (MeV·cm²/g)", "S_total (MeV cm^2/g)", "S_total (MeV�cm�/g)") if c in df_ion.columns), None)
            rng_col = next((c for c in ("CSDA range (g/cm²)", "CSDA Range (g/cm^2)", "CSDA Range (g/cm�)") if c in df_ion.columns), None)

            ax_isp.loglog(df_ion[e_col_i], df_ion[sp_col],
                          color="crimson", lw=2, label=f"{ion_label} S_total")
            ax_isp.set_xlabel("Energy (MeV)")
            ax_isp.set_ylabel("Stopping Power (MeV·cm²/g)")
            ax_isp.set_title(f"{ion_label} Stopping Power")
            ax_isp.legend(fontsize=9)
            ax_isp.grid(True, which="both", alpha=0.3)

            ax_irng.loglog(df_ion[e_col_i], df_ion[rng_col],
                           color="navy", lw=2, label=f"{ion_label} CSDA Range")
            ax_irng.set_xlabel("Energy (MeV)")
            ax_irng.set_ylabel("CSDA Range (g/cm²)")
            ax_irng.set_title(f"{ion_label} CSDA Range")
            ax_irng.legend(fontsize=9)
            ax_irng.grid(True, which="both", alpha=0.3)

            finish_shieldlab_figure(fig_ion)
            figure_download_buttons(
                fig_ion,
                basename=f"ion_{ion_label.lower()}_{name.replace(' ', '_')}",
                tier=_tier,
                caption=auto_caption("ion_range", material=name, density=rho, ion=ion_label),
                key_prefix="ion",
            )
            plt_ion_mod.close(fig_ion)

    with tab_kn:
        st.subheader(str(copy["tab_kn_subheader"]))
        st.caption(
            "Differential cross-section dσ/dΩ (Klein-Nishina, 1929). "
            "Reference: Evans *The Atomic Nucleus* (1955) Ch. 23."
        )
        try:
            from shieldlab.physics.klein_nishina import (
                klein_nishina_polar_fig, compton_energy_fig,
                total_compton_cross_section,
            )
            import matplotlib.pyplot as _kn_plt

            _kn_col1, _kn_col2 = st.columns([1, 2])
            with _kn_col1:
                _kn_energies_str = st.text_input(
                    "Photon energies (MeV, comma-separated)",
                    value="0.1, 0.3, 0.662, 1.25, 2.0",
                    key="kn_energies",
                    help="Up to 6 energies. Each plotted as a separate curve.",
                )
                _kn_energies = [float(e.strip()) for e in _kn_energies_str.split(",") if e.strip()][:6]

                st.markdown("**Total cross-section (cm²/electron):**")
                for _ke in _kn_energies:
                    _sig = total_compton_cross_section(_ke)
                    st.markdown(f"- {_ke} MeV -> {_sig:.4e} cm²/el")

            with _kn_col2:
                _tab_polar, _tab_energy = st.tabs(["Polar dσ/dΩ", "Compton E'(θ)"])
                with _tab_polar:
                    _fig_polar = klein_nishina_polar_fig(_kn_energies)
                    figure_download_buttons(
                        _fig_polar,
                        basename=f"klein_nishina_polar_{name.replace(' ','_')}",
                        tier=_tier,
                        caption=(
                            f"Klein-Nishina polar differential cross-section dσ/dΩ "
                            f"for photon energies {', '.join(str(e) for e in _kn_energies)} MeV. "
                            f"Computed via ShieldLab G4."
                        ),
                        key_prefix="kn_polar",
                    )
                    _kn_plt.close(_fig_polar)
                with _tab_energy:
                    _fig_energy = compton_energy_fig(_kn_energies)
                    figure_download_buttons(
                        _fig_energy,
                        basename=f"compton_energy_{name.replace(' ','_')}",
                        tier=_tier,
                        caption=(
                            f"Scattered photon energy E'(θ) and electron kinetic energy T(θ) "
                            f"for energies {', '.join(str(e) for e in _kn_energies)} MeV."
                        ),
                        key_prefix="kn_energy",
                    )
                    _kn_plt.close(_fig_energy)
        except Exception as _kn_exc:
            render_error_reporter(_kn_exc, context="Klein-Nishina tab")

    with tab_inv:
        st.subheader("Inverse Shielding Design")
        st.caption(
            "Given a target transmission T (%), find the required thickness or "
            "density. Uses MAC values fetched for the current material."
        )
        try:
            from shieldlab.physics.inverse_design import (
                required_thickness_table, hvl, tvl, sensitivity_analysis,
            )
            import matplotlib.pyplot as _inv_plt

            _inv_col1, _inv_col2 = st.columns([1, 2])
            with _inv_col1:
                _inv_energy = st.selectbox(
                    "Energy (MeV)",
                    E_arr.tolist(),
                    format_func=lambda e: f"{e*1000:.1f} keV  ({e:.4f} MeV)",
                    key="inv_energy",
                )
                _inv_idx  = np.searchsorted(E_arr, _inv_energy)
                _inv_mac  = float(mac_arr[_inv_idx])
                _inv_rho  = rho
                _inv_hvl  = hvl(_inv_mac, _inv_rho)
                _inv_tvl  = tvl(_inv_mac, _inv_rho)
                st.metric("HVL (cm)", f"{_inv_hvl:.4f}")
                st.metric("TVL (cm)", f"{_inv_tvl:.4f}")
                st.metric("MAC (cm²/g)", f"{_inv_mac:.5f}")

            with _inv_col2:
                _inv_tab_table, _inv_tab_sens = st.tabs(
                    ["Design Table", "Sensitivity (? variation)"]
                )
                with _inv_tab_table:
                    _inv_E_sel = E_arr
                    _inv_mac_sel = mac_arr
                    _df_inv = required_thickness_table(_inv_E_sel, _inv_mac_sel, _inv_rho)
                    st.dataframe(_df_inv.style.format(precision=4),
                                 use_container_width=True, hide_index=True)
                    _inv_csv = _df_inv.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        data=_inv_csv,
                        file_name=f"inverse_design_{name.replace(' ','_')}.csv",
                        mime="text/csv",
                        key="inv_dl_csv",
                    )
                with _inv_tab_sens:
                    _rho_range = np.linspace(max(0.1, _inv_rho * 0.5), _inv_rho * 1.5, 40)
                    _df_sens = sensitivity_analysis(_inv_mac, _inv_rho, T_target=0.1,
                                                    rho_range=_rho_range)
                    import matplotlib.pyplot as _splt
                    _fig_sens, _ax_s = _splt.subplots(figsize=(6, 4))
                    _ax_s.plot(_df_sens["density_g_cm3"], _df_sens["thickness_cm"],
                               color="#0a47a0", lw=1.5)
                    _ax_s.axvline(_inv_rho, color="red", ls="--", lw=1, label=f"ρ = {_inv_rho} g/cm³")
                    _ax_s.set_xlabel("Density (g/cm³)")
                    _ax_s.set_ylabel("Required thickness (cm) for T = 10 %")
                    _ax_s.set_title(f"Sensitivity - {name}")
                    _ax_s.legend(fontsize=8)
                    finish_shieldlab_figure(_fig_sens)
                    figure_download_buttons(
                        _fig_sens,
                        basename=f"sensitivity_{name.replace(' ','_')}",
                        tier=_tier,
                        caption=(
                            f"Required shield thickness vs density for 10% transmission "
                            f"of {name}. MAC = {_inv_mac:.4f} cm²/g."
                        ),
                        key_prefix="inv_sens",
                    )
                    _splt.close(_fig_sens)
        except Exception as _inv_exc:
            render_error_reporter(_inv_exc, context="Inverse Design tab")

    with tab_export:
        st.subheader("Export Results")
        st.markdown("Download all computed results as Excel (.xlsx) or a journal-quality PDF report.")

        col_xl, col_pdf = st.columns(2)

        with col_xl:
            if st.button("Generate Excel Report", type="primary", use_container_width=True):
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as xw:
                    # Sheet 1: Shielding parameters
                    df_shield.to_excel(xw, sheet_name='Shielding_Parameters', index=False)

                    # Sheet 2: Transmission vs thickness at first energy
                    if len(E_arr) > 0:
                        x_exp = np.linspace(0, float(T_arr.max() if T_arr.size else 20.0) + 2, 100)
                        df_tv_exp = compute_transmission_vs_thickness(
                            float(mac_arr[0]), rho, x_exp, float(E_arr[0]), gp_mat)
                        df_tv_exp.to_excel(xw, sheet_name='Transmission_vs_Thickness', index=False)

                    # Sheet 3: Elemental composition (Wi + Fi)
                    desc_tmp = material_descriptors(name, mf, rho)
                    _mf_tmp = desc_tmp.get('mole_fractions', {})
                    el_exp = pd.DataFrame([
                        {
                            "Element": el,
                            "Weight_fraction_Wi": wf,
                            "Weight_percent_Wi": wf * 100,
                            "Mole_fraction_Fi": _mf_tmp.get(el, float('nan')),
                            "Mole_percent_Fi": _mf_tmp.get(el, float('nan')) * 100,
                        }
                        for el, wf in sorted(mf.items(), key=lambda x: -x[1])
                    ])
                    el_exp.to_excel(xw, sheet_name='Composition', index=False)

                    # Sheet 4: Descriptors
                    desc_all2 = material_descriptors(name, mf, rho)
                    sigma_R2 = compute_fnrcs(mf, rho)
                    hvl_n2, tvl_n2 = compute_fnrcs_hvl(sigma_R2)
                    descriptor_payload = {
                        **desc_all2,
                        "FNRCS_Sigma_R_cm": sigma_R2,
                        "FNRCS_HVL_cm": hvl_n2,
                        "FNRCS_TVL_cm": tvl_n2,
                    }
                    desc_rows = descriptor_mapping_to_rows(descriptor_payload)
                    desc_exp = pd.DataFrame([
                        {"Parameter": row.parameter, "Value": row.value}
                        for row in desc_rows
                    ])
                    desc_exp.to_excel(xw, sheet_name='Descriptors', index=False)

                    # Sheet 5: ESTAR (electron stopping) if computed
                    if "df_estar" in st.session_state:
                        st.session_state["df_estar"].to_excel(
                            xw, sheet_name='ESTAR_Electrons', index=False)

                    # Sheet 6: Ion Range if computed
                    if "df_ion" in st.session_state:
                        ion_sheet = f"Ion_{st.session_state.get('df_ion_type','Ion')}"
                        st.session_state["df_ion"].to_excel(
                            xw, sheet_name=ion_sheet, index=False)

                buf.seek(0)
                st.download_button(
                    "Download Excel Report",
                    data=buf,
                    file_name=f"shielding_{name.replace(' ','_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True,
                )

        # CSV download (always free)
        csv_buf = io.StringIO()
        df_shield.to_csv(csv_buf, index=False)
        st.download_button(
            "Download CSV",
            data=csv_buf.getvalue(),
            file_name=f"shielding_{name.replace(' ','_')}.csv",
            mime="text/csv",
        )

        with col_pdf:
            st.markdown("**PDF Report** (journal-quality, includes tables + figures)")
            _pdf_disabled = (_tier == "free")
            if _pdf_disabled:
                st.info("PDF report is a Pro feature. Upgrade to download.")
            if st.button("Generate PDF Report", type="secondary",
                          disabled=_pdf_disabled, use_container_width=True):
                with st.spinner("Generating PDF..."):
                    try:
                        from shieldlab.report.pdf_report import pdf_bytes as _pdf_bytes
                        from shieldlab import __version__ as _ver
                        import matplotlib
                        matplotlib.use("Agg")
                        import matplotlib.pyplot as _pdf_plt
                        _figs: dict = {}
                        # Regenerate key figures for PDF embedding
                        if len(E_arr) > 1:
                            _figs["MAC vs Energy"] = plot_mac_vs_energy(
                                E_arr, mac_arr, mac_en_arr, material_name=name)
                            _figs["HVL & TVL vs Energy"] = plot_hvl_tvl_vs_energy(
                                E_arr, hvl_arr, tvl_arr, material_name=name)
                            _figs["LAC vs Energy"] = _pdf_plt.subplots(figsize=(9, 4))[0]
                            _ax_pdf_lac = _figs["LAC vs Energy"].axes[0]
                            _ax_pdf_lac.loglog(E_arr * 1000, lac_arr, 'g-', lw=2)
                            _ax_pdf_lac.set_xlabel('Energy (keV)')
                            _ax_pdf_lac.set_ylabel('LAC μ (cm⁻¹)')
                            _ax_pdf_lac.set_title(f'Linear Attenuation - {name}')
                            _ax_pdf_lac.grid(alpha=0.3, which='both')
                        if len(E_arr) == 1:
                            _x_pdf = np.linspace(0, float(T_arr.max() if T_arr.size else 20) + 5, 200)
                            _df_tv_pdf = compute_transmission_vs_thickness(
                                float(mac_arr[0]), rho, _x_pdf, float(E_arr[0]), gp_mat)
                            _figs["Transmission"] = plot_transmission_vs_thickness(
                                _x_pdf,
                                _df_tv_pdf["T (narrow beam)"].to_numpy(),
                                _df_tv_pdf["T (with buildup)"].to_numpy(),
                                material_name=name,
                                energy_label=f"{float(E_arr[0]*1000):.1f} keV",
                            )
                        _pdf = _pdf_bytes(cs, _figs, version=_ver)
                        # Close regenerated figures to free memory
                        for _f in _figs.values():
                            _pdf_plt.close(_f)
                        st.download_button(
                            "Download PDF Report",
                            data=_pdf,
                            file_name=f"ShieldLabG4_Report_{name.replace(' ','_')}.pdf",
                            mime="application/pdf", use_container_width=True,
                        )
                    except Exception as _exc:
                        st.error(f"PDF generation failed: {_exc}")

        st.markdown("---")
        st.subheader("Session Save / Restore")
        st.markdown(
            "Save your complete calculation state to a `.shieldlab` file and reload it later "
            "on any ShieldLab G4 instance."
        )
        col_save, col_load = st.columns(2)
        with col_save:
            try:
                from shieldlab.io.session import session_download_button
                from shieldlab import __version__ as _ver2
                session_download_button(cs, version=_ver2, key="session_dl_calc")
            except Exception as _se:
                st.warning(f"Session save unavailable: {_se}")
        with col_load:
            try:
                from shieldlab.io.session import session_upload_widget
                _loaded = session_upload_widget(key="session_upload_calc")
                if _loaded is not None:
                    st.session_state["_loaded_session"] = _loaded
                    st.info("Session loaded. Refresh or recalculate to apply.")
            except Exception as _le:
                st.warning(f"Session restore unavailable: {_le}")

        st.markdown("---")
        st.subheader("How to cite ShieldLab G4")
        try:
            from shieldlab import __version__ as _cite_ver
        except Exception:
            _cite_ver = "dev"
        _cite_url = "https://github.com/shieldlab-g4/shieldlab"
        _bibtex = (
            "@software{shieldlabg4,\n"
            f"  title   = {{ShieldLab G4 \u2014 Analytical Radiation Shielding Toolkit}},\n"
            f"  version = {{{_cite_ver}}},\n"
            f"  url     = {{{_cite_url}}},\n"
            "  year    = {2026},\n"
            "}"
        )
        _apa = (
            f"ShieldLab G4 Team. (2026). *ShieldLab G4* (Version {_cite_ver}). "
            f"{_cite_url}"
        )
        _ieee = (
            f"ShieldLab G4 Team, \"ShieldLab G4,\" Version {_cite_ver}, 2026. "
            f"[Online]. Available: {_cite_url}"
        )
        _ctab_bib, _ctab_apa, _ctab_ieee = st.tabs(["BibTeX", "APA", "IEEE"])
        with _ctab_bib:
            st.code(_bibtex, language="bibtex")
        with _ctab_apa:
            st.markdown(_apa)
        with _ctab_ieee:
            st.code(_ieee)



