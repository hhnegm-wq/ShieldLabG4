from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "ui" / "pages"


def _page_files() -> list[Path]:
    return sorted(
        path
        for path in PAGES_DIR.glob("*.py")
        if path.is_file() and not path.name.startswith("_")
    )


def test_pages_use_inline_bootstrap_pattern() -> None:
    """Every page must carry the standard inline path-bootstrap block.

    The inline pattern is required because Streamlit executes pages as
    top-level scripts; sys.path must be configured before any project
    imports, so a shared helper import cannot substitute for it.
    """
    violations: list[str] = []

    for path in _page_files():
        content = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        if "_UI_DIR = Path(__file__).resolve().parent.parent" not in content:
            violations.append(f"{rel}: missing _UI_DIR bootstrap line")
        if "from bootstrap import ensure_project_paths" not in content:
            violations.append(f"{rel}: missing ensure_project_paths import")
        if "ensure_project_paths()" not in content:
            violations.append(f"{rel}: missing ensure_project_paths() call")
        if "from _page_init import bootstrap_page" in content:
            violations.append(f"{rel}: still uses removed _page_init helper")

    assert not violations, "Page bootstrap contract violations found:\n" + "\n".join(violations)