from __future__ import annotations

import os

import pytest

from ui.components.navigation import page_href, visible_page_specs


pytestmark = pytest.mark.skipif(
    os.environ.get("SHIELDLAB_UI_SMOKE", "0") != "1",
    reason="UI smoke disabled. Set SHIELDLAB_UI_SMOKE=1 to run.",
)


def test_platform_pages_smoke():
    playwright = pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    base_url = os.environ.get("SHIELDLAB_BASE_URL", "http://localhost:8501")
    pages = [(spec.route, spec.key) for spec in visible_page_specs()]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for route, page_key in pages:
            bad_responses: list[str] = []

            def _capture_response(response) -> None:
                if response.status < 400:
                    return
                if not response.url.startswith(base_url):
                    return
                resource_type = response.request.resource_type
                if resource_type not in {"document", "fetch", "xhr", "script", "stylesheet", "image"}:
                    return
                bad_responses.append(f"{response.status} {resource_type} {response.url}")

            page.on("response", _capture_response)
            page.goto(base_url + route, wait_until="domcontentloaded")
            page.wait_for_timeout(900)
            page.remove_listener("response", _capture_response)
            body = page.inner_text("body")
            assert "Traceback:" not in body, f"Traceback detected on {route}"
            assert "ValueError:" not in body, f"ValueError detected on {route}"
            assert not bad_responses, f"4xx/5xx asset or fetch failures on {page_key}: {bad_responses}"
        browser.close()


def test_key_actions_visible():
    playwright = pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    base_url = os.environ.get("SHIELDLAB_BASE_URL", "http://localhost:8501")
    # Group labels by route so each page is only visited once.
    from collections import defaultdict
    route_labels: dict = defaultdict(list)
    for route, label in [
        (page_href("settings"), "Apply Settings"),
        (page_href("settings"), "Reset Defaults"),
        (page_href("study_builder"), "Load"),
        (page_href("methods"), "Generate Methods Pack"),
    ]:
        route_labels[route].append(label)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for route, labels in route_labels.items():
            page.goto(base_url + route, wait_until="networkidle", timeout=30_000)
            for label in labels:
                # Wait for the specific button to appear (Streamlit renders async via WebSocket).
                try:
                    page.wait_for_selector(
                        f"button:has-text('{label}')",
                        state="visible",
                        timeout=15_000,
                    )
                except Exception:
                    pass
                btn = page.get_by_role("button", name=label)
                if btn.count() == 0:
                    btn = page.get_by_text(label)
                assert btn.count() > 0, f"Action '{label}' not found on {route}"
        browser.close()
