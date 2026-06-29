"""Unit tests for worker dead-letter-queue (DLQ) logic.

These tests are pure Python — no Azure credentials required.
They use unittest.mock to verify that _move_to_poison() is called at the
correct dequeue counts and that the poison envelope is well-formed JSON.
"""
from __future__ import annotations

import json
import sys
import types
import unittest
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Provide a minimal stub for azure.storage.queue so the module imports without
# the real Azure SDK installed in CI.
# ---------------------------------------------------------------------------

def _ensure_azure_stubs() -> None:
    for mod_name in (
        "azure",
        "azure.identity",
        "azure.storage",
        "azure.storage.queue",
        "azure.storage.blob",
    ):
        if mod_name not in sys.modules:
            sys.modules[mod_name] = types.ModuleType(mod_name)

    # QueueClient stub
    sys.modules["azure.storage.queue"].QueueClient = MagicMock  # type: ignore[attr-defined]
    sys.modules["azure.storage.blob"].BlobServiceClient = MagicMock  # type: ignore[attr-defined]
    sys.modules["azure.identity"].DefaultAzureCredential = MagicMock  # type: ignore[attr-defined]


_ensure_azure_stubs()

# Import after stubs are in place.
from worker.queue_worker import (  # noqa: E402
    WorkerConfig,
    _move_to_poison,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(**overrides) -> WorkerConfig:
    defaults = dict(
        storage_account_url="",
        queue_name="simulation-jobs",
        input_container="simulation-input",
        output_container="simulation-output",
        storage_connection_string="UseDevelopmentStorage=true",
        poll_seconds=10,
        visibility_timeout=300,
        max_dequeue_count=5,
    )
    defaults.update(overrides)
    return WorkerConfig(**defaults)


def _make_message(dequeue_count: int, content: str = '{"job_id":"test-1"}') -> MagicMock:
    msg = MagicMock()
    msg.id = "msg-id-1"
    msg.pop_receipt = "pop-receipt-1"
    msg.dequeue_count = dequeue_count
    msg.content = content
    msg.inserted_on = None
    return msg


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestMoveToPoisonEnvelope:
    """_move_to_poison sends a valid JSON envelope and deletes the original."""

    def test_envelope_is_valid_json(self) -> None:
        q_client = MagicMock()
        p_client = MagicMock()
        msg = _make_message(dequeue_count=6, content='{"job_id":"x"}')
        error = RuntimeError("boom")

        _move_to_poison(msg, error, q_client, p_client)

        assert p_client.send_message.called
        raw = p_client.send_message.call_args[0][0]
        envelope = json.loads(raw)
        assert envelope["original_content"] == '{"job_id":"x"}'
        assert envelope["dequeue_count"] == 6
        assert "boom" in envelope["error"]
        assert envelope["poisoned_at"] is not None

    def test_original_message_deleted_after_poison(self) -> None:
        q_client = MagicMock()
        p_client = MagicMock()
        msg = _make_message(dequeue_count=6)

        _move_to_poison(msg, RuntimeError("x"), q_client, p_client)

        q_client.delete_message.assert_called_once_with(msg.id, msg.pop_receipt)

    def test_poison_queue_create_called(self) -> None:
        q_client = MagicMock()
        p_client = MagicMock()
        msg = _make_message(dequeue_count=6)

        _move_to_poison(msg, RuntimeError("x"), q_client, p_client)

        p_client.create_queue.assert_called_once()


@pytest.mark.unit
class TestMainLoopDlq:
    """Integration-level: main loop moves exhausted messages to DLQ."""

    def test_message_exceeding_max_dequeue_goes_to_dlq(self) -> None:
        cfg = _make_config(max_dequeue_count=3)

        exhausted_msg = _make_message(dequeue_count=4)

        q_client = MagicMock()
        p_client = MagicMock()
        blob_service = MagicMock()

        # receive_messages returns exhausted message once, then nothing.
        call_count = [0]

        def _receive(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return iter([exhausted_msg])
            raise StopIteration

        q_client.receive_messages.side_effect = _receive

        with (
            patch("worker.queue_worker.build_clients", return_value=(q_client, p_client, blob_service)),
            patch("worker.queue_worker.load_config", return_value=cfg),
            patch("worker.queue_worker.time.sleep", side_effect=StopIteration),
        ):
            try:
                main()
            except StopIteration:
                pass

        # Should have been moved to DLQ.
        assert p_client.send_message.called
        q_client.delete_message.assert_called_once_with(exhausted_msg.id, exhausted_msg.pop_receipt)

    def test_message_within_retry_limit_is_left_in_queue(self) -> None:
        """A failing job below max_dequeue_count is left for retry (not deleted)."""
        cfg = _make_config(max_dequeue_count=5)
        msg = _make_message(dequeue_count=2)

        q_client = MagicMock()
        p_client = MagicMock()
        blob_service = MagicMock()

        call_count = [0]

        def _receive(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return iter([msg])
            raise StopIteration

        q_client.receive_messages.side_effect = _receive

        with (
            patch("worker.queue_worker.build_clients", return_value=(q_client, p_client, blob_service)),
            patch("worker.queue_worker.load_config", return_value=cfg),
            patch("worker.queue_worker.run_job", side_effect=RuntimeError("transient")),
            patch("worker.queue_worker.time.sleep", side_effect=StopIteration),
        ):
            try:
                main()
            except StopIteration:
                pass

        # Message NOT moved to DLQ; NOT deleted from main queue.
        p_client.send_message.assert_not_called()
        q_client.delete_message.assert_not_called()
