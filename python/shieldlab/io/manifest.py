"""Reproducibility manifest.

Emits a JSON manifest alongside every result set capturing:
    - git commit SHA (HEAD)
    - container image digest (if running inside a container)
    - random seed
    - configuration / study hash (sha256 of the canonicalised JSON)
    - python + platform info
    - environment lockfile reference (requirements.txt hash)
    - timestamp (UTC)

This is what allows a reviewer to bit-for-bit reproduce a result.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def _container_digest() -> str | None:
    # Best-effort: docker / k8s typically expose this as an env var.
    for var in ("CONTAINER_IMAGE_DIGEST", "IMAGE_DIGEST", "POD_IMAGE"):
        v = os.environ.get(var)
        if v:
            return v
    return None


def _hash_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _hash_canonical(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_manifest(
    *,
    output_dir: str | Path,
    config: dict | None = None,
    seed: int | str | None = None,
    extra: dict | None = None,
) -> dict:
    """Compose and write ``manifest.json`` next to the run outputs.

    Returns the manifest dict.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    requirements_hash = None
    for candidate in (
        Path("requirements.txt"),
        Path("python/pyproject.toml"),
    ):
        h = _hash_file(candidate)
        if h:
            requirements_hash = {str(candidate): h}
            break

    manifest = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "host": socket.gethostname(),
        "python": {
            "version": sys.version.split()[0],
            "implementation": platform.python_implementation(),
        },
        "platform": platform.platform(),
        "git_sha": _git_sha(),
        "container_image_digest": _container_digest(),
        "seed": seed if seed is not None else os.environ.get("SHIELDLAB_SEED"),
        "config_hash": _hash_canonical(config) if config is not None else None,
        "requirements_hash": requirements_hash,
        "extra": extra or {},
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest


__all__ = ["build_manifest"]
