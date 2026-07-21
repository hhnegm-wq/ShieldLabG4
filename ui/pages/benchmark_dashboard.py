"""Benchmark dashboard page: acceptance status, drift metrics, and provenance coverage."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

_UI_DIR = Path(__file__).resolve().parent.parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from bootstrap import ensure_project_paths  # noqa: E402

ensure_project_paths()

import config  # noqa: E402
from components.platform_settings import get_platform_settings
from components.layout import render_page_hero
from components.enterprise_ui import render_kpi_strip, render_panel_header, render_breadcrumb
from shieldlab.io.release_gate import evaluate_release_gate, policy_for_profile


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _load_validation_summaries(root: Path) -> list[dict]:
    rows: list[dict] = []
    if not root.exists():
        return rows
    for summary_file in sorted(root.glob("*/validation_summary.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(summary_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        benchmark = payload.get("benchmark_summary", {}) if isinstance(payload.get("benchmark_summary", {}), dict) else {}
        quantities = benchmark.get("quantities", {}) if isinstance(benchmark.get("quantities", {}), dict) else {}
        rows.append(
            {
                "result_set": Path(payload.get("result_dir", summary_file.parent)).name,
                "study_file": Path(payload.get("study_file", "")).name,
                "benchmark_status": payload.get("benchmark_status", benchmark.get("status", "unavailable")),
                "has_thresholds": bool(benchmark.get("has_thresholds", False)),
                "metric_count": len(quantities),
                "run_count": int(payload.get("run_summary_count", 0) or 0),
                "reference_comparison": bool(payload.get("reference_comparison_exists", False)),
                "buildup_comparison": bool(payload.get("buildup_comparison_exists", False)),
                "assumptions_present": isinstance(payload.get("assumptions"), dict) and bool(payload.get("assumptions")),
                "literature_sources_present": isinstance(payload.get("literature_sources"), dict) and bool(payload.get("literature_sources")),
                "provenance_manifest": bool((summary_file.parent / "provenance_manifest.json").exists()),
                "summary_path": str(summary_file),
            }
        )
    return rows


def _status_emoji(status: str) -> str:
    status_l = str(status).lower()
    if status_l == "passed":
        return "passed"
    if status_l == "failed":
        return "failed"
    if status_l == "available":
        return "available"
    return "unavailable"


def _load_release_report_trends(validation_dir: Path) -> pd.DataFrame:
    rows: list[dict] = []
    if not validation_dir.exists():
        return pd.DataFrame()
    for report_path in sorted(validation_dir.glob("release_validation_report_*.json"), key=lambda p: p.stat().st_mtime):
        payload = _load_json(report_path)
        summary = payload.get("summary", {}) if isinstance(payload.get("summary", {}), dict) else {}
        readiness = summary.get("q1_readiness", {}) if isinstance(summary.get("q1_readiness", {}), dict) else {}
        generated_at = payload.get("generated_at_utc")
        try:
            generated_dt = datetime.fromisoformat(str(generated_at).replace("Z", "+00:00")) if generated_at else datetime.fromtimestamp(report_path.stat().st_mtime)
        except ValueError:
            generated_dt = datetime.fromtimestamp(report_path.stat().st_mtime)
        rows.append(
            {
                "generated_at": generated_dt,
                "release_gate": str(summary.get("release_gate", "unknown")),
                "study_error_count": int(summary.get("study_error_count", 0) or 0),
                "failed_benchmark_sets": int(summary.get("failed_benchmark_sets", 0) or 0),
                "runtime_result_sets": int(summary.get("runtime_result_sets", 0) or 0),
                "threshold_coverage_ratio": float(readiness.get("threshold_coverage_ratio", 0.0) or 0.0),
                "provenance_coverage_ratio": float(readiness.get("provenance_coverage_ratio", 0.0) or 0.0),
                "citation_coverage_ratio": float(readiness.get("citation_coverage_ratio", 0.0) or 0.0),
                "statistical_adequacy_ratio": float(readiness.get("statistical_adequacy_ratio", 0.0) or 0.0),
                "ready_for_submission": bool(readiness.get("ready_for_submission", False)),
                "report_path": str(report_path),
            }
        )
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows).sort_values("generated_at")
    frame["generated_at"] = pd.to_datetime(frame["generated_at"])  # type: ignore[arg-type]
    return frame


settings = get_platform_settings()

if bool(settings.get("show_hero_sections", True)):
    render_page_hero(
        "Benchmark Dashboard",
        "Monitor benchmark status, threshold compliance, citation quality, statistical adequacy, and provenance completeness across all result sets.",
        "Scientific Governance",
    )
else:
    st.title("Benchmark Dashboard")

render_breadcrumb(["ShieldLab G4", "Analysis"], current="Benchmark Dashboard")

rows = _load_validation_summaries(config.RESULTS_DIR)
if not rows:
    st.info("No validation_summary.json files found under the configured results directory.")
    st.stop()

frame = pd.DataFrame(rows)
frame["benchmark_status"] = frame["benchmark_status"].astype(str)

status_counts = frame["benchmark_status"].value_counts(dropna=False).to_dict()
render_kpi_strip(
    [
        {"label": "Result Sets", "value": int(frame.shape[0]), "trend": "Tracked", "trend_state": "steady", "footnote": "Validation summaries indexed"},
        {"label": "Passed", "value": int(status_counts.get("passed", 0)), "trend": "Gate", "trend_state": "up", "footnote": "Benchmark-compliant sets"},
        {"label": "Failed", "value": int(status_counts.get("failed", 0)), "trend": "Attention", "trend_state": "warn", "footnote": "Sets outside thresholds"},
        {"label": "Threshold-backed", "value": int(frame["has_thresholds"].sum()), "trend": "Policy", "trend_state": "steady", "footnote": "Acceptance criteria available"},
        {"label": "Provenance", "value": int(frame["provenance_manifest"].sum()), "trend": "Manifest", "trend_state": "up", "footnote": "With provenance manifest"},
        {"label": "Assumptions", "value": int(frame["assumptions_present"].sum()), "trend": "Model", "trend_state": "steady", "footnote": "With study assumptions"},
    ],
    title="ShieldLab Governance Control Strip",
    subtitle="Release readiness, benchmark pass/fail distribution, and evidence completeness at a glance.",
)

render_panel_header(
    "Status Grid",
    "Per-result benchmark and provenance coverage matrix.",
    legend_items=[("Passed", "#10b981"), ("Failed", "#ef4444"), ("Available", "#3b82f6")],
    controls=["Grid", "Coverage", "Traceability"],
)
display = frame.copy()
display["benchmark_status"] = display["benchmark_status"].map(_status_emoji)
display["reference_comparison"] = display["reference_comparison"].map(lambda v: "yes" if v else "no")
display["buildup_comparison"] = display["buildup_comparison"].map(lambda v: "yes" if v else "no")
display["provenance_manifest"] = display["provenance_manifest"].map(lambda v: "yes" if v else "no")
display["assumptions_present"] = display["assumptions_present"].map(lambda v: "yes" if v else "no")
display["literature_sources_present"] = display["literature_sources_present"].map(lambda v: "yes" if v else "no")

st.dataframe(
    display[
        [
            "result_set",
            "study_file",
            "benchmark_status",
            "metric_count",
            "run_count",
            "reference_comparison",
            "buildup_comparison",
            "provenance_manifest",
            "assumptions_present",
            "literature_sources_present",
            "summary_path",
        ]
    ],
    width="stretch",
    hide_index=True,
)

st.caption(
    "This dashboard is generated from validation_summary.json files and companion provenance_manifest.json artifacts in each result folder."
)

render_panel_header(
    "Release Drift Trends",
    "Historical gate movement, benchmark regressions, and publication-readiness coverage ratios.",
    controls=["Trend", "Coverage", "CSV"],
)
trend_df = _load_release_report_trends(config.PROJECT_ROOT / "docs" / "validation")
if trend_df.empty:
    st.info("No release_validation_report_*.json files found yet under docs/validation.")
else:
    c_t1, c_t2, c_t3 = st.columns(3)
    latest = trend_df.iloc[-1]
    c_t1.metric("Latest failed benchmark sets", int(latest["failed_benchmark_sets"]))
    c_t2.metric("Latest threshold coverage", f"{float(latest['threshold_coverage_ratio']) * 100.0:.1f}%")
    c_t3.metric("Latest provenance coverage", f"{float(latest['provenance_coverage_ratio']) * 100.0:.1f}%")
    c_t4, c_t5 = st.columns(2)
    c_t4.metric("Latest citation coverage", f"{float(latest['citation_coverage_ratio']) * 100.0:.1f}%")
    c_t5.metric("Latest statistical adequacy", f"{float(latest['statistical_adequacy_ratio']) * 100.0:.1f}%")

    trend_plot = trend_df.set_index("generated_at")[["study_error_count", "failed_benchmark_sets"]]
    st.markdown("**Error and benchmark regression trend**")
    st.line_chart(trend_plot, width="stretch")

    readiness_plot = trend_df.set_index("generated_at")[
        [
            "threshold_coverage_ratio",
            "provenance_coverage_ratio",
            "citation_coverage_ratio",
            "statistical_adequacy_ratio",
        ]
    ]
    st.markdown("**Coverage trend for publication readiness**")
    st.line_chart(readiness_plot, width="stretch")

    display_trend = trend_df.copy()
    display_trend["generated_at"] = display_trend["generated_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
    display_trend["ready_for_submission"] = display_trend["ready_for_submission"].map(lambda v: "yes" if v else "no")
    display_trend["release_gate"] = display_trend["release_gate"].map(_status_emoji)
    st.dataframe(
        display_trend[
            [
                "generated_at",
                "release_gate",
                "study_error_count",
                "failed_benchmark_sets",
                "runtime_result_sets",
                "threshold_coverage_ratio",
                "provenance_coverage_ratio",
                "citation_coverage_ratio",
                "statistical_adequacy_ratio",
                "ready_for_submission",
                "report_path",
            ]
        ],
        width="stretch",
        hide_index=True,
    )
    st.download_button(
        "Download trend table (CSV)",
        data=trend_df.to_csv(index=False).encode("utf-8"),
        file_name="release_validation_trends.csv",
        mime="text/csv", width="stretch",
    )

latest_report = _load_json(config.PROJECT_ROOT / "docs" / "validation" / "release_validation_report_latest.json")
if latest_report:
    st.markdown("### Gate Diagnosis")
    selected_profile = st.selectbox(
        "Gate profile",
        ["release", "dev"],
        index=0,
        help="release is strict for publication gating; dev is lenient for in-progress validation.",
    )
    policy = policy_for_profile(selected_profile)
    gate_passed, reasons = evaluate_release_gate(latest_report, policy)
    if gate_passed:
        st.success(f"Gate passes under '{selected_profile}' profile.")
    else:
        st.error(f"Gate fails under '{selected_profile}' profile.")
        for reason in reasons:
            st.write(f"- {reason}")

        fix_map = {
            "threshold_coverage_ratio": "Re-run or enrich benchmark sets so each validation summary contains threshold-backed benchmark metrics.",
            "provenance_coverage_ratio": "Ensure each result set includes provenance_manifest.json by running through the standard runner pipeline.",
            "citation_coverage_ratio": "Fill missing paper DOI fields in benchmark study reference sections.",
            "statistical_adequacy_ratio": "Increase run.histories to at least 5000 for benchmarked result sets.",
            "study_error_count": "Resolve study validator errors in literature_benchmark_*.json files.",
            "failed_benchmark_sets": "Address failed benchmark metrics or review reference acceptance thresholds.",
            "ready_for_submission": "Meet all readiness thresholds and remove benchmark failures.",
        }
        st.markdown("**Actionable fixes**")
        emitted: set[str] = set()
        for reason in reasons:
            for key, guidance in fix_map.items():
                if key in reason and guidance not in emitted:
                    st.write(f"- {guidance}")
                    emitted.add(guidance)



