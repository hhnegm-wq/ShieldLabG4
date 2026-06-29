"""Tests for shieldlab.io.session — round-trip JSON save/load."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _p in [str(_ROOT / "python"), str(_ROOT / "ui")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import json
import numpy as np
import pytest

from shieldlab.io.session import save_session, load_session, SCHEMA_VERSION


def _make_calc_state() -> dict:
    """Create a minimal calc_state dict mimicking shielding_calculator.py output."""
    return {
        "mat_name":       "Lead",
        "density":        11.35,
        "mass_fractions": {"Pb": 1.0},
        "energies_MeV":   np.linspace(0.1, 10.0, 5),
        "thicknesses_cm": np.array([0.5, 1.0, 2.0]),
        "particle":       "gamma",
        "energy_display": "0.1–10 MeV",
        "gp_mat":         "Lead",
        "mac_arr":        np.array([5.54, 0.71, 0.50, 0.41, 0.38]),
        "hvl_arr":        np.array([0.011, 0.086, 0.122, 0.149, 0.161]),
    }


class TestSessionRoundTrip:
    """Verify that save_session → load_session preserves all data."""

    def test_schema_version_preserved(self):
        cs = _make_calc_state()
        raw = save_session(cs)
        payload = json.loads(raw)
        assert payload["schema_version"] == SCHEMA_VERSION

    def test_checksum_present(self):
        cs = _make_calc_state()
        raw = save_session(cs)
        payload = json.loads(raw)
        assert "checksum" in payload and len(payload["checksum"]) > 0

    def test_scalar_roundtrip(self):
        cs = _make_calc_state()
        raw = save_session(cs)
        cs2 = load_session(raw.encode())
        assert cs2["mat_name"] == "Lead"
        assert abs(cs2["density"] - 11.35) < 1e-9

    def test_numpy_roundtrip(self):
        """np.ndarray values should survive serialisation as np.ndarray."""
        cs = _make_calc_state()
        raw = save_session(cs)
        cs2 = load_session(raw.encode())
        assert isinstance(cs2["energies_MeV"], np.ndarray), \
            "energies_MeV should be restored as np.ndarray"
        np.testing.assert_allclose(cs2["energies_MeV"], cs["energies_MeV"])

    def test_nested_dict_roundtrip(self):
        cs = _make_calc_state()
        raw = save_session(cs)
        cs2 = load_session(raw.encode())
        assert cs2["mass_fractions"] == {"Pb": 1.0}

    def test_load_from_path(self, tmp_path):
        """load_session should accept a Path."""
        cs = _make_calc_state()
        raw = save_session(cs)
        p = tmp_path / "test.shieldlab"
        p.write_text(raw, encoding="utf-8")
        cs2 = load_session(p)
        assert cs2["mat_name"] == "Lead"

    def test_corrupted_checksum_raises(self):
        """A tampered payload should raise ValueError."""
        cs = _make_calc_state()
        raw = save_session(cs)
        payload = json.loads(raw)
        payload["checksum"] = "badhash000000"
        tampered = json.dumps(payload)
        with pytest.raises(ValueError, match="[Cc]hecksum"):
            load_session(tampered.encode())


class TestSessionNumpyEncoder:
    """Edge cases for the numpy JSON encoder."""

    def test_integer_scalar(self):
        cs = {"x": np.int64(42)}
        raw = save_session(cs)
        cs2 = load_session(raw.encode())
        assert cs2["x"] == 42

    def test_float_scalar(self):
        cs = {"y": np.float32(3.14)}
        raw = save_session(cs)
        cs2 = load_session(raw.encode())
        assert abs(cs2["y"] - 3.14) < 0.001

    def test_bool_scalar(self):
        cs = {"flag": np.bool_(True)}
        raw = save_session(cs)
        cs2 = load_session(raw.encode())
        assert cs2["flag"] is True
