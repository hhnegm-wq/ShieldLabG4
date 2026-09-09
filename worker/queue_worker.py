from __future__ import annotations

import json
import logging
import os
import pathlib
import subprocess
import tempfile
import time
from dataclasses import dataclass

from shieldlab.backends import (
    BackendConfig,
    JobBackend,
    JobMessage,
    get_backend,
    load_config as load_backend_config,
)

_log = logging.getLogger(__name__)


@dataclass
class WorkerConfig:
    """Worker loop tuning (independent of the storage backend)."""

    poll_seconds: int
    visibility_timeout: int
    max_dequeue_count: int
    job_timeout: int


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _env_flag(name: str) -> bool:
    return _env(name, "").lower() in {"1", "true", "yes", "on"}


def load_worker_config() -> WorkerConfig:
    return WorkerConfig(
        poll_seconds=int(_env("SHIELDLAB_WORKER_POLL_SECONDS", "10") or "10"),
        visibility_timeout=int(_env("SHIELDLAB_WORKER_VISIBILITY_TIMEOUT", "300") or "300"),
        max_dequeue_count=int(_env("SHIELDLAB_WORKER_MAX_DEQUEUE_COUNT", "5") or "5"),
        job_timeout=int(_env("SHIELDLAB_WORKER_JOB_TIMEOUT", "3600") or "3600"),
    )


def _safe_poison(backend: JobBackend, message: JobMessage, error: str) -> None:
    """Move a message to the poison queue, logging (never raising) on failure."""
    try:
        backend.move_to_poison(message, error)
    except Exception as dlq_exc:
        _log.error("[DLQ] Failed to move message to poison queue: %s", dlq_exc, exc_info=True)


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


def build_runner_command(study_path: pathlib.Path, run_args: list[str]) -> list[str]:
    python_exe = _env("SHIELDLAB_WORKER_PYTHON_EXE", "python") or "python"
    cmd = [python_exe, "-m", "shieldlab.io.runner", str(study_path)]

    build_dir = _env("SHIELDLAB_WORKER_BUILD_DIR")
    if build_dir:
        cmd.extend(["--build-dir", build_dir])

    executable = _env("SHIELDLAB_WORKER_G4_EXECUTABLE")
    if executable:
        cmd.extend(["--executable", executable])

    geant4_setup = _env("SHIELDLAB_WORKER_GEANT4_SETUP")
    if geant4_setup:
        cmd.extend(["--geant4-setup", geant4_setup])

    wsl_distro = _env("SHIELDLAB_WORKER_WSL_DISTRO")
    if wsl_distro:
        cmd.extend(["--wsl-distro", wsl_distro])

    if _env_flag("SHIELDLAB_WORKER_NO_PLOTS"):
        cmd.append("--no-plots")
    if _env_flag("SHIELDLAB_WORKER_ALLOW_VALIDATION_ERRORS"):
        cmd.append("--allow-validation-errors")

    cmd.extend(str(arg) for arg in run_args)
    return cmd


def run_job(
    message_data: dict,
    backend: JobBackend,
    backend_cfg: BackendConfig,
    worker_cfg: WorkerConfig,
) -> None:
    job_id = message_data.get("job_id") or f"job-{int(time.time())}"
    study_blob_path = message_data.get("study_blob_path", "")
    output_prefix = message_data.get("output_prefix", f"jobs/{job_id}/")
    run_args = message_data.get("run_args") or []

    if not isinstance(run_args, list):
        raise ValueError("run_args must be a list")

    input_container, input_blob_name = parse_study_blob_path(
        study_blob_path, backend_cfg.input_container
    )
    study_bytes = backend.get_blob(input_container, input_blob_name)

    with tempfile.TemporaryDirectory(prefix="shieldlab-worker-") as tmp:
        tmp_path = pathlib.Path(tmp)
        study_path = tmp_path / pathlib.Path(input_blob_name).name
        study_path.write_bytes(study_bytes)

        cmd = build_runner_command(study_path, run_args)

        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=worker_cfg.job_timeout
        )

        prefix = output_prefix.rstrip("/")
        log_payload = (
            f"job_id={job_id}\n"
            f"command={' '.join(cmd)}\n"
            f"exit_code={proc.returncode}\n"
            "----- stdout -----\n"
            f"{proc.stdout}\n"
            "----- stderr -----\n"
            f"{proc.stderr}\n"
        ).encode("utf-8")
        backend.put_blob(backend_cfg.output_container, f"{prefix}/worker.log", log_payload)

        if proc.returncode != 0:
            raise RuntimeError(
                f"Runner failed for {job_id} with exit code {proc.returncode}"
            )

        results_dir = pathlib.Path(_env("SHIELDLAB_RESULTS_DIR", "build/results"))
        if not results_dir.exists():
            return

        for path in results_dir.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(results_dir).as_posix()
            backend.put_blob(
                backend_cfg.output_container,
                f"{prefix}/artifacts/{rel}",
                path.read_bytes(),
            )


def process_once(
    backend: JobBackend, backend_cfg: BackendConfig, worker_cfg: WorkerConfig
) -> bool:
    """Receive and handle at most one message.

    Returns True if a message was handled, False if the queue was empty.
    Preserves the DLQ contract: a message that exceeds ``max_dequeue_count`` (or
    fails on its last allowed attempt) is moved to the poison queue.
    """
    message = backend.receive(worker_cfg.visibility_timeout)
    if message is None:
        return False

    if message.dequeue_count > worker_cfg.max_dequeue_count:
        _safe_poison(
            backend, message,
            f"Exceeded max_dequeue_count ({worker_cfg.max_dequeue_count})",
        )
        return True

    try:
        payload = json.loads(message.content)
        run_job(payload, backend, backend_cfg, worker_cfg)
        backend.delete(message)
        _log.info("Job processed: %s", payload.get("job_id", "unknown"))
    except Exception as exc:
        _log.error(
            "Job failed (dequeue_count=%d): %s",
            message.dequeue_count, exc, exc_info=True,
        )
        # Last allowed attempt -> dead-letter now instead of waiting for the
        # visibility timeout to re-expose the message.
        if message.dequeue_count >= worker_cfg.max_dequeue_count:
            _safe_poison(backend, message, str(exc))
        # Otherwise leave it leased; it reappears after the visibility timeout.
    return True


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    backend_cfg = load_backend_config()
    worker_cfg = load_worker_config()
    backend = get_backend(backend_cfg)
    backend.ensure_ready()

    _log.info(
        "Worker started. backend=%s  queue=%s  poison=%s-poison  max_retries=%d",
        type(backend).__name__, backend_cfg.queue_name, backend_cfg.queue_name,
        worker_cfg.max_dequeue_count,
    )
    while True:
        if not process_once(backend, backend_cfg, worker_cfg):
            time.sleep(worker_cfg.poll_seconds)


if __name__ == "__main__":
    main()
