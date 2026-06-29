from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AssetCheckResult:
    checked: list[Path]
    missing: list[Path]


def check_critical_assets(ui_dir: Path) -> AssetCheckResult:
    """Validate existence of critical UI assets used by branding and shell visuals."""
    from components.logo import LOGO_PATH, _CANDIDATES
    checked = list(_CANDIDATES)
    missing = [p for p in _CANDIDATES if not p.exists()]
    # Canonical logo must exist
    if LOGO_PATH is None:
        missing.append(ui_dir / "assets" / "logo.png")
    return AssetCheckResult(checked=checked, missing=missing)
