"""Authentication, CORS, and rate-limiting helpers for the ShieldLab G4 API.

Phase 0 hardening (replaces the prior stub that accepted any non-empty key):

- Real API-key verification against either:
    * ``SHIELDLAB_API_KEYS`` env var (comma-separated) for self-hosted deployments
    * ``SHIELDLAB_API_KEY_HASHES`` env var (comma-separated SHA-256 hex digests)
      for production deployments where plaintext keys must not appear in env.
- Constant-time comparison to prevent timing oracles.
- ``allowed_origins()`` resolves a strict CORS allowlist from ``SHIELDLAB_CORS_ORIGINS``
  (comma-separated). Wildcard ``*`` is rejected unless ``SHIELDLAB_DEV=1``.
- ``RateLimiter`` is a dependency-free, in-memory token-bucket. For multi-replica
  deployments, swap it for Redis (interface preserved).

Environment variables:
    SHIELDLAB_API_KEYS              "key1,key2"  (dev/self-hosted only)
    SHIELDLAB_API_KEY_HASHES        "<sha256>,<sha256>"  (production)
    SHIELDLAB_CORS_ORIGINS          "https://app.example.com,https://admin.example.com"
    SHIELDLAB_RATE_LIMIT_PER_MIN    "60"  (per API key)
    SHIELDLAB_DEV                   "1" enables wildcard CORS + dev fallbacks
"""
from __future__ import annotations

import hashlib
import hmac
import os
import threading
import time
from collections import defaultdict
from typing import Iterable

from fastapi import HTTPException


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

def _is_dev() -> bool:
    return os.environ.get("SHIELDLAB_DEV", "").lower() in {"1", "true", "yes"}


def allowed_origins() -> list[str]:
    """Return the CORS allowlist. Refuses wildcard outside dev mode."""
    raw = os.environ.get("SHIELDLAB_CORS_ORIGINS", "").strip()
    if not raw:
        # Safe defaults: localhost only.
        return [
            "http://localhost:8501",
            "http://127.0.0.1:8501",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if "*" in origins and not _is_dev():
        raise RuntimeError(
            "SHIELDLAB_CORS_ORIGINS=* is forbidden outside SHIELDLAB_DEV=1. "
            "Set explicit origins instead."
        )
    return origins


# ---------------------------------------------------------------------------
# API key verification
# ---------------------------------------------------------------------------

def _load_key_hashes() -> set[str]:
    hashes: set[str] = set()
    raw_hashes = os.environ.get("SHIELDLAB_API_KEY_HASHES", "").strip()
    if raw_hashes:
        for h in raw_hashes.split(","):
            h = h.strip().lower()
            if len(h) == 64 and all(c in "0123456789abcdef" for c in h):
                hashes.add(h)
    raw_keys = os.environ.get("SHIELDLAB_API_KEYS", "").strip()
    if raw_keys:
        for k in raw_keys.split(","):
            k = k.strip()
            if k:
                hashes.add(hashlib.sha256(k.encode("utf-8")).hexdigest())
    return hashes


def verify_api_key(x_api_key: str | None) -> str:
    """Verify the supplied API key. Returns the matched key fingerprint (sha256[:12]).

    Raises 401 on missing/invalid key. Raises 503 if the server has no keys configured
    in production (dev mode falls back to accepting any non-empty key with a warning).
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header.",
        )
    configured = _load_key_hashes()
    if not configured:
        if _is_dev():
            return "dev-mode-accepted"
        raise HTTPException(
            status_code=503,
            detail=(
                "API key authentication is not configured on this server. "
                "Set SHIELDLAB_API_KEY_HASHES or SHIELDLAB_API_KEYS."
            ),
        )
    digest = hashlib.sha256(x_api_key.encode("utf-8")).hexdigest()
    for expected in configured:
        if hmac.compare_digest(digest, expected):
            return digest[:12]
    raise HTTPException(status_code=401, detail="Invalid API key.")


# ---------------------------------------------------------------------------
# Rate limiting (in-memory token bucket; swap for Redis in multi-replica)
# ---------------------------------------------------------------------------

class RateLimiter:
    """Per-key sliding window limiter. Thread-safe."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.limit = max(1, int(requests_per_minute))
        self.window_s = 60.0
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def hit(self, key: str) -> None:
        now = time.monotonic()
        cutoff = now - self.window_s
        with self._lock:
            bucket = self._hits[key]
            # Drop expired
            i = 0
            for i, ts in enumerate(bucket):
                if ts >= cutoff:
                    break
            else:
                i = len(bucket)
            del bucket[:i]
            if len(bucket) >= self.limit:
                retry_in = max(0.0, self.window_s - (now - bucket[0]))
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Retry in {retry_in:.1f}s.",
                    headers={"Retry-After": str(int(retry_in) + 1)},
                )
            bucket.append(now)


def default_rate_limiter() -> RateLimiter:
    rpm = int(os.environ.get("SHIELDLAB_RATE_LIMIT_PER_MIN", "60"))
    return RateLimiter(rpm)


def global_rate_limiter() -> RateLimiter:
    """Per-client-IP limiter applied to *every* request (authenticated or not).

    Defense-in-depth against L7 floods and credential brute-forcing: unlike the
    per-key limiter, this throttles unauthenticated and failed-auth traffic too.
    Tune with ``SHIELDLAB_GLOBAL_RATE_LIMIT_PER_MIN`` (default 120/min per IP).
    """
    rpm = int(os.environ.get("SHIELDLAB_GLOBAL_RATE_LIMIT_PER_MIN", "120"))
    return RateLimiter(rpm)


def _trust_proxy() -> bool:
    return os.environ.get("SHIELDLAB_TRUST_PROXY", "").lower() in {"1", "true", "yes"}


def client_ip(scope_client: tuple | None, x_forwarded_for: str | None) -> str:
    """Resolve the client IP used for rate limiting.

    When ``SHIELDLAB_TRUST_PROXY`` is set (the app runs behind a trusted reverse
    proxy such as Caddy), the left-most ``X-Forwarded-For`` hop is trusted.
    Otherwise the socket peer address is used, so a client cannot spoof its IP
    with a forged header when the app is exposed directly.
    """
    if _trust_proxy() and x_forwarded_for:
        first = x_forwarded_for.split(",")[0].strip()
        if first:
            return first
    if scope_client:
        return scope_client[0]
    return "unknown"


__all__ = [
    "allowed_origins",
    "verify_api_key",
    "RateLimiter",
    "default_rate_limiter",
    "global_rate_limiter",
    "client_ip",
]
