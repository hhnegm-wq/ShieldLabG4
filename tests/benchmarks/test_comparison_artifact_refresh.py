import pandas as pd

from shieldlab.analysis.comparison import comparison_has_uncertainty_columns


def test_comparison_has_uncertainty_columns_false_for_empty_or_legacy_tables():
    assert comparison_has_uncertainty_columns(pd.DataFrame()) is False

    legacy = pd.DataFrame(
        [
            {
                "energy": 662,
                "energy_unit": "keV",
                "mass_attenuation_cm2_g_percent_difference": 2.5,
            }
        ]
    )
    assert comparison_has_uncertainty_columns(legacy) is False


def test_comparison_has_uncertainty_columns_true_for_uncertainty_aware_tables():
    uncertainty_aware = pd.DataFrame(
        [
            {
                "energy": 662,
                "energy_unit": "keV",
                "mass_attenuation_cm2_g_percent_difference": 2.5,
                "mass_attenuation_std_cm2_g_simulated": 0.004,
                "mass_attenuation_cm2_g_normalized_residual": 0.63,
            }
        ]
    )
    assert comparison_has_uncertainty_columns(uncertainty_aware) is True
