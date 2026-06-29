from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = REPO_ROOT / "docs" / "validation" / "paper3_nanogeant4" / "manuscript_nanogeant4_v10.md"
FIGURE_SCRIPT = REPO_ROOT / "scripts" / "generate_paper3_v10_figures.py"
FIGURE_DIR = REPO_ROOT / "results" / "paper3" / "figures" / "v10"

WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[./+-][A-Za-z0-9]+)*")
FIGURE_LINK_RE = re.compile(r"!\[[^\]]*Figure\s+([1-5])\.[^\]]*\]\(([^)]+)\)")

EXPECTED_FIGURE_STEMS = [
    "paper3_v10_fig1_six_material_xcom_validation",
    "paper3_v10_fig2_kedge_landscape_delta_heatmap",
    "paper3_v10_fig3_cross_regime_ratio_heatmaps",
    "paper3_v10_fig4_explicit_rve_agreement",
    "paper3_v10_fig5_modelling_workflow",
]

REQUIRED_SECTIONS = [
    "## 1. Introduction",
    "## 2. Theoretical Basis",
    "## 3. Geant4 Modelling Regimes",
    "## 4. Benchmark Protocol",
    "## 5. Results",
    "## 6. Discussion",
    "## 7. Conclusions",
    "## 8. Limitations and Validity Scope",
    "## 9. Reproducibility, Code Availability, and Ethics",
    "## 10. References",
]

REQUIRED_PHRASES = [
    "**Manuscript version:** v10",
    "2026-05-20",
    "Study-to-result provenance",
    "Non-composition-equivalent stress test",
    "excluded from H1 pass/fail",
    "The recommended workflow is Regime A",
    "G4PVParameterised",
    "G4MultiUnion",
    "negative-control stress test",
]

ABSTRACT_PHRASES = [
    "0.339\u20130.793%",
    "0.967\u20132.933%",
    "\u00b13% H1 gate",
    "negative-control stress test",
]

FORBIDDEN_PHRASES = [
    "TODO",
    "TBD",
    "[X]",
    "[INSERT]",
    "[REF",
    "figures/v09",
    "paper3_v09_fig",
    "generate_paper3_v09",
    "orange squares",
    "grey band",
    "first time",
    "unprecedented",
    "novel absorber",
    "best shielding material",
]

REQUIRED_STYLE_CONSTANTS = ["#0000FF", "#FF0000", "#00FF00", "#000000"]
OLD_PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]


def abstract_word_count(abstract: str) -> int:
    cleaned = re.sub(r"`[^`]*`", " ", abstract)
    cleaned = re.sub(r"\$[^$]*\$", " ", cleaned)
    cleaned = re.sub(r"[*_#\[\](){}]", " ", cleaned)
    return len(WORD_RE.findall(cleaned))


def markdown_target_to_path(target: str) -> Path:
    clean_target = target.split("{")[0].strip()
    return (MANUSCRIPT.parent / clean_target).resolve()


def extract_abstract(text: str) -> str:
    match = re.search(r"## Abstract\s+(.*?)\n\*\*Keywords:\*\*", text, re.DOTALL)
    if not match:
        raise ValueError("Abstract section not found")
    return match.group(1).strip()


def main() -> int:
    failures: list[str] = []

    if not MANUSCRIPT.exists():
        failures.append(f"Missing manuscript: {MANUSCRIPT}")
    if not FIGURE_SCRIPT.exists():
        failures.append(f"Missing figure script: {FIGURE_SCRIPT}")
    if not FIGURE_DIR.exists():
        failures.append(f"Missing figure directory: {FIGURE_DIR}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    text = MANUSCRIPT.read_text(encoding="utf-8")
    script_text = FIGURE_SCRIPT.read_text(encoding="utf-8")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            failures.append(f"Missing section: {section}")

    for phrase in REQUIRED_PHRASES:
        if phrase not in text:
            failures.append(f"Missing required phrase: {phrase}")

    for phrase in FORBIDDEN_PHRASES:
        if phrase.lower() in text.lower():
            failures.append(f"Forbidden phrase present: {phrase}")

    try:
        abstract = extract_abstract(text)
    except ValueError as error:
        failures.append(str(error))
        abstract = ""

    if abstract:
        word_count = abstract_word_count(abstract)
        paragraphs = [paragraph for paragraph in re.split(r"\n\s*\n", abstract) if paragraph.strip()]
        if not 200 <= word_count <= 250:
            failures.append(f"Abstract word count outside 200-250: {word_count}")
        if len(paragraphs) != 4:
            failures.append(f"Abstract paragraph count is not 4: {len(paragraphs)}")
        for phrase in ABSTRACT_PHRASES:
            if phrase not in abstract:
                failures.append(f"Abstract missing phrase: {phrase}")
    else:
        word_count = -1

    figure_links = FIGURE_LINK_RE.findall(text)
    if len(figure_links) != 5:
        failures.append(f"Expected 5 figure links, found {len(figure_links)}")
    linked_numbers = sorted(int(figure_number) for figure_number, _ in figure_links)
    if linked_numbers != [1, 2, 3, 4, 5]:
        failures.append(f"Unexpected figure numbers: {linked_numbers}")
    for figure_number, target in figure_links:
        figure_path = markdown_target_to_path(target)
        if not figure_path.exists():
            failures.append(f"Figure {figure_number} target missing: {figure_path}")
        if "figures/v10" not in target:
            failures.append(f"Figure {figure_number} does not use v10 path: {target}")

    for stem in EXPECTED_FIGURE_STEMS:
        for extension in ["png", "pdf", "svg"]:
            figure_file = FIGURE_DIR / f"{stem}.{extension}"
            if not figure_file.exists():
                failures.append(f"Missing figure artifact: {figure_file}")
    manifest = FIGURE_DIR / "paper3_v10_figure_manifest.json"
    if not manifest.exists():
        failures.append(f"Missing figure manifest: {manifest}")

    for constant in REQUIRED_STYLE_CONSTANTS:
        if constant not in script_text:
            failures.append(f"Missing style constant: {constant}")
    for old_color in OLD_PALETTE:
        if old_color in script_text:
            failures.append(f"Old palette color still present: {old_color}")
    if "dpi=300" not in script_text:
        failures.append("PNG save DPI is not locked to 300")

    for reference_number in range(1, 18):
        if f"\n{reference_number}. " not in text:
            failures.append(f"Missing reference entry: {reference_number}")

    results_without_captions = FIGURE_LINK_RE.sub("", text)
    for target in ["Figure 1", "Figure 2", "Figure 3A", "Figure 3B", "Figure 4", "Figure 5", "Table 1", "Table 2", "Table 3", "Table 4", "Table 5"]:
        if target not in results_without_captions:
            failures.append(f"Missing prose reference: {target}")

    if failures:
        print(f"FAIL: paper3 v10 verification found {len(failures)} issue(s)")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("PASS: paper3 v10 verification succeeded")
    print(f"Abstract words: {word_count}")
    print(f"Figure links: {len(figure_links)}")
    print(f"Figure artifacts: {len(EXPECTED_FIGURE_STEMS) * 3}")
    print("References: 17")
    return 0


if __name__ == "__main__":
    sys.exit(main())
