"""Backend-agnostic interface for the job queue + blob storage pipeline."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class JobMessage:
    """A dequeued job message, independent of the underlying queue.

    Attributes:
        id: opaque message identifier (used with :meth:`JobBackend.delete`).
        receipt: opaque lease/pop-receipt guarding delete against a re-leased copy.
        content: the message body (a JSON string).
        dequeue_count: number of times this message has been received (>= 1).
        inserted_at: when the message was first enqueued, if known.
    """

    id: str
    receipt: str
    content: str
    dequeue_count: int
    inserted_at: datetime | None = None


@dataclass
class BackendConfig:
    """Configuration shared by all backends."""

    queue_name: str = "simulation-jobs"
    input_container: str = "simulation-input"
    output_container: str = "simulation-output"
    max_dequeue_count: int = 5
    # LocalBackend
    local_root: str = ""
    # AzureBackend
    azure_connection_string: str = ""
    azure_account_url: str = ""


class JobBackend(ABC):
    """Producer/consumer interface for the simulation-job pipeline.

    Producer (API) uses :meth:`put_blob` + :meth:`enqueue`.
    Consumer (worker) uses :meth:`receive`, :meth:`get_blob`, :meth:`put_blob`,
    :meth:`delete`, and :meth:`move_to_poison`.
    """

    def __init__(self, config: BackendConfig) -> None:
        self.config = config

    # ── lifecycle ──────────────────────────────────────────────────────────
    def ensure_ready(self) -> None:
        """Create queues/containers if required. Idempotent. Default: no-op."""

    # ── producer (API) side ────────────────────────────────────────────────
    @abstractmethod
    def put_blob(self, container: str, blob_name: str, data: bytes) -> None:
        """Store ``data`` at ``container/blob_name`` (overwrite if present)."""

    @abstractmethod
    def enqueue(self, payload: str) -> None:
        """Append ``payload`` (a JSON string) to the main job queue."""

    # ── consumer (worker) side ─────────────────────────────────────────────
    @abstractmethod
    def receive(self, visibility_timeout: int) -> JobMessage | None:
        """Lease the next visible message, hiding it for ``visibility_timeout``
        seconds and incrementing its dequeue count. Return ``None`` if empty."""

    @abstractmethod
    def delete(self, message: JobMessage) -> None:
        """Permanently remove a successfully-processed message."""

    @abstractmethod
    def move_to_poison(self, message: JobMessage, error: str) -> None:
        """Move a permanently-failed message to the dead-letter (poison) queue."""

    @abstractmethod
    def get_blob(self, container: str, blob_name: str) -> bytes:
        """Return the bytes stored at ``container/blob_name``."""

    def list_blobs(self, container: str, prefix: str = "") -> list[str]:
        """List blob names in ``container`` starting with ``prefix``."""
        raise NotImplementedError
