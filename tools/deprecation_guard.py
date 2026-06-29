from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INCLUDE_SUFFIXES = {
    ".py",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".css",
    ".js",
    ".ts",
    ".tsx",
}

EXCLUDED_DIR_NAMES = {
    ".git",
    ".pytest_cache",
    ".benchmarks",
    "build",
    "results",
    "tmp",
    "__pycache__",
}

PATTERNS = [
    ("deprecated use_container_width", re.compile(r"use_container_width\s*=", re.IGNORECASE)),
    ("deprecated st.components.v1.html", re.compile(r"st\.components\.v1\.html\s*\(", re.IGNORECASE)),
    ("mojibake byte markers", re.compile(r"(Ã|Â|â€|ðŸ)")),
]


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def main() -> int:
    violations: list[str] = []
    self_path = Path(__file__).resolve().relative_to(ROOT)

    for path in ROOT.rglob("*"):
        if not path.is_file() or _is_excluded(path):
            continue
        if path.suffix.lower() not in INCLUDE_SUFFIXES:
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        rel = path.relative_to(ROOT)
        if rel == self_path:
            continue
        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            for label, pattern in PATTERNS:
                if pattern.search(line):
                    violations.append(f"{rel}:{idx}: {label}: {line.strip()}")

    if violations:
        print("Deprecation and text-quality guard failed:\n")
        for item in violations:
            print(item)
        return 1

    print("Deprecation and text-quality guard passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
