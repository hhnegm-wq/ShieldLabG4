"""Run Study page - execute Geant4 with live output streaming."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

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
from shieldlab.io.study_validator import has_errors, issues_to_frame, validate_study
from shieldlab.content import PAGE_COPY

copy = PAGE_COPY["run_study"]


def _safe_uploaded_study_path(filename: str) -> Path:
    safe_name = Path(filename).name
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", safe_name)
    if not safe_name.lower().endswith(".json"):
        safe_name = f"{safe_name}.json"
    destination = (config.STUDIES_DIR / safe_name).resolve()
    if not config.is_within_directory(destination, config.STUDIES_DIR.resolve()):
        raise ValueError("Uploaded study filename resolves outside the studies directory.")
    return destination


def _validated_build_dir(path_text: str) -> Path:
    candidate = config.resolve_project_path(path_text, base_dir=config.PROJECT_ROOT)
    candidate_text = str(candidate).replace("\\", "/")
    is_wsl_unc = candidate_text.startswith("//wsl.localhost/") or candidate_text.startswith("//wsl$/")
    if not is_wsl_unc and not config.is_within_directory(candidate, config.PROJECT_ROOT):
        raise ValueError("Build directory must stay inside the ShieldLab G4 project root.")
    return candidate

render_page_hero(str(copy["title"]), str(copy["caption"]), "Monte Carlo Simulation")

render_breadcrumb(["ShieldLab G4", "Simulation"], current="Run Study")

_run_studies = sorted(config.STUDIES_DIR.glob("*.json")) if config.STUDIES_DIR.exists() else []
_run_results = (
    [d for d in config.RESULTS_DIR.iterdir() if d.is_dir()] if config.RESULTS_DIR.exists() else []
)
_build_dir_default = (config.PROJECT_ROOT / "build").exists()
render_status_bar([
    {"label": "Build Dir", "value": "OK" if _build_dir_default else "Missing", "state": "ok" if _build_dir_default else "warn"},
    {"label": "Studies", "value": len(_run_studies), "state": "info"},
    {"label": "Result Sets", "value": len(_run_results), "state": "neutral"},
])
render_kpi_strip(
    [
        {"label": "Studies Available", "value": len(_run_studies), "trend": "Catalog", "trend_state": "steady", "footnote": "Run-ready JSON studies"},
        {"label": "Result Sets", "value": len(_run_results), "trend": "Output", "trend_state": "up", "footnote": "Existing computed runs"},
        {"label": "Engine", "value": "Geant4", "trend": "11.4", "trend_state": "up", "footnote": "Underlying Monte Carlo core"},
        {"label": "Modes", "value": "Live + Batch", "trend": "Streamed", "trend_state": "steady", "footnote": "Interactive or queued execution"},
        {"label": "Build Dir", "value": "OK" if _build_dir_default else "Missing", "trend": "Compiled", "trend_state": "up" if _build_dir_default else "warn", "footnote": "ShieldLab Geant4 binary"},
        {"label": "Output Format", "value": "NPZ + JSON", "trend": "Portable", "trend_state": "neutral", "footnote": "Result + summary artifacts"},
    ],
    title="ShieldLab Execution Control Strip",
    subtitle="Stream Geant4 jobs, monitor live progress, and route results into ShieldLab analytics.",
)

st.subheader(str(copy["selector_heading"]))
studies = sorted(config.STUDIES_DIR.glob("*.json")) if config.STUDIES_DIR.exists() else []
study_names = [p.name for p in studies]

col_pick, col_upload = st.columns([3, 2])
with col_pick:
    selected = st.selectbox(str(copy["selectbox_label"]), ["-- select --"] + study_names)
with col_upload:
    uploaded = st.file_uploader(str(copy["upload_label"]), type="json")

study_path: Path | None = None
study_obj: dict | None = None

_MAX_UPLOAD_BYTES = 512 * 1024  # 512 KB — prevent memory exhaustion from oversized uploads

if uploaded is not None:
    raw_bytes = uploaded.read()
    if len(raw_bytes) > _MAX_UPLOAD_BYTES:
        st.error(
            f"Uploaded file is too large ({len(raw_bytes) // 1024} KB). "
            f"Maximum allowed size is {_MAX_UPLOAD_BYTES // 1024} KB."
        )
        st.stop()
    raw = raw_bytes.decode("utf-8", errors="replace")
    # Validate JSON *before* writing to disk so invalid uploads leave no artefact.
    try:
        study_obj = json.loads(raw)
    except json.JSONDecodeError as e:
        st.error(f"Uploaded file is not valid JSON: {e}")
        st.stop()
    tmp = _safe_uploaded_study_path(uploaded.name)
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(raw, encoding="utf-8")
    study_path = tmp
elif selected != "-- select --":
    study_path = config.STUDIES_DIR / selected
    try:
        study_obj = json.loads(study_path.read_text(encoding="utf-8"))
    except Exception as e:
        st.error(str(copy["study_read_error"]).format(error=e))

if study_obj:
    with st.expander(str(copy["study_info_heading"]), expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        src = study_obj.get("source", {})
        run = study_obj.get("run", {})
        sweep = (
            f"energy ({len(run.get('energy_grid', []))} pts)"
            if "energy_grid" in run
            else f"thickness ({len(run.get('thickness_grid', []))} pts)"
            if "thickness_grid" in run
            else "composition"
            if "composition_sweep" in run
            else "single"
        )
        with c1:
            st.metric("Study", study_obj.get("name", "-"))
        with c2:
            st.metric("Beam", f"{src.get('particle','?')} {src.get('energy','?')} {src.get('energy_unit','keV')}")
        with c3:
            st.metric("Sweep", sweep)
        with c4:
            st.metric("Histories", run.get("histories", "-"))
        if study_obj.get("description"):
            st.caption(study_obj["description"])
        layers = study_obj.get("geometry", {}).get("layers", [])
        if layers:
            st.markdown(
                f"**{copy['layers_label']}** "
                + "  |  ".join(
                    f"{ly.get('material')} {ly.get('thickness_cm')} cm" for ly in layers
                )
            )

    with st.expander("Scientific Pre-Run Checklist", expanded=True):
        issues = validate_study(study_obj)
        errors = [issue for issue in issues if issue.severity == "error"]
        warnings = [issue for issue in issues if issue.severity == "warning"]
        geometry_layers = study_obj.get("geometry", {}).get("layers", []) if isinstance(study_obj.get("geometry", {}), dict) else []
        run_cfg = study_obj.get("run", {}) if isinstance(study_obj.get("run", {}), dict) else {}
        source_cfg = study_obj.get("source", {}) if isinstance(study_obj.get("source", {}), dict) else {}

        checks = [
            ("Study schema version present", bool(study_obj.get("study_schema_version"))),
            ("Materials configured", bool(study_obj.get("materials"))),
            ("Geometry layers configured", bool(geometry_layers)),
            ("Particle + source energy defined", bool(source_cfg.get("particle")) and bool(source_cfg.get("energy"))),
            ("Histories configured", bool(run_cfg.get("histories"))),
            ("No validation errors", len(errors) == 0),
        ]

        for label, ok in checks:
            st.write(f"{'PASS' if ok else 'FAIL'} {label}")

        if warnings:
            st.warning(f"{len(warnings)} scientific warning(s) detected. Review before execution.")
        if errors:
            st.error(f"{len(errors)} blocking validation error(s) detected. Fix before execution.")

with st.expander(str(copy["run_config_heading"])):
    build_dir_str = st.text_input(str(copy["build_dir_label"]), value=str(config.BUILD_DIR))
    executable_str = st.text_input("Geant4 executable", value=str(config.GEANT4_EXECUTABLE))
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        wsl_distro = st.text_input(
            "WSL distro",
            value=str(config.WSL_DISTRO),
            help="Set when the Geant4 build lives inside WSL. Leave blank for native Windows execution.",
        )
    with col_w2:
        geant4_setup = st.text_input(
            "Geant4 setup script",
            value=str(config.GEANT4_SETUP),
            help="Optional path to geant4.sh inside WSL, for example /home/user/geant4-install/bin/geant4.sh.",
        )
    st.caption(
        "Recommended for this project: keep the Geant4 build in WSL, point the build directory to the WSL-mounted project path, and set the distro so the browser launches the Linux binary through bash."
    )
    col_o1, col_o2 = st.columns(2)
    with col_o1:
        skip_geant4 = st.checkbox(
            str(copy["skip_geant4_label"]),
            value=False,
            help=str(copy["skip_geant4_help"]),
        )
    with col_o2:
        no_plots = st.checkbox(str(copy["skip_plots_label"]), value=False)

st.divider()

st.subheader(str(copy["validation_heading"]))
if study_obj is None:
    st.info(str(copy["select_study_info"]))
else:
    col_vbtn, _ = st.columns([1, 3])
    with col_vbtn:
        do_validate = st.button(str(copy["validate_button"]), width="stretch")

    if do_validate:
        issues = validate_study(study_obj)
        n_err = sum(1 for i in issues if i.severity == "error")
        n_warn = sum(1 for i in issues if i.severity == "warning")
        if n_err:
            st.error(str(copy["validation_errors"]).format(errors=n_err, warnings=n_warn))
        elif n_warn:
            st.warning(str(copy["validation_warnings"]).format(warnings=n_warn))
        else:
            st.success(str(copy["validation_success"]))
        if issues:
            st.dataframe(
                issues_to_frame(issues)[["severity", "path", "message"]],
                width="stretch",
                hide_index=True,
            )

    st.divider()

    st.subheader(str(copy["execute_heading"]))
    col_rbtn, _ = st.columns([1, 3])
    with col_rbtn:
        do_run = st.button(str(copy["run_button"]), type="primary", width="stretch")

    if do_run:
        try:
            build_dir = _validated_build_dir(build_dir_str)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()

        # Sanitise user-supplied subprocess arguments before they reach Popen.
        # subprocess uses list-form (no shell=True) so shell injection is not possible,
        # but we still reject null bytes and excessively long strings as a defence-in-depth measure.
        _MAX_ARG_LEN = 512

        def _safe_arg(value: str, label: str) -> str:
            value = value.strip()
            if "\x00" in value:
                st.error(f"Invalid value for '{label}': contains null byte.")
                st.stop()
            if len(value) > _MAX_ARG_LEN:
                st.error(f"Value for '{label}' exceeds maximum allowed length ({_MAX_ARG_LEN} chars).")
                st.stop()
            return value

        executable_str_safe = _safe_arg(executable_str, "Geant4 executable")
        wsl_distro_safe = _safe_arg(wsl_distro, "WSL distro")
        geant4_setup_safe = _safe_arg(geant4_setup, "Geant4 setup script")

        env = os.environ.copy()
        env["PYTHONPATH"] = str(config.SHIELDLAB_PYTHON)
        cmd = [
            str(config.PYTHON_EXE),
            "-m",
            "shieldlab.io.runner",
            str(study_path),
            "--build-dir",
            str(build_dir),
            "--executable",
            executable_str_safe,
        ]
        if wsl_distro_safe:
            cmd.extend(["--wsl-distro", wsl_distro_safe])
        if geant4_setup_safe:
            cmd.extend(["--geant4-setup", geant4_setup_safe])
        if skip_geant4:
            cmd.append("--skip-geant4")
        if no_plots:
            cmd.append("--no-plots")

        st.markdown(f"**{copy['live_output_label']}**")
        output_ph = st.empty()
        lines: list[str] = []

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
            )
            for line in proc.stdout:  # type: ignore[union-attr]
                lines.append(line)
                output_ph.code("".join(lines[-100:]), language=None)
            proc.wait()
        except Exception as exc:
            st.error(str(copy["launch_error"]).format(error=exc))
            st.stop()

        if proc.returncode == 0:
            st.success(str(copy["success_message"]))

            result_dir = build_dir / study_obj.get("run", {}).get(
                "output_dir", "results/study"
            )
            val_file = result_dir / "validation_summary.json"

            if val_file.exists():
                summary = json.loads(val_file.read_text())
                mc = st.columns(4)
                with mc[0]:
                    st.metric("Geant4 Runs", summary.get("run_summary_count", 0))
                with mc[1]:
                    st.metric("Figures", len(summary.get("figures", [])))
                with mc[2]:
                    st.metric("Excel", "Yes" if summary.get("workbook") else "No")
                with mc[3]:
                    st.metric(
                        "Ref Comparison",
                        "Yes" if summary.get("reference_comparison_exists") else "No",
                    )

                manifest_file = result_dir / "provenance_manifest.json"
                st.caption(
                    f"Provenance manifest: {'available' if manifest_file.exists() else 'not found'}"
                )

                benchmark_status = summary.get("benchmark_status")
                if benchmark_status == "failed":
                    st.error("Benchmark status: failed configured acceptance limits.")
                elif benchmark_status == "passed":
                    st.success("Benchmark status: passed configured acceptance limits.")
                elif benchmark_status == "available":
                    st.info("Benchmark metrics are available for this study, but no acceptance thresholds are configured.")

                # Preview figures
                fig_dir = result_dir / "figures"
                pngs = sorted(fig_dir.glob("*.png")) if fig_dir.exists() else []
                if pngs:
                    st.markdown("**Figures**")
                    img_cols = st.columns(min(len(pngs), 4))
                    for i, p in enumerate(pngs[:4]):
                        with img_cols[i]:
                            try:
                                from PIL import Image
                                st.image(
                                    Image.open(str(p)),
                                    width="stretch",
                                    caption=p.stem.replace("_", " "),
                                )
                            except Exception:
                                st.image(str(p), width="stretch", caption=p.stem)

                st.info(
                    str(copy["result_saved_message"]).format(result_dir=result_dir.name)
                )
        else:
            st.error(str(copy["failure_message"]).format(code=proc.returncode))



