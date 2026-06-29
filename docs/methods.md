# ShieldLab G4 — Methods (authoritative)

> This is the single source of truth for the physics, numerical methods,
> uncertainty treatment, validation, and limitations of ShieldLab G4. Any
> claim made elsewhere (UI text, README, paper) must be consistent with
> the statements here. Last updated: 2026-05-11 — reflects Phase 0–2.5
> completion (all six implementation phases).

## 1. Geometry

- Default geometry: 1-D rectangular slab stack with finite transverse extent.
- Each layer is defined by `material`, `thickness_cm`, optional `density_g_cm3`.
- Source axis = +z; downstream face is the "transmission" boundary.
- Finite transverse leakage corrections are **not** applied; users requiring
  broad-beam, infinite-slab geometry must select a transverse size ≥ 10 mfp
  perpendicular to the source axis (UI surfaces a warning otherwise).

## 2. Source

- Default: monoenergetic `G4ParticleGun` emitting along +z from a point upstream
  of the first layer.
- Energy, particle type, and direction are set via macro / study JSON.
- Random seed is **explicit** and persisted (Phase 0 hardening): resolution
  order is `--seed=N` CLI flag → `SHIELDLAB_SEED` env var → wall-clock fallback.
  The chosen seed appears in `run_summary.csv`.

## 3. Physics

- Default modular physics list: `G4EmStandardPhysics_option4(0)` +
  `G4DecayPhysics(0)`. Both are registered explicitly in `app/ShieldLabG4.cc`.
- Override via `SHIELDLAB_PHYSICS_LIST=<reference list name>` (uses
  `G4PhysListFactory`).
- Production cuts are Geant4 defaults; Phase 1 ADR will pin per-region cuts
  for high-Z layers.

## 4. Scoring

| Quantity                                    | Volume / surface          | Reported in                        |
|---------------------------------------------|---------------------------|------------------------------------|
| Primary world-boundary transmission         | Downstream world boundary | `run_summary.csv` (column `transmission_fraction`) |
| Statistical σ on transmission (batch means) | Same                      | `run_summary.csv` (`transmission_sigma`, `batches`) |
| Beer–Lambert μ from primary transmission    | Derived                   | `run_summary.csv` (`linear_attenuation_cm_inv`) — flagged when bounded |
| Per-layer energy deposition (G4PSEnergyDeposit) | Layer volumes         | `layer_dose.csv` (`energy_dep_MeV`, `energy_dep_sigma`) |
| Per-layer dose (G4PSDoseDeposit)            | Layer volumes             | `layer_dose.csv` (`dose_Gy`, `dose_sigma_Gy`) |
| Secondary species at downstream face        | Surface flux              | `secondary_tally.csv`              |
| Broad-beam buildup observable               | Downstream face           | `lcns5_buildup_observable.csv`     |

**Per-layer scoring (Phase 1 — COMPLETE):** `G4MultiFunctionalDetector`
is registered for every layer volume with two primitives:
`G4PSEnergyDeposit` and `G4PSDoseDeposit`. `EventAction` reads the hits
map after each event and accumulates per-layer totals in thread-local
buffers. `RunAction::EndOfRunAction` merges worker-thread accumulators
and writes `layer_dose.csv` with per-event and cumulative columns, plus
batch-means σ columns for both energy deposit and dose.

**Caveats** (must remain visible in the UI and report headers):

- "Transmission" refers to **primary tracks crossing the downstream world
  boundary**, not detector dose. It is not equivalent to the broad-beam
  attenuation a real detector would record.
- The Beer–Lambert μ falls back to a *lower-bound* estimate
  (`-ln(0.5/N) / x`) when no primary transmits. This is flagged as
  `attenuation_estimate_type = lower_bound_zero_transmission`.

## 5. Uncertainty

- Per-run statistical σ on transmission is computed by **batch means**
  (Geant4 events partitioned into ~10 equal batches; sample variance of
  per-batch transmission divided by N_batches gives σ of the mean).
- Per-layer dose and energy-deposit σ are written to `layer_dose.csv`
  (`dose_sigma_Gy`, `energy_dep_sigma` columns) via the same batch-means
  estimator applied to `G4PSEnergyDeposit` / `G4PSDoseDeposit` tallies.
- MT vs serial consistency: `tests/benchmarks/test_mt_consistency.py`
  verifies that per-layer dose from MT and serial runs agree within 2σ
  for ≥ 9 / 10 random seeds. This gate is enforced by `science_gate`
  before any MT result is accepted for publication.
- `tools/figure_audit.py` enforces uncertainty-bar metadata in all stored
  scientific figures (`--src-only` gate on every PR).

## 6. Analytical photon shielding (`shieldlab.physics.shielding_params`)

- MAC (μ/ρ) and MAC_en use NIST XCOM / XrayMassCoef data via
  `nist_xcom.py` (cached on disk).
- HVL = ln 2 / μ; TVL = ln 10 / μ; MFP = 1 / μ. Buildup is applied via
  G-P factors when invoked; analytical attenuation without buildup is
  explicitly **narrow-beam**.
- G-P buildup factors come from ANSI/ANS-6.4.3-1991 (Water, Concrete,
  Iron, Lead).

## 7. Dose conversion

- Photon fluence-to-H*(10) uses ICRP-74 Table A.21
  (`shieldlab.physics.dose_conversion`). Energies outside [0.010, 10.0] MeV
  raise; no silent extrapolation across the photoelectric edge.

## 8. Validation

- ANSI/ANS-6.4.3 buildup: see `python/shieldlab/physics/buildup_validation.py`
  and `tests/benchmarks/test_buildup_ansi.py` (`@pytest.mark.publication`).
  Acceptance: mean |Δ|/B < 5%, max |Δ|/B < 15% per material.
- ICRP-74 unit tests: `tests/test_dose_conversion.py`.
- Reference provenance: `tools/reference_provenance_check.py` blocks any
  release shipping placeholder source labels.
- Combined publication gate: `tools/science_gate.py`.

## 9. Reproducibility

Every result directory must contain a `manifest.json` (see
`shieldlab.io.manifest.build_manifest`) with:
git SHA, container image digest, seed, config hash, python/platform version,
and a hash of the active requirements file. CI for tagged releases attaches
the manifest to the GitHub release.

## 10. Known limitations

- 1-D slab geometry only (no 3-D voxel imports yet).
- Primary transmission scoring and per-layer `G4PSEnergyDeposit`/`G4PSDoseDeposit`
  tallies are fully implemented (Phase 1). Full broad-beam detector-response with
  explicit geometry and response function is a future ROADMAP item.
- Multi-threaded (`SHIELDLAB_RUN_MANAGER=mt`) execution is validated by
  `tests/benchmarks/test_mt_consistency.py` (Phase 1.5, ≤ 2σ / ≥ 9 of 10 seeds);
  this gate is enforced by `science_gate` before MT results are accepted.
- Density during composition sweeps is user-supplied; physical density change
  with composition is not modelled.
- Nanocomposites are homogenised to elemental mass fractions — micro-/nano-
  structure effects are not resolved.
- Licensed ANSI/ANS-6.4.3-1991 buildup coefficient tables are scaffolded;
  full 40-material independent benchmark review is a ROADMAP future sprint.
- Isotope library: 100 isotopes (ICRP-107 subset); expansion to ~1000 is
  a ROADMAP item.
- Neutron transport in Geant4 is not validated beyond fast-neutron removal
  cross-section (FNRCS) analytical screening.

## 11. Observability and audit trail

Every API request carries an `X-Correlation-Id` header (generated if absent)
propagated through `TracingMiddleware` into an OpenTelemetry span
(`api/telemetry.py`). All log records include `correlation_id` via
`_CorrelationFilter`; JSON-lines format ensures machine-parseable audit
trails. Span exporter resolution order: `OTEL_EXPORTER_OTLP_ENDPOINT` →
`APPLICATIONINSIGHTS_CONNECTION_STRING` → `ConsoleSpanExporter` (dev).
Set `SHIELDLAB_OTEL_ENABLED=0` to disable entirely.

## 12. Per-tenant quota

API job submissions (`/api/v1/jobs/submit`) are subject to a sliding-window
quota enforced by `QuotaMiddleware` (`api/middleware/quota.py`):

- **Job quota**: `SHIELDLAB_QUOTA_JOBS_PER_DAY` (default 100) per API key.
- **CPU-minute quota**: `SHIELDLAB_QUOTA_CPU_MINUTES_PER_DAY` (default 500)
  per API key; each submission costs `SHIELDLAB_QUOTA_CPU_COST_MINUTES`
  (default 5.0 min).
- Exceeded quotas return HTTP 429 with `Retry-After` header and JSON body
  `{detail, reason, retry_after_seconds}`.
- Requests without `X-API-Key` bypass quota (anonymous / internal use).

## 13. Change control

- Changes to physics list, default scoring, or buildup tables require an ADR
  under `docs/adr/`.
- This document version: 2.0 (Phase 0–2.5 complete, 2026-05-11).
