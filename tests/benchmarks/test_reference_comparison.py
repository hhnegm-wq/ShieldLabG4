import math

import pandas as pd

from shieldlab.analysis.comparison import compare_buildup_observable, compare_coefficients, summarize_reference_comparison


def test_compare_coefficients_carries_uncertainty_and_normalized_residuals():
    sweep = pd.DataFrame(
        [
            {
                "energy": 662,
                "energy_unit": "keV",
                "events": 50000,
                "attenuation_estimate_type": "primary_track_world_boundary",
                "transmission_fraction": 0.512,
                "transmission_fraction_std": 0.0022,
                "transmission_fraction_ci95_half_width": 0.0043,
                "reflection_fraction": 0.101,
                "reflection_fraction_std": 0.0013,
                "reflection_fraction_ci95_half_width": 0.0025,
                "absorption_fraction": 0.387,
                "absorption_fraction_std": 0.0021,
                "absorption_fraction_ci95_half_width": 0.0041,
                "linear_attenuation_cm_inv": 0.812,
                "linear_attenuation_std_cm_inv": 0.018,
                "mass_attenuation_cm2_g": 0.264,
                "mass_attenuation_std_cm2_g": 0.006,
            }
        ]
    )
    reference = pd.DataFrame(
        [
            {
                "energy": 662,
                "energy_unit": "keV",
                "source": "paper",
                "linear_attenuation_cm_inv": 0.800,
                "mass_attenuation_cm2_g": 0.250,
            }
        ]
    )

    comparison = compare_coefficients(sweep, reference)

    assert comparison.shape[0] == 1
    row = comparison.iloc[0]
    assert math.isclose(row["linear_attenuation_std_cm_inv_simulated"], 0.018, rel_tol=1e-9)
    assert math.isclose(row["mass_attenuation_std_cm2_g_simulated"], 0.006, rel_tol=1e-9)
    assert math.isclose(row["linear_attenuation_cm_inv_percent_difference"], 1.5, rel_tol=1e-9)
    assert math.isclose(row["mass_attenuation_cm2_g_percent_difference"], 5.6, rel_tol=1e-9)
    assert math.isclose(row["linear_attenuation_cm_inv_normalized_residual"], (0.812 - 0.800) / 0.018, rel_tol=1e-9)
    assert math.isclose(row["mass_attenuation_cm2_g_normalized_residual"], (0.264 - 0.250) / 0.006, rel_tol=1e-9)


def test_summarize_reference_comparison_applies_thresholds():
    comparison = pd.DataFrame(
        [
            {
                "mass_attenuation_cm2_g_percent_difference": 3.0,
                "linear_attenuation_cm_inv_percent_difference": 7.0,
            },
            {
                "mass_attenuation_cm2_g_percent_difference": -4.0,
                "linear_attenuation_cm_inv_percent_difference": -6.0,
            },
        ]
    )
    acceptance = {
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
    }

    summary = summarize_reference_comparison(comparison, acceptance)

    assert summary["status"] == "failed"
    assert summary["has_thresholds"] is True
    assert summary["quantities"]["mass_attenuation_cm2_g_percent_difference"]["status"] == "passed"
    assert summary["quantities"]["linear_attenuation_cm_inv_percent_difference"]["status"] == "failed"
    assert math.isclose(
        summary["quantities"]["mass_attenuation_cm2_g_percent_difference"]["mean_abs_percent_difference"],
        3.5,
        rel_tol=1e-9,
    )


def test_compare_buildup_observable_supports_acceptance_metrics():
    observable = pd.DataFrame(
        [
            {
                "energy": 15,
                "energy_unit": "keV",
                "mc_buildup_observable_count": 1.05,
                "mc_buildup_observable_energy": 1.15,
            },
            {
                "energy": 100,
                "energy_unit": "keV",
                "mc_buildup_observable_count": 1.08,
                "mc_buildup_observable_energy": 1.22,
            },
        ]
    )
    reference_buildup = pd.DataFrame(
        [
            {
                "energy": 0.015,
                "energy_unit": "MeV",
                "ebf_a": 0.0,
                "ebf_b": 1.10,
                "ebf_c": 1.0,
                "ebf_d": 0.0,
                "ebf_xk": 10.0,
            },
            {
                "energy": 0.1,
                "energy_unit": "MeV",
                "ebf_a": 0.0,
                "ebf_b": 1.20,
                "ebf_c": 1.0,
                "ebf_d": 0.0,
                "ebf_xk": 10.0,
            },
        ]
    )

    comparison = compare_buildup_observable(observable, reference_buildup, depth_mfp=5.0)
    assert comparison.shape[0] == 2
    assert "buildup_observable_energy_percent_difference" in comparison.columns

    acceptance = {
        "metrics": {
            "buildup_observable_energy_percent_difference": {
                "mean_abs_max": 50.0,
                "max_abs_max": 60.0,
            }
        }
    }
    summary = summarize_reference_comparison(comparison, acceptance)
    assert summary["status"] == "passed"
    assert summary["quantities"]["buildup_observable_energy_percent_difference"]["status"] == "passed"