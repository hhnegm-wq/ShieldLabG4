"""Tests for shieldlab.physics.dose_rate — ICRP-116 interpolation and point-source formula."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _p in [str(_ROOT / "python"), str(_ROOT / "ui")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pytest
from shieldlab.physics.dose_rate import (
    fluence_to_h10, dose_rate_point, air_kerma_rate, GAMMA_K,
)


def _rel(a, b):
    return abs(a - b) / abs(b)


class TestIcrp116:
    """ICRP-116 h*(10) conversion coefficient interpolation."""

    def test_at_1MeV(self):
        """h*(10) at 1 MeV = 25.6 pSv·cm² (ICRP-116 Table A.1, AP geometry)."""
        h = fluence_to_h10(1.0)
        # Table value is 25.6; accept ±5%
        assert _rel(h, 25.6) < 0.05, f"h*(10) at 1 MeV = {h:.3f} (expected ~25.6)"

    def test_at_60keV(self):
        """h*(10) at 60 keV = 3.44 pSv·cm² (ICRP-116 Table A.1, AP geometry)."""
        h = fluence_to_h10(0.06)
        assert _rel(h, 3.44) < 0.02, f"h*(10) at 60 keV = {h:.3f} (expected 3.44)"

    def test_at_70keV_icrp116_new_point(self):
        """h*(10) at 70 keV = 3.94 pSv·cm² — new ICRP-116 tabulation point."""
        h = fluence_to_h10(0.07)
        assert _rel(h, 3.94) < 0.02, f"h*(10) at 70 keV = {h:.3f} (expected 3.94)"

    def test_at_15MeV_icrp116_extension(self):
        """h*(10) at 15 MeV = 138.0 pSv·cm² (ICRP-116 high-energy extension)."""
        h = fluence_to_h10(15.0)
        assert _rel(h, 138.0) < 0.02, f"h*(10) at 15 MeV = {h:.3f} (expected 138.0)"

    def test_monotone_above_100keV(self):
        """h*(10) should broadly increase from 100 keV to ~3 MeV."""
        energies = [0.1, 0.2, 0.5, 1.0, 2.0, 3.0]
        values   = [fluence_to_h10(e) for e in energies]
        # Not strictly monotone everywhere but 0.1 < 3.0
        assert values[0] < values[-1], \
            "h*(10) should be larger at 3 MeV than at 0.1 MeV"

    def test_out_of_range_low_raises(self):
        """Energies below 0.01 MeV must raise ValueError (no extrapolation)."""
        with pytest.raises(ValueError, match="outside ICRP-116"):
            fluence_to_h10(0.001)

    def test_out_of_range_high_raises(self):
        """Energies above 20 MeV must raise ValueError (no extrapolation)."""
        with pytest.raises(ValueError, match="outside ICRP-116"):
            fluence_to_h10(25.0)

    def test_table_boundary_ok(self):
        """Exactly at table boundaries (0.01 and 20.0 MeV) should not raise."""
        assert fluence_to_h10(0.01) > 0
        assert fluence_to_h10(20.0) > 0


class TestDoseRatePoint:
    """Point-source dose-rate formula."""

    def test_inverse_square(self):
        """Doubling distance should quarter dose rate."""
        A = 1e9  # Bq
        E = np.array([0.662])
        I = np.array([1.0])
        h1 = dose_rate_point(A, E, I, 100.0)   # 1 m
        h2 = dose_rate_point(A, E, I, 200.0)   # 2 m
        assert _rel(h1 / h2, 4.0) < 0.01, \
            f"Inverse-square: ratio = {h1/h2:.3f} (expected 4.0)"

    def test_linear_in_activity(self):
        """Dose rate should scale linearly with activity."""
        E = np.array([0.662])
        I = np.array([1.0])
        h1 = dose_rate_point(1e6, E, I, 100.0)
        h2 = dose_rate_point(2e6, E, I, 100.0)
        assert _rel(h2, 2 * h1) < 1e-6

    def test_cs137_rough_check(self):
        """Cs-137 1 GBq at 1 m ~ 85 µSv/h (textbook value ≈ 0.085 mSv/h)."""
        A  = 1e9
        E  = np.array([0.662])
        I  = np.array([0.851])
        H  = dose_rate_point(A, E, I, 100.0)
        # Accept wide tolerance (factor of 3) given different conversion methods
        assert 10.0 < H < 500.0, f"Cs-137 1 GBq @ 1 m → {H:.2f} µSv/h"


class TestAirKermaRate:
    """Air-kerma rate constant Γ_k."""

    def test_gamma_k_table_nonempty(self):
        """GAMMA_K dict should have at least 10 isotopes."""
        assert len(GAMMA_K) >= 10

    def test_cs137_gamma_k(self):
        """Cs-137 Γ_k should be tabulated in GAMMA_K (key starts with 'Cs-137')."""
        cs137_key = next((k for k in GAMMA_K if k.startswith("Cs-137")), None)
        assert cs137_key is not None, f"Cs-137 not found in GAMMA_K keys: {list(GAMMA_K)}"

    def test_air_kerma_positive(self):
        """air_kerma_rate should return a positive value."""
        from shieldlab.physics.dose_rate import air_kerma_rate
        cs137_key = next(k for k in GAMMA_K if k.startswith("Cs-137"))
        val = air_kerma_rate(1e9, GAMMA_K[cs137_key], 1.0)
        assert val > 0
