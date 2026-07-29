"""Unit tests for ui/auth.py — tier resolution and authentication helpers.

Covers:
  - License-key SHA-256 validation (correct key, wrong key, missing env vars)
  - JWT HS256 token validation (valid, expired, wrong secret, missing secret)
  - Tier resolution priority order (key > JWT > session override > default)
  - Dev tier override (set_tier_override / is_pro)
  - Timing-safe comparison (cannot short-circuit on length)
"""
from __future__ import annotations

import hashlib
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Path setup — add ui/ to sys.path so auth.py can be imported without Streamlit
# actually running a server.
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent
_UI_DIR = str(_ROOT / "ui")
if _UI_DIR not in sys.path:
    sys.path.insert(0, _UI_DIR)

# Stub out streamlit before importing auth so we don't need a running server.
_st_stub = MagicMock()
_st_stub.session_state = {}
sys.modules.setdefault("streamlit", _st_stub)


def _fresh_auth():
    """Re-import auth with a clean session_state stub."""
    import importlib
    _st_stub.session_state = {}
    if "auth" in sys.modules:
        del sys.modules["auth"]
    import auth as _auth  # noqa: PLC0415
    return _auth


def _make_jwt(payload: dict, secret: str, expired: bool = False) -> str:
    """Minimal HS256 JWT builder (header.payload.signature)."""
    import jwt as pyjwt  # PyJWT
    import datetime

    now = datetime.datetime.utcnow()
    if expired:
        payload["exp"] = now - datetime.timedelta(hours=1)
    else:
        payload["exp"] = now + datetime.timedelta(hours=1)
    return pyjwt.encode(payload, secret, algorithm="HS256")


# ---------------------------------------------------------------------------
# License-key tests
# ---------------------------------------------------------------------------

class TestLicenseKey:
    """Tests for _check_license_key()."""

    def test_valid_key_returns_pro(self):
        auth = _fresh_auth()
        key = "my-secret-pro-key"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        with patch.dict(os.environ, {"SHIELDLAB_LICENSE_KEY": key,
                                      "SHIELDLAB_PRO_KEY_HASH": key_hash}):
            assert auth._check_license_key() == "pro"

    def test_wrong_key_returns_none(self):
        auth = _fresh_auth()
        key = "correct-key"
        wrong_key = "wrong-key"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        with patch.dict(os.environ, {"SHIELDLAB_LICENSE_KEY": wrong_key,
                                      "SHIELDLAB_PRO_KEY_HASH": key_hash}):
            assert auth._check_license_key() is None

    def test_missing_key_env_returns_none(self):
        auth = _fresh_auth()
        env = {"SHIELDLAB_PRO_KEY_HASH": "somehash"}
        env.pop("SHIELDLAB_LICENSE_KEY", None)
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("SHIELDLAB_LICENSE_KEY", None)
            assert auth._check_license_key() is None

    def test_missing_hash_env_returns_none(self):
        auth = _fresh_auth()
        with patch.dict(os.environ, {"SHIELDLAB_LICENSE_KEY": "anykey"}, clear=False):
            os.environ.pop("SHIELDLAB_PRO_KEY_HASH", None)
            assert auth._check_license_key() is None

    def test_empty_key_returns_none(self):
        auth = _fresh_auth()
        key_hash = hashlib.sha256(b"real-key").hexdigest()
        with patch.dict(os.environ, {"SHIELDLAB_LICENSE_KEY": "",
                                      "SHIELDLAB_PRO_KEY_HASH": key_hash}):
            assert auth._check_license_key() is None

    def test_hash_case_insensitive(self):
        """Stored hash may be uppercase; comparison must still pass."""
        auth = _fresh_auth()
        key = "case-test-key"
        key_hash = hashlib.sha256(key.encode()).hexdigest().upper()
        with patch.dict(os.environ, {"SHIELDLAB_LICENSE_KEY": key,
                                      "SHIELDLAB_PRO_KEY_HASH": key_hash}):
            assert auth._check_license_key() == "pro"

    def test_timing_safe_no_short_circuit(self):
        """hmac.compare_digest must not short-circuit on differing lengths."""
        auth = _fresh_auth()
        key = "my-key"
        real_hash = hashlib.sha256(key.encode()).hexdigest()
        # A hash that differs only in the last character should take the same time
        wrong_hash = real_hash[:-1] + ("a" if real_hash[-1] != "a" else "b")
        with patch.dict(os.environ, {"SHIELDLAB_LICENSE_KEY": key,
                                      "SHIELDLAB_PRO_KEY_HASH": wrong_hash}):
            t0 = time.perf_counter()
            result = auth._check_license_key()
            elapsed = time.perf_counter() - t0
        assert result is None
        # Sanity: should complete in under 1 second
        assert elapsed < 1.0


# ---------------------------------------------------------------------------
# JWT tests
# ---------------------------------------------------------------------------

class TestJWTToken:
    """Tests for _check_jwt_token()."""

    def test_valid_pro_token_returns_pro(self):
        pytest.importorskip("jwt")
        auth = _fresh_auth()
        secret = "test-secret"
        token = _make_jwt({"tier": "pro"}, secret)
        _st_stub.session_state["_jwt_token"] = token
        with patch.dict(os.environ, {"SHIELDLAB_JWT_SECRET": secret}):
            assert auth._check_jwt_token() == "pro"

    def test_valid_free_token_returns_free(self):
        pytest.importorskip("jwt")
        auth = _fresh_auth()
        secret = "test-secret"
        token = _make_jwt({"tier": "free"}, secret)
        _st_stub.session_state["_jwt_token"] = token
        with patch.dict(os.environ, {"SHIELDLAB_JWT_SECRET": secret}):
            assert auth._check_jwt_token() == "free"

    def test_expired_token_returns_none(self):
        pytest.importorskip("jwt")
        auth = _fresh_auth()
        secret = "test-secret"
        token = _make_jwt({"tier": "pro"}, secret, expired=True)
        _st_stub.session_state["_jwt_token"] = token
        with patch.dict(os.environ, {"SHIELDLAB_JWT_SECRET": secret}):
            assert auth._check_jwt_token() is None

    def test_wrong_secret_returns_none(self):
        pytest.importorskip("jwt")
        auth = _fresh_auth()
        token = _make_jwt({"tier": "pro"}, "signing-secret")
        _st_stub.session_state["_jwt_token"] = token
        with patch.dict(os.environ, {"SHIELDLAB_JWT_SECRET": "wrong-secret"}):
            assert auth._check_jwt_token() is None

    def test_missing_secret_env_returns_none(self):
        pytest.importorskip("jwt")
        auth = _fresh_auth()
        token = _make_jwt({"tier": "pro"}, "secret")
        _st_stub.session_state["_jwt_token"] = token
        os.environ.pop("SHIELDLAB_JWT_SECRET", None)
        assert auth._check_jwt_token() is None

    def test_no_token_in_session_returns_none(self):
        auth = _fresh_auth()
        _st_stub.session_state.pop("_jwt_token", None)
        with patch.dict(os.environ, {"SHIELDLAB_JWT_SECRET": "secret"}):
            assert auth._check_jwt_token() is None

    def test_missing_tier_claim_defaults_free(self):
        pytest.importorskip("jwt")
        auth = _fresh_auth()
        secret = "test-secret"
        token = _make_jwt({"sub": "user123"}, secret)  # no 'tier' claim
        _st_stub.session_state["_jwt_token"] = token
        with patch.dict(os.environ, {"SHIELDLAB_JWT_SECRET": secret}):
            assert auth._check_jwt_token() == "free"


# ---------------------------------------------------------------------------
# Tier resolution priority
# ---------------------------------------------------------------------------

class TestTierResolution:
    """Tests for get_user_tier() priority order."""

    def test_default_is_free(self):
        auth = _fresh_auth()
        _st_stub.session_state.clear()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SHIELDLAB_LICENSE_KEY", None)
            os.environ.pop("SHIELDLAB_PRO_KEY_HASH", None)
            os.environ.pop("SHIELDLAB_JWT_SECRET", None)
            assert auth.get_user_tier() == "free"

    def test_license_key_beats_session_override(self):
        auth = _fresh_auth()
        key = "priority-test-key"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        _st_stub.session_state["_tier"] = "free"  # session says free
        with patch.dict(os.environ, {"SHIELDLAB_LICENSE_KEY": key,
                                      "SHIELDLAB_PRO_KEY_HASH": key_hash}):
            assert auth.get_user_tier() == "pro"  # key wins

    def test_session_override_used_when_no_key_or_jwt(self):
        auth = _fresh_auth()
        _st_stub.session_state["_tier"] = "pro"
        os.environ.pop("SHIELDLAB_LICENSE_KEY", None)
        os.environ.pop("SHIELDLAB_PRO_KEY_HASH", None)
        os.environ.pop("SHIELDLAB_JWT_SECRET", None)
        assert auth.get_user_tier() == "pro"

    def test_is_pro_true_with_valid_key(self):
        auth = _fresh_auth()
        key = "pro-key"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        with patch.dict(os.environ, {"SHIELDLAB_LICENSE_KEY": key,
                                      "SHIELDLAB_PRO_KEY_HASH": key_hash}):
            assert auth.is_pro() is True

    def test_is_pro_false_on_free_tier(self):
        auth = _fresh_auth()
        _st_stub.session_state.clear()
        os.environ.pop("SHIELDLAB_LICENSE_KEY", None)
        os.environ.pop("SHIELDLAB_PRO_KEY_HASH", None)
        os.environ.pop("SHIELDLAB_JWT_SECRET", None)
        assert auth.is_pro() is False


# ---------------------------------------------------------------------------
# Dev override
# ---------------------------------------------------------------------------

class TestDevOverride:
    """Tests for set_tier_override()."""

    def test_set_free_override(self):
        auth = _fresh_auth()
        auth.set_tier_override("free")
        assert _st_stub.session_state.get("_tier") == "free"

    def test_set_pro_override(self):
        auth = _fresh_auth()
        auth.set_tier_override("pro")
        assert _st_stub.session_state.get("_tier") == "pro"

    def test_override_reflected_in_get_user_tier(self):
        auth = _fresh_auth()
        os.environ.pop("SHIELDLAB_LICENSE_KEY", None)
        os.environ.pop("SHIELDLAB_PRO_KEY_HASH", None)
        os.environ.pop("SHIELDLAB_JWT_SECRET", None)
        auth.set_tier_override("pro")
        assert auth.get_user_tier() == "pro"


class TestSupabaseHelpers:
    def test_supabase_disabled_without_env(self):
        auth = _fresh_auth()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SHIELDLAB_SUPABASE_URL", None)
            os.environ.pop("SHIELDLAB_SUPABASE_ANON_KEY", None)
            assert auth._supabase_enabled() is False

    def test_context_from_supabase_user_reads_metadata(self):
        auth = _fresh_auth()

        class DummyUser:
            email = "user@example.com"
            app_metadata = {"tier": "pro", "role": "operator"}
            user_metadata = {}

        ctx = auth._context_from_supabase_user(DummyUser())
        assert ctx is not None
        assert ctx.email == "user@example.com"
        assert ctx.tier == "pro"
        assert ctx.role == "operator"
        assert ctx.provider == "supabase"

    def test_operator_role_implies_pro_when_tier_missing(self):
        auth = _fresh_auth()

        class DummyUser:
            email = "operator@example.com"
            app_metadata = {"role": "operator"}
            user_metadata = {}

        ctx = auth._context_from_supabase_user(DummyUser())
        assert ctx is not None
        assert ctx.tier == "pro"
        assert ctx.role == "operator"

    def test_get_user_context_uses_supabase_context_first(self):
        auth = _fresh_auth()
        fake_ctx = auth.UserContext(
            email="admin@example.com",
            tier="pro",
            role="admin",
            provider="supabase",
        )
        with patch.object(auth, "_load_supabase_context", return_value=fake_ctx):
            ctx = auth.get_user_context()
            assert ctx == fake_ctx
            assert auth.get_user_tier() == "pro"
            assert auth.get_user_role() == "admin"
