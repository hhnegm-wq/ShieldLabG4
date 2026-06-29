"""Pro-gate UI components for ShieldLab G4.

Usage
-----
>>> from ui.components.pro_gate import pro_only, pro_badge
>>>
>>> # Render a locked placeholder when the user is on Free:
>>> if pro_only("Multi-material comparison"):
...     # build the actual Pro UI here
...     pass
"""

from __future__ import annotations

import streamlit as st

from shieldlab.content import PAGE_COPY


def _common() -> dict:
    """Lazy accessor for PAGE_COPY['common'] so it resolves at call-time, not import-time."""
    return PAGE_COPY["common"]


def pro_badge() -> str:
    """Return an inline HTML badge for use in markdown strings."""
    return '<span class="slg-pro-badge">PRO</span>'


def pro_only(
    feature_label: str,
    help_text: str = "",
    key: str = "",
) -> bool:
    """Gate a UI section behind the Pro tier.

    Returns True if the user is Pro (caller should render the feature).
    Returns False and renders a locked placeholder if the user is Free.

    Parameters
    ----------
    feature_label : short name of the feature shown in the lock message
    help_text     : extra explanation (shown under the lock message)
    key           : unique key suffix for the Streamlit widget
    """
    from auth import get_user_tier
    tier = get_user_tier()

    if tier == "pro":
        return True

    # Free user - render lock banner
    _cc = _common()
    st.info(
        str(_cc["pro_gate_message"]).format(
            feature_label=feature_label,
            upgrade_url=str(_cc["upgrade_url"]),
        ),
        icon=None,
    )
    if help_text:
        st.caption(help_text)
    return False


def pro_download_button(
    label: str,
    data: bytes | str,
    file_name: str,
    mime: str,
    feature_label: str = "High-resolution export",
    key: str = "",
) -> None:
    """Render a download button that is locked for Free users.

    Parameters
    ----------
    label         : button label (shown on the download button)
    data          : file content
    file_name     : suggested filename
    mime          : MIME type
    feature_label : label used in the lock tooltip
    key           : unique Streamlit key
    """
    from auth import get_user_tier
    tier = get_user_tier()

    if tier == "pro":
        st.download_button(
            label=label,
            data=data,
            file_name=file_name,
            mime=mime,
            key=key or f"pro_dl_{file_name}",
        )
    else:
        st.button(
            f"Locked: {label}",
            key=key or f"locked_{file_name}",
            disabled=True,
            help=str(_common()["locked_download_help"]).format(feature_label=feature_label),
        )

