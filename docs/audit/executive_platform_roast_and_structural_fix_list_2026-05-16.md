# ShieldLab G4 Executive Roast and Structural Fix List

Date: 2026-05-16
Audience: product leadership, platform leadership, technical founder, principal engineer
Intent: deliberately blunt assessment of where the platform still looks stronger in ambition than in operating model

## Executive Roast

ShieldLab G4 is what happens when serious scientific software outgrows the prototype shell that got it to market, but the shell is still pretending it belongs in the board deck.

The good news is that the platform has real substance: domain depth, validation work, cloud plumbing, simulation core, analytical stack, and enough discipline to ship. The bad news is that the product still visibly runs on compromise debt. The platform is often impressive because of how much work it does despite its shell, not because the shell itself is structurally strong.

The blunt version:

- The science looks more mature than the product wrapper delivering it.
- The UI is a heavily customized Streamlit app wearing enterprise styling like a tailored suit over a lab prototype.
- The CSS layer is doing institutional damage control for framework decisions that should have been temporary.
- The repo tells the story of a team that kept making the correct tactical decision under pressure and is now paying compound interest on all of them at once.
- The platform says "production system" in the docs, but parts of the implementation still say "high-end internal tool with strong taste and weak boundaries."

If you strip away the gradients, the strongest statement the product currently makes is: "we were disciplined enough to make a prototype look expensive." That is not the same as being structurally enterprise-grade.

### What an executive should hear

- This is not a weak platform. It is an uneven one.
- The core technical value is real. The delivery shell is still overextended.
- The current UI layer is extracting more polish than the underlying framework deserves.
- The architecture has crossed the line where polish improvements are no longer the main bottleneck; platform shape is.
- If the next phase is external credibility, sales motion, or regulated deployment, the main risk is no longer "missing features." It is architectural trust.

### The harshest honest summary

ShieldLab G4 currently feels like a credible scientific engine trapped inside a presentation layer that has been repeatedly upgraded instead of fundamentally replaced.

That is survivable for an internal tool.

It becomes expensive for a product.

## Structural Weaknesses To Fix Next

This list is ordered by structural importance, not by convenience.

## 1. The UI shell is still framework-constrained instead of product-shaped

Problem:
The frontend still depends on Streamlit as the primary product shell, while substantial effort goes into hiding or restyling native framework behavior.

Why it matters:
This creates a permanent tax on credibility, UX control, layout consistency, accessibility, and upgrade safety. Every major visual improvement risks becoming framework-specific patchwork.

What it looks like today:

- Large centralized CSS injection in `ui/components/styles.py`
- Framework-native chrome being hidden to preserve the intended product feel
- Per-page exceptions and hero variants rather than a true component system

Fix next:

- Decide whether Streamlit remains the shell for the next 12 months or only the delivery vehicle for an interim release.
- If it remains, formalize a Streamlit design system with strict component wrappers and no direct page-level ad hoc styling.
- If it does not remain, define a migration seam now: preserve domain APIs and plotting/export services, replace only the shell.

## 2. Styling is centralized, but not yet governed like a design system

Problem:
The styling layer has become powerful, but it is still effectively a giant stylesheet with growing responsibility rather than a governed UI system.

Why it matters:
This makes visual consistency dependent on vigilance instead of structure. The platform can look polished and still drift page by page because the enforcement mechanism is social, not architectural.

What it looks like today:

- One large CSS injector carries tokens, layout, widgets, cards, tables, hero treatments, and framework overrides
- Shared patterns exist, but page code can still bypass them
- Visual consistency requires manual cleanup campaigns

Fix next:

- Split the current style surface into explicit layers: tokens, shell, components, data-display, page-specific exceptions
- Enforce usage through helper functions or wrapper components in `ui/components`
- Add a lightweight visual contract checklist for any new page or significant UI change

## 3. The platform boundary is broad enough to hurt maintainability

Problem:
The repository mixes C++, Python packages, UI, API, worker, infrastructure, papers, validation assets, backup artifacts, and operational docs in one active working surface.

Why it matters:
This raises cognitive load for every contributor and makes changes feel riskier than they should. It also blurs release boundaries between scientific core, product surface, and deployment machinery.

What it looks like today:

- Very high surface area in a single workspace
- Multiple delivery concerns evolving in parallel
- Backups and generated artifacts living close to source concerns

Fix next:

- Define explicit top-level ownership zones: scientific core, product surface, platform services, infrastructure, publication artifacts
- Tighten ignore/exclude rules for generated and backup material
- Write down release boundaries: what ships as product, what exists only as research/validation support

## 4. Visualization quality now exists, but enforcement came after drift

Problem:
The platform has a strong figure system now, but several pages had already drifted away from the intended standard before being pulled back into line.

Why it matters:
When chart quality depends on retrofits, the next drift is already scheduled. This matters because the product's credibility is heavily tied to visual trust in results.

What it looks like today:

- Shared presets in `python/shieldlab/viz/style.py`
- Multiple pages recently normalized to the same figure-finishing pattern
- Prior inconsistency in preset choice and final figure styling

Fix next:

- Move figure finalization into one shared helper used by every UI page and export path
- Add a test or lint-like check that fails on non-approved plot preset usage in UI pages
- Treat figure style selection as policy, not preference

## 5. The product experience is cleaner than the interaction model beneath it

Problem:
The app increasingly looks like a platform, but the interaction model still reflects a page-oriented Streamlit workflow rather than a coherent product workflow.

Why it matters:
Enterprise users do not judge polish only by visuals. They judge it by flow control, state continuity, predictable task progression, and whether the product feels intentional rather than page-assembled.

What it looks like today:

- Strong page-level presentation
- Ongoing need for shell, hero, tab, button, and card normalization
- User journeys still feel composition-driven rather than product-orchestrated

Fix next:

- Define the top 3 user workflows end to end and redesign around them instead of around page inventory
- Formalize navigation semantics: analysis, simulation, reference, operations, admin
- Reduce special-case layouts that communicate authorship history instead of product logic

## 6. Operational maturity is documented well, but not always legible as a product capability

Problem:
The repo contains substantial work on security, observability, quotas, validation, and deployment readiness, but a lot of that value is easier to discover in documents than in the product architecture story.

Why it matters:
A platform can be operationally solid and still fail to communicate trust if the implementation shape feels improvised. Buyers and reviewers trust coherence as much as feature checklists.

What it looks like today:

- Strong documentation around production readiness
- Real platform hardening work already present
- Perception risk because the UI shell and repo sprawl undercut the maturity narrative

Fix next:

- Write one canonical architecture narrative that maps product surfaces to platform guarantees
- Make operational controls legible in the product and admin surfaces, not just in docs
- Separate evidence of hardening from marketing-style readiness language

## 7. Too much platform quality depends on disciplined humans instead of hard guardrails

Problem:
The team is clearly disciplined, but the repo still allows too many high-impact inconsistencies unless someone notices and fixes them manually.

Why it matters:
Discipline scales worse than guardrails. As scope grows, manual consistency collapses first.

What it looks like today:

- Styling consistency restored by review and cleanup
- Mixed patterns historically allowed across pages
- Shared helpers exist, but adoption is not fully enforced

Fix next:

- Add simple structural gates: page scaffold checks, approved hero/component usage, plotting preset enforcement, doc generation boundaries
- Prefer "easy to do right, hard to do wrong" helpers over conventions in prose
- Reduce the number of places where page authors can improvise framework behavior directly

## 8. Product naming and visual language are outrunning platform truth

Problem:
The branding increasingly signals a hardened enterprise platform, while some structural choices still reflect an advanced research application.

Why it matters:
A mismatch between brand promise and implementation shape creates trust drag. The risk is not that the product is bad. The risk is that it invites scrutiny at the wrong abstraction layer.

What it looks like today:

- Strong visual polish and premium framing
- Advanced scientific and validation substance underneath
- Visible shell and architecture choices that still feel transitional

Fix next:

- Align external positioning with the maturity of the least convincing layer, not the most impressive one
- Avoid claiming "enterprise" purely from polish, docs, and cloud readiness
- Treat platform credibility as a systems problem, not a branding problem

## 9. The repo still carries signs of active construction in customer-visible areas

Problem:
The platform has production claims, but the working tree structure still shows ongoing build-out in places a skeptical reviewer would notice quickly.

Why it matters:
Customers, auditors, and reviewers infer process quality from repository hygiene faster than teams expect.

What it looks like today:

- Backup directories in the active workspace
- Generated outputs and artefacts close to source
- Research, product, and operational materials densely interleaved

Fix next:

- Move backup and bulky generated outputs fully out of the main development surface
- Reduce repository noise that weakens first-pass confidence
- Make the repo look as intentional as the strongest parts of the product already are

## 10. The next bottleneck is not visual polish; it is platform simplification

Problem:
The platform has reached the point where another round of UI shine yields diminishing returns unless the underlying shape is simplified.

Why it matters:
Without simplification, every future improvement will cost more than it should and age worse than it should.

Fix next:

- Consolidate page scaffolds and shared interaction patterns
- Shrink the number of one-off implementation paths
- Decide which parts are core product, which are research support, and which are transitional infrastructure

## Recommended Next Moves

If leadership wants the highest-return structural improvements, the next sequence should be:

1. Make an explicit decision on the product shell strategy: keep Streamlit with hard guardrails, or start a controlled shell migration.
2. Refactor the current styling layer into governed UI primitives instead of one increasingly omniscient CSS file.
3. Reduce repo sprawl and define clear ownership and shipping boundaries.
4. Turn visual and plotting consistency into automated policy, not cleanup work.
5. Reframe the product around top user workflows instead of page inventory.

## Enterprise Remediation Roadmap

This roadmap is designed to convert the weaknesses above into a controlled upgrade program instead of another round of reactive cleanup.

### Program objective

Within 12 months, ShieldLab G4 should be able to credibly present itself as a professional platform because:

- the product shell is intentional rather than heavily disguised
- the UI system is governed by reusable primitives instead of one-off page styling
- the scientific core, product surface, platform services, and operational controls have explicit boundaries
- consistency is enforced through guardrails and CI, not review heroics
- the user experience is organized around workflows, not page accumulation

### Definition of done

This roadmap is complete only when all of the following are true:

1. A new page can be added using approved scaffolds without touching global CSS for layout rescue.
2. All shipped figures use a single approved visualization pipeline with CI enforcement.
3. The repository has explicit ownership and packaging boundaries for scientific core, UI, API, worker, infrastructure, and publication assets.
4. The product can explain its architecture, controls, and operating model in one canonical document without hand-waving around the shell.
5. The product experience supports the top user workflows end to end with consistent state, navigation, and export behavior.
6. Enterprise claims are backed by technical shape, not just visual polish and documentation volume.

### Transformation principles

- Fix root causes before polishing symptoms.
- Prefer structural guardrails over manual conventions.
- Preserve the scientific and analytical core while reducing shell debt.
- Separate transition architecture from target architecture explicitly.
- Do not run a shell migration and a broad product redesign without a written seam between them.

## Workstreams

The program should run as six parallel workstreams with one accountable owner each.

| Workstream | Purpose | Primary owner |
| --- | --- | --- |
| WS-UX-SHELL | Shell strategy, navigation, workflow design, component scaffolds | Product/UX lead |
| WS-DESIGN-SYSTEM | Tokens, components, style layering, visual contracts | Frontend lead |
| WS-VIZ-GOV | Shared plotting pipeline, figure audit, export consistency | Data visualization lead |
| WS-ARCH | Module boundaries, repo hygiene, ownership model, packaging | Platform architect |
| WS-OPS-LEGIBILITY | Make security, quota, traceability, and operations visible and coherent | Platform lead |
| WS-GOVERNANCE | CI guardrails, ADRs, contribution rules, release policy | Engineering manager |

## Phase 0: Decision and Containment

Timeline: 2 weeks

Goal:
Stop further drift while making the two highest-leverage decisions explicit: shell strategy and governance model.

Deliverables:

- ADR defining the product shell strategy for the next 12 months:
  - Option A: retain Streamlit as the shell with strict wrappers and no direct page-level framework styling
  - Option B: begin a controlled shell migration while preserving the existing scientific/services layer
- Freeze policy for UI changes until new scaffolds are in place
- Repository hygiene policy covering backups, generated outputs, and non-source artifacts
- Canonical ownership map for major top-level areas

Actions:

1. Decide whether Streamlit is strategic, transitional, or sunset-bound.
2. Declare approved UI entry points in `ui/components` and mark direct ad hoc page styling as deprecated.
3. Move backup and disposable artefacts out of the active repo surface or fully ignore them.
4. Publish a one-page architecture boundary map.

Exit criteria:

- Shell decision documented and signed off.
- No new page is allowed to bypass approved UI wrappers.
- Repo hygiene rules merged and enforced.

## Phase 1: Guardrails Before More Polish

Timeline: 2 to 6 weeks

Goal:
Make it hard to introduce new inconsistency in UI, figures, structure, and docs.

Deliverables:

- Approved page scaffold and hero/component wrappers
- Shared plotting finalization helper used everywhere in the UI
- CI checks for banned UI and plotting patterns
- Contribution rules for when ADRs are required

Actions by weakness:

- Weakness 1 and 2:
  - Split `ui/components/styles.py` into layers: tokens, shell, components, data-display, exceptions.
  - Move shared cards, heroes, table treatments, button variants, and layout wrappers behind helper APIs.
- Weakness 4:
  - Centralize figure finishing in a single shared helper in the visualization layer.
  - Add a check that flags non-approved `apply_journal_style(...)` usage in UI pages.
- Weakness 7:
  - Add a structural CI rule set:
    - no direct page-local hero CSS without exception
    - no raw page-level layout HTML when a shared wrapper exists
    - no figure export path bypassing the approved pipeline

Exit criteria:

- A new UI page can be built from scaffolds without copying styles from another page.
- All current figure pages use the same finishing pipeline.
- CI blocks at least the most common regression paths.

## Phase 2: Product-Shape the Experience

Timeline: 6 to 12 weeks

Goal:
Shift the product from page inventory to user workflow design.

Deliverables:

- Top 3 workflow definitions with start, handoff, result, and export states
- Revised navigation model aligned to workflows and operating roles
- Standard state model for inputs, runs, results, exports, and references
- Removal of page-specific layout exceptions that do not fit the product model

Priority workflows to design around:

1. Configure a shielding study, validate assumptions, run analysis, and export defensible results.
2. Compare materials or scenarios across methods with consistent charts, tables, and narrative summaries.
3. Review operational state, quotas, provenance, and run outputs as an admin or reviewer.

Actions by weakness:

- Weakness 5:
  - Redesign around workflow entry points instead of content buckets.
  - Standardize page anatomy: hero, assumptions, controls, primary result, supporting analysis, export, provenance.
- Weakness 6:
  - Expose operational trust signals in-product where relevant: provenance, quotas, validation status, release context.
- Weakness 8:
  - Align visible product claims with the maturity of the implemented workflow, not aspirational language.

Exit criteria:

- A user can complete each top workflow without jumping through inconsistent interaction patterns.
- Navigation reflects product logic rather than historical page growth.
- Product copy and UX no longer overclaim relative to implementation truth.

## Phase 3: Structural Separation and Platform Legibility

Timeline: 3 to 6 months

Goal:
Reduce architectural ambiguity and make the platform easier to trust, operate, and evolve.

Deliverables:

- Repository boundary model and package ownership chart
- Clear separation between product code, research/validation assets, and generated artefacts
- Canonical architecture document mapping product surfaces to platform services and controls
- Packaging and release model that distinguishes shipped product from supporting research material

Actions by weakness:

- Weakness 3 and 9:
  - Define which directories are product runtime, platform support, validation evidence, generated output, or working material.
  - Reduce visible construction noise in the main workspace.
  - Ensure backup, benchmark, and generated result handling follows a deliberate storage policy.
- Weakness 6:
  - Write one architecture narrative explaining how UI, API, worker, infra, observability, and scientific core relate.
  - Make admin and operations surfaces mirror this narrative.

Exit criteria:

- A new contributor can understand system boundaries quickly from the repo shape and docs.
- Product trust no longer depends on knowing hidden context from prior team decisions.
- Release artefacts and research artefacts are clearly separated.

## Phase 4: Shell Hardening or Shell Migration

Timeline: 3 to 9 months depending on strategy

Goal:
Resolve the most important structural question instead of carrying it indefinitely.

If Streamlit remains the shell:

- Build a formal shell layer with zero direct framework chrome exposure.
- Restrict all product-facing page assembly to approved primitives.
- Add regression tests for shell behavior, accessibility basics, and layout integrity.
- Treat framework upgrades as controlled platform events with visual regression gates.

If Streamlit is transitional:

- Define the seam to preserve:
  - domain models
  - analysis services
  - plotting/export pipeline
  - auth/session contracts
  - API/worker integration
- Rebuild only the shell and workflow layer first.
- Migrate page by page based on workflow importance, not based on which page is easiest.

Decision rule:

- Keep Streamlit only if the team accepts its constraints and can enforce disciplined wrappers.
- Migrate if the product roadmap requires UX control, accessibility posture, shell stability, and product behavior beyond what disciplined containment can realistically sustain.

Exit criteria:

- The shell is no longer the least convincing layer of the product.
- The platform no longer relies on concealment of framework behavior to look professional.

## Phase 5: Enterprise Operating Model

Timeline: 6 to 12 months

Goal:
Back the product story with an operating model that is visible, measurable, and auditable.

Deliverables:

- Published architecture narrative and operating model
- Service ownership matrix and escalation model
- SLO/SLA-aligned product surfaces for health, provenance, export, and admin controls
- Release governance tying UX, scientific validity, and platform policy together

Actions:

1. Define service owners for UI, API, worker, infra, validation, and documentation.
2. Make release criteria explicit across three axes: scientific quality, product quality, platform quality.
3. Publish a roadmap cadence with quarterly platform debt reduction targets.
4. Add executive-level KPIs that reflect trust, not just throughput.

Exit criteria:

- Operational maturity is legible inside the product, not only in supporting documents.
- Releases communicate what is guaranteed, what is experimental, and what is internal.
- The platform can survive external scrutiny without relying on explanatory context from the core team.

## Weakness-to-Roadmap Mapping

| Weakness | Primary phase | Primary workstream |
| --- | --- | --- |
| 1. UI shell is framework-constrained | Phase 0, 4 | WS-UX-SHELL |
| 2. Styling is not governed like a design system | Phase 1 | WS-DESIGN-SYSTEM |
| 3. Platform boundary is too broad | Phase 3 | WS-ARCH |
| 4. Visualization quality lacks enforcement | Phase 1 | WS-VIZ-GOV |
| 5. Experience is cleaner than the interaction model | Phase 2 | WS-UX-SHELL |
| 6. Operational maturity is under-legible | Phase 2, 3, 5 | WS-OPS-LEGIBILITY |
| 7. Quality depends on disciplined humans | Phase 1, 5 | WS-GOVERNANCE |
| 8. Branding outruns platform truth | Phase 2, 5 | WS-UX-SHELL |
| 9. Repo shows active construction in visible areas | Phase 0, 3 | WS-ARCH |
| 10. Main bottleneck is simplification | Phase 3, 4, 5 | WS-ARCH |

## 30 / 60 / 90 Day Priorities

### First 30 days

- Make the shell strategy decision.
- Freeze ad hoc UI pattern growth.
- Split styling into governed layers.
- Centralize figure finishing and enforce approved plot patterns.
- Clean repo hygiene issues that most visibly weaken confidence.

### By 60 days

- Ship approved page scaffolds and workflow-aligned navigation.
- Expose key trust signals in the UX where users actually need them.
- Define ownership boundaries and release boundaries.
- Publish the canonical architecture narrative.

### By 90 days

- Complete the redesign of the top 3 workflows.
- Eliminate the highest-value shell and page exceptions.
- Lock structural guardrails into CI and contribution rules.
- Decide whether shell hardening is sufficient or whether migration begins.

## Success Metrics

Track these metrics at the program level:

- `% pages using approved scaffold`
- `% UI surfaces using approved shared components only`
- `% figure outputs using approved shared visualization pipeline`
- `count of page-local style exceptions`
- `count of repo-visible backup/generated artefact paths`
- `time to add a new page using approved scaffold`
- `number of CI catches for structural regressions per month`
- `top-workflow completion rate without UX exception handling`
- `number of enterprise claims backed by visible product capability`

## Governance Model

Use a weekly platform review with these standing questions:

1. Did we reduce structural debt this week, or only restyle it?
2. Did we make the correct path easier than the shortcut?
3. Did we reduce surface area, or add another exception?
4. Did product claims move closer to implementation truth?

Require an ADR for:

- shell strategy changes
- component model changes
- navigation model changes
- repo boundary changes
- release policy changes

## Recommended sequencing rule

Do not spend another major cycle on visual polish without first completing Phase 0 and Phase 1. The platform has already extracted most of the value available from cosmetic improvement alone.

The next return comes from shape, enforcement, and product logic.

## Closing View

ShieldLab G4 is not failing because it lacks substance.

It is at risk of underselling its substance through a delivery shape that still shows too much of its prototype ancestry.

That is a fixable problem. But it stops being a design problem at this stage. It is now an architecture, governance, and product-boundary problem.
