from pathlib import Path

import pandas as pd
import pytest

from shieldlab.analysis import collect_buildup_observable


def test_collect_buildup_observable_writes_summary(tmp_path):
    result_dir = tmp_path / "results"
    run_dir = result_dir / "E_662_keV"
    run_dir.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "events": 1000,
                "transmitted": 400,
                "reflected": 50,
                "total_thickness_cm": 2.0,
                "transmission_fraction": 0.4,
                "reflection_fraction": 0.05,
                "absorption_fraction": 0.55,
                "linear_attenuation_cm_inv": 0.46,
                "attenuation_estimate_type": "direct",
            }
        ]
    ).to_csv(run_dir / "run_summary.csv", index=False)

    pd.DataFrame(
        [
            {
                "particle_name": "gamma",
                "count": 50,
                "total_kinetic_energy_MeV": 12.5,
                "mean_kinetic_energy_MeV": 0.25,
                "count_per_primary_event": 0.05,
                "fraction_of_events_with_secondary": 0.05,
            },
            {
                "particle_name": "e-",
                "count": 120,
                "total_kinetic_energy_MeV": 6.0,
                "mean_kinetic_energy_MeV": 0.05,
                "count_per_primary_event": 0.12,
                "fraction_of_events_with_secondary": 0.12,
            },
        ]
    ).to_csv(run_dir / "secondary_tally.csv", index=False)

    output = collect_buildup_observable(result_dir)
    assert output == result_dir / "buildup_observable_summary.csv"
    assert output.exists()

    summary = pd.read_csv(output)
    assert summary.shape[0] == 1
    row = summary.iloc[0]

    assert row["energy"] == pytest.approx(662.0)
    assert row["energy_unit"] == "keV"
    assert row["downstream_secondary_species"] == 2
    assert row["downstream_secondary_count_per_event"] == pytest.approx(0.17)
    assert row["downstream_secondary_energy_per_event_MeV"] == pytest.approx(0.0185)
    assert row["mc_buildup_observable_count"] == pytest.approx(1.17)
    assert row["mc_buildup_observable_energy"] == pytest.approx(1.0279456193)


def test_collect_buildup_observable_requires_secondary_tally(tmp_path):
    result_dir = tmp_path / "results"
    run_dir = result_dir / "E_100_keV"
    run_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "events": 100,
                "transmitted": 10,
                "reflected": 5,
                "total_thickness_cm": 1.0,
                "transmission_fraction": 0.1,
                "reflection_fraction": 0.05,
                "absorption_fraction": 0.85,
                "linear_attenuation_cm_inv": 2.3,
                "attenuation_estimate_type": "direct",
            }
        ]
    ).to_csv(run_dir / "run_summary.csv", index=False)

    with pytest.raises(ValueError, match="lcns5_buildup_observable.csv"):
        collect_buildup_observable(result_dir)


def test_collect_buildup_observable_prefers_lcns5_export(tmp_path):
    result_dir = tmp_path / "results"
    run_dir = result_dir / "E_1173_keV"
    run_dir.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "events": 2000,
                "transmitted": 900,
                "reflected": 100,
                "total_thickness_cm": 2.0,
                "transmission_fraction": 0.45,
                "reflection_fraction": 0.05,
                "absorption_fraction": 0.50,
                "linear_attenuation_cm_inv": 0.39,
                "attenuation_estimate_type": "direct",
            }
        ]
    ).to_csv(run_dir / "run_summary.csv", index=False)

    pd.DataFrame(
        [
            {
                "events": 2000,
                "secondary_total_count": 360,
                "secondary_total_kinetic_energy_MeV": 20.0,
                "secondary_count_per_primary_event": 0.18,
                "secondary_energy_per_primary_event_MeV": 0.01,
                "primary_downstream_photon_count": 1200,
                "total_downstream_photon_count": 1500,
                "primary_downstream_photon_energy_MeV": 70.0,
                "total_downstream_photon_energy_MeV": 90.0,
                "mc_buildup_observable_count": 1.18,
                "mc_buildup_observable_energy": 1.2857142857,
            }
        ]
    ).to_csv(run_dir / "lcns5_buildup_observable.csv", index=False)

    output = collect_buildup_observable(result_dir)
    summary = pd.read_csv(output)
    row = summary.iloc[0]

    assert row["downstream_secondary_count_per_event"] == pytest.approx(0.18)
    assert row["downstream_secondary_energy_per_event_MeV"] == pytest.approx(0.01)
    assert row["mc_buildup_observable_count"] == pytest.approx(1.18)
    assert row["mc_buildup_observable_energy"] == pytest.approx(1.2857142857)
