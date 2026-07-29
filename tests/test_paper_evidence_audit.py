from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_audit_module():
    path = Path(__file__).resolve().parents[1] / "tools" / "paper_evidence_audit.py"
    spec = importlib.util.spec_from_file_location("paper_evidence_audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_paper_evidence_audit_current_repo_passes() -> None:
    audit = _load_audit_module()
    root = Path(__file__).resolve().parents[1]
    assert audit.run_audit(root) == []


def test_audit_catches_placeholders_and_missing_reference_evidence(tmp_path: Path) -> None:
    audit = _load_audit_module()
    manuscript = tmp_path / "manuscript.md"
    manuscript.write_text(
        "# Paper\n\n"
        "*Department of Physics, [AFFILIATION REQUIRED]*\n\n"
        "Claim [1].\n\n"
        "## References\n\n"
        "[1] Example reference without a resolvable source.\n",
        encoding="utf-8",
    )

    errors = audit.audit_manuscript(manuscript)

    assert any("placeholder" in error for error in errors)
    assert any("reference 1 has no DOI/URL" in error for error in errors)
