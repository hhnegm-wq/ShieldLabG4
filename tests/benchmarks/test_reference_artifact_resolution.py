import json

import pandas as pd

from shieldlab.analysis.comparison import resolve_reference_artifacts


def _write_study_with_coefficients(path, mac_ref: float = 0.25, mu_ref: float = 0.5):
    study = {
        "references": {
            "coefficients": [
                {
                    "energy": 662,
                    "energy_unit": "keV",
                    "source": "synthetic",
                    "linear_attenuation_cm_inv": mu_ref,
                    "mass_attenuation_cm2_g": mac_ref,
                }
            ]
        }
    }
    path.write_text(json.dumps(study), encoding="utf-8")


def test_resolve_reference_artifacts_recomputes_stale_comparison_when_sweep_provided(tmp_path):
    result_dir = tmp_path / "results"
    result_dir.mkdir()

    study_file = tmp_path / "study.json"
    _write_study_with_coefficients(study_file)

    # Existing stale comparison lacks uncertainty-aware columns.
    stale = pd.DataFrame(
        [
            {
                "energy": 662,
                "energy_unit": "keV",
                "mass_attenuation_cm2_g_percent_difference": 99.0,
            }
        ]
    )
    stale.to_csv(result_dir / "reference_comparison.csv", index=False)

    sweep = pd.DataFrame(
        [
            {
                "energy": 662,
                "energy_unit": "keV",
                "events": 10000,
                "attenuation_estimate_type": "direct",
                "transmission_fraction": 0.37,
                "transmission_fraction_std": 0.0048,
                "transmission_fraction_ci95_half_width": 0.0094,
                "reflection_fraction": 0.05,
                "reflection_fraction_std": 0.0022,
                "reflection_fraction_ci95_half_width": 0.0043,
                "absorption_fraction": 0.58,
                "absorption_fraction_std": 0.0049,
                "absorption_fraction_ci95_half_width": 0.0096,
                "linear_attenuation_cm_inv": 0.5,
                "linear_attenuation_std_cm_inv": 0.01,
                "mass_attenuation_cm2_g": 0.25,
                "mass_attenuation_std_cm2_g": 0.005,
            }
        ]
    )

    _, comparison, _ = resolve_reference_artifacts(result_dir, {"study_file": str(study_file)}, sweep)

    assert "mass_attenuation_cm2_g_normalized_residual" in comparison.columns
    assert "linear_attenuation_cm_inv_normalized_residual" in comparison.columns
    assert comparison.iloc[0]["mass_attenuation_cm2_g_percent_difference"] != 99.0


def test_resolve_reference_artifacts_keeps_uncertainty_aware_comparison(tmp_path):
    result_dir = tmp_path / "results"
    result_dir.mkdir()

    study_file = tmp_path / "study.json"
    _write_study_with_coefficients(study_file)

    current = pd.DataFrame(
        [
            {
                "energy": 662,
                "energy_unit": "keV",
                "mass_attenuation_cm2_g_percent_difference": 1.2,
                "mass_attenuation_std_cm2_g_simulated": 0.004,
                "mass_attenuation_cm2_g_normalized_residual": 0.3,
            }
        ]
    )
    current.to_csv(result_dir / "reference_comparison.csv", index=False)

    sweep = pd.DataFrame(
        [
            {
                "energy": 662,
                "energy_unit": "keV",
                "mass_attenuation_cm2_g": 0.25,
                "mass_attenuation_std_cm2_g": 0.005,
            }
        ]
    )

    _, comparison, _ = resolve_reference_artifacts(result_dir, {"study_file": str(study_file)}, sweep)

    assert comparison.iloc[0]["mass_attenuation_cm2_g_percent_difference"] == 1.2
    assert "mass_attenuation_cm2_g_normalized_residual" in comparison.columns
