"""Lightweight requirements -> code -> test traceability matrix.

Scans the repository for ``@requirement(REQ-xxx)`` markers in source
comments / docstrings and emits a Markdown matrix in
``docs/traceability_matrix.md``.

Marker syntax (free-form, anywhere in the file):
    # @requirement(REQ-PHY-001) Per-detector dose tally
    /* @requirement(REQ-SE-014) MT-safe RunAction merging */

This is intentionally simple — the goal is to make traceability cheap
enough to keep current.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

PATTERN = re.compile(r"@requirement\((REQ-[A-Z]+-\d+)\)\s*([^\n\r*/]*)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--out", default="docs/traceability_matrix.md"
    )
    parser.add_argument(
        "--exts",
        nargs="+",
        default=[".py", ".cc", ".cpp", ".hh", ".h"],
    )
    args = parser.parse_args()

    root = Path(args.root)
    findings: dict[str, list[tuple[Path, int, str]]] = defaultdict(list)
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in args.exts:
            continue
        if any(part in {"build", "backups", "__pycache__", ".git", ".venv"} for part in p.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in PATTERN.finditer(text):
            req = m.group(1)
            note = m.group(2).strip()
            line_no = text[: m.start()].count("\n") + 1
            rel = p.relative_to(root) if p.is_relative_to(root) else p
            findings[req].append((rel, line_no, note))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = ["# Traceability Matrix", "", "Auto-generated. Do not edit by hand.", ""]
    if not findings:
        lines.append("_No `@requirement(REQ-...)` markers found yet._")
    else:
        lines.append("| Requirement | File | Line | Note |")
        lines.append("|---|---|---|---|")
        for req in sorted(findings):
            for path, line_no, note in findings[req]:
                lines.append(f"| {req} | `{path}` | {line_no} | {note} |")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"traceability: wrote {out_path} ({len(findings)} requirements)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
