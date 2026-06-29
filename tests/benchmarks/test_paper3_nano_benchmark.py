import json
from pathlib import Path

from shieldlab.analysis.nano_benchmark import plan_benchmark
from shieldlab.io.study_validator import has_errors, validate_study


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STUDY_FILE = PROJECT_ROOT / "configs" / "studies" / "paper3_hdpe_bi2o3_regime_a_baseline.json"


def test_paper3_baseline_study_has_no_validation_errors():
    study = json.loads(STUDY_FILE.read_text(encoding="utf-8"))
    issues = validate_study(study)

    assert not has_errors(issues)


def test_paper3_benchmark_plan_writes_macro_and_manifests(tmp_path):
    outputs = plan_benchmark(STUDY_FILE, build_dir=tmp_path / "build")

    macro_text = Path(outputs["macro_file"]).read_text(encoding="utf-8")
    plan_payload = json.loads(Path(outputs["plan_file"]).read_text(encoding="utf-8"))
    manifest_payload = json.loads(Path(outputs["manifest_file"]).read_text(encoding="utf-8"))

    assert "/shield/material/addMassFraction P3_HDPE_Bi2O3_30wt 2.45" in macro_text
    assert "Bi:" in macro_text
    assert "O:" in macro_text
    assert "C:" in macro_text
    assert "H:" in macro_text
    assert "/shield/output/setDirectory results/paper3/regime_a_hdpe_bi2o3_baseline/E_30_keV" in macro_text
    assert "/shield/output/setDirectory results/paper3/regime_a_hdpe_bi2o3_baseline/E_1332_keV" in macro_text

    assert plan_payload["study"]["paper3"]["campaign"] == "paper3_nano_regimes"
    assert plan_payload["study"]["paper3"]["regime"] == "A"
    assert plan_payload["execution"]["validation_mode"] == "benchmark_narrow_beam"
    assert plan_payload["physics_context"]["materials"] == ["P3_HDPE_Bi2O3_30wt"]
    assert plan_payload["artifacts"]["expected_result_subdirs"][0] == "E_30_keV"
    assert plan_payload["artifacts"]["expected_result_subdirs"][-1] == "E_1332_keV"

    assert manifest_payload["extra"]["campaign"] == "paper3_nano_regimes"
    assert manifest_payload["extra"]["regime"] == "A"
    assert manifest_payload["extra"]["material_family"] == "HDPE_Bi2O3"
    assert manifest_payload["extra"]["status"] == "planned"