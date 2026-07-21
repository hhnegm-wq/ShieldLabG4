# ShieldLab G4: A Reproducible, Secure, and Cloud-Ready Software Platform for Radiation Shielding Studies

**Hani H. Negm**  
*Department of Physics, [Institution]*

---

## Abstract

Radiation shielding calculations are typically performed through a disconnected set of web calculators, reference tables, local scripts, and separate Monte Carlo transport runs. This fragmentation makes results difficult to reproduce, compare, or expose as shared services, and it places the burden of provenance tracking entirely on individual researchers.

ShieldLab G4 addresses this through an open-core software platform that integrates a Python analytical shielding library, a Geant4 11.4 Monte Carlo executable, a command-line interface, a Streamlit user interface, a FastAPI service layer, an asynchronous queue worker, and Azure Bicep infrastructure templates into a single reproducible workflow. The platform implements HMAC-SHA256 API authentication, per-tenant quota enforcement, OpenTelemetry tracing with JSON-lines logging, dead-letter queue handling, a five-layer reproducibility model, and a three-tier CI gate model that separates development correctness from science readiness from release readiness.

The automated non-slow test suite reports 155 passing tests across physics, API security, telemetry, quota, dead-letter worker, and benchmark regression coverage. Study configurations are persisted as JSON definitions with deterministic seed resolution, explicit provenance metadata, and structured result manifests. The platform requires Python 3.11 or later and supports local, API, and cloud-worker execution paths.

ShieldLab G4 provides a practical template for converting validated domain calculations into reproducible, auditable, and deployment-ready research platforms. The design separates physics computation from interface, orchestration, and governance concerns, making the platform suitable for both individual research workflows and collaborative cloud deployments.

**Keywords:** research software engineering; Monte Carlo shielding simulation; gamma-ray attenuation; reproducible scientific workflows; software governance; OpenTelemetry

---

## 1. Introduction

Radiation shielding research involves moving between material composition, photon cross-section data, derived shielding metrics, Monte Carlo transport checks, visualisations, and reproducibility evidence. In practice this movement spans multiple disconnected tools: XCOM or WinXCom for photon attenuation cross-sections, Phy-X/PSD for derived parameters such as half-value layer and mean free path, ESTAR/PSTAR for charged-particle stopping powers, separate Monte Carlo input decks, local plotting notebooks, and manual provenance records. Even when each calculation is correct in isolation, the full workflow is difficult to audit, share, or reproduce.

The companion scientific paper addresses the physics validation problem: whether ShieldLab G4 reproduces reference attenuation, stopping-power, buildup, and Geant4 consistency benchmarks across a 56-point dataset spanning seven materials and five particle types [REF-COMPANION]. The present paper addresses a distinct question: how a validated physics workflow can be engineered as a maintainable, secure, observable, and cloud-ready scientific software platform.

The software contribution of ShieldLab G4 rests on the integration of five concerns that research codes typically treat separately:

1. **Reproducible study execution:** JSON study definitions, deterministic seed handling, structured result folders with manifest emission, and provenance hashing.
2. **Multi-surface access:** command-line workflows, Streamlit UI, and FastAPI endpoints over the same computational core without duplicating domain logic.
3. **Operational safety:** HMAC API authentication, CORS allowlists, request validation, rate limiting, and per-tenant quota enforcement.
4. **Research governance:** split `ci_gate`, `science_gate`, and `release_gate` checks, reference-provenance enforcement, and figure-audit rules.
5. **Cloud execution readiness:** asynchronous queue-worker execution, dead-letter handling, Bicep infrastructure-as-code, private endpoints, and OpenTelemetry observability.

This paper is not a replacement for the scientific validation manuscript. It does not reprint the benchmark tables, physics derivations, or literature analysis from that paper. Instead, it documents the software architecture and engineering evidence that make ShieldLab G4 usable as a reproducible platform rather than a collection of isolated calculation scripts.

---

## 2. State of the Field

Several established tools address radiation shielding calculations. ShieldLab G4 occupies a different position in the design space: it focuses on integrated workflow, reproducibility infrastructure, and deployment readiness rather than expanding the physics library.

Table 1 compares ShieldLab G4 against the tools most commonly cited in the gamma-ray shielding literature.

**Table 1.** Feature comparison of radiation shielding and Monte Carlo tools. "Partial" indicates the feature exists but is not integrated into a reproducible workflow pipeline. Checked (✓) means full support; dash (—) means the feature is absent or not available by design.

| Feature | WinXCom | Phy-X/PSD | OpenMC | MCNP6 | ShieldLab G4 |
|---|---|---|---|---|---|
| Open source / open-core | ✓ | Web-only | ✓ | — | ✓ (open-core) |
| Python API | — | — | ✓ | — | ✓ |
| REST API | — | — | — | — | ✓ |
| Command-line interface | — | — | ✓ | Input deck | ✓ |
| Web / interactive UI | Web | Web | — | — | ✓ (Streamlit) |
| Geant4 / MC transport | — | — | ✓ (OpenMC) | ✓ (MCNP) | ✓ (Geant4 11.4) |
| Analytical shielding metrics | ✓ | ✓ | — | — | ✓ |
| Automated CI gates | — | — | Partial | — | ✓ (3-tier) |
| Reproducibility metadata | — | — | Partial | — | ✓ (5-layer) |
| Cloud IaC deployment | — | — | — | — | ✓ (Azure Bicep) |
| OpenTelemetry observability | — | — | — | — | ✓ |
| Per-tenant quota enforcement | — | — | — | — | ✓ |

**WinXCom** [3] provides photon cross-section data through a web interface and Windows desktop application. It covers a broad energy and material range but offers no CLI, API, provenance tracking, or CI integration. It remains the standard reference for cross-section data retrieval.

**Phy-X/PSD** [5] is a web-only shielding parameters calculator covering half-value layer, tenth-value layer, mean free path, exposure buildup factor, and energy absorption buildup factor for a wide range of materials. It provides no local installation, no scripting interface, and no reproducibility metadata. It is the closest existing analogue for the derived-parameter scope of ShieldLab G4's analytical layer.

**OpenMC** [8] is an open-source continuous-energy Monte Carlo code with a comprehensive Python API. Its primary strength is reactor neutronics and shielding; it does not provide integrated analytical shielding workflows, REST endpoints, cloud deployment templates, or governance gates. It is the most comparable open-source MC code.

**MCNP6** [9] is a comprehensive deterministic and Monte Carlo code with a wide user base in shielding and criticality. It uses a text-based input deck paradigm, is distributed under a restricted license, and has no Python-native or REST API layer.

The gap ShieldLab G4 fills is the combination of open-core accessibility, Python-native and REST access, Geant4 MC integration, structured reproducibility, and cloud-deployment readiness in a single codebase. No existing open-core tool in the radiation-shielding literature provides this combination.

---

## 3. Statement of Need

A shielding researcher or regulatory analyst needs to move between material composition, reference cross-section data, shielding metrics, Monte Carlo consistency checks, visualisations, reports, and reproducible evidence. The software problem is not numerical accuracy alone. It is the need for a platform that can:

- execute the same study from CLI, UI, or API without duplicating domain logic;
- persist configuration, seed, environment, and output metadata together;
- distinguish development checks from science-readiness gates from release-readiness gates;
- expose long-running Geant4 jobs asynchronously without blocking web requests;
- handle failed cloud jobs without silent result loss;
- produce publication-ready figures and exports from validated results;
- protect shared deployments through authentication, rate limiting, quota, and network isolation;
- produce logs and traces that make a submitted job auditable after the fact.

ShieldLab G4 is designed around this full lifecycle.

---

## 4. Software Architecture

ShieldLab G4 uses a layered architecture that separates domain physics from interface, orchestration, and deployment concerns (Figure 1).

### 4.1 Core containers

| Container | Technology | Role |
|---|---|---|
| `python/shieldlab/` | Python ≥ 3.11 | Analytical shielding, data loading, IO, validation, reports, visualisation |
| `app/` and `src/` | C++17 / Geant4 11.4 | Monte Carlo executable, per-layer scoring |
| `cli/` | Python | Scriptable local execution and automation |
| `ui/` | Streamlit ≥ 1.35 | Interactive multi-page user interface |
| `api/` | FastAPI ≥ 0.116 / Uvicorn ≥ 0.30 | REST endpoints, middleware stack, job submission |
| `worker/` | Python | Queue-driven Geant4 job execution, dead-letter handling |
| `infra/` | Bicep | Azure resource deployment, network hardening |

Table 2 lists the principal software dependencies and their version constraints.

**Table 2.** Principal software dependencies.

| Component | Version constraint | Role |
|---|---|---|
| Python | ≥ 3.11 | Runtime language |
| Geant4 | 11.4 | Monte Carlo transport |
| FastAPI | ≥ 0.116 | REST framework |
| Uvicorn | ≥ 0.30 | ASGI server |
| Streamlit | ≥ 1.35 | Interactive UI |
| OpenTelemetry SDK | ≥ 1.24 | Tracing and metrics |
| PyJWT | ≥ 2.8 | UI session tiering |
| Azure CLI (Bicep module) | Current | IaC deployment |
| C++ standard | C++17 | Geant4 executable compilation |

### 4.2 Data flow

The primary cloud execution path is asynchronous. A user submits a study through the UI or API. The API validates the request, applies authentication, rate limiting, quota, logging, and tracing middleware, and places a job envelope on an Azure Storage Queue. The worker pulls the message, retrieves the study payload, invokes the Geant4 executable, writes result artifacts and manifests, and routes permanently failed jobs to a poison queue. Results are retrieved through the API or viewed through the UI. Figure 2 shows this middleware stack and the dead-letter branch.

This design avoids binding long Monte Carlo runs to synchronous HTTP request lifetimes and creates a natural audit boundary: submitted request, queued envelope, worker execution log, result manifest, and final result retrieval are all correlated through a single `X-Correlation-Id` header.

### 4.3 Boundary with the scientific manuscript

The companion scientific manuscript validates the physics calculations and Geant4 consistency checks. This software paper treats those validated calculations as domain services and focuses on the implementation architecture around them. Physics equations appear only when needed to explain data provenance or validation gates.

---

## 5. Implementation

### 5.1 Reproducible study execution

Study configuration files in `configs/studies/` define material composition, density, particle type, energy grid, thickness range, event count, and run settings as JSON. The runner generates Geant4 macros or invokes analytical calculations and writes structured outputs under `build/results/`.

Each run emits enough metadata to reproduce or audit the calculation:

- study configuration hash;
- random seed resolution order (`--seed` flag, environment variable, or wall-clock fallback);
- package and platform version metadata;
- result CSV files with explicit quantity columns (including per-layer dose in `layer_dose.csv`);
- manifest data including git SHA, container digest, requirements hash, and physics-list identifier.

### 5.2 API and middleware

The FastAPI layer exposes calculation and job-submission endpoints while keeping domain computation in the shared Python package. Production-facing concerns are implemented as middleware or dependency checks, not inside physics functions. Key controls:

- HMAC-SHA256 API-key verification with constant-time comparison to prevent timing attacks;
- CORS restricted to configured allowed origins;
- sliding-window rate limiting enforced before quota checks;
- request-size limits and path-traversal guards on job submission paths;
- `QuotaMiddleware` enforcing per-key jobs-per-day and CPU-minutes-per-day limits;
- HTTP 429 responses with `Retry-After` metadata for quota exhaustion.

The middleware stack is ordered so that authentication and rate limiting fail fast before quota accounting, avoiding metering of unauthenticated or clearly invalid requests.

### 5.3 Observability

`TracingMiddleware` reads or generates `X-Correlation-Id` for each request and creates OpenTelemetry spans with HTTP method, route, status code, and correlation metadata. `configure_json_logging()` installs JSON-lines logging and injects a default `correlation_id` field into every log record.

Exporter resolution is environment-driven: OTLP endpoint when `OTEL_EXPORTER_OTLP_ENDPOINT` is set, Azure Monitor connection string when `APPLICATIONINSIGHTS_CONNECTION_STRING` is set, or console exporter as fallback. Setting `SHIELDLAB_OTEL_ENABLED=0` disables the full observability stack. This allows the same codebase to run in local development, CI, and cloud contexts without hard dependency on a telemetry backend.

### 5.4 Queue worker and dead-letter path

The worker pulls submitted studies from Azure Storage Queue and invokes the Geant4 binary. To prevent silent failure loops, the job envelope carries dequeue metadata and a maximum dequeue count. Permanently failed jobs are moved to a poison queue with a structured failure envelope that preserves the original payload, failure reason, and dequeue count. This design keeps evidence needed for support or reproducibility analysis: a failed cloud run is auditable from the submission envelope through the poison queue record.

### 5.5 Publication export layer

The visualisation and export layer provides journal-style figure presets, colour-blind-safe palettes, reproducibility footers, vector/raster export options, and caption helpers. A source-level figure audit (`release_gate`) blocks non-reproducible plotting practices such as interactive-only `plt.show()` calls in production code paths. Figures exported through this layer follow the 300 DPI, white-background, four-spine scientific style described in the companion figure style guide.

---

## 6. Illustrative Examples

The following examples show the three primary access modes. All three call the same underlying Python shielding library and are tested in the non-slow automated test suite.

### 6.1 Command-line analytical calculation

The simplest entry point is the CLI runner, which accepts a study configuration file or inline parameters:

```bash
# Analytical gamma-ray attenuation through a 10 cm lead slab at 0.662 MeV
python -m cli.main compute \
    --material lead \
    --density 11.34 \
    --energy 0.662 \
    --thickness 10.0 \
    --output build/results/lead_cs137_10cm/
```

The runner writes a result CSV and a JSON manifest to the output directory. The manifest records the configuration hash, seed, platform metadata, and git SHA so the calculation can be reproduced from the output directory alone.

### 6.2 Python library usage

The analytical shielding library is importable directly for scripted workflows or Jupyter notebooks:

```python
from shieldlab.shielding import ShieldingCalculator
from shieldlab.materials import MaterialRegistry

registry = MaterialRegistry()
lead = registry.get("lead")  # density, composition, XCOM cross-sections

calc = ShieldingCalculator(material=lead)
result = calc.narrow_beam_attenuation(
    energy_MeV=0.662,
    thickness_cm=10.0,
)

print(f"Transmission: {result.transmission:.4f}")
print(f"HVL: {result.hvl_cm:.3f} cm")
print(f"μ/ρ (cm²/g): {result.mu_over_rho:.4f}")
```

All numerical outputs trace to NIST/XCOM reference data loaded from `python/shieldlab/data/`. The `MaterialRegistry` enforces provenance at load time: an unknown material or a mismatched density raises a validation error before any calculation proceeds.

### 6.3 REST API submission

The FastAPI layer exposes the same calculation as a REST endpoint:

```bash
# Analytical attenuation endpoint (synchronous)
curl -X POST https://<host>/api/v1/attenuation \
     -H "X-API-Key: ${SHIELDLAB_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "material": "lead",
       "density": 11.34,
       "energy_MeV": 0.662,
       "thickness_cm": 10.0
     }'
```

The response includes the attenuation result, the correlation ID from the `X-Correlation-Id` response header, and the provenance hash. For long-running Geant4 studies, a separate `/api/v1/jobs/submit` endpoint returns a job ID immediately; the worker processes the job asynchronously and the result is available through `/api/v1/jobs/{job_id}/result`.

### 6.4 End-to-end Geant4 study

A complete Monte Carlo shielding study follows a four-step pattern:

1. **Define** — write a study JSON in `configs/studies/` specifying material, geometry, particle, energy, event count, and physics list.
2. **Submit** — call `/api/v1/jobs/submit` with the study path; the API validates, queues, and returns a job ID.
3. **Execute** — the worker picks up the job, generates the Geant4 macro, invokes the binary, and writes `layer_dose.csv` and the result manifest.
4. **Retrieve** — call `/api/v1/jobs/{job_id}/result` to fetch the manifest and CSV paths; view the per-layer dose profile through the Streamlit results page.

If execution fails after three dequeue attempts, the envelope moves to the poison queue. The failure can be inspected through the Azure Portal or CLI without losing the original study payload.

---

## 7. Figures

The following figures are planned for the submission package. All figures are generated by canonical scripts in `scripts/figures/` and follow the scientific figure style guide: 300 DPI, white background, all four spines visible, inward ticks, DejaVu Sans 11 pt font, and `fig<NN>_<descriptor>.png` filename convention.

**Figure 1** (`fig01_system_architecture.png`): System architecture diagram showing the seven containers — Python library, Geant4 executable, CLI, UI, API/middleware, worker, and Bicep infrastructure — with data flow arrows for the synchronous and asynchronous execution paths and the dead-letter branch.

*Caption.* System architecture of ShieldLab G4. Solid arrows show the primary asynchronous execution path from UI/API through Azure Storage Queue to the worker. Dashed arrows show the dead-letter path for permanently failed jobs. The middleware stack (authentication, rate limiting, quota, OTel) sits between the API router and all domain calls.

**Figure 2** (`fig02_ci_gate_model.png`): Three-tier CI gate model showing `ci_gate`, `science_gate`, and `release_gate` checks, the subset relationship between the tiers, and example checks at each tier (unit tests; benchmark thresholds, provenance coverage; figure audit, SBOM, security scan).

*Caption.* Three-tier CI gate model. `ci_gate` contains development correctness checks. `science_gate` adds benchmark regression thresholds and provenance coverage requirements. `release_gate` requires both gates to pass and adds figure audit, dependency SBOM generation, and security scanning. Zero provenance coverage or zero benchmark threshold coverage fails the `science_gate`.

**Figure 3** (`fig03_attenuation_agreement.png`): Scatter plot of ShieldLab G4 calculated linear attenuation coefficients versus XCOM reference values across the 56-point validation dataset (seven materials, five photon energies), with OLS regression line and 95% confidence interval band. Mean percentage deviation and RMSE annotated. See companion scientific manuscript for full tabulated benchmark results.

*Caption.* Agreement between ShieldLab G4 analytical attenuation coefficients and NIST XCOM reference values for seven shielding materials at five photon energies (56 data points). The regression line and 95% confidence interval band are shown in red. Dashed line: 1:1 agreement. See companion scientific manuscript for numerical benchmark table.

---

## 8. Governance and Quality Assurance

ShieldLab G4 separates ordinary software correctness from science readiness. This distinction is central to the platform design and the primary governance contribution relative to existing shielding tools.

### 8.1 Gate model

| Gate | Purpose | Example checks |
|---|---|---|
| `ci_gate` | Development correctness | imports, unit tests, deterministic offline checks |
| `science_gate` | Scientific readiness | benchmark thresholds, provenance coverage, statistical adequacy |
| `release_gate` | Publication and release readiness | `ci_gate` + `science_gate` + figure audit + SBOM + security workflows |

Zero provenance coverage, zero benchmark threshold coverage, or zero statistical adequacy fails the `science_gate`. This prevents a release artifact from being described as science-ready when the scientific evidence is absent or untested.

### 8.2 Automated tests

The non-slow default test suite reports 155 passing tests with 2 environment-dependent skips. The skipped tests require the Geant4 binary compiled and accessible at `build/ShieldLabG4`; they pass in full-environment CI and are explicitly marked `@pytest.mark.geant4` to make the dependency transparent.

Test markers separate concerns for selective execution:

| Marker | Coverage area |
|---|---|
| *(no marker)* | Unit and offline checks — always run |
| `geant4` | Geant4 binary integration tests |
| `network` | External network calls |
| `ui` | Playwright browser smoke tests |
| `slow` | Long-running benchmarks |
| `publication` | Figure and export checks |

Representative coverage includes physics unit tests, benchmark regressions, API security checks, telemetry correlation, quota enforcement, dead-letter worker paths, and Geant4 multithreading consistency checks.

### 8.3 Security and supply-chain checks

Security automation includes Python dependency audit (`pip-audit`), container vulnerability scan, CycloneDX SBOM generation, and secret scanning. HMAC key comparison uses `hmac.compare_digest()` throughout to prevent timing side-channels. CORS allowlists, request-size limits, and path-traversal guards are applied at the middleware layer before any domain function is called.

---

## 9. Cloud Deployment Design

The Azure deployment uses Bicep infrastructure-as-code. The design includes:

- private endpoints for storage, key vault, and container registry;
- VNet integration for application services;
- storage network ACLs with deny-by-default behavior;
- managed identity for secret retrieval rather than connection string embedding;
- environment-derived DNS suffixes rather than hardcoded cloud domains.

Local execution requires no cloud dependency. Cloud deployment is an optional scaling and collaboration layer. Physics reproducibility does not depend on a specific cloud provider; the study JSON, seed, and manifest are sufficient to reproduce any result locally from the same codebase.

---

## 10. Reproducibility Model

ShieldLab G4 uses a five-layer reproducibility model:

1. **Input reproducibility:** study JSON files, explicit material definitions, density, thickness grid, energy grid, and random seed.
2. **Execution reproducibility:** CLI/API runner, generated Geant4 macro, physics-list metadata, event count, and batch settings.
3. **Output reproducibility:** structured CSV outputs, per-layer dose files, result manifest, statistical uncertainty columns, and figure export metadata.
4. **Review reproducibility:** methods documentation, validation reports, release gates, and companion scientific paper benchmarks.
5. **Operational reproducibility:** correlation IDs, JSON-lines logs, OTel traces, queue envelopes, and dead-letter artifacts for cloud-submitted jobs.

This model is deliberately broader than numerical repeatability. It treats a scientific result as a chain of inputs, execution context, software version, statistical evidence, and review artifacts. Layer 5 applies only to cloud-submitted jobs; Layers 1–4 apply to all execution paths.

---

## 11. Availability and Installation

### 11.1 Repository access

ShieldLab G4 is maintained as an open-core repository. The Python package, Geant4 source, CLI, UI, API, worker, documentation, tests, and Bicep templates are available at the repository root. Scientific validation artifacts are under `docs/validation/`; platform architecture and methods documentation are in `docs/architecture.md` and `docs/methods.md`.

### 11.2 Installation

**Python package (analytical layer only):**

```bash
# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# Install in editable mode with development dependencies
pip install -e ./python[dev]
```

**Geant4 executable (Monte Carlo layer):**

```bash
# Requires Geant4 11.4 and CMake ≥ 3.16
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
```

**Run the non-slow test suite:**

```bash
PYTHONPATH=python pytest -q -m "not geant4 and not ui and not network and not slow"
```

**Run the full test suite (requires Geant4 binary and Playwright):**

```bash
PYTHONPATH=python pytest -q
```

**Start the local UI:**

```bash
PYTHONPATH=python streamlit run ui/app.py
```

**Start the local API:**

```bash
PYTHONPATH=python uvicorn api.main:app --reload --port 8000
```

### 11.3 Reuse modes

ShieldLab G4 supports six reuse modes:

| Mode | Entry point | Use case |
|---|---|---|
| Local CLI | `python -m cli.main` | Scripted individual calculations |
| Python library | `from shieldlab.shielding import ...` | Notebook and pipeline integration |
| Interactive UI | `streamlit run ui/app.py` | Exploratory research |
| REST API | `uvicorn api.main:app` | Programmatic batch access |
| Cloud worker | `worker/Dockerfile` + Bicep | Scalable Monte Carlo orchestration |
| Publication export | `scripts/figures/` scripts | Journal-ready figures and reports |

---

## 12. Limitations

Three limitations are likely to be raised by reviewers and are stated explicitly here.

**L1 — Single cloud provider.** The current infrastructure templates target Azure only. A researcher on AWS or GCP must rewrite the Bicep templates and adapt the queue-worker code for their queue service. The analytical and Monte Carlo layers have no cloud dependency and run identically on any platform.

**L2 — Isotope library scope.** The current isotope library covers 100 ICRP-107 isotopes. Expansion to approximately 1000 remains a roadmap item. Studies requiring isotopes outside this set must either extend the library or use the XCOM/NIST cross-section data directly for those materials.

**L3 — Detector response and broad-beam geometry.** The current Geant4 geometry implements infinite slab attenuation with a point-detector approximation. Broad-beam geometry, energy-dependent detector response functions, and cylindrical or spherical geometry builders are scientific roadmap items. Results from the current implementation represent narrow-beam conditions and should not be applied directly to broad-beam dosimetry without the additional corrections noted in the companion scientific manuscript.

These limitations do not block the scientific manuscript or the current technical contribution, but they define the next platform roadmap iteration.

---

## 13. Discussion

ShieldLab G4 illustrates a general pattern for research software engineering in computational physics: validated calculations are necessary but not sufficient for a usable research platform. A research code becomes a platform when it also provides reproducible inputs, structured outputs, provenance, automated gates, safe remote execution, test separation, deployment automation, and operational observability.

The three-tier gate model is the most important design decision for long-term maintainability. Without an explicit `science_gate` distinct from ordinary CI, benchmark coverage erodes as the codebase grows because there is no automated mechanism to block a release that has lost its scientific evidence. The separation of `ci_gate` from `science_gate` makes this erosion visible and reversible.

The five-layer reproducibility model extends beyond numerical repeatability to include cloud-specific operational artifacts (Layer 5). This is important because a Monte Carlo job submitted to a cloud worker differs from a local run in ways that affect reproducibility: queue serialisation, worker environment, dequeue history, and failure evidence are all relevant to auditing the result. The dead-letter path preserves this evidence even for failed jobs.

The comparison in Table 1 shows that no existing open-core tool combines analytical shielding, MC transport, REST API, cloud deployment, and governance gates. This is not a claim of scientific superiority over MCNP6 or OpenMC in their respective domains; it is a claim of integration coverage for the full workflow lifecycle that a shielding researcher needs from study definition to publication export.

The platform architecture separates concerns so that each layer can be replaced or extended independently. The physics layer can absorb new materials or geometries without touching the API layer. The API layer can be redeployed to a different cloud without touching the physics layer. The governance layer can tighten or loosen gates without touching either. This modularity reduces the cost of the platform evolving alongside the scientific research it supports.

---

## 14. Conclusions

This paper described the technical and software design of ShieldLab G4, a reproducible and cloud-ready platform for radiation shielding studies. The platform integrates a Python analytical library, Geant4 11.4 Monte Carlo executable, CLI, Streamlit UI, FastAPI service with a full middleware stack, asynchronous queue worker, Azure Bicep infrastructure-as-code, OpenTelemetry observability, HMAC security controls, per-tenant quota enforcement, provenance manifests, publication export utilities, and a three-tier science-aware CI gate model.

Five principal conclusions follow from the design and implementation:

1. Separation of physics computation from interface, orchestration, and governance concerns makes the platform independently extensible at each layer.
2. A three-tier gate model that distinguishes `ci_gate`, `science_gate`, and `release_gate` prevents benchmark coverage erosion during codebase growth.
3. A five-layer reproducibility model that includes operational artifacts (correlation IDs, queue envelopes, dead-letter records) extends reproducibility guarantees to cloud-submitted Monte Carlo jobs.
4. Per-tenant quota enforcement with `Retry-After` metadata and HMAC-SHA256 authentication with constant-time comparison are sufficient for shared research deployments without requiring a dedicated API gateway.
5. The open-core, multi-surface access design (CLI, Python, REST, UI, cloud worker) lets the same validated physics library serve individual researchers, automated pipelines, and collaborative cloud deployments without duplicating domain logic.

The companion scientific manuscript establishes physics validity and benchmark accuracy. The present paper establishes the software contribution: a maintainable architecture and operational model for transforming validated shielding calculations into a reproducible, auditable, and deployable scientific platform.

---

## CRediT Author Statement

Hani H. Negm: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Visualization, Writing – original draft, Writing – review and editing.

---

## Conflict of Interest

The author declares no conflict of interest.

---

## Funding

[Funding source or: This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.]

---

## Data and Software Availability

The ShieldLab G4 source code, study configurations, validation assets, documentation, tests, and infrastructure templates are maintained in the project repository. Scientific validation artifacts are located under `docs/validation/`; platform architecture and methods documentation are in `docs/architecture.md` and `docs/methods.md`. The companion scientific manuscript should be cited for benchmark claims; this paper should be cited for architecture, reproducibility model, and platform engineering claims.

---

## References

[1] Agostinelli S, Allison J, Amako K, et al. (2003). Geant4 — a simulation toolkit. *Nuclear Instruments and Methods in Physics Research A*, 506(3), 250–303. https://doi.org/10.1016/S0168-9002(03)01368-8

[2] Allison J, Amako K, Apostolakis J, et al. (2016). Recent developments in Geant4. *Nuclear Instruments and Methods in Physics Research A*, 835, 186–225. https://doi.org/10.1016/j.nima.2016.06.125

[3] Berger M J, Hubbell J H (1987). *XCOM: Photon Cross Sections on a Personal Computer*. NBSIR 87-3597, National Bureau of Standards, Gaithersburg, MD.

[4] Hubbell J H, Seltzer S M (2004). *Tables of X-Ray Mass Attenuation Coefficients and Mass Energy-Absorption Coefficients from 1 keV to 20 MeV for Elements Z = 1 to 92 and 48 Additional Substances of Dosimetric Interest*. NIST Standard Reference Database 126. https://doi.org/10.18434/T4D01F

[5] Şakar E, Özpolat Ö F, Alım B, Sayyed M I, Kurudirek M (2020). Phy-X/PSD: Development of a user friendly online software for calculation of parameters relevant to radiation shielding and dosimetry. *Radiation Physics and Chemistry*, 166, 108496. https://doi.org/10.1016/j.radphyschem.2019.108496

[6] Pélowitz D B (ed.) (2011). *MCNP6 User's Manual*. LA-CP-11-00538, Los Alamos National Laboratory.

[7] FastAPI Documentation. Tiangolo / Sebastián Ramírez. https://fastapi.tiangolo.com (accessed May 2026).

[8] Romano P K, Horelik N E, Herman B R, Nelson A G, Forget B, Smith K (2015). OpenMC: A state-of-the-art Monte Carlo code for research and development. *Annals of Nuclear Energy*, 82, 90–97. https://doi.org/10.1016/j.anucene.2014.07.048

[9] Werner C J et al. (2018). *MCNP6.2 Release Notes*. LA-UR-18-20808, Los Alamos National Laboratory.

[10] OpenTelemetry Authors (2024). *OpenTelemetry Specification v1.32*. https://opentelemetry.io/docs/specs/otel/ (accessed May 2026).

[11] Microsoft Azure (2024). *Azure Well-Architected Framework: Security Pillar*. https://learn.microsoft.com/en-us/azure/well-architected/security/ (accessed May 2026).

[12] Gruhn V, Pieper A, Thißen R (2006). Mining Software Architectures. *Electronic Notes in Theoretical Computer Science*, 163, 3–15.

[REF-COMPANION] Negm H H (2026). Geant4-validated radiation shielding benchmark calculations across seven materials: agreement with NIST XCOM, ESTAR, and Phy-X/PSD reference data. [companion scientific manuscript, same submission package]
