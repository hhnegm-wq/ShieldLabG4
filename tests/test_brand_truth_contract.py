from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_user_facing_brand_copy_avoids_overclaim_language() -> None:
    targets = [
        ROOT / "python" / "shieldlab" / "metadata.py",
        ROOT / "python" / "shieldlab" / "content.py",
    ]
    banned_phrases = [
        "Enterprise Radiation Shielding Platform",
        "enterprise radiation shielding platform",
        "production-ready scientific platform",
    ]

    violations: list[str] = []
    for path in targets:
        content = path.read_text(encoding="utf-8")
        for phrase in banned_phrases:
            if phrase in content:
                violations.append(f"{path.relative_to(ROOT)} contains banned phrase '{phrase}'")

    assert not violations, "Brand/truth contract violations found:\n" + "\n".join(violations)