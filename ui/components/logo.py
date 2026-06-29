"""Logo path resolution — single source of truth for the ShieldLab G4 brand mark.

All UI modules should import ``LOGO_PATH`` from here rather than maintaining
their own candidate lists.
"""
from __future__ import annotations

from pathlib import Path

_UI_DIR = Path(__file__).parent.parent  # …/ui/

# Ordered by preference: canonical assets copy first, then original sources.
_CANDIDATES = [
    _UI_DIR / "assets" / "logo.png",
    _UI_DIR.parent / "logo_icon" / "ShieldLabG4_new_logo.png",
    _UI_DIR.parent / "logo_icon" / "ShieldLabG4_logo.png",
]

LOGO_PATH: Path | None = next((p for p in _CANDIDATES if p.exists()), None)
