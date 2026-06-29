"""OpenTelemetry tracing bootstrap for the ShieldLab G4 API.

Phase 2.4: distributed tracing with correlation-ID propagation.

Every inbound HTTP request receives a ``X-Correlation-Id`` response header
(echoed from the request header, or auto-generated as a UUID4). A new OTel
span is opened for the request and the correlation ID is attached as an
attribute. Structured JSON log records include the correlation ID so that
logs, traces, and Azure Monitor Application Insights queries can be
correlated across the API → worker boundary.

Environment variables
---------------------
OTEL_EXPORTER_OTLP_ENDPOINT
    OTLP endpoint (e.g. "http://otel-collector:4317"). If absent, a
    ``ConsoleSpanExporter`` is used so local development always has traces
    without extra infrastructure.

APPLICATIONINSIGHTS_CONNECTION_STRING
    Azure Monitor connection string. When set the Azure Monitor exporter is
    used in addition to (or instead of) the OTLP exporter. This is the
    recommended path for Azure-hosted deployments.

OTEL_SERVICE_NAME
    Service name attached to every span (default: "shieldlab-api").

SHIELDLAB_OTEL_ENABLED
    Set to "0" to disable OTel entirely (useful for unit tests).
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

_OTEL_AVAILABLE = False
_tracer = None

# ---------------------------------------------------------------------------
# Optional OTel import – gracefully disabled when SDK is not installed
# ---------------------------------------------------------------------------

def _try_init_otel() -> None:
    global _OTEL_AVAILABLE, _tracer  # noqa: PLW0603

    if os.environ.get("SHIELDLAB_OTEL_ENABLED", "1").lower() in {"0", "false", "no"}:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        service_name = os.environ.get("OTEL_SERVICE_NAME", "shieldlab-api")
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)

        _exporter_added = False

        # Azure Monitor exporter (preferred for cloud deployments)
        ai_conn = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
        if ai_conn:
            try:
                from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

                az_exporter = AzureMonitorTraceExporter(connection_string=ai_conn)
                provider.add_span_processor(BatchSpanProcessor(az_exporter))
                _exporter_added = True
                logger.info("OTel: Azure Monitor exporter configured")
            except ImportError:
                logger.warning(
                    "OTel: azure-monitor-opentelemetry-exporter not installed; "
                    "skipping Azure Monitor exporter"
                )

        # OTLP exporter (gRPC, for local collectors / Jaeger / Tempo)
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        if otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )

                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                _exporter_added = True
                logger.info("OTel: OTLP exporter configured → %s", otlp_endpoint)
            except ImportError:
                logger.warning(
                    "OTel: opentelemetry-exporter-otlp-proto-grpc not installed; "
                    "skipping OTLP exporter"
                )

        # Console exporter fallback (always on in dev when no other exporter is wired)
        if not _exporter_added:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
            logger.info("OTel: Console exporter active (dev/local mode)")

        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(service_name)
        _OTEL_AVAILABLE = True
        logger.info("OTel: tracing initialised (service=%s)", service_name)

    except ImportError:
        logger.info(
            "OTel: opentelemetry-sdk not installed; tracing disabled. "
            "Install opentelemetry-sdk to enable distributed tracing."
        )


_try_init_otel()


# ---------------------------------------------------------------------------
# Correlation-ID + span middleware
# ---------------------------------------------------------------------------

_CORRELATION_HEADER = "X-Correlation-Id"


class TracingMiddleware(BaseHTTPMiddleware):
    """Attach a correlation ID to every request/response and open an OTel span.

    * Reads ``X-Correlation-Id`` from the incoming request headers.
    * Falls back to a fresh UUID4 when the header is absent.
    * Sets ``request.state.correlation_id`` so route handlers can log it.
    * Adds the correlation ID to the response headers.
    * When OTel is available, wraps the request in a named span with
      ``http.method``, ``http.route``, ``http.status_code``, and
      ``correlation_id`` attributes.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get(_CORRELATION_HEADER) or str(uuid4())
        request.state.correlation_id = correlation_id

        if _OTEL_AVAILABLE and _tracer is not None:
            from opentelemetry import trace
            from opentelemetry.trace import StatusCode

            span_name = f"{request.method} {request.url.path}"
            with _tracer.start_as_current_span(span_name) as span:
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.route", str(request.url.path))
                span.set_attribute("correlation_id", correlation_id)
                try:
                    response = await call_next(request)
                    span.set_attribute("http.status_code", response.status_code)
                    if response.status_code >= 500:
                        span.set_status(StatusCode.ERROR)
                    else:
                        span.set_status(StatusCode.OK)
                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(StatusCode.ERROR, str(exc))
                    raise
                response.headers[_CORRELATION_HEADER] = correlation_id
                return response
        else:
            response = await call_next(request)
            response.headers[_CORRELATION_HEADER] = correlation_id
            return response


# ---------------------------------------------------------------------------
# Structured JSON logging helper
# ---------------------------------------------------------------------------

class _CorrelationFilter(logging.Filter):
    """Inject ``correlation_id`` into every log record (falls back to '-')."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "-"
        return True


def configure_json_logging(level: int = logging.INFO) -> None:
    """Configure root logger to emit structured JSON lines.

    Each record includes: timestamp, level, logger, correlation_id, message.
    Call once at application startup (e.g. in the FastAPI lifespan).
    """
    import json as _json
    import traceback as _tb

    class _JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload: dict = {
                "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                "level": record.levelname,
                "logger": record.name,
                "correlation_id": getattr(record, "correlation_id", "-"),
                "msg": record.getMessage(),
            }
            if record.exc_info:
                payload["exc"] = "".join(_tb.format_exception(*record.exc_info))
            return _json.dumps(payload)

    root = logging.getLogger()
    if root.handlers:
        root.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    handler.addFilter(_CorrelationFilter())
    root.setLevel(level)
    root.addHandler(handler)
