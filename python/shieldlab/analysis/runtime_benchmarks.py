from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


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


def load_reference_acceptance(study_file: str | Path | None) -> dict:
    if study_file is None:
        return {}

    study_path = Path(study_file)
    if not study_path.exists():
        return {}

    with study_path.open("r", encoding="utf-8-sig") as handle:
        study = json.load(handle)

    references = study.get("references", {})
    if not isinstance(references, dict):
        return {}
    acceptance = references.get("acceptance_criteria", {})
    return acceptance if isinstance(acceptance, dict) else {}


def load_reference_buildup(study_file: str | Path | None) -> pd.DataFrame:
    if study_file is None:
        return pd.DataFrame(columns=BUILDUP_COLUMNS)

    study_path = Path(study_file)
    if not study_path.exists():
        return pd.DataFrame(columns=BUILDUP_COLUMNS)

    with study_path.open("r", encoding="utf-8-sig") as handle:
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
        rows.append(
            {
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
            }
        )

    if not rows:
        return pd.DataFrame(columns=BUILDUP_COLUMNS)

    data = pd.DataFrame(rows)
    for column in BUILDUP_COLUMNS:
        if column not in data:
            data[column] = pd.NA
    return data[list(BUILDUP_COLUMNS)]


def gp_buildup_from_coefficients(a: float, b: float, c: float, d: float, xk: float, t_mfp: float) -> float:
    if xk <= 0:
        return float("nan")
    tanh_arg = float(np.tanh(t_mfp / xk - 2.0))
    tanh_m2 = float(np.tanh(-2.0))
    k_val = c * (t_mfp ** a) + d * (tanh_arg - tanh_m2) / (1.0 - tanh_m2)
    if abs(k_val - 1.0) < 1e-9:
        buildup = 1.0 + (b - 1.0) * t_mfp
    else:
        buildup = 1.0 + (b - 1.0) * (k_val**t_mfp - 1.0) / (k_val - 1.0)
    return float(max(buildup, 1.0))


def summarize_reference_comparison(comparison: pd.DataFrame, acceptance: dict | None = None) -> dict:
    acceptance = acceptance or {}
    metric_rules = acceptance.get("metrics", {}) if isinstance(acceptance, dict) else {}
    percent_columns = [column for column in comparison.columns if column.endswith("_percent_difference")]
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