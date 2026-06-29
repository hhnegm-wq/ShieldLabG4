"""Strict science-readiness gate.

Wraps ``shieldlab.io.release_gate`` with the *publication* profile and adds
two extra checks:

  1. ``science_gate`` field in the latest validation report is "pass".
  2. Reference-provenance scan (``tools/reference_provenance_check.py``)
     finds zero placeholders.

Exit code 0 → all green; 1 → at least one check failed.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "validation" / "release_validation_report_latest.json"


def main() -> int:
    failures: list[str] = []

    if not REPORT.exists():
        print(f"science_gate: FAIL — report not found at {REPORT}")
        return 1

    report = json.loads(REPORT.read_text(encoding="utf-8"))
    summary = report.get("summary", {})
    science = summary.get("science_gate")
    if science != "pass":
        failures.append(
            f"science_gate field in report is {science!r}; ready_for_submission="
            f"{summary.get('q1_readiness', {}).get('ready_for_submission')}"
        )

    prov = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "reference_provenance_check.py")],
        capture_output=True,
        text=True,
    )
    if prov.returncode != 0:
        failures.append("reference_provenance_check failed:\n" + prov.stdout)

    if failures:
        print("science_gate: FAIL")
        for f in failures:
            print(f"- {f}")
        return 1
    print("science_gate: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
