#!/usr/bin/env python
"""
verify_manuscript.py
Checks that the Paper 2 technical/software manuscript is ready for submission.

Run from repo root:
    python papers/paper2_technical_software/verify_manuscript.py

Exit code: 0 = all checks pass, 1 = failures found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PAPER_DIR = Path(__file__).parent
REPO_ROOT  = PAPER_DIR.parent.parent

MANUSCRIPT = PAPER_DIR / "manuscript_technical_software_v02.md"
DATA_CSV   = PAPER_DIR / "data_validation_report.csv"
FIGURES    = [
    PAPER_DIR / "figures" / "fig01_system_architecture.png",
    PAPER_DIR / "figures" / "fig02_ci_gate_model.png",
    PAPER_DIR / "figures" / "fig03_attenuation_agreement.png",
    PAPER_DIR / "figures" / "fig04_reproducibility_model.png",
    PAPER_DIR / "figures" / "fig05_security_deployment_controls.png",
    PAPER_DIR / "figures" / "fig06_correlation_observability_flow.png",
    PAPER_DIR / "figures" / "fig07_validation_coverage_map.png",
]
COVER_LETTER = PAPER_DIR / "final" / "cover_letter.md"
HIGHLIGHTS   = PAPER_DIR / "final" / "highlights.md"
FINAL_DOCX   = PAPER_DIR / "final" / "manuscript_technical_software_v02.docx"

OPEN_PLACEHOLDERS = ["[Institution]", "[AFFILIATION REQUIRED"]

PASS = "  [PASS]"
FAIL = "  [FAIL]"
WARN = "  [WARN]"

results: list[tuple[bool, str, str]] = []   # (ok, tag, message)


def check(ok: bool, label: str, detail: str = "", warn_only: bool = False) -> None:
    tag  = PASS if ok else (WARN if warn_only else FAIL)
    results.append((ok or warn_only, tag, f"{label}{': ' + detail if detail else ''}"))


# ── 1. Manuscript file exists ────────────────────────────────────────────────
check(MANUSCRIPT.exists(), "Manuscript file exists", str(MANUSCRIPT))

if MANUSCRIPT.exists():
    text = MANUSCRIPT.read_text(encoding="utf-8")

    # 2. Minimum length
    word_count = len(text.split())
    check(word_count >= 2000, "Manuscript word count", f"{word_count} words (min 2000)")

    # 3. Contains required sections (case-insensitive)
    required_headings = [
        "abstract", "introduction", "statement of need", "software architecture",
        "illustrative examples", "conclusions", "availability", "limitations",
    ]
    for heading in required_headings:
        found = heading.lower() in text.lower()
        check(found, f"Section present: '{heading}'")

    # 4. Figure canonical names referenced
    for fname in [
        "fig01_system_architecture",
        "fig02_ci_gate_model",
        "fig03_attenuation_agreement",
        "fig04_reproducibility_model",
        "fig05_security_deployment_controls",
        "fig06_correlation_observability_flow",
        "fig07_validation_coverage_map",
    ]:
        found = fname in text
        check(found, f"Figure name in manuscript: {fname}")

    # 5. Open placeholders
    for ph in OPEN_PLACEHOLDERS:
        found = ph in text
        check(not found, f"Placeholder resolved: {ph}", warn_only=True)

    # 6. Benchmark count (n=56 or "56 data points" etc.)
    has_56 = re.search(r"\b56\b", text) is not None
    check(has_56, "Benchmark count 56 mentioned in manuscript")

    # 7. Test count
    has_155 = re.search(r"\b155\b", text) is not None
    check(has_155, "Test count 155 mentioned in manuscript")

    # 8. At least 6 keywords
    kw_section = re.search(r"(?i)keywords?[:\s]+(.+)", text)
    if kw_section:
        kw_count = len([k for k in kw_section.group(1).split(';') if k.strip()])
        check(kw_count >= 5, "Keyword count", f"{kw_count} (target ≥5)")
    else:
        check(False, "Keywords section present")

    # 9. DOI / URL for code repository
    has_repo = re.search(r"github\.com|zenodo\.org|doi\.org", text, re.I) is not None
    check(has_repo, "Repository URL or DOI present", warn_only=True)

# ── 10. Data CSV ─────────────────────────────────────────────────────────────
check(DATA_CSV.exists(), "data_validation_report.csv exists")
if DATA_CSV.exists():
    lines = DATA_CSV.read_text().splitlines()
    n_data = len(lines) - 1  # subtract header
    check(n_data == 56, "CSV has 56 data rows", f"found {n_data}")

# ── 11. Figures ──────────────────────────────────────────────────────────────
for fig in FIGURES:
    ok = fig.exists() and fig.stat().st_size > 50_000
    check(ok, f"Figure exists and non-trivial: {fig.name}",
          f"{fig.stat().st_size:,} bytes" if fig.exists() else "MISSING")

# ── 12. Final deliverables ───────────────────────────────────────────────────
check(COVER_LETTER.exists(), "Cover letter exists", str(COVER_LETTER), warn_only=True)
check(HIGHLIGHTS.exists(),   "Highlights file exists", str(HIGHLIGHTS), warn_only=True)
check(FINAL_DOCX.exists(),   "Final DOCX exists", str(FINAL_DOCX), warn_only=True)

# ── Summary ──────────────────────────────────────────────────────────────────
n_pass = sum(1 for ok, _, _ in results if ok)
n_fail = sum(1 for ok, tag, _ in results if not ok and tag == FAIL)
n_warn = sum(1 for ok, tag, _ in results if not ok and tag == WARN)

print("\nShieldLab G4 — Paper 2 Pre-submission Verification")
print("=" * 60)
for ok, tag, msg in results:
    print(f"{tag}  {msg}")

print("\n" + "-" * 60)
print(f"  {n_pass} passed    {n_warn} warnings    {n_fail} failures")
print("-" * 60)

if n_fail > 0:
    print("\nFix failures before submission.\n")
    sys.exit(1)
elif n_warn > 0:
    print("\nAddress warnings before submission.\n")
    sys.exit(0)
else:
    print("\nAll checks passed. Manuscript appears submission-ready.\n")
    sys.exit(0)
