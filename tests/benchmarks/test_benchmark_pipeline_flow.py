import json
from pathlib import Path

import pandas as pd

from shieldlab.analysis.comparison import compare_coefficients, load_reference_coefficients
from shieldlab.io.runner import _write_validation_summary
from shieldlab.io.sweep_collector import collect_sweep


def test_benchmark_pipeline_flow_from_sweep_to_validation_summary(tmp_path):
    result_dir = tmp_path / "results"
    run_dir = result_dir / "E_662_keV"
    run_dir.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "events": 10000,
                "transmitted": 3679,
                "reflected": 500,
                "total_thickness_cm": 2.0,
                "transmission_fraction": 0.3679,
                "reflection_fraction": 0.05,
                "absorption_fraction": 0.5821,
                "linear_attenuation_cm_inv": 0.5,
                "attenuation_estimate_type": "direct",
            }
        ]
    ).to_csv(run_dir / "run_summary.csv", index=False)
    pd.DataFrame([{"density_g_cm3": 2.0}]).to_csv(run_dir / "layer_energy_deposition.csv", index=False)

    study_file = tmp_path / "study.json"
    study = {
        "source": {"particle": "gamma", "energy": 662, "energy_unit": "keV"},
        "geometry": {
            "type": "slab",
            "layers": [{"material": "SLG_Test", "thickness_cm": 2.0}],
        },
        "materials": [{"name": "SLG_Test"}],
        "run": {"validation_mode": "benchmark_narrow_beam", "physics_list": "emstandard_opt4"},
        "references": {
            "paper_title": "Synthetic benchmark paper",
            "paper_doi": "10.1000/example-benchmark",
            "sample_id": "SYN-BENCH-1",
            "acceptance_criteria": {
                "metrics": {
                    "mass_attenuation_cm2_g_percent_difference": {
                        "mean_abs_max": 5.0,
                        "max_abs_max": 10.0,
                    },
                    "linear_attenuation_cm_inv_percent_difference": {
                        "mean_abs_max": 5.0,
                        "max_abs_max": 10.0,
                    },
                }
            },
            "coefficients": [
                {
                    "energy": 662,
                    "energy_unit": "keV",
                    "source": "synthetic",
                    "linear_attenuation_cm_inv": 0.498,
                    "mass_attenuation_cm2_g": 0.252,
                }
            ],
        },
    }
    study_file.write_text(json.dumps(study), encoding="utf-8")

    sweep_file = collect_sweep(result_dir)
    sweep_df = pd.read_csv(sweep_file)
    reference_df = load_reference_coefficients(study_file)
    comparison_df = compare_coefficients(sweep_df, reference_df)
    comparison_file = result_dir / "reference_comparison.csv"
    comparison_df.to_csv(comparison_file, index=False)

    macro_file = tmp_path / "generated.mac"
    workbook = result_dir / "report.xlsx"
    study_validation_file = result_dir / "study_validation.csv"
    macro_file.write_text("/run/beamOn 1000\n", encoding="utf-8")
    workbook.write_bytes(b"xlsx")
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
    comparison_out = pd.read_csv(comparison_file)

    assert payload["reference_comparison_exists"] is True
    assert payload["buildup_observable_exists"] is False
    assert payload["buildup_comparison_exists"] is False
    assert payload["benchmark_status"] == "passed"
    assert payload["benchmark_summary"]["status"] == "passed"
    assert payload["benchmark_summary"]["has_thresholds"] is True
    assert payload["benchmark_summary"]["quantities"]["mass_attenuation_cm2_g_percent_difference"]["status"] == "passed"
    assert payload["benchmark_summary"]["quantities"]["linear_attenuation_cm_inv_percent_difference"]["status"] == "passed"
    assert payload["literature_sources"]["paper_doi"] == "10.1000/example-benchmark"
    assert "mass_attenuation_cm2_g_normalized_residual" in comparison_out.columns
    assert "linear_attenuation_cm_inv_normalized_residual" in comparison_out.columns
    assert Path(payload["sweep_summary"]) == sweep_file
