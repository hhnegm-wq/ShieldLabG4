# ShieldLab G4 — No-Holds-Barred Physics & Science Roast
**Date:** 2026-05-17 | **Scope:** Platform physics core, scientific papers, validation methodology

---

## 1. Executive Roast (Three Paragraphs for a Director or Programme Manager)

ShieldLab G4 is marketed as a unified, validated, reference-grade platform for radiation shielding calculations. In practice, its crown jewel — the 56-point NIST XCOM photon benchmark — is essentially a test that the platform can reproduce its own primary data source after a round-trip through log-log interpolation. That is not science; that is bookkeeping. The single hardest-hit result, Bismuth at 60 keV with a 15.26% deviation, is waved away as an "L-shell absorption-edge interpolation artefact also present in WinXCom and Phy-X/PSD." Other platforms making the same blunder is not a defence — it is a confession that the interpolation scheme is 1987-era table-lookup engineering passed off as physics. A production-grade shielding platform in 2026 should detect absorption edges and use the correct post-edge tabulated value rather than blending across a physical discontinuity.

The buildup-factor validation is the most damaging item in the entire codebase. `buildup_validation.py` begins with this immortal comment: *"STATUS (Phase 1, partial) — The fully-cited Harima 1993 / ANSI/ANS-6.4.3-1991 reference table is **not yet bundled**."* The GP buildup implementation is validated exclusively against its own previously computed output. That is not validation; that is a regression test disguised as a benchmark. The platform's claims to reproduce Phy-X/PSD buildup factors — and the scientific manuscript's statements about GP model fidelity — rest entirely on coefficients that have never been independently verified against the standard they claim to implement. If those coefficients are wrong in a systematic way, every buildup-corrected broad-beam estimate in every study ever run on this platform is wrong, and the code itself cannot detect this.

The dosimetry layer compounds the problem. The H*(10) fluence-to-dose conversion table hard-coded in `dose_rate.py` comes from ICRP Publication 74 (1996). ICRP Publication 116 (2010) superseded it fourteen years ago with improved particle and angular dependence data. The difference is not academic: at some energies, ICRP-116 values differ by 5–15% from ICRP-74. The platform's dose-rate outputs — which feed directly into personnel dose estimates in every study — are therefore systematically off by up to 15% before any other error is introduced. Meanwhile, the release validation report is simultaneously marking itself `PASS` while reporting `threshold_coverage_ratio: 0.000`, `provenance_coverage_ratio: 0.000`, and `statistical_adequacy_ratio: 0.000`. A platform that calls a release "validated" when not a single threshold, provenance record, or statistical adequacy check has been populated is not a scientific platform. It is a gate that waves itself through.

---

## 2. Structural Weaknesses List

### PHYSICS ENGINE

| # | Weakness | Severity | Evidence |
|---|---|---|---|
| P-1 | **Absorption-edge interpolation failure** — log-log interpolation blends across physical discontinuities (K, L edges). Bi@60 keV: 15.26% error. Same flaw in WinXCom does not justify it. | High | `nist_xcom.py` `get_mac_element()`; validation CSV Bi row |
| P-2 | **GP buildup factors: self-consistency validation only** — `buildup_baseline.json` is computed from the shipped coefficients, not from ANSI/ANS-6.4.3-1991 published tables. Independent accuracy is unproven. | Critical | `buildup_validation.py` lines 1–25 (STATUS comment) |
| P-3 | **ICRP-74 dosimetry (1996) — 14 years outdated** — `dose_rate.py` H*(10) table from ICRP Pub. 74. ICRP-116 (2010) is current standard; differences up to 5–15% at some energies. | High | `dose_rate.py` `_ICRP74_H` array |
| P-4 | **GP buildup material coverage is dangerously narrow** — only Water, Concrete, Iron, Lead have GP coefficients. Novel glass and nanocomposite compositions studied by the platform have *no buildup data*, yet the UI does not warn users prominently. | Medium | `shielding_params.py` `_GP_EBF` / `_GP_EABF` dict |
| P-5 | **FNRCS database uses 1985/2000 textbook data** — fast-neutron removal cross-sections sourced from Shultis & Faw 2000 / Lamarsh 2001. ENDF/B-VIII.0 (2018) elemental cross-sections are current. Several f-block elements (Tc, Pm) use placeholder round numbers. | Medium | `shielding_params.py` `FNRCS_BARNS` dict |
| P-6 | **Ion stopping power accuracy floor** — `ion_range.py` documents ±10–20% below 100 keV. The UI presents stopping-power curves with no accuracy confidence band at low energies; this is undisclosed to the user. | Medium | `ion_range.py` module docstring |
| P-7 | **Geant4 geometry: slab-only, no broad-beam support** — only 1-D infinite slab with pencil-beam source. No cylindrical, spherical, wedge, voxelised or detector-response geometry. Narrow-beam HVL used where broad-beam dose is needed will underestimate actual attenuation requirements. | High | `app/ShieldLabG4.cc`; Paper 1 §6(d) |
| P-8 | **No neutron-transport Geant4 validation** — FNRCS is analytical-only. The Geant4 engine uses `emstandard_opt4` (electromagnetic only); no hadronic physics list is activated. The platform currently cannot simulate neutron shielding. | High | `src/ActionInitialization.cc` physics list; Paper 1 §6(e) |
| P-9 | **Multi-layer composite shielding absent** — `inverse_design.py` and the analytical engine handle only homogeneous single-layer slabs. Real shields (e.g., Pb + HDPE + concrete) cannot be optimised analytically. | Medium | `inverse_design.py` scope; UI has no multi-layer study builder |
| P-10 | **H*(10) interpolation uses flat `np.interp` (linear)** — at edges of the ICRP energy table, `left` and `right` are constant extrapolations. At high energies (>10 MeV) or very low energies (<10 keV), extrapolated dose coefficients are wrong. | Low–Medium | `dose_rate.py` `fluence_to_h10()` |
| P-11 | **Klein-Nishina incoherent scattering factors S(q,Z)** — `klein_nishina.py` claims to include "incoherent scattering factors S(q, Z) for bound-electron effects" in the manuscript (Paper 1 §2.1) but the implementation uses the free-electron KN formula without S(q,Z). | Medium | `klein_nishina.py` — no S(q,Z) implementation |
| P-12 | **Z_eff formula exponent is approximation** — uses Z^2.94 (Hine 1952). Modern literature (Murty 1965, Manohara 2008) uses cross-section-weighted Z_eff. The difference matters for novel high-Z composite materials at low energy. | Low–Medium | `shielding_params.py` `zeff_neff()` formula |

---

### SCIENTIFIC PAPERS

| # | Weakness | Severity | Evidence |
|---|---|---|---|
| P1-1 | **`[Institution]` is a placeholder in both manuscripts** — institutional affiliation unresolved at manuscript-prep time. Cannot submit to any journal with `[Institution]` in the author block. | Critical | Paper 1 author block; Paper 2 author block |
| P1-2 | **Novel-material benchmarks are circular self-citations** — the six "novel material" benchmarks in §4.5 (Table 4) compare ShieldLab G4 against published Phy-X/PSD values from the *author's own prior studies* [16–21]. This is not independent external validation; it is checking that the platform reproduces values it was partially designed around. | High | Paper 1 §4.5, Table 4 |
| P1-3 | **External literature anchoring is thin for Table 8** — only one "exact benchmark overlap" reference (Eakins [33]) for the experimental literature context section; the other two references are for granite and heavy-metal oxide glass systems, which do not overlap the benchmark material set. | Medium | Paper 1 §4.13, Table 8 |
| P1-4 | **Inter-code comparison (Table 10) is a capability matrix, not a benchmark** — the paper compares against "MCNP6, FLUKA/PHITS" in Table 10 but there is no numerical comparison. The abstract and title imply validation "against seven reference codes," which will mislead readers. | High | Paper 1 §5, Table 10 |
| P1-5 | **GP buildup factors not independently validated vs. ANS-6.4.3-1991** — Paper 1 §4.9 presents buildup factor curves with no caveat that the coefficients are unverified against the reference standard. Readers assume these are correctly implemented. | High | Paper 1 §4.9, `buildup_validation.py` |
| P1-6 | **Stopping power tables at NIST tabulation points give Δ < 0.01%** — trivially, if the platform interpolates at exactly the same energy points in the table, it reads the table back with rounding noise. This result is presented as a validation but is mathematically guaranteed. | Medium | Paper 1 §4.6, Tables 6 & 7 |
| P2-1 | **Paper 2 Reference [6] is informal web documentation** — `[6] FastAPI Documentation. Tiangolo / Sebastián Ramírez. https://fastapi.tiangolo.com` is not a peer-reviewed reference and should not occupy a numbered citation slot. FastAPI should be cited via Zenodo DOI or omitted. | Medium | Paper 2 References section |
| P2-2 | **Test count "155 passing tests" is stale** — current test gate passes 170 tests. The manuscript states 155 in §8.2 and the abstract. | Medium | Paper 2 §8.2, abstract; pytest output = 170 |
| P2-3 | **Python import example mismatch** — the manuscript's §6.2 example shows `from shieldlab.shielding import ShieldingCalculator` and `from shieldlab.materials import MaterialRegistry`. Neither `shieldlab.shielding` nor `shieldlab.materials` exists as an importable module. The actual API uses `shieldlab.physics.shielding_params` etc. | High | Paper 2 §6.2 code example; `python/shieldlab/` package structure |
| P2-4 | **Reviewer 2 M4 response is "Partially addressed"** — CI gate timing was left unresolved. Response document states: "no stable timing benchmark was added." This will fail actual peer review. | Low | Paper 2 `response_to_reviewers_round1.md` |
| P2-5 | **Reviewer 2 m3: import name not fixed** — response says "confirmed import namespace is `shieldlab`" but §6.2 example still uses `from shieldlab.shielding import ShieldingCalculator` which is a non-existent sub-module. | High | Paper 2 §6.2 |

---

### RELEASE VALIDATION GATE

| # | Weakness | Severity | Evidence |
|---|---|---|---|
| V-1 | **`threshold_coverage_ratio: 0.000`** — not a single benchmark threshold is defined in any study config. The "science gate" passes with 0% threshold coverage. | Critical | `release_validation_report_latest.md` |
| V-2 | **`provenance_coverage_ratio: 0.000`** — no provenance manifests present. All 6 study files pass with 0 provenance records. | Critical | `release_validation_report_latest.md` |
| V-3 | **`statistical_adequacy_ratio: 0.000`** — 0 result sets meet the ≥5000 histories adequacy threshold. | High | `release_validation_report_latest.md` |
| V-4 | **`ready_for_submission: False` despite `Release gate: PASS`** — the gate reports PASS at the top but the publication readiness block says NOT READY and `ready_for_submission: False`. These two states are logically contradictory and will mislead operators. | High | `release_validation_report_latest.md` |

---

## 3. Papers Audit Summary

### Paper 1 — Scientific Manuscript (v08)
- **Good:** Rigorous photon MAC benchmark (56 points, 9 materials). Honest about scope limitations. Clear equations with proper references. Geant4 MC consistency checks at 3 material/energy points. Good statistical framing.
- **Bad:** Institution placeholder, circular self-citations for novel-material benchmarks, thin external experimental anchoring, misleading "validated against MCNP6/FLUKA" framing (capability matrix only), GP buildup unverified, stopping-power validation trivial at tabulation points.
- **Fixable now:** Institution note, framing of Table 10 caption, clarification of GP buildup caveat, stopping-power validation disclaimer.

### Paper 2 — Technical/Software Manuscript (v02)
- **Good:** Comprehensive architecture description, good reviewer response, honest limitations section, well-structured CI gate model.
- **Bad:** Stale test count (155→170), wrong import examples (`shieldlab.shielding` does not exist), FastAPI informal citation, partially-addressed reviewer comments.
- **Fixable now:** Test counts, import examples, FastAPI citation.
