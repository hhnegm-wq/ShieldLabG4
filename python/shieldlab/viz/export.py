"""Figure export helpers — Streamlit download buttons for journal submissions.

Provides
--------
fig_to_bytes(fig, fmt, dpi)
    Render a matplotlib Figure to bytes in the requested format.

figure_download_buttons(fig, basename, tier, formats, caption)
    Render a figure with ``st.pyplot`` then emit one download button per
    requested format.  Pro formats are gated behind the tier check.
"""

from __future__ import annotations

import io
from typing import Literal

import matplotlib.pyplot as plt

from shieldlab.metadata import COPYRIGHT_OWNER, PRODUCT_NAME

# ---------------------------------------------------------------------------
# Format catalogue
# ---------------------------------------------------------------------------
_FORMAT_META: dict[str, dict] = {
    "png96":  {"label": "PNG (96 DPI)",  "ext": "png",  "mime": "image/png",                "dpi": 96,  "pro": False},
    "png300": {"label": "PNG (300 DPI)", "ext": "png",  "mime": "image/png",                "dpi": 300, "pro": True},
    "png600": {"label": "PNG (600 DPI)", "ext": "png",  "mime": "image/png",                "dpi": 600, "pro": True},
    "svg":    {"label": "SVG",           "ext": "svg",  "mime": "image/svg+xml",             "dpi": None,"pro": True},
    "eps":    {"label": "EPS",           "ext": "eps",  "mime": "application/postscript",    "dpi": 300, "pro": True},
    "pdf":    {"label": "PDF",           "ext": "pdf",  "mime": "application/pdf",           "dpi": 300, "pro": True},
    "tiff":   {"label": "TIFF (600 DPI)","ext": "tiff", "mime": "image/tiff",               "dpi": 600, "pro": True},
}

# Default format lists
_FREE_FORMATS  = ["png96"]
_PRO_FORMATS   = ["png300", "png600", "svg", "eps", "pdf", "tiff"]
_ALL_FORMATS   = _FREE_FORMATS + _PRO_FORMATS


def fig_to_bytes(
    fig: plt.Figure,
    fmt: str = "png96",
    dpi: int | None = None,
) -> bytes:
    """Render *fig* to bytes.

    Parameters
    ----------
    fig  : matplotlib Figure
    fmt  : key from _FORMAT_META (e.g. "png300", "svg", "eps", "pdf")
    dpi  : override DPI; if None uses the value from _FORMAT_META

    Returns
    -------
    bytes
    """
    meta = _FORMAT_META.get(fmt)
    if meta is None:
        raise ValueError(f"Unknown format key '{fmt}'. Choose from {list(_FORMAT_META)}")

    out_dpi = dpi if dpi is not None else meta["dpi"]
    buf = io.BytesIO()

    if meta["ext"] == "svg":
        fig.savefig(buf, format="svg", bbox_inches="tight")
    elif meta["ext"] == "eps":
        # EPS does not support transparency — set white background
        orig_fc = fig.get_facecolor()
        fig.set_facecolor("white")
        try:
            fig.savefig(buf, format="eps", dpi=out_dpi, bbox_inches="tight")
        finally:
            fig.set_facecolor(orig_fc)
    else:
        fig.savefig(buf, format=meta["ext"], dpi=out_dpi, bbox_inches="tight")

    return buf.getvalue()


def figure_download_buttons(
    fig: plt.Figure,
    basename: str = "figure",
    tier: Literal["free", "pro"] = "free",
    caption: str = "",
    show_figure: bool = True,
    key_prefix: str = "",
) -> None:
    """Display *fig* in Streamlit and render format-download buttons below it.

    Free users get a watermarked PNG-96 only.
    Pro users get PNG-300, PNG-600, SVG, EPS, PDF, TIFF.

    Parameters
    ----------
    fig         : matplotlib Figure to render
    basename    : stem used for the downloaded filename (no extension)
    tier        : "free" or "pro"
    caption     : optional caption string shown below the figure
    show_figure : whether to call st.pyplot(fig) (set False if already shown)
    key_prefix  : unique prefix for Streamlit widget keys (required if called
                  multiple times on the same page)
    """
    import streamlit as st
    from shieldlab.viz.style import add_reproducibility_footer
    from shieldlab import __version__

    # Stamp reproducibility footer
    add_reproducibility_footer(
        fig,
        version=__version__,
        label=PRODUCT_NAME,
        owner=COPYRIGHT_OWNER,
    )

    # Apply free-tier watermark
    if tier == "free":
        fig.text(
            0.5, 0.5,
            f"{PRODUCT_NAME} — Free",
            ha="center", va="center",
            fontsize=22,
            color="0.70",
            alpha=0.18,
            rotation=30,
            transform=fig.transFigure,
            fontweight="bold",
        )

    if show_figure:
        st.pyplot(fig, width="stretch")

    if caption:
        st.caption(caption)

    # Download buttons — max 4 per row to prevent text wrapping in narrow layouts
    formats_to_show = _ALL_FORMATS if tier == "pro" else _FREE_FORMATS
    _MAX_PER_ROW = 4
    for _row_start in range(0, len(formats_to_show), _MAX_PER_ROW):
        batch = formats_to_show[_row_start : _row_start + _MAX_PER_ROW]
        cols = st.columns(len(batch))

        for col, fmt_key in zip(cols, batch):
            meta = _FORMAT_META[fmt_key]
            is_gated = meta["pro"] and tier != "pro"
            label = f"⬇ {meta['label']}"
            fname = f"{basename}.{meta['ext']}"

            if is_gated:
                col.button(
                    f"🔒 {meta['label']}",
                    key=f"{key_prefix}_{fmt_key}_locked",
                    help="Upgrade to Pro to unlock high-resolution and vector formats.",
                    disabled=True,
                )
            else:
                try:
                    data = fig_to_bytes(fig, fmt=fmt_key)
                    col.download_button(
                        label=label,
                        data=data,
                        file_name=fname,
                        mime=meta["mime"],
                        key=f"{key_prefix}_{fmt_key}_dl",
                    )
                except Exception:
                    col.button(label, disabled=True, key=f"{key_prefix}_{fmt_key}_err",
                               help="Export failed. Try a different format.")
