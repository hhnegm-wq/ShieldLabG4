import json
from pathlib import Path

import pandas as pd

from shieldlab.analysis.paper3_results import build_reference_coefficients, build_result_pack


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STUDY_FILE = PROJECT_ROOT / "configs" / "studies" / "paper3_hdpe_bi2o3_regime_a_baseline.json"


def test_paper3_result_pack_writes_reference_comparison_and_acceptance(tmp_path):
    result_dir = tmp_path / "results"
    result_dir.mkdir(parents=True)

    reference = build_reference_coefficients(STUDY_FILE)
    sweep = reference.rename(
        columns={
            "linear_attenuation_cm_inv": "linear_attenuation_cm_inv",
            "mass_attenuation_cm2_g": "mass_attenuation_cm2_g",
        }
    ).copy()
    sweep["events"] = 1000
    sweep["attenuation_estimate_type"] = "direct"
    sweep["transmission_fraction"] = 0.5
    sweep["transmission_fraction_std"] = 0.01
    sweep["transmission_fraction_ci95_half_width"] = 0.02
    sweep["reflection_fraction"] = 0.02
    sweep["reflection_fraction_std"] = 0.001
    sweep["reflection_fraction_ci95_half_width"] = 0.002
    sweep["absorption_fraction"] = 0.48
    sweep["absorption_fraction_std"] = 0.01
    sweep["absorption_fraction_ci95_half_width"] = 0.02
    sweep["linear_attenuation_std_cm_inv"] = 0.001
    sweep["mass_attenuation_std_cm2_g"] = 0.001
    sweep.to_csv(result_dir / "sweep_summary.csv", index=False)

    run_dir = result_dir / "E_662_keV"
    run_dir.mkdir()
    pd.DataFrame(
        [
            {
                "channel": "total_gamma",
                "particle_name": "gamma",
                "bin_index": 0,
                "energy_low_MeV": 0.001,
                "energy_high_MeV": 0.002,
                "count": 5,
            },
            {
                "channel": "total_gamma",
                "particle_name": "gamma",
                "bin_index": 1,
                "energy_low_MeV": 0.002,
                "energy_high_MeV": 0.004,
                "count": 7,
            },
        ]
    ).to_csv(run_dir / "downstream_spectrum.csv", index=False)

    outputs = build_result_pack(STUDY_FILE, result_dir, with_figures=True)

    comparison = pd.read_csv(outputs["reference_comparison"])
    acceptance = json.loads(outputs["acceptance"].read_text(encoding="utf-8"))

    assert not comparison.empty
    assert acceptance["benchmark_summary"]["status"] == "passed"
    assert acceptance["benchmark_summary"]["quantities"]["mass_attenuation_cm2_g_percent_difference"]["status"] == "passed"
    assert outputs["downstream_spectrum_summary"].exists()
    assert outputs["figure_f3_png"].exists()
    assert outputs["figure_f3_pdf"].exists()
    assert outputs["figure_transmission_png"].exists()
    assert outputs["figure_transmission_pdf"].exists()
    assert outputs["figure_spectrum_png"].exists()
    assert outputs["figure_spectrum_pdf"].exists()