# ShieldLab G4: A Reproducible, Secure, and Cloud-Ready Software Platform for Radiation Shielding Studies

**Hani H. Negm**  
*Department of Physics, [Institution]*

---

## Abstract

Scientific radiation-shielding workflows require not only accurate physics models, but also reproducible execution, traceable data products, secure remote access, publication-quality reporting, and scalable compute orchestration. ShieldLab G4 is an open-core scientific software platform that connects a Python analytical shielding library, a Geant4 11.4 Monte Carlo executable, a Streamlit user interface, a FastAPI service layer, an asynchronous worker path, and Azure infrastructure-as-code into a single reproducible workflow for radiation shielding studies. This technical/software paper describes the platform architecture, implementation strategy, reproducibility model, governance gates, observability layer, security controls, and deployment design. The companion scientific manuscript reports the physics validation and benchmark results; the present paper focuses on software engineering novelty and operational readiness. The platform includes structured study configuration, result manifests, JSON-lines logging with correlation identifiers, OpenTelemetry tracing, per-tenant quota middleware, HMAC API-key authentication, PyJWT-based UI tiering, dead-letter queue handling for failed jobs, publication export utilities, and CI gates for science readiness and security. A non-slow automated test suite currently reports 155 passing tests with 2 environment-dependent skips. The result is a practical template for converting a domain-specific scientific codebase into a reproducible, auditable, and deployment-ready research platform.

**Keywords:** scientific software; radiation shielding; Geant4; reproducibility; FastAPI; Streamlit; Azure; observability; CI/CD; research software engineering

---

## 1. Introduction

Radiation shielding research is commonly performed through a fragmented collection of analytical calculators, tabulated reference data, local scripts, and separate Monte Carlo transport runs. This fragmentation makes it difficult to reproduce published calculations, compare analytical and Monte Carlo outputs, package results for review, or expose validated workflows through secure shared services. The companion scientific paper addresses the physics validation problem: whether ShieldLab G4 reproduces reference attenuation, stopping-power, buildup, and Geant4 consistency benchmarks. The present paper addresses a different question: how such a validated physics workflow can be engineered as a maintainable, secure, observable, and cloud-ready scientific software platform.

The software contribution of ShieldLab G4 is the integration of five concerns that are often treated separately in research codes:

1. **Reproducible study execution:** JSON study definitions, deterministic seed handling, structured result folders, and manifest emission.
2. **Multi-surface access:** command-line workflows, Streamlit UI, and FastAPI endpoints over the same computational core.
3. **Operational safety:** HMAC API authentication, CORS allowlists, request validation, rate limiting, and per-tenant quota enforcement.
4. **Research governance:** split `ci_gate`, `science_gate`, and `release_gate` checks, reference-provenance enforcement, and figure-audit rules.
5. **Cloud execution readiness:** asynchronous queue-worker execution, dead-letter handling, Bicep infrastructure, private endpoints, and observability through OpenTelemetry.

This paper is intentionally not a replacement for the scientific validation manuscript. It does not reprint the benchmark tables, physics derivations, or literature analysis from that paper. Instead, it documents the software architecture and engineering evidence that make ShieldLab G4 usable as a reproducible platform rather than a set of isolated calculation scripts.

---

## 2. Statement of Need

A shielding researcher or regulatory analyst typically needs to move between material composition, reference cross-section data, shielding metrics, Monte Carlo checks, plots, reports, and reproducible evidence. In many projects this path involves multiple tools: XCOM or WinXCom for photon attenuation, Phy-X/PSD for derived shielding parameters, ESTAR/PSTAR/ASTAR for charged-particle stopping, separate Monte Carlo input decks, local plotting notebooks, and manual provenance tracking. Even when each calculation is correct, the full workflow is difficult to audit.

The software problem is therefore not only numerical accuracy. It is the need for a platform that can:

- execute the same study from CLI, UI, or API;
- persist configuration, seed, environment, and output metadata;
- distinguish development checks from science-readiness gates;
- expose long-running Geant4 jobs without blocking web requests;
- handle failed cloud jobs without silent loss;
- provide publication-ready figures and exports;
- protect shared deployments through authentication, rate limiting, quota, and network isolation;
- produce logs and traces that make a submitted job auditable after the fact.

ShieldLab G4 was designed around this full lifecycle.

---

## 3. Software Architecture

ShieldLab G4 uses a layered architecture that separates domain physics from interface, orchestration, and deployment concerns.

### 3.1 Core containers

| Container | Technology | Role |
|---|---|---|
| `python/shieldlab/` | Python | Analytical shielding, data loading, IO, validation, reports, visualisation |
| `app/` and `src/` | C++17 / Geant4 11.4 | Monte Carlo executable for slab studies and per-layer scoring |
| `cli/` | Python CLI | Scriptable local execution and automation |
| `ui/` | Streamlit | Interactive multi-page user interface |
| `api/` | FastAPI / Uvicorn | REST access to calculations and job submission |
| `worker/` | Python worker | Queue-driven Geant4 job execution and dead-letter handling |
| `infra/` | Bicep | Azure resource deployment and network hardening |

### 3.2 Data flow

The primary cloud execution path is asynchronous. A user submits a study through the UI or API. The API validates the request, applies authentication, rate limiting, quota, logging, and tracing middleware, and places a job envelope on an Azure Storage Queue. The worker pulls the message, retrieves the study payload, invokes the Geant4 executable, writes result artifacts and manifests, and moves permanently failed jobs to a poison queue. Results are later retrieved through the API or viewed through the UI.

This design avoids tying long Monte Carlo runs to synchronous HTTP request lifetimes. It also creates a natural audit boundary: submitted request, queued envelope, worker execution log, result manifest, and final result retrieval can all be correlated.

### 3.3 Boundary with the scientific manuscript

The scientific manuscript validates the physics calculations and Geant4 consistency checks. This software paper treats those validated calculations as domain services and focuses on the implementation architecture around them. Physics equations are referenced only when needed to explain data provenance or validation gates.

---

## 4. Implementation

### 4.1 Reproducible study execution

Study configuration files in `configs/studies/` define material composition, density, particle, energy grid, thickness, event count, and run settings. The runner generates Geant4 macros or invokes analytical calculations and writes structured outputs under `build/results/`.

Each run is designed to emit enough metadata to reproduce or audit the calculation:

- study configuration hash;
- random seed resolution order (`--seed`, environment variable, or wall-clock fallback);
- package and platform version metadata;
- result CSV files with explicit quantity columns;
- manifest data including provenance fields such as git SHA, container digest, and requirements hash where available.

### 4.2 API and middleware

The FastAPI layer exposes calculation and job-submission endpoints while keeping domain computation in the shared Python package. Production-facing concerns are implemented as middleware or dependency checks rather than embedded inside physics functions.

Key controls include:

- HMAC-SHA256 API-key verification with constant-time comparison;
- CORS restricted to configured allowed origins;
- sliding-window rate limiting;
- request-size and path-traversal guards in job submission;
- `QuotaMiddleware` enforcing per-key jobs/day and CPU-minutes/day;
- HTTP 429 responses with `Retry-After` metadata for quota exhaustion.

### 4.3 Observability

ShieldLab G4 includes a lightweight observability layer suitable for both local development and cloud deployment. `TracingMiddleware` reads or generates `X-Correlation-Id` for each request and creates OpenTelemetry spans with HTTP method, route, status code, and correlation metadata. `configure_json_logging()` installs JSON-lines logging and injects a default `correlation_id` field into every log record.

Exporter resolution is environment-driven: OTLP endpoint, Azure Monitor connection string, or console exporter. Observability can be disabled with `SHIELDLAB_OTEL_ENABLED=0`. This allows the same codebase to run in local, CI, and cloud contexts without hard dependency on a telemetry backend.

### 4.4 Queue worker and dead-letter path

The worker is responsible for pulling submitted studies from Azure Storage Queue and invoking the Geant4 binary. To prevent silent failure loops, the job envelope carries dequeue metadata and a maximum dequeue count. Permanently failed jobs are moved to a poison queue with a structured failure envelope. This design preserves failed payloads for later inspection and avoids deleting evidence needed for support or reproducibility analysis.

### 4.5 Publication export layer

The visualisation and export layer provides journal-style figure presets, colour-blind-safe palettes, reproducibility footers, vector/raster export options, and caption helpers. The purpose is not to validate scientific content by itself, but to make validated results easier to submit, review, and reproduce. A source-level figure audit blocks non-reproducible plotting practices such as interactive-only `plt.show()` calls in production paths.

---

## 5. Governance and Quality Assurance

ShieldLab G4 separates ordinary software correctness from science-readiness. This distinction is central to the platform design.

### 5.1 Gate model

| Gate | Purpose | Example checks |
|---|---|---|
| `ci_gate` | Development correctness | imports, unit tests, deterministic offline checks |
| `science_gate` | Scientific readiness | benchmark thresholds, provenance coverage, statistical adequacy |
| `release_gate` | Publication/release readiness | `ci_gate` + `science_gate` + figure audit + security workflows |

A key design decision is that zero threshold coverage, zero provenance coverage, or zero statistical adequacy must fail the science gate. This prevents a release artifact from being described as science-ready when the scientific evidence is absent.

### 5.2 Automated tests

The non-slow default suite reports 155 passing tests with 2 environment-dependent skips. Test markers distinguish unit, network, UI, Geant4, publication, and slow checks. This split keeps routine CI deterministic while preserving heavier benchmarks for explicit release or publication contexts.

Representative coverage includes:

- physics unit tests;
- benchmark regressions;
- API security checks;
- telemetry and quota tests;
- dead-letter worker tests;
- Geant4 multithreading consistency benchmark when the binary is available;
- UI smoke tests under explicit opt-in.

### 5.3 Security and supply-chain checks

Security automation includes Python dependency audit, container vulnerability scan, CycloneDX SBOM generation, and secret scanning. These checks support shared or commercial deployments, but they also benefit open research by making dependencies and deployment artifacts easier to audit.

---

## 6. Cloud Deployment Design

The Azure deployment is described as infrastructure-as-code using Bicep. The design includes private endpoints for storage, key vault, and container registry; VNet integration for application services; storage network ACLs with deny-by-default behavior; and environment-derived DNS suffixes rather than hardcoded cloud domains.

The software architecture does not require cloud execution for local research use. Cloud deployment is an optional scaling and collaboration layer. This distinction is important: physics reproducibility should not depend on a specific cloud provider, while operational collaboration can benefit from managed identity, private networking, queue-based workers, and centralized telemetry.

---

## 7. Reproducibility Model

ShieldLab G4 uses a layered reproducibility model:

1. **Input reproducibility:** study JSON files, explicit material definitions, density, thickness, energy grid, and random seed.
2. **Execution reproducibility:** CLI/API runner, generated Geant4 macro, physics-list metadata, event count, and batch settings.
3. **Output reproducibility:** structured CSV outputs, result manifest, statistical uncertainty columns, and figure export metadata.
4. **Review reproducibility:** methods documentation, validation reports, release gates, and companion scientific paper benchmarks.
5. **Operational reproducibility:** correlation IDs, logs, traces, queue envelopes, and dead-letter artifacts for cloud-submitted jobs.

This model is deliberately broader than numerical repeatability. It treats a scientific result as a chain of inputs, execution context, software version, statistical evidence, and review artifacts.

---

## 8. Availability and Reuse

ShieldLab G4 is organized as an open-core repository with a Python package, Geant4 executable source, Streamlit UI, FastAPI service, worker, documentation, tests, and infrastructure templates. Reuse modes include:

- local CLI calculations;
- interactive UI exploration;
- scripted Python workflows;
- REST API batch submission;
- cloud worker execution;
- publication figure/report export.

The scientific validation dataset and manuscript are maintained under `docs/validation/`. The companion scientific manuscript should be cited for benchmark claims; this technical/software paper should be cited for architecture, reproducibility, and platform engineering claims.

---

## 9. Limitations

The current technical platform has several known boundaries:

- Azure Storage Queue is currently used for job orchestration; Azure Service Bus and KEDA autoscaling are future deployment enhancements.
- The isotope library includes 100 ICRP-107 isotopes; expansion to approximately 1000 remains a roadmap item.
- The UI is optimized for desktop workflows; explicit mobile guard and broader visual regression coverage remain future work.
- Geant4 GPS source models, cylindrical/spherical geometry builders, and broad-beam detector-response workflows are scientific roadmap items rather than solved software features.
- Cloud execution is optional and provider-specific in the current infrastructure templates; local execution remains the most portable reproducibility path.

These limitations do not block the scientific manuscript or the current technical/software contribution, but they define the next platform roadmap.

---

## 10. Discussion

ShieldLab G4 illustrates a general pattern for research software engineering in computational physics: validated calculations are necessary but not sufficient. A research code becomes a platform when it also provides reproducible inputs, structured outputs, provenance, automated gates, safe remote execution, test separation, deployment automation, and operational observability.

The most important design choice is the separation of concerns. Physics calculations live in the shared analytical and Geant4 layers. Interfaces call those layers but do not redefine them. Governance gates distinguish ordinary CI from science readiness. The scientific manuscript handles physics validation; this technical/software paper handles architecture and reproducibility. This separation reduces overclaiming and makes the platform easier to review by both scientific and software audiences.

---

## 11. Conclusions

This paper presented the technical/software design of ShieldLab G4, a reproducible and cloud-ready platform for radiation shielding studies. The platform integrates a Python analytical library, Geant4 executable, CLI, Streamlit UI, FastAPI service, asynchronous worker, Azure infrastructure templates, observability, security controls, quota enforcement, provenance manifests, publication export utilities, and science-aware CI gates.

The companion scientific manuscript establishes physics validity and benchmark accuracy. The present paper establishes the software contribution: a maintainable architecture and operational model for transforming validated shielding calculations into a reproducible, auditable, and deployable scientific platform.

---

## CRediT Author Statement

Hani H. Negm: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Visualization, Writing - original draft, Writing - review and editing.

---

## Data and Software Availability

The ShieldLab G4 source code, study configurations, validation assets, documentation, tests, and infrastructure templates are maintained in the project repository. Scientific validation artifacts are located under `docs/validation/`; platform architecture and methods documentation are maintained in `docs/architecture.md` and `docs/methods.md`.

---

## References

[1] Agostinelli S et al. (2003). Geant4 - a simulation toolkit. *Nuclear Instruments and Methods in Physics Research A*, 506(3), 250-303.

[2] Allison J et al. (2016). Recent developments in Geant4. *Nuclear Instruments and Methods in Physics Research A*, 835, 186-225.

[3] Berger M J, Hubbell J H (1987). *XCOM: Photon Cross Sections on a Personal Computer*. NBSIR 87-3597, National Bureau of Standards.

[4] Hubbell J H, Seltzer S M (2004). *Tables of X-Ray Mass Attenuation Coefficients and Mass Energy-Absorption Coefficients*. NIST.

[5] Şakar E, Özpolat Ö F, Alım B, Sayyed M I, Kurudirek M (2020). Phy-X/PSD: Development of a user friendly online software for calculation of parameters relevant to radiation shielding and dosimetry. *Radiation Physics and Chemistry*, 166, 108496.

[6] Microsoft Azure. Azure Well-Architected Framework and Azure Architecture Center documentation.

[7] OpenTelemetry Authors. OpenTelemetry specification and documentation.
