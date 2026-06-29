"""ICRP-74 ambient dose-equivalent conversion factors h*(10) for photons.

Source: ICRP Publication 74 (1996), Table A.21 — "Conversion coefficients from
fluence to ambient dose equivalent H*(10), in pSv·cm²".

This module is intentionally dependency-light (numpy only) and is the
authoritative table used elsewhere in the platform when converting
photon fluence to H*(10) for dose-rate, sensitivity, and validation
calculations.

Public API
----------
ICRP74_PHOTON_FLUENCE_TO_H10
    Tuple of (energy_MeV, h_pSv_cm2) arrays — the digitised table.

h10_per_fluence(energy_MeV)
    Log-log interpolated conversion factor in pSv·cm². Out-of-range
    energies are flagged via a ValueError so callers cannot silently
    extrapolate.

dose_rate_from_fluence(fluence_per_cm2_s, energy_MeV)
    Returns H*(10) in µSv/h for a given fluence rate (s⁻¹·cm⁻²) at a
    given monoenergetic photon energy.

References
----------
ICRP, 1996. "Conversion Coefficients for use in Radiological Protection
against External Radiation." ICRP Publication 74. Ann. ICRP 26 (3-4).
"""
from __future__ import annotations

import numpy as np

# (E_MeV, h*(10)/Φ in pSv·cm²) — ICRP-74 Table A.21
_E_MEV = np.array([
    0.010, 0.015, 0.020, 0.030, 0.040, 0.050, 0.060, 0.080,
    0.100, 0.150, 0.200, 0.300, 0.400, 0.500, 0.600, 0.800,
    1.000, 1.500, 2.000, 3.000, 4.000, 5.000, 6.000, 8.000,
    10.000,
])
_H_PSV_CM2 = np.array([
    0.061, 0.83, 1.05, 0.81, 0.64, 0.55, 0.51, 0.53,
    0.61, 0.89, 1.20, 1.80, 2.38, 2.93, 3.44, 4.38,
    5.20, 6.90, 8.60, 11.10, 13.40, 15.50, 17.60, 21.60,
    25.60,
])

ICRP74_PHOTON_FLUENCE_TO_H10 = (_E_MEV, _H_PSV_CM2)

_LOG_E = np.log(_E_MEV)
_LOG_H = np.log(_H_PSV_CM2)


def h10_per_fluence(energy_MeV: float | np.ndarray) -> np.ndarray:
    """Return h*(10)/Φ in pSv·cm² for the supplied photon energy / energies.

    Uses log-log interpolation over the ICRP-74 Table A.21 grid. Raises
    ValueError if any energy is outside the tabulated range
    [0.010, 10.0] MeV — extrapolation is unsafe near the low-energy
    photoelectric edge.
    """
    e = np.asarray(energy_MeV, dtype=float)
    if np.any(e < _E_MEV[0]) or np.any(e > _E_MEV[-1]):
        raise ValueError(
            f"Energy outside ICRP-74 Table A.21 range "
            f"[{_E_MEV[0]:.3f}, {_E_MEV[-1]:.1f}] MeV"
        )
    return np.exp(np.interp(np.log(e), _LOG_E, _LOG_H))


def dose_rate_from_fluence(
    fluence_per_cm2_s: float | np.ndarray,
    energy_MeV: float | np.ndarray,
) -> np.ndarray:
    """Convert photon fluence rate (s⁻¹·cm⁻²) to H*(10) in µSv/h.

    H*(10) [µSv/h] = Φ̇ [s⁻¹·cm⁻²] · h*(10)/Φ [pSv·cm²] · 3600 [s/h] · 1e-6 [µSv/pSv]
    """
    h_pSv_cm2 = h10_per_fluence(energy_MeV)
    return np.asarray(fluence_per_cm2_s) * h_pSv_cm2 * 3600.0 * 1e-6


__all__ = [
    "ICRP74_PHOTON_FLUENCE_TO_H10",
    "h10_per_fluence",
    "dose_rate_from_fluence",
]
