from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_workspace_settings_hide_transient_artifacts() -> None:
    settings_path = ROOT / ".vscode" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))

    expected_entries = {
        "backups": True,
        "build": True,
        "results": True,
        "tmp": True,
        ".benchmarks": True,
        ".streamlit": True,
        "streamlit_debug.log": True,
    }

    assert settings.get("files.exclude") == expected_entries
    assert settings.get("search.exclude") == expected_entries


def test_workspace_settings_reduce_watcher_noise() -> None:
    settings_path = ROOT / ".vscode" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    watcher_excludes = settings.get("files.watcherExclude", {})

    for pattern in (
        "**/backups/**",
        "**/build/**",
        "**/results/**",
        "**/tmp/**",
        "**/.benchmarks/**",
        "**/.streamlit/**",
    ):
        assert watcher_excludes.get(pattern) is True