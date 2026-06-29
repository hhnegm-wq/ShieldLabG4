"""ANSI/ANS-6.4.3-1991 G-P buildup factor validation (scaffold).

STATUS (Phase 1, partial)
-------------------------
The fully-cited Harima 1993 / ANSI/ANS-6.4.3-1991 reference table is
**not yet bundled**: the standard is copyrighted and shipping a
digitised copy of Table 4 inside this repository requires either a
licensed redistribution agreement or a clearly-cited public re-derivation
(NUREG/CR-5740, IAEA-TECDOC-1308, etc.). Until that data lands under
``data/references/ansi_ans_643/`` with a passing reference sidecar, this
module exposes a **self-consistency regression check** instead of a true
literature-comparison test:

    * For each canonical material in
      :data:`shieldlab.physics.shielding_params._GP_EBF` we evaluate
      ``gp_buildup_factor`` at the energies present in its own
      coefficient table for a fixed mfp grid.
    * The values are stored in ``buildup_baseline.json`` (committed under
      version control). Tests fail if the implementation drifts away
      from the recorded baseline — catching accidental refactoring bugs.

When the licensed reference data is added, swap ``REF_BUILDUP`` from the
self-consistency baseline to the published values and the validator
becomes a true cross-check (the API does not change).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REF_MFP = np.array([1.0, 2.0, 4.0, 7.0])

_BASELINE_PATH = Path(__file__).with_name("buildup_baseline.json")


def _materials_and_energies() -> dict[str, np.ndarray]:
    """Energies tabulated for each canonical (non-alias) material."""
    from shieldlab.physics.shielding_params import _GP_EBF  # type: ignore[attr-defined]

    canonical = ("Water", "Concrete", "Iron", "Lead")
    return {m: _GP_EBF[m][:, 0].copy() for m in canonical if m in _GP_EBF}


def _compute_matrix(material: str, energies: np.ndarray) -> np.ndarray:
    from shieldlab.physics.shielding_params import gp_buildup_factor

    out = np.zeros((len(energies), len(REF_MFP)))
    for i, e in enumerate(energies):
        for j, mfp in enumerate(REF_MFP):
            out[i, j] = float(gp_buildup_factor(float(e), float(mfp), material=material))
    return out


def regenerate_baseline() -> Path:
    """Recompute the self-consistency baseline from current GP coefficients."""
    payload: dict[str, dict] = {}
    for material, energies in _materials_and_energies().items():
        matrix = _compute_matrix(material, energies)
        payload[material] = {
            "energies_MeV": energies.tolist(),
            "mfp": REF_MFP.tolist(),
            "buildup": matrix.tolist(),
            "note": (
                "Self-consistency snapshot of the shipped G-P coefficients; "
                "NOT a literature reference. Replace with ANSI/ANS-6.4.3-1991 "
                "values once a licensed copy is shipped under data/references/."
            ),
        }
    _BASELINE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return _BASELINE_PATH


def _load_baseline() -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    if not _BASELINE_PATH.exists():
        regenerate_baseline()
    raw = json.loads(_BASELINE_PATH.read_text(encoding="utf-8"))
    energies = {m: np.asarray(v["energies_MeV"], float) for m, v in raw.items()}
    refs = {m: np.asarray(v["buildup"], float) for m, v in raw.items()}
    return energies, refs


_ENERGIES, REF_BUILDUP = _load_baseline()


@dataclass
class BuildupValidationResult:
    material: str
    energies_MeV: np.ndarray
    mfp: np.ndarray
    reference: np.ndarray
    computed: np.ndarray
    rel_residual: np.ndarray  # (computed - ref) / ref

    @property
    def mean_abs_residual(self) -> float:
        return float(np.mean(np.abs(self.rel_residual)))

    @property
    def max_abs_residual(self) -> float:
        return float(np.max(np.abs(self.rel_residual)))


def validate_material(material: str) -> BuildupValidationResult:
    if material not in REF_BUILDUP:
        raise KeyError(
            f"No baseline for material={material!r}. Available: {sorted(REF_BUILDUP)}."
        )
    energies = _ENERGIES[material]
    ref = REF_BUILDUP[material]
    computed = _compute_matrix(material, energies)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.where(ref != 0.0, (computed - ref) / ref, 0.0)
    return BuildupValidationResult(
        material=material,
        energies_MeV=energies,
        mfp=REF_MFP,
        reference=ref,
        computed=computed,
        rel_residual=rel,
    )


def validate_all(tolerance: float = 1e-6) -> dict[str, BuildupValidationResult]:
    return {m: validate_material(m) for m in REF_BUILDUP}


__all__ = [
    "REF_MFP",
    "REF_BUILDUP",
    "BuildupValidationResult",
    "validate_material",
    "validate_all",
    "regenerate_baseline",
]
