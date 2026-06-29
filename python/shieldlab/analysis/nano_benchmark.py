from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from shieldlab.io.macro_writer import write_macro
from shieldlab.io.manifest import build_manifest
from shieldlab.io.runner import run_study
from shieldlab.io.study_validator import has_errors, issues_to_frame, validate_study, write_validation_report


def _load_study(study_file: str | Path) -> dict[str, Any]:
    with Path(study_file).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _project_root_from_study(study_file: Path) -> Path:
    if study_file.parent.name == "studies" and study_file.parent.parent.name == "configs":
        return study_file.parent.parent.parent
    return Path.cwd()


def _result_dir(build_dir: Path, study: dict[str, Any]) -> Path:
    output_dir = Path(study.get("run", {}).get("output_dir", "results/study"))
    if output_dir.is_absolute():
        return output_dir
    return build_dir / output_dir


def _default_macro_path(build_dir: Path, study_file: Path) -> Path:
    return build_dir / f"generated_{study_file.stem}.mac"


def _build_plan_payload(
    study: dict[str, Any],
    study_file: Path,
    build_dir: Path,
    macro_file: Path,
    result_dir: Path,
    validation_file: Path,
) -> dict[str, Any]:
    paper3 = study.get("paper3", {}) if isinstance(study.get("paper3", {}), dict) else {}
    run = study.get("run", {}) if isinstance(study.get("run", {}), dict) else {}
    source = study.get("source", {}) if isinstance(study.get("source", {}), dict) else {}
    geometry = study.get("geometry", {}) if isinstance(study.get("geometry", {}), dict) else {}
    layers = geometry.get("layers", []) if isinstance(geometry.get("layers", []), list) else []
    materials = study.get("materials", []) if isinstance(study.get("materials", []), list) else []
    return {
        "schema_version": "1.0",
        "status": "planned",
        "study": {
            "file": str(study_file),
            "name": study.get("name"),
            "description": study.get("description"),
            "paper3": paper3,
        },
        "execution": {
            "build_dir": str(build_dir),
            "result_dir": str(result_dir),
            "macro_file": str(macro_file),
            "validation_file": str(validation_file),
            "validation_mode": run.get("validation_mode"),
            "physics_list": run.get("physics_list"),
            "histories": run.get("histories"),
            "random_seed": run.get("random_seed"),
            "energy_grid": list(run.get("energy_grid", [])) if isinstance(run.get("energy_grid"), list) else [],
        },
        "physics_context": {
            "particle": source.get("particle"),
            "energy_unit": source.get("energy_unit"),
            "direction": source.get("direction"),
            "geometry_type": geometry.get("type"),
            "transverse_size_cm": geometry.get("transverse_size_cm"),
            "layer_count": len(layers),
            "materials": [material.get("name") for material in materials if isinstance(material, dict)],
        },
        "artifacts": {
            "expected_result_subdirs": [
                f"E_{str(energy).replace('.', 'p')}_{source.get('energy_unit', 'keV')}"
                for energy in (run.get("energy_grid") or [])
            ],
        },
    }


def _write_plan_files(
    study: dict[str, Any],
    study_file: Path,
    build_dir: Path,
    macro_file: Path,
    result_dir: Path,
    validation_file: Path,
) -> tuple[Path, Path]:
    result_dir.mkdir(parents=True, exist_ok=True)
    plan_payload = _build_plan_payload(study, study_file, build_dir, macro_file, result_dir, validation_file)
    plan_file = result_dir / "paper3_benchmark_plan.json"
    plan_file.write_text(json.dumps(plan_payload, indent=2), encoding="utf-8")

    paper3 = study.get("paper3", {}) if isinstance(study.get("paper3", {}), dict) else {}
    build_manifest(
        output_dir=result_dir,
        config=study,
        seed=study.get("run", {}).get("random_seed"),
        extra={
            "campaign": paper3.get("campaign"),
            "regime": paper3.get("regime"),
            "material_family": paper3.get("material_family"),
            "target_figures": paper3.get("target_figures"),
            "plan_file": str(plan_file),
            "study_validation": str(validation_file),
            "macro_file": str(macro_file),
            "status": "planned",
        },
    )
    manifest_file = result_dir / "manifest.json"
    return plan_file, manifest_file


def plan_benchmark(
    study_file: str | Path,
    *,
    build_dir: str | Path | None = None,
    macro_file: str | Path | None = None,
    allow_validation_errors: bool = False,
) -> dict[str, Path]:
    study_path = Path(study_file)
    study = _load_study(study_path)
    project_root = _project_root_from_study(study_path)
    build_path = Path(build_dir) if build_dir else project_root / "build"
    result_path = _result_dir(build_path, study)
    validation_path = result_path / "study_validation.csv"

    issues = validate_study(study)
    write_validation_report(issues, validation_path)
    if has_errors(issues) and not allow_validation_errors:
        errors = issues_to_frame(issues)
        raise ValueError(
            "Study validation failed. Fix the errors in "
            f"{validation_path}.\n{errors[errors['severity'] == 'error'].to_string(index=False)}"
        )

    macro_path = Path(macro_file) if macro_file else _default_macro_path(build_path, study_path)
    write_macro(study_path, macro_path)
    plan_file, manifest_file = _write_plan_files(study, study_path, build_path, macro_path, result_path, validation_path)
    return {
        "study_file": study_path,
        "macro_file": macro_path,
        "result_dir": result_path,
        "study_validation": validation_path,
        "plan_file": plan_file,
        "manifest_file": manifest_file,
    }


def run_benchmark(
    study_file: str | Path,
    *,
    build_dir: str | Path | None = None,
    macro_file: str | Path | None = None,
    executable: str = "./ShieldLabG4",
    geant4_setup: str | None = None,
    wsl_distro: str | None = None,
    dry_run: bool = False,
    skip_geant4: bool = False,
    no_plots: bool = False,
    allow_validation_errors: bool = False,
) -> dict[str, Path | None]:
    planned = plan_benchmark(
        study_file,
        build_dir=build_dir,
        macro_file=macro_file,
        allow_validation_errors=allow_validation_errors,
    )
    if dry_run:
        return planned

    executed = run_study(
        study_file,
        build_dir=build_dir,
        macro_file=planned["macro_file"],
        executable=executable,
        geant4_setup=geant4_setup,
        wsl_distro=wsl_distro,
        skip_geant4=skip_geant4,
        no_plots=no_plots,
        allow_validation_errors=allow_validation_errors,
    )
    return {**planned, **executed}


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan or execute the Paper 3 nanocomposite benchmark campaign.")
    parser.add_argument("study_file", help="Input study JSON file")
    parser.add_argument("--build-dir", help="Optional build directory")
    parser.add_argument("--macro-file", help="Optional macro output path")
    parser.add_argument("--executable", default="./ShieldLabG4", help="Geant4 executable to run")
    parser.add_argument("--geant4-setup", help="Optional Geant4 setup script")
    parser.add_argument("--wsl-distro", help="Optional WSL distro name for Geant4 execution")
    parser.add_argument("--dry-run", action="store_true", help="Only validate and emit planning artifacts")
    parser.add_argument("--skip-geant4", action="store_true", help="Skip Geant4 execution after planning")
    parser.add_argument("--no-plots", action="store_true", help="Skip workbook plot generation during execution")
    parser.add_argument(
        "--allow-validation-errors",
        action="store_true",
        help="Proceed even if validation reports errors",
    )
    args = parser.parse_args()

    outputs = run_benchmark(
        args.study_file,
        build_dir=args.build_dir,
        macro_file=args.macro_file,
        executable=args.executable,
        geant4_setup=args.geant4_setup,
        wsl_distro=args.wsl_distro,
        dry_run=args.dry_run,
        skip_geant4=args.skip_geant4,
        no_plots=args.no_plots,
        allow_validation_errors=args.allow_validation_errors,
    )
    serializable = {key: str(value) if isinstance(value, Path) else value for key, value in outputs.items()}
    print(json.dumps(serializable, indent=2))


if __name__ == "__main__":
    main()