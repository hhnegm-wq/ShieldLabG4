"""Opt-in anonymous event telemetry for ShieldLab G4.

Wire to PostHog / Plausible / Amplitude by setting the env var and installing
the provider SDK.  **No data is sent unless the user explicitly opts in and
SHIELDLAB_TELEMETRY_KEY is configured.**

Env vars
--------
SHIELDLAB_TELEMETRY_KEY   - provider write key / project API key
SHIELDLAB_TELEMETRY_HOST  - (optional) self-hosted PostHog endpoint

Session state
-------------
_telemetry_consent : bool  - True only after user explicitly opts in
"""
from __future__ import annotations

import os
from typing import Any


def _get_key() -> str:
    return os.environ.get("SHIELDLAB_TELEMETRY_KEY", "")


def _consent_given() -> bool:
    """Return True only when the user has explicitly opted in."""
    try:
        import streamlit as st  # type: ignore
        return bool(st.session_state.get("_telemetry_consent", False))
    except Exception:
        return False


def track_event(event_name: str, props: dict[str, Any] | None = None) -> None:
    """Fire a single named event if consent is given and key is configured.

    Parameters
    ----------
    event_name:
        Dot-separated event identifier, e.g. ``"calc.run"`` or ``"pdf.export"``.
    props:
        Optional mapping of additional string-serialisable properties.
        PII must never be included.
    """
    if not _consent_given():
        return
    key = _get_key()
    if not key:
        return

    # try:
    #     import posthog
    #     host = os.environ.get("SHIELDLAB_TELEMETRY_HOST", "https://app.posthog.com")
    #     posthog.project_api_key = key
    #     posthog.host = host
    #     posthog.capture(
    #         distinct_id="anonymous",
    #         event=event_name,
    #         properties=props or {},
    #     )
    # except Exception:
    #     pass  # telemetry must never break the app


def render_consent_widget() -> None:
    """Render a small opt-in / opt-out toggle in the current Streamlit context.

    Call this from a Settings page or sidebar.
    """
    try:
        import streamlit as st  # type: ignore
        current = bool(st.session_state.get("_telemetry_consent", False))
        new_val = st.checkbox(
            "Allow anonymous usage analytics",
            value=current,
            help=(
                "Sends anonymised event names only (e.g. 'calc.run').  "
                "No personal data, no file contents.  "
                "Requires SHIELDLAB_TELEMETRY_KEY to be configured."
            ),
        )
        if new_val != current:
            st.session_state["_telemetry_consent"] = new_val
    except Exception:
        pass

