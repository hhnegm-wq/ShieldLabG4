from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "ui" / "pages"

FORBIDDEN_PAGE_PATTERNS = [
    (
        "direct unsafe_allow_html in page module",
        re.compile(r"unsafe_allow_html\s*=\s*True"),
    ),
    (
        "raw shell HTML emitted directly from page module",
        re.compile(r"<(div|section|a)\s+class=", re.IGNORECASE),
    ),
]


def _page_files() -> list[Path]:
    return sorted(path for path in PAGES_DIR.glob("*.py") if path.is_file())


class TestUiShellContract:
    def test_page_modules_do_not_bypass_shared_shell_primitives(self):
        violations: list[str] = []

        for path in _page_files():
            content = path.read_text(encoding="utf-8")
            rel = path.relative_to(ROOT)
            for label, pattern in FORBIDDEN_PAGE_PATTERNS:
                for match in pattern.finditer(content):
                    line_no = content.count("\n", 0, match.start()) + 1
                    violations.append(f"{rel}:{line_no}: {label}")

        assert not violations, "UI shell contract violations found:\n" + "\n".join(violations)
