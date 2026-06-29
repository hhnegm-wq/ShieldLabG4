from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


def _parse_energy(folder_name: str) -> tuple[float | None, str | None]:
    if not folder_name.startswith("E_"):
        return None, None
    parts = folder_name[2:].rsplit("_", 1)
    if len(parts) != 2:
        return None, None
    value = parts[0].replace("p", ".")
    try:
        return float(value), parts[1]
    except ValueError:
        return None, None


def _energy_to_mev(value: float, unit: str) -> float:
    unit_l = unit.lower()
    if unit_l == "mev":
        return value
    if unit_l == "kev":
        return value / 1000.0
    if unit_l == "ev":
        return value / 1.0e6
    if unit_l == "gev":
        return value * 1000.0
    return math.nan


def collect_buildup_observable(result_dir: str | Path, output_file: str | Path | None = None) -> Path:
    """Collect a preliminary simulation-side buildup observable from downstream secondaries.

    This is a first-stage Monte Carlo observable, not a strict broad-beam buildup factor.
    It provides energy-wise secondary-yield indicators that can be compared against
    literature buildup trends while full detector-response buildup scoring is developed.
    """

    result_path = Path(result_dir)
    rows: list[dict[str, float | int | str]] = []

    for run_dir in sorted(path for path in result_path.iterdir() if path.is_dir()):
        energy, unit = _parse_energy(run_dir.name)
        if energy is None or unit is None:
            continue

        run_summary_path = run_dir / "run_summary.csv"
        secondary_path = run_dir / "secondary_tally.csv"
        lcns5_path = run_dir / "lcns5_buildup_observable.csv"
        if not run_summary_path.exists() or (not secondary_path.exists() and not lcns5_path.exists()):
            continue

        run_summary = pd.read_csv(run_summary_path).iloc[0].to_dict()
        secondaries = pd.read_csv(secondary_path) if secondary_path.exists() else pd.DataFrame()
        lcns5 = pd.read_csv(lcns5_path).iloc[0].to_dict() if lcns5_path.exists() else {}

        events = int(run_summary.get("events", 0) or 0)
        transmission = float(run_summary.get("transmission_fraction", 0.0) or 0.0)
        linear_mu = float(run_summary.get("linear_attenuation_cm_inv", math.nan) or math.nan)
        total_thickness = float(run_summary.get("total_thickness_cm", math.nan) or math.nan)

        if lcns5:
            count_per_event = float(lcns5.get("secondary_count_per_primary_event", 0.0) or 0.0)
            secondary_energy_per_event = float(lcns5.get("secondary_energy_per_primary_event_MeV", 0.0) or 0.0)
            species_count = int(secondaries.shape[0]) if not secondaries.empty else 0
            strict_count = float(lcns5.get("mc_buildup_observable_count", math.nan) or math.nan)
            strict_energy = float(lcns5.get("mc_buildup_observable_energy", math.nan) or math.nan)
        else:
            count_per_event = float(secondaries.get("count_per_primary_event", pd.Series(dtype=float)).sum()) if not secondaries.empty else 0.0
            total_secondary_energy = float(secondaries.get("total_kinetic_energy_MeV", pd.Series(dtype=float)).sum()) if not secondaries.empty else 0.0
            secondary_energy_per_event = total_secondary_energy / events if events > 0 else 0.0
            species_count = int(secondaries.shape[0])
            strict_count = math.nan
            strict_energy = math.nan

        source_energy_mev = _energy_to_mev(float(energy), str(unit))
        energy_ratio = (
            secondary_energy_per_event / source_energy_mev
            if events > 0 and math.isfinite(source_energy_mev) and source_energy_mev > 0
            else math.nan
        )

        rows.append(
            {
                "energy": float(energy),
                "energy_unit": str(unit),
                "events": events,
                "transmission_fraction": transmission,
                "total_thickness_cm": total_thickness,
                "linear_attenuation_cm_inv": linear_mu,
                "downstream_secondary_species": species_count,
                "downstream_secondary_count_per_event": count_per_event,
                "downstream_secondary_energy_per_event_MeV": secondary_energy_per_event,
                "mc_buildup_observable_count": strict_count if math.isfinite(strict_count) else (1.0 + count_per_event),
                "mc_buildup_observable_energy": strict_energy if math.isfinite(strict_energy) else (1.0 + (energy_ratio if math.isfinite(energy_ratio) else 0.0)),
            }
        )

    if not rows:
        raise ValueError(f"No E_* result folders with lcns5_buildup_observable.csv or secondary_tally.csv were found under {result_path}")

    summary = pd.DataFrame(rows).sort_values("energy")
    output_path = Path(output_file) if output_file else result_path / "buildup_observable_summary.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False)
    return output_path
