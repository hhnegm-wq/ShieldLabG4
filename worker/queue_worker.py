from __future__ import annotations

import json
import logging
import os
import pathlib
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient

_log = logging.getLogger(__name__)


@dataclass
class WorkerConfig:
    storage_account_url: str
    queue_name: str
    input_container: str
    output_container: str
    storage_connection_string: str
    poll_seconds: int
    visibility_timeout: int
    max_dequeue_count: int  # messages exceeding this are moved to the poison queue


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def load_config() -> WorkerConfig:
    return WorkerConfig(
        storage_account_url=_env("AZURE_STORAGE_ACCOUNT_URL"),
        queue_name=_env("AZURE_QUEUE_NAME", "simulation-jobs"),
        input_container=_env("AZURE_INPUT_CONTAINER_NAME", "simulation-input"),
        output_container=_env("AZURE_OUTPUT_CONTAINER_NAME", "simulation-output"),
        storage_connection_string=_env("AZURE_STORAGE_CONNECTION_STRING"),
        poll_seconds=int(_env("SHIELDLAB_WORKER_POLL_SECONDS", "10")),
        visibility_timeout=int(_env("SHIELDLAB_WORKER_VISIBILITY_TIMEOUT", "300")),
        max_dequeue_count=int(_env("SHIELDLAB_WORKER_MAX_DEQUEUE_COUNT", "5")),
    )


def build_clients(cfg: WorkerConfig):
    """Return (queue_client, poison_queue_client, blob_service_client)."""
    poison_queue_name = cfg.queue_name + "-poison"
    if cfg.storage_connection_string:
        queue_client = QueueClient.from_connection_string(
            conn_str=cfg.storage_connection_string,
            queue_name=cfg.queue_name,
        )
        poison_client = QueueClient.from_connection_string(
            conn_str=cfg.storage_connection_string,
            queue_name=poison_queue_name,
        )
        blob_client = BlobServiceClient.from_connection_string(cfg.storage_connection_string)
        return queue_client, poison_client, blob_client

    if not cfg.storage_account_url:
        raise RuntimeError("AZURE_STORAGE_ACCOUNT_URL is required when no connection string is provided")

    credential = DefaultAzureCredential()
    queue_url = cfg.storage_account_url.replace(".blob.", ".queue.")
    if not queue_url.endswith("/"):
        queue_url += "/"
    queue_client = QueueClient(
        account_url=queue_url,
        queue_name=cfg.queue_name,
        credential=credential,
    )
    poison_client = QueueClient(
        account_url=queue_url,
        queue_name=poison_queue_name,
        credential=credential,
    )
    blob_client = BlobServiceClient(account_url=cfg.storage_account_url, credential=credential)
    return queue_client, poison_client, blob_client


def _move_to_poison(
    message,
    error: Exception,
    queue_client: QueueClient,
    poison_client: QueueClient,
) -> None:
    """Enqueue a structured poison envelope then delete the original message."""
    try:
        poison_client.create_queue()
    except Exception:
        _log.debug("Poison queue already exists or could not be created — continuing", exc_info=True)

    envelope = json.dumps(
        {
            "original_content": message.content,
            "dequeue_count": message.dequeue_count,
            "inserted_on": (
                message.inserted_on.isoformat()
                if message.inserted_on
                else None
            ),
            "poisoned_at": datetime.now(timezone.utc).isoformat(),
            "error": str(error),
        },
        ensure_ascii=False,
    )
    poison_client.send_message(envelope)
    queue_client.delete_message(message.id, message.pop_receipt)
    _log.warning(
        "[DLQ] Moved message (dequeue_count=%d) to poison queue. Error: %s",
        message.dequeue_count, error,
    )


def parse_study_blob_path(path_value: str, default_container: str) -> tuple[str, str]:
    normalized = path_value.strip().lstrip("/")
    if not normalized:
        raise ValueError("study_blob_path is empty")

    if "/" not in normalized:
        return default_container, normalized

    first, rest = normalized.split("/", 1)
    if first and rest:
        return first, rest
    return default_container, normalized


def run_job(message_data: dict, cfg: WorkerConfig, blob_service: BlobServiceClient) -> None:
    job_id = message_data.get("job_id") or f"job-{int(time.time())}"
    study_blob_path = message_data.get("study_blob_path", "")
    output_prefix = message_data.get("output_prefix", f"jobs/{job_id}/")
    run_args = message_data.get("run_args") or []

    if not isinstance(run_args, list):
        raise ValueError("run_args must be a list")

    input_container, input_blob_name = parse_study_blob_path(study_blob_path, cfg.input_container)
    input_blob = blob_service.get_blob_client(container=input_container, blob=input_blob_name)

    with tempfile.TemporaryDirectory(prefix="shieldlab-worker-") as tmp:
        tmp_path = pathlib.Path(tmp)
        study_path = tmp_path / pathlib.Path(input_blob_name).name
        with open(study_path, "wb") as fp:
            fp.write(input_blob.download_blob().readall())

        cmd = [
            "python",
            "-m",
            "shieldlab.io.runner",
            str(study_path),
        ]
        cmd.extend(str(arg) for arg in run_args)

        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=int(_env("SHIELDLAB_WORKER_JOB_TIMEOUT", "3600")),
        )

        output_container_client = blob_service.get_container_client(cfg.output_container)

        log_blob_name = f"{output_prefix.rstrip('/')}/worker.log"
        log_payload = (
            f"job_id={job_id}\n"
            f"command={' '.join(cmd)}\n"
            f"exit_code={proc.returncode}\n"
            "----- stdout -----\n"
            f"{proc.stdout}\n"
            "----- stderr -----\n"
            f"{proc.stderr}\n"
        ).encode("utf-8")
        output_container_client.upload_blob(log_blob_name, log_payload, overwrite=True)

        if proc.returncode != 0:
            raise RuntimeError(f"Runner failed for {job_id} with exit code {proc.returncode}")

        results_dir = pathlib.Path(_env("SHIELDLAB_RESULTS_DIR", "build/results"))
        if not results_dir.exists():
            return

        for path in results_dir.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(results_dir).as_posix()
            blob_name = f"{output_prefix.rstrip('/')}/artifacts/{rel}"
            with open(path, "rb") as fp:
                output_container_client.upload_blob(blob_name, fp, overwrite=True)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    cfg = load_config()
    queue_client, poison_client, blob_service = build_clients(cfg)

    for client in (queue_client, poison_client):
        try:
            client.create_queue()
        except Exception:
            _log.debug("Queue already exists or could not be created — continuing", exc_info=True)

    _log.info(
        "Worker started. queue=%s  poison=%s  max_retries=%d",
        cfg.queue_name, cfg.queue_name + "-poison", cfg.max_dequeue_count,
    )
    while True:
        messages = queue_client.receive_messages(messages_per_page=1, visibility_timeout=cfg.visibility_timeout)
        got_message = False
        for message in messages:
            got_message = True

            # Move to poison queue if the message has already exceeded the retry limit.
            if message.dequeue_count > cfg.max_dequeue_count:
                try:
                    error_sentinel = RuntimeError(
                        f"Exceeded max_dequeue_count ({cfg.max_dequeue_count})"
                    )
                    _move_to_poison(message, error_sentinel, queue_client, poison_client)
                except Exception as dlq_exc:
                    _log.error("[DLQ] Failed to move message to poison queue: %s", dlq_exc, exc_info=True)
                continue

            try:
                payload = json.loads(message.content)
                run_job(payload, cfg, blob_service)
                queue_client.delete_message(message.id, message.pop_receipt)
                _log.info("Job processed: %s", payload.get("job_id", "unknown"))
            except Exception as exc:
                _log.error(
                    "Job failed (dequeue_count=%d): %s",
                    message.dequeue_count, exc, exc_info=True,
                )
                # If this was the last allowed attempt, move to DLQ immediately
                # rather than waiting for the visibility timeout to expire.
                if message.dequeue_count >= cfg.max_dequeue_count:
                    try:
                        _move_to_poison(message, exc, queue_client, poison_client)
                    except Exception as dlq_exc:
                        _log.error("[DLQ] Failed to move message to poison queue: %s", dlq_exc, exc_info=True)
                # Otherwise leave in queue — visibility timeout will re-expose it.

        if not got_message:
            time.sleep(cfg.poll_seconds)


if __name__ == "__main__":
    main()
