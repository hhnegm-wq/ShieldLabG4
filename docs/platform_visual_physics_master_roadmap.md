# ShieldLab G4 Visual + Physics Master Roadmap

Last updated: 2026-05-04  
Owner: Dr. Hani H. Negm  
Status: Working roadmap for platform correction, enhancement, validation, and scientific hardening

---

## 1. Purpose

This document defines the corrective roadmap for two coupled goals:

1. Upgrade ShieldLab G4 into a bright, enterprise-grade scientific platform with stronger clarity, consistency, and perceived trust.
2. Harden the physics, simulation, analytical, comparison, and validation layers so the platform becomes scientifically stronger, more transparent, and less error-prone.

The roadmap is intentionally biased toward scientific credibility first. Visual quality should support scientific trust, not distract from it.

---

## 2. Product Direction

### 2.1 North-Star Vision

ShieldLab G4 should feel like a modern scientific decision platform rather than a collection of pages.

The target experience is:

- Bright and clean enough for enterprise and academic review meetings.
- Dense enough for experts without feeling cluttered.
- Explicit enough that every result can be traced to inputs, assumptions, models, and references.
- Structured enough that a new researcher can move from material definition to benchmark comparison without confusion.

### 2.2 Core Principles

1. Scientific trust before decoration.
2. Clarity before novelty.
3. Consistency before page-level improvisation.
4. Validation and provenance must be visible, not hidden.
5. Every important result should be reproducible and auditable.

---

## 3. Visual Quality Roadmap

## 3.1 Target Visual Identity

The future visual system should be a bright enterprise scientific interface with these characteristics:

- Light primary background, not dark-first.
- Strong dark text and restrained accent colors.
- Minimal glass effects, used only where they add hierarchy.
- Clean sectioning, disciplined spacing, and explicit information grouping.
- Professional tables, charts, and scientific annotation blocks.

This is not a marketing landing-page aesthetic. It is a lab platform aesthetic.

## 3.2 Current Visual Problems To Correct

1. The platform still carries visual artifacts from a darker style direction that weakens consistency.
2. Page heroes are more consistent than before, but the overall page bodies are not yet governed by one strong layout system.
3. Control zones, tables, and evidence sections do not always read as parts of one product family.
4. Chart framing and result presentation need a clearer enterprise reporting style.
5. Some pages are still more "feature surfaces" than "workflow surfaces".

## 3.3 Visual System Corrections

### A. Design Tokens and Theme Governance

Must add:

1. A canonical token system for:
- page background
- elevated surfaces
- panel borders
- primary text
- muted text
- scientific accents
- success, warning, error, validation, and pending states
- chart palette
- spacing scale
- border radii
- shadow depths

2. A single semantic color policy:
- validated: green
- warning: amber
- failed: red
- informational: blue
- scientific/reference: slate or teal

3. A controlled accent policy so no page invents its own color logic.

Should add:

4. CSS variable map for all tokens.
5. Visual regression checklist for core layout classes.

### B. Layout Architecture

Must add:

1. A standard page scaffold:
- page header / purpose
- key metrics row
- main interaction zone
- result zone
- evidence / assumptions / validation zone
- export / provenance zone

2. A consistent max-width strategy and content rhythm across all pages.

3. Standard card types:
- summary card
- control card
- result card
- validation card
- literature/reference card

Should add:

4. Sticky context banner showing current study/material/context when useful.
5. Anchor navigation for long scientific pages.

### C. Typography

Must add:

1. A formal type scale for page titles, section headers, subsection labels, metric labels, table headers, and captions.
2. Better numeric formatting for scientific values.
3. Tabular alignment for numbers in tables.
4. Stronger caption styling for assumptions, notes, and warnings.

Should add:

5. Monospace treatment for units, symbols, config hashes, and study IDs.

### D. Forms and Input UX

Must add:

1. Uniform label-help-error order.
2. Units visible at point of entry for every numeric quantity.
3. Inline scientific validation before computation or run submission.
4. Consistent handling of invalid density, impossible fractions, missing layers, or invalid energy ranges.

Should add:

5. Assumption preview panels before execution.
6. Derived-value previews for important workflows.

### E. Tables and Scientific Data Presentation

Must add:

1. One shared table style across all pages.
2. Fixed column formatting rules for:
- decimals
- scientific notation
- units
- percent differences
- uncertainty columns
- provenance columns

3. Clear table titles and table purpose captions.

Should add:

4. Sticky headers for long outputs.
5. Copy/export buttons near critical tables.

### F. Charts and Result Reporting

Must add:

1. One chart theme for all analytical and benchmark plots.
2. Mandatory axis labels with units.
3. Plot subtitles containing key study assumptions when relevant.
4. Consistent legends, grid behavior, export naming, and reference overlay styling.

Should add:

5. Uncertainty band styling.
6. Literature-vs-simulation residual companion plots where applicable.

### G. Navigation and Workflow Clarity

Must add:

1. Sidebar grouping by workflow, not only by page title.
2. Global visibility of platform mode and current context.
3. Better naming consistency for related pages and actions.

Should add:

4. "Recommended next step" blocks between pages.
5. Cross-links between calculator, study builder, run study, and results explorer.

### H. Accessibility and Enterprise Readiness

Must add:

1. WCAG-conscious contrast ratios.
2. Visible keyboard focus states.
3. Non-color-only encoding for chart meaning and status meaning.
4. Mobile-safe layout behavior for critical actions.

Should add:

5. Reduced-motion mode for data-dense sections.

## 3.4 Visual Execution Phases

### Phase V1: Foundation

1. Finalize bright token system.
2. Replace inconsistent dark residual styling.
3. Standardize layout containers and card classes.

### Phase V2: Workflow Pages

1. Rebuild shielding calculator layout under the new scaffold.
2. Rebuild study builder, run study, and results explorer using the same page grammar.
3. Normalize forms, tables, and chart wrappers.

### Phase V3: Scientific Reporting Quality

1. Upgrade evidence panels, validation summaries, and assumptions blocks.
2. Improve export affordances and scientific captions.
3. Add page-level visual QA checks.

---

## 4. Physics-Core Roadmap

## 4.1 Goal

Every physics-facing module should be accurate, explainable, benchmarked, and transparent about assumptions and limitations.

This means:

- better validation,
- better uncertainty treatment,
- stronger comparison pipelines,
- stronger literature traceability,
- better model diagnostics,
- fewer silent failure modes.

## 4.2 Material Definition and Composition Physics

### Must Add

1. Strict composition closure checks.
2. Explicit normalization warnings when user inputs do not sum to unity.
3. Rejection of negative fractions, NaN values, and duplicate constituent definitions.
4. Unified phase-mixing engine shared across calculator and study builder.
5. Effective phase preview table for all composite input modes.
6. Elemental mass-fraction preview after every resolution pass.
7. Material provenance metadata:
- user-defined
- literature-derived
- estimated
- imported

8. Material fingerprinting or hash for reproducibility.
9. Density validation with scientific plausibility warnings.
10. Explicit weight-fraction vs volume-fraction conversion evidence.

### Should Add

11. Temperature-aware density correction support.
12. Optional porosity or void-fraction handling.
13. Composition uncertainty fields for fractions and density.
14. Automatic warning when a material falls outside typical density or composition ranges.

## 4.3 Source and Beam Physics

### Must Add

1. Monoenergetic and spectral source modes with explicit metadata.
2. Energy-unit normalization and validation everywhere.
3. Directional model transparency.
4. Clear narrow-beam vs broad-beam declaration for every relevant workflow.
5. Detector geometry assumption visibility.

### Should Add

6. Beam divergence controls.
7. Source-size and field-size modeling.
8. Filtered source spectra import.
9. Energy spread / source uncertainty options.

## 4.4 Analytical Shielding Physics

### Must Add

1. Clear validity-domain labeling for analytical formulas.
2. Detection of unphysical outputs at extreme energies or thicknesses.
3. Explicit distinction between direct attenuation, scatter contribution, and buildup use cases.
4. Better explanation of derived quantities:
- MAC
- LAC
- HVL
- TVL
- MFP
- Zeff
- Neff

5. Unit-tested monotonicity and sanity checks where physically expected.

### Should Add

6. Sensitivity analysis on density and composition.
7. Automatic identification of unstable input regimes.

## 4.5 Monte Carlo Physics and Simulation Governance

### Must Add

1. Physics-list provenance stored with each run.
2. Random seed capture for reproducibility.
3. Geometry, build, executable, and environment metadata capture.
4. Run-level quality diagnostics:
- events used
- convergence quality
- warnings
- dropped or invalid records

5. Statistical uncertainty output for key run quantities.
6. Clear distinction between simulation estimate, fitted estimate, and derived estimate.

### Should Add

7. Multi-physics-list comparison mode for sensitivity analysis.
8. Automatic benchmark mode presets by problem type.
9. Early-stop or adaptive histories when uncertainty target is reached.

## 4.6 Secondary Radiation and Transport Diagnostics

### Must Add

1. Better scoring and separation of transmitted, reflected, and absorbed fractions.
2. Stronger secondary tally visibility where data exists.
3. Backscatter ratio and scatter contribution diagnostics where feasible.
4. Explicit region-based or tally-based interpretation notes.

### Should Add

5. Secondary breakdown by particle species and region.
6. Scatter-dominance warnings for broad-beam-like conditions.

## 4.7 Buildup Factors and Broad-Beam Corrections

### Must Add

1. Literature G-P coefficient ingestion with provenance.
2. Evaluated EBF and EABF literature overlays versus energy and depth.
3. Depth parameterization in mean free paths with explicit definition.
4. Traceable source labels including paper, table, and sample.
5. Guardrails for invalid or incomplete coefficient sets.

### Must Add Next

6. Simulation-side buildup observable design.
7. MC-to-literature buildup comparison framework.
8. Residual metrics for buildup comparisons.
9. Depth conversion logic between geometric thickness and mean free paths.

### Should Add

10. Confidence intervals for buildup comparisons.
11. Broad-beam interpretation notes in UI and exports.

## 4.8 Uncertainty Quantification

### Must Add

1. Statistical uncertainty for simulation outputs.
2. Uncertainty schema for analytical inputs.
3. Separation of:
- statistical uncertainty
- input uncertainty
- model uncertainty
- literature uncertainty

4. Standard reporting format: value, uncertainty, confidence level, method.
5. Uncertainty-aware comparison metrics.

### Should Add

6. Fast first-order propagation mode.
7. Optional Monte Carlo uncertainty propagation mode.
8. Sensitivity ranking of input contributors.

## 4.9 Benchmarking and Reference Comparison

### Must Add

1. Expand literature benchmark coverage beyond current attenuation overlays.
2. Standard reference ingestion format for coefficients, buildup factors, and benchmark metadata.
3. Automated residual metrics:
- mean absolute percent difference
- max absolute percent difference
- RMSE
- mean bias

4. Acceptance thresholds per benchmark.
5. Failure-state visibility when a benchmark exceeds tolerance.
6. Results explorer evidence section for benchmark status.

### Should Add

7. Benchmark dashboard summarizing all benchmark studies.
8. Drift monitoring across versions.
9. Automated benchmark report artifact generation.

## 4.10 Schema, Units, and Provenance

### Must Add

1. Schema versioning for study configs and result artifacts.
2. Mandatory unit fields for all physical quantities.
3. Consistent energy-unit conversions and explicit unit reporting.
4. Provenance references in configs, overlays, exports, and reports.
5. No silent fallback when a schema block is unknown or incomplete.

### Should Add

6. Migration helpers for older study schemas.
7. Schema linting before run submission.

## 4.11 Results Explorer Scientific Corrections

### Must Add

1. Assumptions panel for each result set.
2. Literature overlay status block.
3. Residual summary metrics beside overlays.
4. Visibility of reference source and comparison basis.
5. Scientific note when direct comparison is not physically available.

### Should Add

6. Uncertainty ribbons on comparison plots.
7. Outlier-energy diagnostics.
8. Export bundle with plots, tables, assumptions, and provenance manifest.

## 4.12 Study Builder and Run Study Scientific Governance

### Must Add

1. Shared validation messages between builder and calculator.
2. Scientific linting before execution.
3. Pre-run warnings for:
- unrealistic density
- invalid composition closure
- impossible thickness/energy combinations
- unsupported reference comparison mode

4. Better run metadata storage.
5. Better validation summaries after completion.

### Should Add

6. Pre-run checklist UI.
7. Scientific confidence badge or quality state for completed studies.

---

## 5. Validation, Testing, and Scientific Hardening

## 5.1 Mandatory Testing Layers

### Unit Tests

Must cover:

1. Formula parsing.
2. Mixture normalization.
3. Volume-to-mass conversion.
4. Elemental mass fraction resolution.
5. Descriptor calculations.
6. G-P coefficient evaluation.
7. Unit conversion utilities.

### Regression Tests

Must cover:

1. Existing literature benchmarks.
2. LCNS5 buildup ingestion and evaluation.
3. Core calculator outputs for known materials.
4. Results explorer overlay generation.

### Integration Tests

Must cover:

1. Study config to run artifact path.
2. Study config to results explorer path.
3. Reference overlay loading path.
4. Export artifact generation path.

### Numerical Stability Tests

Must cover:

1. Near-zero transmission.
2. Near-unity transmission.
3. Very low energy edge cases.
4. Very high energy edge cases.
5. Very thin and very thick slabs.
6. Missing or partial reference data.

### UI Scientific Consistency Tests

Must cover:

1. Displayed units.
2. Displayed assumptions.
3. Warning visibility.
4. Provenance visibility.
5. Uncertainty labels where available.

## 5.2 Validation Governance

Must add:

1. A validation report pipeline for every release candidate.
2. Named acceptance criteria for each benchmark family.
3. Scientific signoff checklist before claiming a module is validated.
4. Explicit list of validated regimes and non-validated regimes.

Should add:

5. CI benchmark gate that blocks merges on drift.
6. Versioned validation snapshots for publication use.

---

## 6. Documentation and Transparency

## 6.1 Must Add

1. Physics assumptions document for each major calculation family.
2. Reference ingestion rules and review workflow.
3. Explanation of how comparison metrics are computed.
4. Explanation of uncertainty categories and reporting conventions.
5. Scientific glossary for users outside radiation-shielding specialization.

## 6.2 Should Add

6. "Why this warning appears" help patterns in UI.
7. Mini methods notes attached to major plots and exports.
8. Publication-ready wording templates for methods sections.

---

## 7. Delivery Priority

## 7.1 Priority 1: Scientific Hardening Already In Motion

1. Shared material physics explainer and phase-mix preview.
2. Literature G-P buildup table ingestion.
3. Results explorer literature buildup overlays.
4. Syntax and schema validation on touched paths.

## 7.2 Priority 2: Next Required Scientific Work

1. Simulation-side buildup estimator design and implementation.
2. Uncertainty outputs for simulation summaries.
3. Benchmark acceptance thresholds and drift detection.
4. Assumptions/provenance manifest in results explorer and exports.
5. Stronger scientific linting before runs.

## 7.3 Priority 3: Platform-Wide Scientific Maturity

1. Schema versioning and migration support.
2. Expanded benchmark dashboard.
3. Automated validation report per release.
4. Broader sensitivity and uncertainty analysis tools.

## 7.4 Priority 4: Bright Enterprise Visual Pass

1. Bright token system and theme replacement.
2. Shared layout scaffold across all pages.
3. Shared scientific card, table, and chart presentation system.
4. Workflow-based navigation refinements.
5. Accessibility and visual QA standardization.

---

## 8. Definition of Done

An item is not complete until all of the following are true:

1. The feature exists in the product.
2. The output is scientifically understandable in the UI.
3. Units and assumptions are visible.
4. The behavior is covered by tests where applicable.
5. The result is exported with enough provenance to be audited.
6. Validation or benchmark evidence exists if the item claims scientific credibility.
7. The design is visually consistent with the shared system.

---

## 9. Non-Negotiable Standards

1. No silent normalization without telling the user.
2. No silent unit conversion ambiguity.
3. No silent reference mismatch.
4. No hidden scientific assumptions for core results.
5. No raw tracebacks exposed in normal user workflows.
6. No visual styling change that weakens scientific readability.
7. No benchmark claim without stored evidence.

---

## 10. Immediate Action Backlog

## 10.1 Must Do Next

1. Implement simulation-side buildup-comparison architecture.
2. Add uncertainty fields and reporting to core result summaries.
3. Add residual metrics and assumption panels to results explorer.
4. Add benchmark thresholds and automated pass/fail evaluation.
5. Create the bright design token file and page scaffold plan.

## 10.2 Should Do Immediately After

1. Normalize table and chart presentation system.
2. Add schema versioning and provenance manifest support.
3. Add pre-run scientific linting UI.
4. Add benchmark dashboard page.
5. Start page-by-page bright enterprise redesign from the shared system.

---

## 11. Success Criteria

The roadmap is succeeding when:

1. Results are easier to trust at first glance.
2. Benchmark disagreements are visible and diagnosable.
3. Scientific assumptions are visible on every major workflow.
4. Literature overlays are traceable and reproducible.
5. Visual consistency improves without reducing analytical depth.
6. Users can move from material definition to validated comparison with less ambiguity and fewer avoidable errors.
