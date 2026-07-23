"""Storage + queue abstraction for the ShieldLab G4 job pipeline.

Decouples the API (producer) and worker (consumer) from any single cloud so the
platform can run:

- **local / demo / free mode** — filesystem blobs + a SQLite queue, with **no
  external services**. Runs on any Linux VM (e.g. Oracle Cloud Always Free) or
  a laptop. This is the default when no Azure storage is configured.
- **Azure mode** — Azure Queue Storage + Blob Storage (production).

Backend selection (in order):
1. ``SHIELDLAB_BACKEND`` = ``local`` | ``azure``
2. auto-detect: ``azure`` if an Azure storage env var is set, else ``local``.

A future ``RedisBackend`` (or S3/MinIO) is a drop-in: implement
:class:`JobBackend` and register it in :func:`get_backend`.
"""
from __future__ import annotations

import os

from .base import BackendConfig, JobBackend, JobMessage

__all__ = [
    "BackendConfig",
    "JobBackend",
    "JobMessage",
    "get_backend",
    "load_config",
    "detect_backend_kind",
]


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def load_config() -> BackendConfig:
    """Build a :class:`BackendConfig` from the environment.

    Queue/container names accept clean ``SHIELDLAB_*`` names first, falling back
    to the historical ``AZURE_*`` names so existing Azure deployments keep working.
    """
    return BackendConfig(
        queue_name=_env("SHIELDLAB_QUEUE_NAME") or _env("AZURE_QUEUE_NAME") or "simulation-jobs",
        input_container=(
            _env("SHIELDLAB_INPUT_CONTAINER") or _env("AZURE_INPUT_CONTAINER_NAME") or "simulation-input"
        ),
        output_container=(
            _env("SHIELDLAB_OUTPUT_CONTAINER") or _env("AZURE_OUTPUT_CONTAINER_NAME") or "simulation-output"
        ),
        max_dequeue_count=int(_env("SHIELDLAB_WORKER_MAX_DEQUEUE_COUNT", "5") or "5"),
        local_root=_env("SHIELDLAB_LOCAL_DATA_DIR"),
        azure_connection_string=_env("AZURE_STORAGE_CONNECTION_STRING"),
        azure_account_url=_env("AZURE_STORAGE_ACCOUNT_URL"),
    )


def detect_backend_kind() -> str:
    """Return ``'local'`` or ``'azure'`` based on env (explicit override wins)."""
    kind = _env("SHIELDLAB_BACKEND").lower()
    if kind:
        return kind
    if _env("AZURE_STORAGE_CONNECTION_STRING") or _env("AZURE_STORAGE_ACCOUNT_URL"):
        return "azure"
    return "local"


def get_backend(config: BackendConfig | None = None, kind: str | None = None) -> JobBackend:
    """Instantiate the selected job backend.

    Args:
        config: explicit config; if omitted, read from the environment.
        kind: explicit backend kind; if omitted, auto-detected.
    """
    cfg = config or load_config()
    resolved = (kind or detect_backend_kind()).lower()
    if resolved in ("local", "demo", "filesystem", "fs"):
        from .local_backend import LocalBackend

        return LocalBackend(cfg)
    if resolved in ("azure", "az"):
        from .azure_backend import AzureBackend

        return AzureBackend(cfg)
    raise ValueError(
        f"Unknown SHIELDLAB_BACKEND={resolved!r}. Use 'local' (free/demo) or 'azure'."
    )
