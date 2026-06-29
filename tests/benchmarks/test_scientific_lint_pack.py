import json
from pathlib import Path

from shieldlab.io.study_validator import validate_study, validate_study_file


def test_scientific_lint_pack_flags_unsupported_modes_and_impossible_regimes():
    study = {
        "name": "lint_fixture",
        "study_schema_version": "1.0",
        "materials": [
            {
                "name": "LowDensityHeavy",
                "density_g_cm3": 0.08,
                "phase": "solid",
                "formula": "PbO",
            }
        ],
        "source": {"particle": "gamma", "energy": 10, "energy_unit": "keV", "direction": [1, 0, 0]},
        "geometry": {
            "type": "slab",
            "layers": [{"material": "LowDensityHeavy", "thickness_cm": 150.0, "divisions": 1}],
        },
        "run": {
            "histories": 800,
            "validation_mode": "invalid_mode",
            "energy_grid": [10, 20],
        },
        "references": {
            "comparison_mode": "unsupported_mode",
        },
    }

    issues = validate_study(study)
    warnings = {(issue.path, issue.message) for issue in issues if issue.severity == "warning"}

    assert any(path == "run.validation_mode" for path, _ in warnings)
    assert any(path == "references.comparison_mode" for path, _ in warnings)
    assert any(path == "run.energy_grid" for path, _ in warnings)
    assert any(path == "materials[0].density_g_cm3" for path, _ in warnings)


def test_scientific_lint_pack_warns_for_benchmark_mode_without_reference_data(tmp_path):
    study = {
        "name": "lint_reference_fixture",
        "study_schema_version": "1.0",
        "materials": [{"name": "Pb", "density_g_cm3": 11.35, "formula": "Pb"}],
        "source": {"particle": "gamma", "energy": 662, "energy_unit": "keV", "direction": [1, 0, 0]},
        "geometry": {
            "type": "slab",
            "layers": [{"material": "Pb", "thickness_cm": 2.0, "divisions": 1}],
        },
        "run": {
            "histories": 5000,
            "validation_mode": "benchmark_narrow_beam",
            "energy_grid": [662],
        },
        "references": {
            "comparison_mode": "full",
        },
    }

    study_path = tmp_path / "study.json"
    study_path.write_text(json.dumps(study), encoding="utf-8")

    issues = validate_study_file(Path(study_path))
    warnings = {(issue.path, issue.message) for issue in issues if issue.severity == "warning"}

    assert any(path == "run.validation_mode" for path, _ in warnings)
    assert any(path == "references.comparison_mode" for path, _ in warnings)
