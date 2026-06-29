# Contributing to ShieldLab G4

Thank you for your interest in contributing. This document describes how the
project is organized, how to set up a development environment, and the workflow
and quality gates every change must pass.

## Architecture at a glance

ShieldLab G4 uses a deliberate **two-host execution model**:

| Layer | Runs on | Path |
|-------|---------|------|
| Geant4 Monte Carlo core (C++) | **WSL / Linux** (Geant4 is not built natively on Windows) | `app/`, `src/`, `include/`, built to `build/ShieldLabG4` |
| Analytical physics library (Python) | Windows or Linux | `python/shieldlab/` |
| REST API (FastAPI) | Windows or Linux / container | `api/` |
| Web UI (Streamlit) | Windows or Linux | `ui/` |
| Batch worker (queue → Geant4 → blob) | Linux / container | `worker/` |
| CLI | Windows or Linux | `cli/` |
| Infrastructure as Code | Azure (Bicep / AKS manifests) | `infra/`, `deploy/` |

> **Important:** The Geant4 binary must be built and executed inside **WSL**.
> On Windows, the worker/runner delegates Monte Carlo execution to WSL via
> `wsl bash -lc ...`. IntelliSense errors for Geant4 headers on Windows are
> expected (the headers live in the WSL toolchain) and are not real errors.

## Development setup

### Python stack (Windows or Linux)

```powershell
# Windows PowerShell
$env:PYTHONPATH = 'python;ui'
python -m pip install -e ./python
python -m streamlit run ui/app.py --server.port 8501
```

### Geant4 core (WSL)

```bash
# Inside WSL, with the Geant4 environment sourced
cmake -S . -B build && cmake --build build -j
./build/ShieldLabG4 --help
```

## Running the tests

The fast suite (no Geant4 binary, no network, no UI browser) must stay green:

```powershell
$env:PYTHONPATH = 'python;ui'
pytest -q --ignore=backups -m "not geant4 and not publication and not ui and not network"
```

Baseline: **215 passed, 5 skipped**. Geant4-marked tests run only when
`SHIELDLAB_TEST_GEANT4=1` and the binary is available (WSL).

## Branch & pull-request workflow

1. Branch from `main`: `git checkout -b feat/<short-name>` (or `fix/`, `docs/`, `chore/`).
2. Keep commits focused; follow **Conventional Commits**
   (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`, `ci:`).
3. Ensure the fast test suite passes and `pre-commit` hooks are clean.
4. Open a PR into `main`. CI must be green (`ci_gate`, `science_gate`,
   `release_gate`, security scan) before merge.
5. `main` is protected: no direct pushes; review via CODEOWNERS.

## Code style & hygiene

- Python is linted/formatted with **ruff**; run `pre-commit install` once to
  enable automatic checks (see `.pre-commit-config.yaml`).
- Respect `.editorconfig` (UTF-8, LF, 4-space Python / 2-space C++).
- Do **not** commit generated or binary artifacts: build outputs, `results/`,
  `backups/`, Office/PDF exports of manuscripts (track the `.md` source and
  regenerate exports), or third-party reference PDFs. See `.gitignore`.

## Scientific accuracy

Physics changes must preserve benchmark agreement (NIST XCOM ≤ 2 %, HVL ≤ 1.5 %,
ANSI/ANS-6.4.3 buildup self-consistency). Add or update a test in
`tests/benchmarks/` for any change to a physics formula.

## Reporting security issues

Do not open public issues for vulnerabilities. Follow `SECURITY.md`.
