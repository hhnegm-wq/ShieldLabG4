"""Dose-rate calculator for common radiation sources.

Supports point, line, and disk source geometries.
References:
  - Shultis & Faw, "Radiation Shielding" (2000)
  - NCRP Report 151 (2005)
  - ICRP Publication 116 (2010) – fluence-to-dose-equivalent conversion coefficients
    (supersedes ICRP 74, 1996; photon H*(10) AP geometry, Table A.1)

Public API
----------
dose_rate_point(A_Bq, E_MeV, mu_en_rho, rho, distance_cm, Gamma=None) -> float  [uSv/h]
dose_rate_line(A_Bq_per_cm, L_cm, E_MeV, mu_en_rho, rho, distance_cm) -> float  [uSv/h]
dose_rate_disk(A_Bq_per_cm2, R_cm, E_MeV, mu_en_rho, rho, distance_cm) -> float [uSv/h]
kerma_rate_constant(E_MeV, mu_en_rho) -> float  [uSv·m²/(h·MBq)]
fluence_to_h10(E_MeV) -> float  [pSv·cm²]
air_kerma_rate(A_Bq, E_MeV, Gamma_k, distance_m) -> float  [uGy/h]
shielded_dose_rate(H0_uSv_h, mac, rho, thickness_cm, buildup=1.0) -> float [uSv/h]
dose_rate_table(A_Bq, E_MeV, mac_arr, rho, distances_m, mf=None) -> pd.DataFrame
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd
from scipy import integrate  # type: ignore

# ── Constants ─────────────────────────────────────────────────────────────────
_C     = 3.0e8          # speed of light m/s
_E_eV  = 1.60218e-19   # 1 eV in J
_MEV   = _E_eV * 1e6   # 1 MeV in J

# Air properties at STP (NIST)
_RHO_AIR = 1.293e-3     # g/cm³  dry air at STP

# ── ICRP 116 H*(10) fluence-to-dose-equivalent coefficients (pSv·cm²) ────────
# Photon ambient dose equivalent H*(10) conversion coefficients, AP geometry.
# Source: ICRP Publication 116 (2010), Table A.1.
# Supersedes ICRP Publication 74 (1996).
# Energies extended to 20 MeV; 0.070 MeV point added relative to ICRP-74.
_ICRP116_E = np.array([
    0.010, 0.015, 0.020, 0.030, 0.040, 0.050, 0.060, 0.070, 0.080, 0.100,
    0.150, 0.200, 0.300, 0.400, 0.500, 0.600, 0.800, 1.000, 1.500,
    2.000, 3.000, 4.000, 5.000, 6.000, 8.000, 10.000, 15.000, 20.000,
])
_ICRP116_H = np.array([
    0.0061, 0.083, 0.58, 1.68, 2.38, 2.93, 3.44, 3.94, 4.38, 5.20,
    6.90,   8.60, 11.1, 13.4, 15.5, 17.6, 21.6, 25.6, 33.2,
    39.7,   51.9, 62.8, 72.4, 80.8, 96.0, 110.0, 138.0, 163.0,
])

# Air kerma-rate constant Gamma_k (μGy·m²/(h·MBq)) for standard sources
# Source: Attix "Introduction to Radiological Physics", Table B.1
GAMMA_K: dict[str, float] = {
    "Cs-137 (662 keV)":         0.0780,
    "Co-60 (1173+1332 keV)":    0.3090,
    "Am-241 (59.5 keV)":        0.0027,
    "Na-22 (511+1275 keV)":     0.3140,
    "Ir-192 (multi)":           0.1110,
    "I-131 (364+637 keV)":      0.0590,
    "F-18 (511 keV PET)":       0.1420,
    "Tc-99m (140 keV)":         0.0155,
    "In-111 (171+245 keV)":     0.0860,
    "Ga-67 (93+184+300 keV)":   0.0380,
    "Tl-201 (71+167 keV)":      0.0180,
    "Ba-133 (multi)":           0.0580,
    "Eu-152 (multi)":           0.2400,
    "Mn-54 (835 keV)":          0.1170,
    "Y-90 (bremsstrahlung)":    0.0025,
}

# ── Helper: ICRP-116 H*(10) conversion coefficient ───────────────────────────

def fluence_to_h10(E_MeV: float | np.ndarray) -> float | np.ndarray:
    """Interpolate ICRP-116 H*(10) fluence-to-dose coefficient (pSv·cm²).

    Uses log-log interpolation for physical accuracy (both E and H*(10) vary
    over orders of magnitude; linear interpolation introduces systematic error
    especially at low energies).

    Parameters
    ----------
    E_MeV : float or array  photon energy in MeV

    Returns
    -------
    h10 : float or array  conversion coefficient in pSv·cm²

    Raises
    ------
    ValueError
        If any energy in E_MeV falls outside the ICRP-116 table range
        [0.010, 20.0] MeV.  Extrapolation is not physically justified.
    """
    E = np.asarray(E_MeV, dtype=float)
    scalar = E.ndim == 0
    E = np.atleast_1d(E)

    E_min, E_max = _ICRP116_E[0], _ICRP116_E[-1]
    if np.any(E < E_min) or np.any(E > E_max):
        out = E[(E < E_min) | (E > E_max)]
        raise ValueError(
            f"Energy {out} MeV is outside ICRP-116 H*(10) table range "
            f"[{E_min}, {E_max}] MeV. Extrapolation is not supported."
        )

    # Log-log interpolation: interpolate log10(H) vs log10(E)
    log_E  = np.log10(E)
    log_Etab = np.log10(_ICRP116_E)
    log_Htab = np.log10(_ICRP116_H)
    h10 = 10.0 ** np.interp(log_E, log_Etab, log_Htab)

    return float(h10[0]) if scalar else h10


def kerma_rate_constant(E_MeV: float, mu_en_rho_air: float) -> float:
    """Compute air-kerma rate constant Gamma_k from first principles.

    Gamma_k = (E * mu_en/rho)_air * 1/(4π) × unit conversion

    Parameters
    ----------
    E_MeV         : photon energy in MeV
    mu_en_rho_air : mass energy-absorption coefficient of air (cm²/g)

    Returns
    -------
    Gamma_k in μGy·m²/(h·MBq)
    """
    # K_dot / (A/r²) = E [MeV] × mu_en/rho [cm²/g] × (1 MeV = 1.602e-13 J)
    # = E_MeV × 1.602e-13 J/MeV × mu_en_rho cm²/g × 1e4 m²/cm² / 1e3 g/kg
    # = E_MeV × mu_en_rho × 1.602e-14 [Gy·m²·s / (particle/s / m²)]
    # Convert to μGy·m²/(h·MBq):
    # 1 MBq = 1e6 Bq = 1e6 s⁻¹;  1 h = 3600 s;  1 Gy → 1e6 μGy
    gamma_gy_m2_per_h_bq = (
        E_MeV * mu_en_rho_air * 1.602e-13  # Gy·cm²/g per photon/s/m²
        * (1 / (4 * math.pi))              # for isotropic point source
        * 1e4                              # cm² → m² correction factor
        * 1e-3                             # g → kg
        * 3600                             # s → h
    )
    return gamma_gy_m2_per_h_bq * 1e6 * 1e6  # Gy → μGy, Bq → MBq


def air_kerma_rate(A_Bq: float, gamma_k: float, distance_m: float) -> float:
    """Point-source air-kerma rate using tabulated Gamma_k constant.

    K_dot = Gamma_k × A / r²

    Parameters
    ----------
    A_Bq       : source activity in Bq
    gamma_k    : air-kerma rate constant in μGy·m²/(h·MBq)
    distance_m : distance from source in metres
    Returns
    -------
    K_dot in μGy/h
    """
    A_MBq = A_Bq / 1e6
    return gamma_k * A_MBq / (distance_m ** 2)


# ── Core dose-rate functions ──────────────────────────────────────────────────

def dose_rate_point(
    A_Bq: float,
    E_MeV: float | np.ndarray,
    intensities: float | np.ndarray,
    distance_cm: float,
    mu_air: float | None = None,
) -> float:
    """H*(10) ambient dose-equivalent rate for an unshielded point source (μSv/h).

    Uses fluence-to-dose conversion from ICRP-116 (2010).

    Parameters
    ----------
    A_Bq        : activity in Bq
    E_MeV       : gamma energy (MeV); scalar or array for multi-line sources
    intensities : photon yield per disintegration (same shape as E_MeV)
    distance_cm : source-to-point distance in cm
    mu_air      : (unused placeholder) linear atten. of air

    Returns
    -------
    H_dot in μSv/h
    """
    E   = np.atleast_1d(np.asarray(E_MeV, dtype=float))
    I   = np.atleast_1d(np.asarray(intensities, dtype=float))
    r   = float(distance_cm)

    # Photon fluence rate at distance r: Phi = A * I / (4π r²)  [photons cm⁻² s⁻¹]
    Phi = A_Bq * I / (4.0 * math.pi * r**2)  # photons/cm²/s

    # H*(10) conversion coefficients (pSv·cm²)
    h10 = fluence_to_h10(E)  # pSv·cm²

    # H_dot = Phi × h10   [pSv/s] → [μSv/h]
    H_dot_pSv_s = np.sum(Phi * h10)
    return H_dot_pSv_s * 1e-6 * 3600.0  # pSv/s → μSv/h


def dose_rate_line(
    A_Bq_per_cm: float,
    L_cm: float,
    E_MeV: float | np.ndarray,
    intensities: float | np.ndarray,
    distance_cm: float,
) -> float:
    """H*(10) dose-equivalent rate for a finite line source (μSv/h).

    Point of interest is at perpendicular distance *distance_cm* from the
    midpoint of the line source.

    Parameters
    ----------
    A_Bq_per_cm : linear source strength (Bq/cm)
    L_cm        : total length of line source (cm)
    E_MeV       : photon energy (MeV)
    intensities : photon yield per disintegration
    distance_cm : perpendicular distance from source midpoint (cm)

    Returns
    -------
    H_dot in μSv/h
    """
    E = np.atleast_1d(np.asarray(E_MeV, dtype=float))
    I = np.atleast_1d(np.asarray(intensities, dtype=float))
    r = float(distance_cm)
    half = L_cm / 2.0

    # Integrate 1/(r² + z²) from -L/2 to +L/2  → (1/r) arctan(L/2/r)
    integral = (1.0 / r) * math.atan(half / r)  # factor 2 since ±

    total = 0.0
    for e_i, i_i in zip(E, I):
        h10 = float(fluence_to_h10(e_i))
        # Phi_line = A_Bq_per_cm * I * integral_over_length / (4π)
        Phi = A_Bq_per_cm * i_i * integral / (2.0 * math.pi)  # (×2 for ± sym)
        total += Phi * h10
    return total * 1e-6 * 3600.0


def dose_rate_disk(
    A_Bq_per_cm2: float,
    R_cm: float,
    E_MeV: float | np.ndarray,
    intensities: float | np.ndarray,
    distance_cm: float,
) -> float:
    """H*(10) dose-equivalent rate for a disk (circular area) source (μSv/h).

    Point of interest is on the axis, at axial distance *distance_cm* from the
    disk centre.

    Parameters
    ----------
    A_Bq_per_cm2 : areal source strength (Bq/cm²)
    R_cm         : disk radius (cm)
    E_MeV        : photon energy (MeV)
    intensities  : photon yield per disintegration
    distance_cm  : axial distance from disk to detector (cm)
    """
    E = np.atleast_1d(np.asarray(E_MeV, dtype=float))
    I = np.atleast_1d(np.asarray(intensities, dtype=float))
    h = float(distance_cm)

    # Phi_disk = A_areal * I / 2 * ln(1 + R²/h²)
    # Derived from integrating 1/(h²+r²) × r dr × 2π / (4π) over disk
    ln_factor = 0.5 * math.log(1.0 + (R_cm / h) ** 2)

    total = 0.0
    for e_i, i_i in zip(E, I):
        h10 = float(fluence_to_h10(e_i))
        Phi = A_Bq_per_cm2 * i_i * ln_factor
        total += Phi * h10
    return total * 1e-6 * 3600.0


def shielded_dose_rate(
    H0_uSv_h: float,
    mac: float,
    rho: float,
    thickness_cm: float,
    buildup: float = 1.0,
) -> float:
    """Apply exponential attenuation + buildup to a dose-rate.

    Parameters
    ----------
    H0_uSv_h    : unshielded dose-equivalent rate (μSv/h)
    mac         : mass attenuation coefficient (cm²/g)
    rho         : material density (g/cm³)
    thickness_cm: shield thickness (cm)
    buildup     : buildup factor B (default = 1 = narrow beam)

    Returns
    -------
    H_dot in μSv/h
    """
    mu   = mac * rho           # linear attenuation coefficient (cm⁻¹)
    return H0_uSv_h * buildup * math.exp(-mu * thickness_cm)


# ── Convenience table builder ─────────────────────────────────────────────────

def dose_rate_table(
    A_Bq: float,
    E_MeV: float | np.ndarray,
    intensities: float | np.ndarray,
    distances_m: np.ndarray,
    shield_mac: float | None = None,
    shield_rho: float | None = None,
    shield_thickness_cm: float = 0.0,
) -> pd.DataFrame:
    """Build a DataFrame of dose rates vs distance, optionally with shielding.

    Returns columns: Distance_m, H_dot_free_uSv_h, H_dot_shielded_uSv_h (if shield)
    """
    rows = []
    for d_m in distances_m:
        d_cm = d_m * 100.0
        H0 = dose_rate_point(A_Bq, E_MeV, intensities, d_cm)
        row: dict = {
            "Distance_m": round(d_m, 3),
            "Distance_cm": round(d_cm, 1),
            "H*(10)_free_uSv_h": round(H0, 6),
        }
        if shield_mac and shield_rho and shield_thickness_cm > 0:
            Hs = shielded_dose_rate(H0, shield_mac, shield_rho, shield_thickness_cm)
            row["H*(10)_shielded_uSv_h"] = round(Hs, 8)
            row["Shield_reduction_factor"] = round(H0 / Hs, 2) if Hs else float("inf")
        rows.append(row)
    return pd.DataFrame(rows)
