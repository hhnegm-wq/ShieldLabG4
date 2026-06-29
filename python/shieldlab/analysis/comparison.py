from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REFERENCE_COLUMNS = (
    "energy",
    "energy_unit",
    "source",
    "linear_attenuation_cm_inv",
    "mass_attenuation_cm2_g",
)


BUILDUP_COLUMNS = (
    "energy",
    "energy_unit",
    "zeq",
    "ebf_a",
    "ebf_b",
    "ebf_c",
    "ebf_d",
    "ebf_xk",
    "eabf_a",
    "eabf_b",
    "eabf_c",
    "eabf_d",
    "eabf_xk",
    "source",
)


UNCERTAINTY_AWARE_COMPARISON_COLUMNS = (
    "linear_attenuation_std_cm_inv_simulated",
    "mass_attenuation_std_cm2_g_simulated",
    "linear_attenuation_cm_inv_normalized_residual",
    "mass_attenuation_cm2_g_normalized_residual",
)


def _convert_energy(values: pd.Series, from_unit: pd.Series, to_unit: str) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    src = from_unit.astype(str).str.lower()
    dst = str(to_unit).lower()
    result = pd.Series(np.nan, index=numeric.index, dtype=float)

    if dst == "mev":
        result = np.where(src == "kev", numeric / 1000.0, numeric)
        result = np.where(src == "ev", numeric / 1.0e6, result)
        result = np.where(src == "gev", numeric * 1000.0, result)
    elif dst == "kev":
        result = np.where(src == "mev", numeric * 1000.0, numeric)
        result = np.where(src == "ev", numeric / 1000.0, result)
        result = np.where(src == "gev", numeric * 1.0e6, result)
    else:
        result = numeric

    return pd.Series(result, index=numeric.index, dtype=float)


def comparison_has_uncertainty_columns(comparison: pd.DataFrame) -> bool:
    if comparison.empty:
        return False
    return any(column in comparison.columns for column in UNCERTAINTY_AWARE_COMPARISON_COLUMNS)


def resolve_reference_artifacts(
    result_dir: str | Path,
    validation: dict | None,
    sweep: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    result_path = Path(result_dir)
    validation_data = validation if isinstance(validation, dict) else {}

    reference_path = result_path / "reference_coefficients.csv"
    comparison_path = result_path / "reference_comparison.csv"

    reference = pd.read_csv(reference_path) if reference_path.exists() else pd.DataFrame()
    comparison = pd.read_csv(comparison_path) if comparison_path.exists() else pd.DataFrame()
    buildup = pd.DataFrame()
    has_uncertainty = comparison_has_uncertainty_columns(comparison)

    if not reference.empty and ((not comparison.empty and (has_uncertainty or sweep is None)) or sweep is None):
        study_file = validation_data.get("study_file")
        if study_file:
            buildup = load_reference_buildup(study_file)
        return reference, comparison, buildup

    study_file = validation_data.get("study_file")
    if not study_file:
        return reference, comparison, buildup

    study_reference = load_reference_coefficients(study_file)
    buildup = load_reference_buildup(study_file)
    if reference.empty:
        reference = study_reference

    if sweep is not None and not study_reference.empty and (comparison.empty or not has_uncertainty):
        comparison = compare_coefficients(sweep, study_reference)

    return reference, comparison, buildup


def load_reference_acceptance(study_file: str | Path | None) -> dict:
    if study_file is None:
        return {}

    study_path = Path(study_file)
    if not study_path.exists():
        return {}

    with study_path.open("r", encoding="utf-8") as handle:
        study = json.load(handle)

    references = study.get("references", {})
    if not isinstance(references, dict):
        return {}
    acceptance = references.get("acceptance_criteria", {})
    return acceptance if isinstance(acceptance, dict) else {}


def load_reference_coefficients(study_file: str | Path | None) -> pd.DataFrame:
    if study_file is None:
        return pd.DataFrame(columns=REFERENCE_COLUMNS)

    study_path = Path(study_file)
    if not study_path.exists():
        return pd.DataFrame(columns=REFERENCE_COLUMNS)

    with study_path.open("r", encoding="utf-8") as handle:
        study = json.load(handle)

    references = study.get("references", {})
    coefficient_rows = references.get("coefficients", []) if isinstance(references, dict) else []
    if not coefficient_rows:
        return pd.DataFrame(columns=REFERENCE_COLUMNS)

    reference = pd.DataFrame(coefficient_rows)
    for column in REFERENCE_COLUMNS:
        if column not in reference:
            reference[column] = pd.NA
    return reference[list(REFERENCE_COLUMNS)]


def compare_coefficients(sweep: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    if sweep.empty or reference.empty:
        return pd.DataFrame()

    merged = sweep.merge(reference, on=["energy", "energy_unit"], how="inner", suffixes=("_simulated", "_reference"))
    if merged.empty:
        return merged

    # Ensure uncertainty columns consistently use *_simulated naming even when
    # they originate only from sweep input and thus are not suffixed by merge.
    if "linear_attenuation_std_cm_inv" in merged.columns and "linear_attenuation_std_cm_inv_simulated" not in merged.columns:
        merged["linear_attenuation_std_cm_inv_simulated"] = merged["linear_attenuation_std_cm_inv"]
    if "mass_attenuation_std_cm2_g" in merged.columns and "mass_attenuation_std_cm2_g_simulated" not in merged.columns:
        merged["mass_attenuation_std_cm2_g_simulated"] = merged["mass_attenuation_std_cm2_g"]

    uncertainty_map = {
        "linear_attenuation_cm_inv": "linear_attenuation_std_cm_inv",
        "mass_attenuation_cm2_g": "mass_attenuation_std_cm2_g",
    }

    for quantity in ("linear_attenuation_cm_inv", "mass_attenuation_cm2_g"):
        simulated = f"{quantity}_simulated"
        benchmark = f"{quantity}_reference"
        percent_difference = f"{quantity}_percent_difference"
        uncertainty_simulated = f"{uncertainty_map[quantity]}_simulated"
        normalized_residual = f"{quantity}_normalized_residual"
        if simulated in merged and benchmark in merged:
            merged[percent_difference] = (merged[simulated] - merged[benchmark]) / merged[benchmark] * 100.0
            if uncertainty_simulated in merged:
                sigma = pd.to_numeric(merged[uncertainty_simulated], errors="coerce")
                delta = pd.to_numeric(merged[simulated], errors="coerce") - pd.to_numeric(merged[benchmark], errors="coerce")
                merged[normalized_residual] = np.where(sigma > 0.0, delta / sigma, np.nan)

    ordered_columns = [
        "energy",
        "energy_unit",
        "source",
        "events",
        "attenuation_estimate_type",
        "transmission_fraction",
        "transmission_fraction_std",
        "transmission_fraction_ci95_half_width",
        "reflection_fraction",
        "reflection_fraction_std",
        "reflection_fraction_ci95_half_width",
        "absorption_fraction",
        "absorption_fraction_std",
        "absorption_fraction_ci95_half_width",
        "linear_attenuation_cm_inv_simulated",
        "linear_attenuation_std_cm_inv_simulated",
        "linear_attenuation_cm_inv_reference",
        "linear_attenuation_cm_inv_percent_difference",
        "linear_attenuation_cm_inv_normalized_residual",
        "mass_attenuation_cm2_g_simulated",
        "mass_attenuation_std_cm2_g_simulated",
        "mass_attenuation_cm2_g_reference",
        "mass_attenuation_cm2_g_percent_difference",
        "mass_attenuation_cm2_g_normalized_residual",
    ]
    return merged[[column for column in ordered_columns if column in merged]]


def compare_buildup_observable(
    observable: pd.DataFrame,
    reference_buildup: pd.DataFrame,
    depth_mfp: float = 5.0,
) -> pd.DataFrame:
    if observable.empty or reference_buildup.empty:
        return pd.DataFrame()

    literature = reference_buildup.copy()
    literature = literature[literature["energy"].notna()].copy()
    if literature.empty:
        return pd.DataFrame()

    target_unit = str(literature["energy_unit"].dropna().astype(str).iloc[0]) if literature["energy_unit"].notna().any() else "MeV"
    literature["energy_cmp"] = _convert_energy(literature["energy"], literature["energy_unit"], target_unit)
    literature["ebf_literature"] = literature.apply(
        lambda row: gp_buildup_from_coefficients(
            float(row["ebf_a"]),
            float(row["ebf_b"]),
            float(row["ebf_c"]),
            float(row["ebf_d"]),
            float(row["ebf_xk"]),
            float(depth_mfp),
        )
        if pd.notna(row.get("ebf_a")) and pd.notna(row.get("ebf_b")) and pd.notna(row.get("ebf_c")) and pd.notna(row.get("ebf_d")) and pd.notna(row.get("ebf_xk"))
        else np.nan,
        axis=1,
    )

    mc = observable.copy()
    mc = mc[mc["energy"].notna()].copy()
    if mc.empty or "mc_buildup_observable_energy" not in mc.columns:
        return pd.DataFrame()
    if "energy_unit" not in mc.columns:
        mc["energy_unit"] = target_unit
    mc["energy_cmp"] = _convert_energy(mc["energy"], mc["energy_unit"], target_unit)

    merged = mc.merge(
        literature[["energy_cmp", "ebf_literature"]],
        on="energy_cmp",
        how="inner",
    )
    if merged.empty:
        return pd.DataFrame()

    merged["buildup_observable_energy_percent_difference"] = (
        (pd.to_numeric(merged["mc_buildup_observable_energy"], errors="coerce") - pd.to_numeric(merged["ebf_literature"], errors="coerce"))
        / pd.to_numeric(merged["ebf_literature"], errors="coerce").replace(0.0, np.nan)
        * 100.0
    )

    columns = [
        "energy_cmp",
        "energy_unit",
        "mc_buildup_observable_count",
        "mc_buildup_observable_energy",
        "ebf_literature",
        "buildup_observable_energy_percent_difference",
    ]
    result = merged[[column for column in columns if column in merged]].copy()
    result = result.rename(columns={"energy_cmp": "energy"})
    result["buildup_depth_mfp"] = float(depth_mfp)
    return result.sort_values("energy")


def load_reference_buildup(study_file: str | Path | None) -> pd.DataFrame:
    if study_file is None:
        return pd.DataFrame(columns=BUILDUP_COLUMNS)

    study_path = Path(study_file)
    if not study_path.exists():
        return pd.DataFrame(columns=BUILDUP_COLUMNS)

    with study_path.open("r", encoding="utf-8") as handle:
        study = json.load(handle)

    references = study.get("references", {})
    buildup = references.get("buildup_factors", {}) if isinstance(references, dict) else {}
    coeff_rows = buildup.get("coefficients", []) if isinstance(buildup, dict) else []
    if not coeff_rows:
        return pd.DataFrame(columns=BUILDUP_COLUMNS)

    rows = []
    default_unit = str(buildup.get("energy_unit", "MeV"))
    default_source = str(buildup.get("source", "literature"))

    for row in coeff_rows:
        if not isinstance(row, dict):
            continue
        ebf = row.get("ebf", {}) if isinstance(row.get("ebf", {}), dict) else {}
        eabf = row.get("eabf", {}) if isinstance(row.get("eabf", {}), dict) else {}
        rows.append({
            "energy": row.get("energy"),
            "energy_unit": row.get("energy_unit", default_unit),
            "zeq": row.get("zeq"),
            "ebf_a": ebf.get("a"),
            "ebf_b": ebf.get("b"),
            "ebf_c": ebf.get("c"),
            "ebf_d": ebf.get("d"),
            "ebf_xk": ebf.get("xk"),
            "eabf_a": eabf.get("a"),
            "eabf_b": eabf.get("b"),
            "eabf_c": eabf.get("c"),
            "eabf_d": eabf.get("d"),
            "eabf_xk": eabf.get("xk"),
            "source": row.get("source", default_source),
        })

    if not rows:
        return pd.DataFrame(columns=BUILDUP_COLUMNS)

    data = pd.DataFrame(rows)
    for column in BUILDUP_COLUMNS:
        if column not in data:
            data[column] = pd.NA
    return data[list(BUILDUP_COLUMNS)]


def gp_buildup_from_coefficients(a: float, b: float, c: float, d: float, xk: float, t_mfp: float) -> float:
    """Evaluate the Harima G-P buildup expression from tabulated coefficients."""
    if xk <= 0:
        return float("nan")
    tanh_arg = float(np.tanh(t_mfp / xk - 2.0))
    tanh_m2 = float(np.tanh(-2.0))
    k_val = c * (t_mfp ** a) + d * (tanh_arg - tanh_m2) / (1.0 - tanh_m2)
    if abs(k_val - 1.0) < 1e-9:
        buildup = 1.0 + (b - 1.0) * t_mfp
    else:
        buildup = 1.0 + (b - 1.0) * (k_val ** t_mfp - 1.0) / (k_val - 1.0)
    return float(max(buildup, 1.0))


def summarize_reference_comparison(comparison: pd.DataFrame, acceptance: dict | None = None) -> dict:
    acceptance = acceptance or {}
    metric_rules = acceptance.get("metrics", {}) if isinstance(acceptance, dict) else {}
    percent_columns = [col for col in comparison.columns if col.endswith("_percent_difference")]
    if comparison.empty or not percent_columns:
        return {
            "status": "unavailable",
            "row_count": int(len(comparison)),
            "quantities": {},
            "has_thresholds": bool(metric_rules),
        }

    quantities: dict[str, dict] = {}
    overall_status = "passed"
    has_thresholds = False

    for column in percent_columns:
        series = pd.to_numeric(comparison[column], errors="coerce").dropna()
        if series.empty:
            continue

        rules = metric_rules.get(column, {}) if isinstance(metric_rules, dict) else {}
        mean_abs_max = rules.get("mean_abs_max") if isinstance(rules, dict) else None
        max_abs_max = rules.get("max_abs_max") if isinstance(rules, dict) else None
        quantity_status = "available"

        mean_abs = float(series.abs().mean())
        max_abs = float(series.abs().max())
        mean_signed = float(series.mean())

        if mean_abs_max is not None or max_abs_max is not None:
            has_thresholds = True
            failed = False
            if mean_abs_max is not None and mean_abs > float(mean_abs_max):
                failed = True
            if max_abs_max is not None and max_abs > float(max_abs_max):
                failed = True
            quantity_status = "failed" if failed else "passed"
            if failed:
                overall_status = "failed"

        quantities[column] = {
            "mean_abs_percent_difference": mean_abs,
            "max_abs_percent_difference": max_abs,
            "mean_signed_percent_difference": mean_signed,
            "count": int(series.shape[0]),
            "status": quantity_status,
            "thresholds": {
                "mean_abs_max": float(mean_abs_max) if mean_abs_max is not None else None,
                "max_abs_max": float(max_abs_max) if max_abs_max is not None else None,
            },
        }

    if not quantities:
        overall_status = "unavailable"
    elif not has_thresholds and overall_status == "passed":
        overall_status = "available"

    return {
        "status": overall_status,
        "row_count": int(len(comparison)),
        "quantities": quantities,
        "has_thresholds": has_thresholds,
    }