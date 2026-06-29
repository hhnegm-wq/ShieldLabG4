import json
from pathlib import Path

from shieldlab.io.release_validation_report import generate_release_validation_report


def _write_study(path: Path, *, valid: bool) -> None:
    payload = {
        "name": path.stem,
        "study_schema_version": "1.0",
        "materials": [
            {
                "name": "ShieldA",
                "density_g_cm3": 11.35 if valid else -1.0,
                "formula": "Pb",
            }
        ],
        "source": {"particle": "gamma", "energy": 662, "energy_unit": "keV", "direction": [1, 0, 0]},
        "geometry": {
            "type": "slab",
            "layers": [{"material": "ShieldA", "thickness_cm": 2.0, "divisions": 1}],
        },
        "run": {"histories": 5000, "validation_mode": "benchmark_narrow_beam", "energy_grid": [662]},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_validation_summary(result_dir: Path, *, status: str) -> None:
    payload = {
        "status": "completed",
        "study_file": "literature_benchmark_fixture.json",
        "result_dir": str(result_dir),
        "run_summary_count": 1,
        "benchmark_status": status,
        "benchmark_summary": {
            "status": status,
            "has_thresholds": True,
            "quantities": {
                "mass_attenuation_cm2_g_percent_difference": {
                    "status": status,
                    "mean_abs_percent_difference": 1.2,
                    "max_abs_percent_difference": 2.4,
                    "mean_signed_percent_difference": 0.4,
                    "count": 1,
                    "thresholds": {"mean_abs_max": 5.0, "max_abs_max": 10.0},
                }
            },
        },
    }
    (result_dir / "validation_summary.json").write_text(json.dumps(payload), encoding="utf-8")
    (result_dir / "provenance_manifest.json").write_text("{}", encoding="utf-8")


def test_generate_release_validation_report_writes_json_and_markdown(tmp_path):
    project_root = tmp_path / "repo"
    studies_dir = project_root / "configs" / "studies"
    results_dir = project_root / "build" / "results"
    output_dir = project_root / "docs" / "validation"
    studies_dir.mkdir(parents=True)
    (results_dir / "fixture_result").mkdir(parents=True)

    _write_study(studies_dir / "literature_benchmark_fixture_valid.json", valid=True)
    _write_study(studies_dir / "literature_benchmark_fixture_invalid.json", valid=False)
    _write_validation_summary(results_dir / "fixture_result", status="failed")

    paths = generate_release_validation_report(
        project_root=project_root,
        studies_dir=studies_dir,
        results_dir=results_dir,
        output_dir=output_dir,
    )

    assert paths["json"].exists()
    assert paths["markdown"].exists()
    assert paths["latest_json"].exists()
    assert paths["latest_markdown"].exists()

    payload = json.loads(paths["latest_json"].read_text(encoding="utf-8"))
    assert payload["summary"]["study_count"] == 2
    assert payload["summary"]["study_error_count"] >= 1
    assert payload["summary"]["failed_benchmark_sets"] == 1
    assert payload["summary"]["release_gate"] == "fail"
    assert "q1_readiness" in payload["summary"]
    assert payload["summary"]["q1_readiness"]["ready_for_submission"] is False
    assert "citation_coverage_ratio" in payload["summary"]["q1_readiness"]
    assert "statistical_adequacy_ratio" in payload["summary"]["q1_readiness"]
    assert "reference_catalog" in payload
    assert "dataset_fingerprint" in payload["reference_catalog"]
    assert "runtime_environment" in payload
    assert "reproducibility_fingerprint" in payload["runtime_environment"]

    # Second run should include drift section against previous report.
    paths2 = generate_release_validation_report(
        project_root=project_root,
        studies_dir=studies_dir,
        results_dir=results_dir,
        output_dir=output_dir,
    )
    payload2 = json.loads(paths2["latest_json"].read_text(encoding="utf-8"))
    assert "drift" in payload2
    assert "study_error_count_delta" in payload2["drift"]
