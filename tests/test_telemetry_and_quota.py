"""Unit tests for Phase 2.4 (OpenTelemetry) and Phase 2.5 (per-tenant quota).

Middleware logic is tested directly without TestClient to avoid FastAPI-version
specific Router initialisation constraints (on_startup removal in FastAPI 0.116+).
"""
from __future__ import annotations

import time
import uuid

import pytest


# ---------------------------------------------------------------------------
# Phase 2.4 – telemetry module
# ---------------------------------------------------------------------------

class TestTelemetryModule:
    """api.telemetry imports cleanly and configures logging/correlation correctly."""

    def test_module_imports_without_error(self):
        import api.telemetry  # noqa: F401

    def test_tracing_middleware_class_is_callable(self):
        from api.telemetry import TracingMiddleware
        assert callable(TracingMiddleware)

    def test_configure_json_logging_installs_handler(self):
        import logging
        from api.telemetry import configure_json_logging

        configure_json_logging()
        root = logging.getLogger()
        assert root.handlers, "Root logger must have at least one handler"
        logging.getLogger("test.telemetry").info("smoke test")

    def test_correlation_filter_injects_default_value(self):
        """_CorrelationFilter sets correlation_id='-' when not already present."""
        import logging
        from api.telemetry import _CorrelationFilter

        f = _CorrelationFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello", args=(), exc_info=None,
        )
        f.filter(record)
        assert hasattr(record, "correlation_id")
        assert record.correlation_id == "-"

    def test_correlation_id_uuid4_format(self):
        """UUID4-generated correlation IDs are 36 chars with 4 hyphens."""
        cid = str(uuid.uuid4())
        assert len(cid) == 36
        assert cid.count("-") == 4

    def test_unique_correlation_ids(self):
        ids = {str(uuid.uuid4()) for _ in range(10)}
        assert len(ids) == 10

    def test_incoming_header_echoed_unchanged(self):
        """Middleware resolves header: use existing value when present."""
        from api.telemetry import _CORRELATION_HEADER
        headers = {_CORRELATION_HEADER: "my-trace-id-abc"}
        cid = headers.get(_CORRELATION_HEADER) or str(uuid.uuid4())
        assert cid == "my-trace-id-abc"

    def test_missing_header_generates_new_id(self):
        """When header is absent, a fresh UUID4 is generated."""
        from api.telemetry import _CORRELATION_HEADER
        headers: dict = {}
        cid = headers.get(_CORRELATION_HEADER) or str(uuid.uuid4())
        assert len(cid) == 36

    def test_dispatch_generates_correlation_header(self, monkeypatch):
        """Regression: TracingMiddleware.dispatch must run end-to-end.

        Previously the middleware called a bare ``uuid4()`` (never imported),
        raising ``NameError`` on *every* request. This test drives the real
        ``dispatch`` coroutine so that regression cannot recur.
        """
        import asyncio
        from starlette.requests import Request
        from starlette.responses import Response

        import api.telemetry as tel

        # Force the non-OTel branch for a deterministic, dependency-free path.
        monkeypatch.setattr(tel, "_OTEL_AVAILABLE", False, raising=False)
        monkeypatch.setattr(tel, "_tracer", None, raising=False)

        middleware = tel.TracingMiddleware(app=lambda scope, receive, send: None)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
        }
        request = Request(scope)

        async def call_next(_req):
            return Response("ok", status_code=200)

        response = asyncio.run(middleware.dispatch(request, call_next))

        assert response.status_code == 200
        assert tel._CORRELATION_HEADER in response.headers
        assert len(response.headers[tel._CORRELATION_HEADER]) == 36
        assert request.state.correlation_id == response.headers[tel._CORRELATION_HEADER]

    def test_dispatch_echoes_incoming_correlation_header(self, monkeypatch):
        """An inbound X-Correlation-Id is preserved on the response."""
        import asyncio
        from starlette.requests import Request
        from starlette.responses import Response

        import api.telemetry as tel

        monkeypatch.setattr(tel, "_OTEL_AVAILABLE", False, raising=False)
        monkeypatch.setattr(tel, "_tracer", None, raising=False)

        middleware = tel.TracingMiddleware(app=lambda scope, receive, send: None)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"x-correlation-id", b"trace-abc-123")],
            "query_string": b"",
        }
        request = Request(scope)

        async def call_next(_req):
            return Response("ok", status_code=200)

        response = asyncio.run(middleware.dispatch(request, call_next))
        assert response.headers[tel._CORRELATION_HEADER] == "trace-abc-123"



# ---------------------------------------------------------------------------
# Phase 2.5 – quota middleware
# ---------------------------------------------------------------------------

class TestInMemoryQuotaStore:
    """_InMemoryQuotaStore sliding-window logic (no ASGI / FastAPI required)."""

    def _store(self):
        from api.middleware.quota import _InMemoryQuotaStore
        return _InMemoryQuotaStore()

    def test_allows_within_limit(self):
        store = self._store()
        for _ in range(5):
            allowed, _ = store.record_and_check_jobs("k1", 60, 10)
            assert allowed

    def test_blocks_at_limit(self):
        store = self._store()
        for _ in range(10):
            store.record_and_check_jobs("k1", 60, 10)
        allowed, retry = store.record_and_check_jobs("k1", 60, 10)
        assert not allowed
        assert retry >= 1

    def test_different_keys_are_independent(self):
        store = self._store()
        for _ in range(10):
            store.record_and_check_jobs("key_a", 60, 10)
        allowed_a, _ = store.record_and_check_jobs("key_a", 60, 10)
        allowed_b, _ = store.record_and_check_jobs("key_b", 60, 10)
        assert not allowed_a
        assert allowed_b

    def test_cpu_budget_blocks_on_excess(self):
        store = self._store()
        # Budget=10 min, cost=6 min per call → 1st passes, 2nd blocked
        ok1, _ = store.record_and_check_cpu("k1", 60, 10.0, 6.0)
        ok2, retry = store.record_and_check_cpu("k1", 60, 10.0, 6.0)
        assert ok1
        assert not ok2
        assert retry >= 1

    def test_window_expiry_allows_again(self):
        """Inject a 2-second-old entry; with 1s window it is pruned → allowed."""
        store = self._store()
        key = "k_expiry"
        # Bypass record_and_check and inject directly to avoid timing dependency
        store._jobs[key].append((time.monotonic() - 2.0, 1.0))
        allowed, _ = store.record_and_check_jobs(key, 1, 1)
        assert allowed


class TestQuotaMiddlewareStatics:
    """QuotaMiddleware static helpers and store logic without an ASGI server."""

    def test_quota_response_status_429(self):
        from api.middleware.quota import QuotaMiddleware
        resp = QuotaMiddleware._quota_response("job_quota_exceeded", 3600)
        assert resp.status_code == 429

    def test_quota_response_retry_after_header(self):
        from api.middleware.quota import QuotaMiddleware
        resp = QuotaMiddleware._quota_response("job_quota_exceeded", 3600)
        assert resp.headers["retry-after"] == "3600"

    def test_quota_response_body_fields(self):
        import json
        from api.middleware.quota import QuotaMiddleware
        resp = QuotaMiddleware._quota_response("cpu_quota_exceeded", 120)
        body = json.loads(resp.body)
        assert body["reason"] == "cpu_quota_exceeded"
        assert body["retry_after_seconds"] == 120

    def test_default_protected_path(self):
        from api.middleware.quota import _quota_paths
        assert "/api/v1/jobs/submit" in _quota_paths()

    def test_env_int_returns_default_for_missing_var(self):
        from api.middleware.quota import _env_int
        assert _env_int("__SHIELDLAB_NONEXISTENT_9x7z__", 99) == 99

    def test_quota_exhaustion_blocks_101st_job(self):
        from api.middleware.quota import _InMemoryQuotaStore
        store = _InMemoryQuotaStore()
        for _ in range(100):
            store.record_and_check_jobs("testkey", 86_400, 100)
        allowed, retry = store.record_and_check_jobs("testkey", 86_400, 100)
        assert not allowed
        assert retry >= 1

    def test_quota_module_imports_without_error(self):
        import api.middleware.quota  # noqa: F401
