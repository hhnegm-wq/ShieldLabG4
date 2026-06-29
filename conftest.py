"""Repo-root pytest configuration.

Phase 0/2 hardening: declares pytest marker taxonomy so tests can be
selected by intent (CI vs nightly vs publication gate).

Markers
-------
unit         Pure-python, < 100 ms.
integration  Cross-module, no network/Geant4.
network      Requires external HTTP (NIST XCOM, etc.).
ui           Streamlit / Playwright surface.
geant4       Requires the ShieldLabG4 binary or libG4* available.
slow         > 30 s.
publication  Validates publication thresholds; blocking pre-release only.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest


_MARKERS = {
    "unit": "Pure-python, fast (<100 ms).",
    "integration": "Cross-module without network or Geant4.",
    "network": "Requires external HTTP access.",
    "ui": "Exercises the Streamlit UI (Playwright).",
    "geant4": "Requires Geant4 binary / libraries.",
    "slow": "Long-running (>30 s).",
    "publication": "Publication-readiness gate; pre-release only.",
}


def pytest_configure(config: pytest.Config) -> None:
    for name, desc in _MARKERS.items():
        config.addinivalue_line("markers", f"{name}: {desc}")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip network/UI/Geant4/publication tests unless explicitly opted in.

    Opt-in via env vars or `-m` selection. Default CI lane is unit + integration.
    """
    selected_marks = (config.getoption("-m") or "").lower()
    explicit_select = bool(selected_marks)
    allow_network = os.environ.get("SHIELDLAB_TEST_NETWORK", "0") == "1"
    allow_ui = os.environ.get("SHIELDLAB_UI_SMOKE", "0") == "1"
    allow_publication = os.environ.get("SHIELDLAB_TEST_PUBLICATION", "0") == "1"
    have_geant4 = shutil.which("ShieldLabG4") is not None or any(
        Path(p).name.startswith("ShieldLabG4") for p in Path("build").glob("ShieldLabG4*")
    )

    skip_network = pytest.mark.skip(reason="network test (set SHIELDLAB_TEST_NETWORK=1)")
    skip_ui = pytest.mark.skip(reason="UI test (set SHIELDLAB_UI_SMOKE=1)")
    skip_g4 = pytest.mark.skip(reason="Geant4 binary not found")
    skip_pub = pytest.mark.skip(reason="publication test (set SHIELDLAB_TEST_PUBLICATION=1)")

    for item in items:
        marks = {m.name for m in item.iter_markers()}
        if explicit_select:
            continue
        if "network" in marks and not allow_network:
            item.add_marker(skip_network)
        if "ui" in marks and not allow_ui:
            item.add_marker(skip_ui)
        if "geant4" in marks and not have_geant4:
            item.add_marker(skip_g4)
        if "publication" in marks and not allow_publication:
            item.add_marker(skip_pub)
