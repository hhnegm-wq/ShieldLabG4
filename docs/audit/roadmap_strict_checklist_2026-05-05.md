# ShieldLab G4 Roadmap Strict Checklist

Date: 2026-05-05
Source roadmap: docs/platform_visual_physics_master_roadmap.md
Scope: strict status check against the actionable backlog and delivery priorities with code evidence.

Status legend:
- [x] Done
- [-] Partial / In progress
- [ ] Pending

## Priority 1: Scientific Hardening Already In Motion

- [x] Shared material physics explainer and phase-mix preview
  Evidence: ui/pages/study_builder.py:32, ui/pages/study_builder.py:45
- [x] Literature G-P buildup table ingestion
  Evidence: python/shieldlab/analysis/benchmarking.py:55
- [x] Results explorer literature buildup overlays
  Evidence: ui/pages/results_explorer.py:489
- [x] Syntax and schema validation on touched paths
  Evidence: python/shieldlab/io/study_validator.py:202, python/shieldlab/io/study_validator.py:351

## Immediate Action Backlog (10.1 Must Do Next)

- [x] Implement simulation-side buildup-comparison architecture
  Evidence: python/shieldlab/analysis/buildup_observable.py:32, python/shieldlab/analysis/comparison.py:216, python/shieldlab/io/runner.py:230
- [x] Add uncertainty fields and reporting to core result summaries
  Evidence: python/shieldlab/io/sweep_collector.py:35, ui/pages/results_explorer.py:447
- [x] Add residual metrics and assumption panels to results explorer
  Evidence: python/shieldlab/analysis/comparison.py:172, ui/pages/results_explorer.py:213, ui/pages/results_explorer.py:394
- [x] Add benchmark thresholds and automated pass/fail evaluation
  Evidence: python/shieldlab/analysis/benchmarking.py:114, configs/studies/literature_benchmark_negm_nio_lcns5_energy.json:144
- [x] Create bright design token file and page scaffold plan
  Evidence: ui/components/platform_settings.py, ui/components/styles.py, ui/components/layout.py, ui/pages/settings.py

## Immediate Action Backlog (10.2 Should Do Immediately After)

- [-] Normalize table and chart presentation system
  Notes: shared theme styles exist, but several pages still include custom inline styles.
  Evidence: ui/components/styles.py:435, ui/pages/home.py:117
- [x] Add schema versioning and provenance manifest support
  Evidence: python/shieldlab/io/schema.py:3, python/shieldlab/io/study_validator.py:204, python/shieldlab/io/runner.py:138, python/shieldlab/io/runner.py:163, python/shieldlab/io/runner.py:286
- [x] Add pre-run scientific linting UI
  Evidence: ui/pages/run_study.py:127, ui/pages/run_study.py:172, python/shieldlab/io/study_validator.py:254
- [x] Add benchmark dashboard page
  Evidence: ui/pages/benchmark_dashboard.py:1
- [-] Start page-by-page bright enterprise redesign from shared system
  Notes: hero/scaffold migration is complete across core pages; deeper per-page content/card normalization remains.
  Evidence: ui/components/layout.py, ui/pages/home.py, ui/pages/comparison.py, ui/pages/results_explorer.py, ui/pages/shielding_calculator.py

## Priority 2: Next Required Scientific Work

- [x] Simulation-side buildup estimator design and implementation
  Evidence: python/shieldlab/analysis/buildup_observable.py:32
- [x] Uncertainty outputs for simulation summaries
  Evidence: python/shieldlab/io/sweep_collector.py:35
- [x] Benchmark acceptance thresholds and drift detection
  Evidence: python/shieldlab/analysis/benchmarking.py:114
- [x] Assumptions/provenance manifest in results explorer and exports
  Evidence: ui/pages/results_explorer.py:213, python/shieldlab/io/runner.py:163
- [x] Stronger scientific linting before runs
  Evidence: python/shieldlab/io/study_validator.py, ui/pages/run_study.py, tests/benchmarks/test_scientific_lint_pack.py

## Priority 3: Platform-Wide Scientific Maturity

- [-] Schema versioning and migration support
  Notes: versioning exists; migration helpers are pending.
  Evidence: python/shieldlab/io/schema.py:3, python/shieldlab/io/study_validator.py:204
- [x] Expanded benchmark dashboard
  Evidence: ui/pages/benchmark_dashboard.py:1
- [x] Automated validation report per release
  Evidence: python/shieldlab/io/release_validation_report.py, tests/benchmarks/test_release_validation_report.py, README.md
- [ ] Broader sensitivity and uncertainty analysis tools
  Notes: baseline uncertainty is implemented, extended sensitivity tooling remains pending.

## Priority 4: Bright Enterprise Visual Pass

- [-] Bright token system and theme replacement
  Evidence: ui/components/platform_settings.py:8, ui/components/styles.py:75
- [-] Shared layout scaffold across all pages
  Notes: shared hero scaffold is now used across pages; remaining layout normalization still in progress.
  Evidence: ui/components/layout.py
- [-] Shared scientific card, table, and chart presentation system
  Evidence: ui/components/styles.py:435
- [ ] Workflow-based navigation refinements
- [-] Accessibility and visual QA standardization
  Evidence: ui/components/styles.py:634

## Non-Negotiables Spot Check

- [x] No silent normalization without telling user
  Evidence: python/shieldlab/io/study_validator.py:91, python/shieldlab/io/study_validator.py:129
- [x] No silent unit conversion ambiguity
  Evidence: python/shieldlab/analysis/comparison.py:44
- [x] No benchmark claim without stored evidence
  Evidence: python/shieldlab/io/runner.py:94, python/shieldlab/io/runner.py:138
- [-] No hidden scientific assumptions for core results
  Notes: assumptions shown in results explorer for study outputs; coverage still needs extension to all workflows.
  Evidence: ui/pages/results_explorer.py:213
