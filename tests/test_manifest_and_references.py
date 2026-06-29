"""Tests for shieldlab.io.manifest and reference_loader."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from shieldlab.data.reference_loader import load_sidecar
from shieldlab.io.manifest import build_manifest


@pytest.mark.unit
def test_build_manifest_writes_required_fields(tmp_path: Path) -> None:
    out = build_manifest(
        output_dir=tmp_path,
        config={"a": 1, "b": [2, 3]},
        seed=42,
        extra={"study_id": "test"},
    )
    on_disk = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    for key in ("schema_version", "generated_at_utc", "config_hash", "seed", "python"):
        assert key in on_disk
    assert on_disk["seed"] == 42
    assert out["config_hash"] == on_disk["config_hash"]


@pytest.mark.unit
def test_reference_sidecar_rejects_placeholder(tmp_path: Path) -> None:
    p = tmp_path / "bad.ref.json"
    p.write_text(json.dumps({
        "id": "x",
        "title": "y",
        "doi": "example_baseline_replace_with_xcom_or_paper",
        "url": "https://example.com",
        "retrieved_at": "2026-05-11",
        "license": "CC-BY-4.0",
        "columns": {"E": {"units": "MeV"}},
        "data_file": "x.csv",
    }), encoding="utf-8")
    with pytest.raises(ValueError):
        load_sidecar(p)


@pytest.mark.unit
def test_reference_sidecar_accepts_full(tmp_path: Path) -> None:
    p = tmp_path / "good.ref.json"
    p.write_text(json.dumps({
        "id": "icrp74_table_a21",
        "title": "ICRP-74 Table A.21",
        "doi": "10.1016/S0146-6453(96)90004-X",
        "url": "https://www.icrp.org/publication.asp?id=ICRP%20Publication%2074",
        "retrieved_at": "2026-05-11",
        "license": "Reproduced for academic use",
        "columns": {"E": {"units": "MeV", "description": "photon energy"}},
        "data_file": "icrp74_a21.csv",
    }), encoding="utf-8")
    sc = load_sidecar(p)
    assert sc.doi.startswith("10.")
