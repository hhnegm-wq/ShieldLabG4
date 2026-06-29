# ShieldLabG4 — Enterprise Implementation & Remediation Plan

**Status:** Draft v1.0
**Author:** Platform Review Board
**Date:** 2026-05-11
**Companion document:** [platform_evaluation_report.md](platform_evaluation_report.md) (fire review, score 6.2/10)
**Scope:** Convert ShieldLabG4 from a research-grade prototype into a publication-credible, enterprise-grade radiation-shielding simulation platform.

---

## 0. Executive Summary

The fire review identified ten classes of blocking issues spanning physics fidelity, scientific provenance, software engineering, security, and release governance. This plan converts every finding into an owned, time-boxed, acceptance-tested workstream organized into **five phases** and **seven workstreams**. The plan is designed so that:

- **Phase 0 (Stop-the-Bleed)** removes shipping risk in days, not weeks.
- **Phase 1 (Scientific Core)** restores defensible physics output and provenance.
- **Phase 2 (Enterprise Hardening)** makes the platform safe for external/paying users.
- **Phase 3 (Publication Readiness)** clears the bar for peer-reviewed submission.
- **Phase 4 (Cloud / SaaS Scale)** enables multi-tenant production operation.

Exit from each phase requires the **Acceptance Criteria** in §6 to be signed off by the named owner roles.

---

## 1. Vision & Definition of "Done"

> A reviewer (regulatory physicist *or* senior software engineer) receiving a frozen ShieldLabG4 build must be able to:
> 1. Reproduce any published figure bit-for-bit from a single command using a captured manifest (config + seed + git SHA + container digest).
> 2. Inspect detector-resolved tallies (not only world-boundary primaries) with reported statistical uncertainty.
> 3. Verify every plotted reference curve against a citable source recorded in the artifact metadata.
> 4. Trust that the release-gate badge (`PASS`) implies *both* CI green *and* publication-readiness green — never one without the other.
> 5. Run the hosted SaaS instance with enforced authentication, per-tenant isolation, audited logs, and documented data-retention.

Anything short of this is "not done."

---

## 2. Workstreams & Owners

| ID | Workstream | Owner role | Primary deliverables |
|----|------------|------------|----------------------|
| WS-PHY | Physics & Validation | Lead Medical/Health Physicist | Detector scoring, buildup validation, MC uncertainty, reference traceability |
| WS-SE  | Software Engineering (C++/Py) | Tech Lead | Refactors, schemas, type safety, test pyramid |
| WS-DEV | DevOps / Cloud | SRE Lead | CI/CD, release gate, IaC, observability |
| WS-SEC | Security & Compliance | Security Officer | AuthN/AuthZ, CORS, secrets, data classification |
| WS-QA  | QA & Testing | QA Lead | Test taxonomy, coverage gates, regression matrices |
| WS-DOC | Documentation & Methods | Scientific Writer | Methods doc, schemas, traceability matrix, ADRs |
| WS-UX  | UX / Reporting | UX Lead | Figure quality, uncertainty bars, comparison page rebuild |

---

## 3. Phased Roadmap

Each phase lists **gap → action → artifact → owner → acceptance**.

### Phase 0 — Stop-the-Bleed (Immediate Blockers)

Goal: nothing in `main` may mislead a user about credibility or expose untrusted endpoints.

| # | Gap (from fire review) | Action | Artifact | Owner | Acceptance |
|---|------------------------|--------|----------|-------|------------|
| 0.1 | API key check is a stub; CORS `allow_origins=["*"]` | Replace stub with real verifier; lock CORS to configured origins; add rate limiting | [api/main.py](api/main.py), `api/security.py` (new) | WS-SEC | OWASP ZAP baseline scan: 0 highs |
| 0.2 | `comparison.py` ships "Placeholder A/B" fallback | Remove fallback; surface explicit empty-state with CTA to load a real run | [ui/pages/comparison.py](ui/pages/comparison.py) | WS-UX | No string `Placeholder` in `ui/` |
| 0.3 | Release gate `PASS` while `q1_publication_ready=false` | Split gate into `ci_gate` and `science_gate`; badge requires both | `tools/release_gate.py`, [docs/validation/](docs/validation/) | WS-DEV | Gate fails on current artifacts |
| 0.4 | Reference label `example_baseline_replace_with_xcom_or_paper` in shipped CSV | Block release if any reference row lacks DOI/URL + retrieval date | `tools/reference_provenance_check.py` (new) | WS-PHY | CI fails on placeholder source |
| 0.5 | `backups/` committed to repo | Move to artifact storage; add to `.gitignore`; rewrite history if licenses permit | repo root | WS-SE | `git ls-files backups/` empty |
| 0.6 | No seed control exposed | Add `--seed` CLI/macro flag; persist seed + RNG engine name in `run_summary.csv` | [app/ShieldLabG4.cc](app/ShieldLabG4.cc), [src/RunAction.cc](src/RunAction.cc) | WS-PHY | Two runs with same seed → byte-identical tallies |

**Exit criterion:** A fresh clone + `make release-check` returns FAIL today and PASS only after 0.1–0.6 are merged.

---

### Phase 1 — Scientific Core

Goal: outputs are physically defensible and traceable.

| # | Gap | Action | Artifact | Owner | Acceptance |
|---|-----|--------|----------|-------|------------|
| 1.1 | Only primary world-boundary transmission is scored | Introduce `G4MultiFunctionalDetector` with `G4PSDoseDeposit`, `G4PSEnergyDeposit`, `G4PSFlatSurfaceCurrent` per layer + behind-shield detector volume | new [include/SensitiveDetectors.hh](include/SensitiveDetectors.hh), [src/DetectorConstruction.cc](src/DetectorConstruction.cc) | WS-PHY+WS-SE | `run_summary.csv` includes per-detector dose, fluence, current with σ |
| 1.2 | No MC statistical uncertainty reported | Compute per-bin σ via batch means (≥10 batches); store in CSV; plot error bars | [src/RunAction.cc](src/RunAction.cc), `python/shieldlab/viz/` | WS-PHY | All shipped figures show σ or σ-band |
| 1.3 | Buildup validation labelled "scaffold" in UI | Implement reference dataset loader for ANSI/ANS-6.4.3-1991 (Water/Concrete/Iron/Lead); compute B-factor residuals; gate publication on |Δ| ≤ tolerance | `python/shieldlab/physics/buildup_validation.py` (new), `tests/benchmarks/test_buildup_ansi.py` | WS-PHY+WS-QA | Mean abs residual < 5% across 4 materials × 6 energies × 7 mfp |
| 1.4 | No detector-response model (ambient dose H*(10), tissue dose) | Add ICRP-74 fluence-to-dose conversion module; expose as scoring filter | `python/shieldlab/physics/dose_conversion.py` (new) | WS-PHY | Unit test vs ICRP-74 Table A.21 within 1% |
| 1.5 | Multi-threading correctness unverified | Add MT vs sequential consistency test (10 seeds × MT on/off); document or disable MT until passing | `tests/benchmarks/test_mt_consistency.py` | WS-QA | MT result within 2σ of sequential for ≥9/10 seeds |
| 1.6 | Reference curves lack provenance metadata | JSON sidecar per reference dataset (DOI, URL, retrieved_at, license, columns_units); enforce schema | `data/references/*.json`, `python/shieldlab/data/reference_loader.py` | WS-DOC+WS-PHY | All reference plots resolve to a sidecar in CI |
| 1.7 | No coupled e–γ / bremsstrahlung treatment for high-Z | Switch default physics list to `G4EmStandardPhysics_option4` *plus* explicit electron/positron production cuts; document choice | [src/PhysicsList](src/) (or main), ADR | WS-PHY | ADR merged; cut study figure in `docs/validation/` |

**Exit criterion:** Independent physicist can reproduce a buildup curve with σ-bars from a single macro and find every reference DOI.

---

### Phase 2 — Enterprise Hardening

Goal: safe for external multi-user deployment.

| # | Gap | Action | Artifact | Owner | Acceptance |
|---|-----|--------|----------|-------|------------|
| 2.1 | Stubbed JWT / license tier system | Replace with Auth0 / Azure AD B2C / Entra ID; map tiers to scopes; rotate license signing keys | [ui/auth.py](ui/auth.py), [api/main.py](api/main.py), `infra/main.bicep` | WS-SEC | Pen-test report attached to release |
| 2.2 | No input schema validation at API boundary | Pydantic models for every request; reject unknown fields; size limits | `api/schemas/` (new) | WS-SE | Fuzz test (1k payloads) → 0 unhandled 500s |
| 2.3 | Secrets management ad-hoc | Move to Azure Key Vault + managed identity; remove env-var fallbacks for prod | `infra/main.bicep`, `api/security.py` | WS-SEC+WS-DEV | No secret value in repo or pipeline logs |
| 2.4 | No structured logging / tracing | Adopt OpenTelemetry; ship to Azure Monitor; correlation IDs end-to-end | `api/`, `worker/`, `ui/` | WS-DEV | Trace from UI click → worker job visible |
| 2.5 | No rate limiting / quota | Per-tenant quotas (jobs/day, CPU-min/month) | `api/middleware/quota.py` (new) | WS-SEC | Load test demonstrates throttling |
| 2.6 | Worker queue lacks DLQ + retry policy | Define poison-message DLQ, exponential retry, idempotency keys | [worker/](worker/), Bicep | WS-DEV | Chaos test: kill worker mid-job → job recovers or surfaces failure |
| 2.7 | No data classification / retention policy | Tag datasets (public / tenant / PII-none); document retention; implement TTL on blob containers | `docs/data_governance.md` (new), Bicep | WS-SEC+WS-DOC | Policy doc signed; lifecycle rules in IaC |
| 2.8 | No SBOM / supply-chain scanning | Add `pip-audit`, `cargo-audit` n/a, `trivy` for containers, SBOM (CycloneDX) per release | `.github/workflows/security.yml` | WS-SEC | SBOM artifact attached to GitHub release |

**Exit criterion:** Third-party security review passes with no Highs; SLO doc (uptime, latency, RPO/RTO) published.

---

### Phase 3 — Publication Readiness

Goal: clear the bar for peer-reviewed submission and regulator scrutiny.

| # | Gap | Action | Artifact | Owner | Acceptance |
|---|-----|--------|----------|-------|------------|
| 3.1 | `q1_publication_ready=false` due to missing thresholds/provenance/statistics | Define numeric thresholds per benchmark; wire into `science_gate` | [docs/validation/](docs/validation/), `tools/science_gate.py` | WS-PHY | Gate green on a real release tag |
| 3.2 | No authoritative Methods document | Write `docs/methods.md` covering geometry, physics list, scoring, uncertainty, validation, limitations | `docs/methods.md` (new) | WS-DOC+WS-PHY | Reviewed by external SME |
| 3.3 | No traceability matrix (requirement → code → test → result) | Generate matrix from code annotations (`@requirement(REQ-xxx)`) | `tools/traceability.py` (new), `docs/traceability_matrix.md` | WS-QA+WS-DOC | 100% of REQs traced |
| 3.4 | Figures lack publication polish (DPI, fonts, colour-blind palettes, units, error bars, legends) | Adopt single `viz` style module enforcing Matplotlib rcParams; CI lint forbids `plt.show` styling drift | `python/shieldlab/viz/style.py` | WS-UX | All figures pass `tools/figure_audit.py` |
| 3.5 | No code/data citation pathway | Mint Zenodo DOI per release; CITATION.cff in repo | `CITATION.cff`, release workflow | WS-DOC | DOI in README on next tag |
| 3.6 | No reproducibility manifest | Per run, emit `manifest.json` with git SHA, container digest, seed, config hash, environment lockfile | `python/shieldlab/io/manifest.py` (new) | WS-PHY+WS-DEV | Re-run from manifest reproduces hashes |

**Exit criterion:** Submission-ready bundle (paper + code + data + manifest + DOI) builds in CI from a tag.

---

### Phase 4 — Cloud / SaaS Scale

Goal: multi-tenant, observable, cost-controlled production service.

| # | Gap | Action | Artifact | Owner | Acceptance |
|---|-----|--------|----------|-------|------------|
| 4.1 | Single-tenant assumptions | Tenant-scoped storage prefixes, RBAC, per-tenant quotas | `infra/`, `api/` | WS-DEV+WS-SEC | E2E test: tenant A cannot read tenant B blobs |
| 4.2 | No autoscaling for worker | KEDA on AKS scaling on queue length | [deploy/aks/](deploy/aks/) | WS-DEV | Load test: queue depth drives pod count |
| 4.3 | No cost guardrails | Azure budget alerts; per-tenant cost attribution tags | Bicep | WS-DEV | Alert fires in staging at 80% budget |
| 4.4 | No DR / backup story | Geo-redundant storage; documented restore drill | `docs/dr_runbook.md` | WS-DEV | Restore drill executed quarterly |
| 4.5 | No status page / SLOs published | SLO doc + public status endpoint | `docs/slo.md`, `api/health.py` | WS-DEV | SLO dashboard live |

**Exit criterion:** GA announcement gated on passing a 72-hour soak test and DR drill.

---

## 4. Test Pyramid Redesign (WS-QA, cross-cutting)

Adopt strict pytest markers and CI lanes:

| Marker | Scope | Runs in |
|--------|-------|---------|
| `unit` | Pure-Python, < 100 ms | Every PR |
| `integration` | Cross-module, no network | Every PR |
| `network` | External HTTP (NIST XCOM, etc.) | Nightly |
| `ui` | Streamlit / Playwright | Nightly + pre-release |
| `geant4` | Requires Geant4 binary | Nightly + pre-release |
| `slow` | > 30 s | Nightly |
| `publication` | Validates publication thresholds | Pre-release only, blocking |

C++ side: introduce **GoogleTest** suite under `tests/cpp/` for `MaterialRegistry`, `DetectorConstruction` geometry hashes, `RunAction` aggregation. Wire into CMake `ctest`.

Coverage gates: Python ≥ 80% (unit+integration), C++ ≥ 60% on changed files (gcov + gcovr).

---

## 5. Documentation Deliverables (WS-DOC)

| Doc | Purpose | Phase |
|-----|---------|-------|
| `docs/methods.md` | Authoritative physics & numerical methods | 1–3 |
| `docs/architecture.md` + C4 diagrams | System design | 2 |
| `docs/data_governance.md` | Classification, retention, PII posture | 2 |
| `docs/security.md` | Threat model, controls, response | 2 |
| `docs/dr_runbook.md` | Backup / restore / failover | 4 |
| `docs/slo.md` | Availability, latency, error budget | 4 |
| `docs/traceability_matrix.md` | Auto-generated REQ↔code↔test | 3 |
| `docs/adr/` | Architecture Decision Records | continuous |
| `CITATION.cff`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` | OSS hygiene | 0–2 |

---

## 6. Acceptance Criteria Summary (per phase)

- **Phase 0 done** when: release-check fails on placeholders/stubs; CORS locked; seed reproducibility test green.
- **Phase 1 done** when: per-detector tallies + σ shipped; ANSI/ANS-6.4.3 buildup validation < 5% mean abs residual; every reference has DOI sidecar.
- **Phase 2 done** when: external pen-test 0 Highs; OpenTelemetry traces end-to-end; SBOM per release; quota + DLQ in place.
- **Phase 3 done** when: `science_gate` green on a tag; Methods doc reviewed; manifest reproduces hashes; Zenodo DOI minted.
- **Phase 4 done** when: multi-tenant isolation test green; KEDA autoscaling demonstrated; DR drill executed; SLO dashboard live.

---

## 7. Risk Register (top 8)

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | Geant4 ABI changes break MT fix | M | H | Pin Geant4 version; container image with digest |
| R2 | ANSI/ANS-6.4.3 dataset licensing constraints | M | M | Confirm redistribution rights; otherwise script-fetch with citation |
| R3 | Auth provider migration breaks existing users | M | H | Dual-run window; migration script; comms plan |
| R4 | Performance regression from per-layer scoring | H | M | Benchmark before/after; optional scoring scopes |
| R5 | Reference provenance gate blocks all releases initially | H | L | Curate top-N references first; allowlist legacy with deprecation date |
| R6 | C++ test infra adoption friction | M | M | Start with smoke tests; expand by module |
| R7 | Cloud cost overrun during load tests | M | M | Budget alerts + auto-shutdown of staging |
| R8 | Scope creep into new physics modules (neutron activation, etc.) | H | M | Freeze scope to fire-review gaps; new features go through ADR |

---

## 8. KPIs / Success Metrics

- **Scientific:** mean abs residual vs ANSI/ANS-6.4.3 buildup; % references with DOI; % figures with σ-bars.
- **Engineering:** test count by marker; coverage %; mean time to green CI; Mean Time To Recovery.
- **Security:** open Highs/Mediums; days since last secret leak; % endpoints behind authN.
- **Product:** active tenants; jobs/day; p95 job latency; cost per 1k jobs.
- **Process:** % PRs with ADR when required; release-gate false-pass count (target 0).

---

## 9. Governance

- **Change Control Board (CCB):** Tech Lead, Lead Physicist, Security Officer, QA Lead. Meets weekly during Phases 0–2.
- **ADR required** for: physics list change, scoring change, auth provider change, storage layout change, public API change.
- **Sign-off:** each phase exit requires written approval (PR comment) from all four CCB roles.
- **Audit trail:** every release tag links to its `science_gate` JSON, SBOM, manifest, and signed-off phase checklist.

---

## 10. Immediate Next Actions (this week)

1. Open tracking issues for every row in §3 Phase 0; label `phase-0`, assign owner roles.
2. Land PR removing `Placeholder A/B` fallback in [ui/pages/comparison.py](ui/pages/comparison.py).
3. Land PR locking CORS in [api/main.py](api/main.py) and replacing the stub auth with a real verifier interface (impl can stub-call Auth0 sandbox).
4. Land PR splitting release gate; flip current artifacts to FAIL until §3 Phase 1 closes.
5. Land PR adding `--seed` and persisting seed in `run_summary.csv`.
6. Schedule CCB kick-off; ratify this plan as v1.0; assign owners by name.

---

*End of plan. Update via PR; bump version on material change. This document supersedes ad-hoc roadmap notes in `ROADMAP.md` for the remediation period.*
