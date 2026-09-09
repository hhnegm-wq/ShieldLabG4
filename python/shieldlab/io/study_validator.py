from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from shieldlab.core.materials import (
    _ALL_COMPOSITION_MODES,
    formula_mixture_to_mass_fractions,
    formula_to_mass_fractions,
    mixture_to_mass_fractions,
    nanocomposite_to_mass_fractions,
    volume_fractions_to_mass_fractions,
)
from shieldlab.io.schema import STUDY_SCHEMA_VERSION


SUPPORTED_VALIDATION_MODES = {
    "benchmark_narrow_beam",
    "benchmark_broad_beam",
    "screening",
    "none",
}

SUPPORTED_REFERENCE_COMPARISON_MODES = {
    "none",
    "attenuation_coefficients",
    "buildup_overlay",
    "full",
}


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    path: str
    message: str


def _issue(severity: str, path: str, message: str) -> ValidationIssue:
    return ValidationIssue(severity=severity, path=path, message=message)


def _is_positive_number(value: Any) -> bool:
    return isinstance(value, int | float) and value > 0


def _fraction_sum(fractions: dict[str, Any]) -> float:
    return sum(float(value) for value in fractions.values())


def _validate_material(material: dict[str, Any], index: int) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    path = f"materials[{index}]"
    name = material.get("name")
    if not isinstance(name, str) or not name:
        issues.append(_issue("error", f"{path}.name", "Material name is required."))

    density = material.get("density_g_cm3")
    if not _is_positive_number(density):
        issues.append(_issue("error", f"{path}.density_g_cm3", "Material density must be a positive number."))
    elif density < 0.001 or density > 30:
        issues.append(_issue("warning", f"{path}.density_g_cm3", "Material density is outside the usual shielding-material range."))
    else:
        phase = str(material.get("phase", "solid")).strip().lower()
        if phase != "gas" and density < 0.2:
            issues.append(
                _issue(
                    "warning",
                    f"{path}.density_g_cm3",
                    "Density is unusually low for non-gas shielding material. Review composition and units.",
                )
            )
        if phase == "gas" and density > 0.05:
            issues.append(
                _issue(
                    "warning",
                    f"{path}.density_g_cm3",
                    "Gas phase with high density looks physically implausible. Review phase or density units.",
                )
            )

        formula = str(material.get("formula", "")).upper()
        heavy_markers = ("PB", "BI", "W", "U", "TH", "BA")
        if formula and any(marker in formula for marker in heavy_markers) and density < 2.0:
            issues.append(
                _issue(
                    "warning",
                    f"{path}.density_g_cm3",
                    "Heavy-element formula with very low density is outside typical plausibility envelopes.",
                )
            )

    modes = [key for key in _ALL_COMPOSITION_MODES if material.get(key)]
    if len(modes) == 0:
        issues.append(
            _issue(
                "error",
                path,
                f"Material must define one composition mode: {', '.join(_ALL_COMPOSITION_MODES)}.",
            )
        )
    elif len(modes) > 1:
        issues.append(_issue("error", path, f"Material defines multiple composition modes: {', '.join(modes)}."))

    if material.get("mass_fractions"):
        fractions = material["mass_fractions"]
        if not isinstance(fractions, dict):
            issues.append(_issue("error", f"{path}.mass_fractions", "mass_fractions must be an object."))
        else:
            try:
                total = _fraction_sum(fractions)
                if any(float(value) <= 0 for value in fractions.values()):
                    issues.append(_issue("error", f"{path}.mass_fractions", "All mass fractions must be positive."))
                if abs(total - 1.0) > 1.0e-6:
                    issues.append(_issue("error", f"{path}.mass_fractions", f"Mass fractions must sum to 1.0; found {total:.8g}."))
            except (TypeError, ValueError):
                issues.append(_issue("error", f"{path}.mass_fractions", "Mass fractions must be numeric."))

    if material.get("formula"):
        try:
            formula_to_mass_fractions(str(material["formula"]))
        except ValueError as exc:
            issues.append(_issue("error", f"{path}.formula", str(exc)))

    if material.get("formula_mass_fractions"):
        fractions = material["formula_mass_fractions"]
        if not isinstance(fractions, dict):
            issues.append(_issue("error", f"{path}.formula_mass_fractions", "formula_mass_fractions must be an object."))
        else:
            try:
                if any(float(value) <= 0 for value in fractions.values()):
                    issues.append(_issue("error", f"{path}.formula_mass_fractions", "All formula mixture fractions must be positive."))
                total = _fraction_sum(fractions)
                if abs(total - 1.0) > 1.0e-6:
                    issues.append(
                        _issue(
                            "warning",
                            f"{path}.formula_mass_fractions",
                            f"Formula mixture fractions sum to {total:.8g}; they will be normalized before Geant4 material creation.",
                        )
                    )
                formula_mixture_to_mass_fractions(fractions)
            except (TypeError, ValueError) as exc:
                issues.append(_issue("error", f"{path}.formula_mass_fractions", str(exc)))

    if material.get("nanocomposite"):
        nc = material["nanocomposite"]
        if not isinstance(nc, dict):
            issues.append(_issue("error", f"{path}.nanocomposite", "nanocomposite must be an object with 'matrix' and optional 'fillers'."))
        else:
            matrix = nc.get("matrix")
            fillers = nc.get("fillers") or []
            if not isinstance(matrix, dict) or not matrix.get("formula") or "weight_fraction" not in matrix:
                issues.append(_issue("error", f"{path}.nanocomposite.matrix", "nanocomposite.matrix must have 'formula' and 'weight_fraction'."))
            if not isinstance(fillers, list):
                issues.append(_issue("error", f"{path}.nanocomposite.fillers", "nanocomposite.fillers must be a list."))
            else:
                for idx, filler in enumerate(fillers):
                    if not isinstance(filler, dict) or not filler.get("formula") or "weight_fraction" not in filler:
                        issues.append(_issue("error", f"{path}.nanocomposite.fillers[{idx}]", "Each filler must have 'formula' and 'weight_fraction'."))
            try:
                m_wf = float(matrix.get("weight_fraction", 0)) if isinstance(matrix, dict) else 0.0
                f_wf = sum(float(f.get("weight_fraction", 0)) for f in fillers) if isinstance(fillers, list) else 0.0
                total = m_wf + f_wf
                if abs(total - 1.0) > 0.01:
                    issues.append(_issue("warning", f"{path}.nanocomposite", f"Matrix + filler weight fractions sum to {total:.4f}; they will be normalised."))
                if isinstance(matrix, dict) and isinstance(fillers, list):
                    nanocomposite_to_mass_fractions(matrix, fillers)
            except (TypeError, ValueError, KeyError) as exc:
                issues.append(_issue("error", f"{path}.nanocomposite", str(exc)))

    if material.get("volume_fractions"):
        vf = material["volume_fractions"]
        if not isinstance(vf, list) or not vf:
            issues.append(_issue("error", f"{path}.volume_fractions", "volume_fractions must be a non-empty list."))
        else:
            for idx, phase in enumerate(vf):
                pp = f"{path}.volume_fractions[{idx}]"
                if not isinstance(phase, dict):
                    issues.append(_issue("error", pp, "Each volume-fraction phase must be an object."))
                    continue
                if not phase.get("formula"):
                    issues.append(_issue("error", f"{pp}.formula", "Volume-fraction phase must have a 'formula'."))
                if not _is_positive_number(phase.get("density_g_cm3")):
                    issues.append(_issue("error", f"{pp}.density_g_cm3", "Phase density must be a positive number."))
                if not _is_positive_number(phase.get("volume_fraction")):
                    issues.append(_issue("error", f"{pp}.volume_fraction", "volume_fraction must be a positive number."))
            try:
                total_vf = sum(float(p.get("volume_fraction", 0)) for p in vf)
                if abs(total_vf - 1.0) > 0.01:
                    issues.append(_issue("warning", f"{path}.volume_fractions", f"Volume fractions sum to {total_vf:.4f}; they will be normalised."))
                volume_fractions_to_mass_fractions(vf)
            except (TypeError, ValueError, KeyError) as exc:
                issues.append(_issue("error", f"{path}.volume_fractions", str(exc)))

    if material.get("mixture"):
        mx = material["mixture"]
        if not isinstance(mx, list) or not mx:
            issues.append(_issue("error", f"{path}.mixture", "mixture must be a non-empty list."))
        else:
            for idx, phase in enumerate(mx):
                pp = f"{path}.mixture[{idx}]"
                if not isinstance(phase, dict):
                    issues.append(_issue("error", pp, "Each mixture phase must be an object."))
                    continue
                if not phase.get("formula"):
                    issues.append(_issue("error", f"{pp}.formula", "Mixture phase must have a 'formula'."))
                if not _is_positive_number(phase.get("weight_fraction")):
                    issues.append(_issue("error", f"{pp}.weight_fraction", "'weight_fraction' must be a positive number."))
            try:
                total_wf = sum(float(p.get("weight_fraction", 0)) for p in mx)
                if abs(total_wf - 1.0) > 0.01:
                    issues.append(_issue("warning", f"{path}.mixture", f"Mixture weight fractions sum to {total_wf:.4f}; they will be normalised."))
                mixture_to_mass_fractions(mx)
            except (TypeError, ValueError, KeyError) as exc:
                issues.append(_issue("error", f"{path}.mixture", str(exc)))

    return issues


def validate_study(study: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    schema_version = study.get("study_schema_version")
    if schema_version is None:
        issues.append(
            _issue(
                "warning",
                "study_schema_version",
                f"study_schema_version is missing. Add study_schema_version='{STUDY_SCHEMA_VERSION}' for reproducible validation.",
            )
        )
    elif str(schema_version) != STUDY_SCHEMA_VERSION:
        issues.append(
            _issue(
                "warning",
                "study_schema_version",
                f"Study schema version '{schema_version}' differs from supported '{STUDY_SCHEMA_VERSION}'.",
            )
        )

    materials = study.get("materials", [])
    if not isinstance(materials, list):
        issues.append(_issue("error", "materials", "materials must be a list."))
        materials = []

    material_names: set[str] = set()
    duplicates: set[str] = set()
    for index, material in enumerate(materials):
        if not isinstance(material, dict):
            issues.append(_issue("error", f"materials[{index}]", "Each material entry must be an object."))
            continue
        name = material.get("name")
        if isinstance(name, str) and name:
            if name in material_names:
                duplicates.add(name)
            material_names.add(name)
        issues.extend(_validate_material(material, index))
    for duplicate in sorted(duplicates):
        issues.append(_issue("error", "materials", f"Duplicate material name: {duplicate}."))

    geometry = study.get("geometry", {})
    if not isinstance(geometry, dict):
        issues.append(_issue("error", "geometry", "geometry must be an object."))
        geometry = {}
    layers = geometry.get("layers", [])
    if not isinstance(layers, list) or not layers:
        issues.append(_issue("error", "geometry.layers", "At least one geometry layer is required."))
        layers = []
    if "transverse_size_cm" in geometry and not _is_positive_number(geometry["transverse_size_cm"]):
        issues.append(_issue("error", "geometry.transverse_size_cm", "Transverse size must be a positive number."))

    for index, layer in enumerate(layers):
        path = f"geometry.layers[{index}]"
        if not isinstance(layer, dict):
            issues.append(_issue("error", path, "Each layer must be an object."))
            continue
        material = layer.get("material")
        if not isinstance(material, str) or not material:
            issues.append(_issue("error", f"{path}.material", "Layer material is required."))
        elif not material.startswith("G4_") and material not in material_names:
            issues.append(_issue("error", f"{path}.material", f"Layer references undefined material: {material}."))
        if not _is_positive_number(layer.get("thickness_cm")):
            issues.append(_issue("error", f"{path}.thickness_cm", "Layer thickness must be a positive number."))
        elif float(layer.get("thickness_cm")) > 1000.0:
            issues.append(_issue("warning", f"{path}.thickness_cm", "Layer thickness is unusually large for standard shielding studies."))
        divisions = layer.get("divisions", 1)
        if not isinstance(divisions, int) or divisions <= 0:
            issues.append(_issue("error", f"{path}.divisions", "Layer divisions must be a positive integer."))

    source = study.get("source", {})
    if not isinstance(source, dict):
        issues.append(_issue("error", "source", "source must be an object."))
        source = {}
    if "direction" in source:
        direction = source["direction"]
        if not isinstance(direction, list) or len(direction) != 3:
            issues.append(_issue("error", "source.direction", "Source direction must contain exactly three values."))
        else:
            try:
                if sum(float(value) ** 2 for value in direction) <= 0:
                    issues.append(_issue("error", "source.direction", "Source direction vector must be non-zero."))
            except (TypeError, ValueError):
                issues.append(_issue("error", "source.direction", "Source direction values must be numeric."))
    if "energy" in source and not _is_positive_number(source["energy"]):
        issues.append(_issue("error", "source.energy", "Source energy must be a positive number."))

    run = study.get("run", {})
    if not isinstance(run, dict):
        issues.append(_issue("error", "run", "run must be an object."))
        run = {}
    if not isinstance(run.get("histories", 10000), int) or run.get("histories", 10000) <= 0:
        issues.append(_issue("error", "run.histories", "Run histories must be a positive integer."))
    elif int(run.get("histories", 10000)) < 1000:
        issues.append(_issue("warning", "run.histories", "Histories < 1000 may be too low for stable uncertainty estimation."))

    validation_mode = str(run.get("validation_mode", "none")) if run.get("validation_mode") is not None else "none"
    if validation_mode not in SUPPORTED_VALIDATION_MODES:
        issues.append(
            _issue(
                "warning",
                "run.validation_mode",
                f"Unsupported validation_mode '{validation_mode}'. Supported modes: {sorted(SUPPORTED_VALIDATION_MODES)}.",
            )
        )
    energy_grid = run.get("energy_grid")
    thickness_grid = run.get("thickness_grid")
    composition_sweep = run.get("composition_sweep")
    active_sweep_modes = sum([bool(energy_grid), bool(thickness_grid), bool(composition_sweep)])
    if active_sweep_modes > 1:
        issues.append(_issue("error", "run", "run can only define one of: energy_grid, thickness_grid, composition_sweep."))
    if energy_grid is not None:
        if not isinstance(energy_grid, list) or not energy_grid:
            issues.append(_issue("error", "run.energy_grid", "Energy grid must be a non-empty list."))
        else:
            for index, energy in enumerate(energy_grid):
                if not _is_positive_number(energy):
                    issues.append(_issue("error", f"run.energy_grid[{index}]", "Energy-grid values must be positive numbers."))
    if thickness_grid is not None:
        if not isinstance(thickness_grid, list) or not thickness_grid:
            issues.append(_issue("error", "run.thickness_grid", "Thickness grid must be a non-empty list."))
        else:
            for index, thickness in enumerate(thickness_grid):
                if not _is_positive_number(thickness):
                    issues.append(_issue("error", f"run.thickness_grid[{index}]", "Thickness-grid values must be positive numbers."))
    if composition_sweep is not None:
        if not isinstance(composition_sweep, dict):
            issues.append(_issue("error", "run.composition_sweep", "composition_sweep must be an object."))
        else:
            cs_mat = composition_sweep.get("material")
            cs_cmp = composition_sweep.get("compound")
            material_names_local = {m.get("name") for m in study.get("materials", []) if isinstance(m, dict)}
            if not isinstance(cs_mat, str) or not cs_mat:
                issues.append(_issue("error", "run.composition_sweep.material", "composition_sweep.material must be a non-empty string."))
            elif cs_mat not in material_names_local:
                issues.append(_issue("error", "run.composition_sweep.material", f"composition_sweep.material '{cs_mat}' is not defined in study materials."))
            if not isinstance(cs_cmp, str) or not cs_cmp:
                issues.append(_issue("error", "run.composition_sweep.compound", "composition_sweep.compound must be a non-empty formula string."))
            if not _is_positive_number(composition_sweep.get("from_wt")):
                issues.append(_issue("error", "run.composition_sweep.from_wt", "from_wt must be a positive number."))
            if not _is_positive_number(composition_sweep.get("to_wt")):
                issues.append(_issue("error", "run.composition_sweep.to_wt", "to_wt must be a positive number."))
            steps = composition_sweep.get("steps", 5)
            if not isinstance(steps, int) or steps < 2:
                issues.append(_issue("error", "run.composition_sweep.steps", "steps must be an integer >= 2."))
            from_wt = composition_sweep.get("from_wt")
            to_wt = composition_sweep.get("to_wt")
            if _is_positive_number(from_wt) and _is_positive_number(to_wt) and float(to_wt) <= float(from_wt):
                issues.append(_issue("error", "run.composition_sweep", "to_wt must be greater than from_wt."))
            if _is_positive_number(to_wt) and float(to_wt) >= 1.0:
                issues.append(_issue("error", "run.composition_sweep.to_wt", "to_wt must be < 1.0 (weight fraction)."))

    references = study.get("references", {})
    if references:
        coefficient_rows = references.get("coefficients", []) if isinstance(references, dict) else []
        if not isinstance(coefficient_rows, list):
            issues.append(_issue("error", "references.coefficients", "Reference coefficients must be a list."))
        for index, row in enumerate(coefficient_rows):
            path = f"references.coefficients[{index}]"
            if not isinstance(row, dict):
                issues.append(_issue("error", path, "Each reference coefficient row must be an object."))
                continue
            if not _is_positive_number(row.get("energy")):
                issues.append(_issue("error", f"{path}.energy", "Reference energy must be a positive number."))
            if not row.get("linear_attenuation_cm_inv") and not row.get("mass_attenuation_cm2_g"):
                issues.append(
                    _issue(
                        "warning",
                        path,
                        "Reference row has no linear_attenuation_cm_inv or mass_attenuation_cm2_g value.",
                    )
                )

        buildup = references.get("buildup_factors", {}) if isinstance(references, dict) else {}
        if buildup and not isinstance(buildup, dict):
            issues.append(_issue("error", "references.buildup_factors", "buildup_factors must be an object."))
        elif isinstance(buildup, dict):
            coeff_rows = buildup.get("coefficients", [])
            if coeff_rows and not isinstance(coeff_rows, list):
                issues.append(_issue("error", "references.buildup_factors.coefficients", "Buildup coefficient rows must be a list."))
            for index, row in enumerate(coeff_rows if isinstance(coeff_rows, list) else []):
                path = f"references.buildup_factors.coefficients[{index}]"
                if not isinstance(row, dict):
                    issues.append(_issue("error", path, "Each buildup coefficient row must be an object."))
                    continue
                if not _is_positive_number(row.get("energy")):
                    issues.append(_issue("error", f"{path}.energy", "Buildup energy must be a positive number."))
                if not _is_positive_number(row.get("zeq")):
                    issues.append(_issue("warning", f"{path}.zeq", "Buildup row is missing a positive Zeq value."))
                for block_name in ("ebf", "eabf"):
                    params = row.get(block_name, {})
                    if not isinstance(params, dict):
                        issues.append(_issue("error", f"{path}.{block_name}", f"{block_name} must be an object with a, b, c, d, xk."))
                        continue
                    for param in ("a", "b", "c", "d", "xk"):
                        if param not in params:
                            issues.append(_issue("error", f"{path}.{block_name}.{param}", f"Missing {block_name}.{param} coefficient."))
                        else:
                            try:
                                float(params[param])
                            except (TypeError, ValueError):
                                issues.append(_issue("error", f"{path}.{block_name}.{param}", f"{block_name}.{param} must be numeric."))

        acceptance = references.get("acceptance_criteria", {}) if isinstance(references, dict) else {}
        if acceptance and not isinstance(acceptance, dict):
            issues.append(_issue("error", "references.acceptance_criteria", "acceptance_criteria must be an object."))
        elif isinstance(acceptance, dict):
            metrics = acceptance.get("metrics", {})
            if metrics and not isinstance(metrics, dict):
                issues.append(_issue("error", "references.acceptance_criteria.metrics", "metrics must be an object."))
            for metric_name, rules in (metrics.items() if isinstance(metrics, dict) else []):
                metric_path = f"references.acceptance_criteria.metrics.{metric_name}"
                if not isinstance(rules, dict):
                    issues.append(_issue("error", metric_path, "Metric acceptance rules must be an object."))
                    continue
                for field in ("mean_abs_max", "max_abs_max"):
                    if field in rules:
                        try:
                            if float(rules[field]) < 0:
                                issues.append(_issue("error", f"{metric_path}.{field}", f"{field} must be >= 0."))
                        except (TypeError, ValueError):
                            issues.append(_issue("error", f"{metric_path}.{field}", f"{field} must be numeric."))

        comparison_mode = references.get("comparison_mode") if isinstance(references, dict) else None
        if comparison_mode is not None:
            comparison_mode = str(comparison_mode)
            if comparison_mode not in SUPPORTED_REFERENCE_COMPARISON_MODES:
                issues.append(
                    _issue(
                        "warning",
                        "references.comparison_mode",
                        f"Unsupported comparison_mode '{comparison_mode}'. Supported modes: {sorted(SUPPORTED_REFERENCE_COMPARISON_MODES)}.",
                    )
                )
            elif comparison_mode in {"attenuation_coefficients", "full"} and not references.get("coefficients"):
                issues.append(
                    _issue(
                        "warning",
                        "references.comparison_mode",
                        "comparison_mode requires reference coefficients, but references.coefficients is empty.",
                    )
                )
            elif comparison_mode in {"buildup_overlay", "full"}:
                buildup = references.get("buildup_factors", {}) if isinstance(references.get("buildup_factors", {}), dict) else {}
                if not buildup.get("coefficients"):
                    issues.append(
                        _issue(
                            "warning",
                            "references.comparison_mode",
                            "comparison_mode requires buildup coefficients, but references.buildup_factors.coefficients is empty.",
                        )
                    )

    # Impossible or unstable regime checks for gamma shielding runs.
    source = study.get("source", {}) if isinstance(study.get("source", {}), dict) else {}
    particle = str(source.get("particle", "gamma")).strip().lower()
    source_unit = str(source.get("energy_unit", "keV")).strip().lower()
    energy_grid = run.get("energy_grid") if isinstance(run.get("energy_grid"), list) else []
    total_thickness_cm = 0.0
    try:
        total_thickness_cm = float(sum(float(layer.get("thickness_cm", 0.0)) for layer in layers if isinstance(layer, dict)))
    except (TypeError, ValueError):
        total_thickness_cm = 0.0

    def _to_kev(value: float, unit: str) -> float:
        if unit == "kev":
            return value
        if unit == "mev":
            return value * 1000.0
        if unit == "ev":
            return value / 1000.0
        if unit == "gev":
            return value * 1_000_000.0
        return value

    energy_candidates: list[float] = []
    if _is_positive_number(source.get("energy")):
        energy_candidates.append(_to_kev(float(source.get("energy")), source_unit))
    for energy in energy_grid:
        if _is_positive_number(energy):
            energy_candidates.append(_to_kev(float(energy), source_unit))

    if particle == "gamma" and energy_candidates:
        min_energy_kev = min(energy_candidates)
        max_energy_kev = max(energy_candidates)
        if total_thickness_cm > 100.0 and min_energy_kev <= 20.0:
            issues.append(
                _issue(
                    "warning",
                    "run.energy_grid",
                    "Very thick shield with very low photon energies may produce numerically saturated transmission (near zero).",
                )
            )
        if total_thickness_cm < 0.01 and max_energy_kev >= 5000.0:
            issues.append(
                _issue(
                    "warning",
                    "run.energy_grid",
                    "Extremely thin shield at very high energies may be physically uninformative for attenuation benchmarks.",
                )
            )

    if validation_mode.startswith("benchmark") and isinstance(references, dict):
        has_any_reference = bool(references.get("coefficients")) or bool((references.get("buildup_factors") or {}).get("coefficients"))
        if not has_any_reference:
            issues.append(
                _issue(
                    "warning",
                    "run.validation_mode",
                    "Benchmark validation mode is selected but no reference coefficients/buildup tables are provided.",
                )
            )

    return issues


def validate_study_file(study_file: str | Path) -> list[ValidationIssue]:
    with Path(study_file).open("r", encoding="utf-8-sig") as handle:
        return validate_study(json.load(handle))


def issues_to_frame(issues: list[ValidationIssue]) -> pd.DataFrame:
    return pd.DataFrame([asdict(issue) for issue in issues], columns=["severity", "path", "message"])


def write_validation_report(issues: list[ValidationIssue], output_file: str | Path) -> Path:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    issues_to_frame(issues).to_csv(output_path, index=False)
    return output_path


def has_errors(issues: list[ValidationIssue]) -> bool:
    return any(issue.severity == "error" for issue in issues)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a ShieldLab-G4 study JSON file.")
    parser.add_argument("study_file", help="Input study JSON file")
    parser.add_argument("--output", help="Optional CSV validation report path")
    args = parser.parse_args()

    issues = validate_study_file(args.study_file)
    if args.output:
        print(write_validation_report(issues, args.output))
    if issues:
        print(issues_to_frame(issues).to_string(index=False))
    else:
        print("No validation issues found.")
    raise SystemExit(1 if has_errors(issues) else 0)


if __name__ == "__main__":
    main()