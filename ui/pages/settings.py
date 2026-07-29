"""Platform settings page for shared UI preferences."""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_UI_DIR = Path(__file__).resolve().parent.parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from bootstrap import ensure_project_paths  # noqa: E402

ensure_project_paths()

import config  # noqa: E402
from shieldlab.content import PAGE_COPY
from components.platform_capabilities import PLATFORM_CAPABILITIES
from components.platform_settings import (
    apply_platform_preset,
    get_platform_settings,
    reset_platform_settings,
    update_platform_settings,
)
from components.layout import render_page_hero
from components.enterprise_ui import (
    render_breadcrumb as _render_breadcrumb_settings,
    render_path_table,
    render_platform_capability_grid,
    render_status_bar,
)
from auth import get_user_context

copy = PAGE_COPY["settings"]
settings = get_platform_settings()

hero_kicker = str(copy.get("hero_kicker", "Platform Settings"))
hero_title = str(copy.get("hero_title", "Control the whole platform experience"))
hero_body = str(
    copy.get(
        "hero_body",
        "Adjust font size, layout density, content width, and shell-level presentation settings that apply across browser sessions for the current user profile.",
    )
)

render_page_hero(hero_title, hero_body, hero_kicker)
_render_breadcrumb_settings(["ShieldLab G4", "Platform"], current="Settings")
st.caption(str(copy["caption"]))

_user_ctx = get_user_context()

st.divider()
st.subheader("Account")
st.caption("Current signed-in account, capability tier, and hosted-auth provider state.")
render_status_bar([
    {"label": "Provider", "value": _user_ctx.provider, "state": "ok" if _user_ctx.provider != "local" else "neutral"},
    {"label": "Role", "value": _user_ctx.role, "state": "ok" if _user_ctx.role in {"operator", "admin"} else "neutral"},
    {"label": "Tier", "value": _user_ctx.tier.upper(), "state": "ok" if _user_ctx.tier == "pro" else "neutral"},
    {"label": "Email", "value": _user_ctx.email or "not signed in", "state": "neutral"},
])

preset_labels = dict(
    copy.get(
        "preset_labels",
        {
            "default": "Default",
            "presentation": "Presentation",
            "compact_lab": "Compact Lab",
            "accessibility_large_text": "Accessibility Large Text",
            "custom": "Custom",
        },
    )
)
current_preset = str(settings.get("theme_preset", "default"))

with st.form("platform_preset_form"):
    selected_preset = st.selectbox(
        str(copy.get("preset_label", "Theme preset")),
        list(preset_labels.keys()),
        index=list(preset_labels.keys()).index(current_preset if current_preset in preset_labels else "custom"),
        format_func=lambda preset_key: preset_labels[preset_key],
    )
    preset_apply_clicked = st.form_submit_button(str(copy.get("preset_apply_label", "Apply Preset")), width="stretch")

if preset_apply_clicked:
    if selected_preset == "custom":
        st.info(str(copy.get("custom_preset_info", "Custom reflects the current manual combination of settings. Choose a named preset to apply a stored profile.")))
    else:
        apply_platform_preset(selected_preset)
        st.success(str(copy.get("preset_applied_message", "Applied preset: {preset}.")).format(preset=preset_labels[selected_preset]))
        st.rerun()

with st.form("platform_settings_form"):
    c1, c2 = st.columns(2)
    with c1:
        shell_mode = st.selectbox(
            "Shell mode",
            ["enterprise", "standard"],
            index=["enterprise", "standard"].index(str(settings.get("shell_mode", "enterprise"))),
            format_func=lambda mode: {
                "enterprise": "Enterprise Projection",
                "standard": "Standard Scientific",
            }.get(mode, mode),
            help="Enterprise Projection enables the premium dashboard shell, KPI strips, and panel headers.",
        )
        visual_theme = st.selectbox(
            "Visual theme",
            ["bright_lab", "dark_glass", "classic_blue"],
            index=["bright_lab", "dark_glass", "classic_blue"].index(str(settings.get("visual_theme", "bright_lab"))),
            format_func=lambda theme: {"bright_lab": "Bright Lab (ShieldLab Green)", "dark_glass": "Dark Glass", "classic_blue": "Classic Blue"}.get(theme, theme),
        )
        font_size = st.radio(
            str(copy.get("font_size_label", "Font size")),
            ["small", "medium", "large"],
            index=["small", "medium", "large"].index(str(settings["font_size"])),
            horizontal=True,
        )
        content_density = st.radio(
            str(copy.get("content_density_label", "Content density")),
            ["compact", "comfortable"],
            index=["compact", "comfortable"].index(str(settings["content_density"])),
            horizontal=True,
        )
    with c2:
        content_width = st.selectbox(
            str(copy.get("content_width_label", "Content width")),
            ["standard", "wide", "full"],
            index=["standard", "wide", "full"].index(str(settings["content_width"])),
        )
        show_hero_sections = st.checkbox(
            str(copy.get("show_hero_sections_label", "Show hero sections")),
            value=bool(settings["show_hero_sections"]),
        )
        show_platform_footer = st.checkbox(
            str(copy.get("show_platform_footer_label", "Show platform footer")),
            value=bool(settings["show_platform_footer"]),
        )

    c_apply, c_reset = st.columns(2)
    apply_clicked = c_apply.form_submit_button(str(copy.get("apply_label", "Apply Settings")), type="primary", width="stretch")
    reset_clicked = c_reset.form_submit_button(str(copy.get("reset_label", "Reset Defaults")), width="stretch")

if apply_clicked:
    update_platform_settings(
        shell_mode=shell_mode,
        visual_theme=visual_theme,
        font_size=font_size,
        content_density=content_density,
        content_width=content_width,
        show_hero_sections=show_hero_sections,
        show_platform_footer=show_platform_footer,
    )
    st.success(str(copy.get("updated_message", "Platform settings updated and saved for future browser sessions.")))
    st.rerun()

if reset_clicked:
    reset_platform_settings()
    st.success(str(copy.get("reset_message", "Platform settings restored to defaults.")))
    st.rerun()

current = get_platform_settings()
mc = st.columns(8)
_preset_abbr = {
    "default": "Def.", "presentation": "Pres.", "compact_lab": "Compact",
    "accessibility_large_text": "A11y", "custom": "Custom",
}
mc[0].metric(str(copy.get("active_preset_metric", "Preset")), _preset_abbr.get(str(current["theme_preset"]), str(current["theme_preset"]).title()))
mc[1].metric("Shell", "Ent." if str(current.get("shell_mode", "enterprise")) == "enterprise" else "Std.")
mc[2].metric("Theme", {"bright_lab": "Green", "dark_glass": "Dark", "classic_blue": "Blue"}.get(str(current.get("visual_theme", "bright_lab")), "Custom"))
mc[3].metric(str(copy.get("font_metric", "Font")), str(current["font_size"]).title())
mc[4].metric(str(copy.get("density_metric", "Density")), {"compact": "Compact", "comfortable": "Comfy"}.get(str(current["content_density"]), str(current["content_density"]).title()))
mc[5].metric(str(copy.get("width_metric", "Width")), {"standard": "Std.", "wide": "Wide", "full": "Full"}.get(str(current["content_width"]), str(current["content_width"]).title()))
mc[6].metric(str(copy.get("hero_metric", "Hero")), str(copy.get("on_label", "On")) if current["show_hero_sections"] else str(copy.get("off_label", "Off")))
mc[7].metric(str(copy.get("footer_metric", "Footer")), str(copy.get("on_label", "On")) if current["show_platform_footer"] else str(copy.get("off_label", "Off")))

# ── System Health ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("System Health")
st.caption("Live platform and session provenance status.")

import json as _json
from shieldlab import __version__ as _SHIELDLAB_VERSION

# Load validation report if available
_val_report_path = config.PROJECT_ROOT / "docs" / "validation" / "release_validation_report_latest.json"
_val_gate = "unavailable"
_val_generated_at = "—"
_val_study_count = "—"
_val_benchmark_pass = "—"
if _val_report_path.exists():
    try:
        _val_data = _json.loads(_val_report_path.read_text(encoding="utf-8"))
        _val_gate = str(_val_data.get("summary", {}).get("release_gate", "unavailable"))
        _val_generated_at = str(_val_data.get("generated_at_utc", "—"))[:10]
        _val_study_count = str(_val_data.get("summary", {}).get("study_count", "—"))
        _failed = _val_data.get("summary", {}).get("failed_benchmark_sets", "—")
        _val_benchmark_pass = "pass" if _failed == 0 else f"{_failed} failed"
    except Exception:
        import logging as _settings_log
        _settings_log.getLogger(__name__).warning(
            "Failed to parse validation report at %s", _val_report_path, exc_info=True
        )

import streamlit as _st_session  # noqa: F401 — used only for session_id probe

# Streamlit's internal scriptrunner API path has moved across versions, so
# import defensively and degrade to "—" if it is unavailable.
try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx as _get_script_run_ctx
except Exception:  # pragma: no cover - internal API location varies by version
    try:
        from streamlit.runtime.scriptrunner_utils.script_run_context import (
            get_script_run_ctx as _get_script_run_ctx,
        )
    except Exception:
        _get_script_run_ctx = None

_session_id = _get_script_run_ctx() if _get_script_run_ctx is not None else None
_session_id_str = (
    str(_session_id.session_id)[:8] + "…"
    if _session_id is not None
    else "—"
)

render_status_bar([
    {"label": "Platform", "value": f"ShieldLab G4 v{_SHIELDLAB_VERSION}", "state": "ok"},
    {"label": "Validation gate", "value": _val_gate, "state": "ok" if _val_gate == "pass" else "warn"},
    {"label": "Report date", "value": _val_generated_at, "state": "neutral"},
    {"label": "Studies", "value": _val_study_count, "state": "neutral"},
    {"label": "Benchmarks", "value": _val_benchmark_pass, "state": "ok" if _val_benchmark_pass == "pass" else "neutral"},
    {"label": "Session", "value": _session_id_str, "state": "neutral"},
])

render_platform_capability_grid(
    PLATFORM_CAPABILITIES,
    title="Product Operations Surface",
    subtitle="Settings remains the operator-facing entry point for runtime controls while deeper evidence lives in benchmark, results, and methods surfaces.",
)

st.info(str(copy.get("session_note", "These controls are saved to a local user profile and apply across the platform shell after rerun.")))

st.divider()
st.subheader(str(copy.get("system_paths_heading", "System and Paths")))
st.caption(str(copy.get("system_paths_caption", "Runtime paths and environment configuration resolved at startup.")))

with st.expander(str(copy.get("system_paths_expander", "System Configuration & Runtime Paths")), expanded=False):
    g4_binary_name = str(copy.get("geant4_binary_name", "ShieldLabG4"))
    g4_binary_candidates = [
        config.BUILD_DIR / g4_binary_name,
        config.BUILD_DIR / f"{g4_binary_name}.exe",
        config.BUILD_DIR / "Release" / g4_binary_name,
        config.BUILD_DIR / "Release" / f"{g4_binary_name}.exe",
        config.BUILD_DIR / "Debug" / g4_binary_name,
    ]
    g4_binary_path: Path | None = next(
        (p for p in g4_binary_candidates if p.exists()), None
    )

    path_entries = [
        (str(copy.get("path_project_root",  "Project Root")),   config.PROJECT_ROOT),
        (str(copy.get("path_python_lib",    "Python Library")),  config.SHIELDLAB_PYTHON),
        (str(copy.get("path_python_exe",    "Python Executable")), config.PYTHON_EXE),
        (str(copy.get("path_build_dir",     "Build Directory")),  config.BUILD_DIR),
        (str(copy.get("path_studies_dir",   "Studies Directory")), config.STUDIES_DIR),
        (str(copy.get("path_results_dir",   "Results Directory")), config.RESULTS_DIR),
        (str(copy.get("path_geant4_binary", "Geant4 Binary")),
         g4_binary_path if g4_binary_path else config.BUILD_DIR / g4_binary_name),
    ]

    runtime_entries = [
        ("WSL distro", config.WSL_DISTRO or "(native Windows / auto)"),
        ("Geant4 setup", config.GEANT4_SETUP or "(runner default / unset)"),
        ("Geant4 executable", config.GEANT4_EXECUTABLE),
    ]

    render_path_table(
        [
            {
                "label": label,
                "value": path,
                "badge_class": "path-badge-ok" if Path(path).exists() else "path-badge-miss",
                "badge_text": "exists" if Path(path).exists() else "not found",
            }
            for label, path in path_entries
        ]
    )

    render_path_table(
        [{"label": label, "value": value} for label, value in runtime_entries],
        runtime=True,
    )

    st.caption(str(copy.get(
        "env_var_override_note",
        "Set `SHIELDLAB_PROJECT_ROOT`, `SHIELDLAB_PYTHONPATH`, `SHIELDLAB_BUILD_DIR`, "
        "`SHIELDLAB_STUDIES_DIR`, `SHIELDLAB_PYTHON_EXE`, `SHIELDLAB_WSL_DISTRO`, `SHIELDLAB_GEANT4_SETUP`, "
        "and `SHIELDLAB_G4_EXECUTABLE` environment variables to override defaults.",
    )))

    # Live status metrics
    _mc = st.columns(4)
    _mc[0].metric("Project Root", "OK" if config.PROJECT_ROOT.exists() else "Missing",
                  delta="exists" if config.PROJECT_ROOT.exists() else "missing")
    _mc[1].metric("Python Exe",   "OK" if config.PYTHON_EXE.exists() else "Missing",
                  delta="exists" if config.PYTHON_EXE.exists() else "missing")
    _mc[2].metric("Build Dir",    "OK" if config.BUILD_DIR.exists() else "Missing",
                  delta="exists" if config.BUILD_DIR.exists() else "missing")
    _mc[3].metric("G4 Binary",    "OK" if g4_binary_path else "Missing",
                  delta="found" if g4_binary_path else "not built")


