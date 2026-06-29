from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "ui" / "pages"

FORBIDDEN_PAGE_PATTERNS = [
    (
        "page-local figure finish helper",
        re.compile(r"def\s+_finish_fig\s*\("),
    ),
]


def _page_files() -> list[Path]:
    return sorted(path for path in PAGES_DIR.glob("*.py") if path.is_file())


class TestVisualStyleContract:
    def test_page_modules_do_not_define_local_figure_finish_helpers(self):
        violations: list[str] = []

        for path in _page_files():
            content = path.read_text(encoding="utf-8")
            rel = path.relative_to(ROOT)
            for label, pattern in FORBIDDEN_PAGE_PATTERNS:
                for match in pattern.finditer(content):
                    line_no = content.count("\n", 0, match.start()) + 1
                    violations.append(f"{rel}:{line_no}: {label}")

        assert not violations, "Visualization style contract violations found:\n" + "\n".join(violations)

    def test_ui_pages_only_use_approved_journal_style_calls(self):
        violations: list[str] = []
        allowed_calls = {
            'apply_journal_style("shieldlab_web")',
            "apply_journal_style(journal_preset)",
        }

        for path in _page_files():
            content = path.read_text(encoding="utf-8")
            rel = path.relative_to(ROOT)
            for match in re.finditer(r"apply_journal_style\([^\n]+\)", content):
                call = match.group(0).strip()
                if call not in allowed_calls:
                    line_no = content.count("\n", 0, match.start()) + 1
                    violations.append(f"{rel}:{line_no}: non-approved journal style call '{call}'")

        assert not violations, "Visualization preset policy violations found:\n" + "\n".join(violations)