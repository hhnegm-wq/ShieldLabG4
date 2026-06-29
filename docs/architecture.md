# Architecture (C4-style summary)

> Last updated: 2026-05-17 — repository boundary and UI shell contract clarified.

## Level 1 – System context

- **Users**: shielding researchers, medical/health physicists, regulatory analysts, SaaS subscribers (free/pro tiers).
- **External systems**: NIST XCOM (data fetch, cached on disk), Azure (compute / storage / queue / Key Vault / Container Registry), Azure Monitor / Application Insights (OTel traces), Auth0/Entra (production SSO — future sprint).

## Level 2 – Containers

| Container | Tech | Responsibility |
| --- | --- | --- |
| `ui/` | Streamlit | Multi-page user interface; PyJWT HS256 tier auth |
| `api/` | FastAPI / uvicorn | REST API (9 endpoints); HMAC auth; rate limit; OTel tracing |
| `api/middleware/` | Starlette BaseHTTPMiddleware | TracingMiddleware + QuotaMiddleware |
| `worker/` | Python + Geant4 binary | Pulls jobs from Azure Queue; DLQ with poison-queue envelope |
| `app/` + `src/` | C++17 / Geant4 11.4 MT | Monte Carlo executable `ShieldLabG4` |
| `python/shieldlab/` | Pure-Python package | Analytical physics, IO, validation, viz, report |
| `infra/` | Bicep | Azure IaC: private endpoints, VNet, storage ACL, identity |

## Repository ownership zones

| Zone | Paths | Role | Shipping status |
| --- | --- | --- | --- |
| Scientific core | `app/`, `src/`, `include/`, `python/shieldlab/physics/`, `python/shieldlab/core/` | Transport engine, analytical physics, numerical methods | Product runtime |
| Product surface | `ui/`, `api/`, `cli/` | User-facing interaction, service APIs, operator workflows | Product runtime |
| Platform services | `worker/`, `python/shieldlab/io/`, `python/shieldlab/viz/`, `tools/` | Orchestration, manifests, reports, export, governance checks | Product/runtime support |
| Infrastructure | `infra/`, `deploy/`, `.github/`, `scripts/` | Deployment, CI/CD, cloud provisioning, operational automation | Deployment support |
| Config and study inputs | `configs/`, `macros/` | Versioned study definitions and deterministic execution inputs | Versioned support asset |
| Validation and publication evidence | `docs/validation/`, `docs/ref_papers/`, `tests/`, `README.md`, `CHANGELOG.md` | Validation record, papers, regression evidence, product narrative | Release evidence/support |
| Local transient artefacts | `backups/`, `results/`, `build/`, `tmp/`, `.benchmarks/`, `.streamlit/`, `streamlit_debug.log` | Local outputs, scratch work, generated binaries, debug state | Must not be treated as source-of-truth |

## Release boundaries

### Ships as product/runtime

- `ui/`
- `api/`
- `worker/`
- `python/shieldlab/`
- `app/`, `src/`, `include/`
- `infra/` and `deploy/` for environment provisioning
- `configs/` and `macros/` when explicitly required by a release bundle

### Ships as validation or governance evidence

- `tests/`
- `docs/validation/`
- selected `tools/` used by release gates, provenance checks, or audits
- `docs/architecture.md`, ADRs, methods, and security/governance documentation

### Does not define the product and must remain disposable

- `backups/`
- `results/`
- `build/`
- `tmp/`
- `.benchmarks/`
- `.streamlit/`
- `streamlit_debug.log`

These paths may exist in local workspaces for execution convenience, but they are not authoritative product source and must not be used as architectural evidence when evaluating platform quality.

## Level 3 – Components

### Analytical physics layer (`python/shieldlab/physics/`)

- `shielding_params.py`  MAC, HVL, TVL, MFP, EBF, Zeff, FNRCS
- `nist_xcom.py`  NIST data fetch + on-disk cache
- `dose_conversion.py`  ICRP-74 H*(10) fluence-to-dose (Table A.21, 25 AP points)
- `dose_rate.py`  Point / line / disk dose-rate; ICRP-74 h*(10); air-kerma Γ
- `buildup_validation.py`  ANSI/ANS-6.4.3 self-consistency validator
- `inverse_design.py`  Newton-iteration required-thickness / density solver
- `klein_nishina.py`  Klein-Nishina dσ/dΩ; polar figures; Thomson limit

### IO and governance layer (`python/shieldlab/io/`)

- `runner.py`  Study orchestrator (macro generation, Geant4 invocation)
- `manifest.py`  Reproducibility manifest: git-SHA, container digest, seed, config hash, python/platform version, requirements hash
- `release_gate.py`  Three-tier gate: `ci_gate` / `science_gate` / `release_gate`
- `release_validation_report.py`  JSON + Markdown gate report with per-metric status

### Validation and CI tools (`tools/`)

- `reference_provenance_check.py`  Blocks placeholder DOIs in CI
- `figure_audit.py`  Source-lint: blocks `plt.show()` and rcParams writes; `--src-only` for PR gate
- `science_gate.py`  Threshold-coverage + provenance + statistical-adequacy checks; zero-coverage fails the gate

### Data layer (`python/shieldlab/data/`)

- `compendium.py`  150 NIST COMPENDIUM materials (ICRU-46/PNNL-15870/NIST)
- `isotopes.py`  100 ICRP-107 isotopes (medical / industrial / environmental)
- `reference_loader.py`  Strict sidecar loader: requires DOI/URL, retrieved_at, licence

### API and security layer (`api/`)

- `main.py`  FastAPI: 9 endpoints + `configure_json_logging()` at startup
- `security.py`  HMAC-SHA256 API-key verify; `RateLimiter`; `allowed_origins`
- `telemetry.py`  `TracingMiddleware` (X-Correlation-Id, OTel spans); `configure_json_logging()` (JSON-lines + correlation filter); graceful degradation: OTLP → AzureMonitor → Console
- `middleware/quota.py`  `QuotaMiddleware`: per-API-key sliding-window jobs/day and CPU-min/day; HTTP 429 + Retry-After on exhaustion

### Visualisation layer (`python/shieldlab/viz/`)

- `style.py`  `apply_journal_style(preset)` — Nature / Elsevier / IEEE / APS / publication_strict; Okabe-Ito 8-colour palette
- `export.py`  `figure_download_buttons()` — 7 formats; Pro-gated ≥300 DPI; Free-tier watermark
- `captions.py`  `auto_caption()` — journal-ready captions for 9 plot types

## Level 4 – Cross-cutting concerns

| Concern | Implementation |
| --- | --- |
| **Auth** | HMAC-SHA256 API key (constant-time); PyJWT HS256 UI tier; `X-API-Key` header |
| **Observability** | `TracingMiddleware` → OTel spans; JSON-lines logging with `correlation_id`; Azure Monitor exporter |
| **Rate limiting** | `RateLimiter` (per-key sliding window) in `api/security.py` |
| **Quota** | `QuotaMiddleware` (per-key jobs/day + CPU-min/day) in `api/middleware/quota.py` |
| **Security CI** | pip-audit, Trivy SARIF, CycloneDX SBOM, Gitleaks (`.github/workflows/security.yml`) |
| **Governance** | `ci_gate` / `science_gate` / `release_gate`; figure-audit `--src-only` on every PR |
| **IaC** | Bicep private endpoints, VNet integration, storage deny-default ACL, `environment().suffixes.storage` |

## Data flow (job submission)

```text
User ──► UI (Streamlit / PyJWT tier)
           │
           ▼
        API /api/v1/jobs/submit
           │  [HMAC auth · QuotaMiddleware · TracingMiddleware · RateLimiter]
           ▼
        Azure Storage Queue
           │
           ▼
        Worker (queue_worker.py)
           │  [DLQ: max_dequeue_count → _move_to_poison()]
           ▼
        ShieldLabG4 (Geant4 11.4 MT)
           │  [--seed · G4MultiFunctionalDetector · layer_dose.csv]
           ▼
        Azure Blob (results/ + manifest.json)
           │
           ▼
        API /api/v1/jobs/<id>/result  ──► UI Results Explorer
```

## ADR index

| ADR | Decision | Status |
| --- | --- | --- |
| ADR-0001 | Async job queue over synchronous API for Geant4 runs | Accepted |
| ADR-0002 | UI shell visual contract for shared page primitives | Accepted |
