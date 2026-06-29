"""Benchmark: computed HVL vs Attix textbook & NIST-derived values.

Primary reference:
  Attix, F.H. (1986). *Introduction to Radiological Physics and Radiation
  Dosimetry*, Wiley.  Table values for HVL are derived from µ = MAC × ρ,
  HVL = ln2 / µ_total.

Secondary reference (for cross-check):
  Shultis, J.K. & Faw, R.E. (2000). *Radiation Shielding*, ANS.

HVL (cm) = ln(2) / (MAC × ρ)  — narrow-beam, broad-good-geometry.
Tolerance: ±1.5 % (HVL is a derived quantity; slight rho differences compound).
"""
import math
import pytest
from conftest import compute_hvl  # noqa: F401

_TOL = 0.015  # 1.5 %


def _ref_hvl(mac_cm2g: float, rho: float) -> float:
    """Derive reference HVL from NIST MAC + tabulated density."""
    return math.log(2) / (mac_cm2g * rho)


# ── Lead ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("E_MeV, nist_mac, rho", [
    (0.060,  5.021,  11.35),  # HVL ≈ 0.01215 cm (≈ 0.12 mm Pb)
    (0.662,  0.1110, 11.35),  # HVL ≈ 0.551 cm
    (1.332,  0.05624,11.35),  # HVL ≈ 1.086 cm
])
def test_lead_hvl(lead_mf, E_MeV, nist_mac, rho):
    ref = _ref_hvl(nist_mac, rho)
    calc = compute_hvl(lead_mf, rho, E_MeV)
    assert abs(calc - ref) / ref < _TOL, (
        f"Lead HVL at {E_MeV} MeV: calc={calc:.4f} cm, ref={ref:.4f} cm"
    )


# ── Water ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("E_MeV, nist_mac, rho", [
    (0.060,  0.2058, 1.0),   # HVL ≈ 3.367 cm
    (0.662,  0.08570,1.0),   # HVL ≈ 8.088 cm
    (1.000,  0.07066,1.0),   # HVL ≈ 9.809 cm
])
def test_water_hvl(water_mf, E_MeV, nist_mac, rho):
    ref = _ref_hvl(nist_mac, rho)
    calc = compute_hvl(water_mf, rho, E_MeV)
    assert abs(calc - ref) / ref < _TOL, (
        f"Water HVL at {E_MeV} MeV: calc={calc:.4f} cm, ref={ref:.4f} cm"
    )


# ── Iron ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("E_MeV, nist_mac, rho", [
    (0.060,  1.205,  7.87),  # HVL ≈ 0.0732 cm
    (0.662,  0.07357,7.87),  # HVL ≈ 1.198 cm
    (1.332,  0.05180,7.87),  # HVL ≈ 1.700 cm
])
def test_iron_hvl(iron_mf, E_MeV, nist_mac, rho):
    ref = _ref_hvl(nist_mac, rho)
    calc = compute_hvl(iron_mf, rho, E_MeV)
    assert abs(calc - ref) / ref < _TOL, (
        f"Fe HVL at {E_MeV} MeV: calc={calc:.4f} cm, ref={ref:.4f} cm"
    )


# ── HDPE ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("E_MeV, nist_mac, rho", [
    (0.060,  0.1990, 0.95),  # HVL ≈ 3.667 cm
    (0.662,  0.08786,0.95),  # HVL ≈ 8.304 cm
    (1.000,  0.07240,0.95),  # HVL ≈ 10.083 cm
])
def test_hdpe_hvl(hdpe_mf, E_MeV, nist_mac, rho):
    ref = _ref_hvl(nist_mac, rho)
    calc = compute_hvl(hdpe_mf, rho, E_MeV)
    assert abs(calc - ref) / ref < _TOL, (
        f"HDPE HVL at {E_MeV} MeV: calc={calc:.4f} cm, ref={ref:.4f} cm"
    )


# ── Concrete ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("E_MeV, nist_mac, rho", [
    (0.060,  0.2666, 2.35),  # HVL ≈ 1.105 cm
    (0.662,  0.08280,2.35),  # HVL ≈ 3.557 cm
    (1.332,  0.05910,2.35),  # HVL ≈ 4.983 cm
])
def test_concrete_hvl(concrete_mf, E_MeV, nist_mac, rho):
    ref = _ref_hvl(nist_mac, rho)
    calc = compute_hvl(concrete_mf, rho, E_MeV)
    assert abs(calc - ref) / ref < _TOL, (
        f"Concrete HVL at {E_MeV} MeV: calc={calc:.4f} cm, ref={ref:.4f} cm"
    )


# ── HVL monotonicity (increasing E → increasing HVL above ~100 keV) ──────────
def test_lead_hvl_monotone_above_200kev(lead_mf):
    """HVL must increase with energy in the Compton-dominated regime (0.2–3 MeV).

    Above ~3 MeV pair production becomes significant for Pb (Z=82), increasing
    mu/rho and thus decreasing HVL again.  The monotone assumption only holds
    in the Compton window.
    """
    energies = [0.200, 0.400, 0.662, 1.000, 1.332, 2.000, 3.000]
    hvls = [compute_hvl(lead_mf, 11.35, E) for E in energies]
    for i in range(len(hvls) - 1):
        assert hvls[i] < hvls[i + 1], (
            f"Lead HVL not monotone: E={energies[i]}-{energies[i+1]} MeV, "
            f"HVL={hvls[i]:.4f}-{hvls[i+1]:.4f} cm"
        )


def test_water_hvl_monotone_above_100kev(water_mf):
    energies = [0.100, 0.200, 0.400, 0.662, 1.000, 2.000, 4.000]
    hvls = [compute_hvl(water_mf, 1.0, E) for E in energies]
    for i in range(len(hvls) - 1):
        assert hvls[i] < hvls[i + 1], (
            f"Water HVL not monotone at E={energies[i]}-{energies[i+1]} MeV"
        )
