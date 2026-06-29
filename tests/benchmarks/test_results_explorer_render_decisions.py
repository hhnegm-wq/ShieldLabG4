import pandas as pd
import pytest


@pytest.fixture
def resolved_artifacts_full():
    reference = pd.DataFrame(
        [{"energy": 662, "energy_unit": "keV", "mass_attenuation_cm2_g": 0.25, "source": "paper"}]
    )
    comparison = pd.DataFrame(
        [
            {
                "energy": 662,
                "energy_unit": "keV",
                "mass_attenuation_cm2_g_percent_difference": 1.4,
                "mass_attenuation_cm2_g_normalized_residual": 0.41,
            }
        ]
    )
    buildup = pd.DataFrame(
        [
            {
                "energy": 0.662,
                "energy_unit": "MeV",
                "zeq": 15.2,
                "ebf_a": 0.2,
                "ebf_b": 1.1,
                "ebf_c": 0.4,
                "ebf_d": -0.1,
                "ebf_xk": 12.0,
                "eabf_a": 0.2,
                "eabf_b": 1.1,
                "eabf_c": 0.4,
                "eabf_d": -0.1,
                "eabf_xk": 12.0,
            }
        ]
    )
    return reference, comparison, buildup


@pytest.fixture
def resolved_artifacts_no_reference():
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def _render_decisions(reference_df: pd.DataFrame, comparison_df: pd.DataFrame, buildup_df: pd.DataFrame) -> dict:
    return {
        "show_reference_overlay": not reference_df.empty,
        "show_comparison_table": not comparison_df.empty,
        "show_benchmark_summary": not comparison_df.empty,
        "show_normalized_residual_caption": (
            "mass_attenuation_cm2_g_normalized_residual" in comparison_df.columns
            or "linear_attenuation_cm_inv_normalized_residual" in comparison_df.columns
        ),
        "show_buildup_overlay": not buildup_df.empty,
    }


def test_render_decisions_with_full_resolved_artifacts(resolved_artifacts_full):
    decisions = _render_decisions(*resolved_artifacts_full)
    assert decisions == {
        "show_reference_overlay": True,
        "show_comparison_table": True,
        "show_benchmark_summary": True,
        "show_normalized_residual_caption": True,
        "show_buildup_overlay": True,
    }


def test_render_decisions_with_no_reference_artifacts(resolved_artifacts_no_reference):
    decisions = _render_decisions(*resolved_artifacts_no_reference)
    assert decisions == {
        "show_reference_overlay": False,
        "show_comparison_table": False,
        "show_benchmark_summary": False,
        "show_normalized_residual_caption": False,
        "show_buildup_overlay": False,
    }
