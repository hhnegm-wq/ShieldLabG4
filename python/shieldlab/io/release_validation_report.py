from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from shieldlab.io.study_validator import has_errors, issues_to_frame, validate_study_file


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _stable_hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _collect_study_validation(studies_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for study_path in sorted(studies_dir.glob("literature_benchmark_*.json")):
        issues = validate_study_file(study_path)
        issue_frame = issues_to_frame(issues)
        errors = issue_frame[issue_frame["severity"] == "error"]
        warnings = issue_frame[issue_frame["severity"] == "warning"]
        rows.append(
            {
                "study_file": study_path.name,
                "errors": int(errors.shape[0]),
                "warnings": int(warnings.shape[0]),
                "is_valid": not has_errors(issues),
                "messages": issue_frame.to_dict(orient="records"),
            }
        )
    return rows


def _collect_reference_catalog(studies_dir: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for study_path in sorted(studies_dir.glob("literature_benchmark_*.json")):
        study_payload = _load_json(study_path)
        references = study_payload.get("references", {}) if isinstance(study_payload.get("references", {}), dict) else {}
        entry = {
            "study_file": study_path.name,
            "paper_title": references.get("paper_title"),
            "paper_doi": references.get("paper_doi"),
            "sample_id": references.get("sample_id"),
            "has_reference_coefficients": bool(references.get("coefficients")),
            "has_buildup_factors": bool((references.get("buildup_factors") or {}).get("coefficients"))
            if isinstance(references.get("buildup_factors") or {}, dict)
            else False,
            "reference_fingerprint": _stable_hash(references),
        }
        entries.append(entry)

    doi_count = sum(1 for e in entries if e.get("paper_doi"))
    title_count = sum(1 for e in entries if e.get("paper_title"))
    sample_id_count = sum(1 for e in entries if e.get("sample_id"))
    total = len(entries)
    return {
        "entries": entries,
        "dataset_fingerprint": _stable_hash(entries),
        "coverage": {
            "study_count": total,
            "doi_coverage_ratio": (doi_count / total) if total else 0.0,
            "title_coverage_ratio": (title_count / total) if total else 0.0,
            "sample_id_coverage_ratio": (sample_id_count / total) if total else 0.0,
        },
    }


def _collect_runtime_environment(results_dir: Path) -> dict[str, Any]:
    manifests = sorted(results_dir.glob("*/provenance_manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    platforms = sorted(
        {
            str(((_load_json(path).get("execution", {}) if isinstance(_load_json(path).get("execution", {}), dict) else {}).get("platform", "unknown")))
            for path in manifests
        }
    )
    payload = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "manifest_count": len(manifests),
        "observed_execution_platforms": platforms,
    }
    payload["reproducibility_fingerprint"] = _stable_hash(payload)
    return payload


def _collect_runtime_validation(results_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not results_dir.exists():
        return rows
    for summary_path in sorted(results_dir.glob("*/validation_summary.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        payload = _load_json(summary_path)
        benchmark = payload.get("benchmark_summary", {}) if isinstance(payload.get("benchmark_summary", {}), dict) else {}
        quantities = benchmark.get("quantities", {}) if isinstance(benchmark.get("quantities", {}), dict) else {}
        rows.append(
            {
                "result_set": summary_path.parent.name,
                "study_file": Path(str(payload.get("study_file", ""))).name,
                "status": str(payload.get("status", "unknown")),
                "benchmark_status": str(payload.get("benchmark_status", benchmark.get("status", "unavailable"))),
                "has_thresholds": bool(benchmark.get("has_thresholds", False)),
                "metric_count": int(len(quantities)),
                "run_count": int(payload.get("run_summary_count", 0) or 0),
                "histories": int(payload.get("histories", 0) or 0),
                "random_seed_present": payload.get("random_seed") is not None,
                "provenance_manifest": bool((summary_path.parent / "provenance_manifest.json").exists()),
                "literature_sources": payload.get("literature_sources", {}) if isinstance(payload.get("literature_sources", {}), dict) else {},
                "summary_path": str(summary_path),
                "metrics": quantities,
            }
        )
    return rows


def _summarize(studies: list[dict[str, Any]], runtime: list[dict[str, Any]], reference_catalog: dict[str, Any]) -> dict[str, Any]:
    study_total = len(studies)
    study_errors = sum(1 for row in studies if row["errors"] > 0)
    study_warnings = sum(row["warnings"] for row in studies)

    status_counts: dict[str, int] = {}
    for row in runtime:
        key = row["benchmark_status"]
        status_counts[key] = status_counts.get(key, 0) + 1

    failed_sets = [row for row in runtime if row["benchmark_status"] == "failed"]
    threshold_sets = [row for row in runtime if row["has_thresholds"]]
    provenance_sets = [row for row in runtime if row["provenance_manifest"]]
    statistical_adequate_sets = [row for row in runtime if int(row.get("histories", 0) or 0) >= 5000]
    runtime_count = len(runtime)

    threshold_ratio = (len(threshold_sets) / runtime_count) if runtime_count > 0 else 0.0
    provenance_ratio = (len(provenance_sets) / runtime_count) if runtime_count > 0 else 0.0
    statistical_ratio = (len(statistical_adequate_sets) / runtime_count) if runtime_count > 0 else 0.0
    doi_coverage_ratio = float(
        (
            (reference_catalog.get("coverage", {}) if isinstance(reference_catalog.get("coverage", {}), dict) else {}).get(
                "doi_coverage_ratio", 0.0
            )
        )
        or 0.0
    )

    gate_pass = study_errors == 0 and len(failed_sets) == 0
    q1_readiness = {
        "no_study_validation_errors": study_errors == 0,
        "no_failed_benchmark_sets": len(failed_sets) == 0,
        "threshold_coverage_ratio": threshold_ratio,
        "provenance_coverage_ratio": provenance_ratio,
        "citation_coverage_ratio": doi_coverage_ratio,
        "statistical_adequacy_ratio": statistical_ratio,
        "ready_for_submission": gate_pass
        and threshold_ratio >= 0.8
        and provenance_ratio >= 0.9
        and doi_coverage_ratio >= 0.9
        and statistical_ratio >= 0.8,
    }
    # Phase 0 hardening: a strict, separately-named "science_gate" so a
    # user can never confuse CI-engineering green with publication-readiness green.
    # The legacy ``release_gate`` field is preserved for backwards compatibility
    # but represents only the engineering CI gate (no errors, no failed sets).
    science_gate_pass = bool(q1_readiness["ready_for_submission"])
    return {
        "study_count": study_total,
        "study_error_count": study_errors,
        "study_warning_count": study_warnings,
        "runtime_result_sets": runtime_count,
        "benchmark_status_counts": status_counts,
        "failed_benchmark_sets": len(failed_sets),
        "threshold_backed_sets": len(threshold_sets),
        "provenance_manifest_sets": len(provenance_sets),
        "statistically_adequate_sets": len(statistical_adequate_sets),
        "ci_gate": "pass" if gate_pass else "fail",
        "science_gate": "pass" if science_gate_pass else "fail",
        # Legacy alias: only true when BOTH gates pass. Previously this flipped
        # to "pass" when the CI gate alone passed, which was the governance bug
        # called out in the fire review.
        "release_gate": "pass" if (gate_pass and science_gate_pass) else "fail",
        "q1_readiness": q1_readiness,
    }


def _compute_drift(current_summary: dict[str, Any], previous_report: dict[str, Any]) -> dict[str, Any]:
    previous_summary = previous_report.get("summary", {}) if isinstance(previous_report.get("summary", {}), dict) else {}
    drift = {
        "study_error_count_delta": int(current_summary.get("study_error_count", 0)) - int(previous_summary.get("study_error_count", 0) or 0),
        "study_warning_count_delta": int(current_summary.get("study_warning_count", 0)) - int(previous_summary.get("study_warning_count", 0) or 0),
        "failed_benchmark_sets_delta": int(current_summary.get("failed_benchmark_sets", 0)) - int(previous_summary.get("failed_benchmark_sets", 0) or 0),
        "runtime_result_sets_delta": int(current_summary.get("runtime_result_sets", 0)) - int(previous_summary.get("runtime_result_sets", 0) or 0),
        "release_gate_previous": previous_summary.get("release_gate", "unknown"),
        "release_gate_current": current_summary.get("release_gate", "unknown"),
    }
    return drift


def _to_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines: list[str] = []
    lines.append("# ShieldLab G4 Release Validation Report")
    lines.append("")
    lines.append(f"Generated: {report['generated_at_utc']}")
    lines.append(
        f"CI gate: **{summary.get('ci_gate', summary.get('release_gate', 'unknown')).upper()}**"
        f" — Science gate: **{summary.get('science_gate', 'unknown').upper()}**"
        f" — Combined release gate: **{summary['release_gate'].upper()}**"
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Study files validated: {summary['study_count']}")
    lines.append(f"- Study files with errors: {summary['study_error_count']}")
    lines.append(f"- Study warnings total: {summary['study_warning_count']}")
    lines.append(f"- Runtime result sets: {summary['runtime_result_sets']}")
    lines.append(f"- Failed benchmark sets: {summary['failed_benchmark_sets']}")
    lines.append(f"- Threshold-backed sets: {summary['threshold_backed_sets']}")
    lines.append(f"- Provenance manifests present: {summary['provenance_manifest_sets']}")
    lines.append(f"- Statistically adequate result sets (histories >= 5000): {summary.get('statistically_adequate_sets', 0)}")
    readiness = summary.get("q1_readiness", {}) if isinstance(summary.get("q1_readiness", {}), dict) else {}
    if readiness:
        lines.append(f"- Q1 readiness: {'READY' if readiness.get('ready_for_submission') else 'NOT READY'}")
    lines.append("")
    lines.append("## Benchmark Status Counts")
    lines.append("")
    if summary["benchmark_status_counts"]:
        for key, value in sorted(summary["benchmark_status_counts"].items()):
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- No runtime benchmark summaries found.")
    lines.append("")
    if readiness:
        lines.append("## Publication Readiness")
        lines.append("")
        lines.append(f"- no_study_validation_errors: {readiness.get('no_study_validation_errors')}")
        lines.append(f"- no_failed_benchmark_sets: {readiness.get('no_failed_benchmark_sets')}")
        lines.append(f"- threshold_coverage_ratio: {float(readiness.get('threshold_coverage_ratio', 0.0)):.3f}")
        lines.append(f"- provenance_coverage_ratio: {float(readiness.get('provenance_coverage_ratio', 0.0)):.3f}")
        lines.append(f"- citation_coverage_ratio: {float(readiness.get('citation_coverage_ratio', 0.0)):.3f}")
        lines.append(f"- statistical_adequacy_ratio: {float(readiness.get('statistical_adequacy_ratio', 0.0)):.3f}")
        lines.append(f"- ready_for_submission: {readiness.get('ready_for_submission')}")
        lines.append("")

    reference_catalog = report.get("reference_catalog", {}) if isinstance(report.get("reference_catalog", {}), dict) else {}
    if reference_catalog:
        lines.append("## Reference Dataset Fingerprint")
        lines.append("")
        lines.append(f"- dataset_fingerprint: {reference_catalog.get('dataset_fingerprint')}")
        coverage = reference_catalog.get("coverage", {}) if isinstance(reference_catalog.get("coverage", {}), dict) else {}
        lines.append(f"- doi_coverage_ratio: {float(coverage.get('doi_coverage_ratio', 0.0)):.3f}")
        lines.append(f"- title_coverage_ratio: {float(coverage.get('title_coverage_ratio', 0.0)):.3f}")
        lines.append(f"- sample_id_coverage_ratio: {float(coverage.get('sample_id_coverage_ratio', 0.0)):.3f}")
        lines.append("")

    runtime_env = report.get("runtime_environment", {}) if isinstance(report.get("runtime_environment", {}), dict) else {}
    if runtime_env:
        lines.append("## Reproducibility Fingerprint")
        lines.append("")
        lines.append(f"- python_version: {runtime_env.get('python_version')}")
        lines.append(f"- platform: {runtime_env.get('platform')}")
        lines.append(f"- manifest_count: {runtime_env.get('manifest_count')}")
        lines.append(f"- reproducibility_fingerprint: {runtime_env.get('reproducibility_fingerprint')}")
        lines.append("")

    lines.append("## Drift vs Previous Report")
    lines.append("")
    drift = report.get("drift", {})
    if drift:
        for key, value in drift.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- No previous report available.")
    lines.append("")
    lines.append("## Study Validation Details")
    lines.append("")
    for row in report["study_validation"]:
        state = "PASS" if row["is_valid"] else "FAIL"
        lines.append(f"- {row['study_file']}: {state} (errors={row['errors']}, warnings={row['warnings']})")
    return "\n".join(lines) + "\n"


def generate_release_validation_report(
    project_root: str | Path,
    studies_dir: str | Path,
    results_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, Path]:
    root = Path(project_root)
    studies_path = Path(studies_dir)
    results_path = Path(results_dir)
    studies = _collect_study_validation(Path(studies_dir))
    runtime = _collect_runtime_validation(results_path)
    reference_catalog = _collect_reference_catalog(studies_path)
    runtime_environment = _collect_runtime_environment(results_path)
    summary = _summarize(studies, runtime, reference_catalog)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    latest_json = output_path / "release_validation_report_latest.json"
    previous = _load_json(latest_json) if latest_json.exists() else {}

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "studies_dir": str(studies_path),
        "results_dir": str(results_path),
        "summary": summary,
        "reference_catalog": reference_catalog,
        "runtime_environment": runtime_environment,
        "study_validation": studies,
        "runtime_validation": runtime,
    }
    report["drift"] = _compute_drift(summary, previous) if previous else {}

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = output_path / f"release_validation_report_{stamp}.json"
    md_path = output_path / f"release_validation_report_{stamp}.md"

    json_text = json.dumps(report, indent=2)
    md_text = _to_markdown(report)

    json_path.write_text(json_text, encoding="utf-8")
    md_path.write_text(md_text, encoding="utf-8")
    latest_json.write_text(json_text, encoding="utf-8")
    (output_path / "release_validation_report_latest.md").write_text(md_text, encoding="utf-8")

    runtime_frame = pd.DataFrame(runtime)
    if not runtime_frame.empty:
        runtime_frame.to_csv(output_path / f"release_validation_runtime_snapshot_{stamp}.csv", index=False)

    return {
        "json": json_path,
        "markdown": md_path,
        "latest_json": latest_json,
        "latest_markdown": output_path / "release_validation_report_latest.md",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ShieldLab G4 release validation report artifacts.")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument("--studies-dir", default=None)
    parser.add_argument("--results-dir", default=None)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    root = Path(args.project_root)
    studies_dir = Path(args.studies_dir) if args.studies_dir else root / "configs" / "studies"
    results_dir = Path(args.results_dir) if args.results_dir else root / "build" / "results"
    output_dir = Path(args.output_dir) if args.output_dir else root / "docs" / "validation"

    paths = generate_release_validation_report(
        project_root=root,
        studies_dir=studies_dir,
        results_dir=results_dir,
        output_dir=output_dir,
    )
    for key, value in paths.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
