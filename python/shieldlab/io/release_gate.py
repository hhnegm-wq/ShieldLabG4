from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GatePolicy:
    max_study_errors: int = 0
    max_failed_benchmark_sets: int = 0
    min_threshold_coverage: float = 0.95
    min_provenance_coverage: float = 0.95
    min_citation_coverage: float = 0.90
    min_statistical_adequacy: float = 0.80
    require_ready_for_submission: bool = True


GATE_PROFILES: dict[str, GatePolicy] = {
    "release": GatePolicy(
        max_study_errors=0,
        max_failed_benchmark_sets=0,
        min_threshold_coverage=0.95,
        min_provenance_coverage=0.95,
        min_citation_coverage=0.90,
        min_statistical_adequacy=0.80,
        require_ready_for_submission=True,
    ),
    "dev": GatePolicy(
        max_study_errors=999,
        max_failed_benchmark_sets=999,
        min_threshold_coverage=0.0,
        min_provenance_coverage=0.0,
        min_citation_coverage=0.0,
        min_statistical_adequacy=0.0,
        require_ready_for_submission=False,
    ),
}


def policy_for_profile(profile: str) -> GatePolicy:
    key = str(profile).strip().lower()
    return GATE_PROFILES.get(key, GATE_PROFILES["release"])


def _load_report(report_path: Path) -> dict[str, Any]:
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def evaluate_release_gate(report: dict[str, Any], policy: GatePolicy) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    summary = report.get("summary", {}) if isinstance(report.get("summary", {}), dict) else {}
    readiness = summary.get("q1_readiness", {}) if isinstance(summary.get("q1_readiness", {}), dict) else {}

    study_error_count = int(summary.get("study_error_count", 0) or 0)
    failed_benchmark_sets = int(summary.get("failed_benchmark_sets", 0) or 0)
    threshold_coverage = float(readiness.get("threshold_coverage_ratio", 0.0) or 0.0)
    provenance_coverage = float(readiness.get("provenance_coverage_ratio", 0.0) or 0.0)
    citation_coverage = float(readiness.get("citation_coverage_ratio", 0.0) or 0.0)
    statistical_adequacy = float(readiness.get("statistical_adequacy_ratio", 0.0) or 0.0)
    ready_for_submission = bool(readiness.get("ready_for_submission", False))

    if study_error_count > policy.max_study_errors:
        reasons.append(
            f"study_error_count={study_error_count} exceeds max_study_errors={policy.max_study_errors}"
        )
    if failed_benchmark_sets > policy.max_failed_benchmark_sets:
        reasons.append(
            "failed_benchmark_sets="
            f"{failed_benchmark_sets} exceeds max_failed_benchmark_sets={policy.max_failed_benchmark_sets}"
        )
    if threshold_coverage < policy.min_threshold_coverage:
        reasons.append(
            f"threshold_coverage_ratio={threshold_coverage:.3f} below min_threshold_coverage={policy.min_threshold_coverage:.3f}"
        )
    if provenance_coverage < policy.min_provenance_coverage:
        reasons.append(
            f"provenance_coverage_ratio={provenance_coverage:.3f} below min_provenance_coverage={policy.min_provenance_coverage:.3f}"
        )
    if citation_coverage < policy.min_citation_coverage:
        reasons.append(
            f"citation_coverage_ratio={citation_coverage:.3f} below min_citation_coverage={policy.min_citation_coverage:.3f}"
        )
    if statistical_adequacy < policy.min_statistical_adequacy:
        reasons.append(
            "statistical_adequacy_ratio="
            f"{statistical_adequacy:.3f} below min_statistical_adequacy={policy.min_statistical_adequacy:.3f}"
        )
    if policy.require_ready_for_submission and not ready_for_submission:
        reasons.append("q1_readiness.ready_for_submission is false")

    return len(reasons) == 0, reasons


def main() -> None:
    parser = argparse.ArgumentParser(description="Fail CI when release validation report violates quality gates.")
    parser.add_argument("--profile", choices=["dev", "release"], default="release")
    parser.add_argument(
        "--report",
        default=str(
            Path(__file__).resolve().parents[3]
            / "docs"
            / "validation"
            / "release_validation_report_latest.json"
        ),
        help="Path to release validation report JSON.",
    )
    parser.add_argument("--max-study-errors", type=int, default=None)
    parser.add_argument("--max-failed-benchmark-sets", type=int, default=None)
    parser.add_argument("--min-threshold-coverage", type=float, default=None)
    parser.add_argument("--min-provenance-coverage", type=float, default=None)
    parser.add_argument("--min-citation-coverage", type=float, default=None)
    parser.add_argument("--min-statistical-adequacy", type=float, default=None)
    parser.add_argument("--allow-not-ready", action="store_true", default=False)
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        raise SystemExit(f"Release report not found: {report_path}")

    report = _load_report(report_path)
    base = policy_for_profile(args.profile)
    policy = GatePolicy(
        max_study_errors=base.max_study_errors if args.max_study_errors is None else args.max_study_errors,
        max_failed_benchmark_sets=base.max_failed_benchmark_sets
        if args.max_failed_benchmark_sets is None
        else args.max_failed_benchmark_sets,
        min_threshold_coverage=base.min_threshold_coverage
        if args.min_threshold_coverage is None
        else args.min_threshold_coverage,
        min_provenance_coverage=base.min_provenance_coverage
        if args.min_provenance_coverage is None
        else args.min_provenance_coverage,
        min_citation_coverage=base.min_citation_coverage
        if args.min_citation_coverage is None
        else args.min_citation_coverage,
        min_statistical_adequacy=base.min_statistical_adequacy
        if args.min_statistical_adequacy is None
        else args.min_statistical_adequacy,
        require_ready_for_submission=False if args.allow_not_ready else base.require_ready_for_submission,
    )

    passed, reasons = evaluate_release_gate(report, policy)
    if passed:
        print("Release gate PASSED")
        raise SystemExit(0)

    print("Release gate FAILED")
    for reason in reasons:
        print(f"- {reason}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
