from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from shieldlab.core.materials import formula_mixture_to_mass_fractions, resolve_material_mass_fractions
from shieldlab.physics.nist_xcom import get_mac_compound


def _energy_command(source: dict[str, Any]) -> str:
    energy = source.get("energy", 662)
    unit = source.get("energy_unit", "keV")
    return f"/gun/energy {energy} {unit}"


def _energy_unit(source: dict[str, Any]) -> str:
    return source.get("energy_unit", "keV")


def _energy_label(energy: float | int, unit: str) -> str:
    energy_text = str(energy).replace(".", "p")
    return f"E_{energy_text}_{unit}"


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


def _reference_rows(study: dict[str, Any]) -> list[dict[str, Any]]:
    references = study.get("references", {})
    if not isinstance(references, dict):
        return []
    rows = references.get("coefficients", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _reference_linear_attenuation(
    study: dict[str, Any],
    materials_by_name: dict[str, dict[str, Any]],
    energy: float | int,
    unit: str,
) -> float | None:
    for row in _reference_rows(study):
        if float(row.get("energy", math.nan)) != float(energy):
            continue
        if str(row.get("energy_unit", unit)).lower() != str(unit).lower():
            continue
        linear = row.get("linear_attenuation_cm_inv")
        if linear is not None:
            return float(linear)
        mass = row.get("mass_attenuation_cm2_g")
        if mass is None:
            continue
        layers = study.get("geometry", {}).get("layers", [])
        if len(layers) != 1:
            continue
        material = materials_by_name.get(str(layers[0].get("material", "")))
        if material is None:
            continue
        density = float(material.get("density_g_cm3", 0.0))
        if density > 0:
            return float(mass) * density
    return None


def _xcom_linear_attenuation(
    study: dict[str, Any],
    materials_by_name: dict[str, dict[str, Any]],
    energy: float | int,
    unit: str,
) -> float | None:
    layers = study.get("geometry", {}).get("layers", [])
    if len(layers) != 1:
        return None
    material_name = str(layers[0].get("material", ""))
    material = materials_by_name.get(material_name)
    if material is None:
        return None
    density = float(material.get("density_g_cm3", 0.0))
    if density <= 0:
        return None
    mass_fractions = resolve_material_mass_fractions(material)
    if not mass_fractions:
        return None
    try:
        mac, _ = get_mac_compound(mass_fractions, [_energy_to_mev(energy, unit)])
    except Exception:
        return None
    if len(mac) != 1 or not math.isfinite(float(mac[0])):
        return None
    return float(mac[0]) * density


def _benchmark_layer_plan(
    study: dict[str, Any],
    materials_by_name: dict[str, dict[str, Any]],
    energy: float | int,
    unit: str,
) -> list[dict[str, Any]] | None:
    run = study.get("run", {})
    if str(run.get("validation_mode", "")).strip().lower() != "benchmark_narrow_beam":
        return None

    geometry = study.get("geometry", {})
    layers = geometry.get("layers", [])
    total_base_thickness = sum(float(layer.get("thickness_cm", 0.0)) for layer in layers)
    if total_base_thickness <= 0:
        return None

    benchmark = run.get("benchmark_validation", {}) if isinstance(run.get("benchmark_validation", {}), dict) else {}
    target_transmission = float(benchmark.get("target_transmission", 0.65))
    min_thickness_cm = float(benchmark.get("min_total_thickness_cm", 0.001))
    max_thickness_cm = float(benchmark.get("max_total_thickness_cm", max(total_base_thickness, 5.0)))

    if not 0 < target_transmission < 1:
        raise ValueError("benchmark_validation.target_transmission must be between 0 and 1")
    if min_thickness_cm <= 0 or max_thickness_cm <= 0 or min_thickness_cm > max_thickness_cm:
        raise ValueError("benchmark_validation thickness bounds are invalid")

    reference_mu = _reference_linear_attenuation(study, materials_by_name, energy, unit)
    if reference_mu is None:
        reference_mu = _xcom_linear_attenuation(study, materials_by_name, energy, unit)
    if reference_mu is None or reference_mu <= 0:
        return None

    target_total_thickness = -math.log(target_transmission) / reference_mu
    target_total_thickness = min(max(target_total_thickness, min_thickness_cm), max_thickness_cm)
    scale = target_total_thickness / total_base_thickness

    planned_layers: list[dict[str, Any]] = []
    for layer in layers:
        planned_layer = dict(layer)
        planned_layer["thickness_cm"] = float(layer.get("thickness_cm", 0.0)) * scale
        planned_layers.append(planned_layer)
    return planned_layers


def _direction_command(source: dict[str, Any]) -> str:
    direction = source.get("direction", [1, 0, 0])
    if len(direction) != 3:
        raise ValueError("source.direction must contain exactly three values")
    return f"/gun/direction {direction[0]} {direction[1]} {direction[2]}"


def _layer_command(layer: dict[str, Any]) -> str:
    material = layer["material"]
    thickness = layer.get("thickness_cm")
    divisions = layer.get("divisions", 1)
    if thickness is None:
        raise ValueError(f"Layer {material} is missing thickness_cm")
    return f"/shield/geometry/addLayer {material} {thickness} cm {divisions}"


def _material_command(material: dict[str, Any]) -> str:
    name = material["name"]
    density = material["density_g_cm3"]
    fractions = resolve_material_mass_fractions(material)
    components = " ".join(f"{element}:{fraction}" for element, fraction in fractions.items())
    return f"/shield/material/addMassFraction {name} {density} {components}"


def _extract_phase_fractions(material: dict[str, Any]) -> dict[str, float]:
    """Extract compound-formula → unnormalised weight dict for composition sweep."""
    if material.get("formula_mass_fractions"):
        return {f: float(v) for f, v in material["formula_mass_fractions"].items()}
    nc = material.get("nanocomposite")
    if nc:
        phases: dict[str, float] = {nc["matrix"]["formula"]: float(nc["matrix"]["weight_fraction"])}
        for filler in nc.get("fillers") or []:
            phases[filler["formula"]] = phases.get(filler["formula"], 0.0) + float(filler["weight_fraction"])
        return phases
    mx = material.get("mixture")
    if mx:
        phases = {}
        for phase in mx:
            phases[phase["formula"]] = phases.get(phase["formula"], 0.0) + float(phase["weight_fraction"])
        return phases
    vf = material.get("volume_fractions")
    if vf:
        phases = {}
        for phase in vf:
            phases[phase["formula"]] = phases.get(phase["formula"], 0.0) + float(phase["density_g_cm3"]) * float(phase["volume_fraction"])
        return phases
    if material.get("formula"):
        return {str(material["formula"]): 1.0}
    raise ValueError(f"Cannot extract phase fractions for material '{material.get('name', '?')}' — composition sweep requires formula-based composition.")


def _vary_compound_fraction(phase_fractions: dict[str, float], compound: str, step_value: float) -> dict[str, float]:
    """Set one compound to step_value, scale all others proportionally so sum = 1.0."""
    if compound not in phase_fractions:
        raise ValueError(f"Compound '{compound}' not found in material phases: {list(phase_fractions)}")
    remaining_original = sum(v for k, v in phase_fractions.items() if k != compound)
    if remaining_original <= 0:
        raise ValueError(f"Cannot sweep: all composition weight is in compound '{compound}'")
    scale = (1.0 - step_value) / remaining_original
    result = {k: v * scale for k, v in phase_fractions.items() if k != compound}
    result[compound] = step_value
    return result


def macro_from_study(study: dict[str, Any]) -> str:
    source = study.get("source", {})
    materials = study.get("materials", [])
    materials_by_name = {str(material.get("name", "")): material for material in materials}
    geometry = study.get("geometry", {})
    run = study.get("run", {})
    layers = geometry.get("layers", [])
    if not layers:
        raise ValueError("study.geometry.layers must contain at least one layer")

    lines = [
        "/control/verbose 0",
        "/run/verbose 0",
        "/event/verbose 0",
        "/tracking/verbose 0",
        "/process/em/verbose 0",
    ]

    lines.extend(_material_command(material) for material in materials)
    lines.extend([
        "/shield/geometry/clearLayers",
        f"/shield/geometry/transverseSize {geometry.get('transverse_size_cm', 10)} cm",
    ])
    lines.extend(_layer_command(layer) for layer in layers)
    output_dir = run.get("output_dir", "results/study")
    histories = run.get("histories", 10000)
    energy_grid = run.get("energy_grid")
    thickness_grid = run.get("thickness_grid")
    composition_sweep = run.get("composition_sweep")
    unit = _energy_unit(source)

    active_modes = sum([bool(energy_grid), bool(thickness_grid), bool(composition_sweep)])
    if active_modes > 1:
        raise ValueError("study.run can only define one of: energy_grid, thickness_grid, composition_sweep")

    if composition_sweep:
        comp_material_name = composition_sweep["material"]
        compound = composition_sweep["compound"]
        from_wt = float(composition_sweep["from_wt"])
        to_wt = float(composition_sweep["to_wt"])
        n_steps = int(composition_sweep.get("steps", 5))
        target_mat = next((m for m in materials if m.get("name") == comp_material_name), None)
        if target_mat is None:
            raise ValueError(f"composition_sweep.material '{comp_material_name}' not found in study materials")
        base_density = target_mat["density_g_cm3"]
        phase_fractions = _extract_phase_fractions(target_mat)
        step_values = (
            [from_wt + (to_wt - from_wt) * i / (n_steps - 1) for i in range(n_steps)]
            if n_steps > 1 else [from_wt]
        )
        lines.extend(["/run/initialize", f"/gun/particle {source.get('particle', 'gamma')}",
                       _direction_command(source), _energy_command(source)])
        for step_value in step_values:
            label = str(round(step_value, 6)).replace(".", "p")
            step_mat_name = f"{comp_material_name}_{compound}_{label}"
            new_phases = _vary_compound_fraction(phase_fractions, compound, step_value)
            elem_fractions = formula_mixture_to_mass_fractions(new_phases)
            components = " ".join(f"{el}:{frac}" for el, frac in elem_fractions.items())
            lines.extend([
                f"/shield/material/addMassFraction {step_mat_name} {base_density} {components}",
                "/shield/geometry/clearLayers",
                f"/shield/geometry/transverseSize {geometry.get('transverse_size_cm', 10)} cm",
            ])
            for layer in layers:
                layer_mat = step_mat_name if layer["material"] == comp_material_name else layer["material"]
                divs = layer.get("divisions", 1)
                lines.append(f"/shield/geometry/addLayer {layer_mat} {layer['thickness_cm']} cm {divs}")
            lines.extend([
                f"/shield/output/setDirectory {output_dir}/C_{compound}_{label}",
                f"/run/beamOn {histories}",
            ])
    elif thickness_grid:
        # Thickness sweep: one run per thickness, fixed energy
        lines.extend(["/run/initialize", f"/gun/particle {source.get('particle', 'gamma')}", _direction_command(source), _energy_command(source)])
        for thickness_cm in thickness_grid:
            label = str(thickness_cm).replace(".", "p")
            lines.extend(
                [
                    f"/shield/geometry/clearLayers",
                    f"/shield/geometry/transverseSize {geometry.get('transverse_size_cm', 10)} cm",
                ]
            )
            for layer in layers:
                mat = layer["material"]
                divs = layer.get("divisions", 1)
                lines.append(f"/shield/geometry/addLayer {mat} {thickness_cm} cm {divs}")
            lines.extend(
                [
                    f"/shield/output/setDirectory {output_dir}/T_{label}_cm",
                    f"/run/beamOn {histories}",
                ]
            )
    elif energy_grid:
        geometry_type = geometry.get("type", "slab")
        if geometry_type in ("rve_explicit", "rve_multiunion"):
            # ── Regime B / C: fixed explicit-RVE geometry, sweep energy only ──
            rve = geometry.get("rve", {})
            side_nm = float(rve.get("side_nm", 1000))
            lines.extend([
                f"/shield/geometry/mode {geometry_type}",
                f"/shield/rve/matrixMaterial {rve.get('matrix_material', '')}",
                f"/shield/rve/fillerMaterial {rve.get('filler_material', '')}",
                f"/shield/rve/sideLength {int(side_nm)} nm",
                f"/shield/rve/particleRadius {rve.get('particle_radius_nm', 25)} nm",
                f"/shield/rve/volumeFraction {rve.get('volume_fraction', 0.1)}",
                f"/shield/rve/maxParticles {int(rve.get('max_particles', 2000))}",
                f"/shield/rve/seed {int(rve.get('seed', 12345))}",
            ])
            lines.extend([
                "/run/initialize",
                f"/gun/particle {source.get('particle', 'gamma')}",
                _direction_command(source),
            ])
            for energy in energy_grid:
                lines.extend([
                    f"/shield/output/setDirectory {output_dir}/{_energy_label(energy, unit)}",
                    f"/gun/energy {energy} {unit}",
                    f"/run/beamOn {histories}",
                ])
        else:
            # ── Slab: per-energy benchmark geometry adjustment ────────────────
            lines.extend(["/run/initialize", f"/gun/particle {source.get('particle', 'gamma')}", _direction_command(source)])
            for energy in energy_grid:
                planned_layers = _benchmark_layer_plan(study, materials_by_name, energy, unit) or layers
                lines.extend(
                    [
                        f"/shield/geometry/clearLayers",
                        f"/shield/geometry/transverseSize {geometry.get('transverse_size_cm', 10)} cm",
                    ]
                )
                lines.extend(_layer_command(layer) for layer in planned_layers)
                lines.extend(
                    [
                        f"/shield/output/setDirectory {output_dir}/{_energy_label(energy, unit)}",
                        f"/gun/energy {energy} {unit}",
                        f"/run/beamOn {histories}",
                    ]
                )
    else:
        lines.extend(
            [
                "/run/initialize",
                f"/gun/particle {source.get('particle', 'gamma')}",
                _direction_command(source),
                f"/shield/output/setDirectory {output_dir}",
                _energy_command(source),
                f"/run/beamOn {histories}",
            ]
        )
    return "\n".join(lines) + "\n"


def write_macro(study_file: str | Path, output_file: str | Path | None = None) -> Path:
    study_path = Path(study_file)
    with study_path.open("r", encoding="utf-8-sig") as handle:
        study = json.load(handle)

    if output_file is None:
        output_path = study_path.with_suffix(".mac")
    else:
        output_path = Path(output_file)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(macro_from_study(study), encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Geant4 macro from a ShieldLab-G4 study JSON file.")
    parser.add_argument("study_file", help="Input study JSON file")
    parser.add_argument("--output", help="Output macro path")
    args = parser.parse_args()
    print(write_macro(args.study_file, args.output))


if __name__ == "__main__":
    main()