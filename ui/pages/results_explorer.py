"""Results Explorer page - figures, data tables, descriptors, download."""
from __future__ import annotations

import io
import json
import logging
import math
import sys
from pathlib import Path

_log = logging.getLogger(__name__)

import numpy as np
import pandas as pd
import streamlit as st

_UI_DIR = Path(__file__).resolve().parent.parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from bootstrap import ensure_project_paths  # noqa: E402

ensure_project_paths()

import config  # noqa: E402
from shieldlab.content import PAGE_COPY
from shieldlab.analysis import (
    compare_coefficients,
    load_reference_coefficients,
    resolve_reference_artifacts,
)
from shieldlab.analysis.runtime_benchmarks import (
    gp_buildup_from_coefficients,
    load_reference_acceptance,
    load_reference_buildup,
    summarize_reference_comparison,
)
import matplotlib.pyplot as plt
from shieldlab.viz.style import apply_journal_style, finish_shieldlab_figure, OKABE_ITO
from components.platform_settings import get_platform_settings
from components.layout import render_page_hero
from components.enterprise_ui import render_kpi_strip, render_panel_header, render_breadcrumb

copy = PAGE_COPY["results_explorer"]
_settings = get_platform_settings()

render_page_hero(str(copy["title"]), str(copy["caption"]), "Simulation Results & Analysis")
render_breadcrumb(["ShieldLab G4", "Analysis"], current="Results Explorer")

if not config.RESULTS_DIR.exists():
    st.warning(str(copy["missing_dir"]))
    st.stop()

result_dirs = sorted(
    [d for d in config.RESULTS_DIR.iterdir() if d.is_dir()],
    key=lambda d: d.stat().st_mtime,
    reverse=True,
)
if not result_dirs:
    st.info(str(copy["empty_dir"]))
    st.stop()

col_sel, col_style = st.columns([3, 1])
with col_sel:
    selected_name = st.selectbox(
        str(copy["folder_label"]),
        [d.name for d in result_dirs],
        help=str(copy["folder_help"]),
    )
with col_style:
    journal_preset = st.selectbox(
        "Figure style",
        ["shieldlab_web", "elsevier", "nature", "ieee", "aps", "publication_strict", "default"],
        help="Figure style preset. 'shieldlab_web' is optimised for on-screen display; journal presets use publication dimensions.",
    )

result_path = config.RESULTS_DIR / selected_name


# Load validation summary
val_file = result_path / "validation_summary.json"
val_data: dict = {}
if val_file.exists():
    try:
        val_data = json.loads(val_file.read_text())
    except Exception:
        _log.warning("Failed to parse validation_summary.json at %s", val_file, exc_info=True)

study_meta: dict = {}
study_file_path = Path(val_data["study_file"]) if isinstance(val_data.get("study_file"), str) else None
if study_file_path and study_file_path.exists():
    try:
        study_meta = json.loads(study_file_path.read_text(encoding="utf-8"))
    except Exception:
        study_meta = {}

_all_sec = sorted(result_path.glob("**/secondary_tally.csv"))
render_kpi_strip(
    [
        {"label": "Geant4 Runs", "value": val_data.get("run_summary_count", "-"), "trend": "Validated", "trend_state": "steady", "footnote": "Run summaries in result set"},
        {"label": "Stored Figures", "value": len(val_data.get("figures", [])), "trend": "Artifacts", "trend_state": "up", "footnote": "Registered output visuals"},
        {"label": "Excel Report", "value": "YES" if val_data.get("workbook") else "NO", "trend": "Workbook", "trend_state": "neutral", "footnote": "Compiled spreadsheet report"},
        {"label": "Reference Match", "value": "YES" if val_data.get("reference_comparison_exists") else "NO", "trend": "Benchmark", "trend_state": "steady", "footnote": "Literature coefficient comparison"},
        {"label": "Run Status", "value": str(val_data.get("status", "-")).upper(), "trend": "Execution", "trend_state": "neutral", "footnote": "Validation completion state"},
        {"label": "Secondary Tallies", "value": len(_all_sec), "trend": "Transport", "trend_state": "up" if _all_sec else "neutral", "footnote": "Secondary particle tally files"},
    ],
    title="ShieldLab Results Control Strip",
    subtitle="Execution status, artifact readiness, benchmark linkage, and secondary transport coverage.",
)

st.divider()

def _fig_to_png(fig, dpi: int = 300) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    return buf.read()


def _fig_to_pdf(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="pdf", bbox_inches="tight")
    buf.seek(0)
    return buf.read()


def _export_buttons(fig, basename: str, key: str) -> None:
    """Render PNG + PDF download buttons for a matplotlib figure."""
    st.download_button(
        "⬇ PNG", _fig_to_png(fig), f"{basename}.png", "image/png",
        key=f"{key}_png", width="stretch",
    )
    st.download_button(
        "⬇ PDF", _fig_to_pdf(fig), f"{basename}.pdf", "application/pdf",
        key=f"{key}_pdf", width="stretch",
    )


tab_analysis, tab_layer, tab_sec, tab_figs, tab_data, tab_desc, tab_dl = st.tabs([
    "MC Analysis",
    "Layer Physics",
    "Secondaries",
    "Stored Figures",
    "Numerical Data",
    "Descriptors",
    "Download",
])

# TAB 1 - MC Analysis: publication-quality sweep plots
with tab_analysis:
    render_panel_header(
        "Monte Carlo Analysis",
        "Energy/thickness/composition sweep diagnostics with benchmark overlays and uncertainty tables.",
        legend_items=[("Monte Carlo", "#10b981"), ("Reference", "#3b82f6"), ("Uncertainty", "#f59e0b")],
        controls=["Figures", "Tables", "Benchmark"],
    )
    apply_journal_style(journal_preset)

    BLUE  = OKABE_ITO[0]   # #0072B2
    ORNG  = OKABE_ITO[1]   # #E69F00
    GREEN = OKABE_ITO[2]   # #009E73
    RED   = OKABE_ITO[3]   # #D55E00
    PURP  = OKABE_ITO[4]   # #CC79A7
    SKY   = OKABE_ITO[5]   # #56B4E9

    _esweep_path = result_path / "sweep_summary.csv"
    if _esweep_path.exists():
        df_e = pd.read_csv(_esweep_path).sort_values("energy")
        reference_df, comparison_df, buildup_df = resolve_reference_artifacts(result_path, val_data, df_e)
        references_meta = study_meta.get("references", {}) if isinstance(study_meta.get("references", {}), dict) else {}
        geometry_meta = study_meta.get("geometry", {}) if isinstance(study_meta.get("geometry", {}), dict) else {}
        run_meta = study_meta.get("run", {}) if isinstance(study_meta.get("run", {}), dict) else {}
        source_meta = study_meta.get("source", {}) if isinstance(study_meta.get("source", {}), dict) else {}
        layers_meta = geometry_meta.get("layers", []) if isinstance(geometry_meta.get("layers", []), list) else []
        assumptions = val_data.get("assumptions", {}) if isinstance(val_data.get("assumptions", {}), dict) else {
            "particle": source_meta.get("particle"),
            "source_energy": source_meta.get("energy"),
            "source_energy_unit": source_meta.get("energy_unit"),
            "geometry_type": geometry_meta.get("type"),
            "layer_count": len(layers_meta),
            "total_thickness_cm": float(sum(float(layer.get("thickness_cm", 0.0)) for layer in layers_meta if isinstance(layer, dict))) if layers_meta else None,
            "materials": [material.get("name") for material in study_meta.get("materials", []) if isinstance(material, dict) and material.get("name")],
            "validation_mode": run_meta.get("validation_mode"),
            "physics_list": run_meta.get("physics_list"),
        }
        literature_sources = val_data.get("literature_sources", {}) if isinstance(val_data.get("literature_sources", {}), dict) else {
            "paper_title": references_meta.get("paper_title"),
            "paper_doi": references_meta.get("paper_doi"),
            "sample_id": references_meta.get("sample_id"),
            "has_reference_coefficients": bool(references_meta.get("coefficients")),
            "has_buildup_factors": bool((references_meta.get("buildup_factors") or {}).get("coefficients")) if isinstance(references_meta.get("buildup_factors") or {}, dict) else False,
            "buildup_source": (references_meta.get("buildup_factors") or {}).get("source") if isinstance(references_meta.get("buildup_factors") or {}, dict) else None,
        }
        benchmark_summary = val_data.get("benchmark_summary", {}) if isinstance(val_data.get("benchmark_summary", {}), dict) else {}
        if not benchmark_summary and study_file_path:
            benchmark_summary = summarize_reference_comparison(comparison_df, load_reference_acceptance(study_file_path))

        if assumptions or literature_sources or benchmark_summary:
            with st.expander("Study Assumptions, Provenance, and Benchmark Status", expanded=True):
                c_meta1, c_meta2, c_meta3 = st.columns(3)
                with c_meta1:
                    st.markdown("**Study assumptions**")
                    st.write(f"Particle: {assumptions.get('particle', '-')}")
                    st.write(f"Source energy: {assumptions.get('source_energy', '-')} {assumptions.get('source_energy_unit', '')}".strip())
                    st.write(f"Geometry: {assumptions.get('geometry_type', '-')}")
                    st.write(f"Layers: {assumptions.get('layer_count', '-')}")
                    if assumptions.get("total_thickness_cm") is not None:
                        st.write(f"Total thickness: {assumptions.get('total_thickness_cm', 0):.6g} cm")
                with c_meta2:
                    st.markdown("**Execution assumptions**")
                    st.write(f"Validation mode: {assumptions.get('validation_mode', '-')}")
                    st.write(f"Physics list: {assumptions.get('physics_list', '-')}")
                    materials = assumptions.get("materials") or []
                    st.write(f"Materials: {', '.join(str(m) for m in materials) if materials else '-'}")
                with c_meta3:
                    st.markdown("**Literature provenance**")
                    st.write(f"Paper: {literature_sources.get('paper_title', '-')}")
                    st.write(f"DOI: {literature_sources.get('paper_doi', '-')}")
                    st.write(f"Sample: {literature_sources.get('sample_id', '-')}")
                    st.write(f"Reference coefficients: {'yes' if literature_sources.get('has_reference_coefficients') else 'no'}")
                    st.write(f"Buildup coefficients: {'yes' if literature_sources.get('has_buildup_factors') else 'no'}")

                if benchmark_summary:
                    benchmark_status = benchmark_summary.get("status", "unavailable")
                    if benchmark_status == "failed":
                        st.error("Benchmark status: failed against configured acceptance limits.")
                    elif benchmark_status == "passed":
                        st.success("Benchmark status: passed configured acceptance limits.")
                    elif benchmark_status == "available":
                        st.info("Benchmark metrics are available, but no acceptance thresholds are configured for this study.")
                    else:
                        st.info("No benchmark comparison metrics are available for this result set.")

        _unit = str(df_e["energy_unit"].iloc[0]) if "energy_unit" in df_e.columns else "keV"
        E = df_e["energy"].to_numpy(dtype=float)
        T = df_e["transmission_fraction"].to_numpy(dtype=float)
        R = df_e.get("reflection_fraction", pd.Series(np.zeros(len(E)))).to_numpy(dtype=float)
        A = df_e.get("absorption_fraction", pd.Series(np.zeros(len(E)))).to_numpy(dtype=float)
        mu = df_e["linear_attenuation_cm_inv"].to_numpy(dtype=float)
        T_std = df_e.get("transmission_fraction_std", pd.Series(np.full(len(E), np.nan))).to_numpy(dtype=float)
        mu_std = df_e.get("linear_attenuation_std_cm_inv", pd.Series(np.full(len(E), np.nan))).to_numpy(dtype=float)
        mac = df_e.get("mass_attenuation_cm2_g", pd.Series(np.full(len(E), np.nan))).to_numpy(dtype=float)
        mac_std = df_e.get("mass_attenuation_std_cm2_g", pd.Series(np.full(len(E), np.nan))).to_numpy(dtype=float)
        hvl = df_e.get("hvl_cm", pd.Series(np.full(len(E), np.nan))).to_numpy(dtype=float)
        tvl = df_e.get("tvl_cm", pd.Series(np.full(len(E), np.nan))).to_numpy(dtype=float)
        mfp = df_e.get("mean_free_path_cm", pd.Series(np.full(len(E), np.nan))).to_numpy(dtype=float)
        thickness = df_e.get("total_thickness_cm", pd.Series(np.full(len(E), np.nan))).to_numpy(dtype=float)

        ref_mac_df = reference_df.copy()
        if not ref_mac_df.empty:
            ref_mac_df = ref_mac_df[
                (ref_mac_df.get("energy_unit", pd.Series(dtype=str)).astype(str).str.lower() == _unit.lower())
                & ref_mac_df.get("mass_attenuation_cm2_g", pd.Series(dtype=float)).notna()
            ].sort_values("energy")

        has_variable_thickness = np.isfinite(thickness).any() and np.nanmax(thickness) - np.nanmin(thickness) > 1e-9

        st.subheader("Energy Sweep - Monte Carlo Results")
        if has_variable_thickness:
            st.caption(
                f"Benchmark narrow-beam mode used an energy-dependent slab thickness from {np.nanmin(thickness):.4f} to {np.nanmax(thickness):.4f} cm to keep transmission in a measurable range."
            )
        if np.isfinite(T_std).any() or np.isfinite(mu_std).any():
            u1, u2 = st.columns(2)
            with u1:
                if np.isfinite(T_std).any():
                    st.metric("Median T std. err.", f"{np.nanmedian(T_std):.4g}")
            with u2:
                if np.isfinite(mu_std).any():
                    st.metric("Median μ std. err.", f"{np.nanmedian(mu_std):.4g} cm⁻¹")
            st.caption(
                "Uncertainty is currently propagated from primary transmitted/reflected counts using a binomial model and delta-method conversion for attenuation-derived quantities."
            )

        fig1, ax1 = plt.subplots()
        ax1r = ax1.twinx()
        ln1 = ax1.semilogy(E, T, "o-", color=BLUE, lw=1.5, ms=4, label=r"$T(E)$ - MC")
        ln2 = ax1r.loglog(E, mu, "s--", color=ORNG, lw=1.2, ms=3.5, label=r"$\mu\,(E)$ (cm$^{-1}$)")
        ax1.set_xlabel(f"Photon Energy ({_unit})")
        ax1.set_ylabel(r"Transmission $T$ (fraction)", color=BLUE)
        ax1r.set_ylabel(r"Linear Attenuation $\mu$ (cm$^{-1}$)", color=ORNG)
        ax1.tick_params(axis="y", colors=BLUE)
        ax1r.tick_params(axis="y", colors=ORNG)
        lns = ln1 + ln2
        ax1.legend(lns, [l.get_label() for l in lns], loc="best")
        ax1.set_title(f"MC Transmission & Attenuation - {selected_name}")
        ax1.grid(True, which="both", ls=":", alpha=0.35)
        finish_shieldlab_figure(fig1)
        col1, col2 = st.columns([4, 1])
        with col1:
            st.pyplot(fig1, width="stretch")
        with col2:
            st.markdown("**Export**")
            _export_buttons(fig1, f"{selected_name}_T_mu_vs_E", "fig1")
        plt.close(fig1)

        if not np.all(np.isnan(hvl)):
            fig2, ax2 = plt.subplots()
            ax2.semilogy(E, hvl, "o-", color=BLUE, lw=1.5, ms=4, label="HVL (cm)")
            ax2.semilogy(E, tvl, "s--", color=ORNG, lw=1.5, ms=4, label="TVL (cm)")
            ax2.set_xlabel(f"Photon Energy ({_unit})")
            ax2.set_ylabel("Thickness (cm)")
            ax2.set_title(f"Half-Value Layer & Tenth-Value Layer - {selected_name}")
            ax2.legend()
            ax2.grid(True, which="both", ls=":", alpha=0.35)
            finish_shieldlab_figure(fig2)
            col3, col4 = st.columns([4, 1])
            with col3:
                st.pyplot(fig2, width="stretch")
            with col4:
                st.markdown("**Export**")
                _export_buttons(fig2, f"{selected_name}_HVL_TVL_vs_E", "fig2")
            plt.close(fig2)

        if not np.all(np.isnan(mac)):
            if comparison_df.empty:
                fig3, ax3 = plt.subplots()
                ax3.loglog(E, mac, "D-", color=GREEN, lw=1.5, ms=4,
                           label=r"$\mu/\rho$ (cm$^2$ g$^{-1}$)")
                ax3.set_xlabel(f"Photon Energy ({_unit})")
                ax3.set_ylabel(r"Mass Attenuation Coefficient $\mu/\rho$ (cm$^2$ g$^{-1}$)")
                ax3.set_title(f"Mass Attenuation Coefficient - {selected_name}")
                if not ref_mac_df.empty:
                    ax3.loglog(
                        ref_mac_df["energy"].to_numpy(dtype=float),
                        ref_mac_df["mass_attenuation_cm2_g"].to_numpy(dtype=float),
                        "o--",
                        color=RED,
                        lw=1.2,
                        ms=4,
                        label="Published paper",
                    )
                ax3.legend()
                ax3.grid(True, which="both", ls=":", alpha=0.35)
            else:
                fig3, (ax3, ax3r) = plt.subplots(
                    2,
                    1,
                    sharex=True,
                    gridspec_kw={"height_ratios": [3, 1], "hspace": 0.08},
                )
                ax3.loglog(E, mac, "D-", color=GREEN, lw=1.5, ms=4,
                           label="Monte Carlo")
                ref_energy = comparison_df["energy"].to_numpy(dtype=float)
                ref_mac = comparison_df["mass_attenuation_cm2_g_reference"].to_numpy(dtype=float)
                mc_ref = comparison_df["mass_attenuation_cm2_g_simulated"].to_numpy(dtype=float)
                pct = comparison_df["mass_attenuation_cm2_g_percent_difference"].to_numpy(dtype=float)
                ax3.loglog(ref_energy, ref_mac, "o--", color=RED, lw=1.2, ms=4, label="Published paper")
                ax3.loglog(ref_energy, mc_ref, "s", color=BLUE, ms=4, label="MC at paper energies")
                ax3.set_ylabel(r"Mass Attenuation Coefficient $\mu/\rho$ (cm$^2$ g$^{-1}$)")
                ax3.set_title(f"Paper vs Monte Carlo MAC Overlay - {selected_name}")
                ax3.legend()
                ax3.grid(True, which="both", ls=":", alpha=0.35)

                ax3r.axhline(0.0, color="black", lw=0.8, alpha=0.5)
                ax3r.semilogx(ref_energy, pct, "o-", color=ORNG, lw=1.2, ms=4)
                ax3r.set_xlabel(f"Photon Energy ({_unit})")
                ax3r.set_ylabel("Diff. (%)")
                ax3r.grid(True, which="both", ls=":", alpha=0.35)
            finish_shieldlab_figure(fig3)
            col5, col6 = st.columns([4, 1])
            with col5:
                st.pyplot(fig3, width="stretch")
            with col6:
                st.markdown("**Export**")
                _export_buttons(fig3, f"{selected_name}_MAC_vs_E", "fig3")
            plt.close(fig3)

            if not comparison_df.empty:
                mean_abs_pct = float(comparison_df["mass_attenuation_cm2_g_percent_difference"].abs().mean())
                max_abs_pct = float(comparison_df["mass_attenuation_cm2_g_percent_difference"].abs().max())
                c_cmp1, c_cmp2, c_cmp3 = st.columns(3)
                with c_cmp1:
                    st.metric("Mean |MAC diff|", f"{mean_abs_pct:.2f}%")
                with c_cmp2:
                    st.metric("Max |MAC diff|", f"{max_abs_pct:.2f}%")
                if "mass_attenuation_cm2_g_normalized_residual" in comparison_df.columns:
                    normalized = pd.to_numeric(comparison_df["mass_attenuation_cm2_g_normalized_residual"], errors="coerce")
                    with c_cmp3:
                        if normalized.notna().any():
                            st.metric("Max |MAC residual| / σ", f"{normalized.abs().max():.2f}")
                st.dataframe(
                    comparison_df.round(5),
                    width="stretch",
                    hide_index=True,
                )

                quantities = benchmark_summary.get("quantities", {}) if isinstance(benchmark_summary, dict) else {}
                if quantities:
                    bench_rows = []
                    for metric_name, metric_data in quantities.items():
                        thresholds = metric_data.get("thresholds", {}) if isinstance(metric_data.get("thresholds", {}), dict) else {}
                        bench_rows.append({
                            "Metric": metric_name,
                            "Status": metric_data.get("status", "available"),
                            "Mean |diff| (%)": metric_data.get("mean_abs_percent_difference"),
                            "Max |diff| (%)": metric_data.get("max_abs_percent_difference"),
                            "Mean signed diff (%)": metric_data.get("mean_signed_percent_difference"),
                            "Threshold mean |diff| (%)": thresholds.get("mean_abs_max"),
                            "Threshold max |diff| (%)": thresholds.get("max_abs_max"),
                        })
                    st.markdown("**Benchmark residual summary**")
                    st.dataframe(pd.DataFrame(bench_rows).round(4), width="stretch", hide_index=True)

                normalized_cols = [
                    column
                    for column in [
                        "linear_attenuation_cm_inv_normalized_residual",
                        "mass_attenuation_cm2_g_normalized_residual",
                    ]
                    if column in comparison_df.columns
                ]
                if normalized_cols:
                    st.caption(
                        "Normalized residuals are computed as (simulation - literature) / simulation standard error where uncertainty is available."
                    )

            if np.isfinite(T_std).any() or np.isfinite(mu_std).any() or np.isfinite(mac_std).any():
                uncertainty_cols = ["energy", "energy_unit", "transmission_fraction"]
                for column in [
                    "transmission_fraction_std",
                    "transmission_fraction_ci95_half_width",
                    "linear_attenuation_cm_inv",
                    "linear_attenuation_std_cm_inv",
                    "mass_attenuation_cm2_g",
                    "mass_attenuation_std_cm2_g",
                ]:
                    if column in df_e.columns:
                        uncertainty_cols.append(column)
                st.markdown("**Monte Carlo uncertainty summary**")
                st.dataframe(df_e[uncertainty_cols].round(6), width="stretch", hide_index=True)

        fig4, ax4 = plt.subplots()
        ax4.stackplot(E, T, R, A,
                      labels=["Transmitted", "Reflected", "Absorbed"],
                      colors=[BLUE, ORNG, RED], alpha=0.75)
        ax4.set_xlabel(f"Photon Energy ({_unit})")
        ax4.set_ylabel("Fraction of Primary Events")
        ax4.set_title(f"Transport Fractions vs Energy - {selected_name}")
        ax4.legend(loc="upper right")
        ax4.set_ylim(0, 1)
        ax4.grid(True, ls=":", alpha=0.35)
        finish_shieldlab_figure(fig4)
        col7, col8 = st.columns([4, 1])
        with col7:
            st.pyplot(fig4, width="stretch")
        with col8:
            st.markdown("**Export**")
            _export_buttons(fig4, f"{selected_name}_fractions_vs_E", "fig4")
        plt.close(fig4)

        if not np.all(np.isnan(mfp)) and not np.all(mfp == 0):
            fig5, ax5 = plt.subplots()
            ax5.loglog(E, mfp, "^-", color=PURP, lw=1.5, ms=4, label="MFP (cm)")
            ax5.set_xlabel(f"Photon Energy ({_unit})")
            ax5.set_ylabel(r"Mean Free Path $\lambda$ (cm)")
            ax5.set_title(f"Mean Free Path vs Energy - {selected_name}")
            ax5.legend()
            ax5.grid(True, which="both", ls=":", alpha=0.35)
            finish_shieldlab_figure(fig5)
            col9, col10 = st.columns([4, 1])
            with col9:
                st.pyplot(fig5, width="stretch")
            with col10:
                st.markdown("**Export**")
                _export_buttons(fig5, f"{selected_name}_MFP_vs_E", "fig5")
            plt.close(fig5)

        buildup_observable_file = val_data.get("buildup_observable_summary")
        buildup_comparison_file = val_data.get("buildup_comparison")
        mc_buildup_path = Path(buildup_observable_file) if isinstance(buildup_observable_file, str) else (result_path / "buildup_observable_summary.csv")
        buildup_cmp_path = Path(buildup_comparison_file) if isinstance(buildup_comparison_file, str) else (result_path / "buildup_comparison.csv")
        mc_buildup_df = pd.read_csv(mc_buildup_path) if mc_buildup_path.exists() else pd.DataFrame()
        buildup_cmp_df = pd.read_csv(buildup_cmp_path) if buildup_cmp_path.exists() else pd.DataFrame()

        if not buildup_df.empty or not mc_buildup_df.empty:
            bunit = str(buildup_df["energy_unit"].dropna().astype(str).iloc[0]) if buildup_df["energy_unit"].notna().any() else "MeV"
            depth_mfp = st.slider(
                "Literature buildup depth (mean free paths, μx)",
                min_value=1.0,
                max_value=40.0,
                value=5.0,
                step=0.5,
                help="Evaluates literature G-P coefficients at the selected penetration depth.",
            )

            bdf = buildup_df.copy()
            bdf = bdf[bdf["energy"].notna()].sort_values("energy")
            mc_df = mc_buildup_df.copy()
            if not mc_df.empty:
                mc_df = mc_df[mc_df["energy"].notna()].copy()
                if "energy_unit" in mc_df.columns:
                    unit_l = bunit.lower()
                    src_u = mc_df["energy_unit"].astype(str).str.lower()
                    with np.errstate(invalid="ignore"):
                        if unit_l == "mev":
                            mc_df["energy_plot"] = np.where(src_u == "kev", mc_df["energy"] / 1000.0, mc_df["energy"])
                        elif unit_l == "kev":
                            mc_df["energy_plot"] = np.where(src_u == "mev", mc_df["energy"] * 1000.0, mc_df["energy"])
                        else:
                            mc_df["energy_plot"] = mc_df["energy"]
                else:
                    mc_df["energy_plot"] = mc_df["energy"]
                mc_df = mc_df.sort_values("energy_plot")

            if not bdf.empty or not mc_df.empty:
                bdf["EBF (literature)"] = bdf.apply(
                    lambda r: gp_buildup_from_coefficients(
                        float(r["ebf_a"]),
                        float(r["ebf_b"]),
                        float(r["ebf_c"]),
                        float(r["ebf_d"]),
                        float(r["ebf_xk"]),
                        float(depth_mfp),
                    )
                    if pd.notna(r["ebf_a"]) and pd.notna(r["ebf_b"]) and pd.notna(r["ebf_c"]) and pd.notna(r["ebf_d"]) and pd.notna(r["ebf_xk"])
                    else np.nan,
                    axis=1,
                )
                bdf["EABF (literature)"] = bdf.apply(
                    lambda r: gp_buildup_from_coefficients(
                        float(r["eabf_a"]),
                        float(r["eabf_b"]),
                        float(r["eabf_c"]),
                        float(r["eabf_d"]),
                        float(r["eabf_xk"]),
                        float(depth_mfp),
                    )
                    if pd.notna(r["eabf_a"]) and pd.notna(r["eabf_b"]) and pd.notna(r["eabf_c"]) and pd.notna(r["eabf_d"]) and pd.notna(r["eabf_xk"])
                    else np.nan,
                    axis=1,
                )

                fig6, ax6 = plt.subplots()
                if not bdf.empty:
                    xvals = bdf["energy"].to_numpy(dtype=float)
                    ax6.semilogx(xvals, bdf["EBF (literature)"].to_numpy(dtype=float), "o-", color=BLUE, lw=1.5, ms=4, label="EBF (literature)")
                    ax6.semilogx(xvals, bdf["EABF (literature)"].to_numpy(dtype=float), "s--", color=ORNG, lw=1.5, ms=4, label="EABF (literature)")
                if not mc_df.empty and "mc_buildup_observable_energy" in mc_df.columns:
                    ax6.semilogx(
                        mc_df["energy_plot"].to_numpy(dtype=float),
                        mc_df["mc_buildup_observable_energy"].to_numpy(dtype=float),
                        "^-",
                        color=GREEN,
                        lw=1.5,
                        ms=4,
                        label="MC buildup observable (energy)",
                    )
                ax6.set_xlabel(f"Photon Energy ({bunit})")
                ax6.set_ylabel(f"Buildup Factor at μx = {depth_mfp:.1f}")
                ax6.set_title(f"Buildup Comparison - {selected_name}")
                ax6.legend()
                ax6.grid(True, which="both", ls=":", alpha=0.35)
                finish_shieldlab_figure(fig6)

                col11, col12 = st.columns([4, 1])
                with col11:
                    st.pyplot(fig6, width="stretch")
                with col12:
                    st.markdown("**Export**")
                    _export_buttons(fig6, f"{selected_name}_literature_buildup", "fig6")
                plt.close(fig6)

                if not bdf.empty:
                    st.dataframe(
                        bdf[["energy", "energy_unit", "zeq", "EBF (literature)", "EABF (literature)"]].round(6),
                        width="stretch",
                        hide_index=True,
                    )

                if not mc_df.empty:
                    cols = [
                        "energy",
                        "energy_unit",
                        "downstream_secondary_count_per_event",
                        "downstream_secondary_energy_per_event_MeV",
                        "mc_buildup_observable_count",
                        "mc_buildup_observable_energy",
                    ]
                    cols = [c for c in cols if c in mc_df.columns]
                    st.markdown("**Monte Carlo buildup observables**")
                    st.dataframe(mc_df[cols].round(6), width="stretch", hide_index=True)

                if not bdf.empty and not mc_df.empty and "mc_buildup_observable_energy" in mc_df.columns:
                    if buildup_cmp_df.empty:
                        lit_cmp = bdf[["energy", "EBF (literature)"]].copy()
                        mc_cmp = mc_df[["energy_plot", "mc_buildup_observable_energy"]].copy().rename(columns={"energy_plot": "energy"})
                        cmp = lit_cmp.merge(mc_cmp, on="energy", how="inner")
                        if not cmp.empty:
                            cmp["buildup_observable_energy_percent_difference"] = (
                                (cmp["mc_buildup_observable_energy"] - cmp["EBF (literature)"])
                                / cmp["EBF (literature)"].replace(0.0, np.nan)
                                * 100.0
                            )
                    else:
                        cmp = buildup_cmp_df.copy()

                    if not cmp.empty and "buildup_observable_energy_percent_difference" in cmp.columns:
                        c_b1, c_b2 = st.columns(2)
                        with c_b1:
                            st.metric(
                                "Mean |MC vs literature buildup diff|",
                                f"{cmp['buildup_observable_energy_percent_difference'].abs().mean():.2f}%",
                            )
                        with c_b2:
                            st.metric(
                                "Max |MC vs literature buildup diff|",
                                f"{cmp['buildup_observable_energy_percent_difference'].abs().max():.2f}%",
                            )
                        buildup_metric = {}
                        if isinstance(benchmark_summary, dict):
                            quantities = benchmark_summary.get("quantities", {}) if isinstance(benchmark_summary.get("quantities", {}), dict) else {}
                            buildup_metric = quantities.get("buildup_observable_energy_percent_difference", {}) if isinstance(quantities.get("buildup_observable_energy_percent_difference", {}), dict) else {}
                        metric_status = buildup_metric.get("status")
                        if metric_status == "passed":
                            st.success("Buildup residual metric: passed configured acceptance limits.")
                        elif metric_status == "failed":
                            st.error("Buildup residual metric: failed configured acceptance limits.")
                        st.dataframe(cmp.round(6), width="stretch", hide_index=True)
                    else:
                        st.info("MC buildup observable file is present, but no exact energy matches with literature buildup coefficients were found.")

                st.caption(
                    "Monte Carlo buildup observables are a simulation-side scaffold derived from downstream secondary yields and energy. They support preliminary MC-vs-literature trend checks while full detector-response buildup scoring is implemented."
                )

    _tsweep_path = result_path / "thickness_sweep_summary.csv"
    if _tsweep_path.exists():
        df_t = pd.read_csv(_tsweep_path).sort_values("thickness_cm")
        Xarr = df_t["thickness_cm"].to_numpy(dtype=float)
        Tarr = df_t["transmission_fraction"].to_numpy(dtype=float)
        mu_t = df_t["linear_attenuation_cm_inv"].to_numpy(dtype=float)
        Tarr_std = df_t.get("transmission_fraction_std", pd.Series(np.full(len(Xarr), np.nan))).to_numpy(dtype=float)
        mu_t_std = df_t.get("linear_attenuation_std_cm_inv", pd.Series(np.full(len(Xarr), np.nan))).to_numpy(dtype=float)

        st.subheader("Thickness Sweep - Monte Carlo Results")
        if np.isfinite(Tarr_std).any() or np.isfinite(mu_t_std).any():
            t_u1, t_u2 = st.columns(2)
            with t_u1:
                if np.isfinite(Tarr_std).any():
                    st.metric("Median T std. err. (thickness)", f"{np.nanmedian(Tarr_std):.4g}")
            with t_u2:
                if np.isfinite(mu_t_std).any():
                    st.metric("Median μ std. err. (thickness)", f"{np.nanmedian(mu_t_std):.4g} cm⁻¹")

        fig6, axes6 = plt.subplots(1, 2, figsize=(plt.rcParams["figure.figsize"][0] * 2.1,
                                                    plt.rcParams["figure.figsize"][1]))
        ax6a, ax6b = axes6

        # Beer-Lambert fit
        valid = (Tarr > 0) & np.isfinite(Tarr)
        if np.isfinite(Tarr_std).any():
            ax6a.errorbar(Xarr, Tarr, yerr=Tarr_std, fmt="o", color=BLUE, ms=4, lw=1.0,
                          capsize=2, label="MC simulation", zorder=3)
        else:
            ax6a.semilogy(Xarr, Tarr, "o", color=BLUE, ms=4, label="MC simulation", zorder=3)
        if valid.sum() >= 2:
            mu_fit = np.polyfit(Xarr[valid], -np.log(Tarr[valid]), 1)[0]
            x_fit = np.linspace(Xarr.min(), Xarr.max(), 200)
            ax6a.semilogy(x_fit, np.exp(-mu_fit * x_fit), "--", color=ORNG, lw=1.5,
                          label=fr"Beer-Lambert fit: $\mu={mu_fit:.3f}$ cm$^{{-1}}$")
        ax6a.set_xlabel(r"Shield Thickness $x$ (cm)")
        ax6a.set_ylabel(r"Transmission $T = e^{-\mu x}$")
        ax6a.set_title("Transmission vs Thickness")
        ax6a.legend()
        ax6a.grid(True, which="both", ls=":", alpha=0.35)

        # ? constancy
        mu_valid = mu_t[np.isfinite(mu_t) & (mu_t > 0)]
        if np.isfinite(mu_t_std).any():
            ax6b.errorbar(Xarr, mu_t, yerr=mu_t_std, fmt="s-", color=GREEN, lw=1.2, ms=4, capsize=2)
        else:
            ax6b.plot(Xarr, mu_t, "s-", color=GREEN, lw=1.2, ms=4)
        if len(mu_valid) > 0:
            ax6b.axhline(float(np.mean(mu_valid)), ls="--", color=RED, lw=1, label=fr"$\bar{{\mu}}={np.mean(mu_valid):.3f}$")
        ax6b.set_xlabel(r"Shield Thickness $x$ (cm)")
        ax6b.set_ylabel(r"Linear Attenuation $\mu$ (cm$^{-1}$)")
        ax6b.set_title(r"$\mu$ Consistency Check")
        ax6b.legend()
        ax6b.grid(True, ls=":", alpha=0.35)

        fig6.suptitle(f"Thickness Sweep - {selected_name}", fontweight="bold")
        finish_shieldlab_figure(fig6)
        col_t1, col_t2 = st.columns([4, 1])
        with col_t1:
            st.pyplot(fig6, width="stretch")
        with col_t2:
            st.markdown("**Export**")
            _export_buttons(fig6, f"{selected_name}_thickness_sweep", "fig6")
        plt.close(fig6)

        if np.isfinite(Tarr_std).any() or np.isfinite(mu_t_std).any():
            st.markdown("**Thickness sweep uncertainty summary**")
            uncertainty_cols_t = ["thickness_cm", "transmission_fraction"]
            for column in [
                "transmission_fraction_std",
                "transmission_fraction_ci95_half_width",
                "linear_attenuation_cm_inv",
                "linear_attenuation_std_cm_inv",
                "mass_attenuation_cm2_g",
                "mass_attenuation_std_cm2_g",
            ]:
                if column in df_t.columns:
                    uncertainty_cols_t.append(column)
            st.dataframe(df_t[uncertainty_cols_t].round(6), width="stretch", hide_index=True)
            st.caption("Thickness-sweep uncertainty follows the same binomial-count and delta-method propagation used for the energy sweep.")

    _single_run = result_path / "run_summary.csv"
    if _single_run.exists():
        df_sr = pd.read_csv(_single_run).iloc[0]
        T_s = float(df_sr.get("transmission_fraction", 0))
        R_s = float(df_sr.get("reflection_fraction", 0))
        A_s = float(df_sr.get("absorption_fraction", 0))
        mu_s = float(df_sr.get("linear_attenuation_cm_inv", 0))
        x_s = float(df_sr.get("total_thickness_cm", 0))
        N_s = int(df_sr.get("events", 0))
        transmitted_s = float(df_sr.get("transmitted", 0))
        reflected_s = float(df_sr.get("reflected", 0))
        T_s_std = np.sqrt(T_s * max(1.0 - T_s, 0.0) / N_s) if N_s > 0 else np.nan
        R_s_std = np.sqrt(R_s * max(1.0 - R_s, 0.0) / N_s) if N_s > 0 else np.nan
        absorbed_count_s = max(N_s - transmitted_s - reflected_s, 0.0)
        A_s_std = np.sqrt(A_s * max(1.0 - A_s, 0.0) / N_s) if N_s > 0 else np.nan
        mu_s_std = T_s_std / (x_s * T_s) if N_s > 0 and x_s > 0 and T_s > 0 else np.nan

        if T_s > 0 or R_s > 0 or A_s > 0:
            st.subheader("Single-Run Transport Summary")
            fig7, ax7 = plt.subplots(figsize=(3.5, 3.5))
            labels7 = ["Transmitted", "Reflected", "Absorbed"]
            vals7 = [T_s, R_s, A_s]
            colors7 = [BLUE, ORNG, RED]
            non_zero = [(l, v, c) for l, v, c in zip(labels7, vals7, colors7) if v > 1e-6]
            if non_zero:
                l7, v7, c7 = zip(*non_zero)
                wedges, texts, autotexts = ax7.pie(
                    v7, labels=l7, colors=c7,
                    autopct="%1.2f%%", startangle=90,
                    wedgeprops={"linewidth": 0.8, "edgecolor": "white"},
                )
                for at in autotexts:
                    at.set_fontsize(plt.rcParams.get("font.size", 8))
            ax7.set_title(
                f"Transport Fractions\n"
                f"N={N_s:,}  x={x_s:.2f} cm  μ={mu_s:.4f} cm⁻¹",
            )
            finish_shieldlab_figure(fig7)
            col_sr1, col_sr2 = st.columns([2, 2])
            with col_sr1:
                st.pyplot(fig7, width="stretch")
                _export_buttons(fig7, f"{selected_name}_transport_fractions", "fig7")
            with col_sr2:
                st.markdown("**Key results:**")
                kpi_rows = [
                    ("Events (histories)", f"{N_s:,}"),
                    ("Transmitted", f"{T_s:.4f}  ({T_s*100:.2f} %) +/- {1.96*T_s_std:.4f}" if np.isfinite(T_s_std) else f"{T_s:.4f}  ({T_s*100:.2f} %)") ,
                    ("Reflected", f"{R_s:.4f}  ({R_s*100:.2f} %) +/- {1.96*R_s_std:.4f}" if np.isfinite(R_s_std) else f"{R_s:.4f}  ({R_s*100:.2f} %)") ,
                    ("Absorbed", f"{A_s:.4f}  ({A_s*100:.2f} %) +/- {1.96*A_s_std:.4f}" if np.isfinite(A_s_std) else f"{A_s:.4f}  ({A_s*100:.2f} %)") ,
                    ("μ (cm⁻¹)", f"{mu_s:.5f} +/- {1.96*mu_s_std:.5f}" if np.isfinite(mu_s_std) else f"{mu_s:.5f}"),
                    ("Total thickness (cm)", f"{x_s:.3f}"),
                ]
                st.dataframe(
                    pd.DataFrame(kpi_rows, columns=["Quantity", "Value"]),
                    width="stretch", hide_index=True,
                )
            plt.close(fig7)

    if not _esweep_path.exists() and not _tsweep_path.exists() and not _single_run.exists():
        _csweep_path = result_path / "composition_sweep_summary.csv"
        if _csweep_path.exists():
            df_c = pd.read_csv(_csweep_path).sort_values("compound_fraction")
            compound_name = str(df_c["compound"].iloc[0]) if "compound" in df_c.columns else "compound"
            Xc = df_c["compound_fraction"].to_numpy(dtype=float)
            Tc = df_c["transmission_fraction"].to_numpy(dtype=float)
            mu_c = df_c["linear_attenuation_cm_inv"].to_numpy(dtype=float)
            Tc_std = df_c.get("transmission_fraction_std", pd.Series(np.full(len(Xc), np.nan))).to_numpy(dtype=float)
            mu_c_std = df_c.get("linear_attenuation_std_cm_inv", pd.Series(np.full(len(Xc), np.nan))).to_numpy(dtype=float)
            hvl_c = df_c.get("hvl_cm", pd.Series(np.full(len(Xc), np.nan))).to_numpy(dtype=float)
            tvl_c = df_c.get("tvl_cm", pd.Series(np.full(len(Xc), np.nan))).to_numpy(dtype=float)

            st.subheader(f"Composition Sweep - {compound_name}")
            if np.isfinite(Tc_std).any() or np.isfinite(mu_c_std).any():
                c_u1, c_u2 = st.columns(2)
                with c_u1:
                    if np.isfinite(Tc_std).any():
                        st.metric("Median T std. err. (composition)", f"{np.nanmedian(Tc_std):.4g}")
                with c_u2:
                    if np.isfinite(mu_c_std).any():
                        st.metric("Median μ std. err. (composition)", f"{np.nanmedian(mu_c_std):.4g} cm⁻¹")

            fig_c1, axes_c = plt.subplots(1, 2, figsize=(
                plt.rcParams["figure.figsize"][0] * 2.2,
                plt.rcParams["figure.figsize"][1],
            ))
            ax_c1, ax_c2 = axes_c

            if np.isfinite(Tc_std).any():
                ax_c1.errorbar(Xc * 100, Tc, yerr=Tc_std, fmt="o-", color=BLUE, lw=1.5, ms=4,
                               capsize=2, label=r"$T$ (MC)")
            else:
                ax_c1.plot(Xc * 100, Tc, "o-", color=BLUE, lw=1.5, ms=4,
                           label=r"$T$ (MC)")
            ax_c1r = ax_c1.twinx()
            if np.isfinite(mu_c_std).any():
                ax_c1r.errorbar(Xc * 100, mu_c, yerr=mu_c_std, fmt="s--", color=ORNG, lw=1.2, ms=3.5,
                                capsize=2, label=r"$\mu$ (cm$^{-1}$)")
            else:
                ax_c1r.plot(Xc * 100, mu_c, "s--", color=ORNG, lw=1.2, ms=3.5,
                            label=r"$\mu$ (cm$^{-1}$)")
            ax_c1.set_xlabel(f"Weight fraction of {compound_name} (%)")
            ax_c1.set_ylabel("Transmission $T$", color=BLUE)
            ax_c1r.set_ylabel(r"$\mu$ (cm$^{-1}$)", color=ORNG)
            ax_c1.tick_params(axis="y", colors=BLUE)
            ax_c1r.tick_params(axis="y", colors=ORNG)
            lns_c = ax_c1.get_lines() + ax_c1r.get_lines()
            ax_c1.legend(lns_c, [l.get_label() for l in lns_c], loc="best")
            ax_c1.set_title("Transmission & Attenuation vs Composition")
            ax_c1.grid(True, ls=":", alpha=0.35)

            if not np.all(np.isnan(hvl_c)):
                ax_c2.semilogy(Xc * 100, hvl_c, "o-", color=BLUE, lw=1.5, ms=4, label="HVL")
                ax_c2.semilogy(Xc * 100, tvl_c, "s--", color=ORNG, lw=1.5, ms=4, label="TVL")
                ax_c2.set_xlabel(f"Weight fraction of {compound_name} (%)")
                ax_c2.set_ylabel("Thickness (cm)")
                ax_c2.set_title("HVL & TVL vs Composition")
                ax_c2.legend()
                ax_c2.grid(True, which="both", ls=":", alpha=0.35)

            fig_c1.suptitle(f"Composition Sweep - {selected_name}", fontweight="bold")
            finish_shieldlab_figure(fig_c1)
            col_c1, col_c2 = st.columns([4, 1])
            with col_c1:
                st.pyplot(fig_c1, width="stretch")
            with col_c2:
                st.markdown("**Export**")
                _export_buttons(fig_c1, f"{selected_name}_composition_sweep", "fig_cs")
            plt.close(fig_c1)

            if np.isfinite(Tc_std).any() or np.isfinite(mu_c_std).any():
                st.markdown("**Composition sweep uncertainty summary**")
                uncertainty_cols_c = ["compound", "compound_fraction", "transmission_fraction"]
                for column in [
                    "transmission_fraction_std",
                    "transmission_fraction_ci95_half_width",
                    "linear_attenuation_cm_inv",
                    "linear_attenuation_std_cm_inv",
                    "mass_attenuation_cm2_g",
                    "mass_attenuation_std_cm2_g",
                ]:
                    if column in df_c.columns:
                        uncertainty_cols_c.append(column)
                st.dataframe(df_c[uncertainty_cols_c].round(6), width="stretch", hide_index=True)
                st.caption("Composition-sweep uncertainty follows the same binomial-count and delta-method propagation used for the energy sweep.")
        else:
            st.info("No simulation CSV results found in this folder. Run a study first.")

# TAB 2 - Layer Physics: energy deposition per layer
with tab_layer:
    render_panel_header(
        "Layer Physics",
        "Per-layer attenuation and transport summaries resolved from the selected result set.",
        controls=["Layer Table", "Physics", "Export"],
    )
    apply_journal_style(journal_preset)

    BLUE  = OKABE_ITO[0]
    ORNG  = OKABE_ITO[1]
    GREEN = OKABE_ITO[2]
    RED   = OKABE_ITO[3]

    layer_files = sorted(result_path.glob("**/layer_energy_deposition.csv"))
    if not layer_files:
        st.info("No layer_energy_deposition.csv found in this result set.")
    else:
        for lf in layer_files:
            df_l = pd.read_csv(lf)
            if df_l.empty:
                continue
            folder_tag = lf.parent.name if lf.parent != result_path else selected_name
            st.markdown(f"**Run:** `{folder_tag}`")

            # Figure: horizontal bar chart - Edep per layer per event
            labels_l = [
                f"L{int(r['layer'])}: {r['material']}\n({r['thickness_cm']:.2f} cm, {r.get('density_g_cm3', 0):.3f} g/cm³)"
                for _, r in df_l.iterrows()
            ]
            edep_ev = df_l["edep_MeV_per_event"].to_numpy(dtype=float)
            edep_tot = df_l["edep_MeV_total"].to_numpy(dtype=float)

            n_lay = len(df_l)
            fig_l, axes_l = plt.subplots(1, 2, figsize=(
                plt.rcParams["figure.figsize"][0] * 2.2,
                max(2.0, 0.45 * n_lay + 1.2),
            ))
            ax_la, ax_lb = axes_l

            y_pos = np.arange(n_lay)
            ax_la.barh(y_pos, edep_ev, color=BLUE, alpha=0.85, edgecolor="white", lw=0.5)
            ax_la.set_yticks(y_pos)
            ax_la.set_yticklabels(labels_l)
            ax_la.set_xlabel(r"Energy Deposition per Event (MeV event$^{-1}$)")
            ax_la.set_title("Edep per Primary Event")
            ax_la.grid(True, axis="x", ls=":", alpha=0.4)
            ax_la.invert_yaxis()

            ax_lb.barh(y_pos, edep_tot, color=GREEN, alpha=0.85, edgecolor="white", lw=0.5)
            ax_lb.set_yticks(y_pos)
            ax_lb.set_yticklabels(labels_l)
            ax_lb.set_xlabel("Total Energy Deposition (MeV)")
            ax_lb.set_title("Total Edep (Full Run)")
            ax_lb.grid(True, axis="x", ls=":", alpha=0.4)
            ax_lb.invert_yaxis()

            fig_l.suptitle(f"Layer Energy Deposition - {folder_tag}", fontweight="bold")
            finish_shieldlab_figure(fig_l)
            st.pyplot(fig_l, width="stretch")
            _export_buttons(fig_l, f"{folder_tag}_layer_edep", f"led_{folder_tag}")
            plt.close(fig_l)

            st.dataframe(df_l.round(6), width="stretch", hide_index=True)
            st.markdown("---")

# TAB 3 - Secondary Particle Tally
with tab_sec:
    render_panel_header(
        "Secondaries",
        "Secondary particle production and transport tallies extracted from run artifacts.",
        controls=["Tallies", "Flux", "CSV"],
    )
    apply_journal_style(journal_preset)

    BLUE  = OKABE_ITO[0]
    ORNG  = OKABE_ITO[1]
    GREEN = OKABE_ITO[2]
    RED   = OKABE_ITO[3]
    PURP  = OKABE_ITO[4]
    SKY   = OKABE_ITO[5]

    sec_tally_files = sorted(result_path.glob("**/secondary_tally.csv"))
    if not sec_tally_files:
        st.info(str(copy["secondary_tally_missing"]))
        st.caption("Rebuild the Geant4 binary with the secondary-tally update, then re-run the study.")
    else:
        st.subheader(str(copy["secondary_tally_heading"]))
        st.caption(str(copy["secondary_tally_caption"]))
        for sec_file in sec_tally_files:
            df_sec = pd.read_csv(sec_file)
            if df_sec.empty:
                continue
            folder_tag = sec_file.parent.name if sec_file.parent != result_path else selected_name
            st.markdown(f"**Run:** `{folder_tag}`")
            n_sp = len(df_sec)

            # Sort by count desc (should already be sorted but enforce it)
            df_sec = df_sec.sort_values("count", ascending=False).reset_index(drop=True)
            species = df_sec["particle_name"].tolist()
            counts = df_sec["count"].to_numpy(dtype=float)
            mean_ke = df_sec.get("mean_kinetic_energy_MeV",
                                  pd.Series(np.zeros(n_sp))).to_numpy(dtype=float)
            cpe = df_sec.get("count_per_primary_event",
                              pd.Series(np.zeros(n_sp))).to_numpy(dtype=float)

            palette = (OKABE_ITO * math.ceil(n_sp / len(OKABE_ITO)))[:n_sp]
            y_pos = np.arange(n_sp)

            # Figure: 2-panel - count bar + mean KE bar
            fig_s, axes_s = plt.subplots(
                1, 2,
                figsize=(plt.rcParams["figure.figsize"][0] * 2.2,
                         max(2.2, 0.45 * n_sp + 1.2)),
            )
            ax_s1, ax_s2 = axes_s

            ax_s1.barh(y_pos, counts, color=palette, edgecolor="white", lw=0.5)
            ax_s1.set_yticks(y_pos)
            ax_s1.set_yticklabels(species)
            ax_s1.set_xlabel("Secondary Count (downstream face)")
            ax_s1.set_title("Secondary Particle Count")
            ax_s1.grid(True, axis="x", ls=":", alpha=0.4)
            ax_s1.invert_yaxis()
            # Annotate with count/primary
            for i, (cnt, cp) in enumerate(zip(counts, cpe)):
                ax_s1.text(cnt * 1.01, i, f" {cp:.3f}/ev", va="center",
                           fontsize=max(5, plt.rcParams.get("font.size", 7) - 1))

            ax_s2.barh(y_pos, mean_ke, color=palette, edgecolor="white", lw=0.5, alpha=0.85)
            ax_s2.set_yticks(y_pos)
            ax_s2.set_yticklabels(species)
            ax_s2.set_xlabel(r"Mean Kinetic Energy $\langle E_k \rangle$ (MeV)")
            ax_s2.set_title("Mean KE of Secondaries")
            ax_s2.grid(True, axis="x", ls=":", alpha=0.4)
            ax_s2.invert_yaxis()

            fig_s.suptitle(f"Secondary Particle Tally - {folder_tag}", fontweight="bold")
            finish_shieldlab_figure(fig_s)
            col_s1, col_s2 = st.columns([5, 1])
            with col_s1:
                st.pyplot(fig_s, width="stretch")
            with col_s2:
                st.markdown("**Export**")
                _export_buttons(fig_s, f"{folder_tag}_secondaries", f"sec_{folder_tag}")
            plt.close(fig_s)

            # Tabular summary
            top = df_sec.iloc[0]
            st.caption(
                f"Dominant secondary: **{top['particle_name']}** - "
                f"{int(top['count']):,} particles "
                f"({float(cpe[0]):.4f}/primary), "
                f"mean KE = {float(mean_ke[0]):.4f} MeV"
            )
            st.dataframe(
                df_sec.style.background_gradient(subset=["count"], cmap="Blues"),
                width="stretch", hide_index=True,
            )
            st.markdown("---")

# TAB 4 - Stored Figures (PNG files produced by G4 viz module)
with tab_figs:
    render_panel_header(
        "Stored Figures",
        "Archived figure pack associated with the selected simulation output.",
        controls=["Preview", "Metadata", "Download"],
    )
    fig_dir = result_path / "figures"
    pngs = sorted(fig_dir.glob("*.png")) if fig_dir.exists() else []

    if not pngs:
        st.info(str(copy["no_figures"]))
    else:
        st.caption(f"{len(pngs)} figure(s) in `figures/` directory.")
        fig_style = st.radio("Layout", ["2-column", "1-column (large)"], horizontal=True)
        n_cols = 2 if fig_style == "2-column" else 1
        row_chunks = [pngs[i : i + n_cols] for i in range(0, len(pngs), n_cols)]
        for row_chunk in row_chunks:
            cols = st.columns(n_cols)
            for j, p in enumerate(row_chunk):
                with cols[j]:
                    try:
                        from PIL import Image
                        st.image(Image.open(str(p)), width="stretch")
                    except Exception:
                        st.image(str(p), width="stretch")
                    c_cap, c_dl = st.columns([3, 1])
                    c_cap.caption(p.stem.replace("_", " ").title())
                    c_dl.download_button(
                        "Download", p.read_bytes(), file_name=p.name,
                        mime="image/png", key=f"png_dl_{p.stem}",
                    )

# TAB 5 - Numerical Data tables
with tab_data:
    render_panel_header(
        "Numerical Data",
        "Structured numeric outputs including sweep tables and derived coefficients.",
        controls=["Table", "Filter", "Export"],
    )
    # Sweep summaries in priority order
    sweep_csvs = [
        ("composition_sweep_summary.csv", "Composition Sweep"),
        ("thickness_sweep_summary.csv", "Thickness Sweep"),
        ("sweep_summary.csv", "Energy Sweep"),
    ]
    found_sweep = False
    for csv_name, label in sweep_csvs:
        csv_path = result_path / csv_name
        if csv_path.exists():
            st.markdown(f"**{label}** - `{csv_name}`")
            df_sw = pd.read_csv(csv_path)
            st.dataframe(df_sw.round(6), width="stretch", hide_index=True)
            found_sweep = True

    run_summaries = sorted(result_path.glob("**/run_summary.csv"))
    if run_summaries:
        with st.expander(f"Per-Run Summaries ({len(run_summaries)} found)", expanded=not found_sweep):
            all_runs = pd.concat(
                [pd.read_csv(f).assign(folder=f.parent.name) for f in run_summaries],
                ignore_index=True,
            )
            st.dataframe(all_runs, width="stretch", hide_index=True)

    layer_files_dt = sorted(result_path.glob("**/layer_energy_deposition.csv"))
    if layer_files_dt:
        with st.expander(f"Layer Energy Deposition ({len(layer_files_dt)} file(s))"):
            all_l = pd.concat(
                [pd.read_csv(f).assign(folder=f.parent.name) for f in layer_files_dt],
                ignore_index=True,
            )
            st.dataframe(all_l, width="stretch", hide_index=True)

    if not found_sweep and not run_summaries:
        st.info(str(copy["no_csv"]))

# TAB 6 - Descriptors
with tab_desc:
    render_panel_header(
        "Descriptors",
        "Material descriptors, composition metadata, and derived shielding indicators.",
        controls=["Descriptors", "Elements", "Summary"],
    )
    study_file_path = val_data.get("study_file")
    if not study_file_path:
        st.info(str(copy["no_study_reference"]))
    else:
        sp = Path(study_file_path)
        if not sp.exists():
            st.warning(str(copy["missing_study_file"]).format(path=sp))
        else:
            try:
                study_obj = json.loads(sp.read_text(encoding="utf-8"))
                if not study_obj.get("materials"):
                    st.info(str(copy["built_in_materials"]))
                else:
                    from shieldlab.core.descriptors import (
                        descriptors_from_study,
                        elemental_expansion_table,
                    )
                    st.markdown("**Material Descriptors**")
                    st.caption(
                        "Molar mass, average Z, Z_eff (n=3.5), N_eff, and electron density "
                        "computed from the elemental mass fractions."
                    )
                    desc_df = descriptors_from_study(study_obj)
                    st.dataframe(desc_df.round(4), width="stretch", hide_index=True)
                    st.markdown("**Elemental Expansion**")
                    elem_df = elemental_expansion_table(study_obj)
                    st.dataframe(elem_df.round(6), width="stretch", hide_index=True)
            except Exception as exc:
                st.error(str(copy["descriptors_error"]).format(error=exc))

# TAB 7 - Download
with tab_dl:
    render_panel_header(
        "Download",
        "Consolidated result delivery: figures, tables, and packaged run artifacts.",
        controls=["Artifacts", "CSV", "Workbook"],
    )
    xlsx_path = result_path / "shieldlab_results.xlsx"
    if xlsx_path.exists():
        with open(str(xlsx_path), "rb") as fh:
            xlsx_bytes = fh.read()
        st.download_button(
            label=str(copy["download_excel_label"]),
            data=xlsx_bytes,
            file_name=f"{selected_name}_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.caption(
            f"**{len(xlsx_bytes) / 1024:.0f} KB** ? sheets: Study Info, Run Summary, "
            "Layer Edep, Derived Coefficients, Material Descriptors, Elemental Expansion, "
            "Energy/Thickness/Composition Sweeps, Reference Coefficients, Reference Comparison, Figures Index."
        )
    else:
        st.warning(str(copy["excel_missing"]))

    if val_file.exists():
        st.markdown("---")
        st.download_button(
            label=str(copy["download_validation_label"]),
            data=val_file.read_bytes(),
            file_name=f"{selected_name}_validation.json",
            mime="application/json",
        )

    st.markdown("---")
    st.markdown(f"**{copy['csv_section_label']}**")
    all_csvs = list(result_path.glob("*.csv")) + list(result_path.glob("**/run_summary.csv"))
    unique_csvs = {p.name: p for p in all_csvs}
    if unique_csvs:
        for fname, fpath in sorted(unique_csvs.items()):
            try:
                st.download_button(
                    label=f"Download {fname}",
                    data=fpath.read_bytes(),
                    file_name=fname,
                    mime="text/csv",
                    key=f"dl_{fname}",
                )
            except Exception:
                _log.debug("Could not render download button for %s", fname, exc_info=True)
    else:
        st.info("No CSV files found in this result set.")




