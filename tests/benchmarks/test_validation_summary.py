import json
from pathlib import Path

import pandas as pd

from shieldlab.io.runner import _write_validation_summary


def test_write_validation_summary_includes_benchmark_status_and_provenance(tmp_path):
    result_dir = tmp_path / "results"
    result_dir.mkdir()

    comparison = pd.DataFrame(
        [
            {
                "energy": 662,
                "energy_unit": "keV",
                "mass_attenuation_cm2_g_percent_difference": 7.5,
                "linear_attenuation_cm_inv_percent_difference": 3.0,
            }
        ]
    )
    comparison.to_csv(result_dir / "reference_comparison.csv", index=False)

    figure_dir = result_dir / "figures"
    figure_dir.mkdir()
    (figure_dir / "energy_plot.png").write_bytes(b"png")

    study_file = tmp_path / "study.json"
    study = {
        "source": {"particle": "gamma", "energy": 662, "energy_unit": "keV"},
        "geometry": {
            "type": "slab",
            "layers": [
                {"material": "ShieldA", "thickness_cm": 1.25},
                {"material": "ShieldB", "thickness_cm": 0.75},
            ],
        },
        "materials": [{"name": "ShieldA"}, {"name": "ShieldB"}],
        "run": {"validation_mode": "benchmark_narrow_beam", "physics_list": "emstandard_opt4"},
        "references": {
            "paper_title": "Synthetic benchmark paper",
            "paper_doi": "10.1000/example",
            "sample_id": "SYN-1",
            "coefficients": [{"energy": 662, "energy_unit": "keV", "mass_attenuation_cm2_g": 0.25}],
            "buildup_factors": {
                "source": "Synthetic buildup table",
                "coefficients": [{"energy": 0.662, "ebf": {"a": 0.1}}],
            },
            "acceptance_criteria": {
                "metrics": {
                    "mass_attenuation_cm2_g_percent_difference": {
                        "mean_abs_max": 5.0,
                        "max_abs_max": 10.0,
                    }
                }
            },
        },
    }
    study_file.write_text(json.dumps(study), encoding="utf-8")

    macro_file = tmp_path / "generated.mac"
    workbook = result_dir / "report.xlsx"
    sweep_file = result_dir / "sweep_summary.csv"
    study_validation_file = result_dir / "study_validation.csv"
    macro_file.write_text("/run/beamOn 1000\n", encoding="utf-8")
    workbook.write_bytes(b"xlsx")
    sweep_file.write_text("energy,energy_unit\n662,keV\n", encoding="utf-8")
    study_validation_file.write_text("severity,message\n", encoding="utf-8")

    output_path = _write_validation_summary(
        result_dir=result_dir,
        study=study,
        study_file=study_file,
        macro_file=macro_file,
        workbook=workbook,
        sweep_file=sweep_file,
        study_validation_file=study_validation_file,
        buildup_observable_file=None,
        buildup_comparison_file=None,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["reference_comparison_exists"] is True
    assert payload["buildup_observable_exists"] is False
    assert payload["buildup_comparison_exists"] is False
    assert payload["benchmark_status"] == "failed"
    assert payload["benchmark_summary"]["has_thresholds"] is True
    assert payload["benchmark_summary"]["quantities"]["mass_attenuation_cm2_g_percent_difference"]["status"] == "failed"
    assert payload["assumptions"]["layer_count"] == 2
    assert payload["assumptions"]["total_thickness_cm"] == 2.0
    assert payload["assumptions"]["materials"] == ["ShieldA", "ShieldB"]
    assert payload["literature_sources"]["paper_title"] == "Synthetic benchmark paper"
    assert payload["literature_sources"]["paper_doi"] == "10.1000/example"
    assert payload["literature_sources"]["sample_id"] == "SYN-1"
    assert payload["literature_sources"]["has_reference_coefficients"] is True
    assert payload["literature_sources"]["has_buildup_factors"] is True
    assert payload["literature_sources"]["buildup_source"] == "Synthetic buildup table"
    assert payload["figures"] == ["energy_plot.png"]
    assert Path(payload["study_file"]) == study_file
