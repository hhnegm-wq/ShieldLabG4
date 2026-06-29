from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

from shieldlab.analysis import hvl, mean_free_path, tvl


def _binomial_std_error(count: float, total: int) -> float:
    if total <= 0:
        return math.nan
    fraction = max(0.0, min(1.0, float(count) / total))
    return math.sqrt(fraction * (1.0 - fraction) / total)


def _derived_uncertainties(mu: float, mu_std: float) -> dict[str, float]:
    if not math.isfinite(mu) or not math.isfinite(mu_std) or mu <= 0.0:
        return {
            "mean_free_path_std_cm": math.nan,
            "hvl_std_cm": math.nan,
            "tvl_std_cm": math.nan,
        }

    mfp_value = mean_free_path(mu)
    hvl_value = hvl(mu)
    tvl_value = tvl(mu)
    scale = mu_std / mu
    return {
        "mean_free_path_std_cm": abs(mfp_value * scale),
        "hvl_std_cm": abs(hvl_value * scale),
        "tvl_std_cm": abs(tvl_value * scale),
    }


def _uncertainty_fields(summary: dict, density: float) -> dict[str, float]:
    events = int(summary.get("events", 0) or 0)
    transmitted = float(summary.get("transmitted", 0.0) or 0.0)
    reflected = float(summary.get("reflected", 0.0) or 0.0)
    thickness_cm = float(summary.get("total_thickness_cm", math.nan) or math.nan)
    transmission = float(summary.get("transmission_fraction", 0.0) or 0.0)
    reflection = float(summary.get("reflection_fraction", 0.0) or 0.0)
    absorption = float(summary.get("absorption_fraction", 0.0) or 0.0)
    mu = float(summary.get("linear_attenuation_cm_inv", math.nan) or math.nan)
    attenuation_estimate_type = str(summary.get("attenuation_estimate_type", "direct"))

    transmission_std = _binomial_std_error(transmitted, events)
    reflection_std = _binomial_std_error(reflected, events)
    absorption_count = max(events - transmitted - reflected, 0.0)
    absorption_std = _binomial_std_error(absorption_count, events)

    mu_std = math.nan
    if (
        attenuation_estimate_type == "direct"
        and events > 0
        and math.isfinite(thickness_cm)
        and thickness_cm > 0.0
        and transmission > 0.0
        and math.isfinite(transmission_std)
    ):
        mu_std = transmission_std / (thickness_cm * transmission)

    mass_att_std = mu_std / density if math.isfinite(mu_std) and density and density > 0 else math.nan
    derived = _derived_uncertainties(mu, mu_std)
    return {
        "transmission_fraction_std": transmission_std,
        "reflection_fraction_std": reflection_std,
        "absorption_fraction_std": absorption_std,
        "transmission_fraction_ci95_half_width": 1.96 * transmission_std if math.isfinite(transmission_std) else math.nan,
        "reflection_fraction_ci95_half_width": 1.96 * reflection_std if math.isfinite(reflection_std) else math.nan,
        "absorption_fraction_ci95_half_width": 1.96 * absorption_std if math.isfinite(absorption_std) else math.nan,
        "linear_attenuation_std_cm_inv": mu_std,
        "mass_attenuation_std_cm2_g": mass_att_std,
        **derived,
    }


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


def _parse_thickness(folder_name: str) -> float | None:
    """Parse a T_<value>_cm folder name; returns thickness in cm or None."""
    if not folder_name.startswith("T_") or not folder_name.endswith("_cm"):
        return None
    body = folder_name[2:-3].replace("p", ".")
    try:
        return float(body)
    except ValueError:
        return None


def collect_sweep(result_dir: str | Path, output_file: str | Path | None = None) -> Path:
    result_path = Path(result_dir)
    rows: list[dict[str, float | int | str | None]] = []

    for run_dir in sorted(path for path in result_path.iterdir() if path.is_dir()):
        energy, unit = _parse_energy(run_dir.name)
        summary_path = run_dir / "run_summary.csv"
        layer_path = run_dir / "layer_energy_deposition.csv"
        if energy is None or not summary_path.exists():
            continue

        summary = pd.read_csv(summary_path).iloc[0].to_dict()
        layers = pd.read_csv(layer_path) if layer_path.exists() else pd.DataFrame()
        mu = float(summary.get("linear_attenuation_cm_inv", 0.0))
        density = float(layers.iloc[0].get("density_g_cm3", math.nan)) if len(layers.index) == 1 else math.nan
        uncertainty_fields = _uncertainty_fields(summary, density)

        rows.append(
            {
                "energy": energy,
                "energy_unit": unit,
                "events": int(summary.get("events", 0)),
                "attenuation_estimate_type": summary.get("attenuation_estimate_type", "direct"),
                "total_thickness_cm": float(summary.get("total_thickness_cm", math.nan)),
                "transmission_fraction": float(summary.get("transmission_fraction", 0.0)),
                "reflection_fraction": float(summary.get("reflection_fraction", 0.0)),
                "absorption_fraction": float(summary.get("absorption_fraction", 0.0)),
                "linear_attenuation_cm_inv": mu,
                "mass_attenuation_cm2_g": mu / density if density and density > 0 else math.nan,
                "mean_free_path_cm": mean_free_path(mu),
                "hvl_cm": hvl(mu),
                "tvl_cm": tvl(mu),
                **uncertainty_fields,
            }
        )

    if not rows:
        raise ValueError(f"No sweep result folders were found under {result_path}")

    sweep = pd.DataFrame(rows).sort_values("energy")
    if output_file is None:
        output_path = result_path / "sweep_summary.csv"
    else:
        output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sweep.to_csv(output_path, index=False)
    return output_path


def collect_thickness_sweep(result_dir: str | Path, output_file: str | Path | None = None) -> Path:
    """Collect T_*_cm child folders into thickness_sweep_summary.csv."""
    result_path = Path(result_dir)
    rows: list[dict[str, float | int | str | None]] = []

    for run_dir in sorted(path for path in result_path.iterdir() if path.is_dir()):
        thickness = _parse_thickness(run_dir.name)
        summary_path = run_dir / "run_summary.csv"
        layer_path = run_dir / "layer_energy_deposition.csv"
        if thickness is None or not summary_path.exists():
            continue

        summary = pd.read_csv(summary_path).iloc[0].to_dict()
        layers = pd.read_csv(layer_path) if layer_path.exists() else pd.DataFrame()
        mu = float(summary.get("linear_attenuation_cm_inv", 0.0))
        density = float(layers.iloc[0].get("density_g_cm3", math.nan)) if len(layers.index) == 1 else math.nan
        uncertainty_fields = _uncertainty_fields(summary, density)

        rows.append(
            {
                "thickness_cm": thickness,
                "events": int(summary.get("events", 0)),
                "attenuation_estimate_type": summary.get("attenuation_estimate_type", "direct"),
                "total_thickness_cm": float(summary.get("total_thickness_cm", math.nan)),
                "transmission_fraction": float(summary.get("transmission_fraction", 0.0)),
                "reflection_fraction": float(summary.get("reflection_fraction", 0.0)),
                "absorption_fraction": float(summary.get("absorption_fraction", 0.0)),
                "linear_attenuation_cm_inv": mu,
                "mass_attenuation_cm2_g": mu / density if density and density > 0 else math.nan,
                "mean_free_path_cm": mean_free_path(mu),
                "hvl_cm": hvl(mu),
                "tvl_cm": tvl(mu),
                **uncertainty_fields,
            }
        )

    if not rows:
        raise ValueError(f"No T_*_cm result folders were found under {result_path}")

    sweep = pd.DataFrame(rows).sort_values("thickness_cm")
    if output_file is None:
        output_path = result_path / "thickness_sweep_summary.csv"
    else:
        output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sweep.to_csv(output_path, index=False)
    return output_path


def _parse_composition(folder_name: str) -> tuple[str | None, float | None]:
    """Parse a C_<compound>_<value> folder name; returns (compound, fraction) or (None, None)."""
    if not folder_name.startswith("C_"):
        return None, None
    body = folder_name[2:]   # strip "C_"
    parts = body.rsplit("_", 1)
    if len(parts) != 2:
        return None, None
    compound = parts[0]
    try:
        value = float(parts[1].replace("p", "."))
        return compound, value
    except ValueError:
        return None, None


def collect_composition_sweep(result_dir: str | Path, output_file: str | Path | None = None) -> Path:
    """Collect C_<compound>_<value> child folders into composition_sweep_summary.csv."""
    result_path = Path(result_dir)
    rows: list[dict[str, float | int | str | None]] = []

    for run_dir in sorted(path for path in result_path.iterdir() if path.is_dir()):
        compound, fraction = _parse_composition(run_dir.name)
        summary_path = run_dir / "run_summary.csv"
        layer_path = run_dir / "layer_energy_deposition.csv"
        if compound is None or not summary_path.exists():
            continue

        summary = pd.read_csv(summary_path).iloc[0].to_dict()
        layers = pd.read_csv(layer_path) if layer_path.exists() else pd.DataFrame()
        mu = float(summary.get("linear_attenuation_cm_inv", 0.0))
        density = float(layers.iloc[0].get("density_g_cm3", math.nan)) if len(layers.index) == 1 else math.nan
        uncertainty_fields = _uncertainty_fields(summary, density)

        rows.append(
            {
                "compound": compound,
                "compound_fraction": fraction,
                "events": int(summary.get("events", 0)),
                "attenuation_estimate_type": summary.get("attenuation_estimate_type", "direct"),
                "total_thickness_cm": float(summary.get("total_thickness_cm", math.nan)),
                "transmission_fraction": float(summary.get("transmission_fraction", 0.0)),
                "reflection_fraction": float(summary.get("reflection_fraction", 0.0)),
                "absorption_fraction": float(summary.get("absorption_fraction", 0.0)),
                "linear_attenuation_cm_inv": mu,
                "mass_attenuation_cm2_g": mu / density if density and density > 0 else math.nan,
                "mean_free_path_cm": mean_free_path(mu),
                "hvl_cm": hvl(mu),
                "tvl_cm": tvl(mu),
                **uncertainty_fields,
            }
        )

    if not rows:
        raise ValueError(f"No C_*_* composition result folders were found under {result_path}")

    sweep = pd.DataFrame(rows).sort_values("compound_fraction")
    if output_file is None:
        output_path = result_path / "composition_sweep_summary.csv"
    else:
        output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sweep.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect ShieldLab-G4 sweep result folders into one CSV."
    )
    parser.add_argument("result_dir", help="Sweep result directory containing E_*, T_*_cm, or C_* child folders")
    parser.add_argument("--output", help="Output CSV path")
    parser.add_argument("--thickness", action="store_true", help="Collect T_*_cm thickness folders")
    parser.add_argument("--composition", action="store_true", help="Collect C_* composition folders")
    args = parser.parse_args()
    if args.thickness:
        print(collect_thickness_sweep(args.result_dir, args.output))
    elif args.composition:
        print(collect_composition_sweep(args.result_dir, args.output))
    else:
        print(collect_sweep(args.result_dir, args.output))


if __name__ == "__main__":
    main()