from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _latest_release_report(validation_dir: Path) -> dict[str, Any]:
    latest = validation_dir / "release_validation_report_latest.json"
    if latest.exists():
        return _load_json(latest)
    candidates = sorted(validation_dir.glob("release_validation_report_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return _load_json(candidates[0]) if candidates else {}


def _equation_blocks() -> list[dict[str, str]]:
    return [
        {
            "name": "Mass attenuation mixture rule",
            "equation": r"(mu/rho) = sum_i w_i * (mu/rho)_i",
            "notes": "NIST mixture rule for compounds and mixtures.",
        },
        {
            "name": "Transmission model",
            "equation": r"T = exp(-(mu/rho)*rho*x)",
            "notes": "Narrow-beam attenuation model used for analytical comparison.",
        },
        {
            "name": "HVL and TVL",
            "equation": r"HVL = ln(2)/mu ; TVL = ln(10)/mu",
            "notes": "Derived attenuation metrics for shielding studies.",
        },
        {
            "name": "Buildup GP model",
            "equation": r"B = 1 + (b-1)*(K^x - 1)/(K - 1)",
            "notes": "GP-based buildup calculation for broad-beam corrections.",
        },
        {
            "name": "Normalized residual",
            "equation": r"r = (simulation - reference) / sigma_sim",
            "notes": "Uncertainty-aware residual metric for benchmark diagnostics.",
        },
    ]


def _uncertainty_statements() -> list[str]:
    return [
        "Transmission, reflection, and absorption uncertainty are propagated with binomial standard-error models.",
        "95% confidence half-widths are reported for event fractions when count statistics are available.",
        "Linear and mass attenuation uncertainty are propagated through delta-method conversion from transmission uncertainty.",
        "Benchmark normalized residuals are reported as (simulation - literature) / simulation standard error.",
        "Uncertainty interpretation must distinguish statistical, input, model, and literature components.",
    ]


def _bibliography_entries(release_report: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = release_report.get("reference_catalog", {}) if isinstance(release_report.get("reference_catalog", {}), dict) else {}
    entries = catalog.get("entries", []) if isinstance(catalog.get("entries", []), list) else []
    output: list[dict[str, Any]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        doi = item.get("paper_doi")
        title = item.get("paper_title")
        output.append(
            {
                "study_file": item.get("study_file"),
                "title": title,
                "doi": doi,
                "sample_id": item.get("sample_id"),
                "doi_url": f"https://doi.org/{doi}" if doi else None,
            }
        )
    return output


def _assumption_block(release_report: dict[str, Any]) -> dict[str, Any]:
    runtime = release_report.get("runtime_validation", []) if isinstance(release_report.get("runtime_validation", []), list) else []
    summary = release_report.get("summary", {}) if isinstance(release_report.get("summary", {}), dict) else {}
    q1 = summary.get("q1_readiness", {}) if isinstance(summary.get("q1_readiness", {}), dict) else {}
    return {
        "release_gate": summary.get("release_gate"),
        "q1_readiness": q1,
        "runtime_result_sets": len(runtime),
        "threshold_backed_sets": summary.get("threshold_backed_sets"),
        "provenance_manifest_sets": summary.get("provenance_manifest_sets"),
        "benchmark_status_counts": summary.get("benchmark_status_counts", {}),
    }


def _benchmark_table(release_report: dict[str, Any]) -> pd.DataFrame:
    runtime = release_report.get("runtime_validation", []) if isinstance(release_report.get("runtime_validation", []), list) else []
    rows: list[dict[str, Any]] = []
    for item in runtime:
        metrics = item.get("metrics", {}) if isinstance(item.get("metrics", {}), dict) else {}
        if not metrics:
            rows.append(
                {
                    "result_set": item.get("result_set"),
                    "study_file": item.get("study_file"),
                    "benchmark_status": item.get("benchmark_status"),
                    "metric": None,
                    "status": None,
                    "mean_abs_percent_difference": None,
                    "max_abs_percent_difference": None,
                    "threshold_mean_abs_max": None,
                    "threshold_max_abs_max": None,
                }
            )
            continue
        for metric_name, values in metrics.items():
            if not isinstance(values, dict):
                continue
            thresholds = values.get("thresholds", {}) if isinstance(values.get("thresholds", {}), dict) else {}
            rows.append(
                {
                    "result_set": item.get("result_set"),
                    "study_file": item.get("study_file"),
                    "benchmark_status": item.get("benchmark_status"),
                    "metric": metric_name,
                    "status": values.get("status"),
                    "mean_abs_percent_difference": values.get("mean_abs_percent_difference"),
                    "max_abs_percent_difference": values.get("max_abs_percent_difference"),
                    "threshold_mean_abs_max": thresholds.get("mean_abs_max"),
                    "threshold_max_abs_max": thresholds.get("max_abs_max"),
                }
            )
    return pd.DataFrame(rows)


def _to_markdown(pack: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# ShieldLab G4 Manuscript Methods Pack")
    lines.append("")
    lines.append(f"Generated: {pack['generated_at_utc']}")
    lines.append("")
    lines.append("## Core Equations")
    lines.append("")
    for eq in pack["equations"]:
        lines.append(f"- **{eq['name']}**: {eq['equation']}")
        lines.append(f"  - {eq['notes']}")
    lines.append("")
    lines.append("## Assumptions and Validation Context")
    lines.append("")
    assumptions = pack.get("assumptions", {})
    for key, value in assumptions.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Uncertainty Statements")
    lines.append("")
    for statement in pack["uncertainty_statements"]:
        lines.append(f"- {statement}")
    lines.append("")
    lines.append("## Bibliography")
    lines.append("")
    bibliography = pack.get("bibliography", [])
    if bibliography:
        for row in bibliography:
            title = row.get("title") or "Untitled reference"
            if row.get("doi"):
                lines.append(f"- {title}. DOI: {row.get('doi')} ({row.get('doi_url')})")
            else:
                lines.append(f"- {title}. DOI missing.")
    else:
        lines.append("- No bibliography entries available in release report catalog.")
    lines.append("")
    lines.append("## Benchmark Table Artifact")
    lines.append("")
    lines.append(f"- CSV: {pack['artifacts'].get('benchmark_table_csv')}")
    return "\n".join(lines) + "\n"


def generate_methods_export_pack(project_root: str | Path, output_dir: str | Path) -> dict[str, Path]:
    root = Path(project_root)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    validation_dir = root / "docs" / "validation"
    release_report = _latest_release_report(validation_dir)

    equations = _equation_blocks()
    uncertainty = _uncertainty_statements()
    assumptions = _assumption_block(release_report)
    bibliography = _bibliography_entries(release_report)
    reference_coverage = (
        (release_report.get("reference_catalog", {}) if isinstance(release_report.get("reference_catalog", {}), dict) else {}).get(
            "coverage", {}
        )
    )
    benchmark_frame = _benchmark_table(release_report)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bench_csv = out / f"methods_benchmark_table_{stamp}.csv"
    if not benchmark_frame.empty:
        benchmark_frame.to_csv(bench_csv, index=False)

    pack: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "equations": equations,
        "assumptions": assumptions,
        "uncertainty_statements": uncertainty,
        "bibliography": bibliography,
        "reference_coverage": reference_coverage if isinstance(reference_coverage, dict) else {},
        "artifacts": {
            "source_release_report": str((validation_dir / "release_validation_report_latest.json")),
            "benchmark_table_csv": str(bench_csv) if bench_csv.exists() else None,
        },
    }

    json_path = out / f"methods_export_pack_{stamp}.json"
    md_path = out / f"methods_export_pack_{stamp}.md"
    latest_json = out / "methods_export_pack_latest.json"
    latest_md = out / "methods_export_pack_latest.md"

    json_text = json.dumps(pack, indent=2)
    md_text = _to_markdown(pack)

    json_path.write_text(json_text, encoding="utf-8")
    md_path.write_text(md_text, encoding="utf-8")
    latest_json.write_text(json_text, encoding="utf-8")
    latest_md.write_text(md_text, encoding="utf-8")

    return {
        "json": json_path,
        "markdown": md_path,
        "latest_json": latest_json,
        "latest_markdown": latest_md,
        "benchmark_table_csv": bench_csv,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate manuscript-ready methods export pack artifacts.")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    root = Path(args.project_root)
    output_dir = Path(args.output_dir) if args.output_dir else root / "docs" / "validation"

    outputs = generate_methods_export_pack(root, output_dir)
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
