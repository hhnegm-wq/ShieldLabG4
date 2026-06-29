# ADR-0003: Product Shell Strategy — Retain Streamlit with Hard Guardrails

- Status: Accepted
- Date: 2026-05-17
- Decision makers: Technical founder, platform lead, frontend lead
- Supersedes: none (first explicit shell-strategy decision)

## Context

The executive platform assessment (2026-05-16) identified the UI shell as the platform's highest-priority structural risk. ShieldLab G4 uses Streamlit as its product shell. Substantial engineering effort has gone into overriding and concealing Streamlit's native chrome to produce an enterprise visual identity. That pattern creates four compounding costs:

1. Every visual improvement risks framework-specific patchwork rather than structural progress.
2. Layout consistency, accessibility, and upgrade safety are permanently taxed by the shell mismatch.
3. Ad hoc page-level styling has accumulated without governance, producing cleanup cycles instead of system behavior.
4. The product looks more mature than its shell structure permits.

Two options were evaluated:

**Option A — Retain Streamlit with hard guardrails**
Keep Streamlit as the product shell for the next 12 months. Formalize a strict component wrapper layer. Prohibit direct page-level framework styling. Treat framework upgrades as controlled platform events.

**Option B — Begin controlled shell migration**
Define a migration seam now. Preserve domain APIs, plotting services, and the scientific core. Replace the shell layer progressively, page by page, ordered by workflow importance.

## Decision

**Option A is adopted for the current release cycle.**

Rationale:

- The domain core, API, worker, and visualization layers are solid and framework-independent. The cost of shell migration is not justified by the marginal UX improvement it would deliver in the near term.
- The highest-return structural improvements (style layer governance, CI guardrails, workflow-oriented navigation) can be fully implemented within Option A without a shell migration.
- Streamlit's constraints are manageable under strict discipline enforced by code structure and CI, not by convention.
- The conditions under which Option B becomes correct are defined below as an explicit trigger checklist.

## Constraints accepted with Option A

By choosing Option A, the platform explicitly accepts the following permanent constraints for the current release cycle:

1. No custom keyboard shortcuts or global keybinding.
2. No multi-step modal workflows without Streamlit workarounds.
3. Limited control over URL routing (Streamlit's st.navigation model).
4. Accessibility posture limited to what Streamlit's rendered HTML permits.
5. Framework upgrade risk (Streamlit minor versions can alter rendered DOM structure).

These constraints are acceptable for the current scientific application profile and user base.

## Required implementation under Option A

Option A is only viable if the following guardrails are implemented and enforced by CI within the current sprint:

### Style layer governance (WS-DESIGN-SYSTEM)
- `ui/components/styles.py` must be split into explicit modules: `tokens.py`, `surface.py`, `data_display.py`, `shell_components.py`. `styles.py` becomes a thin injector that imports from those modules.
- No new CSS rules may be added directly to `styles.py`. Changes must go to the correct sub-module.
- Page modules under `ui/pages/` must not use `unsafe_allow_html=True` directly or emit raw shell HTML.

### Approved entry points (WS-UX-SHELL)
- Page heroes: `render_page_hero(...)` from `ui/components/layout.py`.
- Dashboard/navigation cards: helpers from `ui/components/enterprise_ui.py`.
- Metric and status strips: helpers from `ui/components/enterprise_ui.py`.
- Page modules must not bypass these wrappers.

### CI enforcement (WS-GOVERNANCE)
- `tools/page_scaffold_check.py` must validate page structure on every PR.
- `tools/figure_audit.py` must enforce `apply_journal_style("shieldlab_web")` presence on any page module that imports `matplotlib`.
- Both checks must be wired into `release-validation-gate.yml`.

## Trigger conditions for Option B

The shell migration decision (Option B) should be revisited and may be triggered if any of the following becomes true:

- A committed enterprise customer requires WCAG 2.1 AA accessibility compliance that cannot be achieved within Streamlit's rendered output.
- A product roadmap item requires multi-step modal state management that Streamlit's execution model cannot support without architectural harm.
- A Streamlit upgrade breaks visual regression tests in a way that requires more than one sprint to remediate.
- The product requires white-label deployment where the Streamlit branding seam is customer-visible and cannot be suppressed.

If any trigger fires, a new ADR must be filed within two weeks and the Option B migration seam must be defined before any new features are added to the shell layer.

## Consequences

Positive:
- Shell decision is explicit and documented. No further debate without a trigger event.
- The platform can invest in Option A guardrails with confidence that the investment is justified.
- New contributors have a clear answer to "why Streamlit" and "when would that change."

Tradeoffs:
- The platform carries Streamlit's constraint envelope for the current release cycle.
- Some UX improvements will require creative workarounds rather than direct implementation.
- Shell hardening work produces framework-specific assets, not portable shell primitives.

## References

- `docs/audit/executive_platform_roast_and_structural_fix_list_2026-05-16.md` §1, §10
- `ADR-0002-ui-shell-visual-contract.md`
- `ui/components/styles.py`
- `ui/components/enterprise_ui.py`
- `ui/components/layout.py`
