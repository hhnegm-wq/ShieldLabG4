from pathlib import Path

import pytest

from shieldlab.io.study_validator import has_errors, issues_to_frame, validate_study_file


ROOT = Path(__file__).resolve().parents[2]
STUDY_DIR = ROOT / "configs" / "studies"
LITERATURE_STUDIES = sorted(STUDY_DIR.glob("literature_benchmark_*.json"))


@pytest.mark.parametrize("study_path", LITERATURE_STUDIES, ids=lambda p: p.name)
def test_literature_benchmark_config_has_no_validation_errors(study_path: Path):
    issues = validate_study_file(study_path)
    assert not has_errors(issues), (
        f"Validation errors in {study_path.name}:\n"
        f"{issues_to_frame(issues).to_string(index=False)}"
    )


def test_literature_benchmark_config_list_is_not_empty():
    assert LITERATURE_STUDIES, "No literature benchmark study files were found under configs/studies."
