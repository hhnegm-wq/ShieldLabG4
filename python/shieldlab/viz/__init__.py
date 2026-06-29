"""shieldlab.viz — Publication-quality figure helpers.

Modules
-------
style   : apply_journal_style() — global matplotlib RC params for journal submission.
export  : figure_download_buttons() — Streamlit download buttons (PNG/SVG/EPS/PDF).
captions: auto_caption() — generate figure captions from calc context.
"""

from shieldlab.viz.style import apply_journal_style, JOURNAL_PRESETS
from shieldlab.viz.export import figure_download_buttons, fig_to_bytes
from shieldlab.viz.captions import auto_caption

__all__ = [
    "apply_journal_style",
    "JOURNAL_PRESETS",
    "figure_download_buttons",
    "fig_to_bytes",
    "auto_caption",
]
