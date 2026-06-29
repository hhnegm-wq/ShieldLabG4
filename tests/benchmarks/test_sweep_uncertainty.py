import math

import pandas as pd

from shieldlab.io.sweep_collector import collect_composition_sweep, collect_sweep, collect_thickness_sweep


def _write_run(result_dir, folder_name, summary_row, density):
    run_dir = result_dir / folder_name
    run_dir.mkdir(parents=True)
    pd.DataFrame([summary_row]).to_csv(run_dir / "run_summary.csv", index=False)
    pd.DataFrame([{"density_g_cm3": density}]).to_csv(run_dir / "layer_energy_deposition.csv", index=False)
    return run_dir


def test_collect_sweep_writes_uncertainty_columns_for_direct_estimator(tmp_path):
    result_dir = tmp_path / "energy_sweep"
    result_dir.mkdir()
    _write_run(
        result_dir,
        "E_662_keV",
        {
            "events": 1000,
            "transmitted": 400,
            "reflected": 100,
            "total_thickness_cm": 2.0,
            "transmission_fraction": 0.4,
            "reflection_fraction": 0.1,
            "absorption_fraction": 0.5,
            "linear_attenuation_cm_inv": 0.4581453659370775,
            "attenuation_estimate_type": "direct",
        },
        density=2.5,
    )

    output_path = collect_sweep(result_dir)
    sweep = pd.read_csv(output_path)

    assert sweep.shape[0] == 1
    row = sweep.iloc[0]
    transmission_std = math.sqrt(0.4 * 0.6 / 1000)
    reflection_std = math.sqrt(0.1 * 0.9 / 1000)
    absorption_std = math.sqrt(0.5 * 0.5 / 1000)
    mu_std = transmission_std / (2.0 * 0.4)

    for column in [
        "transmission_fraction_std",
        "reflection_fraction_std",
        "absorption_fraction_std",
        "linear_attenuation_std_cm_inv",
        "mass_attenuation_std_cm2_g",
        "mean_free_path_std_cm",
        "hvl_std_cm",
        "tvl_std_cm",
    ]:
        assert column in sweep.columns

    assert math.isclose(row["transmission_fraction_std"], transmission_std, rel_tol=1e-9)
    assert math.isclose(row["reflection_fraction_std"], reflection_std, rel_tol=1e-9)
    assert math.isclose(row["absorption_fraction_std"], absorption_std, rel_tol=1e-9)
    assert math.isclose(row["transmission_fraction_ci95_half_width"], 1.96 * transmission_std, rel_tol=1e-9)
    assert math.isclose(row["linear_attenuation_std_cm_inv"], mu_std, rel_tol=1e-9)
    assert math.isclose(row["mass_attenuation_std_cm2_g"], mu_std / 2.5, rel_tol=1e-9)
    assert math.isclose(row["mean_free_path_std_cm"], row["mean_free_path_cm"] * (mu_std / row["linear_attenuation_cm_inv"]), rel_tol=1e-9)
    assert math.isclose(row["hvl_std_cm"], row["hvl_cm"] * (mu_std / row["linear_attenuation_cm_inv"]), rel_tol=1e-9)
    assert math.isclose(row["tvl_std_cm"], row["tvl_cm"] * (mu_std / row["linear_attenuation_cm_inv"]), rel_tol=1e-9)


def test_collect_sweep_leaves_mu_uncertainty_nan_for_non_direct_estimator(tmp_path):
    result_dir = tmp_path / "energy_sweep"
    result_dir.mkdir()
    _write_run(
        result_dir,
        "E_1332_keV",
        {
            "events": 2000,
            "transmitted": 1400,
            "reflected": 200,
            "total_thickness_cm": 1.5,
            "transmission_fraction": 0.7,
            "reflection_fraction": 0.1,
            "absorption_fraction": 0.2,
            "linear_attenuation_cm_inv": 0.23778329595915496,
            "attenuation_estimate_type": "primary_track_world_boundary",
        },
        density=3.0,
    )

    output_path = collect_sweep(result_dir)
    row = pd.read_csv(output_path).iloc[0]

    assert math.isfinite(row["transmission_fraction_std"])
    assert math.isnan(row["linear_attenuation_std_cm_inv"])
    assert math.isnan(row["mass_attenuation_std_cm2_g"])
    assert math.isnan(row["mean_free_path_std_cm"])
    assert math.isnan(row["hvl_std_cm"])
    assert math.isnan(row["tvl_std_cm"])


def test_collect_thickness_sweep_writes_uncertainty_columns(tmp_path):
    result_dir = tmp_path / "thickness_sweep"
    result_dir.mkdir()
    _write_run(
        result_dir,
        "T_0p5_cm",
        {
            "events": 1000,
            "transmitted": 900,
            "reflected": 20,
            "total_thickness_cm": 0.5,
            "transmission_fraction": 0.9,
            "reflection_fraction": 0.02,
            "absorption_fraction": 0.08,
            "linear_attenuation_cm_inv": 0.21072103131565256,
            "attenuation_estimate_type": "direct",
        },
        density=1.2,
    )
    _write_run(
        result_dir,
        "T_1p0_cm",
        {
            "events": 1000,
            "transmitted": 800,
            "reflected": 40,
            "total_thickness_cm": 1.0,
            "transmission_fraction": 0.8,
            "reflection_fraction": 0.04,
            "absorption_fraction": 0.16,
            "linear_attenuation_cm_inv": 0.2231435513142097,
            "attenuation_estimate_type": "direct",
        },
        density=1.2,
    )

    output_path = collect_thickness_sweep(result_dir)
    sweep = pd.read_csv(output_path)

    assert sweep["thickness_cm"].tolist() == [0.5, 1.0]
    row = sweep.iloc[0]
    transmission_std = math.sqrt(0.9 * 0.1 / 1000)
    mu_std = transmission_std / (0.5 * 0.9)
    assert math.isclose(row["transmission_fraction_std"], transmission_std, rel_tol=1e-9)
    assert math.isclose(row["linear_attenuation_std_cm_inv"], mu_std, rel_tol=1e-9)
    assert math.isclose(row["mass_attenuation_std_cm2_g"], mu_std / 1.2, rel_tol=1e-9)


def test_collect_composition_sweep_writes_uncertainty_columns(tmp_path):
    result_dir = tmp_path / "composition_sweep"
    result_dir.mkdir()
    _write_run(
        result_dir,
        "C_CuO_0p30",
        {
            "events": 1200,
            "transmitted": 780,
            "reflected": 120,
            "total_thickness_cm": 1.5,
            "transmission_fraction": 0.65,
            "reflection_fraction": 0.10,
            "absorption_fraction": 0.25,
            "linear_attenuation_cm_inv": 0.2876820724517809,
            "attenuation_estimate_type": "direct",
        },
        density=2.8,
    )
    _write_run(
        result_dir,
        "C_CuO_0p60",
        {
            "events": 1200,
            "transmitted": 660,
            "reflected": 120,
            "total_thickness_cm": 1.5,
            "transmission_fraction": 0.55,
            "reflection_fraction": 0.10,
            "absorption_fraction": 0.35,
            "linear_attenuation_cm_inv": 0.3987761199573678,
            "attenuation_estimate_type": "direct",
        },
        density=2.8,
    )

    output_path = collect_composition_sweep(result_dir)
    sweep = pd.read_csv(output_path)

    assert sweep["compound"].tolist() == ["CuO", "CuO"]
    assert sweep["compound_fraction"].tolist() == [0.3, 0.6]
    row = sweep.iloc[0]
    transmission_std = math.sqrt(0.65 * 0.35 / 1200)
    mu_std = transmission_std / (1.5 * 0.65)
    assert math.isclose(row["transmission_fraction_std"], transmission_std, rel_tol=1e-9)
    assert math.isclose(row["linear_attenuation_std_cm_inv"], mu_std, rel_tol=1e-9)
    assert math.isclose(row["mass_attenuation_std_cm2_g"], mu_std / 2.8, rel_tol=1e-9)
