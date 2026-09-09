from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

import pandas as pd

_log = logging.getLogger(__name__)

_G4_TIMEOUT_S: int = int(os.environ.get("SHIELDLAB_G4_TIMEOUT_S", "3600"))

from shieldlab.analysis import collect_buildup_observable, compare_buildup_observable, load_reference_buildup
from shieldlab.analysis.runtime_benchmarks import load_reference_acceptance, summarize_reference_comparison
from shieldlab.io.excel_writer import write_workbook
from shieldlab.io.macro_writer import write_macro
from shieldlab.io.schema import PROVENANCE_MANIFEST_SCHEMA_VERSION, RESULT_SCHEMA_VERSION, STUDY_SCHEMA_VERSION
from shieldlab.io.sweep_collector import collect_composition_sweep, collect_sweep, collect_thickness_sweep
from shieldlab.io.study_validator import has_errors, issues_to_frame, validate_study, write_validation_report


def _load_study(study_file: str | Path) -> dict[str, Any]:
    with Path(study_file).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _project_root_from_study(study_file: Path) -> Path:
    if study_file.parent.name == "studies" and study_file.parent.parent.name == "configs":
        return study_file.parent.parent.parent
    return Path.cwd()


def _wsl_path(path: str | Path) -> tuple[str | None, str]:
    text = str(path).replace("\\", "/")
    if text.startswith("//wsl.localhost/") or text.startswith("//wsl$/"):
        parts = text.lstrip("/").split("/")
        if len(parts) < 3:
            raise ValueError(f"Invalid WSL UNC path: {path}")
        return parts[1], "/" + "/".join(parts[2:])
    if len(text) >= 3 and text[1] == ":" and text[2] == "/":
        drive = text[0].lower()
        remainder = text[3:]
        return None, f"/mnt/{drive}/{remainder}"
    return None, text


def _default_geant4_setup(project_root: Path) -> str | None:
    distro, root = _wsl_path(project_root)
    if distro is None:
        return None
    install_root = str(PurePosixPath(root).parent)
    return f"{install_root}/bin/geant4.sh"


def _result_dir(build_dir: Path, study: dict[str, Any]) -> Path:
    output_dir = Path(study.get("run", {}).get("output_dir", "results/study"))
    if output_dir.is_absolute():
        return output_dir
    return build_dir / output_dir


def _run_geant4(
    macro_file: Path,
    build_dir: Path,
    executable: str,
    geant4_setup: str | None,
    wsl_distro: str | None,
    physics_list: str | None,
) -> None:
    build_distro, build_posix = _wsl_path(build_dir)
    macro_distro, macro_posix = _wsl_path(macro_file)
    distro = wsl_distro or build_distro or macro_distro

    if distro:
        script_parts = [f"cd {shlex.quote(build_posix)}"]
        if physics_list:
            script_parts.append(
                f"export SHIELDLAB_PHYSICS_LIST={shlex.quote(physics_list)}"
            )
        if geant4_setup:
            script_parts.append(f"source {shlex.quote(geant4_setup)}")
        script_parts.append(
            f"{shlex.quote(executable)} {shlex.quote(macro_posix)}"
        )
        script = " && ".join(script_parts)
        _log.info("Running G4 via WSL distro=%s", distro)
        subprocess.run(
            ["wsl", "-d", distro, "--", "bash", "-lc", script],
            check=True,
            timeout=_G4_TIMEOUT_S,
        )
        return

    command = [executable, str(macro_file)]
    env = os.environ.copy()
    if physics_list:
        env["SHIELDLAB_PHYSICS_LIST"] = physics_list
    if platform.system().lower() == "windows" and not executable.lower().endswith(".exe"):
        command[0] = f"{executable}.exe"
    _log.info("Running G4 directly: %s", " ".join(command))
    subprocess.run(command, cwd=build_dir, check=True, timeout=_G4_TIMEOUT_S, env=env)


def _write_validation_summary(
    result_dir: Path,
    study: dict[str, Any],
    study_file: Path,
    macro_file: Path,
    workbook: Path,
    sweep_file: Path | None,
    study_validation_file: Path,
    buildup_observable_file: Path | None,
    buildup_comparison_file: Path | None,
) -> Path:
    run_summary_files = sorted(result_dir.glob("**/run_summary.csv"))
    layer_files = sorted(result_dir.glob("**/layer_energy_deposition.csv"))
    figure_dir = result_dir / "figures"
    reference_comparison_path = result_dir / "reference_comparison.csv"
    comparison_df = pd.read_csv(reference_comparison_path) if reference_comparison_path.exists() else pd.DataFrame()
    buildup_comparison_df = pd.read_csv(buildup_comparison_file) if buildup_comparison_file and buildup_comparison_file.exists() else pd.DataFrame()
    benchmark_df = comparison_df.copy()
    if not buildup_comparison_df.empty:
        benchmark_df = pd.concat([benchmark_df, buildup_comparison_df], ignore_index=True, sort=False)
    benchmark_summary = summarize_reference_comparison(benchmark_df, load_reference_acceptance(study_file))
    references = study.get("references", {}) if isinstance(study.get("references", {}), dict) else {}
    layers = study.get("geometry", {}).get("layers", []) if isinstance(study.get("geometry", {}), dict) else []
    assumptions = {
        "particle": study.get("source", {}).get("particle"),
        "source_energy": study.get("source", {}).get("energy"),
        "source_energy_unit": study.get("source", {}).get("energy_unit"),
        "geometry_type": study.get("geometry", {}).get("type"),
        "layer_count": len(layers) if isinstance(layers, list) else 0,
        "total_thickness_cm": float(sum(float(layer.get("thickness_cm", 0.0)) for layer in layers if isinstance(layer, dict))) if isinstance(layers, list) else 0.0,
        "materials": [material.get("name") for material in study.get("materials", []) if isinstance(material, dict) and material.get("name")],
        "validation_mode": study.get("run", {}).get("validation_mode"),
        "physics_list": study.get("run", {}).get("physics_list"),
        "histories": study.get("run", {}).get("histories"),
        "random_seed": study.get("run", {}).get("random_seed"),
    }
    literature_sources = {
        "paper_title": references.get("paper_title"),
        "paper_doi": references.get("paper_doi"),
        "sample_id": references.get("sample_id"),
        "has_reference_coefficients": bool(references.get("coefficients")),
        "has_buildup_factors": bool((references.get("buildup_factors") or {}).get("coefficients")) if isinstance(references.get("buildup_factors") or {}, dict) else False,
        "buildup_source": (references.get("buildup_factors") or {}).get("source") if isinstance(references.get("buildup_factors") or {}, dict) else None,
    }
    summary = {
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "status": "completed",
        "study_file": str(study_file),
        "macro_file": str(macro_file),
        "result_dir": str(result_dir),
        "workbook": str(workbook),
        "sweep_summary": str(sweep_file) if sweep_file else None,
        "buildup_observable_summary": str(buildup_observable_file) if buildup_observable_file else None,
        "buildup_comparison": str(buildup_comparison_file) if buildup_comparison_file else None,
        "study_validation": str(study_validation_file),
        "run_summary_exists": bool(run_summary_files),
        "run_summary_count": len(run_summary_files),
        "histories": study.get("run", {}).get("histories"),
        "random_seed": study.get("run", {}).get("random_seed"),
        "layer_energy_deposition_exists": bool(layer_files),
        "layer_energy_deposition_count": len(layer_files),
        "reference_comparison_exists": reference_comparison_path.exists(),
        "buildup_observable_exists": buildup_observable_file.exists() if buildup_observable_file else False,
        "buildup_comparison_exists": buildup_comparison_file.exists() if buildup_comparison_file else False,
        "benchmark_summary": benchmark_summary,
        "benchmark_status": benchmark_summary.get("status", "unavailable"),
        "assumptions": assumptions,
        "literature_sources": literature_sources,
        "figures": sorted(path.name for path in figure_dir.glob("*.png")) if figure_dir.exists() else [],
    }
    output_path = result_dir / "validation_summary.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return output_path


def _write_provenance_manifest(
    result_dir: Path,
    study: dict[str, Any],
    study_file: Path,
    macro_file: Path,
    workbook: Path,
    validation_summary_file: Path,
) -> Path:
    run = study.get("run", {}) if isinstance(study.get("run", {}), dict) else {}
    geometry = study.get("geometry", {}) if isinstance(study.get("geometry", {}), dict) else {}
    source = study.get("source", {}) if isinstance(study.get("source", {}), dict) else {}
    references = study.get("references", {}) if isinstance(study.get("references", {}), dict) else {}
    layers = geometry.get("layers", []) if isinstance(geometry.get("layers", []), list) else []
    payload = {
        "manifest_schema_version": PROVENANCE_MANIFEST_SCHEMA_VERSION,
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "study": {
            "study_schema_version": study.get("study_schema_version", STUDY_SCHEMA_VERSION),
            "study_file": str(study_file),
            "study_name": study.get("name"),
            "description": study.get("description"),
        },
        "execution": {
            "run_output_dir": run.get("output_dir"),
            "histories": run.get("histories"),
            "physics_list": run.get("physics_list"),
            "validation_mode": run.get("validation_mode"),
            "platform": platform.platform(),
        },
        "physics_context": {
            "particle": source.get("particle"),
            "source_energy": source.get("energy"),
            "source_energy_unit": source.get("energy_unit"),
            "geometry_type": geometry.get("type"),
            "layer_count": len(layers),
            "materials": [material.get("name") for material in study.get("materials", []) if isinstance(material, dict) and material.get("name")],
        },
        "literature_provenance": {
            "paper_title": references.get("paper_title"),
            "paper_doi": references.get("paper_doi"),
            "sample_id": references.get("sample_id"),
            "has_reference_coefficients": bool(references.get("coefficients")),
            "has_buildup_factors": bool((references.get("buildup_factors") or {}).get("coefficients")) if isinstance(references.get("buildup_factors") or {}, dict) else False,
        },
        "artifacts": {
            "result_dir": str(result_dir),
            "macro_file": str(macro_file),
            "workbook": str(workbook),
            "validation_summary": str(validation_summary_file),
        },
    }
    output_path = result_dir / "provenance_manifest.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def run_study(
    study_file: str | Path,
    build_dir: str | Path | None = None,
    macro_file: str | Path | None = None,
    executable: str = "./ShieldLabG4",
    geant4_setup: str | None = None,
    wsl_distro: str | None = None,
    skip_geant4: bool = False,
    no_plots: bool = False,
    allow_validation_errors: bool = False,
) -> dict[str, Path | None]:
    study_path = Path(study_file)
    project_root = _project_root_from_study(study_path)
    build_path = Path(build_dir) if build_dir else project_root / "build"
    study = _load_study(study_path)
    result_path = _result_dir(build_path, study)
    study_validation_path = result_path / "study_validation.csv"
    validation_issues = validate_study(study)
    write_validation_report(validation_issues, study_validation_path)
    if has_errors(validation_issues) and not allow_validation_errors:
        errors = issues_to_frame(validation_issues)
        raise ValueError(
            "Study validation failed. Fix the errors in "
            f"{study_validation_path}.\n{errors[errors['severity'] == 'error'].to_string(index=False)}"
        )

    macro_path = Path(macro_file) if macro_file else build_path / f"generated_{study_path.stem}.mac"
    write_macro(study_path, macro_path)

    setup_path = geant4_setup if geant4_setup is not None else _default_geant4_setup(project_root)
    if not skip_geant4:
        run = study.get("run", {}) if isinstance(study.get("run", {}), dict) else {}
        physics_list = run.get("physics_list") if isinstance(run, dict) else None
        _run_geant4(macro_path, build_path, executable, setup_path, wsl_distro, str(physics_list) if physics_list else None)

    sweep_path = None
    buildup_observable_path = None
    buildup_comparison_path = None
    if study.get("run", {}).get("energy_grid"):
        sweep_path = collect_sweep(result_path)
        try:
            buildup_observable_path = collect_buildup_observable(result_path)
        except ValueError:
            buildup_observable_path = None
        if buildup_observable_path and buildup_observable_path.exists():
            references = study.get("references", {}) if isinstance(study.get("references", {}), dict) else {}
            depth_mfp = float(references.get("buildup_validation_depth_mfp", 5.0) or 5.0)
            observable_df = pd.read_csv(buildup_observable_path)
            reference_buildup_df = load_reference_buildup(study_path)
            buildup_comparison_df = compare_buildup_observable(observable_df, reference_buildup_df, depth_mfp=depth_mfp)
            if not buildup_comparison_df.empty:
                buildup_comparison_path = result_path / "buildup_comparison.csv"
                buildup_comparison_df.to_csv(buildup_comparison_path, index=False)
    elif study.get("run", {}).get("thickness_grid"):
        sweep_path = collect_thickness_sweep(result_path)
    elif study.get("run", {}).get("composition_sweep"):
        sweep_path = collect_composition_sweep(result_path)

    workbook = write_workbook(result_path, study_file=study_path, make_plots=not no_plots)
    validation = _write_validation_summary(
        result_path,
        study,
        study_path,
        macro_path,
        workbook,
        sweep_path,
        study_validation_path,
        buildup_observable_path,
        buildup_comparison_path,
    )
    provenance_manifest = _write_provenance_manifest(
        result_path,
        study,
        study_path,
        macro_path,
        workbook,
        validation,
    )
    try:
        summary_payload = json.loads(validation.read_text(encoding="utf-8"))
        summary_payload["provenance_manifest"] = str(provenance_manifest)
        validation.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    except (json.JSONDecodeError, OSError):
        pass
    return {
        "macro_file": macro_path,
        "result_dir": result_path,
        "study_validation": study_validation_path,
        "sweep_summary": sweep_path,
        "buildup_observable_summary": buildup_observable_path,
        "buildup_comparison": buildup_comparison_path,
        "workbook": workbook,
        "validation_summary": validation,
        "provenance_manifest": provenance_manifest,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a complete ShieldLab-G4 study workflow.")
    parser.add_argument("study_file", help="Input study JSON file")
    parser.add_argument("--build-dir", help="ShieldLab-G4 build directory")
    parser.add_argument("--macro", help="Output macro path")
    parser.add_argument("--executable", default="./ShieldLabG4", help="Geant4 executable path or command")
    parser.add_argument("--geant4-setup", help="Path to geant4.sh; inferred for WSL project layouts when omitted")
    parser.add_argument("--wsl-distro", help="WSL distro name for launching Geant4 from Windows")
    parser.add_argument("--skip-geant4", action="store_true", help="Reuse existing result CSV files")
    parser.add_argument("--no-plots", action="store_true", help="Skip PNG plot generation")
    parser.add_argument("--allow-validation-errors", action="store_true", help="Continue even if study validation reports errors")
    args = parser.parse_args()

    outputs = run_study(
        args.study_file,
        build_dir=args.build_dir,
        macro_file=args.macro,
        executable=args.executable,
        geant4_setup=args.geant4_setup,
        wsl_distro=args.wsl_distro,
        skip_geant4=args.skip_geant4,
        no_plots=args.no_plots,
        allow_validation_errors=args.allow_validation_errors,
    )
    for name, path in outputs.items():
        if path is not None:
            print(f"{name}: {path}")


if __name__ == "__main__":
    main()