"""Runtime bootstrap helpers for ShieldLab G4 Streamlit pages."""
from __future__ import annotations

import sys
from pathlib import Path


def ensure_project_paths() -> tuple[Path, Path, Path]:
    """Ensure the repo's ui/ and python/ folders are importable.

    Also evicts any previously imported non-repo ``shieldlab`` package so later
    imports resolve to this workspace's implementation.
    """
    ui_dir = Path(__file__).resolve().parent
    project_root = ui_dir.parent
    python_dir = project_root / "python"

    for path in (str(python_dir), str(ui_dir), str(project_root)):
        if path not in sys.path:
            sys.path.insert(0, path)

    # Always evict shieldlab.content so PAGE_COPY is reloaded fresh on every
    # page navigation (guards against stale cached modules from before content.py
    # was updated while the server was running).
    for name in list(sys.modules):
        if name == "shieldlab.content" or name.startswith("shieldlab.content."):
            del sys.modules[name]

    shieldlab_mod = sys.modules.get("shieldlab")
    shieldlab_file = getattr(shieldlab_mod, "__file__", "") if shieldlab_mod else ""
    if shieldlab_file:
        try:
            resolved = Path(shieldlab_file).resolve()
        except OSError:
            resolved = None
        if resolved is None or python_dir.resolve() not in resolved.parents:
            for name in list(sys.modules):
                if name == "shieldlab" or name.startswith("shieldlab."):
                    del sys.modules[name]

    return project_root, python_dir, ui_dir