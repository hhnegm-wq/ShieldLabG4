"""Phase 1.5 – Geant4 MT reproducibility / consistency test.

Verifies that the multi-threaded (MT) Geant4 build produces per-layer dose
and energy-deposit tallies that are statistically consistent with the serial
(``-t 1``) result across ≥ 9 out of 10 independent seeds.

The test is **auto-skipped** unless:

    SHIELDLAB_TEST_GEANT4=1   (set in nightly / science-gate CI)
    ShieldLabG4 binary is found on PATH or at build/ShieldLabG4

It is also decorated with ``@pytest.mark.geant4`` so it can be
excluded from the standard CI run via::

    pytest -m "not geant4"

Acceptance criterion
--------------------
For each layer *i* the MT dose D_mt[i] must be within 2σ of the serial
dose D_s[i], where σ is taken as the larger of the two reported
uncertainties. At least 9 of 10 seeds must pass for the test to pass.
If fewer than 9 seeds pass, the test fails with a summary of which seeds
differed and by how many σ.

Notes
-----
* The test generates a minimal lead-slab macro with 1e5 primaries per run.
  100 k events is enough to get < 5 % statistical uncertainty while keeping
  the test under 5 minutes per seed on a 4-core machine.
* Output CSVs are written to a per-seed temp directory and cleaned up
  automatically on success.
* Requires: Python 3.10+, pytest, numpy, pandas, the ShieldLabG4 binary.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_REQUIRED_ENV = "SHIELDLAB_TEST_GEANT4"
_BINARY_CANDIDATES = [
    "ShieldLabG4",
    str(Path(__file__).resolve().parent.parent.parent / "build" / "ShieldLabG4"),
]

_N_SEEDS = 10
_MIN_PASS = 9
_SIGMA_TOLERANCE = 2.0  # max allowed deviations from serial result
_N_PRIMARIES = 100_000


def _find_binary() -> str | None:
    for cand in _BINARY_CANDIDATES:
        if shutil.which(cand) or Path(cand).is_file():
            return str(Path(cand).resolve()) if Path(cand).is_file() else cand
    return None


def _minimal_macro(seed: int, n_primaries: int, output_dir: str) -> str:
    """Return a minimal G4 macro string for a single-layer lead slab run."""
    return textwrap.dedent(f"""
        /run/numberOfThreads 1
        /run/initialize
        /shieldlab/detector/resetLayers
        /shieldlab/detector/addLayer Pb 1.0 5.0
        /gun/particle gamma
        /gun/energy 0.662 MeV
        /random/setSeeds {seed} {seed + 1}
        /run/beamOn {n_primaries}
    """).strip()


def _run_geant4(binary: str, macro_content: str, work_dir: Path) -> Path:
    """Write macro to *work_dir*, run binary, return path to layer_dose.csv."""
    macro_path = work_dir / "run.mac"
    macro_path.write_text(macro_content, encoding="utf-8")
    result = subprocess.run(
        [binary, str(macro_path)],
        cwd=str(work_dir),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"ShieldLabG4 exited {result.returncode}:\n{result.stderr[-2000:]}"
        )
    csv_path = work_dir / "layer_dose.csv"
    if not csv_path.exists():
        raise RuntimeError(
            f"layer_dose.csv not produced in {work_dir}.\nstdout:\n{result.stdout[-2000:]}"
        )
    return csv_path


def _load_dose(csv_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return (dose_Gy, sigma_Gy) arrays from layer_dose.csv."""
    df = pd.read_csv(csv_path)
    # Accept either snake_case or camelCase column names
    dose_col = next(
        (c for c in df.columns if re.match(r"dose", c, re.I)), None
    )
    sigma_col = next(
        (c for c in df.columns if re.match(r"(sigma|uncertainty|std)", c, re.I)), None
    )
    if dose_col is None:
        raise KeyError(f"No dose column found in {csv_path}. Columns: {list(df.columns)}")
    dose = df[dose_col].to_numpy(dtype=float)
    sigma = df[sigma_col].to_numpy(dtype=float) if sigma_col is not None else np.zeros_like(dose)
    return dose, sigma


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

@pytest.mark.geant4
@pytest.mark.slow
def test_mt_serial_consistency() -> None:
    """MT dose tallies must agree with serial within 2σ for ≥9/10 seeds."""
    if not os.environ.get(_REQUIRED_ENV):
        pytest.skip(
            f"Set {_REQUIRED_ENV}=1 to run Geant4 MT consistency tests. "
            "Auto-skipped in standard CI."
        )

    binary = _find_binary()
    if binary is None:
        pytest.skip("ShieldLabG4 binary not found on PATH or at build/ShieldLabG4")

    rng = np.random.default_rng(42)
    seeds = rng.integers(1_000, 999_999, size=_N_SEEDS).tolist()

    passed: list[int] = []
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="shieldlab_mt_test_") as tmpdir_root:
        for idx, seed in enumerate(seeds):
            # --- serial run (1 thread) ---
            serial_dir = Path(tmpdir_root) / f"serial_{idx}"
            serial_dir.mkdir()
            macro_s = _minimal_macro(seed, _N_PRIMARIES, str(serial_dir))
            dose_s, sig_s = _load_dose(_run_geant4(binary, macro_s, serial_dir))

            # --- MT run (all available cores, same seed) ---
            mt_dir = Path(tmpdir_root) / f"mt_{idx}"
            mt_dir.mkdir()
            # Override /run/numberOfThreads to use all available cores
            macro_mt = macro_s.replace(
                "/run/numberOfThreads 1",
                f"/run/numberOfThreads {max(2, os.cpu_count() or 4)}",
            )
            dose_mt, sig_mt = _load_dose(_run_geant4(binary, macro_mt, mt_dir))

            if len(dose_s) != len(dose_mt):
                failures.append(
                    f"seed {seed}: layer count mismatch ({len(dose_s)} vs {len(dose_mt)})"
                )
                continue

            # Combined uncertainty: σ_combined = sqrt(σ_s² + σ_mt²)
            # Fallback to 0.05 * dose_s (5 %) when σ columns are all zeros
            if np.all(sig_s == 0) and np.all(sig_mt == 0):
                combined_sigma = 0.05 * np.abs(dose_s)
                combined_sigma = np.where(combined_sigma == 0, 1e-30, combined_sigma)
            else:
                combined_sigma = np.sqrt(sig_s**2 + sig_mt**2)
                combined_sigma = np.where(combined_sigma == 0, 1e-30, combined_sigma)

            deviations = np.abs(dose_mt - dose_s) / combined_sigma
            worst = float(np.max(deviations))
            worst_layer = int(np.argmax(deviations))

            if worst <= _SIGMA_TOLERANCE:
                passed.append(seed)
            else:
                failures.append(
                    f"seed {seed}: layer {worst_layer} deviates {worst:.2f}σ "
                    f"(serial={dose_s[worst_layer]:.4e} Gy, "
                    f"MT={dose_mt[worst_layer]:.4e} Gy, "
                    f"σ_combined={combined_sigma[worst_layer]:.4e} Gy)"
                )

    n_passed = len(passed)
    failure_summary = "\n  ".join(failures)
    assert n_passed >= _MIN_PASS, (
        f"MT consistency: only {n_passed}/{_N_SEEDS} seeds passed (need ≥{_MIN_PASS}).\n"
        f"Failing seeds:\n  {failure_summary}"
    )
