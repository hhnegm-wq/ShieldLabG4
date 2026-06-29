"""ICRP-74 H*(10) conversion factor unit tests."""
from __future__ import annotations

import numpy as np
import pytest

from shieldlab.physics.dose_conversion import (
    ICRP74_PHOTON_FLUENCE_TO_H10,
    dose_rate_from_fluence,
    h10_per_fluence,
)


@pytest.mark.unit
def test_table_grid_points_round_trip() -> None:
    e_grid, h_grid = ICRP74_PHOTON_FLUENCE_TO_H10
    interp = h10_per_fluence(e_grid)
    assert np.allclose(interp, h_grid, rtol=1e-12, atol=1e-12)


@pytest.mark.unit
def test_intermediate_energy_within_table_neighbours() -> None:
    # 1.25 MeV (Co-60 average) sits between 1.0 (5.20) and 1.5 (6.90).
    val = float(h10_per_fluence(1.25))
    assert 5.20 <= val <= 6.90


@pytest.mark.unit
def test_out_of_range_raises() -> None:
    with pytest.raises(ValueError):
        h10_per_fluence(0.001)
    with pytest.raises(ValueError):
        h10_per_fluence(50.0)


@pytest.mark.unit
def test_dose_rate_units_sane() -> None:
    # 1 photon/cm²/s of 1 MeV gammas -> 5.20 pSv·cm² × 3600 / 1e6 = 1.872e-2 µSv/h.
    rate = float(dose_rate_from_fluence(1.0, 1.0))
    assert abs(rate - 5.20 * 3600.0 * 1e-6) < 1e-9
