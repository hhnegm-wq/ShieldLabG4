# ADR-0001: Adopt the split CI/science release gate

- Status: Accepted
- Date: 2026-05-11
- Context: The fire review (`docs/platform_evaluation_report.md`) flagged that
  the legacy `release_gate=PASS` field in
  `docs/validation/release_validation_report_latest.json` was set to "pass"
  while `q1_readiness.ready_for_submission` was `false`. This let CI ship
  builds the science gate would have rejected.
- Decision: The summary now exposes three fields:
  - `ci_gate`         — engineering gate (no errors, no failed sets).
  - `science_gate`    — publication gate (thresholds, provenance, statistics).
  - `release_gate`    — combined; "pass" iff both above are "pass".
  Tools and badges must read the named gate matching their intent.
- Consequences:
  - Existing dashboards reading `release_gate` will now see "fail" until the
    science gate passes — this is intended.
  - CI must opt explicitly into the dev profile via
    `shieldlab-release-gate --profile dev` to keep development PRs green.
- References: [platform_implementation_plan.md](../platform_implementation_plan.md) §3 Phase 0, item 0.3.
