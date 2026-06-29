import json
from pathlib import Path

import pandas as pd

from shieldlab.io.runner import run_study


def test_runner_writes_buildup_comparison_for_lcns5_style_study(tmp_path):
    build_dir = tmp_path / "build"
    result_dir = build_dir / "results" / "lcns5_runner_fixture"
    run_15 = result_dir / "E_15_keV"
    run_100 = result_dir / "E_100_keV"
    run_15.mkdir(parents=True)
    run_100.mkdir(parents=True)

    for run_dir, transmission, mu in ((run_15, 0.72, 0.22), (run_100, 0.53, 0.41)):
        pd.DataFrame(
            [
                {
                    "events": 5000,
                    "transmitted": int(5000 * transmission),
                    "reflected": 200,
                    "total_thickness_cm": 2.0,
                    "transmission_fraction": transmission,
                    "reflection_fraction": 0.04,
                    "absorption_fraction": 1.0 - transmission - 0.04,
                    "linear_attenuation_cm_inv": mu,
                    "attenuation_estimate_type": "direct",
                }
            ]
        ).to_csv(run_dir / "run_summary.csv", index=False)
        pd.DataFrame([{"density_g_cm3": 2.6251}]).to_csv(run_dir / "layer_energy_deposition.csv", index=False)
        pd.DataFrame(
            [
                {
                    "events": 5000,
                    "secondary_total_count": 600,
                    "secondary_total_kinetic_energy_MeV": 18.0,
                    "secondary_count_per_primary_event": 0.12,
                    "secondary_energy_per_primary_event_MeV": 0.0036,
                    "primary_downstream_photon_count": 3000,
                    "total_downstream_photon_count": 3900,
                    "primary_downstream_photon_energy_MeV": 150.0,
                    "total_downstream_photon_energy_MeV": 210.0,
                    "mc_buildup_observable_count": 1.12,
                    "mc_buildup_observable_energy": 1.4,
                }
            ]
        ).to_csv(run_dir / "lcns5_buildup_observable.csv", index=False)

    study_file = tmp_path / "lcns5_runner_fixture.json"
    study = {
        "name": "lcns5_runner_fixture",
        "description": "Synthetic LCNS5-style runner fixture",
        "materials": [
            {
                "name": "SLG_LCNS5_FIXTURE",
                "density_g_cm3": 2.6251,
                "phase": "solid",
                "formula_mass_fractions": {"SiO2": 1.0},
            }
        ],
        "source": {"particle": "gamma", "energy": 662, "energy_unit": "keV", "direction": [1, 0, 0]},
        "geometry": {
            "type": "slab",
            "transverse_size_cm": 10,
            "layers": [{"material": "SLG_LCNS5_FIXTURE", "thickness_cm": 2.0, "divisions": 1}],
        },
        "run": {
            "histories": 5000,
            "energy_grid": [15, 100],
            "physics_list": "emstandard_opt4",
            "output_dir": "results/lcns5_runner_fixture",
        },
        "references": {
            "paper_title": "Synthetic LCNS5 buildup fixture",
            "paper_doi": "10.1000/lcns5-fixture",
            "sample_id": "LCNS5_FIXTURE",
            "buildup_validation_depth_mfp": 5.0,
            "acceptance_criteria": {
                "metrics": {
                    "buildup_observable_energy_percent_difference": {
                        "mean_abs_max": 90.0,
                        "max_abs_max": 95.0,
                    }
                }
            },
            "buildup_factors": {
                "source": "synthetic",
                "energy_unit": "MeV",
                "coefficient_model": "G-P (Harima)",
                "coefficients": [
                    {
                        "energy": 0.015,
                        "zeq": 15.0,
                        "ebf": {"a": 0.0, "b": 1.2, "c": 1.0, "d": 0.0, "xk": 10.0},
                        "eabf": {"a": 0.0, "b": 1.2, "c": 1.0, "d": 0.0, "xk": 10.0},
                    },
                    {
                        "energy": 0.1,
                        "zeq": 15.5,
                        "ebf": {"a": 0.0, "b": 1.3, "c": 1.0, "d": 0.0, "xk": 10.0},
                        "eabf": {"a": 0.0, "b": 1.3, "c": 1.0, "d": 0.0, "xk": 10.0},
                    },
                ],
            },
        },
    }
    study_file.write_text(json.dumps(study), encoding="utf-8")

    outputs = run_study(
        study_file,
        build_dir=build_dir,
        skip_geant4=True,
        no_plots=True,
    )

    buildup_comparison = outputs["buildup_comparison"]
    assert buildup_comparison is not None
    assert buildup_comparison.exists()

    comparison_df = pd.read_csv(buildup_comparison)
    assert not comparison_df.empty
    assert "buildup_observable_energy_percent_difference" in comparison_df.columns

    validation_summary = outputs["validation_summary"]
    assert validation_summary is not None
    payload = json.loads(Path(validation_summary).read_text(encoding="utf-8"))
    assert payload["buildup_comparison_exists"] is True
    assert payload["benchmark_summary"]["quantities"]["buildup_observable_energy_percent_difference"]["status"] == "passed"
