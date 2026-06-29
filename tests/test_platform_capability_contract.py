from __future__ import annotations

from pathlib import Path

from ui.components.platform_capabilities import PLATFORM_CAPABILITIES

ROOT = Path(__file__).resolve().parents[1]


def test_platform_capability_registry_covers_core_trust_areas() -> None:
    keys = {capability.key for capability in PLATFORM_CAPABILITIES}
    assert keys == {
        "security_controls",
        "validation_gates",
        "provenance_trail",
        "methods_evidence",
    }


def test_key_product_pages_render_platform_capability_grid() -> None:
    required_pages = [
        ROOT / "ui" / "pages" / "home.py",
        ROOT / "ui" / "pages" / "about.py",
        ROOT / "ui" / "pages" / "settings.py",
    ]

    for path in required_pages:
        content = path.read_text(encoding="utf-8")
        assert "render_platform_capability_grid(" in content, f"Missing platform capability surface in {path.relative_to(ROOT)}"