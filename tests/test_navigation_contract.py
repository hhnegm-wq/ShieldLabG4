from __future__ import annotations

from ui.components.navigation import (
    NAV_SECTION_LABELS,
    PAGE_SPECS,
    PRIMARY_WORKFLOWS,
    QUICK_ACTION_SPECS,
    PAGE_BY_KEY,
)


def test_page_specs_have_unique_keys_and_routes() -> None:
    keys = [spec.key for spec in PAGE_SPECS]
    routes = [spec.route for spec in PAGE_SPECS]

    assert len(keys) == len(set(keys))
    assert len(routes) == len(set(routes))


def test_primary_workflows_reference_registered_pages() -> None:
    assert len(PRIMARY_WORKFLOWS) == 3
    for workflow in PRIMARY_WORKFLOWS:
        assert workflow.start_page_key in PAGE_BY_KEY
        assert workflow.stage_page_keys
        for page_key in workflow.stage_page_keys:
            assert page_key in PAGE_BY_KEY


def test_quick_actions_reference_registered_pages() -> None:
    assert NAV_SECTION_LABELS == ("Simulation", "Analysis", "Reference", "Platform")
    for action in QUICK_ACTION_SPECS:
        assert action.page_key in PAGE_BY_KEY