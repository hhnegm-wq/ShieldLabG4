from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class ContrastCheck:
    name: str
    fg: str
    bg: str
    min_ratio: float = 4.5


def _hex_to_rgb(color: str) -> tuple[float, float, float]:
    c = color.strip().lstrip("#")
    if len(c) != 6:
        raise ValueError(f"Expected 6-digit hex color, got: {color}")
    r = int(c[0:2], 16) / 255.0
    g = int(c[2:4], 16) / 255.0
    b = int(c[4:6], 16) / 255.0
    return r, g, b


def _linear_channel(v: float) -> float:
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color: str) -> float:
    r, g, b = _hex_to_rgb(hex_color)
    return 0.2126 * _linear_channel(r) + 0.7152 * _linear_channel(g) + 0.0722 * _linear_channel(b)


def _contrast_ratio(fg: str, bg: str) -> float:
    l1 = _relative_luminance(fg)
    l2 = _relative_luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run WCAG contrast checks for key UI color pairs.")
    parser.add_argument("--min-ratio", type=float, default=4.5, help="Default minimum contrast ratio.")
    args = parser.parse_args()

    checks = [
        ContrastCheck("Main body text on app background", "#24384d", "#eef3f8", args.min_ratio),
        ContrastCheck("Primary heading on app background", "#12263a", "#eef3f8", args.min_ratio),
        ContrastCheck("Input text on white field", "#10283d", "#ffffff", args.min_ratio),
        ContrastCheck("Sidebar text on teal sidebar", "#eaf7fb", "#147c78", args.min_ratio),
        ContrastCheck("Selected tab text on active tab", "#eaf7fb", "#1d657f", args.min_ratio),
        ContrastCheck("Dataframe cell text on white", "#12263a", "#ffffff", args.min_ratio),
        ContrastCheck("Button text on primary button", "#ffffff", "#0f766e", args.min_ratio),
    ]

    failed = []
    for check in checks:
        ratio = _contrast_ratio(check.fg, check.bg)
        status = "PASS" if ratio >= check.min_ratio else "FAIL"
        print(f"[{status}] {check.name}: ratio={ratio:.2f} (min {check.min_ratio:.2f})")
        if ratio < check.min_ratio:
            failed.append((check.name, ratio, check.min_ratio))

    if failed:
        print("\nContrast audit failed.")
        return 1

    print("\nContrast audit passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
