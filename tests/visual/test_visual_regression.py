"""Visual regression gate for the ShieldLab G4 platform.

Default mode compares current full-page screenshots against the committed
baseline in ``tests/visual/baseline`` and fails on any pixel difference.

Usage
-----
# Validate current UI against the committed baseline:
SHIELDLAB_UI_SMOKE=1 pytest tests/visual/test_visual_regression.py -v -s

# Capture a fresh timestamped set without comparing (manual inspection aid):
SHIELDLAB_UI_SMOKE=1 SHIELDLAB_VISUAL_CAPTURE_ONLY=1 \
    pytest tests/visual/test_visual_regression.py::test_visual_all_pages -v -s

# Replace the committed baseline with the freshly captured current set:
SHIELDLAB_UI_SMOKE=1 SHIELDLAB_UPDATE_VISUAL_BASELINE=1 \
    pytest tests/visual/test_visual_regression.py::test_visual_all_pages -v -s

The SHIELDLAB_BASE_URL env-var overrides the default localhost:8501.
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path

import pytest

from PIL import Image, ImageChops

from ui.components.navigation import NAV_SECTION_LABELS, page_href, visible_page_specs

pytestmark = [
    pytest.mark.ui,
    pytest.mark.skipif(
        os.environ.get("SHIELDLAB_UI_SMOKE", "0") != "1",
        reason="Visual regression disabled. Set SHIELDLAB_UI_SMOKE=1 to run.",
    ),
]

_BASE = os.environ.get("SHIELDLAB_BASE_URL", "http://localhost:8501")
_OUT_ROOT = Path(__file__).parent / "screenshots"
_BASELINE_DIR = Path(__file__).parent / "baseline"
_CAPTURE_ONLY = os.environ.get("SHIELDLAB_VISUAL_CAPTURE_ONLY", "0") == "1"
_UPDATE_BASELINE = os.environ.get("SHIELDLAB_UPDATE_VISUAL_BASELINE", "0") == "1"

_PAGES = [(spec.route, spec.key) for spec in visible_page_specs()]


def _slug_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _assert_exact_match(expected_path: Path, actual_path: Path) -> None:
    expected = Image.open(expected_path).convert("RGBA")
    actual = Image.open(actual_path).convert("RGBA")

    assert expected.size == actual.size, (
        f"Visual baseline size mismatch for {actual_path.name}: "
        f"expected {expected.size}, got {actual.size}"
    )

    diff = ImageChops.difference(expected, actual)
    assert diff.getbbox() is None, (
        f"Visual regression detected for {actual_path.name}. "
        f"Compare baseline {expected_path} with current capture {actual_path}."
    )


def test_visual_all_pages() -> None:
    """Navigate every page, assert no Python tracebacks, and gate on exact baseline images."""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright  # type: ignore[import]

    ts = _slug_ts()
    out_dir = _OUT_ROOT / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        page = ctx.new_page()

        for route, name in _PAGES:
            url = _BASE + route
            try:
                page.goto(url, wait_until="networkidle", timeout=20_000)
            except Exception:
                page.goto(url, wait_until="domcontentloaded", timeout=15_000)
            page.wait_for_timeout(1_500)

            body = page.inner_text("body")
            if "Traceback (most recent call last)" in body or "ValueError:" in body:
                failures.append(f"{name}: Python error on page")

            screenshot_path = out_dir / f"{name}.png"
            page.screenshot(
                path=str(screenshot_path),
                full_page=True,
                type="png",
            )

        ctx.close()
        browser.close()

    print(f"\nScreenshots saved to: {out_dir}")
    for f in sorted(out_dir.glob("*.png")):
        size_kb = f.stat().st_size // 1024
        print(f"  {f.name:40s}  {size_kb:>6} KB")

    assert not failures, "Page errors detected:\n" + "\n".join(failures)

    if _CAPTURE_ONLY:
        return

    if _UPDATE_BASELINE:
        if _BASELINE_DIR.exists():
            shutil.rmtree(_BASELINE_DIR)
        shutil.copytree(out_dir, _BASELINE_DIR)
        return

    assert _BASELINE_DIR.exists(), (
        f"Missing visual baseline directory: {_BASELINE_DIR}. "
        "Set SHIELDLAB_UPDATE_VISUAL_BASELINE=1 to create/update it."
    )

    baseline_files = sorted(p.name for p in _BASELINE_DIR.glob("*.png"))
    current_files = sorted(p.name for p in out_dir.glob("*.png"))
    assert baseline_files == current_files, (
        f"Visual baseline file set mismatch. baseline={baseline_files}, current={current_files}"
    )

    for name in baseline_files:
        _assert_exact_match(_BASELINE_DIR / name, out_dir / name)

    # Keep failed captures for diagnosis, but avoid cluttering the repo on a
    # successful baseline check.
    shutil.rmtree(out_dir)


def test_visual_nav_structure() -> None:
    """Assert the expected 4 nav groups and 12 links are present on every page."""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright  # type: ignore[import]

    expected_groups = {label.upper() for label in NAV_SECTION_LABELS}
    expected_link_count = len(visible_page_specs())

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        page.goto(_BASE + "/", wait_until="networkidle", timeout=20_000)
        page.wait_for_timeout(1_200)

        # Read nav group labels from sidebar section headings
        group_els = page.locator('[data-testid="stSidebarNav"] .st-emotion-cache-1rtdyuf, '
                                 'nav[data-testid="stSidebarNav"] .eyeqlp51, '
                                 '[data-testid="stSidebarNavSeparator"] + * span').all()
        nav_text = page.locator('[data-testid="stSidebarNav"]').inner_text()
        found_groups = {g for g in expected_groups if g in nav_text.upper()}

        nav_links = page.locator('[data-testid="stSidebarNav"] a').all()
        link_count = len(nav_links)

        browser.close()

    assert found_groups == expected_groups, (
        f"Nav groups mismatch. Expected {expected_groups}, found {found_groups}\n"
        f"Full sidebar text:\n{nav_text[:600]}"
    )
    assert link_count == expected_link_count, (
        f"Expected {expected_link_count} nav links, found {link_count}"
    )


def test_visual_no_download_button_wrap() -> None:
    """Assert download buttons on the results explorer render wider than they are tall."""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright  # type: ignore[import]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(_BASE + page_href("results_explorer"), wait_until="networkidle", timeout=20_000)
        page.wait_for_timeout(1_500)

        # Find all download buttons and check none are taller than wide
        wrapped = page.evaluate("""
            () => {
                const btns = [...document.querySelectorAll('[data-testid="stDownloadButton"] button')];
                return btns
                    .filter(b => b.offsetHeight > b.offsetWidth)
                    .map(b => ({ text: b.innerText.trim(), w: b.offsetWidth, h: b.offsetHeight }));
            }
        """)

        browser.close()

    assert not wrapped, (
        f"Download buttons are taller than wide (text wrapping): {wrapped}"
    )
