import json

from shieldlab.io.methods_export_pack import generate_methods_export_pack


def test_generate_methods_export_pack_writes_expected_artifacts(tmp_path):
    project_root = tmp_path / "repo"
    validation_dir = project_root / "docs" / "validation"
    output_dir = project_root / "docs" / "validation"
    validation_dir.mkdir(parents=True)

    release_payload = {
        "reference_catalog": {
            "entries": [
                {
                    "study_file": "literature_benchmark_fixture.json",
                    "paper_title": "Lead shielding benchmark",
                    "paper_doi": "10.1000/shieldlab.demo",
                    "sample_id": "PB-001",
                }
            ],
            "coverage": {"doi_coverage_ratio": 1.0, "title_coverage_ratio": 1.0, "sample_id_coverage_ratio": 1.0},
        },
        "summary": {
            "release_gate": "pass",
            "threshold_backed_sets": 2,
            "provenance_manifest_sets": 2,
            "benchmark_status_counts": {"passed": 2},
            "q1_readiness": {
                "threshold_coverage_ratio": 1.0,
                "provenance_coverage_ratio": 1.0,
                "ready_for_submission": True,
            },
        },
        "runtime_validation": [
            {
                "result_set": "set_a",
                "study_file": "literature_benchmark_fixture.json",
                "benchmark_status": "passed",
                "metrics": {
                    "mass_attenuation_cm2_g_percent_difference": {
                        "status": "passed",
                        "mean_abs_percent_difference": 1.5,
                        "max_abs_percent_difference": 3.0,
                        "thresholds": {"mean_abs_max": 5.0, "max_abs_max": 10.0},
                    }
                },
            }
        ],
    }
    (validation_dir / "release_validation_report_latest.json").write_text(
        json.dumps(release_payload), encoding="utf-8"
    )

    outputs = generate_methods_export_pack(project_root=project_root, output_dir=output_dir)

    assert outputs["json"].exists()
    assert outputs["markdown"].exists()
    assert outputs["latest_json"].exists()
    assert outputs["latest_markdown"].exists()
    assert outputs["benchmark_table_csv"].exists()

    payload = json.loads(outputs["latest_json"].read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"
    assert len(payload["equations"]) >= 4
    assert len(payload["uncertainty_statements"]) >= 3
    assert len(payload["bibliography"]) >= 1
    assert payload["bibliography"][0]["doi_url"] == "https://doi.org/10.1000/shieldlab.demo"
