# ShieldLab G4 — Submission Log

## Paper 1 — Scientific/Physics Paper

| Field | Value |
|---|---|
| Working title | *ShieldLab G4: A Geant4-based open-source framework for gamma-ray shielding validation* |
| Working file | `papers/paper1_scientific/manuscript_scientific_v08.md` |
| Status | Draft (not yet submitted) |
| Target journal | *Computer Physics Communications* (Elsevier) |
| ISSN | 0010-4655 |
| Scope match | Computational physics, Monte Carlo, particle transport |
| Submission system | EVISE / Editorial Manager |
| Manuscript type | Full article |
| Word count (approx.) | — |
| Keywords | Geant4, gamma-ray shielding, mass attenuation coefficient, NIST XCOM, HVL, TVL |

### History

| Date | Action | Notes |
|---|---|---|
| 2025-05 | v0.7 draft | Initial benchmark paper |
| 2025-06 | v0.8 draft | Revised structure and benchmark tables |
| — | *Pending: cover letter, highlights, final DOCX* | |

---

## Paper 2 — Technical / Software Paper

| Field | Value |
|---|---|
| Working title | *ShieldLab G4: An Open-Source Software Platform for Gamma-Ray Shielding Simulation and Validation* |
| Working file | `papers/paper2_technical_software/manuscript_technical_software_v02.md` |
| Status | Draft v0.2 — figures generated, DOCX pending final regen |
| Target journal | *SoftwareX* (Elsevier) |
| ISSN | 2352-7110 |
| Scope match | Open-source research software, physics simulation, cloud deployment |
| Submission system | Editorial Manager — https://www.editorialmanager.com/softx/ |
| Manuscript type | Original Software Article |
| Word count (approx.) | ~4,500 words (excl. references, code blocks) |
| Keywords | Geant4, radiation shielding, FastAPI, open-source, Monte Carlo, scientific software |
| Code repository | https://github.com/hhnegm-wq/ShieldLabG4  *(private — make public before submission, see roadmap P5.1)* |
| Archive DOI | *(Zenodo DOI — create before submission)* |
| License | *(confirm in repository)* |

### SoftwareX Requirements Checklist

- [ ] Main text ≤ 2,000 words (check after DOCX generation; current draft is longer — may need condensing for SoftwareX vs CPC)
- [ ] Code metadata table (Table 1) — included in manuscript §3
- [ ] Software available in public repository — pending public release
- [ ] README with install + quickstart — present (`README.md`)
- [ ] License file — confirm
- [ ] Tests described — §8 Governance & QA
- [ ] Highlights (5 bullets, ≤85 chars each) — `papers/paper2_technical_software/final/highlights.md`
- [ ] Cover letter — `papers/paper2_technical_software/final/cover_letter.md`
- [ ] DOCX for submission — `papers/paper2_technical_software/final/manuscript_technical_software_v02.docx`
- [ ] All figures at 300 DPI — ✅ generated
- [ ] Author ORCID numbers — *(fill before submission)*
- [ ] [Institution] placeholder — *(fill before submission)*
- [ ] [Funding source] placeholder — *(fill or use "No funding" before submission)*
- [ ] [REF-COMPANION] — *(fill with paper 1 DOI/arXiv once available)*

### History

| Date | Action | Notes |
|---|---|---|
| 2025-05 | v0.1 draft | Initial technical paper |
| 2025-06 | v0.2 draft | Full revision with PAPER_PRODUCTION_MASTER_GUIDE; 4-paragraph abstract, State of the Field, explicit limitations |
| 2025-06 | Figures generated | `fig01_system_architecture.png`, `fig02_ci_gate_model.png`, `fig03_attenuation_agreement.png` |
| — | *Pending: final DOCX, cover letter, peer review simulation, submission* | |

### Alternative Journals (if SoftwareX declines)

| Journal | Scope | Note |
|---|---|---|
| *Journal of Open Source Software* (JOSS) | All open software | Very short paper (~1,000 words); stricter OSS checks |
| *Computer Physics Communications* (CPC) | Computational physics | Longer paper; overlap with Paper 1 — check dual submission policy |
| *PLOS ONE* | Broad | Accepts software papers; APC required |
| *F1000Research* | Open access | Rapid publication; post-publication peer review |

---

## Paper 3 — Nanogeant4 Regime Benchmark Paper

| Field | Value |
|---|---|
| Working title | *Memory-Efficient Geant4 Modelling Regimes for Nanocomposite Radiation Shielding: Effective Medium, Explicit Nanoparticle Geometry, and Hybrid Representative-Volume Validation* |
| Working file | `papers/paper3_nanogeant4/manuscript_nanogeant4_v07.md` |
| Status | Draft v07 — affiliation completed; cover letter, highlights, graphical abstract, and clean DOCX prepared |
| Primary target journal | *Radiation Physics and Chemistry* (Elsevier) |
| Secondary targets | *Nuclear Instruments and Methods in Physics Research A*; *Computer Physics Communications* |
| Scope match | Radiation shielding, Monte Carlo methodology, Geant4 benchmark validation |
| Manuscript type | Full article |
| Figure status | Canonical figure regenerated from `python/shieldlab/viz/paper3_figures.py` |
| Verification status | `tools/verify_paper3_manuscript_v05.py` passes |

### History

| Date | Action | Notes |
|---|---|---|
| 2026-05-18 | v04 export | Cross-regime benchmark consolidated but still contained production issues |
| 2026-05-18 | v05 source revision | Canonical source aligned, abstract shortened, stale appendix removed, metadata normalized, figure guide applied |
| 2026-05-18 | v06 promotion | Round 1/2 self-review closed, five-figure suite added, numbered figure references embedded |
| 2026-05-18 | v06 DOCX export | Clean pandoc export completed from manuscript directory with figure paths resolved |
| 2026-05-18 | v07 packaging | Affiliation completed and submission-package files added under `papers/paper3_nanogeant4/final/` |
| 2026-05-18 | v07 package assets | Cover letter, 5 highlights, graphical abstract PNG/PDF, and clean v07 DOCX created |
| 2026-05-18 | Self-review artifacts saved | Roast, roadmap, and fix tracking stored under `papers/paper3_nanogeant4/archive/self_review/` |
