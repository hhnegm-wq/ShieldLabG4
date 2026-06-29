# ShieldLab G4 — Repository Ownership Map

Date: 2026-05-17
Status: Authoritative

This document defines ownership zones for the repository. Every top-level
directory belongs to exactly one zone. Zone boundaries determine what ships
as product, what supports research, and what is transitional infrastructure.

---

## Zone definitions

| Zone | Purpose | Ships as product? |
|------|---------|-------------------|
| **CORE** | Scientific domain library — models, physics, data, validation | No (imported by product) |
| **PRODUCT** | User-facing application layer — UI, API, worker | Yes |
| **PLATFORM** | Deployment, CI, infrastructure | Yes (ops) |
| **RESEARCH** | Validation evidence, literature benchmarks, study configs | No |
| **GENERATED** | Build outputs, results, artifacts | Never tracked |
| **DOCS** | Architecture, ADRs, operational docs | Internal |
| **WORKING** | Temporary scripts, scratch, backups | Never tracked |

---

## Directory mapping

### CORE — `python/`
Owner: Platform architect  
Contents: `shieldlab` Python package — physics engines, material registry, viz, IO, metadata.  
Policy:
- Changes require a unit test in `tests/`.
- Public API changes require an ADR or changelog entry.
- No Streamlit or UI imports allowed here.

### PRODUCT — `ui/`, `api/`, `worker/`
Owner: Product/UX lead (ui), Platform lead (api, worker)  
Contents: Streamlit app, FastAPI service, Celery worker.  
Policy:
- All UI pages must follow ADR-0002 and ADR-0003 visual contract.
- Pages must not import from `app/` (C++ app) directly.
- `ui/components/` is the approved style/component entry point — no ad hoc page-level CSS.
- `api/` and `worker/` must not embed product copy or business logic outside of route handlers.

### PLATFORM — `.github/`, `infra/`, `scripts/`, `tools/`, `deploy/`
Owner: Engineering manager  
Contents: CI workflows, Bicep infrastructure, CI helper scripts, audit/lint tools, deployment configs.  
Policy:
- All CI tools under `tools/` must have a corresponding entry in `release-validation-gate.yml`.
- Infrastructure changes require review by the platform lead before merge.
- No scientific code in this zone.

### RESEARCH — `configs/`, `docs/validation/`, `docs/ref_papers/`
Owner: Data visualization lead / principal engineer  
Contents: Study configuration templates, validation reports, reference literature.  
Policy:
- Study configs are input data, not product code — treat as research artifacts.
- Validation reports are generated outputs; do not hand-edit.
- Reference papers must have provenance records (title, DOI, year).

### DOCS — `docs/`
Owner: Platform lead  
Contents: ADRs, architecture narrative, audit reports, deployment guides, methods documentation.  
Policy:
- ADRs must follow the template in `docs/adr/`.
- Architecture docs must be kept consistent with actual implementation.
- `docs/audit/` contains assessment artifacts — do not delete without sign-off.

### GEANT4 APP — `app/`, `src/`, `include/`
Owner: Platform architect  
Contents: C++ Geant4 application source, headers.  
Policy:
- Build outputs go to `build/` (GENERATED zone — not tracked).
- C++ changes require re-running the simulation validation suite before merge.

### GENERATED — `build/`, `results/`
Owner: No owner (machine-generated)  
Policy: Never committed. Excluded in `.gitignore`. If you see these in the repo, remove them.

### WORKING — `backups/`, `tmp/`
Owner: No owner  
Policy:
- Never committed. Excluded in `.gitignore`.
- `backups/` is for local disaster recovery only — use external artifact storage for anything that must be kept.
- `tmp/` is for throwaway scripts during active debugging — clean up after each session.
- If either directory contains files that belong in a documented zone, move them before closing the work item.

---

## Prohibited patterns

| Pattern | Reason | Zone violation |
|---------|--------|----------------|
| `import streamlit` in `python/shieldlab/` | Framework leak into domain core | CORE ← PRODUCT |
| `unsafe_allow_html=True` in `ui/pages/*.py` | Bypasses ADR-0002 visual contract | PRODUCT internal |
| Matplotlib `rcParams` writes outside `viz/style.py` | Bypasses viz governance | CORE internal |
| `plt.show()` in any source file | Interactive mode in server context | CORE + PRODUCT |
| Committed files in `backups/` or `tmp/` | Working material in source tree | WORKING leak |
| CI tool without `release-validation-gate.yml` entry | Unregistered guardrail | PLATFORM internal |
| New page without `render_page_hero` | Visual contract bypass | PRODUCT internal |

---

## CI enforcement status

| Check | Tool | CI gate | Status |
|-------|------|---------|--------|
| `plt.show()` in source | `tools/figure_audit.py --src-only` | `release-validation-gate.yml` | Active |
| `plt.rcParams` direct writes | `tools/figure_audit.py --src-only` | `release-validation-gate.yml` | Active |
| Contrast ratios | `tools/contrast_audit.py` | `release-validation-gate.yml` | Active |
| Deprecation / text quality | `tools/deprecation_guard.py` | `release-validation-gate.yml` | Active |
| Security scan | `security.yml` | `security.yml` | Active |
| Page scaffold compliance | `tools/page_scaffold_check.py` | `release-validation-gate.yml` | Active |
| UI smoke (Playwright) | `scripts/ci_ui_smoke_gate.sh` | `release-validation-gate.yml` | Active |
| `apply_journal_style` enforcement | `tools/figure_audit.py --check-ui-presets` | `release-validation-gate.yml` | Active |

---

## Release boundaries

**Ships as product:**
- `python/shieldlab/` (as an installed package)
- `ui/` (Streamlit app)
- `api/` (FastAPI service)
- `worker/` (Celery worker + Dockerfile)
- `infra/` (Bicep infrastructure templates)

**Research support only (not customer-visible):**
- `configs/studies/` (study templates)
- `docs/validation/` (validation reports)
- `docs/ref_papers/` (literature)

**Internal ops only:**
- `.github/` (CI)
- `scripts/`, `tools/` (CI helpers)
- `docs/` (architecture and audit)

**Never tracked:**
- `build/`, `results/`, `backups/`, `tmp/`
