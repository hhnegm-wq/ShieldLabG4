"""Material descriptor calculations for shielding materials.

Computes derived quantities from elemental mass-fraction compositions:
  - Molar mass (g/mol)
  - Average atomic number Z_avg
  - Effective atomic number Z_eff (power-law)
  - Effective electron number N_eff (power-law)
  - Electron density (electrons/cm^3)
  - Elemental expansion table

All formulae follow the standard shielding-literature conventions used
in Phy-X / WinXCom and related tools.

Z_eff exponent conventions
--------------------------
* **3.5 (default)** — Manohara et al. (2008) [1] show that n = 3.5 gives
  the best fit across the broad photon energy range relevant to radiation
  shielding (0.01 – 15 MeV).  This is the value used by Phy-X/PSD and is
  returned as ``Zeff_3p5`` in :func:`material_descriptors`.
* **2.94 (legacy)** — Hine (1952) [2] recommended n ≈ 2.94 for bone-like
  mixtures.  Retained for backward compatibility as ``Zeff_2p94`` in
  :func:`material_descriptors`.

References
----------
[1] Manohara, S.R., Hanagodimath, S.M., Thind, K.S., Gerward, L. (2008).
    "On the effective atomic number and electron density: A comprehensive
    set of formulas for all types of materials and energies above 1 keV."
    *Nucl. Instrum. Methods Phys. Res. B* **266**, 3906–3912.
    https://doi.org/10.1016/j.nimb.2008.06.034
[2] Hine, G.J. (1952). "The effective atomic numbers of materials for
    various γ-ray interactions." *Phys. Rev.* **85**, 725.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from shieldlab.core.materials import ATOMIC_WEIGHTS

# Number of electrons == atomic number for neutral atoms
ATOMIC_NUMBERS: dict[str, int] = {
    "H":  1, "He":  2, "Li":  3, "Be":  4, "B":   5, "C":   6, "N":   7, "O":   8, "F":   9, "Ne": 10,
    "Na":11, "Mg": 12, "Al": 13, "Si": 14, "P":  15, "S":  16, "Cl": 17, "Ar": 18, "K":  19, "Ca": 20,
    "Sc":21, "Ti": 22, "V":  23, "Cr": 24, "Mn": 25, "Fe": 26, "Co": 27, "Ni": 28, "Cu": 29, "Zn": 30,
    "Ga":31, "Ge": 32, "As": 33, "Se": 34, "Br": 35, "Kr": 36, "Rb": 37, "Sr": 38, "Y":  39, "Zr": 40,
    "Nb":41, "Mo": 42, "Tc": 43, "Ru": 44, "Rh": 45, "Pd": 46, "Ag": 47, "Cd": 48, "In": 49, "Sn": 50,
    "Sb":51, "Te": 52, "I":  53, "Xe": 54, "Cs": 55, "Ba": 56, "La": 57, "Ce": 58, "Pr": 59, "Nd": 60,
    "Pm":61, "Sm": 62, "Eu": 63, "Gd": 64, "Tb": 65, "Dy": 66, "Ho": 67, "Er": 68, "Tm": 69, "Yb": 70,
    "Lu":71, "Hf": 72, "Ta": 73, "W":  74, "Re": 75, "Os": 76, "Ir": 77, "Pt": 78, "Au": 79, "Hg": 80,
    "Tl":81, "Pb": 82, "Bi": 83, "Po": 84, "At": 85, "Rn": 86, "Fr": 87, "Ra": 88, "Ac": 89, "Th": 90,
    "Pa":91, "U":  92,
}

# Avogadro constant
AVOGADRO = 6.02214076e23

# Power-law exponent: Manohara et al. (2008) Nucl. Instrum. Methods B 266:3906
# Best-fit across 0.01–15 MeV; matches Phy-X/PSD default.
ZEFF_EXPONENT = 3.5          # Manohara 2008 (default)
ZEFF_HINE_EXPONENT = 2.94    # Hine 1952 (legacy / backward-compat reference)


def _electron_fractions(mass_fractions: dict[str, float]) -> dict[str, float]:
    """Convert mass fractions to electron (mole-electron weighted) fractions."""
    raw: dict[str, float] = {}
    for element, wf in mass_fractions.items():
        Z = ATOMIC_NUMBERS.get(element)
        Aw = ATOMIC_WEIGHTS.get(element)
        if Z is None or Aw is None:
            raise ValueError(f"No atomic data for element: {element}")
        raw[element] = wf * Z / Aw
    total = sum(raw.values())
    if total <= 0:
        raise ValueError("Electron fraction total is non-positive")
    return {el: val / total for el, val in raw.items()}


def molar_mass(mass_fractions: dict[str, float]) -> float:
    """Effective molar mass (g/mol) via the mixture rule 1/M = sum(wi/Mi)."""
    inv = sum(wf / ATOMIC_WEIGHTS[el] for el, wf in mass_fractions.items() if el in ATOMIC_WEIGHTS)
    if inv <= 0:
        raise ValueError("Cannot compute molar mass: zero or missing atomic weights")
    return 1.0 / inv


def average_atomic_number(mass_fractions: dict[str, float]) -> float:
    """Mass-fraction weighted average Z."""
    return sum(wf * ATOMIC_NUMBERS[el] for el, wf in mass_fractions.items() if el in ATOMIC_NUMBERS)


def zeff(mass_fractions: dict[str, float], exponent: float = ZEFF_EXPONENT) -> float:
    """Effective atomic number via the power-law formula.

    Z_eff = (sum_i f_ei * Z_i^n)^(1/n)

    where f_ei are electron fractions and n is the exponent.

    Parameters
    ----------
    exponent:
        Power-law exponent.  Default ``ZEFF_EXPONENT = 3.5`` (Manohara 2008,
        recommended for broad photon energy range 0.01–15 MeV).
        Use ``ZEFF_HINE_EXPONENT = 2.94`` for the Hine 1952 legacy value.
    """
    ef = _electron_fractions(mass_fractions)
    raw = sum(fe * (ATOMIC_NUMBERS[el] ** exponent) for el, fe in ef.items() if el in ATOMIC_NUMBERS)
    if raw <= 0:
        return 0.0
    return raw ** (1.0 / exponent)


def neff(mass_fractions: dict[str, float], density_g_cm3: float, exponent: float = ZEFF_EXPONENT) -> float:
    """Effective electron density (electrons/cm^3) via the power-law formula.

    N_eff = (Z_eff / Z_avg) * (density * N_A / M_eff) * Z_avg
          = density * N_A * sum_i (wi * Z_i / Ai)
    """
    n_electrons = sum(
        wf * ATOMIC_NUMBERS.get(el, 0) / ATOMIC_WEIGHTS[el]
        for el, wf in mass_fractions.items()
        if el in ATOMIC_WEIGHTS and el in ATOMIC_NUMBERS
    )
    return density_g_cm3 * AVOGADRO * n_electrons


def electron_density(mass_fractions: dict[str, float], density_g_cm3: float) -> float:
    """Physical electron density (electrons/cm^3)."""
    return neff(mass_fractions, density_g_cm3)


def mole_fractions(mass_fractions: dict[str, float]) -> dict[str, float]:
    """
    Elemental mole fractions Fᵢ (atom fractions) from weight fractions Wᵢ.

    Fᵢ = (Wᵢ / Aᵢ) / Σⱼ(Wⱼ / Aⱼ)

    Returns a dict {element: mole_fraction} that sums to 1.0.
    Corresponds to the 'Fi' column in Phy-X output.
    """
    raw: dict[str, float] = {}
    for el, wf in mass_fractions.items():
        Aw = ATOMIC_WEIGHTS.get(el)
        if Aw:
            raw[el] = wf / Aw
    total = sum(raw.values())
    if total <= 0:
        return {}
    return {el: v / total for el, v in raw.items()}


def material_descriptors(
    name: str,
    mass_fractions: dict[str, float],
    density_g_cm3: float,
) -> dict[str, Any]:
    """Compute the full descriptor dict for a material."""
    try:
        M = molar_mass(mass_fractions)
    except ValueError:
        M = float("nan")
    try:
        Z_avg = average_atomic_number(mass_fractions)
    except (ValueError, KeyError):
        Z_avg = float("nan")
    try:
        Z_eff = zeff(mass_fractions)
    except (ValueError, KeyError):
        Z_eff = float("nan")
    try:
        N_eff = neff(mass_fractions, density_g_cm3)
    except (ValueError, KeyError):
        N_eff = float("nan")
    try:
        e_density = electron_density(mass_fractions, density_g_cm3)
    except (ValueError, KeyError):
        e_density = float("nan")
    try:
        Z_eff_294 = zeff(mass_fractions, exponent=2.94)
    except (ValueError, KeyError):
        Z_eff_294 = float("nan")
    try:
        mf_dict = mole_fractions(mass_fractions)
    except (ValueError, KeyError):
        mf_dict = {}
    # Static Neff per gram: N_A × Σ(wᵢ×Zᵢ/Aᵢ) — energy-independent
    neff_per_g = sum(
        wf * ATOMIC_NUMBERS.get(el, 0) / ATOMIC_WEIGHTS[el]
        for el, wf in mass_fractions.items()
        if el in ATOMIC_WEIGHTS and el in ATOMIC_NUMBERS
    ) * AVOGADRO

    return {
        "material": name,
        "density_g_cm3": density_g_cm3,
        "molar_mass_g_mol": M,
        "average_Z": Z_avg,
        "Zeff_3p5": Z_eff,
        "Zeff_2p94": Z_eff_294,
        "Neff_per_gram": neff_per_g,
        "Neff_electrons_cm3": N_eff,
        "electron_density_cm3": e_density,
        "mole_fractions": mf_dict,
    }


def descriptors_from_study(study: dict[str, Any]) -> pd.DataFrame:
    """Build a descriptor DataFrame from all materials defined in a study.

    Materials without any composition mode (NIST-only references) are skipped.
    """
    from shieldlab.core.materials import resolve_material_mass_fractions

    rows = []
    for material in study.get("materials", []):
        name = material.get("name", "unknown")
        density = material.get("density_g_cm3", float("nan"))
        try:
            fractions = resolve_material_mass_fractions(material)
        except (ValueError, KeyError):
            continue
        rows.append(material_descriptors(name, fractions, float(density)))

    return pd.DataFrame(rows)


def elemental_expansion_table(study: dict[str, Any]) -> pd.DataFrame:
    """Return a long-form table of elemental mass fractions for all materials in a study."""
    from shieldlab.core.materials import resolve_material_mass_fractions

    rows = []
    for material in study.get("materials", []):
        name = material.get("name", "unknown")
        try:
            fractions = resolve_material_mass_fractions(material)
        except (ValueError, KeyError):
            fractions = {}
        for element, fraction in sorted(fractions.items()):
            Z = ATOMIC_NUMBERS.get(element)
            Aw = ATOMIC_WEIGHTS.get(element)
            rows.append({
                "material": name,
                "element": element,
                "Z": Z,
                "atomic_weight": Aw,
                "mass_fraction": fraction,
            })

    return pd.DataFrame(rows)
