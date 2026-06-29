"""Per-tenant (per-API-key) quota enforcement middleware.

Phase 2.5: sliding-window job-submission and CPU-minute quotas.

Two independent counters are tracked per API key:

1. **Job quota** – maximum number of job submissions per rolling window
   (default: 100 jobs / 24 hours).
2. **CPU-budget** – maximum accumulated CPU minutes per rolling window
   (default: 500 CPU-minutes / 24 hours). The middleware charges the
   *estimated* CPU cost at submission time; actual cost is not tracked
   in this layer (swap for a Redis-backed store for multi-replica accuracy).

On quota exhaustion the middleware returns HTTP 429 with a JSON body and a
``Retry-After`` header (seconds until the oldest entry in the sliding window
expires).

Protected paths are configured via ``SHIELDLAB_QUOTA_PATHS`` (comma-separated,
default: ``/api/v1/jobs/submit``). The middleware is no-op on all other paths.

Environment variables
---------------------
SHIELDLAB_QUOTA_PATHS
    Comma-separated list of URL paths that are quota-gated.
    Default: "/api/v1/jobs/submit"

SHIELDLAB_QUOTA_JOBS_PER_DAY
    Maximum job submissions per API key per 24-hour rolling window.
    Default: 100

SHIELDLAB_QUOTA_CPU_MINUTES_PER_DAY
    Maximum CPU-minutes per API key per 24-hour rolling window.
    Default: 500

SHIELDLAB_QUOTA_WINDOW_SECONDS
    Rolling window length in seconds (default: 86400 = 24 hours).

SHIELDLAB_QUOTA_ENABLED
    Set to "0" to disable quota enforcement entirely.

Notes
-----
* Thread-safe with a per-key ``threading.Lock`` via a ``defaultdict``.
* For multi-replica / container deployments replace ``_InMemoryQuotaStore``
  with a Redis-backed implementation that satisfies the same ``QuotaStore``
  protocol (atomic INCR + EXPIRE).
"""
from __future__ import annotations

import logging
import math
import os
import threading
import time
from collections import defaultdict
from typing import Callable, Protocol

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _quota_paths() -> frozenset[str]:
    raw = os.environ.get("SHIELDLAB_QUOTA_PATHS", "/api/v1/jobs/submit")
    return frozenset(p.strip() for p in raw.split(",") if p.strip())


# ---------------------------------------------------------------------------
# Protocol / store interface  (swap implementation for Redis etc.)
# ---------------------------------------------------------------------------

class QuotaStore(Protocol):
    def record_and_check_jobs(
        self, key: str, window_seconds: int, max_jobs: int
    ) -> tuple[bool, int]:
        """Record one job hit for *key*.

        Returns (allowed: bool, retry_after_seconds: int).
        ``retry_after_seconds`` is 0 when allowed.
        """

    def record_and_check_cpu(
        self, key: str, window_seconds: int, max_cpu_minutes: float, cost_minutes: float
    ) -> tuple[bool, int]:
        """Record *cost_minutes* of CPU for *key*.

        Returns (allowed: bool, retry_after_seconds: int).
        """


# ---------------------------------------------------------------------------
# In-memory sliding-window store
# ---------------------------------------------------------------------------

class _InMemoryQuotaStore:
    """Sliding-window rate store backed by in-process deques.

    Each entry is a ``(timestamp, cost)`` tuple. Entries older than the
    window are pruned on every access.
    """

    def __init__(self) -> None:
        # key → list of (ts_float, cost_float)
        self._jobs: dict[str, list[tuple[float, float]]] = defaultdict(list)
        self._cpu: dict[str, list[tuple[float, float]]] = defaultdict(list)
        self._lock: dict[str, threading.Lock] = defaultdict(threading.Lock)

    def _prune(self, entries: list, window_seconds: int, now: float) -> None:
        cutoff = now - window_seconds
        while entries and entries[0][0] < cutoff:
            entries.pop(0)

    def record_and_check_jobs(
        self, key: str, window_seconds: int, max_jobs: int
    ) -> tuple[bool, int]:
        now = time.monotonic()
        with self._lock[key]:
            entries = self._jobs[key]
            self._prune(entries, window_seconds, now)
            current_count = len(entries)
            if current_count >= max_jobs:
                # Retry-after = when the oldest entry expires
                oldest_ts = entries[0][0]
                retry_after = math.ceil(oldest_ts + window_seconds - now)
                return False, max(retry_after, 1)
            entries.append((now, 1.0))
            return True, 0

    def record_and_check_cpu(
        self, key: str, window_seconds: int, max_cpu_minutes: float, cost_minutes: float
    ) -> tuple[bool, int]:
        now = time.monotonic()
        with self._lock[key]:
            entries = self._cpu[key]
            self._prune(entries, window_seconds, now)
            current_cost = sum(e[1] for e in entries)
            if current_cost + cost_minutes > max_cpu_minutes:
                oldest_ts = entries[0][0] if entries else now
                retry_after = math.ceil(oldest_ts + window_seconds - now)
                return False, max(retry_after, 1)
            entries.append((now, cost_minutes))
            return True, 0


# Module-level shared store (one instance for the process lifetime)
_store = _InMemoryQuotaStore()


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class QuotaMiddleware(BaseHTTPMiddleware):
    """Enforce per-API-key job and CPU-minute quotas on protected paths.

    The API key is extracted from the ``X-API-Key`` request header (same
    header used by ``verify_api_key`` in security.py). Requests without an
    API key are not quota-checked (authentication failures are handled by
    the route handler).
    """

    def __init__(self, app, *, store: QuotaStore | None = None) -> None:
        super().__init__(app)
        self._store: QuotaStore = store or _store
        self._protected = _quota_paths()
        self._window = _env_int("SHIELDLAB_QUOTA_WINDOW_SECONDS", 86_400)
        self._max_jobs = _env_int("SHIELDLAB_QUOTA_JOBS_PER_DAY", 100)
        self._max_cpu = _env_int("SHIELDLAB_QUOTA_CPU_MINUTES_PER_DAY", 500)
        self._enabled = os.environ.get("SHIELDLAB_QUOTA_ENABLED", "1").lower() not in {
            "0", "false", "no"
        }

    # Estimated CPU cost per job submission (minutes). Replace with a
    # real estimator that reads particle count / geometry complexity.
    _DEFAULT_CPU_COST_MINUTES: float = 5.0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self._enabled or request.url.path not in self._protected:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key", "").strip()
        if not api_key:
            # No key → let the route handler reject with 401
            return await call_next(request)

        # --- job-count quota ---
        allowed, retry_after = self._store.record_and_check_jobs(
            api_key, self._window, self._max_jobs
        )
        if not allowed:
            logger.warning(
                "Quota exceeded (jobs): key=%.8s… retry_after=%ds", api_key, retry_after
            )
            return self._quota_response("job_quota_exceeded", retry_after)

        # --- CPU-minute quota ---
        allowed, retry_after = self._store.record_and_check_cpu(
            api_key,
            self._window,
            float(self._max_cpu),
            self._DEFAULT_CPU_COST_MINUTES,
        )
        if not allowed:
            logger.warning(
                "Quota exceeded (cpu): key=%.8s… retry_after=%ds", api_key, retry_after
            )
            return self._quota_response("cpu_quota_exceeded", retry_after)

        return await call_next(request)

    @staticmethod
    def _quota_response(reason: str, retry_after: int) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "quota_exceeded",
                "reason": reason,
                "retry_after_seconds": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )
