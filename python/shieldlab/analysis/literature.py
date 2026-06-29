from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
FORMULA_PATTERN = re.compile(r"\b(?:[A-Z][a-z]?\d*(?:\.\d+)?){2,}\b")

SIMULATION_CODE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "geant4": ("geant4",),
    "mcnp": ("mcnp", "mcnpx", "mcnp-5"),
    "phits": ("phits",),
    "fluka": ("fluka",),
}

MATERIAL_TOKEN_BLOCKLIST = {
    "ABSTRACT",
    "ARTICLE",
    "ASCII",
    "CSDA",
    "DOI",
    "EBF",
    "EABF",
    "EDX",
    "FT",
    "FNRCS",
    "GEANT4",
    "HVL",
    "JEOL",
    "MCNP",
    "MCNPX",
    "MeV",
    "MFP",
    "ORIGINAL",
    "PAPER",
    "PHITS",
    "PSD",
    "RESEARCH",
    "TVL",
    "XCOM",
    "XRD",
}

RADIATION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "gamma": ("gamma-ray", "gamma ray", "γ-ray", "γ ray", "photon attenuation", "photon shielding"),
    "xray": ("x-ray", "x ray", "x-rays", "diagnostic radiology"),
    "neutron": ("neutron", "fast neutron", "removal cross-section", "removal cross section"),
    "beta": ("beta", "β"),
    "electron": ("electron", "electrons", "stopping power", "csda"),
    "proton": ("proton", "protons", "pstar"),
    "alpha": ("alpha", "α", "astar"),
    "ion": ("ion", "ions", "heavy ion", "charged particles"),
}

MATERIAL_CLASS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "glass": ("glass", "glasses", "tellurite", "borate", "phosphate", "germinate"),
    "nanocomposite": ("nanocomposite", "nanoparticle", "nano ", "intercalated"),
    "clay_composite": ("attapulgite", "clay"),
    "concrete": ("concrete",),
    "polymer": ("polymer", "thermoplastic", "polyethylene", "epoxy"),
    "metallic_glass": ("metallic glass", "heavy metallic glass", "alloy"),
    "ceramic": ("ceramic", "al2o3", "oxide"),
    "instrumentation": ("instrument", "x ray room", "diagnostic radiology", "multi-physics instrument"),
}

FIGURE_FAMILY_RULES: dict[str, tuple[str, ...]] = {
    "mac_energy": ("gamma", "xray"),
    "hvl_tvl_energy": ("gamma", "xray"),
    "transmission_thickness": ("gamma", "xray", "neutron"),
    "zeff_neff_energy": ("gamma", "xray"),
    "fnrcs": ("neutron",),
    "electron_stopping": ("electron", "beta"),
    "ion_stopping": ("proton", "alpha", "ion"),
    "mc_analytical_overlay": ("gamma", "xray", "neutron", "electron", "proton", "alpha", "ion"),
}


@dataclass(slots=True)
class PaperRecord:
    file_name: str
    title: str
    year: int | None
    doi: str | None
    materials: list[str]
    material_classes: list[str]
    radiation_types: list[str]
    figure_families: list[str]
    simulation_codes: list[str]
    abstract_snippet: str


def _read_pdf_text(path: Path, max_pages: int = 2) -> str:
    reader = PdfReader(str(path))
    snippets: list[str] = []
    for page in reader.pages[:max_pages]:
        text = page.extract_text() or ""
        if text:
            snippets.append(text)
    return "\n".join(snippets)


def _normalized(text: str) -> str:
    return " ".join(text.replace("\x00", " ").split())


def _clean_filename_title(path: Path) -> str:
    title = path.stem.replace("_", " ")
    title = re.sub(r"\s*Elsevier Enhanced Reader\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+", " ", title)
    return title.strip(" -_")


def _candidate_title(text: str, fallback: str) -> str:
    compact = _normalized(text)
    abstract_idx = compact.lower().find("abstract")
    head = compact[:abstract_idx] if abstract_idx > 0 else compact[:1200]
    title_match = re.search(
        r"(?:paper|article|original research article|research article)\s+(.+?)(?:\s+[A-Z][a-z]+\s+[A-Z]\.|\s+Abstract\b)",
        head,
        re.IGNORECASE,
    )
    if title_match:
        return title_match.group(1).strip(" .:-")

    bad_line_starts = (
        "contents lists available",
        "radiation physics and chemistry",
        "phys. scr.",
        "journal of",
        "vol.",
    )

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        lowered = line.lower()
        if len(line) < 25:
            continue
        if lowered.startswith(bad_line_starts):
            continue
        if any(token in lowered for token in ("doi", "received", "available online", "keywords", "abstract")):
            continue
        return re.sub(r"\s+", " ", line)
    return fallback


def _extract_focus_text(text: str, title: str) -> str:
    compact = _normalized(text)
    abstract_match = re.search(r"\babstract\b", compact, re.IGNORECASE)
    if abstract_match:
        abstract = compact[abstract_match.end(): abstract_match.end() + 1800]
        return f"{title}. {abstract}"
    return f"{title}. {compact[:1800]}"


def _extract_year(text: str) -> int | None:
    years = [int(match.group(0)) for match in YEAR_PATTERN.finditer(text)]
    if not years:
        return None
    years = [year for year in years if 1990 <= year <= 2035]
    return max(years) if years else None


def _extract_materials(text: str) -> list[str]:
    formulas = []
    for match in FORMULA_PATTERN.finditer(text):
        token = match.group(0)
        if len(token) > 24:
            continue
        if token.upper() in MATERIAL_TOKEN_BLOCKLIST:
            continue
        if token.lower().startswith("doi"):
            continue
        if token.isupper() and not any(ch.isdigit() for ch in token):
            continue
        formulas.append(token)
    counts = Counter(formulas)
    return [formula for formula, _ in counts.most_common(10)]


def _detect_categories(text: str, mapping: dict[str, tuple[str, ...]]) -> list[str]:
    lowered = text.lower()
    found = []
    for label, keywords in mapping.items():
        if any(keyword in lowered for keyword in keywords):
            found.append(label)
    return found


def _infer_figure_families(radiation_types: Iterable[str]) -> list[str]:
    radiation_set = set(radiation_types)
    figure_families: list[str] = []
    for family, required in FIGURE_FAMILY_RULES.items():
        if radiation_set.intersection(required):
            figure_families.append(family)
    return sorted(set(figure_families))


def _detect_simulation_codes(text: str) -> list[str]:
    return _detect_categories(text, SIMULATION_CODE_KEYWORDS)


def _augment_figure_families(figure_families: list[str], simulation_codes: Iterable[str]) -> list[str]:
    updated = set(figure_families)
    if any(code in {"geant4", "mcnp", "phits", "fluka"} for code in simulation_codes):
        updated.update(["layer_energy_deposition", "mc_analytical_overlay", "publication_caption_pack", "secondary_particle_tally"])
    return sorted(updated)


def extract_paper_record(path: Path) -> PaperRecord:
    raw_text = _read_pdf_text(path)
    compact = _normalized(raw_text)
    fallback_title = _clean_filename_title(path)
    title = _candidate_title(raw_text, fallback_title)
    focus_text = _extract_focus_text(raw_text, title)
    doi_match = DOI_PATTERN.search(compact)
    radiation_types = _detect_categories(focus_text, RADIATION_KEYWORDS)
    material_classes = _detect_categories(focus_text, MATERIAL_CLASS_KEYWORDS)
    simulation_codes = _detect_simulation_codes(focus_text)
    figure_families = _augment_figure_families(_infer_figure_families(radiation_types), simulation_codes)
    return PaperRecord(
        file_name=path.name,
        title=title,
        year=_extract_year(compact),
        doi=doi_match.group(0) if doi_match else None,
        materials=_extract_materials(focus_text),
        material_classes=material_classes,
        radiation_types=radiation_types,
        figure_families=figure_families,
        simulation_codes=simulation_codes,
        abstract_snippet=focus_text[:900],
    )


def build_inventory(paper_dir: str | Path) -> list[PaperRecord]:
    pdf_dir = Path(paper_dir)
    return [extract_paper_record(path) for path in sorted(pdf_dir.glob("*.pdf"))]


def summarise_inventory(records: list[PaperRecord]) -> dict[str, object]:
    material_classes = Counter(label for record in records for label in record.material_classes)
    radiation_types = Counter(label for record in records for label in record.radiation_types)
    figure_families = Counter(label for record in records for label in record.figure_families)
    simulation_codes = Counter(label for record in records for label in record.simulation_codes)
    return {
        "paper_count": len(records),
        "material_classes": dict(material_classes),
        "radiation_types": dict(radiation_types),
        "figure_families": dict(figure_families),
        "simulation_codes": dict(simulation_codes),
    }


def write_inventory(records: list[PaperRecord], output_prefix: str | Path) -> tuple[Path, Path, Path]:
    prefix = Path(output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = prefix.with_suffix(".json")
    csv_path = prefix.with_suffix(".csv")
    summary_path = prefix.with_name(prefix.stem + "_summary").with_suffix(".json")

    rows = [asdict(record) for record in records]
    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "file_name",
                "title",
                "year",
                "doi",
                "materials",
                "material_classes",
                "radiation_types",
                "figure_families",
                "simulation_codes",
                "abstract_snippet",
            ],
        )
        writer.writeheader()
        for row in rows:
            serialised = row.copy()
            for key in ("materials", "material_classes", "radiation_types", "figure_families", "simulation_codes"):
                serialised[key] = "; ".join(serialised[key])
            writer.writerow(serialised)

    summary_path.write_text(json.dumps(summarise_inventory(records), indent=2), encoding="utf-8")
    return json_path, csv_path, summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract benchmark-ready metadata from ShieldLab reference papers.")
    parser.add_argument("paper_dir", help="Directory containing PDF papers")
    parser.add_argument("--output-prefix", required=True, help="Output path prefix without extension")
    args = parser.parse_args()

    records = build_inventory(args.paper_dir)
    json_path, csv_path, summary_path = write_inventory(records, args.output_prefix)
    print(f"papers: {len(records)}")
    print(f"json: {json_path}")
    print(f"csv: {csv_path}")
    print(f"summary: {summary_path}")


if __name__ == "__main__":
    main()