"""Verify Paper 3 manuscript v08 structure, content, and completeness."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANUSCRIPT = ROOT / "docs/validation/paper3_nanogeant4/manuscript_nanogeant4_v08.md"

ERRORS = []


def check(condition: bool, msg: str) -> None:
    if not condition:
        ERRORS.append(msg)


def main() -> int:
    if not MANUSCRIPT.exists():
        print(f"ERROR: manuscript not found at {MANUSCRIPT}")
        return 1

    text = MANUSCRIPT.read_text(encoding="utf-8")

    # ── Version tag ─────────────────────────────────────────────────────────
    check("v08" in text, "Manuscript version tag 'v08' not found")

    # ── Abstract checks ──────────────────────────────────────────────────────
    abstract_m = re.search(r"## Abstract\s+(.*?)(?=\n## |\n---)", text, re.DOTALL)
    check(abstract_m is not None, "Abstract section not found")
    if abstract_m:
        abstract = abstract_m.group(1)
        word_count = len(abstract.split())
        check(word_count >= 150, f"Abstract too short: {word_count} words (expect ≥ 150)")
        check("Bi" in abstract or "Bi₂O₃" in abstract, "Abstract missing Bi₂O₃ / Bi₂O₃ mention")
        check("WO" in abstract or "WO₃" in abstract, "Abstract missing WO₃ mention")
        check("0.189" in abstract, "Abstract missing φ=0.189")
        check("K-edge" in abstract or "K-edge" in abstract, "Abstract missing K-edge mention")
        check("±1%" in abstract or "1%" in abstract, "Abstract missing ±1% accuracy claim")

    # ── Keywords ────────────────────────────────────────────────────────────
    check("Keywords" in text, "Keywords section not found")
    keyword_count = len([k for k in text.split("·") if k.strip()]) - 1
    check(keyword_count >= 8, f"Fewer than 8 keywords (found ~{keyword_count})")

    # ── WO₃ / WO3 content ───────────────────────────────────────────────────
    check("WO₃" in text or "WO3" in text, "No WO₃/WO3 content found in manuscript")
    check("W K-edge" in text or "W\\ K-edge" in text, "W K-edge not mentioned in manuscript")
    check("63.7" in text or "63.72" in text, "WO₃ weight fraction (63.7 wt%) not found")
    check("69.5" in text, "W K-edge energy (69.5 keV) not found")

    # ── Bi₂O₃ content preserved ─────────────────────────────────────────────
    check("Bi₂O₃" in text or "Bi2O3" in text, "Bi₂O₃ content missing")
    check("90.5" in text, "Bi K-edge energy (90.5 keV) not found")
    check("68.6" in text, "Bi₂O₃ weight fraction (68.6 wt%) not found")

    # ── Contribution 4 (cross-material) ─────────────────────────────────────
    check("cross-material" in text.lower() or "cross material" in text.lower(),
          "Cross-material benchmark contribution not found")

    # ── Sections ────────────────────────────────────────────────────────────
    required_sections = [
        "## 1. Introduction",
        "## 2. Theoretical Basis",
        "## 3. Geant4 Modelling Regimes",
        "## 4. Benchmark Protocol",
        "## 5. Results",
        "## 6. Discussion",
        "## 7. Conclusions",
        "## 8. Limitations",
        "## 9. Reproducibility",
        "## 10. References",
    ]
    for sec in required_sections:
        check(sec in text, f"Section '{sec}' not found")

    # ── New sections (v08) ───────────────────────────────────────────────────
    check("5.5" in text and "WO" in text, "§5.5 HDPE/WO₃ section not found")
    check("5.6" in text and "Cross-Material" in text or "5.6" in text and "cross-material" in text.lower(),
          "§5.6 cross-material section not found")
    check("6.4" in text, "§6.4 cross-material generalisability section not found")

    # ── Tables ──────────────────────────────────────────────────────────────
    for tbl in ["Table 1.", "Table 1b.", "Table 1c.", "Table 2.", "Table 3."]:
        check(tbl in text, f"{tbl} not found in manuscript")

    # ── Figures ─────────────────────────────────────────────────────────────
    for fig_n in range(1, 7):
        check(f"Figure {fig_n}" in text or f"fig{fig_n}" in text.lower(),
              f"Figure {fig_n} not referenced in manuscript")

    # ── Dual-validation figure (Fig 2) ──────────────────────────────────────
    check("dual_validation" in text or "dual validation" in text.lower() or
          "two-panel" in text.lower() or "two panel" in text.lower() or
          "paper3_fig2_dual_validation" in text,
          "Dual validation figure (Fig 2) reference not found")

    # ── K-edge comparison figure (Fig 6) ────────────────────────────────────
    check("paper3_fig6_kedge_comparison" in text or "kedge_comparison" in text or
          "K-edge comparison" in text,
          "K-edge comparison figure (Fig 6) not found in manuscript")

    # ── Conclusions ─────────────────────────────────────────────────────────
    check("Two-material" in text or "two-material" in text,
          "Conclusion 5 (two-material generalisation) not found")

    # ── Limitations: single-material limitation removed ──────────────────────
    check("Single material composition" not in text,
          "Old 'Single material composition' limitation still present — should be removed")

    # ── References ──────────────────────────────────────────────────────────
    for ref_n in range(1, 12):
        check(f"\n{ref_n}. " in text, f"Reference [{ref_n}] not found in references section")

    # ── Print results ────────────────────────────────────────────────────────
    if ERRORS:
        print(f"FAIL — {len(ERRORS)} check(s) failed:")
        for e in ERRORS:
            print(f"  ✗ {e}")
        return 1
    else:
        print(f"PASS — all checks passed for {MANUSCRIPT.name}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
