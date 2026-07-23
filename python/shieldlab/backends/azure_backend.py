"""Azure job backend: Azure Queue Storage + Blob Storage.

Preserves the exact behaviour of the original worker/API Azure path. The Azure
SDK is imported lazily so that importing :mod:`shieldlab.backends` (or running
the local/free backend) never requires ``azure-*`` packages to be installed.

Auth: a storage connection string if provided, otherwise
``DefaultAzureCredential`` (managed identity / az login) against
``AZURE_STORAGE_ACCOUNT_URL``.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from .base import BackendConfig, JobBackend, JobMessage

_log = logging.getLogger(__name__)


class AzureBackend(JobBackend):
    """Azure Queue + Blob implementation of :class:`JobBackend`."""

    def __init__(self, config: BackendConfig) -> None:
        super().__init__(config)
        self._poison_queue_name = f"{config.queue_name}-poison"
        self._queue, self._poison, self._blob = self._build_clients()

    def _build_clients(self):
        cfg = self.config
        poison_name = self._poison_queue_name
        if cfg.azure_connection_string:
            from azure.storage.blob import BlobServiceClient
            from azure.storage.queue import QueueClient

            queue = QueueClient.from_connection_string(cfg.azure_connection_string, cfg.queue_name)
            poison = QueueClient.from_connection_string(cfg.azure_connection_string, poison_name)
            blob = BlobServiceClient.from_connection_string(cfg.azure_connection_string)
            return queue, poison, blob

        if not cfg.azure_account_url:
            raise RuntimeError(
                "Azure backend requires AZURE_STORAGE_CONNECTION_STRING or "
                "AZURE_STORAGE_ACCOUNT_URL (with managed identity)."
            )

        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient
        from azure.storage.queue import QueueClient

        credential = DefaultAzureCredential()
        queue_url = cfg.azure_account_url.replace(".blob.", ".queue.")
        if not queue_url.endswith("/"):
            queue_url += "/"
        queue = QueueClient(account_url=queue_url, queue_name=cfg.queue_name, credential=credential)
        poison = QueueClient(account_url=queue_url, queue_name=poison_name, credential=credential)
        blob = BlobServiceClient(account_url=cfg.azure_account_url, credential=credential)
        return queue, poison, blob

    # ── lifecycle ──────────────────────────────────────────────────────────
    def ensure_ready(self) -> None:
        for client in (self._queue, self._poison):
            try:
                client.create_queue()
            except Exception:
                _log.debug("Queue already exists or could not be created", exc_info=True)
        for name in (self.config.input_container, self.config.output_container):
            try:
                self._blob.get_container_client(name).create_container()
            except Exception:
                _log.debug("Container %s already exists or could not be created", name, exc_info=True)

    # ── producer ───────────────────────────────────────────────────────────
    def put_blob(self, container: str, blob_name: str, data: bytes) -> None:
        container_client = self._blob.get_container_client(container)
        try:
            container_client.create_container()
        except Exception:
            _log.debug("create_container(%s) — likely already exists", container, exc_info=True)
        container_client.upload_blob(name=blob_name, data=data, overwrite=True)

    def enqueue(self, payload: str) -> None:
        self._queue.send_message(payload)

    # ── consumer ───────────────────────────────────────────────────────────
    def receive(self, visibility_timeout: int) -> JobMessage | None:
        messages = self._queue.receive_messages(
            messages_per_page=1, visibility_timeout=visibility_timeout
        )
        for message in messages:
            inserted = getattr(message, "inserted_on", None)
            if inserted is not None and inserted.tzinfo is None:
                inserted = inserted.replace(tzinfo=timezone.utc)
            return JobMessage(
                id=message.id,
                receipt=message.pop_receipt,
                content=message.content,
                dequeue_count=message.dequeue_count,
                inserted_at=inserted,
            )
        return None

    def delete(self, message: JobMessage) -> None:
        self._queue.delete_message(message.id, message.receipt)

    def move_to_poison(self, message: JobMessage, error: str) -> None:
        try:
            self._poison.create_queue()
        except Exception:
            _log.debug("Poison queue already exists or could not be created", exc_info=True)
        envelope = json.dumps(
            {
                "original_content": message.content,
                "dequeue_count": message.dequeue_count,
                "inserted_on": (
                    message.inserted_at.isoformat() if message.inserted_at else None
                ),
                "poisoned_at": datetime.now(timezone.utc).isoformat(),
                "error": str(error),
            },
            ensure_ascii=False,
        )
        self._poison.send_message(envelope)
        self._queue.delete_message(message.id, message.receipt)
        _log.warning(
            "[DLQ] Moved message (dequeue_count=%d) to poison queue. Error: %s",
            message.dequeue_count, error,
        )

    def get_blob(self, container: str, blob_name: str) -> bytes:
        blob_client = self._blob.get_blob_client(container=container, blob=blob_name)
        return blob_client.download_blob().readall()

    def list_blobs(self, container: str, prefix: str = "") -> list[str]:
        container_client = self._blob.get_container_client(container)
        return [b.name for b in container_client.list_blobs(name_starts_with=prefix)]
