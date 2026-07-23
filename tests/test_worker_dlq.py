"""Worker dead-letter-queue (DLQ) tests against the LocalBackend.

Pure Python — no Azure. Exercises the real queue semantics (visibility timeout,
dequeue_count, poison queue) via shieldlab.backends.LocalBackend and the
refactored worker.process_once / run_job, instead of mocking Azure clients.
"""
from __future__ import annotations

import json

import pytest

from shieldlab.backends import BackendConfig
from shieldlab.backends.local_backend import LocalBackend
from worker.queue_worker import WorkerConfig, process_once, run_job


def _backend(tmp_path) -> LocalBackend:
    return LocalBackend(BackendConfig(local_root=str(tmp_path), max_dequeue_count=3))


def _worker_cfg(max_dequeue_count: int = 3) -> WorkerConfig:
    return WorkerConfig(
        poll_seconds=0,
        visibility_timeout=300,
        max_dequeue_count=max_dequeue_count,
        job_timeout=60,
    )


def _raise(exc: Exception):
    def _inner(*_a, **_k):
        raise exc
    return _inner


@pytest.mark.unit
class TestLocalBackendPoison:
    """move_to_poison writes a valid envelope and removes the original."""

    def test_envelope_is_valid_json_and_original_removed(self, tmp_path) -> None:
        backend = _backend(tmp_path)
        backend.enqueue(json.dumps({"job_id": "x"}))
        msg = backend.receive(visibility_timeout=300)
        assert msg is not None

        backend.move_to_poison(msg, "boom")

        assert backend.queue_depth("main") == 0
        poison = backend.poison_messages()
        assert len(poison) == 1
        envelope = json.loads(poison[0])
        assert envelope["original_content"] == json.dumps({"job_id": "x"})
        assert "boom" in envelope["error"]
        assert envelope["poisoned_at"] is not None


@pytest.mark.unit
class TestProcessOnceDlq:
    """process_once preserves the DLQ contract across the retry lifecycle."""

    def test_exceeding_max_dequeue_goes_to_dlq(self, tmp_path) -> None:
        backend = _backend(tmp_path)
        wcfg = _worker_cfg(max_dequeue_count=3)
        backend.enqueue(json.dumps({"job_id": "j1"}))

        # Drive dequeue_count up to the limit (visibility 0 => immediately visible).
        for _ in range(wcfg.max_dequeue_count):
            assert backend.receive(visibility_timeout=0) is not None

        # Next receive inside process_once pushes it past the limit -> poison.
        assert process_once(backend, backend.config, wcfg) is True
        assert len(backend.poison_messages()) == 1
        assert backend.queue_depth("main") == 0

    def test_failure_below_limit_is_left_for_retry(self, tmp_path, monkeypatch) -> None:
        backend = _backend(tmp_path)
        wcfg = _worker_cfg(max_dequeue_count=5)
        backend.enqueue(json.dumps({"job_id": "j2"}))

        monkeypatch.setattr(
            "worker.queue_worker.run_job", _raise(RuntimeError("transient"))
        )
        assert process_once(backend, backend.config, wcfg) is True
        # Not poisoned, not deleted — still leased in the main queue.
        assert backend.poison_messages() == []
        assert backend.queue_depth("main") == 1

    def test_failure_on_last_attempt_goes_to_dlq(self, tmp_path, monkeypatch) -> None:
        backend = _backend(tmp_path)
        wcfg = _worker_cfg(max_dequeue_count=1)
        backend.enqueue(json.dumps({"job_id": "j3"}))

        monkeypatch.setattr("worker.queue_worker.run_job", _raise(RuntimeError("fatal")))
        # First receive -> dequeue_count == max; failure -> poison.
        assert process_once(backend, backend.config, wcfg) is True
        assert len(backend.poison_messages()) == 1
        assert backend.queue_depth("main") == 0

    def test_success_deletes_message(self, tmp_path, monkeypatch) -> None:
        backend = _backend(tmp_path)
        wcfg = _worker_cfg(max_dequeue_count=3)
        backend.enqueue(json.dumps({"job_id": "j4"}))

        monkeypatch.setattr("worker.queue_worker.run_job", lambda *_a, **_k: None)
        assert process_once(backend, backend.config, wcfg) is True
        assert backend.queue_depth("main") == 0
        assert backend.poison_messages() == []

    def test_empty_queue_returns_false(self, tmp_path) -> None:
        backend = _backend(tmp_path)
        assert process_once(backend, backend.config, _worker_cfg()) is False


@pytest.mark.unit
class TestRunJobRoundTrip:
    """run_job pulls the study blob, runs (faked), and uploads log + artifacts."""

    def test_run_job_uploads_log_and_artifacts(self, tmp_path, monkeypatch) -> None:
        backend = LocalBackend(BackendConfig(local_root=str(tmp_path)))
        backend.put_blob("simulation-input", "studies/j.json", b'{"study": true}')

        results_dir = tmp_path / "results"
        (results_dir / "sub").mkdir(parents=True)
        (results_dir / "sub" / "out.csv").write_bytes(b"col\n1\n")
        monkeypatch.setenv("SHIELDLAB_RESULTS_DIR", str(results_dir))

        class _Proc:
            returncode = 0
            stdout = "ok"
            stderr = ""

        monkeypatch.setattr(
            "worker.queue_worker.subprocess.run", lambda *_a, **_k: _Proc()
        )

        payload = {
            "job_id": "j",
            "study_blob_path": "simulation-input/studies/j.json",
            "output_prefix": "jobs/j/",
            "run_args": [],
        }
        run_job(payload, backend, backend.config, _worker_cfg())

        artifacts = backend.list_blobs("simulation-output", "jobs/j/")
        assert "jobs/j/worker.log" in artifacts
        assert "jobs/j/artifacts/sub/out.csv" in artifacts
        assert (
            backend.get_blob("simulation-output", "jobs/j/artifacts/sub/out.csv")
            == b"col\n1\n"
        )

