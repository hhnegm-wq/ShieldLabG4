from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = REPO_ROOT / "docs" / "validation" / "paper3_nanogeant4" / "manuscript_nanogeant4_v06.md"
EXPECTED_FILENAME = "manuscript_nanogeant4_v06.md"

REQUIRED_PHRASES = {
    "version": "**Manuscript version:** v06",
    "corresponding_author": "**Corresponding author:** hhnegm@ju.edu.sa",
    "abstract_regime_c": "explicit spheres in a 250 nm RVE using `G4MultiUnion`",
    "beam_method": "Regime C uses a distributed beam sampling $(Y,Z) \\sim \\mathcal{U}[-L/2, +L/2]^2$ per event",
    "multiunion_note": "G4MultiUnion::Voxelize()",
    "limitations_header": "**RVE size selection.**",
    "funding": "**Funding statement:** no external funding was received for this work.",
    "conflict": "**Conflict of interest statement:** the author declares no conflict of interest.",
    "figure_1_ref": "Figure 1 summarises the three modelling regimes",
    "figure_5_ref": "Figure 5 overlays the regime A(phi0p189) $(\\mu/\\rho)$ data (Table 1b)",
}

FORBIDDEN_PHRASES = [
    "AFFILIATION REQUIRED",
    "[email]",
    "[To be added",
    "DO NOT SUBMIT WITH PLACEHOLDER",
    "# Appendix A",
    "Implementation Plan",
    "In progress — simulation running",
    "Pending — to start after regime B completes",
    "Figure F-cross",
]

EXPECTED_FIGURES = [
    REPO_ROOT / "results" / "paper3" / "figures" / "paper3_fig1_regime_map.png",
    REPO_ROOT / "results" / "paper3" / "figures" / "paper3_fig2_regime_a_validation.png",
    REPO_ROOT / "results" / "paper3" / "figures" / "paper3_fig3_buildup_and_spectrum.png",
    REPO_ROOT / "results" / "paper3" / "figures" / "paper3_fig4_multiunion_scalability.png",
    REPO_ROOT / "results" / "paper3" / "figures" / "paper3_fig5_cross_regime_mac.png",
]


def extract_abstract(text: str) -> str:
    match = re.search(r"## Abstract\s+(.*?)\n\*\*Keywords:\*\*", text, re.DOTALL)
    if not match:
        raise ValueError("Could not extract Abstract section")
    return match.group(1).strip()


def extract_keywords(text: str) -> list[str]:
    match = re.search(r"\*\*Keywords:\*\*\s*(.+)", text)
    if not match:
        raise ValueError("Could not extract Keywords line")
    return [part.strip() for part in match.group(1).split("·") if part.strip()]


WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[./+-][A-Za-z0-9]+)*")


def abstract_word_count(abstract: str) -> int:
    cleaned = re.sub(r"`[^`]*`", " ", abstract)
    cleaned = re.sub(r"\$[^$]*\$", " ", cleaned)
    cleaned = re.sub(r"[*_#\[\]()]", " ", cleaned)
    return len(WORD_RE.findall(cleaned))


PARAGRAPH_RE = re.compile(r"\n\s*\n")


def main() -> int:
    failures: list[str] = []

    if not MANUSCRIPT.exists():
        failures.append(f"Missing manuscript: {MANUSCRIPT}")
    if MANUSCRIPT.name != EXPECTED_FILENAME:
        failures.append(f"Unexpected manuscript filename: {MANUSCRIPT.name}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    text = MANUSCRIPT.read_text(encoding="utf-8")

    for label, phrase in REQUIRED_PHRASES.items():
        if phrase not in text:
            failures.append(f"Missing required phrase ({label}): {phrase}")

    for phrase in FORBIDDEN_PHRASES:
        if phrase in text:
            failures.append(f"Forbidden phrase still present: {phrase}")

    for figure_path in EXPECTED_FIGURES:
        if not figure_path.exists():
            failures.append(f"Missing expected figure: {figure_path}")

    for idx in range(1, 6):
        if f"Figure {idx}." not in text:
            failures.append(f"Missing figure caption/reference for Figure {idx}")

    try:
        abstract = extract_abstract(text)
    except ValueError as exc:
        failures.append(str(exc))
        abstract = ""

    try:
        keywords = extract_keywords(text)
    except ValueError as exc:
        failures.append(str(exc))
        keywords = []

    if abstract:
        word_count = abstract_word_count(abstract)
        paragraph_count = len([part for part in PARAGRAPH_RE.split(abstract) if part.strip()])
        if word_count > 250:
            failures.append(f"Abstract too long: {word_count} words")
        if paragraph_count < 4:
            failures.append(f"Abstract is not split into 4 paragraphs: found {paragraph_count}")
    else:
        word_count = -1
        paragraph_count = -1

    if keywords and not (5 <= len(keywords) <= 8):
        failures.append(f"Keyword count outside 5-8 range: {len(keywords)}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: paper3 manuscript v06 verification succeeded")
    print(f"Abstract words: {word_count}")
    print(f"Abstract paragraphs: {paragraph_count}")
    print(f"Keywords: {len(keywords)}")
    print(f"Figures present: {len(EXPECTED_FIGURES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
