# ShieldLab G4 — Product, Physics & Publication Roadmap

> **Mission.** Become the fastest, most trusted analytical companion to
> Geant4 / FLUKA / MCNP for radiation-shielding research — turning a material
> composition into a Q1-journal-ready figure in under 60 seconds.
>
> **Model.** Open-core freemium SaaS. Free tier earns adoption in academia;
> Pro tier (monthly subscription) unlocks publication-grade outputs, multi-
> material studies, custom data libraries, PDF reports, and a REST API.
>
> Last updated: 2026-06-01 · Owner: Dr. Hani H. Negm · Status: Living document

---

## Table of Contents

0. [Vision & Positioning](#0-vision--positioning)
1. [Current State Audit](#1-current-state-audit-may-2026)
2. [Target Personas & Jobs-To-Be-Done](#2-target-personas--jobs-to-be-done)
3. [Roadmap by Priority (4 Tiers · 30 Items)](#3-roadmap-by-priority-4-tiers--30-items)
4. [Free vs Pro — Commercial Gating](#4-free-vs-pro--commercial-gating)
5. [Pricing & Packaging](#5-pricing--packaging)
6. [Robustness, Quality & UX Standards](#6-robustness-quality--ux-standards)
7. [Architecture Evolution](#7-architecture-evolution)
8. [Build Order — 8 Sprints](#8-build-order--8-sprints)
9. [Success Metrics & KPIs](#9-success-metrics--kpis)
10. [Validation & Scientific Credibility](#10-validation--scientific-credibility)
11. [Compliance, Legal & Data](#11-compliance-legal--data)
12. [Go-To-Market](#12-go-to-market)
13. [Risks & Mitigations](#13-risks--mitigations)
14. [Out of Scope](#14-out-of-scope-intentionally)
15. [Open Questions](#15-open-questions--decisions-needed)

---

## 0. Vision & Positioning

**One-liner.** *"Phy-X meets Streamlit, with figures your editor will accept."*

**Why now.**

- Phy-X / NXcom / WinXCom give numbers but not journal-quality figures or
  reproducible reports.
- Geant4 / FLUKA require weeks of setup for a calculation a Bethe-Bloch +
  XCOM workflow can answer in seconds.
- The radiation-shielding literature has exploded since 2020 (concrete
  composites, glass systems, polymer-Bi2O3 nanocomposites) — every paper
  needs the same figures: MAC vs E, HVL/TVL vs E, Zeff vs E, EBF curves,
  Bragg peak depth-dose, transmission vs thickness.
- No commercial tool currently sits between "free academic script" and
  "$50 k Monte-Carlo licence". That is our gap.

**Pillars.**

1. **Scientific accuracy** — every number traceable to NIST / ICRU / ICRP.
2. **Publication-grade output** — vector formats, 600 DPI, journal themes.
3. **Speed** — < 1 s for a typical calculation; instant figure download.
4. **Trust** — versioned, reproducible, citable, validated.
5. **Commercial discipline** — clear free/pro line; never gate accuracy.

---

## 1. Current State Audit (May 2026)

### 1.1 Solid Foundation Already Shipped

| Module                              | Status | Notes                                                  |
|-------------------------------------|--------|--------------------------------------------------------|
| 6 composition modes                 | Done   | formula · mass-frac · mixture · nano · vol-frac        |
| 8 particle types                    | Done   | gamma · e- · e+ · p · alpha · n · mu- · X-ray          |
| XCOM 7-component photon data        | Done   | NIST live fetch + on-disk cache                        |
| Phy-X parameters                    | Done   | MAC, LAC, HVL, TVL, MFP, Zeff, Neff, EBF, RPE          |
| Zeq (24-element interpolation)      | Done   | Energy-dependent equivalent atomic number              |
| Neutron FNRCS / NGCal               | Done   | Sigma_R, HVL_n, TVL_n, per-element contributions       |
| Multi-layer composite shield        | Done   | Per-layer table + 2D geometry schematic                |
| ESTAR electron stopping             | Done   | Within ~2% of NIST ESTAR (validated)                   |
| Proton stopping (PSTAR)             | Done   | Bethe-Bloch + Bragg-Kleeman compound I (validated)     |
| Alpha stopping (ASTAR)              | Done   | Ziegler effective charge with divergence cap           |
| 2D geometry schematic               | Done   | Source -> layers -> detector                           |
| Excel export (multi-sheet)          | Done   | Shielding · Composition · Descriptors · ESTAR · Ion    |
| NIST COMPENDIUM material library    | Done   | 150 materials — ICRU-46 / PNNL-15870 / NIST; shipped in `data/compendium.py` |
| ICRP-107 isotope library            | Done   | 100 isotopes (medical, industrial, environmental, accelerator) in `data/isotopes.py` |
| Benchmark test suite                | Done   | 45 tests in `tests/benchmarks/` — MAC vs NIST ≤ 2 %, HVL vs Attix ≤ 1.5 % |
| Opt-in telemetry stub               | Done   | `ui/components/telemetry.py`; PostHog-ready, consent-gated |
| Methods & References page           | Done   | 11-section physics docs page with NIST/ICRU/ICRP citations |
| Professional UI theme               | Done   | `styles.py`, `.streamlit/config.toml`, navy/teal design system |
| Session save / restore              | Done   | Fully wired in `shielding_calculator.py` |
| Multi-material comparison (gated)   | Done   | `pages/comparison.py` — 2 materials Free, 8 materials Pro |
| PDF report (real figures)           | Done   | `shielding_calculator.py` — real matplotlib figures embedded |
| Production auth architecture        | Done   | `ui/auth.py` — SHA-256 licence key → JWT → session override → "free" |
| Validation report (30/30 PASS)      | Done   | `docs/validation/validation_report.py` — NIST mixture rule citations fixed |

### 1.2 Remaining Gaps (post-audit · June 2026, updated May 2026)

> Items ✅ below were resolved in the June 2026 or May 2026 platform-hardening cycle.
> Items still open are genuine future work (see §3 roadmap).

| Gap                                                    | Pre-audit | Post-audit |
|--------------------------------------------------------|-----------|------------|
| PDF report generator                                   | ❌ Missing | ✅ Shipped |
| Multi-material comparison (gated free/pro)             | ❌ Missing | ✅ Shipped |
| Tier gating / production auth                          | ❌ Stub    | ✅ Shipped (PyJWT HS256) |
| Session save / restore                                 | ❌ Half-wired | ✅ Shipped |
| NIST COMPENDIUM material library (150)                 | ❌ 88 mats | ✅ 150 mats |
| Isotope library (ICRP-107)                             | ❌ 37 isotopes | ✅ 100 isotopes |
| Automated benchmark regression suite                   | ❌ None    | ✅ 45 tests |
| Opt-in telemetry                                       | ❌ Missing | ✅ Stub shipped |
| Methods & references documentation                     | ❌ Missing | ✅ Shipped |
| Professional UI theme                                  | ❌ Missing | ✅ Shipped |
| Validation circular references fixed                   | ❌ "XCOM computed" | ✅ Proper NIST citations |
| HMAC API-key auth + rate limiting                      | ❌ Missing | ✅ Shipped (`api/security.py`) |
| Geant4 G4MultiFunctionalDetector scoring               | ❌ Missing | ✅ Shipped (per-layer dose/energy-deposit + batch-means σ) |
| ICRP-74 fluence-to-dose conversion                     | ❌ Missing | ✅ Shipped (`physics/dose_conversion.py`) |
| MT vs serial consistency test                          | ❌ Missing | ✅ Shipped (`tests/benchmarks/test_mt_consistency.py`) |
| DLQ worker with poison-queue envelope                  | ❌ Missing | ✅ Shipped (`worker/queue_worker.py`) |
| OpenTelemetry distributed tracing                      | ❌ Missing | ✅ Shipped (`api/telemetry.py`, X-Correlation-Id) |
| Per-tenant quota middleware                            | ❌ Missing | ✅ Shipped (`api/middleware/quota.py`, jobs + CPU-min/day) |
| Security CI (SBOM, SARIF, secret scan)                 | ❌ Missing | ✅ Shipped (`.github/workflows/security.yml`) |
| Figure audit CI lint (`--src-only`)                    | ❌ Missing | ✅ Shipped (`tools/figure_audit.py`) |
| Bicep private endpoints + VNet                         | ❌ Missing | ✅ Shipped (`infra/main.bicep`, 0 errors) |
| CITATION.cff, SECURITY.md                              | ❌ Missing | ✅ Shipped |
| docs/methods.md, architecture.md, data_governance.md  | ❌ Missing | ✅ Shipped |
| CHANGELOG.md                                           | ❌ Missing | ✅ Shipped (v1.0.0 entry) |
| Figures SVG / EPS / high-DPI download                  | ❌ Missing | ✅ Shipped (`viz/export.py` `figure_download_buttons`) |
| Free-tier figure watermark                             | ❌ Missing | ✅ Shipped (watermark in `figure_download_buttons`) |
| Dose-rate calculator (Bq/Ci × distance)                | ❌ Missing | ✅ Shipped (`physics/dose_rate.py`, `pages/dose_rate.py`) |
| REST API (FastAPI batch)                               | ❌ Missing | ✅ Shipped (`api/main.py`, 9 endpoints) |
| CLI (`shieldlab calc`)                                 | ❌ Missing | ✅ Shipped (`cli/main.py`, 8 commands) |
| Error reporter button                                  | ❌ Missing | ✅ Shipped (`components/error_reporter.py`) |
| Raw Python tracebacks visible to users                 | ❌ Open    | ✅ Resolved via `error_reporter` + `try/except` wrappers |
| Isotope library expanded to 1 000                      | ⚠️ 100 done | ⚠️ ~900 remaining (future sprint) |

---

## 2. Target Personas & Jobs-To-Be-Done

| Persona                         | Job-To-Be-Done                                                     | Tier  |
|---------------------------------|--------------------------------------------------------------------|-------|
| **PhD student** (rad. physics)  | Generate MAC/HVL/Zeff plots for a thesis chapter                   | Free  |
| **Postdoc**                     | Compare 5 candidate concrete composites in one figure for a paper  | Pro   |
| **Medical physicist**           | Compute dose-rate behind a shield for a clinical isotope source    | Pro   |
| **Industry engineer** (NDT)     | Quick HVL lookup for daily-use industrial gamma sources            | Free  |
| **Regulatory consultant**       | One-click PDF report for a vault-design submission                 | Pro   |
| **Course instructor**           | Live-demo XCOM cross-section components in a lecture               | Free  |
| **Materials lab**               | Batch-evaluate 100 nanocomposite candidates via REST API           | Pro   |
| **Reviewer / editor**           | Reproduce a paper's figure from its session JSON                   | Free  |

---

## 3. Roadmap by Priority (4 Tiers · 30 Items)

### Tier 1 — Publication Quality (highest ROI, blocks journal use)

| #  | Item                                                       | Why                                                          | Effort   |
|----|------------------------------------------------------------|--------------------------------------------------------------|----------|
| 1  | Journal-style global matplotlib theme (`apply_journal_style`) | Journals require 8-10 pt fonts, fixed line widths, 300/600 DPI | ~1 day   |
| 2  | Per-figure download: PNG-300, PNG-600, SVG, EPS, PDF, TIFF | Required by Nature / Elsevier / Springer for vector graphics | ~1 day   |
| 3  | Auto figure-caption generator                              | "Fig. X. MAC of {mat} (rho={rho} g/cm3) vs photon energy."   | ~½ day   |
| 4  | Full PDF report (figures + tables + composition + biblio)  | Currently only Excel; PDF is the de-facto deliverable        | ~2 days  |
| 5  | Citation block (BibTeX + APA + IEEE + RIS)                 | Auto-generated `@software{...}` in Export tab                | ~½ day   |
| 6  | Colour-blind-safe palettes (Okabe-Ito, viridis)            | Q1 journals increasingly require this                        | ~½ day   |
| 7  | Reproducibility footer on every figure (version + hash)    | Reviewer can verify which build produced the figure          | ~½ day   |

### Tier 2 — Physics Completeness (differentiator vs Phy-X)

| #  | Item                                                       | Why                                                          | Effort  |
|----|------------------------------------------------------------|--------------------------------------------------------------|---------|
| 8  | Multi-material comparison tab (up to 8 materials)          | The #1 most-cited figure in shielding papers                 | ~1.5 d  |
| 9  | Bragg peak / depth-dose profile (proton & ion therapy)     | Essential for proton/ion-beam papers                         | ~1 day  |
| 10 | Inverse design (target T -> required thickness or rho)     | Reverse of current forward calc                              | ~½ day  |
| 11 | Dose-rate calculator (Bq/Ci x distance x geometry)         | Standard regulatory tool (uSv/h) with point/line/disk source | ~1 day  |
| 12 | EBF/EABF G-P fit-coefficient table (b, c, a, Xk, d)        | Currently only computed EBF value is shown                   | ~½ day  |
| 13 | Klein-Nishina polar plot (dsigma/dOmega vs scattering angle) | Very common in Compton-scatter papers                      | ~½ day  |
| 14 | Mass energy-absorption coefficients (EpiXS muen/rho)       | Already partially present; needs proper EpiXS interpolation  | ~1 day  |
| 15 | LET (linear energy transfer) for ions                      | Required for biological-effect / RBE papers                  | ~½ day  |
| 16 | Photon kerma & air-kerma rate constant Gamma               | Standard isotope-source descriptor                           | ~½ day  |
| 17 | Neutron buildup factors + dose conversion (ANSI/ANS-6.1.1) | Currently only FNRCS; missing buildup & dose                 | ~1 day  |

### Tier 3 — Geometry & Visualisation (visual impact)

| #  | Item                                                       | Why                                                          | Effort  |
|----|------------------------------------------------------------|--------------------------------------------------------------|---------|
| 18 | Dose-field heatmap (2D colormap of dose vs x, depth)       | Striking figure for papers                                   | ~1 day  |
| 19 | Transmission "waterfall" plot (multi-material x thickness) | Compact comparison figure                                    | ~½ day  |
| 20 | Drag-reorder geometry builder (`streamlit-sortables`)      | UX polish for multi-layer stack                              | ~1 day  |
| 21 | Cylindrical / spherical geometry (pipe, cask, vault)       | Real-world shielding shapes                                  | ~2 days |
| 22 | Oblique-incidence angular attenuation (polar plot of T(θ)) | cos θ correction for slant paths                             | ~1 day  |
| 23 | Geant4-vs-analytical overlay plot                          | Bridge to existing Geant4 simulation outputs                 | ~1 day  |
| 24 | Spectrum-weighted attenuation (full source spectrum)       | Realistic broad-beam vs narrow-beam comparison               | ~1 day  |

### Tier 4 — Data Layer, API & Platform

| #  | Item                                                       | Why                                                          | Effort  |
|----|------------------------------------------------------------|--------------------------------------------------------------|---------|
| 25 | NIST COMPENDIUM material DB (~150 materials)               | Pre-loaded standards (concrete, water, tissue, ICRU phantoms)| ~1.5 d  |
| 26 | Isotope library (ICRP-107 / ENSDF gamma & beta lines)      | 1000+ isotopes vs current 5-10 hardcoded                     | ~2 days |
| 27 | REST API (FastAPI) for batch jobs                          | Pro-tier scriptable access from Python / MATLAB / Mathematica| ~3 days |
| 28 | Session save/restore (JSON `.shieldlab` file)              | Reproducibility + sharing                                    | ~½ day  |
| 29 | Cached-data clear button + cache-age indicator             | Stops the silent "stale cache" pain we already hit           | ~½ day  |
| 30 | CLI (`shieldlab calc -m PbWO4 -e 0.662 ...`)               | Power-users + CI pipelines                                   | ~1 day  |

---

## 4. Free vs Pro — Commercial Gating

> **Principle.** Show every gated UI element with a 🔒 badge instead of hiding
> it. Users see what they are missing → upgrade conversion. **Never gate
> scientific accuracy.** A Free user gets the same physics as a Pro user, just
> with watermarks, fewer points, and basic export formats.

| Capability                              | Free                       | Pro (monthly)                              |
|-----------------------------------------|----------------------------|--------------------------------------------|
| Materials per session                   | 1                          | Up to 8 (comparison tab)                   |
| Energy points per calc                  | 50                         | Unlimited                                  |
| Thickness grid points                   | 25                         | Unlimited                                  |
| Figure formats                          | PNG 96 DPI (watermark)     | PNG-300 · PNG-600 · SVG · EPS · PDF · TIFF |
| Watermark on figures                    | "ShieldLab G4 — Free"      | None                                       |
| PDF report generator                    | No                         | Yes (cover + figures + tables + bibliography) |
| Excel export                            | Basic (3 sheets)           | Full (all sheets, formula references)      |
| Multi-material comparison               | No                         | Yes (up to 8)                              |
| Custom isotope / source builder         | No                         | Yes                                        |
| Dose-rate calculator                    | No                         | Yes                                        |
| Bragg peak / depth-dose / LET           | Preview only               | Full                                       |
| Inverse shielding design                | No                         | Yes                                        |
| NIST COMPENDIUM material DB             | First 10 materials         | All ~150                                   |
| ICRP-107 isotope library                | First 20 isotopes          | All ~1000                                  |
| Cylindrical / spherical geometry        | No                         | Yes                                        |
| Spectrum-weighted attenuation           | No                         | Yes                                        |
| REST API access                         | No                         | Yes (rate-limited 10 000 calls / month)    |
| CLI                                     | Yes                        | Yes                                        |
| Session save / restore                  | Yes                        | Yes                                        |
| Citation block                          | Yes                        | Yes                                        |
| Email support                           | Community (GitHub)         | Priority email (2 business-day SLA)        |
| Branded reports (logo, custom footer)   | No                         | Yes                                        |

---

## 5. Pricing & Packaging

### 5.1 Plans

| Plan                | Price           | Seats | Notes                                              |
|---------------------|-----------------|-------|----------------------------------------------------|
| **Free**            | $0              | 1     | Forever. Watermarked PNG. Single material.         |
| **Academic Pro**    | $9 / month      | 1     | Verified `.edu` or ORCID. All Pro features.        |
| **Professional**    | $29 / month     | 1     | Industry / consultancy.                            |
| **Lab / Team**      | $99 / month     | 5     | Shared material library + admin console.           |
| **Enterprise**      | Custom (>$500/m)| 25+   | SSO, on-prem option, dedicated support, training.  |

### 5.2 Discounts & Trials

- 14-day Pro trial on signup (no card required)
- 2 months free on annual billing (i.e. 10 × monthly = annual)
- 50 % discount for verified students (course-instructor invite code)
- Free Pro for low-income-country (LIC) institutions (UN list)
- Free Pro for open-access papers that cite ShieldLab G4 (after publication)

### 5.3 What we will **never** do

- Never paywall a published scientific figure that was generated on Pro and is
  needed to satisfy a journal's data-availability requirement
- Never lock data export — even Free users can always download CSV of their numbers
- Never hide model versions or validation results behind a paywall

---

## 6. Robustness, Quality & UX Standards

These are non-negotiable for a paid product.

1. **Input guards everywhere** — every recalculation wraps `try/except` and
   shows a friendly message via `st.error`. **No raw tracebacks for end users.**
2. **Spinners + progress bars** on every NIST fetch and any compute > 500 ms.
3. **"Clear cached NIST data" button** + cache-age indicator (we already hit
   the silent stale-cache trap during development).
4. **Session save / restore** — JSON dump of `calc_state` + version stamp +
   git hash, importable on any other instance.
5. **Tooltips on every parameter** — hover help for I-value, G-P method,
   FNRCS, Zeff, Bragg-Kleeman, ZBL, Sternheimer density effect, etc.
6. **Mobile guard** — `st.warning` if viewport width < 800 px.
7. **Telemetry (opt-in only, anonymous)** — feature usage counters; never
   track material composition or numerical inputs.
8. **Pytest regression suite** — formalise `verify_estar.py` and add proton,
   alpha, MAC, HVL, EBF tests with locked-in NIST/Phy-X reference values.
   Target ≥ 80 % coverage on `python/shieldlab/physics/`.
9. **Versioned `CHANGELOG.md`** following [Keep a Changelog](https://keepachangelog.com).
10. **Error reporter** — "Report this issue" button auto-includes calc state
    + traceback + version (with user consent).
11. **Accessibility** — WCAG 2.1 AA: keyboard navigation, ARIA labels, > 4.5:1
    contrast, alt-text on all figures.
12. **Internationalisation-ready** — externalise strings to `i18n/en.json`;
    initial languages: EN, then ZH, AR, ES (top academic markets).
13. **Performance budget** — 95th-percentile calculation < 2 s; figure render
    < 500 ms; cold-start NIST fetch < 5 s.

---

## 7. Architecture Evolution

### 7.1 Today

```
Streamlit (single process)
  └── shieldlab.physics.* (XCOM, ESTAR, ion_range, FNRCS)
       └── on-disk JSON cache of NIST data
```

### 7.2 6-Month Target

```
[ Streamlit UI (Pro) ]   [ FastAPI REST ]   [ CLI ]
        |                        |             |
        +------------+-----------+-------------+
                     |
              shieldlab core (pure-Python lib, pip-installable)
                     |
        +------------+------------+------------+
        |            |            |            |
   physics/      data/        viz/         io/
   (XCOM,        (NIST,       (style,     (excel,
   ESTAR,        ICRP,        export,      pdf,
   PSTAR,        COMPENDIUM)  captions)    json)
   FNRCS,
   Klein-N)
                     |
              Auth0/Clerk + Stripe billing
                     |
              Postgres (users, sessions) + S3 (figure cache)
```

### 7.3 Package Layout (target)

```
shieldlab/
├── core/             # materials, descriptors, units
├── physics/          # XCOM, ESTAR, PSTAR/ASTAR, FNRCS, Klein-Nishina, dose
├── data/             # COMPENDIUM, ICRP-107, GP coefficients
├── viz/              # style.py, export.py, captions.py
├── io/               # excel, pdf_report, session_json, csv
├── api/              # FastAPI app
├── cli/              # Click-based CLI
└── ui/               # Streamlit pages (free + pro)
```

---

## 8. Build Order — 8 Sprints

### Sprint 1 — Publication Quality (1 week) **[Highest ROI]**

1. `shieldlab/viz/style.py` — `apply_journal_style()` (Nature, Elsevier, IEEE presets)
2. `shieldlab/viz/export.py` — `figure_download_buttons(fig, basename)` emitting PNG-300 / PNG-600 / SVG / EPS / PDF
3. Apply `apply_journal_style()` once at top of each Streamlit page
4. Wrap **every** `st.pyplot(fig)` with `figure_download_buttons(...)`
5. `shieldlab/viz/captions.py` — auto-caption generator
6. Reproducibility footer on every figure (version + git hash + UTC timestamp)

### Sprint 2 — Tier Gating Skeleton (3 days)

1. `ui/auth.py` — `get_user_tier() -> Literal["free", "pro"]` (stub returns "free"; Stripe wiring later)
2. `ui/components/pro_gate.py` — `pro_only(label)` widget with 🔒 badge + "Upgrade" link
3. Lock badges next to every gated tab, plot, and download button
4. Free-tier watermark overlay (`fig.text(0.5, 0.5, "ShieldLab G4 — Free", alpha=0.12, rotation=30)`)
5. Energy/thickness point caps for Free tier (50 / 25)

### Sprint 3 — Multi-Material Comparison (2 days)

1. New `tab_compare` in `shielding_calculator.py`
2. Material-list manager (add up to 8) with shared energy grid
3. Overlay MAC / LAC / HVL / TVL plots
4. Side-by-side comparison table + ratio plots (vs. reference material)

### Sprint 4 — PDF Report (2 days)

1. `shieldlab/io/pdf_report.py` using `reportlab`
2. Sections: Cover · Material composition · Source · Phy-X table · MAC plot ·
   HVL/TVL plot · Multi-layer summary · Methods · Bibliography
3. "Download PDF Report" button in Export tab (Pro-gated)
4. Branded variant for Lab/Enterprise (custom logo + footer)

### Sprint 5 — Physics Completeness (1 week)

- Bragg peak depth-dose
- Klein-Nishina polar plot
- Inverse design mode
- Dose-rate calculator (point / line / disk source)
- G-P coefficient table
- LET for ions
- Air-kerma rate constant Gamma

### Sprint 6 — Data Layer (1 week)

- NIST COMPENDIUM YAML/JSON shipped with app (~150 materials)
- ICRP-107 isotope library (~1000 isotopes, gamma + beta)
- Session save/restore (`.shieldlab` JSON)
- Cache-clear UI + age indicator

### Sprint 7 — API & CLI (1 week)

- FastAPI service: `POST /api/v1/shielding`, `/api/v1/estar`, `/api/v1/ion`, `/api/v1/dose-rate`
- API-key auth tied to Pro subscription (rate-limit per plan)
- Click-based CLI: `shieldlab calc`, `shieldlab batch`, `shieldlab report`
- OpenAPI / Swagger docs auto-generated

### Sprint 8 — Polish, Telemetry, Launch Prep (1 week)

- Opt-in telemetry (PostHog or self-hosted Plausible)
- Error reporter ("Report this issue" button)
- `CHANGELOG.md` + semver tagging
- Stripe checkout + customer portal
- Auth0 / Clerk integration
- Landing page (Next.js or Astro) with pricing & docs
- Beta-tester onboarding (target 50 academic users)

---

## 9. Success Metrics & KPIs

| Metric                                          | 3 mo  | 6 mo   | 12 mo  |
|-------------------------------------------------|-------|--------|--------|
| Free monthly active users (MAU)                 | 200   | 1 000  | 5 000  |
| Pro paid subscribers                            | 5     | 50     | 250    |
| MRR (USD)                                       | $50   | $750   | $5 000 |
| Citations of ShieldLab G4 in indexed papers     | 1     | 5      | 25     |
| GitHub stars                                    | 100   | 500    | 2 000  |
| Median calculation time                         | < 2 s | < 1 s  | < 0.5s |
| % sessions ending in figure download            | > 30% | > 50%  | > 60%  |
| Free → Pro conversion (trial → paid)            | 5%    | 8%     | 12%    |
| Net Promoter Score                              | 30    | 45     | 55     |
| Pytest coverage on `physics/`                   | 60%   | 80%    | 90%    |
| Mean time-to-resolve Pro support ticket         | 3 d   | 1 d    | 4 h    |

---

## 10. Validation & Scientific Credibility

A paid scientific tool is only as valuable as its provenance. Every release ships with:

1. **Validation report** (`docs/validation/`) — table of computed vs reference
   values for ESTAR, PSTAR, ASTAR, XCOM, FNRCS across ≥ 30 reference materials.
   Target tolerance: ≤ 2 % vs NIST, ≤ 5 % vs Phy-X for buildup factors.
2. **Reproducibility manifest** — every figure stamped with package version
   + git commit hash + Python interpreter version.
3. **Public benchmark suite** — `tests/benchmarks/` runs on CI on every PR;
   results published to `https://shieldlab-g4.github.io/benchmarks`.
4. **Methods page** — for each parameter, a short page citing the underlying
   formula + standard (e.g. ICRU 37, ICRU 49, ANSI/ANS-6.4.3, Shultis & Faw).
5. **DOI per release** via Zenodo — citable in papers.
6. **Peer-reviewed publication** — submit a methods paper to *Radiation
   Physics and Chemistry* or *Nuclear Instruments and Methods A* by month 9.

---

## 11. Compliance, Legal & Data

- **Licence** — Free tier: AGPL-3.0 (open core). Pro features: commercial
  licence in private repo.
- **Privacy** — GDPR-compliant. No PII beyond email + tier. Telemetry is
  opt-in, anonymous, aggregable.
- **Data residency** — EU customers can request EU-only hosting.
- **Terms of Service** — explicit disclaimer: *not certified for clinical or
  regulatory use without independent validation*.
- **Export controls** — confirm no ITAR/EAR restrictions on neutron/proton
  shielding data (NIST data is public).
- **Copyright holder** — Dr. Hani H. Negm.
- **Primary contact** — hhnegm@ju.edu.sa · negm_sci@aun.edu.sa · +966596301743.
- **Trademark** — register "ShieldLab G4" word-mark.
- **Cookie policy** — only essential cookies on free tier; analytics cookies
  require explicit consent banner.

---

## 12. Go-To-Market

### 12.1 Phase 1 — Beta (Months 1-3)

- Recruit 50 academic beta testers via radiation-physics Twitter/X, ResearchGate,
  RPC mailing list
- Free Pro for all beta testers in exchange for testimonial + bug reports
- Landing page with "Try it free" CTA

### 12.2 Phase 2 — Launch (Month 4)

- Submit "Show HN" + r/Physics + r/MedicalPhysics posts
- Lightning talk at IRPA / IEEE NSS / ESTRO
- Webinar: "From XCOM to publication-ready figure in 60 seconds"

### 12.3 Phase 3 — Growth (Months 5-12)

- Conference sponsorships (small booth at IRPA, ESTRO)
- Course-instructor program: free site-licence in exchange for inclusion in syllabus
- Paid blog posts on Substack / Medium / IAEA newsletter
- SEO: long-tail content on "MAC of <material>", "HVL of <material>"

---

## 13. Risks & Mitigations

| Risk                                                | Likelihood | Impact | Mitigation                                                |
|-----------------------------------------------------|------------|--------|-----------------------------------------------------------|
| NIST changes XCOM URL / format                      | Medium     | High   | Ship an offline data snapshot; auto-fallback              |
| Phy-X / Penelope adds free vector export            | Medium     | High   | Win on UX, multi-material, PDF reports, dose calc, API    |
| Reviewer rejects figure due to subtle physics bug   | Medium     | High   | Validation suite + DOI + version-stamped figures          |
| Low free → pro conversion (< 3 %)                   | Medium     | High   | A/B test pricing; add team plan; ship more Pro-only viz   |
| Streamlit performance ceiling on multi-material     | High       | Medium | Migrate hot paths to FastAPI + cache; consider Reflex     |
| Single-maintainer bus factor                        | High       | High   | Open governance; document everything; recruit co-maintainer |
| Geant4 community sees us as competitive             | Low        | Medium | Position explicitly as analytical *companion*, not replacement |

---

## 14. Out of Scope (intentionally)

- 3D OpenGL / WebGL geometry viewer (matplotlib 2D suffices for papers)
- Full Monte Carlo replacement (we *bridge* to Geant4, never replace)
- Reactor neutronics / criticality (needs ENDF/B + MCNP-class kernels)
- Nuclear data evaluation tools (use JANIS / JEFF for that)
- Real-time collaborative multi-user editing
- Mobile-first UI (responsive guard only; the workflow is desktop-research)
- Custom Monte Carlo physics list editor (out of mission)

---

## 15. Open Questions / Decisions Needed

1. **Hosting** — Streamlit Community Cloud (cheap, capped) vs Hugging Face
   Spaces vs Render vs self-host on Hetzner / Fly.io?
2. **Billing** — Stripe (everywhere) vs Paddle (handles VAT for EU customers automatically)?
3. **Auth provider** — Auth0, Clerk, Supabase Auth, or `streamlit-authenticator`?
4. **Repo strategy** — open-source free tier + private Pro repo, OR single
   monorepo with feature flags (cleaner CI but harder to enforce gating)?
5. **SLA for Pro tier** — 99.5 % (1 cheap region) or 99.9 % (multi-region)?
6. **Data update cadence** — refresh NIST cache weekly, monthly, or on demand?
7. **Co-founder / co-maintainer** — solo or recruit a domain-expert co-founder
   for credibility (radiation-physics PhD)?

---

*This roadmap is a **living document**. Edit freely as priorities shift,
beta-tester feedback arrives, or commercial signals change. Every change
should be reflected in `CHANGELOG.md` and announced in the next release.*
