from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "ui" / "pages"

REQUIRED_PAGE_PATTERNS = [
    (
        "shared page hero",
        re.compile(r"\brender_page_hero\s*\("),
    ),
    (
        "shared breadcrumb",
        re.compile(r"\b\w*render_breadcrumb\w*\s*\("),
    ),
]


def _page_files() -> list[Path]:
    return sorted(
        path
        for path in PAGES_DIR.glob("*.py")
        if path.is_file() and not path.name.startswith("_")
    )


class TestPageScaffoldContract:
    def test_page_modules_use_standard_scaffold(self) -> None:
        violations: list[str] = []

        for path in _page_files():
            content = path.read_text(encoding="utf-8")
            rel = path.relative_to(ROOT)
            for label, pattern in REQUIRED_PAGE_PATTERNS:
                if not pattern.search(content):
                    violations.append(f"{rel}: missing {label}")

        assert not violations, "Page scaffold contract violations found:\n" + "\n".join(violations)