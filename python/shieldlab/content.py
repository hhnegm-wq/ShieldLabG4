"""Centralized user-facing page copy for ShieldLab G4."""
from __future__ import annotations

from shieldlab.metadata import (
    HOME_HERO_BODY,
    HOME_HERO_KICKER,
    LEGAL_DISCLAIMER,
    PLATFORM_SCOPE,
    PRODUCT_NAME,
    PRODUCT_SUBTITLE,
    PRODUCT_TAGLINE,
)

PAGE_COPY: dict[str, dict[str, object]] = {
    "common": {
        "upgrade_url": "https://shieldlab-g4.io/pricing",
        "pro_gate_message": "🔒 **{feature_label}** is a Pro feature. [Upgrade to Pro]({upgrade_url}) to unlock this.",
        "locked_download_help": "{feature_label} — upgrade to Pro to unlock.",
    },
    "home": {
        "title": f"⚛️ {PRODUCT_NAME}",
        "hero_kicker": HOME_HERO_KICKER,
        "hero_body": HOME_HERO_BODY,
        "section_blurb": PLATFORM_SCOPE,
        "disclaimer": LEGAL_DISCLAIMER,
        "features_heading": "Platform Capabilities",
        "workflow_heading": "Workflow",
        "features": [
            (
                "📊",
                "Shielding Calculator",
                "MAC, HVL, TVL, LAC, and transmission across photon and neutron shielding workflows with export-ready figures.",
            ),
            (
                "⚖️",
                "Material Comparison",
                "Side-by-side comparison of candidate shielding materials with ranked tables and overlay plots.",
            ),
            (
                "☢️",
                "Dose-Rate Calculator",
                "Point, line, and disk source dose-rate estimation using isotope data, attenuation, and distance-law models.",
            ),
            (
                "📐",
                "Methods & References",
                "Reference-traceable equations, standards, and validation summaries for each scientific module.",
            ),
        ],
        "workflow_steps": [
            (
                "🔬",
                "1 · Build",
                "Open Study Builder to define materials, configure the scenario, validate the JSON, and save the study package.",
            ),
            (
                "▶️",
                "2 · Run",
                "Open Run Study to execute the Geant4 workflow and collect result artifacts automatically.",
            ),
            (
                "📊",
                "3 · Analyse",
                "Use Results Explorer and the analytical tools to inspect figures, tables, descriptors, and reports.",
            ),
        ],
    },
    "shielding_calculator": {
        "title": "📊 Shielding Calculator",
        "caption": "All-in-one analytical shielding workflow covering XCOM, Phy-X, EpiXS dose, and NGCal neutron removal.",
        "data_source": "Data source: NIST XrayMassCoef and XCOM databases, GP buildup factors (ANSI/ANS-6.4.3), and Shultis & Faw neutron removal data.",
        "mobile_warning": "ShieldLab G4 is optimised for desktop (≥ 800 px). Tables and polar plots may be clipped on narrow screens.",
        "material_blurb": "Enter the shield material using any supported composition mode or load it from the compendium.",
        # Section expander headings
        "section_material": "⚗️  1 · Material Definition",
        "section_source": "☢️  2 · Radiation Source",
        "section_shield": "🧱  3 · Shield Configuration",
        "section_compendium": "📚 Load from NIST COMPENDIUM",
        # Neutron mode
        "neutron_warning": (
            "**Neutron mode**: Standard photon MAC parameters do not apply. "
            "The calculator will compute Fast Neutron Removal Cross Section (FNRCS/NGCal) "
            "and neutron HVL/TVL instead."
        ),
        "neutron_subheader": "🔆 Fast Neutron Removal (NGCal)",
        "neutron_element_subheader": "Per-Element FNRCS Contributions",
        # Calculate button area
        "calc_button": "🔬 Calculate",
        "calc_not_ready": "Define a valid material and energy range above, then click Calculate.",
        "calc_ready_msg": "Ready — {mat_name}  |  density {density:.3f} g/cm³  |  {energy_display}",
        "session_restored": "✅ Session restored — results displayed below.",
        # Results section
        "results_heading": "Results — **{name}** (ρ = {rho:.4f} g/cm³)  ·  {e_display}",
        # Tab labels
        "tab_phyx": "📊 Phy-X Parameters",
        "tab_xcom": "🔬 XCOM Cross Sections",
        "tab_descriptors": "⚛️ Material Descriptors",
        "tab_transmission": "📉 Transmission vs Thickness",
        "tab_plots": "📈 Plots",
        "tab_multilayer": "🧱 Multi-Layer",
        "tab_estar": "⚡ ESTAR (e⁻ β)",
        "tab_ion": "☢️ Ion Range (SRIM)",
        "tab_klein_nishina": "🔵 Klein-Nishina",
        "tab_inverse": "🎯 Inverse Design",
        "tab_export": "💾 Export",
        # Tab 1 — Phy-X
        "phyx_subheader": "Photon Shielding Parameters (Phy-X style)",
        "phyx_caption": (
            "MAC = mass attenuation coefficient · LAC = linear attenuation coefficient · "
            "HVL = half value layer · TVL = tenth value layer · "
            "MFP = mean free path · T = transmission · RPE = radiation protection efficiency · "
            "EBF = exposure buildup factor"
        ),
        "phyx_extended_expander": "🔬 Extended Phy-X parameters — Zeff(E), Neff(E), Ceff(E), ACS, ECS, R",
        "phyx_extended_caption": (
            "**Zeff(E)** = MAC-weighted effective Z (Phy-X — energy-dependent) · "
            "**Neff(E)** = Zeff × Nₐ/M_eff [el/g] · "
            "**Ceff(E)** = Neff/Nₐ × 10⁹ [S/m] · "
            "**ACS(E)** = MAC × M_eff/Nₐ [cm²/atom] · "
            "**ECS(E)** = ACS/Zeff [cm²/electron] · "
            "**R(E)** = μ_Compton/μ_total (from NIST XCOM)"
        ),
        # Tab 2 — XCOM
        "xcom_subheader": "Photon Cross-Section Components (XCOM style)",
        "xcom_caption": (
            "Separate components: coherent scattering, Compton (incoherent), "
            "photoelectric absorption, pair production (nuclear + electron field)"
        ),
        "xcom_fetch_button": "📡 Fetch Full XCOM Data from NIST",
        "xcom_fetch_spinner": "Fetching XCOM 7-component data from NIST…",
        "xcom_zeq_caption": (
            "Zeq is found by log-log interpolation between 24 reference elements (Z=1–82) "
            "that bracket the compound's R = Compton/total ratio. "
            "⚠️ First run fetches XCOM data for each reference element (cached afterwards)."
        ),
        "xcom_zeq_button": "⚙️ Compute Zeq",
        "xcom_zeq_spinner": "Computing Zeq — fetching reference XCOM data (first time may take ~30 s)…",
        # Multi-layer
        "multilayer_stack_label": "**Multi-Layer Stack** (for multilayer calculations)",
        # Calc spinner / errors
        "calc_spinner": "Fetching NIST MAC data and computing shielding parameters…",
        # Tab subheaders (remaining tabs)
        "tab_desc_subheader": "Material Descriptors (Phy-X / XCOM)",
        "tab_trans_subheader": "Transmission vs Thickness",
        "tab_plots_subheader": "Shielding Parameter Plots",
        "tab_multi_subheader": "Multi-Layer Shielding (composite shield)",
        "tab_estar_subheader": "ESTAR – Electron Stopping Power & CSDA Range",
        "tab_ion_subheader": "Ion Stopping Power & Range (SRIM-style)",
        "tab_kn_subheader": "Klein-Nishina Compton Scattering",
    },
    "comparison": {
        "title": "⚖️ Multi-Material Comparison",
        "caption": "Compare shielding materials side-by-side across the key photon and neutron shielding parameters.",
        "free_warning": "Multi-material comparison is a Pro feature. Free users may preview the workflow with 2 materials and watermarked exports; Pro unlocks up to 8 materials and full export formats.",
    },
    "dose_rate": {
        "title": "Dose-Rate Calculator",
        "caption": "Point, line, and disk source geometries with ICRP-74 H*(10) ambient dose equivalent and optional shield attenuation.",
        "source_header": "Source Configuration",
        "gamma_k_missing": "Gamma_k is not available in the current source library for this isotope or custom source.",
        "shield_data_warning": "Could not retrieve XCOM data for shield material — shielding disabled.",
        "icrp_caption": "ICRP Publication 74 fluence-to-ambient-dose-equivalent coefficients h*(10), AP geometry.",
    },
    "results_explorer": {
        "title": "📊 Results Explorer",
        "caption": "Browse simulation outputs, sweep tables, descriptors, figures, and Excel reports from completed runs.",
        "folder_label": "Result folder",
        "folder_help": "Sorted by most recent first.",
        "missing_dir": "Results directory not found. Run a study first.",
        "empty_dir": "No result folders found. Go to Run Study to execute your first simulation.",
        "no_figures": "No figures found. The study may have been run without plots, or the result folder has no figure artifacts.",
        "no_csv": "No CSV data files found in this result folder.",
        "no_study_reference": "No study file reference in validation summary.",
        "missing_study_file": "Study file not found at: {path}",
        "built_in_materials": "This study uses built-in G4 NIST materials — no custom material descriptors available.",
        "descriptors_error": "Could not load descriptors: {error}",
        "excel_missing": "No Excel report found. Re-run the study to generate one.",
        "download_excel_label": "⬇️  Download Excel Report (.xlsx)",
        "download_validation_label": "⬇️  Download Validation Summary (.json)",
        "csv_section_label": "Individual CSVs",
        "secondary_tally_heading": "☢️ Secondary Particle Tally",
        "secondary_tally_caption": "Secondaries detected at the downstream face of the shield — derived from `secondary_tally.csv` written by Geant4.",
        "secondary_tally_missing": "No `secondary_tally.csv` found. Rebuild and re-run with the updated Geant4 binary.",
        "secondary_tally_expander": "Secondary Particle Tally ({n} particle species)",
    },
    "literature_benchmarks": {
        "title": "📚 Literature Benchmarks",
        "caption": "Curated paper-derived benchmark studies, coverage diagnostics, and runnable templates that connect the PDF library to executable ShieldLab G4 studies.",
        "hero_kicker": "Benchmark Registry",
        "hero_title": "📚 Literature Benchmarks",
        "hero_body": "Turn the paper library into executable validation campaigns — track high-value shielding papers, mark which benchmarks are runnable today, and expose the exact study templates used to reproduce paper-grade attenuation workflows in the Geant4 stack.",
        "method_note": "Readiness levels separate exact paper-backed benchmarks from provisional studies that still need one missing table value such as a measured density.",
    },
    "study_builder": {
        "title": "🔬 Study Builder",
        "caption": "Design materials, configure the beam and geometry, validate the study JSON, and prepare the run package.",
        "material_blurb": "Define a shield material in any supported composition format, preview the descriptors, then add it to the study JSON.",
    },
    "run_study": {
        "title": "▶️ Run Study",
        "caption": "Execute a Geant4 simulation workflow and collect result artifacts automatically.",
        "selector_heading": "Select Study",
        "selectbox_label": "From studies directory",
        "upload_label": "Or upload a JSON file",
        "study_info_heading": "Study Info",
        "study_read_error": "Could not read study file: {error}",
        "layers_label": "Layers:",
        "run_config_heading": "⚙️ Run Configuration",
        "build_dir_label": "Build directory",
        "skip_geant4_label": "Skip Geant4 (reuse existing CSVs)",
        "skip_geant4_help": "Re-runs only collection, Excel, and plots — useful for re-processing outputs.",
        "skip_plots_label": "Skip plot generation",
        "validation_heading": "Validation",
        "select_study_info": "Select a study above to proceed.",
        "validate_button": "🔍 Validate",
        "validation_errors": "❌ {errors} error(s), {warnings} warning(s) — fix before running.",
        "validation_warnings": "⚠️ {warnings} warning(s) — safe to run.",
        "validation_success": "✅ No issues found.",
        "execute_heading": "Execute",
        "run_button": "▶️  Run Simulation",
        "live_output_label": "Live Output",
        "launch_error": "Failed to launch process: {error}",
        "success_message": "✅ Simulation completed successfully!",
        "result_saved_message": "Results saved to: `{result_dir}` — open **📊 Results Explorer** for full analysis.",
        "failure_message": "❌ Simulation failed (exit code {code}). Check the output above for details.",
    },
    "methods": {
        "title": "📐 Methods & Physical Models",
        "caption": "ShieldLab G4 applies analytical radiation-transport models validated against NIST, ICRU, ICRP, and ANSI/ANS standards.",
        "quick_reference": "Quick Reference Map",
    },
    "about": {
        "title": "🏛️ About & Legal",
        "caption": f"{PRODUCT_NAME} · {PRODUCT_TAGLINE}",
        "ownership_text": "Scientific ownership, platform stewardship, and rights management are held by Dr. Hani H. Negm.",
        "operational_position": [
            "Research and educational use are first-class platform targets.",
            "Engineering screening and pre-assessment workflows are supported.",
            "Independent verification is still required before clinical, regulatory, or safety-critical use.",
            "Traceability is maintained through versioned exports, methods documentation, and validation reports.",
        ],
        "governance_notes": [
            "Product identity, ownership, and support metadata are centralized in shieldlab.metadata.",
            "Shared page copy is managed through shieldlab.content.",
            "Shared legal footer text is rendered at the platform shell level.",
            "Exported figures inherit reproducibility and ownership markings through the shared visualization layer.",
        ],
        "citation_policy_title": "Citation & Export Policy",
        "citation_policy_intro": "Use the software name, version, owner, and export provenance when citing ShieldLab G4 in papers, reports, or regulatory-support documentation.",
        "citation_policy_points": [
            "Cite the software as ShieldLab G4 with the version shown on this page and the owning author Dr. Hani H. Negm.",
            "Retain the reproducibility footer on exported figures when submitting drafts or circulating technical reviews.",
            "State that analytical outputs should be independently verified before clinical, regulatory, or safety-critical use.",
            "Prefer exporting journal figures together with the methods page and validation summary when publication traceability matters.",
        ],
        "platform_scope_text": "ShieldLab G4 integrates study configuration, run orchestration, analytical shielding, dose-rate estimation, results exploration, methods documentation, and reproducible reporting into a single managed workspace.",
        "citation_example": "ShieldLab G4 v{version}, Dr. Hani H. Negm, validated radiation shielding workspace for analytical shielding, dose-rate estimation, and reproducible reporting.",
    },
    "settings": {
        "title": "⚙️ Platform Settings",
        "caption": "Control typography, layout density, shell presentation, and other global session settings.",
        "hero_kicker": "Platform Configuration",
        "hero_title": "⚙️ Platform Settings",
        "hero_body": "Control the whole platform experience — adjust typography, layout density, content width, and shell-level presentation that apply across browser sessions for the current user profile.",
        "preset_label": "Theme preset",
        "preset_labels": {
            "default": "Default",
            "presentation": "Presentation",
            "compact_lab": "Compact Lab",
            "accessibility_large_text": "Accessibility Large Text",
            "custom": "Custom",
        },
        "preset_apply_label": "Apply Preset",
        "custom_preset_info": "Custom reflects the current manual combination of settings. Choose a named preset to apply a stored profile.",
        "preset_applied_message": "Applied preset: {preset}.",
        "font_size_label": "Font size",
        "content_density_label": "Content density",
        "content_width_label": "Content width",
        "show_hero_sections_label": "Show hero sections",
        "show_platform_footer_label": "Show platform footer",
        "apply_label": "Apply Settings",
        "reset_label": "Reset Defaults",
        "updated_message": "Platform settings updated and saved for future browser sessions.",
        "reset_message": "Platform settings restored to defaults.",
        "active_preset_metric": "Preset",
        "font_metric": "Font",
        "density_metric": "Density",
        "width_metric": "Width",
        "hero_metric": "Hero",
        "footer_metric": "Footer",
        "on_label": "On",
        "off_label": "Off",
        "session_note": "These controls are saved to a local user profile and apply across the platform shell after rerun.",
        # System & Paths admin section
        "system_paths_heading": "🖥️ System & Paths",
        "system_paths_expander": "System Configuration & Runtime Paths",
        "system_paths_caption": "Runtime paths and environment configuration resolved at startup. Environment variables override defaults.",
        "path_project_root": "Project Root",
        "path_python_lib": "Python Library",
        "path_python_exe": "Python Executable",
        "path_build_dir": "Build Directory",
        "path_studies_dir": "Studies Directory",
        "path_results_dir": "Results Directory",
        "path_geant4_binary": "Geant4 Binary",
        "path_exists": "✓ exists",
        "path_missing": "✗ not found",
        "env_var_override_note": "Set `SHIELDLAB_PROJECT_ROOT`, `SHIELDLAB_PYTHONPATH`, `SHIELDLAB_BUILD_DIR`, `SHIELDLAB_STUDIES_DIR`, `SHIELDLAB_PYTHON_EXE` environment variables to override defaults.",
        "geant4_binary_name": "ShieldLabG4",
    },
}