from __future__ import annotations

import re
from pathlib import Path


def _streamlit_nested_pattern() -> re.Pattern[str]:
    caddyfile = Path("deploy/Caddyfile").read_text(encoding="utf-8")
    match = re.search(r"path_regexp\s+streamlitNested\s+(.+)$", caddyfile, re.MULTILINE)
    assert match is not None, "Missing streamlitNested path_regexp in deploy/Caddyfile"
    return re.compile(match.group(1))


def test_caddy_rewrite_matches_nested_streamlit_internal_routes() -> None:
    pattern = _streamlit_nested_pattern()

    health = pattern.fullmatch("/study_builder/_stcore/health")
    host_config = pattern.fullmatch("/settings/_stcore/host-config")
    favicon = pattern.fullmatch("/comparison/favicon.png")

    assert health is not None
    assert host_config is not None
    assert favicon is not None
    assert health.group(1) == "_stcore/health"
    assert host_config.group(1) == "_stcore/host-config"
    assert favicon.group(1) == "favicon.png"


def test_caddy_rewrite_does_not_match_normal_page_routes() -> None:
    pattern = _streamlit_nested_pattern()

    assert pattern.fullmatch("/study_builder") is None
    assert pattern.fullmatch("/settings") is None
    assert pattern.fullmatch("/") is None