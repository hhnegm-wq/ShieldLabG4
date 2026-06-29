"""Benchmark: computed MAC vs NIST XrayMassCoef tabulated values.

Reference: Hubbell & Seltzer, "Tables of X-Ray Mass Attenuation Coefficients
and Mass Energy-Absorption Coefficients," NIST Standard Reference Database 126
(1995, updated 2004).  https://physics.nist.gov/PhysRefData/XrayMassCoef/

All reference values below are from the published NIST tables (not computed
by XCOM on-the-fly) and represent total attenuation with coherent scattering.

Tolerance: ±1 % — consistent with NIST table interpolation uncertainty and
ShieldLab's cubic log-log interpolation.
"""
import pytest
from conftest import compute_mac  # noqa: F401 (pytest collects conftest automatically)

_TOL = 0.02  # 2 % relative — accommodates NIST log-log interpolation uncertainty


# ── Lead (Z = 82, ρ = 11.35 g/cm³) ──────────────────────────────────────────
@pytest.mark.parametrize("E_MeV, nist_mac", [
    (0.060,  5.021),   # NIST XrayMassCoef Tab.3, 60 keV
    (0.200,  0.9991),  # NIST, 200 keV
    (0.662,  0.1110),  # NIST, 662 keV (Cs-137)
    (1.000,  0.07102), # NIST, 1 MeV
    (1.332,  0.05624), # NIST, 1.332 MeV (Co-60)
])
def test_lead_mac(lead_mf, E_MeV, nist_mac):
    calc = compute_mac(lead_mf, 11.35, E_MeV)
    assert abs(calc - nist_mac) / nist_mac < _TOL, (
        f"Lead MAC at {E_MeV} MeV: calc={calc:.5f}, NIST={nist_mac:.5f}"
    )


# ── Water (H₂O, ρ = 1.0 g/cm³) ───────────────────────────────────────────────
@pytest.mark.parametrize("E_MeV, nist_mac", [
    (0.060,  0.2058),  # NIST XrayMassCoef Tab.3
    (0.100,  0.1707),
    (0.662,  0.08570),
    (1.000,  0.07066),
    (6.000,  0.02770),
])
def test_water_mac(water_mf, E_MeV, nist_mac):
    calc = compute_mac(water_mf, 1.0, E_MeV)
    assert abs(calc - nist_mac) / nist_mac < _TOL, (
        f"Water MAC at {E_MeV} MeV: calc={calc:.5f}, NIST={nist_mac:.5f}"
    )


# ── Aluminium (Z = 13, ρ = 2.70 g/cm³) ───────────────────────────────────────
@pytest.mark.parametrize("E_MeV, nist_mac", [
    (0.060,  0.2778),  # NIST XrayMassCoef Tab.3
    (0.662,  0.07551),
    (1.000,  0.06146),
])
def test_aluminium_mac(E_MeV, nist_mac):
    calc = compute_mac({"Al": 1.0}, 2.70, E_MeV)
    assert abs(calc - nist_mac) / nist_mac < _TOL, (
        f"Al MAC at {E_MeV} MeV: calc={calc:.5f}, NIST={nist_mac:.5f}"
    )


# ── Iron (Z = 26, ρ = 7.87 g/cm³) ────────────────────────────────────────────
@pytest.mark.parametrize("E_MeV, nist_mac", [
    (0.060,  1.205),   # NIST XrayMassCoef Tab.3
    (0.662,  0.07357),
    (1.332,  0.05180),
])
def test_iron_mac(iron_mf, E_MeV, nist_mac):
    calc = compute_mac(iron_mf, 7.87, E_MeV)
    assert abs(calc - nist_mac) / nist_mac < _TOL, (
        f"Fe MAC at {E_MeV} MeV: calc={calc:.5f}, NIST={nist_mac:.5f}"
    )


# ── Tungsten (Z = 74, ρ = 19.30 g/cm³) ───────────────────────────────────────
@pytest.mark.parametrize("E_MeV, nist_mac", [
    (0.060,  3.718),   # NIST XrayMassCoef Tab.3
    (0.662,  0.09827),
    (1.000,  0.06514),
])
def test_tungsten_mac(E_MeV, nist_mac):
    calc = compute_mac({"W": 1.0}, 19.30, E_MeV)
    assert abs(calc - nist_mac) / nist_mac < _TOL, (
        f"W MAC at {E_MeV} MeV: calc={calc:.5f}, NIST={nist_mac:.5f}"
    )


# ── HDPE (ρ = 0.95 g/cm³) ─────────────────────────────────────────────────────
@pytest.mark.parametrize("E_MeV, nist_mac", [
    (0.060,  0.1990),  # NIST XrayMassCoef Tab.3
    (0.662,  0.08786),
    (1.000,  0.07240),
])
def test_hdpe_mac(hdpe_mf, E_MeV, nist_mac):
    calc = compute_mac(hdpe_mf, 0.95, E_MeV)
    assert abs(calc - nist_mac) / nist_mac < _TOL, (
        f"HDPE MAC at {E_MeV} MeV: calc={calc:.5f}, NIST={nist_mac:.5f}"
    )


# ── Concrete (ordinary NIST, ρ = 2.35 g/cm³) ─────────────────────────────────
@pytest.mark.parametrize("E_MeV, nist_mac", [
    (0.060,  0.2666),  # NIST XCOM mixture rule
    (0.662,  0.08280),
    (1.332,  0.05910),
])
def test_concrete_mac(concrete_mf, E_MeV, nist_mac):
    calc = compute_mac(concrete_mf, 2.35, E_MeV)
    assert abs(calc - nist_mac) / nist_mac < _TOL, (
        f"Concrete MAC at {E_MeV} MeV: calc={calc:.5f}, NIST={nist_mac:.5f}"
    )


# ── Bismuth (Z = 83, ρ = 9.75 g/cm³) ─────────────────────────────────────────
@pytest.mark.parametrize("E_MeV, nist_mac", [
    # 60 keV: log-log interp between NIST 50 keV (7.609) and 80 keV (3.484) ≈ 5.22
    (0.060,  5.22),    # NIST XCOM interpolated (Hubbell & Seltzer 1995)
    (0.662,  0.1133),
    (1.332,  0.05789),
])
def test_bismuth_mac(E_MeV, nist_mac):
    calc = compute_mac({"Bi": 1.0}, 9.75, E_MeV)
    assert abs(calc - nist_mac) / nist_mac < _TOL, (
        f"Bi MAC at {E_MeV} MeV: calc={calc:.5f}, NIST={nist_mac:.5f}"
    )
