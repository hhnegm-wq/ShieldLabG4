import json

import pandas as pd

from shieldlab.io.runner import _wsl_path, run_study


def test_wsl_path_translates_windows_drive_path_to_mnt_mount():
    distro, translated = _wsl_path(r"D:\projects\ShieldLabG4\build\generated.mac")

    assert distro is None
    assert translated == "/mnt/d/projects/ShieldLabG4/build/generated.mac"


def test_wsl_path_preserves_unc_style_wsl_path():
    distro, translated = _wsl_path(r"//wsl$/Ubuntu/mnt/d/projects/ShieldLabG4/build/generated.mac")

    assert distro == "Ubuntu"
    assert translated == "/mnt/d/projects/ShieldLabG4/build/generated.mac"


def test_run_study_accepts_utf8_bom_study_files(tmp_path):
    build_dir = tmp_path / "build"
    result_dir = build_dir / "results" / "bom_fixture"
    result_dir.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "events": 1000,
                "transmitted": 820,
                "reflected": 70,
                "total_thickness_cm": 1.0,
                "transmission_fraction": 0.82,
                "reflection_fraction": 0.07,
                "absorption_fraction": 0.11,
                "linear_attenuation_cm_inv": 0.198,
                "attenuation_estimate_type": "direct",
            }
        ]
    ).to_csv(result_dir / "run_summary.csv", index=False)
    pd.DataFrame(
        [{"layer_index": 0, "material": "G4_Pb", "density_g_cm3": 11.34}]
    ).to_csv(result_dir / "layer_energy_deposition.csv", index=False)

    study_file = tmp_path / "bom_fixture.json"
    study = {
        "name": "bom_fixture",
        "description": "Windows BOM fixture for runner study loading.",
        "source": {"particle": "gamma", "energy": 662, "energy_unit": "keV", "direction": [1, 0, 0]},
        "geometry": {
            "type": "slab",
            "transverse_size_cm": 10,
            "layers": [{"material": "G4_Pb", "thickness_cm": 1.0, "divisions": 1}],
        },
        "run": {
            "histories": 1000,
            "physics_list": "FTFP_BERT_EMZ",
            "output_dir": "results/bom_fixture",
        },
    }
    study_file.write_text(json.dumps(study, indent=2), encoding="utf-8-sig")

    outputs = run_study(study_file, build_dir=build_dir, skip_geant4=True, no_plots=True)

    assert outputs["macro_file"] is not None and outputs["macro_file"].exists()
    assert outputs["workbook"] is not None and outputs["workbook"].exists()
    assert outputs["validation_summary"] is not None and outputs["validation_summary"].exists()
    assert outputs["provenance_manifest"] is not None and outputs["provenance_manifest"].exists()