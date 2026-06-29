"""Klein-Nishina differential cross-section for Compton scattering.

Provides:
  - dsigma_dOmega(E_MeV, theta_rad) → differential cross section (cm²/sr/electron)
  - klein_nishina_polar_fig(E_MeV_list) → matplotlib Figure with polar plot
  - total_compton_cross_section(E_MeV) → total Klein-Nishina cross section (cm²/electron)
  - compton_energy(E_MeV, theta_rad) → scattered photon energy (MeV)

Reference: Klein & Nishina (1929); Evans "The Atomic Nucleus" (1955) Ch. 23.
"""
from __future__ import annotations

import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import integrate  # type: ignore

# Classical electron radius r₀ (cm)
_R0 = 2.8179403262e-13   # cm

# Rest energy of electron (MeV)
_M_E = 0.51099895        # MeV


def compton_energy(E_MeV: float, theta_rad: float) -> float:
    """Scattered photon energy after Compton scattering.

    E' = E / (1 + (E/m_e c²)(1 - cos θ))
    """
    eps = E_MeV / _M_E
    return E_MeV / (1.0 + eps * (1.0 - math.cos(theta_rad)))


def dsigma_dOmega(
    E_MeV: float | np.ndarray,
    theta_rad: float | np.ndarray,
) -> np.ndarray:
    """Klein-Nishina differential cross section (cm²/sr/electron).

    dσ/dΩ = ½ r₀² (E'/E)² [E'/E + E/E' - sin²θ]

    Parameters
    ----------
    E_MeV     : incident photon energy (MeV) — scalar or array
    theta_rad : scattering angle (rad) — scalar or array

    Returns
    -------
    dσ/dΩ in cm²/sr/electron
    """
    E   = np.asarray(E_MeV,  dtype=float)
    th  = np.asarray(theta_rad, dtype=float)
    eps = E / _M_E
    ratio = 1.0 / (1.0 + eps * (1.0 - np.cos(th)))  # E'/E
    return 0.5 * _R0**2 * ratio**2 * (ratio + 1.0/ratio - np.sin(th)**2)


def total_compton_cross_section(E_MeV: float) -> float:
    """Total Klein-Nishina cross section per electron (cm²/electron).

    Exact closed-form expression (Evans 1955):
    σ = 2π r₀² {[(1+ε)/ε³] [2(1+ε)/(1+2ε) - ln(1+2ε)/ε]
                + ln(1+2ε)/(2ε) - (1+3ε)/(1+2ε)²}
    where ε = E / m_e c²
    """
    eps = E_MeV / _M_E
    if eps < 0.01:
        # Use series expansion to avoid catastrophic cancellation at low energy.
        # σ/σ_T ≈ 1 - 2ε + 26ε²/5 - …  (Evans 1955 §23-2)
        return (8.0 / 3.0) * math.pi * _R0**2 * (1.0 - 2.0 * eps + 5.2 * eps**2)
    # Exact closed-form (Evans 1955 eq. 23-12); prefactor: 2π r₀²
    # Note: coefficient is (1+ε)/ε², not ε³ — the bracket below is
    #       2(1+ε)/(1+2ε) − ln(1+2ε)/ε  (= [Wikipedia bracket] / ε)
    term1 = (1.0 + eps) / eps**2 * (
        2.0 * (1.0 + eps) / (1.0 + 2.0 * eps) - math.log(1.0 + 2.0 * eps) / eps
    )
    term2 = math.log(1.0 + 2.0 * eps) / (2.0 * eps)
    term3 = -(1.0 + 3.0 * eps) / (1.0 + 2.0 * eps) ** 2
    return 2.0 * math.pi * _R0**2 * (term1 + term2 + term3)


def klein_nishina_polar_fig(
    E_MeV_list: list[float],
    n_theta: int = 360,
    show_thomson: bool = True,
) -> plt.Figure:
    """Polar plot of dσ/dΩ vs scattering angle for a list of energies.

    Parameters
    ----------
    E_MeV_list   : list of photon energies (MeV)
    n_theta      : angular resolution (default 360 → 1°)
    show_thomson : overlay Thomson (low-energy) limit
    """
    from shieldlab.viz import OKABE_ITO  # noqa: PLC0415

    theta = np.linspace(0, 2 * math.pi, n_theta)
    cos_t = np.cos(theta)
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(6, 6))

    # Convert cm²/sr to millibarns/sr for readability
    Mbarn = 1e27  # 1 cm² = 1e27 mb

    colours = OKABE_ITO[:len(E_MeV_list)]
    for E, col in zip(E_MeV_list, colours):
        ds = dsigma_dOmega(E, theta) * Mbarn
        ax.plot(theta, ds, color=col, lw=1.5, label=f"{E*1000:.0f} keV")

    if show_thomson:
        # dσ/dΩ_Thomson = ½ r₀² (1 + cos²θ)  [cm²/sr]
        ds_thomson = 0.5 * _R0**2 * (1.0 + cos_t**2) * Mbarn
        ax.plot(theta, ds_thomson, "k--", lw=1.0, label="Thomson (low E)")

    ax.set_theta_zero_location("W")  # 0° points left (forward scatter = right)
    ax.set_theta_direction(-1)
    ax.set_xlabel(r"$d\sigma/d\Omega$ (mb sr$^{-1}$ electron$^{-1}$)", labelpad=15)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=8)
    ax.set_title("Klein-Nishina Differential Cross Section", pad=12)
    fig.tight_layout()
    return fig


def compton_energy_fig(E_MeV_list: list[float]) -> plt.Figure:
    """Plot scattered photon energy E'(θ) and Compton electron energy T(θ)."""
    from shieldlab.viz import OKABE_ITO  # noqa: PLC0415

    theta_deg = np.linspace(0, 180, 360)
    theta_rad = np.deg2rad(theta_deg)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    colours = OKABE_ITO[:len(E_MeV_list)]

    for E, col in zip(E_MeV_list, colours):
        E_prime = np.array([compton_energy(E, t) for t in theta_rad])
        T_e = E - E_prime                         # Compton electron kinetic energy
        keV_in = E * 1000
        ax1.plot(theta_deg, E_prime * 1000, color=col, lw=1.5, label=f"{keV_in:.0f} keV")
        ax2.plot(theta_deg, T_e * 1000,    color=col, lw=1.5, label=f"{keV_in:.0f} keV")

    ax1.set_xlabel("Scattering angle θ (°)")
    ax1.set_ylabel("Scattered photon energy E' (keV)")
    ax1.set_title("Compton Scattered Photon Energy")
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    ax2.set_xlabel("Scattering angle θ (°)")
    ax2.set_ylabel("Compton electron kinetic energy T (keV)")
    ax2.set_title("Compton Electron Kinetic Energy")
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig
