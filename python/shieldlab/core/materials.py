from __future__ import annotations

import re
from collections import defaultdict
from typing import Any


# Standard atomic weights — IUPAC 2021, all Z=1–92
ATOMIC_WEIGHTS = {
    "H":  1.008,   "He":  4.003,  "Li":  6.941,  "Be":  9.012,  "B":  10.811,
    "C":  12.011,  "N":  14.007,  "O":  15.999,  "F":  18.998,  "Ne": 20.180,
    "Na": 22.990,  "Mg": 24.305,  "Al": 26.982,  "Si": 28.086,  "P":  30.974,
    "S":  32.065,  "Cl": 35.453,  "Ar": 39.948,  "K":  39.098,  "Ca": 40.078,
    "Sc": 44.956,  "Ti": 47.867,  "V":  50.942,  "Cr": 51.996,  "Mn": 54.938,
    "Fe": 55.845,  "Co": 58.933,  "Ni": 58.693,  "Cu": 63.546,  "Zn": 65.38,
    "Ga": 69.723,  "Ge": 72.630,  "As": 74.922,  "Se": 78.971,  "Br": 79.904,
    "Kr": 83.798,  "Rb": 85.468,  "Sr": 87.620,  "Y":  88.906,  "Zr": 91.224,
    "Nb": 92.906,  "Mo": 95.960,  "Tc": 98.000,  "Ru":101.07,   "Rh":102.91,
    "Pd":106.42,   "Ag":107.87,   "Cd":112.41,   "In":114.82,   "Sn":118.71,
    "Sb":121.76,   "Te":127.60,   "I": 126.90,   "Xe":131.29,   "Cs":132.91,
    "Ba":137.33,   "La":138.91,   "Ce":140.12,   "Pr":140.91,   "Nd":144.24,
    "Pm":145.00,   "Sm":150.36,   "Eu":151.96,   "Gd":157.25,   "Tb":158.93,
    "Dy":162.50,   "Ho":164.93,   "Er":167.26,   "Tm":168.93,   "Yb":173.04,
    "Lu":174.97,   "Hf":178.49,   "Ta":180.95,   "W": 183.84,   "Re":186.21,
    "Os":190.23,   "Ir":192.22,   "Pt":195.08,   "Au":196.97,   "Hg":200.59,
    "Tl":204.38,   "Pb":207.20,   "Bi":208.98,   "Po":209.00,   "At":210.00,
    "Rn":222.00,   "Fr":223.00,   "Ra":226.00,   "Ac":227.00,   "Th":232.04,
    "Pa":231.04,   "U": 238.03,
}

TOKEN_PATTERN = re.compile(r"([A-Z][a-z]?|\(|\)|\d+(?:\.\d+)?)")


def parse_formula(formula: str) -> dict[str, float]:
    tokens = TOKEN_PATTERN.findall(formula.replace(" ", ""))
    if not tokens or "".join(tokens) != formula.replace(" ", ""):
        raise ValueError(f"Unsupported chemical formula: {formula}")

    stack: list[defaultdict[str, float]] = [defaultdict(float)]
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "(":
            stack.append(defaultdict(float))
            index += 1
        elif token == ")":
            if len(stack) == 1:
                raise ValueError(f"Unmatched ')' in formula: {formula}")
            group = stack.pop()
            index += 1
            multiplier = 1.0
            if index < len(tokens) and _is_number(tokens[index]):
                multiplier = float(tokens[index])
                index += 1
            for element, amount in group.items():
                stack[-1][element] += amount * multiplier
        elif _is_number(token):
            raise ValueError(f"Unexpected number '{token}' in formula: {formula}")
        else:
            element = token
            if element not in ATOMIC_WEIGHTS:
                raise ValueError(f"Atomic weight is not configured for element: {element}")
            index += 1
            amount = 1.0
            if index < len(tokens) and _is_number(tokens[index]):
                amount = float(tokens[index])
                index += 1
            stack[-1][element] += amount

    if len(stack) != 1:
        raise ValueError(f"Unmatched '(' in formula: {formula}")
    return dict(stack[0])


def formula_to_mass_fractions(formula: str) -> dict[str, float]:
    atom_counts = parse_formula(formula)
    masses = {element: count * ATOMIC_WEIGHTS[element] for element, count in atom_counts.items()}
    total_mass = sum(masses.values())
    if total_mass <= 0:
        raise ValueError(f"Formula has non-positive molecular mass: {formula}")
    return {element: mass / total_mass for element, mass in masses.items()}


def formula_mixture_to_mass_fractions(formula_mass_fractions: dict[str, float]) -> dict[str, float]:
    if not formula_mass_fractions:
        raise ValueError("formula_mass_fractions must not be empty")

    fraction_sum = sum(float(fraction) for fraction in formula_mass_fractions.values())
    if fraction_sum <= 0:
        raise ValueError("formula_mass_fractions must sum to a positive value")

    elements: defaultdict[str, float] = defaultdict(float)
    for formula, raw_fraction in formula_mass_fractions.items():
        compound_fraction = float(raw_fraction) / fraction_sum
        compound_elements = formula_to_mass_fractions(formula)
        for element, element_fraction in compound_elements.items():
            elements[element] += compound_fraction * element_fraction

    total = sum(elements.values())
    return {element: fraction / total for element, fraction in elements.items()}


def _is_number(token: str) -> bool:
    try:
        float(token)
    except ValueError:
        return False
    return True


# ── New composition-mode helpers ──────────────────────────────────────────────


def nanocomposite_to_mass_fractions(
    matrix: dict[str, Any],
    fillers: list[dict[str, Any]],
) -> dict[str, float]:
    """Expand a nanocomposite (matrix + filler nanoparticles) to elemental mass fractions.

    Each phase dict must contain ``formula`` and ``weight_fraction``.
    Fractions are normalised automatically (same as formula_mixture_to_mass_fractions).
    """
    phases: dict[str, float] = {matrix["formula"]: float(matrix["weight_fraction"])}
    for filler in (fillers or []):
        f = filler["formula"]
        phases[f] = phases.get(f, 0.0) + float(filler["weight_fraction"])
    return formula_mixture_to_mass_fractions(phases)


def volume_fractions_to_mass_fractions(phases: list[dict[str, Any]]) -> dict[str, float]:
    """Convert volume-fraction phases to elemental mass fractions.

    Each phase dict must contain ``formula``, ``density_g_cm3``, and
    ``volume_fraction``.  The effective mass fraction of each phase is
    proportional to ρ × φ before elemental expansion.
    """
    effective_wf: dict[str, float] = {}
    for phase in phases:
        mass_contrib = float(phase["density_g_cm3"]) * float(phase["volume_fraction"])
        f = phase["formula"]
        effective_wf[f] = effective_wf.get(f, 0.0) + mass_contrib
    return formula_mixture_to_mass_fractions(effective_wf)


def mixture_to_mass_fractions(phases: list[dict[str, Any]]) -> dict[str, float]:
    """Expand a named-phase mixture (each phase: ``formula`` + ``weight_fraction``)
    to elemental mass fractions.  Fractions are normalised automatically.
    """
    wf: dict[str, float] = {}
    for phase in phases:
        f = phase["formula"]
        wf[f] = wf.get(f, 0.0) + float(phase["weight_fraction"])
    return formula_mixture_to_mass_fractions(wf)


_ALL_COMPOSITION_MODES = (
    "mass_fractions",
    "formula",
    "formula_mass_fractions",
    "nanocomposite",
    "volume_fractions",
    "mixture",
)


def resolve_material_mass_fractions(material: dict[str, Any]) -> dict[str, float]:
    """Resolve *any* composition mode in a material dict to elemental mass fractions.

    Supported modes (mutually exclusive):

    * ``mass_fractions``         — explicit element → fraction mapping
    * ``formula``                — single chemical formula string
    * ``formula_mass_fractions`` — compound formula → fraction mapping
    * ``nanocomposite``          — ``{matrix: {formula, weight_fraction}, fillers: [...]}`
    * ``volume_fractions``       — list of ``{formula, density_g_cm3, volume_fraction}``
    * ``mixture``                — list of ``{formula, weight_fraction}``

    Raises :class:`ValueError` if no known mode is found.
    """
    if material.get("mass_fractions"):
        return {el: float(v) for el, v in material["mass_fractions"].items()}
    if material.get("formula"):
        return formula_to_mass_fractions(str(material["formula"]))
    if material.get("formula_mass_fractions"):
        return formula_mixture_to_mass_fractions(material["formula_mass_fractions"])
    nc = material.get("nanocomposite")
    if nc:
        return nanocomposite_to_mass_fractions(nc["matrix"], nc.get("fillers") or [])
    vf = material.get("volume_fractions")
    if vf:
        return volume_fractions_to_mass_fractions(vf)
    mx = material.get("mixture")
    if mx:
        return mixture_to_mass_fractions(mx)
    raise ValueError(
        f"Material '{material.get('name', '?')}' has no recognized composition mode "
        f"({', '.join(_ALL_COMPOSITION_MODES)})."
    )