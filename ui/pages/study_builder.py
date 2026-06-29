"""Study Builder page - JSON editor, guided form, and Material Composer."""
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

from components.platform_settings import get_platform_settings
from components.layout import render_page_hero
from components.enterprise_ui import (
    render_breadcrumb,
    render_kpi_strip,
    render_panel_header,
    render_status_bar,
)
from shieldlab.core.descriptors import descriptors_from_study, material_descriptors
from shieldlab.core.materials import resolve_material_mass_fractions
from shieldlab.io.study_validator import has_errors, issues_to_frame, validate_study
from shieldlab.content import PAGE_COPY

copy = PAGE_COPY["study_builder"]
_settings = get_platform_settings()


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
                "Input": f"ρ·φ = {proxy:.4f}",
                "Normalised share": f"{proxy / total:.4f}",
                "Basis": "mass proxy from volume fraction",
            })
    return rows

render_page_hero(str(copy["title"]), str(copy["caption"]), "Simulation Configuration")

render_breadcrumb(["ShieldLab G4", "Simulation"], current="Study Builder")

_studies_count = len(list(config.STUDIES_DIR.glob("*.json"))) if config.STUDIES_DIR.exists() else 0
render_kpi_strip(
    [
        {"label": "Existing Studies", "value": _studies_count, "trend": "Catalog", "trend_state": "steady", "footnote": "JSON studies in workspace"},
        {"label": "Particles", "value": "9", "trend": "Supported", "trend_state": "up", "footnote": "Photon, charged, neutron, ion"},
        {"label": "Composer Modes", "value": "6", "trend": "Materials", "trend_state": "up", "footnote": "Formula, fractions, mixtures"},
        {"label": "Validators", "value": "Active", "trend": "Schema", "trend_state": "steady", "footnote": "Live JSON validation"},
        {"label": "Density Units", "value": "g/cm³", "trend": "Standard", "trend_state": "neutral", "footnote": "Mass density convention"},
        {"label": "Output", "value": "JSON", "trend": "Portable", "trend_state": "neutral", "footnote": "Run-ready study format"},
    ],
    title="ShieldLab Study Builder Strip",
    subtitle="Author run-ready ShieldLab studies with guided forms, schema validation, and material composer.",
)

_PARTICLES = {
    "gamma (photon)":   ("gamma",   "EM",  "Supported - G4EmStandard opt4"),
    "electron e-":      ("e-",      "EM",  "Supported - EM physics"),
    "positron e+":      ("e+",      "EM",  "Supported - EM physics"),
    "proton (p)":       ("proton",  "EM",  "Supported - EM physics"),
    "alpha":            ("alpha",   "EM",  "Supported - EM physics"),
    "neutron (n)":      ("neutron", "HAD", "Needs hadronic physics list (C++ build required)"),
    "mu- (muon)":       ("mu-",     "EM",  "Supported - EM physics"),
    "pi+ (pion)":       ("pi+",     "HAD", "Needs hadronic physics list (C++ build required)"),
    "Generic ion":      ("ion",     "ION", "Requires /gun/ion A Z command (C++ build required)"),
}
_ENERGY_UNITS = ["keV", "MeV", "eV", "GeV"]

_DEFAULT: dict = {
    "study_schema_version": "1.0",
    "name": "my_study",
    "description": "New shielding study",
    "source": {"particle": "gamma", "energy": 662, "energy_unit": "keV", "direction": [1, 0, 0]},
    "geometry": {
        "transverse_size_cm": 20,
        "layers": [{"material": "G4_Pb", "thickness_cm": 1.0, "divisions": 5}],
    },
    "materials": [],
    "run": {
        "histories": 10000,
        "output_dir": "results/my_study",
        "energy_grid": [100, 300, 662, 1000, 1500],
    },
}

if "study_json_text" not in st.session_state:
    st.session_state.study_json_text = json.dumps(_DEFAULT, indent=2)

templates = sorted(config.STUDIES_DIR.glob("*.json")) if config.STUDIES_DIR.exists() else []
t_names = ["new study"] + [p.name for p in templates]
col_tmpl, col_load = st.columns([4, 1])
with col_tmpl:
    selected_tmpl = st.selectbox("Template", t_names, label_visibility="collapsed")
with col_load:
    if st.button("Load", use_container_width=True) and selected_tmpl != "new study":
        st.session_state.study_json_text = (config.STUDIES_DIR / selected_tmpl).read_text(encoding="utf-8")
        st.rerun()

st.divider()

tab_mat, tab_guided, tab_json = st.tabs(["Material Composer", "Guided Form", "JSON Editor"])

# TAB 1 - MATERIAL COMPOSER
with tab_mat:
    st.markdown(
        str(copy["material_blurb"]) + " "
        "then click **Add to Study JSON**."
    )

    MODE_HELP = {
        "formula":               "Single compound by chemical formula  (e.g. PbWO4, Bi2O3, BaSO4)",
        "mass_fractions":        "Direct elemental mass fractions  (e.g. Pb:0.85, O:0.10, S:0.05)",
        "formula_mass_fractions":"Mixture of formulas by weight  (e.g. PbO:0.6, B2O3:0.2, SiO2:0.2)",
        "mixture":               "Two or more compounds mixed by weight fraction",
        "nanocomposite":         "Polymer matrix + nanoparticle fillers (formula + wt%)",
        "volume_fractions":      "Phases by volume fraction and phase density",
    }
    mode_col, _ = st.columns([2, 3])
    with mode_col:
        comp_mode = st.selectbox(
            "Composition mode",
            list(MODE_HELP.keys()),
            format_func=lambda m: f"{m}  -  {MODE_HELP[m].split('(')[0].strip()}",
        )
    st.caption(f"**{comp_mode}**: {MODE_HELP[comp_mode]}")
    st.info(_composer_physics_note(comp_mode))

    c_name, c_dens = st.columns([2, 1])
    with c_name:
        mat_name = st.text_input("Material name", value="MyMaterial",
                                 help="Used in geometry layers. No spaces.")
    with c_dens:
        density = st.number_input("Density (g/cm³)", value=2.0, min_value=0.001, max_value=30.0, format="%.4f")

    st.markdown("---")

    material_dict: dict | None = None
    input_error: str | None = None

    if comp_mode == "formula":
        formula_in = st.text_input("Chemical formula", value="PbWO4",
                                   help="Hill notation: PbWO4, Bi2O3, BaSO4, C2H4, Fe2O3 .")
        if formula_in.strip():
            material_dict = {"name": mat_name, "density_g_cm3": density, "formula": formula_in.strip()}

    elif comp_mode == "mass_fractions":
        st.markdown("Element : mass fraction pairs - must sum to 1.0.  e.g.  `Pb: 0.85, O: 0.10, S: 0.05`")
        mf_text = st.text_area("Elemental mass fractions", value="Pb: 0.85\nO:  0.10\nS:  0.05", height=130)
        mf_dict = {}
        try:
            for token in mf_text.replace("\n", ",").split(","):
                token = token.strip()
                if not token: continue
                el, val = token.split(":")
                mf_dict[el.strip()] = float(val.strip())
            total = sum(mf_dict.values())
            if abs(total - 1.0) > 0.01:
                input_error = f"Mass fractions sum to {total:.4f} - must equal 1.0."
            elif mf_dict:
                material_dict = {"name": mat_name, "density_g_cm3": density, "mass_fractions": mf_dict}
        except Exception as exc:
            input_error = f"Parse error: {exc}"

    elif comp_mode == "formula_mass_fractions":
        st.markdown("Formula : weight fraction - must sum to 1.0.  e.g.  `PbO: 0.60, B2O3: 0.20, SiO2: 0.20`")
        fmf_text = st.text_area("Compound weight fractions", value="PbO: 0.60\nB2O3: 0.20\nSiO2: 0.20", height=130)
        fmf_dict = {}
        try:
            for token in fmf_text.replace("\n", ",").split(","):
                token = token.strip()
                if not token: continue
                f, v = token.split(":")
                fmf_dict[f.strip()] = float(v.strip())
            total = sum(fmf_dict.values())
            if abs(total - 1.0) > 0.01:
                input_error = f"Weight fractions sum to {total:.4f} - must equal 1.0."
            elif fmf_dict:
                material_dict = {"name": mat_name, "density_g_cm3": density, "formula_mass_fractions": fmf_dict}
        except Exception as exc:
            input_error = f"Parse error: {exc}"

    elif comp_mode == "mixture":
        n_phases = st.number_input("Number of phases", min_value=2, max_value=10, value=2, step=1)
        phases = []
        hdr = st.columns([3, 2]); hdr[0].markdown("**Formula**"); hdr[1].markdown("**Weight fraction**")
        for i in range(int(n_phases)):
            c1, c2 = st.columns([3, 2])
            f = c1.text_input(f"Formula {i+1}", value=["C2H4","Bi2O3"][i] if i<2 else "", key=f"mx_f{i}")
            v = c2.number_input(f"wt {i+1}", value=round(1.0/int(n_phases),4),
                                min_value=0.0001, max_value=0.9999, format="%.4f", key=f"mx_v{i}")
            if f.strip(): phases.append({"formula": f.strip(), "weight_fraction": float(v)})
        total = sum(p["weight_fraction"] for p in phases)
        if abs(total - 1.0) > 0.01:
            input_error = f"Weight fractions sum to {total:.4f} - must equal 1.0."
        elif phases:
            material_dict = {"name": mat_name, "density_g_cm3": density, "mixture": phases}

    elif comp_mode == "nanocomposite":
        st.markdown("**Matrix** + nanoparticle **fillers** - all weight fractions must sum to 1.0.")
        c1, c2 = st.columns([3, 2])
        matrix_f = c1.text_input("Matrix formula", value="C2H4", help="e.g. C2H4, C3H6, C8H8")
        matrix_wf = c2.number_input("Matrix wt fraction", value=0.70, min_value=0.01, max_value=0.99, format="%.4f")
        n_fillers = st.number_input("Number of fillers", min_value=1, max_value=5, value=1, step=1)
        fillers = []
        remaining = round(1.0 - matrix_wf, 6)
        hdr = st.columns([3, 2]); hdr[0].markdown("**Filler formula**"); hdr[1].markdown("**Weight fraction**")
        for i in range(int(n_fillers)):
            c1, c2 = st.columns([3, 2])
            ff = c1.text_input(f"Filler {i+1}", value="Bi2O3", key=f"nc_ff{i}")
            fv = c2.number_input(f"Filler wt {i+1}", value=round(remaining/int(n_fillers),4),
                                 min_value=0.0001, max_value=0.9999, format="%.4f", key=f"nc_fv{i}")
            fillers.append({"formula": ff.strip(), "weight_fraction": float(fv)})
        total = matrix_wf + sum(f["weight_fraction"] for f in fillers)
        if abs(total - 1.0) > 0.01:
            input_error = f"All weight fractions sum to {total:.4f} - must equal 1.0."
        elif matrix_f.strip():
            material_dict = {
                "name": mat_name, "density_g_cm3": density,
                "nanocomposite": {
                    "matrix": {"formula": matrix_f.strip(), "weight_fraction": float(matrix_wf)},
                    "fillers": fillers,
                },
            }

    elif comp_mode == "volume_fractions":
        st.markdown("Phases by formula, bulk density, and volume fraction - vol fractions must sum to 1.0.")
        n_vf = st.number_input("Number of phases", min_value=2, max_value=8, value=2, step=1)
        vf_phases = []
        defaults = [("C2H4", 0.94, 0.60), ("BaSO4", 4.50, 0.40)]
        hdr = st.columns([3, 2, 2])
        hdr[0].markdown("**Formula**"); hdr[1].markdown("**ρ (g/cm³)**"); hdr[2].markdown("**Vol fraction**")
        for i in range(int(n_vf)):
            d = defaults[i] if i < len(defaults) else ("", 1.0, round(1.0/int(n_vf), 4))
            c1, c2, c3 = st.columns([3, 2, 2])
            f = c1.text_input(f"Formula {i+1}", value=d[0], key=f"vf_f{i}")
            rho = c2.number_input(f"ρ {i+1}", value=d[1], min_value=0.001, format="%.3f", key=f"vf_r{i}")
            vv = c3.number_input(f"vol {i+1}", value=d[2], min_value=0.0001, max_value=0.9999, format="%.4f", key=f"vf_v{i}")
            if f.strip():
                vf_phases.append({"formula": f.strip(), "density_g_cm3": float(rho), "volume_fraction": float(vv)})
        total = sum(p["volume_fraction"] for p in vf_phases)
        if abs(total - 1.0) > 0.01:
            input_error = f"Volume fractions sum to {total:.4f} - must equal 1.0."
        elif vf_phases:
            material_dict = {"name": mat_name, "density_g_cm3": density, "volume_fractions": vf_phases}

    if input_error:
        st.error(f"Error: {input_error}")

    if material_dict and not input_error:
        st.markdown("---")
        phase_rows = _phase_preview_rows(material_dict)
        if phase_rows:
            st.markdown("**Effective phase mixing used in the physics model**")
            st.dataframe(pd.DataFrame(phase_rows), use_container_width=True, hide_index=True)

        prev_col, desc_col = st.columns(2)
        mf = None
        with prev_col:
            st.markdown("**Elemental Mass Fractions**")
            try:
                mf = resolve_material_mass_fractions(material_dict)
                rows = [{"Element": el, "Mass Fraction": f"{wf:.6f}", "wt %": f"{wf*100:.3f}"}
                        for el, wf in sorted(mf.items(), key=lambda x: -x[1])]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=220)
            except Exception as exc:
                st.warning(f"Preview error: {exc}")
        with desc_col:
            st.markdown("**Shielding Descriptors**")
            if mf:
                try:
                    desc = material_descriptors(mat_name, mf, density)
                    rows2 = [
                        {"Parameter": "Density (g/cm³)",   "Value": f"{desc['density_g_cm3']:.4f}"},
                        {"Parameter": "Molar mass (g/mol)","Value": f"{desc['molar_mass_g_mol']:.4f}"},
                        {"Parameter": "Mean atomic Z",     "Value": f"{desc['average_Z']:.4f}"},
                        {"Parameter": "Z_eff  (n=3.5)",    "Value": f"{desc['Zeff_3p5']:.4f}"},
                        {"Parameter": "N_eff (e⁻/cm³)",    "Value": f"{desc['Neff_electrons_cm3']:.4e}"},
                        {"Parameter": "Electron density",  "Value": f"{desc['electron_density_cm3']:.4e}"},
                    ]
                    st.dataframe(pd.DataFrame(rows2), use_container_width=True, hide_index=True, height=220)
                except Exception as exc:
                    st.warning(f"Descriptor error: {exc}")

        st.markdown("---")
        add_col, info_col = st.columns([1, 3])
        with add_col:
            do_add = st.button("Add to Study JSON", type="primary", use_container_width=True)
        with info_col:
            st.caption("Appends this material to the `materials[]` array in the JSON Editor. Reference it by name in geometry layers.")
        if do_add:
            try:
                study = json.loads(st.session_state.study_json_text)
                if "materials" not in study:
                    study["materials"] = []
                study["materials"] = [m for m in study["materials"] if m.get("name") != mat_name]
                study["materials"].append(material_dict)
                st.session_state.study_json_text = json.dumps(study, indent=2)
                st.success(f"Material **{mat_name}** added. Switch to JSON Editor to review.")
                st.rerun()
            except json.JSONDecodeError:
                st.error("Current JSON is invalid - fix it in the JSON Editor first.")

# TAB 2 - GUIDED FORM
with tab_guided:
    st.info("Fill in the form, click Apply, then fine-tune in the JSON Editor tab. For custom materials, use the Material Composer tab first.")
    with st.form("guided_form"):
        st.markdown("#### Basic Info")
        g_name = st.text_input("Study name", value="my_study")
        g_desc = st.text_area("Description", value="", height=55)

        st.markdown("#### Beam Source")
        col_p, col_e, col_u = st.columns([2, 2, 1])
        with col_p:
            p_label = st.selectbox("Particle", list(_PARTICLES.keys()))
        p_g4name, p_type, p_note = _PARTICLES[p_label]
        with col_e:
            g_energy = st.number_input("Energy", value=662.0, min_value=0.001, format="%.3f")
        with col_u:
            g_unit = st.selectbox("Unit", _ENERGY_UNITS)

        if p_type in ("HAD", "ION"):
            st.warning(f"{p_label}: {p_note}")
        else:
            st.success(p_note)

        st.markdown("#### Geometry")
        col_m, col_t, col_ts, col_div = st.columns([3, 2, 2, 1])
        with col_m:
            g_mat = st.text_input("Material", value="G4_Pb",
                                  help="G4 NIST name (G4_Pb, G4_WATER) or a custom material from Material Composer.")
        with col_t:
            g_thickness = st.number_input("Thickness (cm)", value=1.0, min_value=0.001, format="%.3f")
        with col_ts:
            g_transverse = st.number_input("Transverse size (cm)", value=20.0, min_value=1.0)
        with col_div:
            g_divisions = st.number_input("Divisions", value=5, min_value=1, step=1)

        st.markdown("#### Run Configuration")
        col_h, col_sw = st.columns(2)
        with col_h:
            g_histories = st.number_input("Histories per run", value=10000, min_value=100, step=1000)
        with col_sw:
            g_sweep = st.selectbox("Sweep type", ["Energy sweep", "Thickness sweep", "Single run"])
        g_energies_str = st.text_input("Energy grid (keV, comma-separated)", value="100, 300, 662, 1000, 1500")
        g_thick_str = st.text_input("Thickness grid (cm, comma-separated)", value="0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0")
        submitted = st.form_submit_button("Apply to JSON Editor", use_container_width=True, type="primary")

    if submitted:
        safe_name = g_name.strip().replace(" ", "_").lower()
        try:
            existing_mats = json.loads(st.session_state.study_json_text).get("materials", [])
        except Exception:
            existing_mats = []
        study_dict: dict = {
            "name": g_name.strip(), "description": g_desc.strip(),
            "source": {"particle": p_g4name, "energy": float(g_energy), "energy_unit": g_unit, "direction": [1, 0, 0]},
            "geometry": {"transverse_size_cm": float(g_transverse),
                         "layers": [{"material": g_mat.strip(), "thickness_cm": float(g_thickness), "divisions": int(g_divisions)}]},
            "materials": existing_mats,
            "run": {"histories": int(g_histories), "output_dir": f"results/{safe_name}"},
        }
        if g_sweep == "Energy sweep":
            try:
                study_dict["run"]["energy_grid"] = [float(e.strip()) for e in g_energies_str.split(",") if e.strip()]
            except ValueError:
                st.error("Invalid energy grid.")
        elif g_sweep == "Thickness sweep":
            try:
                study_dict["run"]["thickness_grid"] = [float(t.strip()) for t in g_thick_str.split(",") if t.strip()]
            except ValueError:
                st.error("Invalid thickness grid.")
        st.session_state.study_json_text = json.dumps(study_dict, indent=2)
        st.success("Applied successfully. Switch to JSON Editor.")
        st.rerun()

# TAB 3 - JSON EDITOR
with tab_json:
    col_edit, col_val = st.columns([3, 2])
    with col_edit:
        st.markdown("**Study JSON**")
        new_text: str = st.text_area("json_area", value=st.session_state.study_json_text,
                                      height=540, label_visibility="collapsed", key="json_textarea")
        st.session_state.study_json_text = new_text
    with col_val:
        st.markdown("**Live Validation**")
        try:
            study_obj = json.loads(new_text)
            issues = validate_study(study_obj)
            n_err = sum(1 for i in issues if i.severity == "error")
            n_warn = sum(1 for i in issues if i.severity == "warning")
            if n_err:
                st.error(f"{n_err} error(s), {n_warn} warning(s)")
            elif n_warn:
                st.warning(f"{n_warn} warning(s), no errors")
            else:
                st.success("Valid, no issues")
            if issues:
                st.dataframe(issues_to_frame(issues)[["severity","path","message"]],
                             use_container_width=True, hide_index=True, height=170)
            if study_obj.get("materials"):
                st.markdown("**Material Descriptors**")
                try:
                    desc_df = descriptors_from_study(study_obj)
                    st.dataframe(desc_df[["material","density_g_cm3","molar_mass_g_mol","Zeff_3p5","Neff_electrons_cm3"]].round(4),
                                 use_container_width=True, hide_index=True)
                except Exception as exc:
                    st.warning(f"Descriptor preview unavailable: {exc}")
        except json.JSONDecodeError as e:
            st.error(f"JSON syntax error - {e}")

st.divider()

st.subheader("Save")
try:
    _default_fname = json.loads(st.session_state.study_json_text).get("name","study").replace(" ","_").lower() + ".json"
except Exception:
    _default_fname = "study.json"
col_name, col_save, col_dl = st.columns([3, 1, 1])
with col_name:
    save_name = st.text_input("Filename", value=_default_fname, label_visibility="collapsed")
with col_save:
    if st.button("Save to studies/", use_container_width=True):
        try:
            parsed = json.loads(st.session_state.study_json_text)
            (config.STUDIES_DIR / save_name).write_text(json.dumps(parsed, indent=2), encoding="utf-8")
            st.success(f"Saved: {save_name}")
        except json.JSONDecodeError:
            st.error("Fix JSON errors before saving.")
with col_dl:
    st.download_button("Download", data=st.session_state.study_json_text,
                       file_name=save_name, mime="application/json", use_container_width=True)



