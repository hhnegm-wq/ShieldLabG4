"""Tests for the pluggable job backend abstraction (LocalBackend + factory)."""
from __future__ import annotations

import json
import time

import pytest

from shieldlab.backends import BackendConfig, detect_backend_kind, get_backend
from shieldlab.backends.local_backend import LocalBackend


def _backend(tmp_path) -> LocalBackend:
    return LocalBackend(BackendConfig(local_root=str(tmp_path)))


@pytest.mark.unit
class TestLocalBlobs:
    def test_put_get_roundtrip(self, tmp_path) -> None:
        b = _backend(tmp_path)
        b.put_blob("input", "studies/a.json", b'{"k": 1}')
        assert b.get_blob("input", "studies/a.json") == b'{"k": 1}'

    def test_overwrite(self, tmp_path) -> None:
        b = _backend(tmp_path)
        b.put_blob("input", "a.txt", b"one")
        b.put_blob("input", "a.txt", b"two")
        assert b.get_blob("input", "a.txt") == b"two"

    def test_get_missing_raises(self, tmp_path) -> None:
        b = _backend(tmp_path)
        with pytest.raises(FileNotFoundError):
            b.get_blob("input", "nope.json")

    def test_list_blobs_prefix(self, tmp_path) -> None:
        b = _backend(tmp_path)
        b.put_blob("out", "jobs/j1/worker.log", b"log")
        b.put_blob("out", "jobs/j1/artifacts/r.csv", b"r")
        b.put_blob("out", "jobs/j2/worker.log", b"other")
        assert b.list_blobs("out", "jobs/j1/") == [
            "jobs/j1/artifacts/r.csv",
            "jobs/j1/worker.log",
        ]

    def test_list_blobs_missing_container(self, tmp_path) -> None:
        assert _backend(tmp_path).list_blobs("nope", "x/") == []

    def test_path_traversal_blocked(self, tmp_path) -> None:
        b = _backend(tmp_path)
        with pytest.raises(ValueError):
            b.put_blob("input", "../escape.txt", b"x")


@pytest.mark.unit
class TestLocalQueue:
    def test_enqueue_receive_delete(self, tmp_path) -> None:
        b = _backend(tmp_path)
        b.enqueue('{"job_id": "j1"}')
        msg = b.receive(visibility_timeout=300)
        assert msg is not None
        assert msg.dequeue_count == 1
        assert json.loads(msg.content)["job_id"] == "j1"
        b.delete(msg)
        assert b.receive(visibility_timeout=300) is None

    def test_visibility_hides_then_reexposes(self, tmp_path) -> None:
        b = _backend(tmp_path)
        b.enqueue('{"job_id": "j2"}')
        first = b.receive(visibility_timeout=1)
        assert first is not None
        # Hidden while leased.
        assert b.receive(visibility_timeout=1) is None
        time.sleep(1.1)
        second = b.receive(visibility_timeout=1)
        assert second is not None
        assert second.dequeue_count == 2

    def test_dequeue_count_increments(self, tmp_path) -> None:
        b = _backend(tmp_path)
        b.enqueue("{}")
        counts = [b.receive(visibility_timeout=0).dequeue_count for _ in range(3)]
        assert counts == [1, 2, 3]

    def test_fifo_order(self, tmp_path) -> None:
        b = _backend(tmp_path)
        for i in range(3):
            b.enqueue(json.dumps({"n": i}))
            time.sleep(0.005)
        got = []
        for _ in range(3):
            m = b.receive(visibility_timeout=300)
            assert m is not None
            got.append(json.loads(m.content)["n"])
            b.delete(m)
        assert got == [0, 1, 2]


@pytest.mark.unit
class TestFactory:
    def test_detect_local_by_default(self, monkeypatch) -> None:
        for var in (
            "SHIELDLAB_BACKEND",
            "AZURE_STORAGE_CONNECTION_STRING",
            "AZURE_STORAGE_ACCOUNT_URL",
        ):
            monkeypatch.delenv(var, raising=False)
        assert detect_backend_kind() == "local"

    def test_detect_azure_when_env_present(self, monkeypatch) -> None:
        monkeypatch.delenv("SHIELDLAB_BACKEND", raising=False)
        monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_URL", "https://x.blob.core.windows.net")
        assert detect_backend_kind() == "azure"

    def test_explicit_override_wins(self, monkeypatch) -> None:
        monkeypatch.setenv("SHIELDLAB_BACKEND", "local")
        monkeypatch.setenv("AZURE_STORAGE_CONNECTION_STRING", "UseDevelopmentStorage=true")
        assert detect_backend_kind() == "local"

    def test_get_backend_local(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("SHIELDLAB_BACKEND", "local")
        monkeypatch.setenv("SHIELDLAB_LOCAL_DATA_DIR", str(tmp_path))
        assert isinstance(get_backend(), LocalBackend)

    def test_unknown_backend_raises(self, monkeypatch) -> None:
        monkeypatch.setenv("SHIELDLAB_BACKEND", "bogus")
        with pytest.raises(ValueError):
            get_backend()
