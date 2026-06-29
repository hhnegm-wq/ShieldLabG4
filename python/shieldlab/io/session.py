"""Session save / restore for ShieldLab G4 calculations.

Saves the full calc_state dict to a JSON `.shieldlab` file that can be
reloaded on any ShieldLab G4 instance to reproduce the calculation exactly.

Public API
----------
save_session(calc_state, version, path=None) -> str | bytes
    Serialise calc_state to a JSON string (or .shieldlab file).

load_session(source) -> dict
    Deserialise and validate a .shieldlab JSON string or file path.

session_download_button(calc_state, version)
    Streamlit widget: download current session as .shieldlab file.
"""
from __future__ import annotations

import json
import datetime
import hashlib
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np

# ── Serialisation helpers ─────────────────────────────────────────────────────

class _NumpyEncoder(json.JSONEncoder):
    """Encode numpy arrays and scalars to JSON-serialisable types."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.ndarray):
            return {"__ndarray__": True, "data": obj.tolist(), "dtype": str(obj.dtype)}
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        return super().default(obj)


def _numpy_hook(dct: dict) -> Any:
    """JSON object_hook to restore numpy arrays."""
    if dct.get("__ndarray__"):
        return np.array(dct["data"], dtype=dct.get("dtype", "float64"))
    return dct


# ── Core functions ────────────────────────────────────────────────────────────

SCHEMA_VERSION = "1.0"

def save_session(
    calc_state: dict,
    version: str = "unknown",
    indent: int = 2,
) -> str:
    """Serialise calc_state to a JSON string.

    The resulting string can be saved as a `.shieldlab` file.

    Parameters
    ----------
    calc_state : dict  — the full calculation state from the Streamlit page
    version    : str   — shieldlab package version string
    indent     : int   — JSON indentation (2 for human-readable)

    Returns
    -------
    JSON string (str)
    """
    # Compute checksum over calc_state only (sort_keys=True for determinism).
    # load_session re-computes by parsing the raw calc_state JSON the same way.
    cs_raw = json.dumps(calc_state, cls=_NumpyEncoder, sort_keys=True, ensure_ascii=False)
    checksum = hashlib.sha256(cs_raw.encode()).hexdigest()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "shieldlab_version": version,
        "saved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "platform": {
            "python": sys.version.split()[0],
            "os":     platform.system(),
        },
        "calc_state": calc_state,
        "checksum": checksum,
    }
    return json.dumps(payload, cls=_NumpyEncoder, indent=indent, ensure_ascii=False)


def load_session(source: str | Path | bytes) -> dict:
    """Deserialise a `.shieldlab` JSON string / path / bytes.

    Returns the `calc_state` dict on success.
    Raises ValueError on schema incompatibility.
    Raises json.JSONDecodeError on malformed JSON.
    """
    if isinstance(source, (Path, str)):
        text = Path(source).read_text(encoding="utf-8")
    elif isinstance(source, bytes):
        text = source.decode("utf-8")
    else:
        raise TypeError(f"Expected str, Path, or bytes; got {type(source)}")

    payload = json.loads(text, object_hook=_numpy_hook)

    schema = payload.get("schema_version", "unknown")
    if schema != SCHEMA_VERSION:
        raise ValueError(
            f"Session schema v{schema} is not compatible with this version "
            f"(expected v{SCHEMA_VERSION}). Try upgrading ShieldLab G4."
        )

    if "calc_state" not in payload:
        raise ValueError("Session file does not contain a 'calc_state' key.")

    # Verify checksum: re-compute over calc_state using the raw (pre-hook) JSON.
    stored_checksum = payload.get("checksum")
    if stored_checksum is not None:
        raw_payload = json.loads(text)          # plain parse, no numpy hook
        raw_cs = raw_payload.get("calc_state", {})
        cs_raw = json.dumps(raw_cs, sort_keys=True, ensure_ascii=False)
        computed = hashlib.sha256(cs_raw.encode()).hexdigest()
        if computed != stored_checksum:
            raise ValueError(
                f"Checksum mismatch — session file may be corrupted or tampered. "
                f"(stored: {stored_checksum[:16]}…, computed: {computed[:16]}…)"
            )

    return payload["calc_state"]


# ── Streamlit widget ──────────────────────────────────────────────────────────

def session_download_button(
    calc_state: dict,
    version: str = "unknown",
    label: str = "💾 Save session (.shieldlab)",
    key: str = "session_dl",
) -> None:
    """Render a Streamlit download button for the current session.

    Must be called inside a Streamlit app context.
    """
    import streamlit as st  # noqa: PLC0415

    mat_name = calc_state.get("mat_name", "material")
    filename = f"shieldlab_{mat_name.replace(' ','_')}.shieldlab"

    try:
        json_str = save_session(calc_state, version=version)
        st.download_button(
            label=label,
            data=json_str,
            file_name=filename,
            mime="application/json",
            key=key,
            width="stretch",
        )
    except Exception as exc:
        st.error(f"Could not serialise session: {exc}")


def session_upload_widget(key: str = "session_upload") -> dict | None:
    """Render a Streamlit file uploader that returns the loaded calc_state dict.

    Returns None if no file is uploaded or loading fails.
    """
    import streamlit as st  # noqa: PLC0415

    uploaded = st.file_uploader(
        "Load a saved session (.shieldlab)",
        type=["shieldlab", "json"],
        key=key,
        help="Upload a .shieldlab session file to restore a previous calculation.",
    )
    if uploaded is None:
        return None

    try:
        cs = load_session(uploaded.read())
        st.success(f"Session loaded: {cs.get('mat_name', 'unknown material')}")
        return cs
    except (ValueError, json.JSONDecodeError) as exc:
        st.error(f"Could not load session: {exc}")
        return None
