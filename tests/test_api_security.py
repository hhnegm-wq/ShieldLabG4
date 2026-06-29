"""Tests for api.security."""
from __future__ import annotations

import hashlib
import os

import pytest
from fastapi import HTTPException

from api.security import RateLimiter, allowed_origins, verify_api_key


@pytest.mark.unit
def test_allowed_origins_default_localhost(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SHIELDLAB_CORS_ORIGINS", raising=False)
    monkeypatch.delenv("SHIELDLAB_DEV", raising=False)
    out = allowed_origins()
    assert all(o.startswith("http://localhost") or o.startswith("http://127.") for o in out)


@pytest.mark.unit
def test_allowed_origins_wildcard_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHIELDLAB_CORS_ORIGINS", "*")
    monkeypatch.delenv("SHIELDLAB_DEV", raising=False)
    with pytest.raises(RuntimeError):
        allowed_origins()


@pytest.mark.unit
def test_allowed_origins_wildcard_allowed_in_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHIELDLAB_CORS_ORIGINS", "*")
    monkeypatch.setenv("SHIELDLAB_DEV", "1")
    assert allowed_origins() == ["*"]


@pytest.mark.unit
def test_verify_api_key_missing_raises() -> None:
    with pytest.raises(HTTPException) as exc:
        verify_api_key(None)
    assert exc.value.status_code == 401


@pytest.mark.unit
def test_verify_api_key_unconfigured_in_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SHIELDLAB_API_KEYS", raising=False)
    monkeypatch.delenv("SHIELDLAB_API_KEY_HASHES", raising=False)
    monkeypatch.delenv("SHIELDLAB_DEV", raising=False)
    with pytest.raises(HTTPException) as exc:
        verify_api_key("anything")
    assert exc.value.status_code == 503


@pytest.mark.unit
def test_verify_api_key_accepts_hashed_key(monkeypatch: pytest.MonkeyPatch) -> None:
    key = "secret-test-key"
    monkeypatch.setenv(
        "SHIELDLAB_API_KEY_HASHES",
        hashlib.sha256(key.encode()).hexdigest(),
    )
    monkeypatch.delenv("SHIELDLAB_API_KEYS", raising=False)
    fp = verify_api_key(key)
    assert isinstance(fp, str) and len(fp) == 12


@pytest.mark.unit
def test_verify_api_key_rejects_wrong_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHIELDLAB_API_KEYS", "good-key")
    monkeypatch.delenv("SHIELDLAB_API_KEY_HASHES", raising=False)
    with pytest.raises(HTTPException) as exc:
        verify_api_key("bad-key")
    assert exc.value.status_code == 401


@pytest.mark.unit
def test_rate_limiter_blocks_after_limit() -> None:
    rl = RateLimiter(requests_per_minute=3)
    for _ in range(3):
        rl.hit("k")
    with pytest.raises(HTTPException) as exc:
        rl.hit("k")
    assert exc.value.status_code == 429
