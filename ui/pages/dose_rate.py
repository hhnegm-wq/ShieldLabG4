"""Dose-rate calculator page for ShieldLab G4."""
import sys
from pathlib import Path

_UI_DIR = Path(__file__).resolve().parent.parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from bootstrap import ensure_project_paths  # noqa: E402

ensure_project_paths()

import config  # noqa: F401, E402 - loads project constants

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math

from shieldlab.viz.style import apply_journal_style, finish_shieldlab_figure
from shieldlab.viz.export import figure_download_buttons
from shieldlab.content import PAGE_COPY
from shieldlab.core.materials import resolve_material_mass_fractions
from shieldlab.physics.dose_rate import (
    dose_rate_point,
    dose_rate_line,
    dose_rate_disk,
    shielded_dose_rate,
    dose_rate_table,
    GAMMA_K,
    fluence_to_h10,
    air_kerma_rate,
)
from shieldlab.physics.shielding_params import STANDARD_SOURCES, compute_shielding_table
from shieldlab.physics.nist_xcom import get_mac_compound
from auth import get_user_tier, render_tier_dev_toggle
from components.pro_gate import pro_badge
from components.layout import render_page_hero
from components.enterprise_ui import render_kpi_strip, render_panel_header, render_breadcrumb

apply_journal_style("shieldlab_web")


# Tier
if "SHIELDLAB_DEV" in __import__("os").environ:
    render_tier_dev_toggle()
_tier = get_user_tier()
copy = PAGE_COPY["dose_rate"]

# Page header
render_page_hero(str(copy["title"]), str(copy["caption"]), "Radiation Protection Dosimetry")
render_breadcrumb(["ShieldLab G4", "Analysis"], current="Dose-Rate Calculator")

render_kpi_strip(
    [
        {"label": "Source Models", "value": "Point/Line/Disk", "trend": "3", "trend_state": "up", "footnote": "Geometry kernels"},
        {"label": "Dose Tracks", "value": "H*(10)", "trend": "Ambient", "trend_state": "steady", "footnote": "Protection quantity"},
        {"label": "Shield Mode", "value": "Optional", "trend": "MAC", "trend_state": "neutral", "footnote": "Attenuation correction"},
        {"label": "Gamma-k Library", "value": len(GAMMA_K), "trend": "Isotopes", "trend_state": "up", "footnote": "Air-kerma constants"},
        {"label": "ICRP Basis", "value": "Pub 74", "trend": "h*(10)", "trend_state": "steady", "footnote": "Fluence conversion"},
        {"label": "Tier", "value": _tier.upper(), "trend": "Session", "trend_state": "neutral", "footnote": "Active account tier"},
    ],
    title="ShieldLab Dosimetry Control Strip",
    subtitle="Source, shielding, and protection-dose calculations with immediate chart and table exports.",
)

# Sidebar: source configuration
with st.expander(str(copy["source_header"]), expanded=True):
    source_mode = st.radio(
        "Source type",
        ["Isotope library", "Custom energy"],
        help="Choose a standard isotope or specify a mono-energetic source.",
    )

    if source_mode == "Isotope library":
        isotope = st.selectbox("Isotope", list(STANDARD_SOURCES.keys()),
                               index=list(STANDARD_SOURCES.keys()).index("Cs-137  (662 keV)"))
        lines = STANDARD_SOURCES[isotope]  # [(E_MeV, intensity), ...]
        E_list  = np.array([l[0] for l in lines])
        I_list  = np.array([l[1] for l in lines])
        gamma_k_val = GAMMA_K.get(isotope.strip(), None)
    else:
        E_custom = st.number_input("Energy (keV)", value=662.0, min_value=1.0, max_value=20000.0)
        I_custom = st.number_input("Photon yield / disintegration", value=1.0,
                                    min_value=0.001, max_value=100.0)
        E_list   = np.array([E_custom / 1000.0])
        I_list   = np.array([I_custom])
        gamma_k_val = None

    st.markdown("---")
    st.subheader("Activity")
    col_a, col_u = st.columns(2)
    with col_a:
        activity_val = st.number_input("Activity", value=1.0, min_value=1e-9, format="%.6g")
    with col_u:
        act_unit = st.selectbox("Unit", ["GBq", "MBq", "kBq", "Bq", "mCi", "Ci"])
    unit_to_bq = {"GBq": 1e9, "MBq": 1e6, "kBq": 1e3, "Bq": 1.0, "mCi": 3.7e7, "Ci": 3.7e10}
    A_Bq = activity_val * unit_to_bq[act_unit]

    st.markdown("---")
    st.subheader("Geometry")
    geom_type = st.radio("Geometry", ["Point source", "Line source", "Disk source"])
    if geom_type == "Line source":
        L_cm = st.number_input("Line length (cm)", value=100.0, min_value=0.1)
        A_Bq_per_cm = A_Bq / max(L_cm, 1e-9)
    elif geom_type == "Disk source":
        R_cm = st.number_input("Disk radius (cm)", value=10.0, min_value=0.1)
        A_Bq_per_cm2 = A_Bq / (math.pi * R_cm**2)

    st.markdown("---")
    st.subheader("Distance Range")
    d_min = st.number_input("Min distance (m)", value=0.1, min_value=0.01)
    d_max = st.number_input("Max distance (m)", value=10.0, min_value=0.1)
    n_d   = st.slider("Number of distances", 10, 200, 50)

    st.markdown("---")
    st.subheader("Shield (optional)")
    use_shield = st.checkbox("Apply a shield")
    if use_shield:
        shield_mat = st.text_input("Shield material formula", value="Pb")
        shield_rho = st.number_input("Shield density (g/cm³)", value=11.35, min_value=0.01)
        shield_x   = st.number_input("Thickness (cm)", value=5.0, min_value=0.0)
    else:
        shield_mat = None
        shield_rho = None
        shield_x   = 0.0

# Main calculation
distances_m = np.linspace(d_min, d_max, n_d)
distances_cm = distances_m * 100.0

# Fetch shield MAC at reference energy if shield specified
shield_mac_ref = None
if use_shield and shield_mat:
    try:
        with st.spinner("Fetching shield attenuation data..."):
            shield_mf = resolve_material_mass_fractions({"formula": shield_mat})
            shield_mac, _shield_mac_en = get_mac_compound(
                shield_mf,
                np.array([float(E_list.mean())]),
            )
            shield_mac_ref = float(shield_mac[0])
    except Exception:
        st.warning(str(copy["shield_data_warning"]))

# Compute dose rates at each distance
H_free  = np.zeros(len(distances_m))
H_shld  = np.zeros(len(distances_m)) if (use_shield and shield_mac_ref) else None

for i, (d_m, d_cm) in enumerate(zip(distances_m, distances_cm)):
    if geom_type == "Point source":
        H0 = dose_rate_point(A_Bq, E_list, I_list, d_cm)
    elif geom_type == "Line source":
        H0 = dose_rate_line(A_Bq_per_cm, L_cm, E_list, I_list, d_cm)
    else:
        H0 = dose_rate_disk(A_Bq_per_cm2, R_cm, E_list, I_list, d_cm)
    H_free[i] = H0
    if H_shld is not None:
        H_shld[i] = shielded_dose_rate(H0, shield_mac_ref, shield_rho, shield_x)

# Display
tab_plot, tab_table, tab_kerma, tab_icrp = st.tabs([
    "Dose-Rate Plot", "Dose-Rate Table", "Air-Kerma & Gamma_k", "ICRP-74 h*(10)"
])

# Tab 1: Dose-rate plot
with tab_plot:
    render_panel_header(
        "H*(10) Dose-Equivalent Rate vs Distance",
        "Log-space distance response for selected source geometry and activity.",
        controls=["Curve", "Reference Limits", "Export"],
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(distances_m, H_free, lw=2, color="#1E3A5F", label="Unshielded")
    if H_shld is not None:
        ax.loglog(distances_m, H_shld, lw=2, color="#E69F00", linestyle="--",
                  label=f"Shielded ({shield_x} cm {shield_mat})")

    # Reference lines
    ref_levels = {
        "Public (1 mSv/y -> 0.11 uSv/h)": 0.11,
        "Workers (20 mSv/y -> 2.28 uSv/h)": 2.28,
        "Controlled (0.4 mGy/h)": 400.0,
    }
    colours_ref = ["#009E73", "#D55E00", "#CC79A7"]
    for (label_r, val_r), col_r in zip(ref_levels.items(), colours_ref):
        ax.axhline(val_r, linestyle=":", color=col_r, lw=1.0, alpha=0.8)
        ax.text(distances_m[-1], val_r * 1.15, label_r, ha="right",
                fontsize=7, color=col_r)

    ax.set_xlabel("Distance from source (m)")
    ax.set_ylabel("H*(10) (uSv/h)")
    ax.set_title(
        f"Dose-Equivalent Rate - {activity_val} {act_unit} "
        f"{geom_type.replace(' source','')}"
    )
    ax.legend(fontsize=9)
    ax.grid(True, which="both", alpha=0.3)
    finish_shieldlab_figure(fig)

    figure_download_buttons(
        fig, "dose_rate_vs_distance",
        tier=_tier, key_prefix="dr_plot",
        caption=f"H*(10) dose-equivalent rate for {activity_val} {act_unit} {geom_type}.",
    )

# Tab 2: Dose-rate table
with tab_table:
    render_panel_header(
        "H*(10) at Selected Distances",
        "Numerical table for free-space and shielded dose rates.",
        controls=["Table", "CSV", "Reduction"],
    )
    df_table = pd.DataFrame({
        "Distance (m)":   np.round(distances_m, 3),
        "Distance (cm)":  np.round(distances_cm, 1),
        "H*(10) free (uSv/h)": np.round(H_free, 6),
    })
    if H_shld is not None:
        df_table["H*(10) shielded (uSv/h)"] = np.round(H_shld, 8)
        df_table["Reduction factor"] = np.where(
            H_shld > 0, np.round(H_free / H_shld, 1), float("inf")
        )
    st.dataframe(df_table, use_container_width=True)

    _csv = df_table.to_csv(index=False)
    st.download_button("Download CSV", _csv,
                       file_name="dose_rate_table.csv", mime="text/csv")

# Tab 3: Air-kerma rate constant
with tab_kerma:
    render_panel_header(
        "Air-Kerma Rate Constant Gamma_k",
        "Gamma constant-based kerma estimation for selected isotopes.",
        controls=["Gamma_k", "Rate", "Library"],
    )
    st.markdown(
        r"""
        The air-kerma rate constant relates activity to air-kerma rate at 1 m:

        $$\dot{K} = \Gamma_k \cdot \frac{A}{r^2}$$

        where $\Gamma_k$ is in uGy m^2/(MBq h).
        """
    )

    if gamma_k_val:
        st.metric(f"Gamma_k for {isotope}", f"{gamma_k_val:.4f} uGy m^2/(MBq h)")
        d_ref = st.number_input("Distance for K-dot (m)", value=1.0, min_value=0.01, key="kd")
        K_dot = air_kerma_rate(A_Bq, gamma_k_val, d_ref)
        col1, col2 = st.columns(2)
        col1.metric("Air-kerma rate", f"{K_dot:.4g} uGy/h")
        col2.metric("Air-kerma rate", f"{K_dot/100:.4g} mGy/h")
    else:
        st.info(str(copy["gamma_k_missing"]))

    st.subheader("Gamma_k Library (all isotopes)")
    df_gk = pd.DataFrame([
        {"Isotope": k, "Gamma_k [uGy m^2/(MBq h)]": v}
        for k, v in GAMMA_K.items()
    ])
    st.dataframe(df_gk, use_container_width=True)

# Tab 4: ICRP-74 h*(10) coefficients
with tab_icrp:
    render_panel_header(
        "ICRP Publication 74 - Fluence-to-Dose Coefficients h*(10)",
        "Reference conversion coefficients over energy for ambient dose equivalent.",
        controls=["Curve", "Reference Table", "Export"],
    )
    st.markdown(
        "Ambient dose equivalent conversion coefficient $h^*(10)$ (pSv·cm²) "
        "for photons, anterior-posterior geometry."
    )

    _E_grid = np.logspace(-2, 1, 200)
    _h_grid = fluence_to_h10(_E_grid)

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.semilogx(_E_grid * 1000, _h_grid, lw=2, color="#1E3A5F")
    # Mark source energies
    for e_i, i_i in zip(E_list, I_list):
        h_i = float(fluence_to_h10(e_i))
        ax2.axvline(e_i * 1000, color="#E69F00", lw=0.8, linestyle="--", alpha=0.6)
        ax2.scatter([e_i * 1000], [h_i], s=40, color="#E69F00", zorder=5)
    ax2.set_xlabel("Photon energy (keV)")
    ax2.set_ylabel("h*(10)  (pSv·cm²)")
    ax2.set_title("ICRP-74 Fluence-to-Dose Conversion (AP geometry)")
    ax2.grid(True, alpha=0.3)
    finish_shieldlab_figure(fig2)

    figure_download_buttons(
        fig2, "icrp74_h10",
        tier=_tier, key_prefix="icrp74_plot",
        caption=str(copy["icrp_caption"]),
    )

    # Table
    from shieldlab.physics.dose_rate import _ICRP74_E, _ICRP74_H  # noqa: PLC0415
    df_icrp = pd.DataFrame({
        "Energy (MeV)": _ICRP74_E,
        "Energy (keV)": (_ICRP74_E * 1000).round(1),
        "h*(10) [pSv·cm²]": _ICRP74_H,
    })
    st.dataframe(df_icrp, use_container_width=True)



