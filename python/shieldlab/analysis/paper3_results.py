from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from shieldlab.analysis.comparison import compare_coefficients
from shieldlab.analysis.runtime_benchmarks import summarize_reference_comparison
from shieldlab.core.materials import resolve_material_mass_fractions
from shieldlab.physics.nist_xcom import get_mac_compound
from shieldlab.viz.paper3_figures import generate_regime_a_figures


DEFAULT_PAPER3_ACCEPTANCE = {
    "metrics": {
        "mass_attenuation_cm2_g_percent_difference": {
            "mean_abs_max": 1.5,
            "max_abs_max": 5.0,
        },
        "linear_attenuation_cm_inv_percent_difference": {
            "mean_abs_max": 1.5,
            "max_abs_max": 5.0,
        },
    }
}

_ENERGY_DIR_PATTERN = re.compile(r"^E_(?P<energy>.+)_(?P<unit>[A-Za-z]+)$")


def _load_study(study_file: str | Path) -> dict[str, Any]:
    with Path(study_file).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _load_sweep(result_dir: str | Path) -> pd.DataFrame:
    sweep_file = Path(result_dir) / "sweep_summary.csv"
    if not sweep_file.exists():
        raise FileNotFoundError(f"Missing sweep summary: {sweep_file}")
    return pd.read_csv(sweep_file)


def _parse_energy_dir(run_dir: Path) -> tuple[float, str] | None:
    match = _ENERGY_DIR_PATTERN.match(run_dir.name)
    if not match:
        return None
    energy_text = match.group("energy").replace("p", ".")
    return float(energy_text), match.group("unit")


def collect_downstream_spectrum(result_dir: str | Path) -> Path | None:
    result_path = Path(result_dir)
    rows: list[pd.DataFrame] = []
    for run_dir in sorted(path for path in result_path.iterdir() if path.is_dir()):
        parsed = _parse_energy_dir(run_dir)
        if parsed is None:
            continue
        energy, unit = parsed
        spectrum_file = run_dir / "downstream_spectrum.csv"
        if not spectrum_file.exists():
            continue
        frame = pd.read_csv(spectrum_file)
        frame["incident_energy"] = energy
        frame["incident_energy_unit"] = unit
        rows.append(frame)

    if not rows:
        return None

    spectrum_summary = pd.concat(rows, ignore_index=True)
    output_file = result_path / "downstream_spectrum_summary.csv"
    spectrum_summary.to_csv(output_file, index=False)
    return output_file


def _update_validation_summary(
    result_dir: Path,
    benchmark_summary: dict[str, Any],
    outputs: dict[str, Path],
) -> None:
    validation_file = result_dir / "validation_summary.json"
    if not validation_file.exists():
        return

    try:
        payload = json.loads(validation_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return

    payload["reference_comparison_exists"] = outputs["reference_comparison"].exists()
    payload["benchmark_summary"] = benchmark_summary
    payload["benchmark_status"] = benchmark_summary.get("status", "unavailable")
    payload["figures"] = sorted(path.name for path in (result_dir / "figures").glob("*.png"))
    if "downstream_spectrum_summary" in outputs:
        payload["downstream_spectrum_summary"] = str(outputs["downstream_spectrum_summary"])

    validation_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _energy_to_mev(energy: float | int, unit: str) -> float:
    unit_key = str(unit).strip().lower()
    value = float(energy)
    if unit_key == "ev":
        return value * 1e-6
    if unit_key == "kev":
        return value * 1e-3
    if unit_key == "mev":
        return value
    if unit_key == "gev":
        return value * 1e3
    raise ValueError(f"Unsupported energy unit '{unit}'")


def build_reference_coefficients(study_file: str | Path) -> pd.DataFrame:
    study = _load_study(study_file)
    run = study.get("run", {}) if isinstance(study.get("run", {}), dict) else {}
    source = study.get("source", {}) if isinstance(study.get("source", {}), dict) else {}
    geometry = study.get("geometry", {}) if isinstance(study.get("geometry", {}), dict) else {}
    layers = geometry.get("layers", []) if isinstance(geometry.get("layers", []), list) else []
    materials = {
        str(material.get("name", "")): material
        for material in (study.get("materials", []) if isinstance(study.get("materials", []), list) else [])
        if isinstance(material, dict) and material.get("name")
    }
    if len(layers) != 1:
        raise ValueError("Paper 3 regime-A reference generation expects exactly one slab layer.")

    layer = layers[0]
    material_name = str(layer.get("material", ""))
    material = materials.get(material_name)
    if material is None:
        raise ValueError(f"Layer material '{material_name}' was not found in study materials.")

    density = float(material.get("density_g_cm3", 0.0))
    if density <= 0:
        raise ValueError(f"Material '{material_name}' must define a positive density_g_cm3.")

    energy_grid = run.get("energy_grid")
    if not isinstance(energy_grid, list) or not energy_grid:
        raise ValueError("Paper 3 reference generation expects run.energy_grid to be a non-empty list.")

    energy_unit = str(source.get("energy_unit", "keV"))
    mass_fractions = resolve_material_mass_fractions(material)
    energies_mev = [_energy_to_mev(energy, energy_unit) for energy in energy_grid]
    mac_values, _ = get_mac_compound(mass_fractions, energies_mev)

    rows = []
    for energy, mac in zip(energy_grid, mac_values, strict=True):
        rows.append(
            {
                "energy": float(energy),
                "energy_unit": energy_unit,
                "source": "nist_xcom",
                "linear_attenuation_cm_inv": float(mac) * density,
                "mass_attenuation_cm2_g": float(mac),
            }
        )
    return pd.DataFrame(rows)


def build_result_pack(
    study_file: str | Path,
    result_dir: str | Path,
    *,
    acceptance: dict[str, Any] | None = None,
    with_figures: bool = False,
) -> dict[str, Path]:
    result_path = Path(result_dir)
    result_path.mkdir(parents=True, exist_ok=True)

    sweep = _load_sweep(result_path)
    reference = build_reference_coefficients(study_file)
    reference_file = result_path / "reference_coefficients.csv"
    reference.to_csv(reference_file, index=False)

    comparison = compare_coefficients(sweep, reference)
    comparison_file = result_path / "reference_comparison.csv"
    comparison.to_csv(comparison_file, index=False)

    applied_acceptance = acceptance or DEFAULT_PAPER3_ACCEPTANCE
    benchmark_summary = summarize_reference_comparison(comparison, applied_acceptance)

    acceptance_payload = {
        "schema_version": "1.0",
        "study_file": str(study_file),
        "result_dir": str(result_path),
        "acceptance": applied_acceptance,
        "benchmark_summary": benchmark_summary,
    }
    acceptance_file = result_path / "paper3_acceptance.json"
    acceptance_file.write_text(json.dumps(acceptance_payload, indent=2), encoding="utf-8")

    spectrum_summary = collect_downstream_spectrum(result_path)

    outputs = {
        "reference_coefficients": reference_file,
        "reference_comparison": comparison_file,
        "acceptance": acceptance_file,
    }
    if spectrum_summary is not None:
        outputs["downstream_spectrum_summary"] = spectrum_summary
    if with_figures:
        outputs.update(generate_regime_a_figures(result_path))
    _update_validation_summary(result_path, benchmark_summary, outputs)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Paper 3 result artifacts from an existing regime-A sweep.")
    parser.add_argument("study_file", help="Paper 3 study JSON file")
    parser.add_argument("result_dir", help="Result directory containing sweep_summary.csv")
    parser.add_argument("--with-figures", action="store_true", help="Generate baseline Paper 3 figures")
    args = parser.parse_args()

    outputs = build_result_pack(args.study_file, args.result_dir, with_figures=args.with_figures)
    serializable = {key: str(value) for key, value in outputs.items()}
    print(json.dumps(serializable, indent=2))


if __name__ == "__main__":
    main()