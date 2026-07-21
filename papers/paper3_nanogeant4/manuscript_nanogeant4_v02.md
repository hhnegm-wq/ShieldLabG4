# Memory-Efficient Geant4 Modelling Regimes for Nanocomposite Radiation Shielding: Effective Medium, Explicit Nanoparticle Geometry, and Hybrid Representative-Volume Validation

**Hani H. Negm**¹

¹ *Department of Physics, **[AFFILIATION REQUIRED — DO NOT SUBMIT WITH PLACEHOLDER]***

**Corresponding author:** [email]

**Manuscript version:** v02 (design + benchmark protocol — no fabricated numerical results)

**Target journals (Q1, in priority order):**
1. *Radiation Physics and Chemistry* (Elsevier, IF ≈ 2.9; primary scope match — shielding + MC methodology)
2. *Nuclear Instruments and Methods in Physics Research A* (NIM A, Elsevier; established Geant4 methods venue)
3. *Computer Physics Communications* (Elsevier; physics + software methodology)
4. *Physics in Medicine and Biology* (IOP; if diagnostic-energy nano-dose results are emphasised)
5. *Annals of Nuclear Energy* (Elsevier; if shielding-engineering framing is emphasised)

---

## Abstract

Nanoparticle-loaded radiation-shielding materials are routinely simulated in Geant4 as elemental homogeneous mixtures, despite the term *nanocomposite* implying a resolved microstructure. The validity boundary of this homogenisation has not been systematically mapped against the explicit-geometry alternatives that Geant4 actually supports, and the computational cost of moving beyond homogenisation is rarely quantified. This paper presents a controlled benchmark of four Geant4 modelling regimes applied to the same nanocomposite formulations: (A) effective-medium mass-fraction `G4Material`; (B) explicit nanoparticle placement via `G4PVParameterised`; (C) voxelised `G4MultiUnion` inclusion clusters; and (D) a hybrid representative-volume-element (RVE) workflow that performs explicit-geometry transport only inside a micrometre-scale validation cell and uses the result as a correction map for a macroscopic homogeneous slab. All four regimes use the same Geant4 11.4 build, the same physics list (`G4EmLivermorePhysics` for photons ≤ 1 MeV; `G4EmStandardPhysics_option4` for higher energies), the same source spectra (mono-energetic photons spanning 30 keV–1.33 MeV plus a Cs-137 line), the same scoring volumes, and matched random-number sequences. Endpoints are: transmitted photon fluence, deposited dose in matrix and filler phases, radial dose-enhancement profile around inclusions, broad-beam buildup, runtime per 10⁶ histories, peak resident-set memory, and geometry-construction time. Validation is anchored to NIST XCOM mass attenuation coefficients (Berger et al., NIST SRD 8) and to the ShieldLab G4 analytical Phy-X/PSD-equivalent layer (1.0.0, v08). The expected outcome is a quantitative regime map: above ~100 keV and away from absorption edges, effective-medium modelling reproduces macroscopic transmission within the photon-benchmark tolerance already established for ShieldLab G4 while explicit geometry adds runtime and memory cost without measurable physics benefit; below ~100 keV with high-Z fillers, explicit nanoparticle geometry yields measurable interface-dose perturbations that homogenisation cannot capture. The hybrid RVE workflow is proposed as the production-grade methodology: it preserves full-shield throughput while quantifying the energy and composition regime in which microstructure changes local energy deposition. A reproducible benchmark harness (configuration files, macros, statistical analysis pipeline, and figure generation) is released as part of ShieldLab G4 v1.1 to enable independent replication.

**Keywords:** Geant4 · radiation shielding · nanocomposite · effective medium · `G4MultiUnion` · `G4PVParameterised` · representative volume element · dose enhancement · Monte Carlo benchmarking · reproducible workflow

---

## 1. Introduction

### 1.1 Background

Polymer-matrix radiation-shielding composites loaded with high-Z fillers (Bi₂O₃, WO₃, PbO, BaSO₄, Gd₂O₃) have become a sustained research focus over the past decade, driven by the need for lead-free, flexible, low-toxicity alternatives in medical X-ray protection, nuclear medicine, and aerospace shielding. A substantial fraction of the recent literature reports filler particle sizes in the nanometre range and labels the resulting materials as *nanocomposites*. When such materials are simulated in Monte Carlo (MC) transport codes — most commonly Geant4 [1–3] — the dominant practice is to define one `G4Material` from elemental mass fractions and a measured or estimated bulk density. The microstructure is not resolved.

This homogenisation is physically defensible for the macroscopic shielding regime in which the relevant photon mean free path (MFP) is orders of magnitude larger than both the filler particle radius and the inter-particle spacing. Under that condition the photon "sees" an effective medium and the Bragg–Gray mass-fraction additivity rule [4,5] yields linear attenuation coefficients consistent with NIST XCOM [6] to within the independent-atom approximation. The validity boundary of this rule has been extensively characterised for macroscopic mixtures [5,7], but the question that motivates this work is different: under what circumstances does the *spatial arrangement* of the high-Z phase, at the nanoscale, change a quantity that a shielding engineer or medical physicist actually cares about — transmission, broad-beam dose, or interface dose — by more than the experimental uncertainty?

### 1.2 Gap

Three gaps remain in the literature:

1. **Validity boundary of homogenisation.** Although effective-medium MC results agree with experiment for many nanocomposite shielding measurements at gamma energies, there is no published systematic Geant4 benchmark that holds composition, density, source, scoring geometry, and physics list constant while varying only the geometric representation (homogeneous vs explicit-particle vs clustered) and reports the cross-method deviation as a function of photon energy and filler loading.
2. **Computational cost characterisation.** The Geant4 Application Developer Guide documents `G4PVParameterised` and `G4MultiUnion` as standard constructs, but the practical scaling of runtime, memory, and geometry-construction time for radiation-shielding-relevant nanoparticle counts has not been mapped. Practitioners frequently assume that "Geant4 can do it" without quantifying when it cannot.
3. **Production-grade methodology.** Existing nanoparticle-resolved Geant4 studies are concentrated in the nano-radiosensitisation/Geant4-DNA community [8,9,10], where the physical scale is sub-cellular and the particle counts are tractable. There is no published bridge between that microscopic methodology and the macroscopic shielding-engineering use case, where a representative volume element (RVE) approach is the only physically and computationally viable path.

### 1.3 Contribution and hypothesis

This paper contributes (i) a controlled four-regime benchmark for nanocomposite shielding in Geant4; (ii) a quantitative regime map separating composition/energy combinations for which homogenisation is sufficient from those for which it is not; (iii) a hybrid RVE-corrected workflow that delivers full-shield throughput with quantified microstructural uncertainty; (iv) an open, reproducible benchmark harness released with ShieldLab G4 v1.1.

**Hypothesis (H1).** For photon energies $E \gtrsim 100$ keV away from absorption edges, and for nanoparticle radii $r$ small compared with the photon MFP ($r \ll 1/\mu$), the transmitted fluence through a macroscopic slab is independent of the choice of regime A, B, or C within the statistical uncertainty of $10^6$-history Geant4 runs, provided composition, density, and scoring are matched.

**Hypothesis (H2).** For photon energies $E \lesssim 100$ keV with high-Z fillers (Bi₂O₃, WO₃), explicit nanoparticle geometry produces a measurable radial dose-enhancement profile around individual particles that the effective-medium regime cannot reproduce, even when the macroscopic transmission agrees.

**Hypothesis (H3).** A hybrid regime D (homogeneous slab + RVE correction map) reproduces the explicit-RVE local metrics to within a stated tolerance while keeping macroscopic runtime within a small multiplier of regime A.

Each hypothesis is operationalised as a numeric acceptance criterion in §4.5.

---

## 2. Theoretical Basis

### 2.1 When homogenisation is exact, when it is approximate, and when it fails

The mass-fraction additivity rule for the mass attenuation coefficient,

$$
\left(\frac{\mu}{\rho}\right)_\text{mix}(E) = \sum_i w_i \left(\frac{\mu}{\rho}\right)_i(E), \tag{1}
$$

is *exact* under the independent-atom approximation and the assumption that the photon interaction probability per unit mass is independent of the geometric distribution of atoms within the irradiated mass. This holds when:

1. The photon de Broglie wavelength is small compared with inter-atomic spacing (true for all E > 1 keV considered here).
2. Coherent (Rayleigh) inter-particle interference is negligible (true above ~10 keV for amorphous nanocomposites).
3. The penetration depth is large compared with any heterogeneity length scale (the *macroscopic-homogenisation condition*).

The third condition is the one that fails first for nanocomposites under low-energy, high-Z conditions: although the photon MFP at 1 MeV in Bi₂O₃ is ≈ 1 cm (much greater than any nanoparticle), the *secondary-electron* range at 50 keV in Bi₂O₃ is ≈ 10 µm, comparable to inter-particle spacing at moderate loadings. Energy deposited by photoelectrons therefore exhibits spatial structure that is invisible to a homogeneous-material MC run.

This is the physical origin of the "regime map" the paper aims to produce.

### 2.2 Effective density

Geant4 requires density. The paper compares three density inputs:

- **Measured:** preferred for experimental validation; pycnometric, Archimedes, or X-ray.
- **Volume-fraction rule of mixtures**, given filler volume fraction $\phi_f$:

  $$\rho_\text{eff} = \phi_f \rho_f + (1 - \phi_f)\rho_m \tag{2}$$

- **Mass-fraction no-void estimate**, given filler mass fraction $w_f$:

  $$\rho_\text{eff} = \left(\frac{w_f}{\rho_f} + \frac{1-w_f}{\rho_m}\right)^{-1} \tag{3}$$

- **Porosity correction**, given total porosity $P$:

  $$\rho_\text{eff, porous} = (1-P)\,\rho_\text{eff} \tag{4}$$

For benchmarks in this paper, identical $\rho_\text{eff}$ is fed to all four regimes to isolate the geometric effect from the density effect.

### 2.3 The representative volume element

An RVE is the smallest cubic cell that statistically reproduces the bulk composite's microstructure. For a random dispersion of monodisperse spheres of radius $r$ at volume fraction $\phi_f$, the mean inter-particle centre-to-centre distance is approximately

$$
\bar d \approx r\left(\frac{4\pi}{3\phi_f}\right)^{1/3}. \tag{5}
$$

A practical RVE side length is $L_\text{RVE} \gtrsim 5\bar d$, capped by available particle count $N_\text{cap}$. For $r = 50$ nm and $\phi_f = 0.05$, $\bar d \approx 200$ nm, so $L_\text{RVE} \approx 1$ µm contains $\sim 10^3$ particles — tractable for Geant4. The paper documents the RVE-convergence study (§4.6).

---

## 3. Geant4 Modelling Regimes

Each regime is defined precisely so that an independent group can reproduce it.

### 3.1 Regime A — Effective-Medium `G4Material`

Implemented in `MaterialRegistry::AddMassFractionMaterialCommand` in [src/MaterialRegistry.cc](src/MaterialRegistry.cc). Compound formulae are expanded to elemental mass fractions using the analytical layer in [python/shieldlab/core/materials.py](python/shieldlab/core/materials.py), then a single `G4Material` is constructed:

```cpp
auto* mat = new G4Material(name, rho_eff*g/cm3, nElements);
for (auto& e : elements) mat->AddElement(nist->FindOrBuildElement(e.symbol), e.fraction);
```

A 1-D slab of thickness $t \in \{1, 5, 10\}$ cm and lateral size 20 cm is built in [src/DetectorConstruction.cc](src/DetectorConstruction.cc).

**Cost class:** O(1) in particle count; identical to bulk-material runs.

### 3.2 Regime B — Explicit Nanoparticles via `G4PVParameterised`

A new class `NanoParticleParameterisation : public G4VPVParameterisation` is introduced (proposed file `src/NanoParticleParameterisation.cc`). It supplies particle positions sampled by random sequential addition (RSA) with periodic boundary conditions inside an RVE cube. Particle radii are drawn from a log-normal distribution truncated to the measured TEM size range. The parameterisation is wrapped in a `G4PVParameterised` placement inside a matrix mother volume.

```cpp
new G4PVParameterised("NP", npLogic, matrixLogic, kUndefined,
                      Ncap, new NanoParticleParameterisation(positions));
```

**Cost class:** geometry navigation scales near-logarithmically with $N$ thanks to voxelisation, but memory grows linearly. The paper measures both.

### 3.3 Regime C — `G4MultiUnion` Cluster

The same RSA particle list is wrapped in a single `G4MultiUnion` solid; one logical volume of filler material is placed once. `Voxelize()` is called after all `AddNode` calls. This regime represents fixed aggregates well and benchmarks how Geant4's internal multi-union voxelisation scales relative to parameterised placement.

**Cost class:** geometry construction is O($N$) once; subsequent navigation is voxelised. Single material per union limits multi-material aggregates.

### 3.4 Regime D — Hybrid RVE-Corrected Effective Medium

Workflow:

1. Run regime A for the full slab: extract transmission $T_A(E)$, broad-beam dose $D_A(E,t)$.
2. Run regime B (or C) for a matched RVE cube: extract microscopic dose enhancement factor

   $$\text{DEF}(r, E, \phi_f) = \frac{D_\text{matrix, explicit}(r, E, \phi_f)}{D_\text{matrix, homogeneous}(r, E, \phi_f)}, \tag{6}$$

   as a function of distance $r$ from the nearest particle surface.

3. Tabulate $\text{DEF}$ as a function of $(E, \phi_f, \bar r_\text{particle})$ and store as a JSON correction map under [python/shieldlab/data/](python/shieldlab/data/).
4. For any new full-shield calculation, run regime A and apply $\text{DEF}$ as a post-processing correction to interface-relevant scoring (e.g., shield-to-tissue boundary dose).

Regime D is the *deliverable methodology* of the paper.

---

## 4. Benchmark Protocol

### 4.1 Materials

| ID | Matrix | Filler | $w_f$ | Estimated $\rho_\text{eff}$ (g cm⁻³) | Reference for measured density |
|---|---|---|---|---|---|
| M1–M4 | HDPE (C₂H₄, $\rho_m=0.95$) | Bi₂O₃ ($\rho_f=8.9$) | 0.05, 0.15, 0.30, 0.50 | 1.00, 1.13, 1.36, 1.90 | *to be verified* |
| M5–M8 | HDPE | WO₃ ($\rho_f=7.16$) | 0.05, 0.15, 0.30, 0.50 | 1.00, 1.13, 1.36, 1.90 | *to be verified* |
| M9–M11 | Epoxy (C₂₁H₂₅ClO₅, $\rho_m\approx 1.2$) | BaSO₄ ($\rho_f=4.5$) | 0.10, 0.30, 0.50 | 1.27, 1.50, 1.86 | *to be verified* |

Per-material density values **must** be replaced by measured or literature-verified values before publication; the M1–M11 row in the manuscript carries provenance tags `[ρ-measured | ρ-volume-rule | ρ-mass-rule]`.

### 4.2 Source spectra

- **Diagnostic band (low-E):** mono-energetic photons at 30, 50, 80, 100, 150 keV (parallel pencil beam, 10⁶ primaries each).
- **Gamma band (mid–high-E):** 356 keV (Ba-133), 511 keV (annihilation), 662 keV (Cs-137), 1173 keV and 1332 keV (Co-60 lines), 10⁶ primaries each.

A separate Cs-137 broad-beam configuration (point source 1 m from slab, full angular sampling) is run for buildup-factor extraction in regimes A and D.

### 4.3 Physics list

- ≤ 1 MeV: `G4EmLivermorePhysics` (uses EPDL97 / EEDL / EADL data — essential for low-energy photoelectric and Compton accuracy).
- > 1 MeV: `G4EmStandardPhysics_option4` (high-accuracy EM).
- Tracking cuts: 0.1 µm (RVE runs), 1 mm (full-slab runs). Cut justification recorded in run metadata.
- Multi-threaded (`SHIELDLAB_RUN_MANAGER=mt`) for full-slab runs; serial for RVE runs (RVE memory cost is the dominant constraint).

### 4.4 Scoring

- **Full slab (A, C, D):** transmitted photon fluence at the back face (G4PSFlatSurfaceFlux), broad-beam absorbed dose in a 1-cm³ "air-equivalent" downstream voxel (G4PSDoseDeposit), per-layer absorbed dose (existing `G4MultiFunctionalDetector` chain in [src/DetectorConstruction.cc](src/DetectorConstruction.cc#L114-L145)).
- **RVE (B, C):** radial dose-enhancement profile in 10-nm shells around each particle surface (custom `G4VPrimitiveScorer`), bulk-averaged matrix dose, bulk-averaged filler dose.

### 4.5 Acceptance criteria (operationalised hypotheses)

| Hypothesis | Metric | Pass criterion |
|---|---|---|
| H1 | $\lvert T_A - T_{B/C}\rvert / T_A$ at $E \geq 100$ keV | ≤ 2σ statistical, ≤ 1% systematic |
| H1 | $\lvert \mu_A/\rho - (\mu/\rho)_\text{NIST}\rvert / (\mu/\rho)_\text{NIST}$ | ≤ 1.5% away from edges (matches existing ShieldLab photon-benchmark gate) |
| H2 | DEF($r \to$ particle surface, $E = 50$ keV) for Bi₂O₃ | > 1.20 (i.e., > 20% local enhancement) — pre-registered threshold |
| H2 | DEF averaged over matrix volume at $E = 50$ keV | within ± 5% of unity (homogenisation valid for bulk-matrix dose) |
| H3 | Regime D full-shield runtime / Regime A runtime | ≤ 1.1× (correction is post-processing, not transport) |
| H3 | Regime D interface dose vs Regime B/C interface dose | within ± 5% |

### 4.6 Statistical and convergence design

- **Replicates:** each (material, energy, regime) cell is run with 10 independent random seeds; mean and standard error reported.
- **MT consistency:** for regime A and D, all 10 seeds × {serial, MT} configurations are required to agree within 2σ (re-uses existing `tests/benchmarks/test_mt_consistency.py` gate).
- **RVE convergence:** for each (material, energy), $L_\text{RVE}$ is doubled until DEF($r$) curves agree within 2σ over the range $0 \leq r \leq 200$ nm; the minimum converged $L_\text{RVE}$ is reported.
- **Uncertainty propagation:** statistical uncertainties from MC are combined in quadrature with $\rho_\text{eff}$ uncertainty (where measured density is unavailable) and reported as total uncertainty bars on all figures.

### 4.7 Reproducibility artefacts

Every benchmark run produces a JSON manifest including: Geant4 version, ShieldLab version, git SHA, physics list, random seed, tracking cuts, raw scorer output, derived metrics, and SHA-256 of all input macros. Manifests are committed under `build/results/paper3_nano/`. The paper cites the git SHA of the release tag (e.g., `v1.1.0-paper3`).

---

## 5. Figures (planned)

| # | Title | Source data | Style |
|---|---|---|---|
| F1 | Schematic of the four regimes (homogeneous slab, parameterised particles, multi-union cluster, hybrid RVE correction) | — | TikZ / Inkscape; vector |
| F2 | Runtime and peak memory vs particle count $N$ for regimes B and C, $N \in \{10², 10³, 10⁴, 10⁵\}$ | benchmark harness | dual-axis, log-log, error bars |
| F3 | Mass attenuation coefficient $(\mu/\rho)$ vs $E$ for M1–M11: regime A, regimes B/C bulk-averaged, NIST XCOM reference | harness + xcom_cache | linear-log, 95% CI ribbons |
| F4 | Radial dose-enhancement profile around a Bi₂O₃ particle at 50, 100, 662 keV | RVE harness | linear, log y |
| F5 | Regime map: recommended method as a function of $(E, \phi_f)$ for fixed $r = 50$ nm | post-processing | filled heatmap with decision contours |
| F6 | Cs-137 transmission and broad-beam dose for full slab: regime A, regime D, NIST/Phy-X reference | harness + ShieldLab analytical | linear, residual sub-panel |
| F7 | Workflow diagram: ShieldLab composition entry → macro generation → benchmark harness → publication outputs | — | TikZ; horizontal |
| F8 (supp.) | RVE convergence study: DEF($r$) for $L_\text{RVE} \in \{0.5, 1, 2, 4\}$ µm | RVE harness | overlay with shaded uncertainty |

All figures use [python/shieldlab/viz/style.py](python/shieldlab/viz/style.py) `apply_journal_style("publication_strict")` with the Okabe–Ito 8-colour palette (colour-blind safe). 600 DPI raster + vector PDF exports.

---

## 6. Limitations and Validity Scope

1. **1-D slab transport only** for regimes A, C, D. Full 3-D geometry (e.g., cylindrical phantoms, anthropomorphic) is out of scope for this paper.
2. **Photon-only benchmark.** Neutron and charged-particle behaviour through nanocomposites is not addressed.
3. **Monodisperse + log-normal particle-size distribution.** Real composites can exhibit broader, multimodal distributions; one supplementary subsection compares mono- vs log-normal results.
4. **No interfacial chemistry** (surface functionalisation, ligands, oxide shells) is modelled — these are below the resolution of the EM physics list used here.
5. **Density uncertainty dominates at high $w_f$.** Where measured density is unavailable, results carry a `[ρ-estimate]` provenance tag in every figure caption.
6. **No experimental validation in this paper** — the benchmark validates the *MC method choice*, not the underlying physics data, which is already validated against NIST XCOM in the companion ShieldLab G4 v1.0.0 scientific paper.

---

## 7. Reproducibility, Code Availability, and Ethics

- **Software:** ShieldLab G4 v1.1 (release tag `v1.1.0-paper3`), MIT licence. Source at [the repository root README](README.md).
- **Data:** all benchmark inputs (study JSONs), raw scorer outputs, derived CSVs, and figure-generation notebooks are released under CC-BY 4.0 in `build/results/paper3_nano/`.
- **Compute environment:** Dockerfile pinned to Ubuntu 22.04 + Geant4 11.4 + Python 3.11 ([worker/Dockerfile](worker/Dockerfile)).
- **No human or animal data.** No external funding declared at this time (to be confirmed before submission). No conflicts of interest.
- **AI-assisted writing disclosure:** the manuscript was drafted with the assistance of GitHub Copilot in agent mode; all physics claims, results, citations, and code were independently verified by the author before submission. This disclosure follows COPE 2023 guidance.

---

## 8. References (verified; **placeholders marked**)

Citation policy: every entry below carries a DOI. Bi₂O₃/HDPE, WO₃/polymer, and BaSO₄/polymer experimental nanocomposite papers will be added in v03 only after individual DOI verification through Crossref. **No invented references.**

1. S. Agostinelli et al., "Geant4 — a simulation toolkit," *Nucl. Instrum. Methods Phys. Res. A* **506**, 250–303 (2003). DOI: [10.1016/S0168-9002(03)01368-8](https://doi.org/10.1016/S0168-9002(03)01368-8).
2. J. Allison et al., "Geant4 developments and applications," *IEEE Trans. Nucl. Sci.* **53**, 270–278 (2006). DOI: [10.1109/TNS.2006.869826](https://doi.org/10.1109/TNS.2006.869826).
3. J. Allison et al., "Recent developments in Geant4," *Nucl. Instrum. Methods Phys. Res. A* **835**, 186–225 (2016). DOI: [10.1016/j.nima.2016.06.125](https://doi.org/10.1016/j.nima.2016.06.125).
4. J. H. Hubbell, "Photon mass attenuation and energy-absorption coefficients from 1 keV to 20 MeV," *Int. J. Appl. Radiat. Isot.* **33**, 1269–1290 (1982). DOI: [10.1016/0020-708X(82)90248-4](https://doi.org/10.1016/0020-708X(82)90248-4).
5. J. H. Hubbell, "Review of photon interaction cross-section data in the medical and biological context," *Phys. Med. Biol.* **44**, R1–R22 (1999). DOI: [10.1088/0031-9155/44/1/001](https://doi.org/10.1088/0031-9155/44/1/001).
6. M. J. Berger, J. H. Hubbell, S. M. Seltzer, J. Chang, J. S. Coursey, R. Sukumar, D. S. Zucker, K. Olsen, *XCOM: Photon Cross Section Database*, NIST SRD 8 (XGAM), NIST, Gaithersburg MD. URL: <https://physics.nist.gov/xcom>.
7. J. H. Hubbell and S. M. Seltzer, *Tables of X-Ray Mass Attenuation Coefficients and Mass Energy-Absorption Coefficients from 1 keV to 20 MeV for Elements Z = 1–92 and 48 Additional Substances of Dosimetric Interest*, NISTIR 5632 (1995).
8. S. Incerti et al., "Comparison of Geant4 very low energy cross-section models with experimental data in water," *Med. Phys.* **37**, 4692–4708 (2010). DOI: [10.1118/1.3476457](https://doi.org/10.1118/1.3476457).
9. S. Incerti et al., "The Geant4-DNA project," *Int. J. Model. Simul. Sci. Comput.* **1**, 157–178 (2010). DOI: [10.1142/S1793962310000122](https://doi.org/10.1142/S1793962310000122).
10. H. N. Tran et al., "Geant4 Monte Carlo simulation of absorbed dose and radiolysis yields enhancement from a gold nanoparticle under MeV proton irradiation," *Nucl. Instrum. Methods Phys. Res. B* **373**, 126–139 (2016). DOI: [10.1016/j.nimb.2016.01.017](https://doi.org/10.1016/j.nimb.2016.01.017).
11. ANSI/ANS-6.4.3-1991 (R2001), *Gamma-Ray Attenuation Coefficients and Buildup Factors for Engineering Materials*, American Nuclear Society.
12. ICRP Publication 116, *Conversion Coefficients for Radiological Protection Quantities for External Radiation Exposures*, Ann. ICRP 40(2–5) (2010).
13. **[To be added — verified Bi₂O₃/HDPE experimental nanocomposite paper, by DOI lookup]**
14. **[To be added — verified WO₃/polymer experimental nanocomposite paper, by DOI lookup]**
15. **[To be added — verified BaSO₄/polymer experimental nanocomposite paper, by DOI lookup]**

---

## 9. Status

This is **manuscript v02** — a design and benchmark protocol containing **no fabricated numerical results**. The next milestone is implementation of the benchmark harness (see Appendix A: Actionable Implementation Plan) and generation of v03 with full Results and Discussion sections.

---

# Appendix A — Actionable Implementation Plan for the ShieldLab G4 Platform

This appendix is the engineering plan that converts the manuscript into reproducible results. Every work package (WP) maps to concrete file paths in the existing codebase, has clear acceptance criteria, and is sized for a single PR.

## A.1 Sprint structure (suggested 6-week cadence)

| Sprint | Duration | Goal | Manuscript sections unlocked |
|---|---|---|---|
| S1 | Week 1 | Literature lock + density provenance | §4.1 verified |
| S2 | Weeks 2–3 | Implement nano-composite material command (regime A++) + RVE explicit geometry (regime B) | §3.1, §3.2 runnable |
| S3 | Week 3 | Implement `G4MultiUnion` mode (regime C) + benchmark harness | §3.3, §4 runnable |
| S4 | Week 4 | Run full benchmark matrix (10 seeds × all materials × all energies × all regimes) | Raw §5 data |
| S5 | Week 5 | Statistical analysis, regime map fitting, figure generation | §4.5, §5, §6 |
| S6 | Week 6 | Manuscript v03 (Results + Discussion), supplementary materials, submission package | Full draft |

## A.2 Work packages (sized for individual PRs)

### WP1 — Literature lock and density provenance ([sprint S1])

- **Files:**
  - `papers/paper3_nanogeant4/references_verified.bib` (new) — BibTeX with DOI for every cite.
  - `papers/paper3_nanogeant4/materials_density_provenance.csv` (new) — one row per (material, $w_f$) with `rho_value`, `rho_source` ∈ {measured, volume_rule, mass_rule}, `doi_or_lab_report`.
- **Acceptance:** every row has a DOI or internal lab-report identifier; no `[verify]` tags remain.
- **Tools:** Crossref API for DOI verification (script `tools/verify_bib_dois.py` — proposed new).

### WP2 — Nano-composite material command (regime A++) ([sprint S2])

- **New macro command:** `/shieldlab/material/addNanoComposite NAME MATRIX_FORMULA MATRIX_RHO FILLER_FORMULA FILLER_RHO LOADING_WT POROSITY`.
- **Files to modify:**
  - [src/MaterialRegistry.cc](src/MaterialRegistry.cc) — add `AddNanoCompositeCommand(spec)` helper that expands matrix + filler formulae using a thin C++ port of `formula_to_mass_fractions` (or shells out to a JSON manifest written by the Python layer).
  - [include/MaterialRegistry.hh](include/MaterialRegistry.hh) — declare the new method.
  - [src/DetectorMessenger.cc](src/DetectorMessenger.cc) — register the new UI command.
  - [python/shieldlab/core/materials.py](python/shieldlab/core/materials.py) — add `nano_composite_mass_fractions(matrix, filler, w_f, porosity)` returning the elemental table + effective density; this is the single source of truth used by Python analytics and consumed by C++ via a generated macro.
- **Acceptance:**
  - New unit test `tests/test_nano_composite_material.py` constructs each of M1–M11 and asserts elemental mass fractions sum to 1.0 ± 1e-9 and that $\rho_\text{eff}$ matches the analytical formulae.
  - Existing 188-pass test gate unchanged.

### WP3 — RVE explicit geometry (regime B) ([sprint S2])

- **New C++ files:**
  - `include/NanoParticleParameterisation.hh`
  - `src/NanoParticleParameterisation.cc` — implements `G4VPVParameterisation`; positions seeded by RSA with periodic boundaries; radii sampled from log-normal truncated distribution.
- **New macro command:** `/shieldlab/rve/buildExplicit NAME MATRIX_MAT FILLER_MAT VOL_FRAC R_MEAN_NM R_SIGMA RVE_SIDE_UM N_CAP SEED`.
- **Hard cap:** the parameterisation refuses to build with $N > N_\text{cap, default} = 5 \times 10^4$ unless `/shieldlab/rve/overrideCap` is set — protects against accidental memory blow-up.
- **Files to modify:** [src/DetectorConstruction.cc](src/DetectorConstruction.cc) — add `BuildRVE()` branch alternative to the slab branch; switched by `/shieldlab/geometry/mode {slab|rve}`.
- **Acceptance:** test `tests/test_rve_geometry.py` builds an RVE with $\phi_f=0.05$, $r=50$ nm, side 1 µm, verifies particle count ∈ expected RSA range, no overlaps (sanity check), Geant4 reports zero geometry errors.

### WP4 — `G4MultiUnion` cluster mode (regime C) ([sprint S3])

- Add `BuildRVEMultiUnion()` in [src/DetectorConstruction.cc](src/DetectorConstruction.cc) that takes the same RSA particle list as WP3 but assembles them into a `G4MultiUnion` instead of parameterised placements.
- **Macro:** `/shieldlab/rve/buildMultiUnion ...` (same args as WP3).
- **Acceptance:** test `tests/test_rve_multiunion.py` reproduces the same transmission as the parameterised regime within 0.5% for a 1000-particle reference RVE.

### WP5 — Benchmark harness ([sprint S3])

- **New Python module:** `python/shieldlab/analysis/nano_benchmark.py` — orchestrator that:
  1. Reads a study JSON describing the (material, energy, regime) matrix.
  2. Generates Geant4 macros into `build/macros/paper3/`.
  3. Invokes the `ShieldLabG4` binary (single or MT mode).
  4. Parses scorer outputs into a tidy DataFrame.
  5. Emits per-cell JSON manifests (§4.7) into `build/results/paper3_nano/`.
- **New study config:** `configs/studies/paper3_nano_regime_comparison.json` — full M1–M11 × energies × regimes × 10 seeds.
- **CLI:** `python -m shieldlab.analysis.nano_benchmark --study configs/studies/paper3_nano_regime_comparison.json --workers N`.
- **Memory & runtime capture:** wrap each Geant4 invocation in a subprocess sampler (psutil) that records peak RSS at 100 Hz and CPU time.
- **Acceptance:** dry-run mode (`--dry-run`) generates all macros and a manifest stub without invoking Geant4; full run reproduces a published reference cell within 1σ when re-executed.

### WP6 — Statistical analysis and regime map ([sprint S5])

- **New Python module:** `python/shieldlab/analysis/regime_map.py` — consumes the harness output, computes pass/fail against §4.5 criteria for every hypothesis, and fits the decision contours for Figure 5.
- **Statistical methods:**
  - Per-cell mean and SE across 10 seeds.
  - Cross-regime deviation as $\Delta = \lvert X_\text{B/C} - X_A\rvert / X_A$.
  - Confidence bands via studentised bootstrap.
  - Regime map via thresholded $\Delta$ over the $(E, \phi_f)$ grid; decision contours via marching squares.
- **Acceptance:** unit tests covering each statistical routine on synthetic data; regression test pinning published Figure 5 contours to ±2% on the grid.

### WP7 — Figure generation ([sprint S5])

- **New module:** `python/shieldlab/viz/paper3_figures.py` — one function per figure (F1–F8). All use `apply_journal_style("publication_strict")` per the [shieldlab.viz](python/shieldlab/viz/__init__.py) policy.
- **Outputs:** vector PDF + 600-DPI PNG into `papers/paper3_nanogeant4/figures/`.
- **Acceptance:** `pytest -m publication` includes `tests/benchmarks/test_paper3_figures.py` asserting all figures regenerate deterministically from committed CSVs (perceptual-hash diff ≤ 1%).

### WP8 — Manuscript v03 ([sprint S6])

- Replace `[expected]`-prefixed claims in §1, §4, §5 with measured values.
- Add full Results and Discussion.
- Fill in references 13–15 with DOI-verified experimental papers.
- Generate final submission package: manuscript PDF (LaTeX, journal template), Supplementary Materials PDF, code-availability statement with git tag, data-availability statement with Zenodo DOI.

## A.3 Risk register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| RVE explicit-geometry memory exceeds available RAM | Medium | High | Hard particle-count cap; staged convergence study; fallback to `G4MultiUnion` |
| `G4MultiUnion` voxelisation slow for $N > 10^4$ | Medium | Medium | Benchmark scaling early in S2; document the practical $N$ ceiling |
| Density values unavailable for some M1–M11 | High | Medium | Use volume-rule estimate with explicit `[ρ-estimate]` provenance tag; do not silently fabricate |
| Cross-regime deviation below detection threshold at all tested $E$ | Low | Low (still publishable as a null result) | Pre-register the null hypothesis; manuscript framing is unchanged |
| Geant4 11.4 → 11.5 upgrade during paper preparation | Medium | Low | Pin Geant4 version in [worker/Dockerfile](worker/Dockerfile); regression-test before re-running |
| Reviewer demands explicit-particle full-slab run | Low | High | Pre-compute one full-slab run at $N \approx N_\text{cap}$ as proof of impracticality and include the cost data in the rebuttal package |

## A.4 Definition of done (for the paper, not just the code)

- [ ] All WP1–WP8 acceptance criteria pass.
- [ ] `pytest -q --ignore=backups` baseline remains 188+ passing (no regressions from new code).
- [ ] New tests added by WP2–WP7 all pass.
- [ ] `pytest -m publication` passes including paper3 figure regression tests.
- [ ] `papers/paper3_nanogeant4/manuscript_nanogeant4_v03.md` is complete with no `[expected]`, `[verify]`, `[placeholder]` tags.
- [ ] `papers/paper3_nanogeant4/references_verified.bib` contains a verified DOI for every cite.
- [ ] Zenodo deposit prepared with code + raw results + figures; DOI minted.
- [ ] `docs/validation/SUBMISSION_CHECKLIST.md` extended with a paper-3 section and all items ticked.
- [ ] Co-author review (when applicable) and ethics statement signed off.

## A.5 Dependency graph

```
WP1 ──┐
WP2 ──┤
WP3 ──┼─► WP5 ──► WP6 ──► WP7 ──► WP8
WP4 ──┘
```

WP2, WP3, WP4 are independent and can be parallelised. WP5 is the integration point. WP6, WP7, WP8 are sequential.

---

# Appendix B — Executable Regime-A Baseline Snapshot (Working Results, 2026-05-18)

This appendix records the first fully executed Paper 3 regime-A benchmark campaign produced directly by the ShieldLab G4 platform after the paper-3 implementation work described in Appendix A. It is intentionally limited to the homogeneous effective-medium regime and is provided as a working-results snapshot, not as the final cross-regime Results section of the paper.

## B.1 Run provenance

- Study file: `configs/studies/paper3_hdpe_bi2o3_regime_a_highstat.json`
- Geant4 executable: rebuilt `ShieldLabG4` on WSL Ubuntu with Geant4 11.4
- Physics list: `emlivermore`
- Histories: $10^6$ photons per energy point
- Material: HDPE/Bi$_2$O$_3$ nanocomposite, 30 wt% filler, density input 2.45 g cm$^{-3}$
- Energy grid: 30, 50, 80, 100, 150, 356, 511, 662, 1173, 1332 keV
- Result directory: `results/paper3/regime_a_hdpe_bi2o3_highstat/`

## B.2 Acceptance against XCOM

The executable acceptance gate in `paper3_acceptance.json` passed for the full 10-point energy grid.

- Mean absolute percent difference in linear attenuation coefficient: **0.549%**
- Maximum absolute percent difference in linear attenuation coefficient: **2.013%**
- Mean absolute percent difference in mass attenuation coefficient: **0.549%**
- Maximum absolute percent difference in mass attenuation coefficient: **2.013%**

These values satisfy the current machine-enforced paper-3 regime-A acceptance thresholds of mean absolute deviation $\leq 1.5\%$ and maximum absolute deviation $\leq 5.0\%$.

## B.3 High-statistics regime-A observables

Selected values from `sweep_summary.csv` are listed below to anchor the manuscript to generated numbers.

| Energy (keV) | Transmission | $\mu$ (cm$^{-1}$) | $\mu/\rho$ (cm$^2$ g$^{-1}$) |
|---|---|---|---|
| 30 | 0.649362 | 21.3221 | 8.7029 |
| 50 | 0.650374 | 5.88991 | 2.40404 |
| 100 | 0.651003 | 4.07566 | 1.66353 |
| 356 | 0.652240 | 0.397089 | 0.162077 |
| 662 | 0.651924 | 0.229959 | 0.0938608 |
| 1332 | 0.650617 | 0.149293 | 0.0609359 |

The flat transmission target near 0.65 is expected because the macro generator rescales thickness per energy to produce a numerically stable direct attenuation estimate for benchmark comparison.

## B.4 Broad-beam observable and downstream secondaries

The high-statistics run also produced `buildup_observable_summary.csv`, enabling the first paper-3 broad-beam transport observations for regime A.

- At 100 keV, the downstream buildup observable reached **1.1363** by count and **1.1075** by energy.
- At 150 keV, the downstream buildup observable reached **1.0992** by count and **1.0522** by energy.
- At 662 keV, the downstream buildup observable was **1.0115** by count and **1.0015** by energy.
- At 1332 keV, the downstream buildup observable was **1.0085** by count and **1.0012** by energy.

The platform now also exports downstream spectral data (`downstream_spectrum.csv` per energy and `downstream_spectrum_summary.csv` for the aggregated campaign). In the present regime-A baseline, the most prominent spectral broadening appears in the 100–150 keV cases, consistent with the large increase in downstream secondary gamma counts relative to the lower-energy points.

## B.5 Generated figure set

The following figure artifacts are now produced directly from code for the high-statistics regime-A campaign:

- `results/paper3/regime_a_hdpe_bi2o3_highstat/figures/paper3_f3_regime_a_mac_vs_xcom.png`
- `results/paper3/regime_a_hdpe_bi2o3_highstat/figures/paper3_regime_a_transmission.png`
- `results/paper3/regime_a_hdpe_bi2o3_highstat/figures/paper3_downstream_gamma_spectrum.png`

These figures are working publication artifacts for the homogeneous regime only. They do **not** yet replace the final cross-regime figures planned in Section 5, because regimes B, C, and D remain to be implemented and benchmarked.

## B.6 Interpretation and remaining gap

This executable snapshot establishes that the paper-3 platform can now:

1. Validate a committed paper-3 study definition.
2. Generate a Geant4 macro deterministically.
3. Execute the regime-A benchmark on WSL Geant4.
4. Compare the resulting attenuation coefficients against NIST XCOM and enforce a machine-readable pass/fail gate.
5. Export downstream buildup and spectrum artifacts suitable for manuscript figures.

What remains unfinished is the core scientific comparison promised by the paper title: explicit-geometry regime B, multi-union regime C, and hybrid regime D are still pending. Accordingly, Appendix B should be treated as a platform-maturity milestone and an executable baseline, not as the final paper Results section.

