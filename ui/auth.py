"""Tier / authentication for ShieldLab G4.

Resolution order (first match wins):
    1. Supabase user session (real hosted user accounts; preferred for shared/public deployments)
    2. ``SHIELDLAB_LICENSE_KEY`` environment variable - SHA-256 hash compared against
         the ``SHIELDLAB_PRO_KEY_HASH`` environment variable (self-hosted Pro deployments).
    3. JWT bearer token in ``st.session_state["_jwt_token"]`` - validated against
         ``SHIELDLAB_JWT_SECRET`` env var (generic cloud/JWT deployments).
    4. ``st.session_state["_tier"]`` manual override - dev/testing only.
    5. Default: ``"free"``.

Supabase mode is enabled when both ``SHIELDLAB_SUPABASE_URL`` and
``SHIELDLAB_SUPABASE_ANON_KEY`` are set. The user's tier/role are sourced from:
    - ``user.app_metadata.tier`` / ``user.user_metadata.tier``
    - ``user.app_metadata.role`` / ``user.user_metadata.role``

Recommended values:
    - tier: ``free`` | ``pro``
    - role: ``viewer`` | ``operator`` | ``admin``
"""

from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import Any, Literal
import streamlit as st

TierType = Literal["free", "pro"]
RoleType = Literal["viewer", "operator", "admin"]


@dataclass(frozen=True)
class UserContext:
    email: str | None
    tier: TierType
    role: RoleType
    provider: str


_SUPABASE_SESSION_KEY = "_supabase_session"
_SUPABASE_NOTICE_KEY = "_supabase_notice"

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


def _supabase_enabled() -> bool:
    return bool(os.environ.get("SHIELDLAB_SUPABASE_URL", "").strip()) and bool(
        os.environ.get("SHIELDLAB_SUPABASE_ANON_KEY", "").strip()
    )


def _supabase_client():
    if not _supabase_enabled():
        return None
    try:
        from supabase import create_client  # type: ignore[import-not-found]
    except Exception:
        return None
    return create_client(
        os.environ["SHIELDLAB_SUPABASE_URL"],
        os.environ["SHIELDLAB_SUPABASE_ANON_KEY"],
    )


def _normalized_tier(value: str | None) -> TierType:
    return "pro" if str(value or "").strip().lower() == "pro" else "free"


def _normalized_role(value: str | None) -> RoleType:
    lowered = str(value or "viewer").strip().lower()
    if lowered in {"admin", "operator", "viewer"}:
        return lowered  # type: ignore[return-value]
    return "viewer"


def _context_from_supabase_user(user: Any) -> UserContext | None:
    if user is None:
        return None
    app_meta = getattr(user, "app_metadata", None) or {}
    user_meta = getattr(user, "user_metadata", None) or {}
    email = getattr(user, "email", None)
    tier = _normalized_tier(app_meta.get("tier") or user_meta.get("tier"))
    role = _normalized_role(app_meta.get("role") or user_meta.get("role"))
    # Admin/operator accounts implicitly unlock Pro UI capability.
    if role in {"admin", "operator"} and tier == "free":
        tier = "pro"
    return UserContext(email=email, tier=tier, role=role, provider="supabase")


def _store_supabase_session(session: Any) -> None:
    if session is None:
        st.session_state.pop(_SUPABASE_SESSION_KEY, None)
        return
    st.session_state[_SUPABASE_SESSION_KEY] = {
        "access_token": getattr(session, "access_token", None),
        "refresh_token": getattr(session, "refresh_token", None),
    }


def _load_supabase_context() -> UserContext | None:
    client = _supabase_client()
    if client is None:
        return None

    data = st.session_state.get(_SUPABASE_SESSION_KEY) or {}
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    if not access_token or not refresh_token:
        return None

    try:
        client.auth.set_session(access_token, refresh_token)
        auth_user = client.auth.get_user()
        user = getattr(auth_user, "user", None) or auth_user
        return _context_from_supabase_user(user)
    except Exception:
        st.session_state.pop(_SUPABASE_SESSION_KEY, None)
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
    supabase_ctx = _load_supabase_context()
    if supabase_ctx is not None:
        return supabase_ctx.tier

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


def get_user_role() -> RoleType:
    supabase_ctx = _load_supabase_context()
    if supabase_ctx is not None:
        return supabase_ctx.role
    return "viewer"


def get_user_context() -> UserContext:
    supabase_ctx = _load_supabase_context()
    if supabase_ctx is not None:
        return supabase_ctx
    return UserContext(email=None, tier=get_user_tier(), role=get_user_role(), provider="local")


def render_auth_sidebar() -> None:
    """Render real-user auth controls for hosted deployments.

    Supabase mode is optional; when disabled the current local/self-hosted tier
    model remains active and no hosted-auth UI is shown.
    """
    if not _supabase_enabled():
        return

    client = _supabase_client()
    if client is None:
        st.sidebar.warning("Supabase auth requested, but the `supabase` package is not installed.")
        return

    ctx = _load_supabase_context()
    st.sidebar.divider()
    st.sidebar.caption("Account")

    notice = st.session_state.pop(_SUPABASE_NOTICE_KEY, None)
    if notice:
        level, text = notice
        getattr(st.sidebar, level)(text)

    if ctx is not None:
        st.sidebar.markdown(f"**{ctx.email or 'Signed in'}**")
        st.sidebar.caption(f"Role: {ctx.role} · Tier: {ctx.tier}")
        if st.sidebar.button("Sign out", key="supabase_sign_out_btn", width="stretch"):
            try:
                client.auth.sign_out()
            except Exception:
                pass
            _store_supabase_session(None)
            st.rerun()
        return

    with st.sidebar.form("supabase_login_form"):
        email = st.text_input("Email", key="supabase_email")
        password = st.text_input("Password", type="password", key="supabase_password")
        c_login, c_signup = st.columns(2)
        login_clicked = c_login.form_submit_button("Sign in", width="stretch")
        signup_clicked = c_signup.form_submit_button("Create account", width="stretch")
        reset_clicked = st.form_submit_button("Send password reset email", width="stretch")

    try:
        if login_clicked:
            auth = client.auth.sign_in_with_password({"email": email, "password": password})
            _store_supabase_session(getattr(auth, "session", None))
            st.session_state[_SUPABASE_NOTICE_KEY] = ("success", "Signed in successfully.")
            st.rerun()
        if signup_clicked:
            client.auth.sign_up({"email": email, "password": password})
            st.session_state[_SUPABASE_NOTICE_KEY] = (
                "success",
                "Account created. Check your email if confirmation is required.",
            )
            st.rerun()
        if reset_clicked:
            redirect_to = os.environ.get("SHIELDLAB_SUPABASE_REDIRECT_TO", "") or None
            client.auth.reset_password_email(email, {"redirect_to": redirect_to} if redirect_to else {})
            st.session_state[_SUPABASE_NOTICE_KEY] = ("success", "Password reset email sent.")
            st.rerun()
    except Exception as exc:
        st.sidebar.error(f"Authentication error: {exc}")


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


def get_tier() -> TierType:
    """Backward-compatible alias used by the shell label in ui/app.py."""
    return get_user_tier()

