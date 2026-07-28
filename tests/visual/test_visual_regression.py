"""Visual regression screenshots for ShieldLab G4 platform.

Usage
-----
# Start the Streamlit app first, then run:
SHIELDLAB_UI_SMOKE=1 pytest tests/visual/test_visual_regression.py -v -s

Screenshots are saved to tests/visual/screenshots/<timestamp>/.
The SHIELDLAB_BASE_URL env-var overrides the default localhost:8501.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pytest

from ui.components.navigation import NAV_SECTION_LABELS, page_href, visible_page_specs

pytestmark = pytest.mark.skipif(
    os.environ.get("SHIELDLAB_UI_SMOKE", "0") != "1",
    reason="Visual regression disabled. Set SHIELDLAB_UI_SMOKE=1 to run.",
)

_BASE = os.environ.get("SHIELDLAB_BASE_URL", "http://localhost:8501")
_OUT_ROOT = Path(__file__).parent / "screenshots"

_PAGES = [(spec.route, spec.key) for spec in visible_page_specs()]


def _slug_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def test_visual_all_pages() -> None:
    """Navigate every page, assert no Python tracebacks, save full-page screenshots."""
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
