"""Figure-quality audit.

Verifies that every PNG figure shipped under ``docs/`` and ``build/results/``
meets minimum publication standards:

    * ≥ 200 DPI
    * Width ≥ 800 px AND height ≥ 600 px
    * Has an accompanying caption sidecar (``<figure>.caption.txt``) — or
      is whitelisted via ``--allow``.

Exit code 0 = pass, 1 = at least one failure.
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path


def _png_info(path: Path) -> tuple[int, int, float] | None:
    """Return (width_px, height_px, dpi) or None if unreadable."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    try:
        # IHDR is at offset 8: 4-byte length, 4-byte "IHDR", then 13-byte payload.
        width = struct.unpack(">I", data[16:20])[0]
        height = struct.unpack(">I", data[20:24])[0]
    except struct.error:
        return None
    dpi = 96.0
    # Look for pHYs chunk
    i = 8
    while i < len(data) - 8:
        try:
            length = struct.unpack(">I", data[i:i + 4])[0]
            chunk = data[i + 4:i + 8]
        except struct.error:
            break
        if chunk == b"pHYs":
            try:
                ppu_x = struct.unpack(">I", data[i + 8:i + 12])[0]
                unit = data[i + 16]
                if unit == 1:  # metres
                    dpi = ppu_x * 0.0254
            except (struct.error, IndexError):
                pass
            break
        i += 12 + length
    return width, height, dpi


import re as _re

# Pattern that flags UI pages with matplotlib but missing apply_journal_style.
_MATPLOTLIB_IMPORT_RE = _re.compile(r"^\s*(import matplotlib|from matplotlib)", _re.MULTILINE)
_APPLY_STYLE_RE       = _re.compile(r'apply_journal_style\s*\(.*shieldlab_web')
# Maximum line to search for the module-level apply_journal_style call.
_UI_PRESET_SCAN_LINES = 80


def _check_ui_presets(ui_roots: list[str]) -> list[str]:
    """Scan UI page files for matplotlib imports without apply_journal_style.

    Any ``ui/pages/*.py`` that imports matplotlib must either:

    * Call ``apply_journal_style("shieldlab_web")`` at module level (first
      ``_UI_PRESET_SCAN_LINES`` lines), OR
    * Import ``apply_journal_style`` from ``shieldlab.viz.style`` anywhere in
      the file (indicating the page manages chart style at render time).
    """
    failures: list[str] = []
    for root in ui_roots:
        rp = Path(root)
        if not rp.exists():
            continue
        for py in sorted(rp.rglob("*.py")):
            try:
                src = py.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not _MATPLOTLIB_IMPORT_RE.search(src):
                continue  # no matplotlib — nothing to enforce
            # Accept if apply_journal_style is imported anywhere in the file
            if "apply_journal_style" in src:
                continue
            # Fallback: check module-level call in first N lines
            head = "\n".join(src.splitlines()[:_UI_PRESET_SCAN_LINES])
            if not _APPLY_STYLE_RE.search(head):
                failures.append(
                    f"{py}: imports matplotlib but missing "
                    f'apply_journal_style("shieldlab_web") '
                    f"in first {_UI_PRESET_SCAN_LINES} lines"
                )
    return failures


# Patterns that indicate interactive / style-drift usage that must not appear
# in shippable source code (python/shieldlab and ui/).  plt.show() blocks
# interactive execution in a server; plt.rcParams direct edits bypass the
# style module.  Both are flagged.
_BANNED_SOURCE_PATTERNS: list[tuple[str, str]] = [
    (r"\bplt\.show\s*\(", "plt.show() call — use savefig / return fig instead"),
    (
        r"plt\.rcParams\s*\[.+\]\s*=",
        "plt.rcParams direct write — use shieldlab.viz.style.apply_journal_style() instead",
    ),
    (
        r"matplotlib\.rcParams\s*\[.+\]\s*=",
        "matplotlib.rcParams direct write — use shieldlab.viz.style.apply_journal_style() instead",
    ),
]


def _check_source_roots(src_roots: list[str]) -> list[str]:
    """Scan Python source files under *src_roots* for banned matplotlib patterns."""
    failures: list[str] = []
    compiled = [(_re.compile(pat), msg) for pat, msg in _BANNED_SOURCE_PATTERNS]
    for root in src_roots:
        rp = Path(root)
        if not rp.exists():
            continue
        for py in rp.rglob("*.py"):
            try:
                lines = py.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for lineno, line in enumerate(lines, start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue   # skip pure-comment lines
                for pattern, msg in compiled:
                    if pattern.search(line):
                        failures.append(f"{py}:{lineno}: {msg}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit shipped figures for DPI/size/caption and source for style drift."
    )
    parser.add_argument("--roots", nargs="+", default=["docs", "build/results"])
    parser.add_argument("--min-dpi", type=float, default=200.0)
    parser.add_argument("--min-width", type=int, default=800)
    parser.add_argument("--min-height", type=int, default=600)
    parser.add_argument("--allow", nargs="*", default=[], help="glob patterns to skip")
    parser.add_argument(
        "--src-roots",
        nargs="*",
        default=["python/shieldlab", "ui"],
        help="Python source roots to scan for plt.show / rcParams drift (default: python/shieldlab ui)",
    )
    parser.add_argument(
        "--src-only",
        action="store_true",
        help="Run source-style lint only; skip all PNG quality checks (equivalent to --roots with no paths).",
    )
    parser.add_argument(
        "--no-source-lint",
        action="store_true",
        help="Skip the source-style lint (plt.show / rcParams check).",
    )
    parser.add_argument(
        "--check-ui-presets",
        action="store_true",
        help=(
            "Enforce that every UI page that imports matplotlib calls "
            'apply_journal_style("shieldlab_web") at module level.'
        ),
    )
    parser.add_argument(
        "--ui-src",
        nargs="*",
        default=["ui/pages"],
        help="UI page directories to scan for the --check-ui-presets check (default: ui/pages).",
    )
    args = parser.parse_args()

    failures: list[str] = []

    # ── PNG quality checks ────────────────────────────────────────────────────
    if not args.src_only:
        for root in args.roots:
            rp = Path(root)
            if not rp.exists():
                continue
            for png in rp.rglob("*.png"):
                if any(png.match(p) for p in args.allow):
                    continue
                info = _png_info(png)
                if info is None:
                    failures.append(f"{png}: unreadable PNG")
                    continue
                w, h, dpi = info
                if w < args.min_width or h < args.min_height:
                    failures.append(f"{png}: {w}x{h} below {args.min_width}x{args.min_height}")
                if dpi < args.min_dpi:
                    failures.append(f"{png}: dpi={dpi:.1f} below {args.min_dpi}")
                caption = png.with_suffix(".caption.txt")
                if not caption.exists():
                    failures.append(f"{png}: missing caption sidecar {caption.name}")

    # ── Source style-drift lint ───────────────────────────────────────────────
    if not args.no_source_lint:
        failures.extend(_check_source_roots(args.src_roots))

    # ── UI preset enforcement ─────────────────────────────────────────────────
    if args.check_ui_presets:
        failures.extend(_check_ui_presets(args.ui_src))

    if failures:
        print("figure_audit: FAIL")
        for f in failures[:200]:
            print(f"- {f}")
        if len(failures) > 200:
            print(f"... and {len(failures) - 200} more")
        return 1
    print("figure_audit: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
