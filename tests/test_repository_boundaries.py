from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GITIGNORE = ROOT / ".gitignore"
ARCHITECTURE_DOC = ROOT / "docs" / "architecture.md"

REQUIRED_IGNORE_PATTERNS = {
    "build/",
    "backups/",
    "results/",
    "tmp/",
    ".benchmarks/",
    ".streamlit/",
    "streamlit_debug.log",
}

REQUIRED_ARCHITECTURE_SECTIONS = {
    "## Repository ownership zones",
    "## Release boundaries",
    "### Ships as product/runtime",
    "### Ships as validation or governance evidence",
    "### Does not define the product and must remain disposable",
    "ADR-0002",
}


class TestRepositoryBoundaries:
    def test_gitignore_covers_local_transient_artifacts(self):
        content = GITIGNORE.read_text(encoding="utf-8")
        missing = sorted(pattern for pattern in REQUIRED_IGNORE_PATTERNS if pattern not in content)
        assert not missing, ".gitignore is missing boundary patterns: " + ", ".join(missing)

    def test_architecture_doc_defines_ownership_and_release_boundaries(self):
        content = ARCHITECTURE_DOC.read_text(encoding="utf-8")
        missing = sorted(section for section in REQUIRED_ARCHITECTURE_SECTIONS if section not in content)
        assert not missing, "architecture.md is missing boundary sections: " + ", ".join(missing)
