"""Tier / authentication for ShieldLab G4.

Tier resolution order (first match wins):
  1. ``SHIELDLAB_LICENSE_KEY`` environment variable - SHA-256 hash compared against
     the ``SHIELDLAB_PRO_KEY_HASH`` environment variable (self-hosted Pro deployments).
  2. JWT bearer token in ``st.session_state["_jwt_token"]`` - validated against
     ``SHIELDLAB_JWT_SECRET`` env var (cloud/Auth0/Clerk deployments, not yet wired).
  3. ``st.session_state["_tier"]`` manual override - dev/testing only.
  4. Default: ``"free"``.

To activate Pro for a self-hosted deployment:
    export SHIELDLAB_LICENSE_KEY="<your-key>"
    export SHIELDLAB_PRO_KEY_HASH="<sha256-of-your-key>"   # pre-hashed

Production cloud auth (Auth0 / Clerk):
    - Replace the JWT block with Auth0 SDK token verification.
    - Verify Stripe subscription status from ``/api/tier`` endpoint.
    - Store tier result in ``st.session_state["_tier"]`` after verification.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Literal
import streamlit as st

TierType = Literal["free", "pro"]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_license_key() -> TierType | None:
    """Check SHIELDLAB_LICENSE_KEY against the stored SHA-256 hash.

    Returns ``"pro"`` if valid, ``None`` otherwise.
    Both env vars must be set; the key is never stored in plain text server-side.
    """
    key = os.environ.get("SHIELDLAB_LICENSE_KEY", "").strip()
    expected_hash = os.environ.get("SHIELDLAB_PRO_KEY_HASH", "").strip()
    if not key or not expected_hash:
        return None
    # Constant-time comparison to prevent timing attacks
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    if hmac.compare_digest(key_hash, expected_hash.lower()):
        return "pro"
    return None


def _check_jwt_token() -> TierType | None:
    """Validate a JWT token stored in session state.

    Expects the JWT ``tier`` claim to contain ``"pro"`` or ``"free"``.
    The token is signed with HS256 using ``SHIELDLAB_JWT_SECRET``.

    For Auth0 / Entra production deployments, replace the ``jwt.decode`` call
    with the appropriate JWKS-backed RS256 verification:
        from jose import jwt as jose_jwt
        payload = jose_jwt.decode(token, JWKS, algorithms=["RS256"],
                                  audience=AUTH0_AUDIENCE)

    Returns ``"pro"`` | ``"free"`` | ``None`` (token absent/invalid/secret missing).
    """
    token: str = st.session_state.get("_jwt_token", "")
    if not token:
        return None
    jwt_secret = os.environ.get("SHIELDLAB_JWT_SECRET", "")
    if not jwt_secret:
        return None
    try:
        import jwt  # PyJWT
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"require": ["exp"]},
        )
        tier = payload.get("tier", "free")
        return "pro" if tier == "pro" else "free"
    except Exception:  # jwt.InvalidTokenError and any import error
        return None


# ---------------------------------------------------------------------------
# Tier resolution
# ---------------------------------------------------------------------------

def get_user_tier() -> TierType:
    """Return the current user's tier.

    Resolution order: license key env var ? JWT token ? session state override ? "free".
    """
    # 1. Self-hosted Pro via license key
    tier_from_key = _check_license_key()
    if tier_from_key is not None:
        return tier_from_key

    # 2. JWT / Auth0 / Clerk token
    tier_from_jwt = _check_jwt_token()
    if tier_from_jwt is not None:
        return tier_from_jwt  # type: ignore[return-value]

    # 3. Dev/test manual override
    return st.session_state.get("_tier", "free")  # type: ignore[return-value]


def set_tier_override(tier: TierType) -> None:
    """Dev helper - force the tier for the current session."""
    st.session_state["_tier"] = tier


def is_pro() -> bool:
    return get_user_tier() == "pro"


# ---------------------------------------------------------------------------
# Dev sidebar override (shown only in development mode)
# ---------------------------------------------------------------------------

def render_tier_dev_toggle() -> None:
    """Sidebar toggle for switching tier during development.

    Only shown when ``SHIELDLAB_DEV=1`` is set.  Never rendered in production.
    """
    if os.environ.get("SHIELDLAB_DEV", "").lower() in ("1", "true", "yes"):
        tier = get_user_tier()
        st.sidebar.divider()
        st.sidebar.caption("Dev: Tier Override")
        new_tier: TierType = st.sidebar.radio(  # type: ignore[assignment]
            "Tier",
            options=["free", "pro"],
            index=0 if tier == "free" else 1,
            horizontal=True,
            key="_tier_toggle",
            label_visibility="collapsed",
        )
        if new_tier != tier:
            set_tier_override(new_tier)
            st.rerun()

