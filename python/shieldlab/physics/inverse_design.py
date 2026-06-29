"""Inverse shielding design: find required thickness or density for a target transmission.

Public API
----------
required_thickness(mac, rho, T_target, buildup_func=None) -> float  [cm]
required_density(mac, x_cm, T_target) -> float                      [g/cm³]
required_thickness_table(E_arr, mac_arr, rho, T_targets) -> pd.DataFrame
sensitivity_analysis(mac, rho, T_target, rho_range) -> pd.DataFrame
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd


def required_thickness(
    mac: float,
    rho: float,
    T_target: float,
    buildup_func=None,
    max_iter: int = 100,
) -> float:
    """Find the shield thickness x (cm) such that T(x) = T_target.

    Narrow-beam: T(x) = exp(-μx) → x = -ln(T_target) / μ

    With buildup B(x):  T(x) = B(x) × exp(-μx) = T_target
    Solved iteratively when buildup_func provided.

    Parameters
    ----------
    mac          : mass attenuation coefficient (cm²/g)
    rho          : material density (g/cm³)
    T_target     : target transmission fraction  0 < T_target < 1
    buildup_func : optional callable B(mu_x) → float
    max_iter     : max iterations for buildup convergence

    Returns
    -------
    x in cm
    """
    if T_target <= 0 or T_target >= 1:
        raise ValueError("T_target must be in (0, 1).")
    mu = mac * rho
    if mu <= 0:
        raise ValueError("mu = mac × rho must be positive.")

    # Narrow beam (analytic)
    x0 = -math.log(T_target) / mu

    if buildup_func is None:
        return x0

    # Iterative: x_{n+1} = -ln(T_target / B(mu × x_n)) / mu
    x = x0
    for _ in range(max_iter):
        B = buildup_func(mu * x)
        if B <= 0 or T_target / B >= 1.0:
            break
        x_new = -math.log(T_target / B) / mu
        if abs(x_new - x) < 1e-6:
            return max(x_new, 0.0)
        x = x_new
    return max(x, 0.0)


def required_density(
    mac: float,
    x_cm: float,
    T_target: float,
) -> float:
    """Find the density ρ (g/cm³) required to achieve T_target at fixed thickness x_cm.

    T = exp(-mac × rho × x)  →  rho = -ln(T) / (mac × x)
    """
    if T_target <= 0 or T_target >= 1:
        raise ValueError("T_target must be in (0, 1).")
    if mac <= 0 or x_cm <= 0:
        raise ValueError("mac and x_cm must be positive.")
    return -math.log(T_target) / (mac * x_cm)


def hvl(mac: float, rho: float) -> float:
    """Half-value layer (cm): x at T = 0.5."""
    return math.log(2.0) / (mac * rho)


def tvl(mac: float, rho: float) -> float:
    """Tenth-value layer (cm): x at T = 0.1."""
    return math.log(10.0) / (mac * rho)


def required_thickness_table(
    E_arr: np.ndarray,
    mac_arr: np.ndarray,
    rho: float,
    T_targets: list[float] | None = None,
) -> pd.DataFrame:
    """Build a table of required thicknesses at multiple energies and T targets.

    Returns a DataFrame with columns:
      Energy_MeV, MAC_cm2_g, LAC_cm, HVL_cm, TVL_cm,
      x_T01_cm, x_T001_cm, x_T0001_cm  (for T = 10%, 1%, 0.1%)
    """
    if T_targets is None:
        T_targets = [0.50, 0.10, 0.01, 0.001]

    rows = []
    for E, mac in zip(E_arr, mac_arr):
        mu = mac * rho
        row: dict = {
            "Energy_MeV": round(float(E), 4),
            "MAC_cm2_g":  round(float(mac), 4),
            "LAC_cm-1":   round(float(mu),  4),
            "HVL_cm":     round(math.log(2) / mu, 4) if mu > 0 else float("nan"),
            "TVL_cm":     round(math.log(10) / mu, 4) if mu > 0 else float("nan"),
        }
        for T in T_targets:
            label = f"x_T{int(T*100):d}pct_cm" if T >= 0.01 else f"x_T{T:.3f}_cm"
            row[label] = round(-math.log(T) / mu, 4) if mu > 0 else float("nan")
        rows.append(row)

    return pd.DataFrame(rows)


def sensitivity_analysis(
    mac: float,
    rho_nominal: float,
    T_target: float,
    rho_range: np.ndarray | None = None,
) -> pd.DataFrame:
    """Show how required thickness changes with material density (sensitivity table).

    Useful for nanocomposite design where filler fraction varies ρ.

    Returns DataFrame: Density_g_cm3, x_required_cm, Mass_per_area_g_cm2
    """
    if rho_range is None:
        rho_range = np.linspace(rho_nominal * 0.5, rho_nominal * 2.0, 20)

    rows = []
    for rho_i in rho_range:
        try:
            x = required_thickness(mac, rho_i, T_target)
            rows.append({
                "Density_g_cm3":        round(rho_i, 3),
                "x_required_cm":        round(x, 4),
                "Mass_per_area_g_cm2":  round(rho_i * x, 4),
            })
        except ValueError:
            pass

    return pd.DataFrame(rows)
