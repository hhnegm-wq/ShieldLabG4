# ADR-0002: UI Shell Visual Contract

Date: 2026-05-17
Status: Accepted
Decision makers: Platform lead, frontend lead, technical founder

## Context

ShieldLab G4's UI had drifted into a pattern where page modules were directly emitting custom HTML and depending on page-local styling decisions. That created three problems:

- pages could bypass shared shell abstractions
- visual consistency depended on manual review instead of structure
- the stylesheet accumulated responsibility without clear layers

This ADR defines the minimum contract for all product-facing Streamlit pages while the current shell remains in place.

## Decision

All page modules under `ui/pages/` must use shared UI primitives for shell-level presentation.

Required rules:

1. Page heroes must use `render_page_hero(...)` from `ui/components/layout.py`.
2. Linked dashboard/navigation cards must use shared helpers from `ui/components/enterprise_ui.py`.
3. Metric strips, path tables, and benchmark cards must use shared helpers from `ui/components/enterprise_ui.py`.
4. Page modules must not use `unsafe_allow_html=True` directly.
5. Page modules must not emit raw shell HTML such as `<div class=...>`, `<section class=...>`, or `<a class=...>` for product shell components.
6. Shared CSS in `ui/components/styles.py` must be organized by responsibility, not only by file position.

Current explicit style layers in `ui/components/styles.py`:

- tokens and scales
- shell components
- surface components
- data-display components
- remaining base/framework styles

## Consequences

Positive:

- pages become thinner and more consistent
- shell evolution happens in shared components instead of by page surgery
- future design-system work has clear control points

Tradeoffs:

- some UI changes now require shared-helper edits rather than page-only edits
- exceptions must be intentional and documented instead of ad hoc

## Visual Contract Checklist

Any new or materially changed page must satisfy all of the following before merge:

- Uses `render_page_hero(...)` for the page hero.
- Uses shared enterprise UI helpers for reusable cards or strips.
- Introduces no direct `unsafe_allow_html=True` in the page module.
- Introduces no page-local shell markup that duplicates an existing shared pattern.
- Reuses approved plot/export styling where figures are present.
- Adds or updates a validation check when a new shared pattern is introduced.

## Enforcement

The repository includes an automated test that scans `ui/pages/` for direct HTML bypasses and `unsafe_allow_html=True` usage. Any exception to this ADR must be explicit, temporary, and documented in a follow-up ADR or issue.
