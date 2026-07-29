from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

_PLACEHOLDER_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\[\s*affiliation\s+required[^\]]*\]",
        r"\[\s*placeholder\s*\]",
        r"\bdo\s+not\s+submit\b",
        r"\byour-org\b",
        r"\bexample\.com\b",
        r"\bTODO\b",
        r"\bTBD\b",
    )
]
_DOI_RE = re.compile(r"https://doi\.org/(10\.\d{4,9}/[^\s)\]>]+)", re.IGNORECASE)
_URL_RE = re.compile(r"https?://[^\s)>]+", re.IGNORECASE)
_NUMERIC_REFERENCE_RE = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)\.)\s+")
_BRACKET_CITATION_RE = re.compile(r"\[([0-9,\s\-–]+)\]")
_REFERENCES_HEADING_RE = re.compile(r"^#{1,3}\s+(?:\d+(?:\.\d+)*\.\s+)?references\s*$", re.IGNORECASE | re.MULTILINE)
_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_TRUSTED_BIBLIOGRAPHIC_RE = re.compile(
    r"\b(NBSIR|NISTIR|ICRU Report|UCRL-|McGraw-Hill|John Wiley|American Nuclear Society|"
    r"Lawrence Livermore National Laboratory|National Bureau of Standards|NIST, Gaithersburg)\b",
    re.IGNORECASE,
)

FINAL_MANUSCRIPTS = [
    Path("papers/paper1_scientific/manuscript_scientific_v08.md"),
    Path("papers/paper2_technical_software/manuscript_technical_software_v02.md"),
    Path("papers/paper3_nanogeant4/manuscript_nanogeant4_v10_submission.md"),
]
REQUIRED_EVIDENCE = [
    Path("docs/validation/release_validation_report_latest.json"),
    Path("docs/validation/validation_report.csv"),
    Path("papers/paper2_technical_software/data_validation_report.csv"),
    Path("tests/visual/baseline/home.png"),
    Path("deploy/Caddyfile"),
]


def _reference_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for line in text.splitlines():
        match = _NUMERIC_REFERENCE_RE.match(line)
        if match:
            number = int(match.group(1) or match.group(2))
            lines.append((number, line))
    return lines


def _references_section(text: str) -> str:
    match = _REFERENCES_HEADING_RE.search(text)
    if match is None:
        return ""
    return text[match.end():]


def _body_without_references(text: str) -> str:
    match = _REFERENCES_HEADING_RE.search(text)
    body = text[: match.start()] if match else text
    return _FENCED_CODE_RE.sub("", body)


def _citation_numbers(text: str) -> set[int]:
    numbers: set[int] = set()
    for match in _BRACKET_CITATION_RE.finditer(text):
        for token in match.group(1).split(","):
            token = token.strip()
            if not token:
                continue
            if "–" in token or "-" in token:
                left, right = re.split(r"[–-]", token, maxsplit=1)
                start, end = int(left.strip()), int(right.strip())
                numbers.update(range(start, end + 1))
            else:
                numbers.add(int(token))
    return numbers


def _has_internal_companion_evidence(line: str) -> bool:
    lowered = line.lower()
    return "companion" in lowered and "same submission package" in lowered


def _has_reference_evidence(line: str) -> bool:
    return bool(_DOI_RE.findall(line) or _URL_RE.findall(line)) or _has_internal_companion_evidence(line) or bool(
        _TRUSTED_BIBLIOGRAPHIC_RE.search(line)
    )


def audit_manuscript(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    for pattern in _PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            errors.append(f"{path}: placeholder or submission-blocking token matched {pattern.pattern!r}")

    references_text = _references_section(text)
    refs = _reference_lines(references_text)
    if not refs:
        errors.append(f"{path}: no numbered references found")
        return errors

    ref_numbers = [number for number, _line in refs]
    expected = list(range(1, max(ref_numbers) + 1))
    if ref_numbers != expected:
        errors.append(f"{path}: reference numbering mismatch: got {ref_numbers}, expected {expected}")

    cited = _citation_numbers(_body_without_references(text))
    missing = sorted(n for n in cited if n not in set(ref_numbers))
    if missing:
        errors.append(f"{path}: citations without reference entries: {missing}")

    doi_or_url_count = 0
    for number, line in refs:
        urls = _URL_RE.findall(line)
        if _has_reference_evidence(line):
            doi_or_url_count += 1
        else:
            errors.append(f"{path}: reference {number} has no DOI/URL or trusted bibliographic evidence")
        for url in urls:
            parsed = urlparse(url.rstrip("."))
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                errors.append(f"{path}: reference {number} has malformed URL {url!r}")

    if doi_or_url_count / max(len(refs), 1) < 0.75:
        errors.append(
            f"{path}: only {doi_or_url_count}/{len(refs)} references carry DOI/URL evidence; minimum is 75%"
        )
    return errors


def audit_evidence(root: Path) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_EVIDENCE:
        path = root / rel
        if not path.exists():
            errors.append(f"missing required evidence artifact: {rel}")
        elif path.is_file() and path.stat().st_size == 0:
            errors.append(f"required evidence artifact is empty: {rel}")

    report = root / "docs/validation/release_validation_report_latest.json"
    if report.exists():
        payload = json.loads(report.read_text(encoding="utf-8"))
        summary = payload.get("summary", {})
        if summary.get("ci_gate") != "pass":
            errors.append("release validation report does not have ci_gate=pass")
        if summary.get("study_error_count", 0) != 0:
            errors.append("release validation report contains study validation errors")
    return errors


def run_audit(root: Path) -> list[str]:
    errors: list[str] = []
    for rel in FINAL_MANUSCRIPTS:
        path = root / rel
        if not path.exists():
            errors.append(f"missing final manuscript source: {rel}")
            continue
        errors.extend(audit_manuscript(path))
    errors.extend(audit_evidence(root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit manuscript citations and platform evidence artifacts.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    root = args.root.resolve()
    errors = run_audit(root)
    if errors:
        print("Paper/evidence audit failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Paper/evidence audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
