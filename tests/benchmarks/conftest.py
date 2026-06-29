r"""Shared fixtures for ShieldLab G4 benchmark tests.

These tests compare computed MAC / HVL / TVL values against published
NIST XrayMassCoef and standard textbook values.  They are kept in a
separate directory so they can be run independently:

    cd D:\projects\ShieldLabG4
    $env:PYTHONPATH="python;ui"
    d:/uv_envs/Scripts/python.exe -m pytest tests/benchmarks/ -v
"""
import sys
import pathlib

import numpy as np
import pytest

# ── ensure project paths are importable ──────────────────────────────────────
_ROOT = pathlib.Path(__file__).resolve().parents[2]
for _p in (_ROOT / "python", _ROOT / "ui"):
    p_str = str(_p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)


# ── shared helper ─────────────────────────────────────────────────────────────

def compute_mac(mass_fractions: dict, density: float, energy_MeV: float) -> float:
    """Return computed MAC (cm²/g) for a single energy."""
    import pandas as pd
    from shieldlab.physics.shielding_params import compute_shielding_table

    E = np.array([energy_MeV])
    df: pd.DataFrame = compute_shielding_table(mass_fractions, density, E)
    return float(df.iloc[0]["μ/ρ (cm²/g)"])


def compute_hvl(mass_fractions: dict, density: float, energy_MeV: float) -> float:
    """Return computed HVL (cm) for a single energy."""
    import pandas as pd
    from shieldlab.physics.shielding_params import compute_shielding_table

    E = np.array([energy_MeV])
    df: pd.DataFrame = compute_shielding_table(mass_fractions, density, E)
    return float(df.iloc[0]["HVL (cm)"])


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def water_mf():
    return {"H": 0.1119, "O": 0.8881}


@pytest.fixture(scope="session")
def lead_mf():
    return {"Pb": 1.0}


@pytest.fixture(scope="session")
def hdpe_mf():
    return {"H": 0.1437, "C": 0.8563}


@pytest.fixture(scope="session")
def iron_mf():
    return {"Fe": 1.0}


@pytest.fixture(scope="session")
def concrete_mf():
    return {
        "H": 0.0221, "C": 0.0020, "O": 0.6574, "Na": 0.0015,
        "Mg": 0.0019, "Al": 0.0189, "Si": 0.3040, "K": 0.0100,
        "Ca": 0.0296, "Fe": 0.0041,
    }
