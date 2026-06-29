"""ISIP design-system tokens for ShieldLab G4.

Single source of truth for all color, shadow, and scale constants.
Import from here rather than hard-coding values in CSS strings.

Design reference: D:/projects/ISIP/platform/src/app/globals.css
                  D:/projects/ISIP/platform/tailwind.config.js
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# ISIP color tokens (exact from globals.css / tailwind.config.js)
# ---------------------------------------------------------------------------
PRIMARY       = "#059669"   # isip-green-600
PRIMARY_LIGHT = "#10b981"   # isip-green-500
PRIMARY_DARK  = "#064e3b"   # isip-green-900
PRIMARY_MID   = "#065f46"   # isip-green-800
PRIMARY_MED   = "#047857"   # isip-green-700
GREEN_50      = "#ecfdf5"   # isip-green-50
GREEN_100     = "#d1fae5"   # isip-green-100
GREEN_200     = "#a7f3d0"   # isip-green-200
GREEN_300     = "#6ee7b7"   # isip-green-300
GREEN_400     = "#34d399"   # isip-green-400
BLUE_500      = "#3b82f6"   # isip-blue-500
BLUE_600      = "#2563eb"   # isip-blue-600
PURPLE_500    = "#8b5cf6"   # isip-purple-500
GOLD_500      = "#f59e0b"   # isip-gold-500
DANGER        = "#ef4444"
SUCCESS       = "#22c55e"
WARN          = "#f59e0b"

# Surfaces (ISIP light system)
BG_PAGE       = "#f9fafb"   # body background-start
BG_PAGE_END   = "#f3f4f6"   # body background-end
SURFACE       = "#ffffff"   # card / widget bg
SURFACE_2     = "#f9fafb"   # subtle row tint
SURFACE_3     = "#ecfdf5"   # green tint row

# Text hierarchy (ISIP dark)
INK           = "#111827"   # gray-900 — headings
INK_SOFT      = "#1f2937"   # gray-800 — body
MUTED         = "#6b7280"   # gray-500 — captions / labels
MUTED_LIGHT   = "#9ca3af"   # gray-400

# Borders
BORDER        = "#f3f4f6"   # gray-100 — default card border
BORDER_MED    = "#e5e7eb"   # gray-200 — stronger divider
BORDER_GREEN  = "rgba(5,150,105,0.22)"   # green-tinted
BORDER_GREEN2 = "rgba(5,150,105,0.40)"  # focus ring

# Shadows  (ISIP shadow-sm / shadow-md / shadow-lg)
SHADOW_SM     = "0 1px 3px rgba(0,0,0,0.10), 0 1px 2px rgba(0,0,0,0.06)"
SHADOW_MD     = "0 4px 6px rgba(0,0,0,0.07), 0 10px 15px rgba(0,0,0,0.05)"
SHADOW_LG     = "0 10px 15px rgba(0,0,0,0.08), 0 20px 40px rgba(0,0,0,0.06)"

_FONT_SCALE = {"small": 0.92, "medium": 1.0, "large": 1.12}
_WIDTH_SCALE = {"standard": "1280px", "wide": "1480px", "full": "1680px"}
_DENSITY = {
    "compact":     {"block_top": "0.5rem", "block_bottom": "1.2rem", "tab_pad": "6px 12px",  "exp_pad": "8px 12px"},
    "comfortable": {"block_top": "0.7rem", "block_bottom": "1.8rem", "tab_pad": "8px 16px",  "exp_pad": "10px 14px"},
}


