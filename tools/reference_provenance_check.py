"""Reference-provenance CI gate.

Walks ``build/results/`` and ``data/references/`` looking for any reference CSV
column or sidecar value that contains a placeholder / banned token. Used by CI
to fail a release that ships unsourced reference data.

Exit codes:
    0  no placeholders found
    1  placeholders found (details printed to stdout)
    2  invocation error
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PLACEHOLDER_TOKENS = (
    "example_baseline_replace_with_xcom_or_paper",
    "placeholder",
    "tbd",
    "todo",
    "fixme",
    "xxx_replace",
)


def _scan_text(path: Path) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                low = line.lower()
                for tok in PLACEHOLDER_TOKENS:
                    if tok in low:
                        hits.append((lineno, line.rstrip()))
                        break
    except OSError:
        pass
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail when reference datasets contain placeholders.")
    parser.add_argument(
        "--roots",
        nargs="+",
        default=["build/results", "data/references"],
        help="Directories to scan",
    )
    parser.add_argument(
        "--patterns",
        nargs="+",
        default=["*.csv", "*reference*.json", "*.ref.json"],
        help="File globs to scan",
    )
    args = parser.parse_args()

    findings: list[tuple[Path, int, str]] = []
    for root in args.roots:
        rp = Path(root)
        if not rp.exists():
            continue
        for pattern in args.patterns:
            for f in rp.rglob(pattern):
                for lineno, line in _scan_text(f):
                    findings.append((f, lineno, line))

    if not findings:
        print("Reference provenance check: PASS")
        return 0

    print("Reference provenance check: FAIL")
    print(f"Found {len(findings)} placeholder occurrences:")
    for f, lineno, line in findings[:200]:
        print(f"  {f}:{lineno}: {line[:160]}")
    if len(findings) > 200:
        print(f"  ... and {len(findings) - 200} more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
