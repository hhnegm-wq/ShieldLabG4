"""Shared constants and sys.path bootstrap for the ShieldLab G4 Streamlit UI."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value).expanduser().resolve() if value else default.resolve()


def resolve_project_path(path_text: str | Path, *, base_dir: Path | None = None) -> Path:
    base = base_dir or PROJECT_ROOT
    candidate = Path(path_text).expanduser()
    if not candidate.is_absolute():
        candidate = base / candidate
    return candidate.resolve()


def is_within_directory(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _default_build_dir(project_root: Path) -> Path:
    # On Windows+WSL, the build dir may be inside the WSL filesystem.
    # Set SHIELDLAB_BUILD_DIR to override; e.g.:
    #   $env:SHIELDLAB_BUILD_DIR = "\\wsl.localhost\Ubuntu\home\<user>\...\build"
    return (project_root / "build").resolve()


PROJECT_ROOT = _env_path("SHIELDLAB_PROJECT_ROOT", Path(__file__).resolve().parents[1])
SHIELDLAB_PYTHON = _env_path("SHIELDLAB_PYTHONPATH", PROJECT_ROOT / "python")
BUILD_DIR = _env_path("SHIELDLAB_BUILD_DIR", _default_build_dir(PROJECT_ROOT))
STUDIES_DIR = _env_path("SHIELDLAB_STUDIES_DIR", PROJECT_ROOT / "configs" / "studies")
RESULTS_DIR = BUILD_DIR / "results"

WSL_DISTRO = os.environ.get("SHIELDLAB_WSL_DISTRO", "Ubuntu")
# Set SHIELDLAB_GEANT4_SETUP to your geant4.sh path, e.g.:
#   $env:SHIELDLAB_GEANT4_SETUP = "/home/<user>/geant4-install/bin/geant4.sh"
GEANT4_SETUP = os.environ.get("SHIELDLAB_GEANT4_SETUP", "")
GEANT4_EXECUTABLE = os.environ.get("SHIELDLAB_G4_EXECUTABLE", "./ShieldLabG4")

# Python interpreter that has shieldlab + streamlit installed
PYTHON_EXE = _env_path("SHIELDLAB_PYTHON_EXE", Path(sys.executable))

_p = str(SHIELDLAB_PYTHON)
if _p not in sys.path:
    sys.path.insert(0, _p)

