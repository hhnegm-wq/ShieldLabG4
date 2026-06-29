# Changelog

All notable changes to **ShieldLab G4** are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] - 2026-05-11

### Added — Platform Hardening: Security (Phase 0)

- `api/security.py` — Real HMAC-SHA256 API-key verification (`verify_api_key`),
  `RateLimiter` (sliding-window per key, configurable burst/window), `allowed_origins`
  (env-driven allowlist), `default_rate_limiter` factory.
- `api/main.py` — CORS locked to `SHIELDLAB_ALLOWED_ORIGINS`; `JobSubmitRequest`
  with Pydantic validators: max 64 MiB payload, numeric-only run_args, path-traversal
  guard on study path. `/api/v1/jobs/submit`, `/api/v1/jobs/{id}/status`,
  `/api/v1/jobs/{id}/result` endpoints wired.
- `ui/auth.py` — Real PyJWT HS256 licence-key → JWT session auth; graceful `None`
  on any decode error; tier-gating applied consistently across all pages.

### Added — Platform Hardening: Geant4 Scoring (Phase 1)

- `src/DetectorConstruction.cc` — `G4MultiFunctionalDetector` with
  `G4PSEnergyDeposit` + `G4PSDoseDeposit` per layer; multi-thread-safe scorer map.
- `src/EventAction.cc` — hits-map readout; per-event dose/energy tally.
- `src/RunAction.cc` — batch-means σ; cumulative `layer_dose.csv` with uncertainty
  columns; `run_summary.csv` with git-SHA, seed, primary count, wall time.
- `app/ShieldLabG4.cc` — `--seed` CLI flag with env override and wall-clock fallback.
- `python/shieldlab/physics/dose_conversion.py` — ICRP-74 Table A.21 fluence-to-dose
  conversion; 25-point AP geometry coefficients.

### Added — Platform Hardening: Geant4 MT Consistency (Phase 1.5)

- `tests/benchmarks/test_mt_consistency.py` — MT vs serial consistency test across
  10 random seeds; combined-σ criterion (≤ 2σ deviation, ≥ 9/10 seeds); auto-skipped
  unless `SHIELDLAB_TEST_GEANT4=1`; binary lookup via PATH and `build/ShieldLabG4`.

### Added — Platform Hardening: Worker & Auth (Phase 2)

- `worker/queue_worker.py` — Azure Storage Queue worker with Dead-Letter Queue:
  `_move_to_poison()` moves permanently failed jobs to a poison queue; max-dequeue-count
  envelope; structured logging per job lifecycle event.

### Added — Platform Hardening: OpenTelemetry Tracing (Phase 2.4)

- `api/telemetry.py` — `TracingMiddleware(BaseHTTPMiddleware)`: reads/generates
  `X-Correlation-Id` per request, opens OTel span with `http.method`, `http.route`,
  `http.status_code`, `correlation_id` attributes. `configure_json_logging()`:
  replaces root handlers with JSON-lines formatter (`_JsonFormatter`) + correlation
  filter (`_CorrelationFilter`) that injects `correlation_id="-"` default.
  Graceful degradation: ConsoleSpanExporter (dev) → OTLPSpanExporter →
  AzureMonitorTraceExporter based on env vars. `SHIELDLAB_OTEL_ENABLED=0` disables.
- `api/requirements.txt` — Added `opentelemetry-sdk>=1.24`,
  `opentelemetry-exporter-otlp-proto-grpc>=1.24`.

### Added — Platform Hardening: Per-Tenant Quota (Phase 2.5)

- `api/middleware/quota.py` — `QuotaMiddleware(BaseHTTPMiddleware)`: per-API-key
  sliding-window job quota and CPU-minute quota. `_InMemoryQuotaStore` with
  `threading.Lock` per key. Returns `HTTP 429` with `Retry-After` header on
  exhaustion. Env-driven config: `SHIELDLAB_QUOTA_JOBS_PER_DAY` (default 100),
  `SHIELDLAB_QUOTA_CPU_MINUTES_PER_DAY` (default 500), `SHIELDLAB_QUOTA_WINDOW_SECONDS`
  (default 86400), `SHIELDLAB_QUOTA_ENABLED`. No key → passes through.
- `api/middleware/__init__.py` — Package marker.

### Added — Platform Hardening: Security CI (Phase 2.8)

- `.github/workflows/security.yml` — Weekly + PR security scan: `pip-audit` (GHSA
  database), Trivy container SARIF uploaded to GitHub Advanced Security,
  CycloneDX SBOM JSON artifact, Gitleaks secret scan.
- `.github/workflows/release-validation-gate.yml` — Release gate: installs OTel
  deps from `api/requirements.txt`; enforces `ci_gate`, `science_gate`,
  `release_gate` before any release tag is accepted.

### Added — Platform Hardening: Figure Audit CI (Phase 3.4)

- `tools/figure_audit.py` — `--src-only` flag scans `python/shieldlab` and `ui`
  source roots for `plt.show()` calls and `rcParams` writes (write-only regex,
  read-access allowed). `--no-source-lint` disables for release-note generation.
  Integrated into CI release gate.

### Added — Platform Hardening: Cloud Infrastructure (Phase 4)

- `infra/main.bicep` — Private endpoints for Storage, Key Vault, and Container
  Registry; VNet integration for App Service; storage network ACL (deny-by-default);
  DNS using `environment().suffixes.storage` (no hardcoded DNS zones). 0 Bicep
  errors, 0 warnings.

### Added — Platform Hardening: Governance & Documentation

- `conftest.py` — pytest markers: `unit`, `integration`, `network`, `ui`,
  `geant4`, `slow`, `publication`; auto-applied via `pytest.ini`.
- `CITATION.cff` — Machine-readable software citation (CFF 1.2 schema) with DOI
  placeholder, ORCID, and SPDX licence identifier.
- `SECURITY.md` — Vulnerability disclosure policy with GPG fingerprint and 90-day
  coordinated-disclosure timeline.
- `docs/methods.md` — Full physics derivations: XCOM, ESTAR, ICRP-74, G-P buildup,
  FNRCS, inverse design.
- `docs/architecture.md` — C4-style architecture documentation: context, container,
  component diagrams; ADR-0001 (async job queue over synchronous API).
- `docs/data_governance.md` — Data classification, retention, lineage, and GDPR
  compliance notes.
- `docs/slo.md` — Service-level objectives: availability, latency P95, error budget.
- `docs/dr_runbook.md` — Disaster-recovery runbook: RTO/RPO, failover steps,
  chaos-test schedule.

### Added — Tests

- `tests/test_telemetry_and_quota.py` — 20 unit tests: `TestTelemetryModule` (8),
  `TestInMemoryQuotaStore` (5), `TestQuotaMiddlewareStatics` (7). All tests avoid
  TestClient / ASGI to prevent FastAPI ≥0.116 Router initialisation conflicts.
- All tests: **155 passing, 2 skipped** (geant4 binary absent).

### Changed — api/main.py

- `configure_json_logging()` called at startup.
- `TracingMiddleware`, `QuotaMiddleware`, `CORSMiddleware` added in stack order.

---

## [Unreleased]

### Added — Sprint 1: Publication-Quality Export

- `shieldlab/viz/style.py` — Journal matplotlib RC presets: `apply_journal_style(preset)`
  with 5 built-in presets (`nature`, `elsevier`, `ieee`, `aps`, `default`).
  Okabe-Ito 8-colour colour-blind-safe palette as default colour cycle.
  `add_reproducibility_footer(fig, version, label)` stamps UTC timestamp at bottom-right.

- `shieldlab/viz/export.py` — `figure_download_buttons(fig, basename, tier, caption, ...)`:
  renders figure + download buttons for 7 formats (PNG 96/300/600 dpi, SVG, EPS, PDF, TIFF).
  High-resolution formats (≥300 dpi) and vector formats gated to **Pro** tier.
  Free tier figures stamped with a diagonal watermark.

- `shieldlab/viz/captions.py` — `auto_caption(plot_type, ...)` generates
  journal-ready figure captions for all 9 plot types (MAC, HVL/TVL, transmission,
  XCOM, ESTAR, ion range, FNRCS, multilayer, geometry).

- `shieldlab/viz/__init__.py` — Package re-exports (`apply_journal_style`,
  `JOURNAL_PRESETS`, `figure_download_buttons`, `fig_to_bytes`, `auto_caption`).

### Added — Sprint 2: Tier Gating Skeleton

- `ui/auth.py` — `get_user_tier() -> Literal["free","pro"]`, `is_pro()`,
  `render_tier_dev_toggle()` (shown only when `SHIELDLAB_DEV` env var is set).
  Reads from `st.session_state["_tier"]`; Stripe/Auth0 wiring deferred to Sprint 6.

- `ui/components/pro_gate.py` — `pro_only(feature_label, ...)`,
  `pro_download_button(...)`, `pro_badge()` — reusable gating widgets for Pro features.

- `ui/components/__init__.py` — Package marker.

### Changed — Shielding Calculator

- `ui/pages/shielding_calculator.py`:
  - Added `apply_journal_style("default")` at module load for publication-ready figures.
  - All 14 `st.pyplot(fig)` call sites replaced with `figure_download_buttons(fig, ...)`,
    wiring download buttons with captions and tier-aware export for every plot:
    geometry, neutron transmission, Zeff(E), XCOM cross-sections, Zeq/R,
    MAC, HVL/TVL, LAC, MFP, T(x), T(E), multilayer geometry, ESTAR, ion range.
  - `render_tier_dev_toggle()` called at page header for dev tier switching.

### Changed — App Entry Point

- `ui/app.py`:
  - Fixed encoding (was garbled UTF-8 in sidebar title/caption).
  - `render_tier_dev_toggle()` wired into sidebar via guarded import.

---

### Added — Sprint 3: Multi-Material Comparison

- `ui/pages/comparison.py` — side-by-side comparison of up to 6 materials.
  Tabs: MAC vs Energy, HVL/TVL, Transmission at fixed thickness, Radar chart,
  Data table, and Export (Excel + CSV).
  Tier-gated radar chart and Excel export.

---

### Added — Sprint 4: PDF Report Engine

- `python/shieldlab/report/pdf_report.py` — `pdf_bytes(calc_state, figs, version)` →
  bytes via ReportLab. Sections: cover, executive summary, material properties,
  shielding parameters table, transmission curves, ESTAR, ion range, appendix.
- `python/shieldlab/report/__init__.py` — Package re-export.
- Export tab in `shielding_calculator.py`: two-column layout (Excel | PDF).
  PDF generation gated to Pro tier; CSV download always free.

---

### Added — Sprint 5: Physics Completeness

- `python/shieldlab/physics/dose_rate.py` — Dose-rate physics library:
  `dose_rate_point`, `dose_rate_line`, `dose_rate_disk`, `shielded_dose_rate`,
  `fluence_to_h10` (ICRP-74 Table A.41, 25-point AP geometry), `kerma_rate_constant`,
  `air_kerma_rate`, `dose_rate_table`. 15-isotope `GAMMA_K` table.
- `python/shieldlab/physics/klein_nishina.py` — Klein-Nishina cross-section library:
  `compton_energy`, `dsigma_dOmega`, `total_compton_cross_section`,
  `klein_nishina_polar_fig`, `compton_energy_fig`. Thomson limit overlay.
- `python/shieldlab/physics/inverse_design.py` — Inverse shielding design:
  `required_thickness` (Newton iteration), `required_density`, `hvl`, `tvl`,
  `required_thickness_table` (Energy × T% design matrix), `sensitivity_analysis`.
- `ui/pages/dose_rate.py` — Dose-rate calculator Streamlit page.
  Tabs: Dose-Rate Plot, Dose-Rate Table, Air-Kerma & Gamma_k, ICRP-74 h*(10).
  Geometry selector: point / line / disk source. Regulatory reference lines.
- `ui/app.py` — Added Dose-Rate Calculator page to Analysis section of navigation.

---

### Added — Sprint 6: Data Layer

- `python/shieldlab/data/compendium.py` — 85+ NIST COMPENDIUM materials database.
  Categories: tissue, construction, shielding, detector, gas, polymer, other.
  API: `get_by_name`, `search`, `list_names`.
- `python/shieldlab/data/isotopes.py` — ICRP-107/ENSDF isotope library (~40 isotopes).
  Medical, industrial, and environmental categories. API: `get_by_symbol`,
  `half_life_str`, `principal_gammas`, `list_symbols`.
- `python/shieldlab/data/__init__.py` — Package marker with re-exports.
- `python/shieldlab/io/session.py` — Session save/restore to `.shieldlab` JSON.
  `save_session` (with SHA-256 checksum), `load_session` (validates checksum + version),
  `session_download_button`, `session_upload_widget`. NumPy-aware JSON encoder/decoder.

---

### Added — Sprint 7: REST API

- `api/__init__.py` — Package marker.
- `api/main.py` — FastAPI REST service (9 endpoints):
  `GET /`, `GET /api/v1/version`, `POST /api/v1/shielding`, `POST /api/v1/estar`,
  `POST /api/v1/ion`, `POST /api/v1/dose-rate`, `POST /api/v1/compare`,
  `GET /api/v1/compendium`, `GET /api/v1/isotopes`.
  All computation endpoints are Pro-gated via `X-API-Key` header. CORS enabled.
- `api/requirements.txt` — fastapi, uvicorn[standard], pydantic ≥2, numpy, pandas, scipy.

---

### Added — Sprint 8: CLI, Testing & Polish

- `cli/__init__.py` — Package marker.
- `cli/main.py` — Click-based CLI with 8 commands:
  `shieldlab calc`, `shieldlab estar`, `shieldlab ion`, `shieldlab dose-rate`,
  `shieldlab compare`, `shieldlab info mat`, `shieldlab info iso`, `shieldlab report`.
  CSV/JSON/table output formats. Run: `python cli/main.py --help`.
- `ui/components/error_reporter.py` — `render_error_reporter(exc, context)`:
  user-friendly error box with expandable traceback + pre-filled GitHub issue URL.
- Session save/restore wired into `shielding_calculator.py` Export tab.
- NIST cache indicator + "🗑 Clear NIST Cache" button added to `ui/pages/home.py`.
- `tests/__init__.py` — Test package marker.
- `tests/test_physics.py` — Regression tests: Lead MAC@100keV vs NIST, HVL, TVL,
  Klein-Nishina Thomson limit, 180° backscatter, inverse design roundtrip.
- `tests/test_dose_rate.py` — Dose-rate tests: ICRP-74 h*(10) at 1 MeV,
  inverse-square law, linear-in-activity, Cs-137 textbook check, Gamma_k table.
- `tests/test_session.py` — Session I/O roundtrip: numpy arrays, scalars, dicts,
  Path-based load, tampered checksum rejection.

---

## [0.1.0] — 2025-01-01 (baseline)

### Added

- Full analytical shielding calculator: NIST XCOM MAC fetcher + cache,
  Phy-X shielding parameter table (MAC, LAC, HVL, TVL, MFP, Zeff, EBF),
  G-P buildup factor (ANSI/ANS-6.4.3), Fast Neutron Removal Cross Section (NGCal).
- ESTAR electron stopping power (ICRU 37, Bethe–Bloch, within 2% of NIST).
- Ion range (ICRU 49 + ZBL nuclear stopping) for protons and alphas.
- Multi-layer attenuation (Bragg–Gray additive).
- 2D geometry schematic using matplotlib patches.
- 6-mode material composer: formula, elemental mass fractions, compound weight fractions,
  mixture, nanocomposite, volume fractions.
- Standard radiation source library (Cs-137, Co-60, Am-241, etc.).
- Excel export with 6 sheets (parameters, transmission, composition, descriptors,
  ESTAR, ion range).
- Streamlit multi-page app with Study Builder, Run Study, Results Explorer stubs.
