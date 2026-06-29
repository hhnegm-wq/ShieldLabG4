# ShieldLab-G4

ShieldLab-G4 is a Geant4-based shielding simulation prototype with a Python workflow layer for study configuration, macro generation, Monte Carlo execution, sweep collection, Excel export, reference comparison, and figure generation.

## Repository Layout

- `app/` — Geant4 application entry point.
- `src/` and `include/` — Geant4 detector, source, stepping, and run logic.
- `python/shieldlab/` — analytical physics, reporting, plotting, and workflow modules.
- `ui/` — Streamlit platform shell and pages.
- `configs/studies/` — study JSON inputs.
- `tests/` — Python tests and benchmark coverage.

## Setup Paths and Environment

The UI no longer requires machine-specific absolute paths. The following environment variables may be used to override defaults when needed:

- `SHIELDLAB_PROJECT_ROOT` — repository root. Defaults to the checked-out repo.
- `SHIELDLAB_PYTHONPATH` — Python package directory. Defaults to `<repo>/python`.
- `SHIELDLAB_BUILD_DIR` — build directory. Defaults to `<repo>/build`.
- `SHIELDLAB_STUDIES_DIR` — study JSON directory. Defaults to `<repo>/configs/studies`.
- `SHIELDLAB_PYTHON_EXE` — Python interpreter for runner and Streamlit execution. Defaults to the active interpreter.
- `SHIELDLAB_PHYSICS_LIST` — Geant4 reference physics list override.
- `SHIELDLAB_RUN_MANAGER` — Geant4 run-manager mode. Supported values: `serial`, `default`, `auto`, and `mt` when Geant4 was built with multithreading.

## Windows Python Workflow

Use this workflow when you want the analytical Python stack and Streamlit UI on Windows. It does not require a native Windows Geant4 build if you are delegating Monte Carlo execution to WSL.

1. Create or activate a Python environment with Streamlit and the project dependencies installed.
2. From PowerShell, set the repo-local package paths:

```powershell
Set-Location D:\projects\ShieldLabG4
$env:PYTHONPATH = 'python;ui'
```

1. Run the Streamlit platform:

```powershell
d:/uv_envs/Scripts/python.exe -m streamlit run ui/app.py --server.port 8501
```

1. Run the Python test suite:

```powershell
d:/uv_envs/Scripts/python.exe -m pytest tests/ -q
```

## WSL + Geant4 Workflow

This remains the recommended Monte Carlo workflow when Geant4 is installed in WSL.

1. Build ShieldLab-G4 inside WSL with the Geant4 environment sourced.
2. Keep study JSON files inside the repo under `configs/studies/`.
3. Launch the workflow from Windows or WSL using the same study JSON.

Example from Windows PowerShell, pointing to a WSL-hosted project:

## One-Command Workflow

From Windows PowerShell, with the Python environment available, run:

```powershell
$env:PYTHONPATH='\\wsl.localhost\Ubuntu\home\negm_\geant4-install\ShieldLabG4\python'
d:/uv_envs/Scripts/python.exe -m shieldlab.io.runner '\\wsl.localhost\Ubuntu\home\negm_\geant4-install\ShieldLabG4\configs\studies\gamma_oxide_glass_formula_mixture_sweep.json'
```

The runner performs the full workflow:

```text
study validation -> Geant4 macro -> Geant4 run -> sweep CSV -> Excel workbook -> figures -> validation summary -> provenance manifest
```

For fast report regeneration from existing result CSV files, use:

```powershell
d:/uv_envs/Scripts/python.exe -m shieldlab.io.runner '<study.json>' --skip-geant4
```

To validate a study without running Geant4, use:

```powershell
d:/uv_envs/Scripts/python.exe -m shieldlab.io.study_validator '<study.json>' --output '<validation.csv>'
```

To generate a release-level validation and benchmark report artifact set, use:

```powershell
d:/uv_envs/Scripts/python.exe -m shieldlab.io.release_validation_report --project-root 'D:\projects\ShieldLabG4'
```

This writes timestamped JSON/Markdown reports and a latest snapshot under `docs/validation`.

To generate a manuscript-ready methods export pack (equations, assumptions, uncertainty statements, and benchmark table), use:

```powershell
d:/uv_envs/Scripts/python.exe -m shieldlab.io.methods_export_pack --project-root 'D:\projects\ShieldLabG4'
```

To enforce release gates (study errors, benchmark failures, and Q1 readiness thresholds), use:

```powershell
d:/uv_envs/Scripts/python.exe -m shieldlab.io.release_gate --report 'D:\projects\ShieldLabG4\docs\validation\release_validation_report_latest.json'
```

You can select a gate profile:

```powershell
# Strict publication gate
d:/uv_envs/Scripts/python.exe -m shieldlab.io.release_gate --profile release --report 'D:\projects\ShieldLabG4\docs\validation\release_validation_report_latest.json'

# Lenient development gate for in-progress datasets
d:/uv_envs/Scripts/python.exe -m shieldlab.io.release_gate --profile dev --report 'D:\projects\ShieldLabG4\docs\validation\release_validation_report_latest.json'
```

CI automation is available via `.github/workflows/release-validation-gate.yml` and runs report generation + gate evaluation on pull requests and main branch pushes.

When the project lives inside WSL, `shieldlab.io.runner` detects the WSL path layout and invokes the Geant4 executable through `wsl bash -lc ...`. That is the intended path for a WSL-hosted Geant4 toolchain.

## Native Windows Geant4 Build

Use this only if Geant4 is installed natively on Windows and your compiler toolchain matches that installation.

1. Open a Visual Studio 2022 x64 developer shell.
2. Configure CMake with your Geant4 installation available in `CMAKE_PREFIX_PATH`.
3. Configure and build:

```powershell
Set-Location D:\projects\ShieldLabG4
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

1. Run a sample macro:

```powershell
.\build\ShieldLabG4.exe .\macros\examples\gamma_lead_slab.mac
```

If you want to enable multithreaded execution, build Geant4 with MT support and then set:

```powershell
$env:SHIELDLAB_RUN_MANAGER = 'mt'
```

If the current Geant4 build does not support MT, ShieldLab-G4 falls back to serial execution.

## Main Outputs

For sweep studies, outputs are written under the study `run.output_dir` inside the build folder. A typical result folder contains:

- `E_*` child folders with Geant4 per-energy CSV files.
- `sweep_summary.csv` with derived attenuation coefficients, MFP, HVL, and TVL.
- `reference_coefficients.csv` and `reference_comparison.csv` when benchmark rows are included in the study JSON.
- `study_validation.csv` with configuration warnings or errors found before macro generation.
- `shieldlab_results.xlsx` with study, run, sweep, reference, comparison, and figure-index sheets.
- `figures/*.png` standard plots.
- `validation_summary.json` describing the generated artifacts.
- `provenance_manifest.json` with schema version, assumptions context, and traceable artifact pointers.

## Study Features Currently Supported

- NIST materials by name in geometry layers.
- Custom elemental mass-fraction materials.
- Formula-defined compounds such as `PbWO4`.
- Compound formula-mixture materials such as oxide glass recipes using `PbO`, `B2O3`, `SiO2`, `Na2O`, and `Al2O3` weight fractions.
- Single-energy runs and energy sweeps.
- Reference coefficient comparison against values embedded in the study JSON.
- Study validation for material definitions, formula parsing, geometry layer references, source settings, run settings, energy grids, and reference coefficient rows.

## Notes on Simulation Outputs

- `run_summary.csv` reports primary-track transmission and reflection at the world boundary. These are not total escaping-particle yields.
- The Monte Carlo attenuation estimate in `run_summary.csv` is labelled as a Beer-Lambert estimate derived from primary transmission, so it should not be interpreted as a buildup-corrected attenuation model.
- For buildup-factor workflows and publication reporting, use the analytical Python modules and validation artifacts together.
