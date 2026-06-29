"""Error reporter widget - one-click "Report this issue" button.

When clicked, formats a pre-filled GitHub issue URL containing:
  - traceback (if available)
  - ShieldLab version
  - Python version
  - Operating system
  - A short description the user fills in

Usage
-----
    from components.error_reporter import render_error_reporter
    try:
        ...
    except Exception as exc:
        render_error_reporter(exc)
"""
from __future__ import annotations

import platform
import sys
import traceback
import urllib.parse

import streamlit as st

_GITHUB_ISSUES = "https://github.com/shieldlab-g4/shieldlab/issues/new"


def render_error_reporter(
    exc: Exception | None = None,
    context: str = "",
    show_traceback: bool = False,
) -> None:
    """Show a user-friendly error box with an optional "Report this issue" link.

    Parameters
    ----------
    exc           : the exception (or None for a generic report prompt)
    context       : extra context string (e.g. page name, parameter values)
    show_traceback: whether to show the full traceback in the expander
    """
    from shieldlab import __version__

    msg = str(exc) if exc else "An unexpected error occurred."

    st.error(f"**Calculation error:** {msg}")

    tb_text = ""
    if exc is not None:
        tb_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    # Build pre-filled issue body
    body_lines = [
        "## Bug Report",
        "",
        "### Description",
        "<!-- Please briefly describe what you were doing when this happened -->",
        "",
        f"**Context:** {context or 'N/A'}",
        "",
        "### Error",
        f"```",
        msg,
        "```",
    ]
    if tb_text:
        body_lines += ["", "### Traceback", "```", tb_text.strip(), "```"]
    body_lines += [
        "",
        "### Environment",
        f"- ShieldLab G4 version: `{__version__}`",
        f"- Python: `{sys.version.split()[0]}`",
        f"- OS: `{platform.system()} {platform.release()}`",
    ]
    body = "\n".join(body_lines)

    issue_url = (
        f"{_GITHUB_ISSUES}?"
        + urllib.parse.urlencode({
            "title": f"[Bug] {msg[:80]}",
            "body":  body,
            "labels": "bug",
        })
    )

    with st.expander("Technical details & report", expanded=False):
        if tb_text and show_traceback:
            st.code(tb_text, language="python")
        elif tb_text:
            st.code(tb_text[:1000] + ("." if len(tb_text) > 1000 else ""), language="python")

        st.markdown(
            f"[Report this issue on GitHub]({issue_url})",
            help="Opens a pre-filled GitHub issue in your browser.",
        )
        st.caption(f"ShieldLab G4 v{__version__} | Python {sys.version.split()[0]} | {platform.system()}")


