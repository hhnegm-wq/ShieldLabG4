"""UI page scaffold compliance checker.

Validates that every page under a given directory follows the ShieldLab G4
page structure contract:

1. Bootstrap pattern present — must import and call ``ensure_project_paths``
   from ``bootstrap``.
2. No direct raw-HTML injection of design-system markup at page level —
   ``st.markdown`` calls with ``unsafe_allow_html=True`` that emit
   ``shieldlab-`` CSS classes are only permitted in ``components/``.
3. No direct ``plt.rcParams`` or ``matplotlib.rcParams`` mutation — must use
   ``apply_journal_style`` instead (enforced separately by ``figure_audit``).

Exit code 0 = all pages compliant, 1 = at least one violation.

Typical invocation in CI:
    python tools/page_scaffold_check.py ui/pages
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ── Checks ────────────────────────────────────────────────────────────────────

_BOOTSTRAP_IMPORT_RE = re.compile(r"from bootstrap import ensure_project_paths")
_BOOTSTRAP_CALL_RE   = re.compile(r"ensure_project_paths\s*\(\s*\)")

# Detects st.markdown(..., unsafe_allow_html=True) that injects shieldlab CSS
# class markup directly from a page file.  This pattern is only allowed in
# components/.  Pages must delegate HTML rendering to component helpers.
_RAW_SHIELDLAB_HTML_RE = re.compile(
    r'st\.markdown\s*\([^)]*shieldlab-[a-z]',
    re.DOTALL,
)


def _check_page(path: Path) -> list[str]:
    """Return a list of violation strings for *path*, or empty list if clean."""
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: unreadable — {exc}"]

    violations: list[str] = []

    # 1. Bootstrap pattern
    has_import = bool(_BOOTSTRAP_IMPORT_RE.search(src))
    has_call   = bool(_BOOTSTRAP_CALL_RE.search(src))
    if not has_import:
        violations.append(
            f"{path}: missing 'from bootstrap import ensure_project_paths'"
        )
    if not has_call:
        violations.append(
            f"{path}: missing 'ensure_project_paths()' call"
        )

    # 2. Raw shieldlab HTML injection
    for m in _RAW_SHIELDLAB_HTML_RE.finditer(src):
        # Get the line number
        lineno = src[:m.start()].count("\n") + 1
        violations.append(
            f"{path}:{lineno}: raw st.markdown with shieldlab- class — "
            "delegate to a component helper instead"
        )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check UI pages comply with the ShieldLab G4 scaffold contract."
    )
    parser.add_argument(
        "page_dirs",
        nargs="*",
        default=["ui/pages"],
        help="Directories to scan for page files (default: ui/pages).",
    )
    parser.add_argument(
        "--glob",
        default="*.py",
        help="File glob pattern within each directory (default: *.py).",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=["__init__.py"],
        help="File names to exclude (default: __init__.py).",
    )
    args = parser.parse_args()

    all_failures: list[str] = []

    for page_dir in args.page_dirs:
        dp = Path(page_dir)
        if not dp.exists():
            print(f"page_scaffold_check: WARNING — directory not found: {dp}")
            continue
        py_files = sorted(dp.rglob(args.glob))
        for py in py_files:
            if py.name in args.exclude:
                continue
            all_failures.extend(_check_page(py))

    if all_failures:
        print("page_scaffold_check: FAIL")
        for f in all_failures:
            print(f"  - {f}")
        return 1

    print("page_scaffold_check: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
