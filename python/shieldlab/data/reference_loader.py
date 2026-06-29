"""Reference dataset loader with strict provenance schema.

Every reference dataset shipped under ``data/references/`` must have a
JSON sidecar describing its provenance, license, and column units.

Required sidecar keys:
    id              str   short stable identifier
    title           str   human-readable title
    doi             str   DOI (10.x/yyyy form) — required for publication gate
    url             str   public URL
    retrieved_at    str   ISO-8601 date the data was retrieved/digitised
    license         str   SPDX identifier or free-text license
    columns         dict  column_name -> {units, description}
    data_file       str   relative CSV/JSON path

Banned values (rejected by the publication gate):
    "example_baseline_replace_with_xcom_or_paper", "tbd", "todo", "?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REQUIRED_KEYS = ("id", "title", "doi", "url", "retrieved_at", "license", "columns", "data_file")
BANNED_VALUES = {
    "example_baseline_replace_with_xcom_or_paper",
    "tbd",
    "todo",
    "?",
    "",
    None,
}


@dataclass(frozen=True)
class ReferenceSidecar:
    id: str
    title: str
    doi: str
    url: str
    retrieved_at: str
    license: str
    columns: dict
    data_file: str
    path: Path


def load_sidecar(path: str | Path) -> ReferenceSidecar:
    """Load and validate a reference sidecar JSON file.

    Raises ValueError on any missing/banned required field.
    """
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED_KEYS if k not in raw]
    if missing:
        raise ValueError(
            f"Reference sidecar {p} is missing required keys: {missing}"
        )
    bad: list[str] = []
    for k in REQUIRED_KEYS:
        v = raw[k]
        if isinstance(v, str) and v.strip().lower() in BANNED_VALUES:
            bad.append(f"{k}={v!r}")
    if bad:
        raise ValueError(
            f"Reference sidecar {p} contains placeholder/banned values: {bad}"
        )
    return ReferenceSidecar(
        id=str(raw["id"]),
        title=str(raw["title"]),
        doi=str(raw["doi"]),
        url=str(raw["url"]),
        retrieved_at=str(raw["retrieved_at"]),
        license=str(raw["license"]),
        columns=dict(raw["columns"]),
        data_file=str(raw["data_file"]),
        path=p,
    )


def discover_sidecars(root: str | Path) -> list[ReferenceSidecar]:
    """Walk ``root`` and load every ``*.ref.json`` sidecar."""
    root = Path(root)
    out: list[ReferenceSidecar] = []
    if not root.exists():
        return out
    for p in sorted(root.rglob("*.ref.json")):
        out.append(load_sidecar(p))
    return out


__all__ = [
    "REQUIRED_KEYS",
    "BANNED_VALUES",
    "ReferenceSidecar",
    "load_sidecar",
    "discover_sidecars",
]
