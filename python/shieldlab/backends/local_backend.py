"""Local job backend: filesystem blobs + SQLite queue.

Zero external services — everything lives under a single data directory
(``SHIELDLAB_LOCAL_DATA_DIR``, default ``./.shieldlab_data``). This makes the
full producer/worker pipeline runnable on any Linux VM (e.g. Oracle Cloud
Always Free) or a laptop, with no cloud account.

The SQLite queue reproduces the Azure Storage Queue semantics the pipeline
relies on: at-least-once delivery, a per-message ``dequeue_count``, a
visibility timeout (leased messages reappear if not deleted), and a poison
(dead-letter) queue. WAL mode + a busy timeout make it safe for the API and
worker to share the same file as separate processes.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .base import BackendConfig, JobBackend, JobMessage

_MAIN_QUEUE = "main"
_POISON_QUEUE = "poison"


def _now() -> float:
    return time.time()


class LocalBackend(JobBackend):
    """Filesystem + SQLite implementation of :class:`JobBackend`."""

    def __init__(self, config: BackendConfig) -> None:
        super().__init__(config)
        root = (
            config.local_root
            or os.environ.get("SHIELDLAB_LOCAL_DATA_DIR", "").strip()
            or str(Path.cwd() / ".shieldlab_data")
        )
        self.root = Path(root).expanduser().resolve()
        self.blobs_root = self.root / "blobs"
        self.db_path = self.root / "queue.db"
        self.blobs_root.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── SQLite plumbing ────────────────────────────────────────────────────
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id            TEXT PRIMARY KEY,
                    queue         TEXT NOT NULL DEFAULT 'main',
                    content       TEXT NOT NULL,
                    dequeue_count INTEGER NOT NULL DEFAULT 0,
                    visible_at    REAL NOT NULL DEFAULT 0,
                    receipt       TEXT,
                    inserted_at   REAL NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_msg_queue_visible ON messages(queue, visible_at)"
            )

    def ensure_ready(self) -> None:
        self.blobs_root.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── blob storage ───────────────────────────────────────────────────────
    def _blob_path(self, container: str, blob_name: str) -> Path:
        safe_container = container.strip("/").replace("..", "")
        if not safe_container:
            raise ValueError("container name is required")
        base = (self.blobs_root / safe_container).resolve()
        target = (base / blob_name.strip("/")).resolve()
        # Guard against path traversal escaping the container directory.
        if target != base and base not in target.parents:
            raise ValueError(f"Unsafe blob path: {container}/{blob_name}")
        return target

    def put_blob(self, container: str, blob_name: str, data: bytes) -> None:
        path = self._blob_path(container, blob_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get_blob(self, container: str, blob_name: str) -> bytes:
        path = self._blob_path(container, blob_name)
        if not path.is_file():
            raise FileNotFoundError(f"blob not found: {container}/{blob_name}")
        return path.read_bytes()

    def list_blobs(self, container: str, prefix: str = "") -> list[str]:
        base = (self.blobs_root / container.strip("/")).resolve()
        if not base.is_dir():
            return []
        names = [
            p.relative_to(base).as_posix()
            for p in base.rglob("*")
            if p.is_file()
        ]
        return sorted(n for n in names if n.startswith(prefix))

    # ── queue ──────────────────────────────────────────────────────────────
    def _enqueue(self, payload: str, queue: str) -> str:
        msg_id = uuid.uuid4().hex
        now = _now()
        with closing(self._connect()) as conn:
            conn.execute(
                "INSERT INTO messages(id, queue, content, dequeue_count, visible_at, receipt, inserted_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (msg_id, queue, payload, 0, now, None, now),
            )
        return msg_id

    def enqueue(self, payload: str) -> None:
        self._enqueue(payload, _MAIN_QUEUE)

    def receive(self, visibility_timeout: int) -> JobMessage | None:
        now = _now()
        with closing(self._connect()) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    "SELECT id, content, dequeue_count, inserted_at FROM messages "
                    "WHERE queue=? AND visible_at <= ? ORDER BY inserted_at LIMIT 1",
                    (_MAIN_QUEUE, now),
                ).fetchone()
                if row is None:
                    conn.execute("COMMIT")
                    return None
                msg_id, content, dequeue_count, inserted_at = row
                receipt = uuid.uuid4().hex
                new_count = int(dequeue_count) + 1
                conn.execute(
                    "UPDATE messages SET dequeue_count=?, visible_at=?, receipt=? WHERE id=?",
                    (new_count, now + max(int(visibility_timeout), 0), receipt, msg_id),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
        return JobMessage(
            id=msg_id,
            receipt=receipt,
            content=content,
            dequeue_count=new_count,
            inserted_at=datetime.fromtimestamp(float(inserted_at), tz=timezone.utc),
        )

    def delete(self, message: JobMessage) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                "DELETE FROM messages WHERE id=? AND (receipt=? OR receipt IS NULL)",
                (message.id, message.receipt),
            )

    def move_to_poison(self, message: JobMessage, error: str) -> None:
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
        now = _now()
        with closing(self._connect()) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    "INSERT INTO messages(id, queue, content, dequeue_count, visible_at, receipt, inserted_at) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (uuid.uuid4().hex, _POISON_QUEUE, envelope, message.dequeue_count, now, None, now),
                )
                conn.execute("DELETE FROM messages WHERE id=?", (message.id,))
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

    # ── introspection (handy for tests / a future status endpoint) ─────────
    def queue_depth(self, queue: str = _MAIN_QUEUE) -> int:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE queue=?", (queue,)
            ).fetchone()
        return int(row[0]) if row else 0

    def poison_messages(self) -> list[str]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT content FROM messages WHERE queue=? ORDER BY inserted_at",
                (_POISON_QUEUE,),
            ).fetchall()
        return [r[0] for r in rows]
