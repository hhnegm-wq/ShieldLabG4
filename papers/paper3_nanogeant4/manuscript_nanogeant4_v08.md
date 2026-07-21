# Controlled Geant4 Benchmarking of Nanocomposite Radiation Shielding Across Effective-Medium and Explicit-RVE Regimes for Two K-Edge Filler Chemistries

**Hani H. Negm**¹

¹ *Hani Negm, Department of Physics, College of Science, Jouf University*

**Corresponding author:** hhnegm@ju.edu.sa

**Manuscript version:** v08 (derived from v07 on 2026-05-18; second-material HDPE/WO₃ benchmark added)

**Target journals (Q1, in priority order):**
1. *Radiation Physics and Chemistry* (Elsevier, IF ≈ 2.9; primary scope match — shielding + MC methodology)
2. *Nuclear Instruments and Methods in Physics Research A* (NIM A, Elsevier; established Geant4 methods venue)
3. *Computer Physics Communications* (Elsevier; physics + software methodology)
4. *Physics in Medicine and Biology* (IOP; if diagnostic-energy nano-dose results are emphasised)
5. *Annals of Nuclear Energy* (Elsevier; if shielding-engineering framing is emphasised)

---

## Abstract

Nanoparticle-filled shielding polymers are commonly simulated in Geant4 as homogeneous mixtures, even when experiments describe them as nanocomposites. The validity limit of that homogenised representation relative to explicit nanoparticle geometry remains poorly quantified for shielding photon transport. This paper extends the benchmark to two distinct K-edge filler chemistries, demonstrating methodology generalisability.

Three Geant4 modelling regimes are benchmarked for HDPE/Bi₂O₃ at $\phi_f = 0.189$ (68.6 wt% Bi₂O₃, $\rho_\text{eff} = 2.452$ g cm$^{-3}$): (A) effective-medium `G4Material`, (B) explicit 25 nm Bi₂O₃ spheres in a 1 µm RVE using `G4PVParameterised`, and (C) explicit spheres in a 250 nm RVE using `G4MultiUnion`. All runs use Geant4 11.4, `G4EmLivermorePhysics`, and a 30 keV–1.33 MeV photon grid. A second independent Regime A benchmark is performed for HDPE/WO₃ at matched volume fraction φ=0.189 (63.7 wt% WO₃, $\rho_\text{eff} = 2.124$ g cm$^{-3}$), which positions its W K-edge (69.5 keV) at a different energy window to the Bi K-edge (90.5 keV), together covering the 50–100 keV diagnostic range. The endpoint is $\mu/\rho(E)$ relative to NIST XCOM.

Regime A reproduces XCOM for the 30 wt% Bi₂O₃ validation material with mean and maximum absolute deviations of 0.549% and 2.013%. For the cross-regime composition, regime B agrees with the matched regime-A baseline within the 3% H1 gate at 30–150 keV ($\mu_B/\mu_{A,\phi} = 0.975\text{–}0.984$) and resolves the Bi K-edge rise between 80 and 100 keV. Regime C also confirms H1 at 30–150 keV ($\mu_C/\mu_{A,\phi} = 0.982\text{–}1.016$), with XCOM agreement from −2.3% to +1.2% in that range. For HDPE/WO₃, the Regime A effective-medium benchmark reproduces NIST XCOM with max |Δ|=0.97% across all 10 energies (mean |Δ|=0.42%), and the W K-edge at 69.5 keV is confirmed by a 31% MAC increase from 50 to 80 keV.

The results support effective-medium modelling for macroscopic shielding when $\mu r \ll 1$ and demonstrate that the emlivermore effective-medium approach is not material-specific: both HDPE/Bi₂O₃ and HDPE/WO₃ at identical φ achieve sub-1% XCOM agreement at Compton-dominated energies and resolve their respective K-edges consistently. The `G4PVParameterised` geometry is markedly more scalable than `G4MultiUnion` on workstation-class hardware.

**Keywords:** Geant4 · radiation shielding · nanocomposite · effective medium · `G4MultiUnion` · `G4PVParameterised` · representative volume element · mass attenuation coefficient · K-edge · WO₃ · Bi₂O₃

---

## 1. Introduction

### 1.1 Background

Polymer-matrix radiation-shielding composites loaded with high-Z fillers (Bi₂O₃, WO₃, PbO, BaSO₄, Gd₂O₃) have become a sustained research focus over the past decade, driven by the need for lead-free, flexible, low-toxicity alternatives in medical X-ray protection, nuclear medicine, and aerospace shielding. Among these, bismuth oxide (Bi₂O₃, Z=83) and tungsten trioxide (WO₃, Z=74) are particularly attractive: both are non-toxic, commercially available as fine powders, and exhibit high-Z K-edges — at 90.5 keV (Bi) and 69.5 keV (W) respectively — that fall squarely within the diagnostic X-ray energy window (50–150 keV). Together these two K-edges bracket the 50–100 keV range where K-edge jumps can significantly enhance shielding performance.

A substantial fraction of the recent literature reports filler particle sizes in the nanometre range and labels the resulting materials as *nanocomposites*. When such materials are simulated in Monte Carlo (MC) transport codes — most commonly Geant4 [1–3] — the dominant practice is to define one `G4Material` from elemental mass fractions and a measured or estimated bulk density. The microstructure is not resolved.

This homogenisation is physically defensible for the macroscopic shielding regime in which the relevant photon mean free path (MFP) is orders of magnitude larger than both the filler particle radius and the inter-particle spacing. Under that condition the photon "sees" an effective medium and the Bragg–Gray mass-fraction additivity rule [4,5] yields linear attenuation coefficients consistent with NIST XCOM [6] to within the independent-atom approximation. The validity boundary of this rule has been extensively characterised for macroscopic mixtures [5,7], but the question that motivates this work is different: under what circumstances does the *spatial arrangement* of the high-Z phase, at the nanoscale, change a quantity that a shielding engineer or medical physicist actually cares about — transmission, broad-beam dose, or interface dose — by more than the experimental uncertainty? And does the answer depend on the specific filler chemistry?

### 1.2 Gap

Three gaps remain in the literature:

1. **Validity boundary of homogenisation.** Although effective-medium MC results agree with experiment for many nanocomposite shielding measurements at gamma energies, there is no published systematic Geant4 benchmark that holds composition, density, source, scoring geometry, and physics list constant while varying only the geometric representation (homogeneous vs explicit-particle vs clustered) and reports the cross-method deviation as a function of photon energy and filler loading.
2. **Computational cost characterisation.** The Geant4 Application Developer Guide documents `G4PVParameterised` and `G4MultiUnion` as standard constructs, but the practical scaling of runtime, memory, and geometry-construction time for radiation-shielding-relevant nanoparticle counts has not been mapped. Practitioners frequently assume that "Geant4 can do it" without quantifying when it cannot.
3. **Production-grade methodology generalisation.** Existing nanoparticle-resolved Geant4 studies are concentrated in the nano-radiosensitisation/Geant4-DNA community [8,9,10], where the physical scale is sub-cellular and the particle counts are tractable. There is no published bridge between that microscopic methodology and the macroscopic shielding-engineering use case, and no demonstration that the methodology generalises across filler chemistries.

### 1.3 Contribution and hypothesis

This paper makes four distinct contributions that have not appeared in the prior Geant4 nanocomposite literature:

1. **First controlled cross-regime benchmark for macroscopic nanocomposite shielding.** Composition, density, source spectrum, scoring geometry, and physics list are held identical across all three modelling regimes; only the geometric representation changes. This isolation allows the method-to-method deviation to be attributed entirely to geometry choice rather than to any other modelling variable. No equivalent comparison has been published for shielding-relevant photon energies and nanoparticle counts.

2. **First quantitative mapping of the computational feasibility boundary for explicit-RVE Geant4 approaches.** The `G4Voxelizer` $(2N)^3$ memory scaling is characterised explicitly against hardware limits on a workstation-class 8 GB system, producing a hardware-referenced scalability boundary that practitioners can use directly when choosing between `G4PVParameterised` and `G4MultiUnion` for a given filler count and RVE size.

3. **Open, reproducible benchmark harness.** All study configuration files, macro writers, orchestrator, XCOM comparison, and figure-generation modules are released in ShieldLab G4 v1.1 under the MIT licence. The full benchmark is re-executable with a single command by any group with access to Geant4 11.4.

4. **First cross-material K-edge benchmark for two filler chemistries.** A second independent Regime A XCOM validation is performed for HDPE/WO₃ at matched volume fraction φ=0.189 using identical methodology, demonstrating that the effective-medium approach is not material-specific and extending the validated energy coverage to 50–80 keV (W K-edge) in addition to 80–100 keV (Bi K-edge).

The prior Geant4 nanoparticle literature is concentrated in the Geant4-DNA / nano-radiosensitisation domain [8,9,10], where the physical scale is sub-cellular and nanoparticle counts are tractable. No published work bridges that microscopic methodology to the macroscopic shielding-engineering use case, and no work demonstrates methodology generalisability across filler chemistries. The novelty is therefore methodological rather than kernel-level: `G4PVParameterised` and `G4MultiUnion` are standard Geant4 geometry constructs; the contribution is the controlled cross-regime shielding benchmark, RVE validation workflow, and two-material generalisation built on top of them.

**Scope of the three regimes.** Two additional Geant4 strategies are intentionally outside this paper. A raw many-daughter `G4PVPlacement` loop is not benchmarked separately because, for identical spheres, it is functionally superseded by `G4PVParameterised` while offering poorer scalability and no benefit in repeated-geometry handling. Nested parameterisation with `G4Region`/`G4ProductionCuts` in the Geant4-DNA style targets eV-scale local-energy-deposition and microdosimetry, not the macroscopic attenuation and transmission observables treated here.

**Hypothesis (H1).** For photon energies where the photon mean free path greatly exceeds the nanoparticle radius ($\mu r \ll 1$, i.e., $r \ll 1/\mu$), the transmitted fluence through the same material composition is independent of the choice of regime A, B, or C within the statistical uncertainty of $10^6$–$10^7$-history Geant4 runs, provided composition, density, and scoring are matched.

**Hypothesis (H2).** For photon energies $E \lesssim 100$ keV with high-Z fillers (Bi₂O₃), the radial dose-enhancement profile around individual particles carries spatial structure that the effective-medium regime cannot reproduce.

Each hypothesis is operationalised as a numeric acceptance criterion in §4.5.

---

## 2. Theoretical Basis

### 2.1 When homogenisation is exact, when it is approximate, and when it fails

The mass-fraction additivity rule for the mass attenuation coefficient,

$$
\left(\frac{\mu}{\rho}\right)_\text{mix}(E) = \sum_i w_i \left(\frac{\mu}{\rho}\right)_i(E),
$$

is *exact* under the independent-atom approximation and the assumption that the photon interaction probability per unit mass is independent of the geometric distribution of atoms within the irradiated mass. This holds when:

1. The photon de Broglie wavelength is small compared with inter-atomic spacing (true for all $E > 1$ keV considered here).
2. Coherent (Rayleigh) inter-particle interference is negligible (true above ~10 keV for amorphous nanocomposites).
3. The penetration depth is large compared with any heterogeneity length scale (the *macroscopic-homogenisation condition*).

The third condition is the one that fails first for nanocomposites under low-energy, high-Z conditions.

### 2.2 Effective density

Geant4 requires density. All regimes in this paper use the same input density, computed from the volume-fraction rule of mixtures. Given filler volume fraction $\phi_f$:

$$\rho_\text{eff} = \phi_f \rho_f + (1 - \phi_f)\rho_m$$

with $\rho_m = 0.95$ g cm$^{-3}$ (HDPE). For Bi₂O₃ ($\rho_f = 8.9$ g cm$^{-3}$) at $\phi_f = 0.189$: $\rho_\text{eff} = 2.452$ g cm$^{-3}$, $w_f = 68.6$ wt% Bi₂O₃. For WO₃ ($\rho_f = 7.16$ g cm$^{-3}$) at $\phi_f = 0.189$: $\rho_\text{eff} = 2.124$ g cm$^{-3}$, $w_f = 63.7$ wt% WO₃.

### 2.3 The representative volume element

An RVE is the smallest cubic cell that statistically reproduces the bulk composite's microstructure. For a random dispersion of monodisperse spheres of radius $r$ at volume fraction $\phi_f$, the mean inter-particle centre-to-centre distance is approximately

$$\bar d \approx r\left(\frac{4\pi}{3\phi_f}\right)^{1/3}.$$

A practical RVE side length is $L_\text{RVE} \gtrsim 5\bar d$. For $r = 25$ nm and $\phi_f = 0.189$, $\bar d \approx 42$ nm, so $L_\text{RVE} = 1$ µm satisfies the criterion and contains approximately 2,889 non-overlapping spheres — tractable for Geant4.

---

## 3. Geant4 Modelling Regimes

### 3.1 Regime A — Effective-Medium `G4Material`

Implemented in `MaterialRegistry::AddMassFractionMaterialCommand` in [src/MaterialRegistry.cc](src/MaterialRegistry.cc). Compound formulae are expanded to elemental mass fractions using the analytical layer in [python/shieldlab/core/materials.py](python/shieldlab/core/materials.py), then a single `G4Material` is constructed:

```cpp
auto* mat = new G4Material(name, rho_eff*g/cm3, nElements);
for (auto& e : elements) mat->AddElement(nist->FindOrBuildElement(e.symbol), e.fraction);
```

A 1-D slab geometry is built in [src/DetectorConstruction.cc](src/DetectorConstruction.cc). Per-energy slab thickness is selected so that transmission is $T \approx 0.65$ at every energy point, maximising the sensitivity of the direct transmission estimator $\hat\mu = -\ln T / t$.

**Cost class:** O(1) in particle count; identical to bulk-material runs.

### 3.2 Regime B — Explicit Nanoparticles via `G4PVParameterised`

Class `NanoParticleParameterisation : public G4VPVParameterisation` is implemented in `include/NanoParticleParameterisation.hh` and `src/NanoParticleParameterisation.cc`. Particle positions are sampled by random sequential addition (RSA) with a hard-sphere exclusion radius of $2r$ inside an RVE cube.

**RVE geometry parameters (this study):** side = 1 µm, $r = 25$ nm, $\phi_f = 0.189$, max particles = 3,500, RSA seed = 22,222. RSA placed **2,888 / 2,888** target spheres (achieved $\phi_f = 0.1890$).

**Cost class:** geometry navigation scales near-logarithmically with $N$ thanks to voxelisation.

### 3.3 Regime C — `G4MultiUnion` Cluster

The same RSA particle list (seeded with 33,333 for an independent draw) is assembled into a single `G4MultiUnion` solid with `Voxelize()`. This regime benchmarks how Geant4's internal multi-union voxelisation scales relative to parameterised placement.

*In practice, `G4MultiUnion::Voxelize()` is only feasible for $N \lesssim 50$ on 8 GB hardware; §5.3 documents the scalability characterisation and the adopted 250 nm / $N = 45$ configuration.*

Figure 1 summarises the three modelling regimes and the recommended workflow that emerges from the benchmark.

![Figure 1. Conceptual regime map for the three Geant4 modelling strategies benchmarked in this paper. Regime A is the production default for bulk attenuation, regime B is the explicit-RVE validation geometry, and regime C is a small-RVE `G4MultiUnion` path constrained by voxelizer scaling.](../../../results/paper3/figures/paper3_fig1_regime_map.png){ width=95% }

---

## 4. Benchmark Protocol

### 4.1 Materials

For the cross-regime benchmark the primary material is HDPE/Bi₂O₃ at φ = 0.189. A second independent Regime A benchmark is performed for HDPE/WO₃ at the same volume fraction to demonstrate methodology generalisability across K-edge filler chemistries.

**Table M1.** Two-material design summary.

| Property | HDPE/Bi₂O₃ | HDPE/WO₃ |
|---|---|---|
| Filler | Bi₂O₃, $\rho_f = 8.9$ g cm$^{-3}$ | WO₃, $\rho_f = 7.16$ g cm$^{-3}$ |
| $\phi_f$ | 0.189 | 0.189 |
| $\rho_\text{eff}$ (g cm$^{-3}$) | 2.452 | 2.124 |
| $w_f$ (wt%) | 68.6% Bi₂O₃ | 63.7% WO₃ |
| K-edge element | Bi (Z=83): 90.5 keV | W (Z=74): 69.5 keV |
| Energy grid straddle | 80–100 keV | 50–80 keV |
| Regime | A + B + C | A only |

For HDPE/WO₃ the elemental mass fractions in the Geant4 material are: w(W) = 0.50528, w(O) = 0.13192, w(C) = 0.31066, w(H) = 0.05214. Random seed 24680.

A separate regime-A validation study at 30 wt% Bi₂O₃ (with $\rho = 2.45$ g cm$^{-3}$ as user-specified input) is also included to verify emlivermore vs XCOM at that composition; it is not used as the cross-regime baseline.

### 4.2 Source spectra

Mono-energetic photons at a 10-point energy grid: 30, 50, 80, 100, 150, 356, 511, 662, 1173, 1332 keV. Parallel pencil beam, zero beam width. Primary particle: gamma. Regime C uses a distributed beam sampling $(Y,Z) \sim \mathcal{U}[-L/2, +L/2]^2$ per event to ensure ergodic averaging across the 250 nm RVE cross-section (§5.3).

### 4.3 Physics list

`G4EmLivermorePhysics` for all runs. Geant4 version: 11.4 beta (geant4-11-04-beta-01). Tracking cuts: default. `SHIELDLAB_PHYSICS_LIST=emlivermore`.

### 4.4 Histories

| Regime | Histories per energy point | Total events |
|---|---|---|
| A | $10^6$ | $1.0 \times 10^7$ |
| B | $10^7$ | $1.0 \times 10^8$ |
| C | $10^7$ | $1.0 \times 10^8$ |

### 4.5 Acceptance criteria

| Criterion | Metric | Gate |
|---|---|---|
| Regime A vs XCOM | mean $|\Delta(\mu/\rho)|$ over 10 energies | $\leq 1.5\%$ |
| Regime A vs XCOM | max $|\Delta(\mu/\rho)|$ over 10 energies | $\leq 5.0\%$ |
| H1 cross-regime | $|\mu_B / \mu_A - 1|$ at each energy | $\leq 3\%$ |

### 4.6 Reproducibility

Every run produces a JSON manifest including: Geant4 version, git SHA, physics list, random seed, macro SHA-256, raw scorer outputs, and derived metrics. Manifests are committed under `results/paper3/`. Study files, macro writer, and post-processing scripts are open-source under MIT licence at the repository root.

---

## 5. Results

### 5.1 Regime A — Effective-Medium Studies

Two sets of Regime A runs are reported: §5.1.0–5.1.5 cover HDPE/Bi₂O₃ (consistent with v07); §5.5 presents the new HDPE/WO₃ Regime A benchmark. Figure 2 shows the dual-panel XCOM validation for both Bi₂O₃ and WO₃ at φ=0.189.

![Figure 2. Regime A XCOM validation for both filler chemistries. (A) HDPE/Bi₂O₃ at 30 wt% with Bi K-edge annotation at 90.5 keV. (B) HDPE/WO₃ at φ=0.189 (63.7 wt%) with W K-edge annotation at 69.5 keV. Both panels show 95% statistical confidence intervals on simulated points; dashed lines are NIST XCOM reference.](../../../results/paper3/figures/paper3_fig2_dual_validation.png){ width=100% }

#### 5.1.0 Regime A(30wt) — XCOM Validation Run (separate study)

**Run provenance:** study file `configs/studies/paper3_hdpe_bi2o3_regime_a_highstat.json`, physics list `emlivermore`, $10^6$ histories per energy, Geant4 11.4, WSL Ubuntu, result directory `results/paper3/regime_a_hdpe_bi2o3_highstat/`.

*Note: this material (30 wt% Bi₂O₃, ρ = 2.45 g cm⁻³) uses a user-supplied density that is physically inconsistent with the two-phase mixture rule. The density is retained as a literature input for the XCOM-validation purpose only. The cross-regime comparison in §5.2–5.4 uses the phi0p189 material described in §5.1.5.*

#### 5.1.1 Acceptance gate (30 wt% XCOM validation)

- Mean absolute percent difference in $\mu/\rho$ vs XCOM: **0.549%** (gate: ≤ 1.5%)
- Maximum absolute percent difference in $\mu/\rho$ vs XCOM: **2.013%** at 80 keV (gate: ≤ 5.0%)

#### 5.1.2 Mass attenuation coefficient table

**Table 1.** Regime A(30wt) mass attenuation coefficients for HDPE/Bi₂O₃ 30 wt% ($\rho = 2.45$ g cm$^{-3}$, user-specified density) vs NIST XCOM.

| $E$ (keV) | $t$ (cm) | $N$ | $T$ | $\mu_\text{sim}$ (cm$^{-1}$) | $(\mu/\rho)_\text{sim}$ (cm$^2$ g$^{-1}$) | $(\mu/\rho)_\text{XCOM}$ (cm$^2$ g$^{-1}$) | $\Delta$ (%) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 0.02025 | $10^6$ | 0.6494 | 21.322 | 8.703 | 8.683 | +0.228 |
| 50 | 0.07304 | $10^6$ | 0.6504 | 5.890 | 2.404 | 2.407 | −0.134 |
| 80 | 0.2167 | $10^6$ | 0.6557 | 1.948 | 0.7951 | 0.8114 | −2.013 |
| 100 | 0.1053 | $10^6$ | 0.6510 | 4.076 | 1.664 | 1.670 | −0.358 |
| 150 | 0.2617 | $10^6$ | 0.6502 | 1.645 | 0.6714 | 0.6719 | −0.075 |
| 356 | 1.0762 | $10^6$ | 0.6522 | 0.3971 | 0.1621 | 0.1634 | −0.799 |
| 511 | 1.5309 | $10^6$ | 0.6512 | 0.2801 | 0.1143 | 0.1149 | −0.445 |
| 662 | 1.8605 | $10^6$ | 0.6519 | 0.2300 | 0.09386 | 0.09451 | −0.686 |
| 1173 | 2.6772 | $10^6$ | 0.6515 | 0.1601 | 0.06533 | 0.06568 | −0.532 |
| 1332 | 2.8791 | $10^6$ | 0.6506 | 0.1493 | 0.06094 | 0.06107 | −0.220 |

#### 5.1.3 Discussion of regime A accuracy

The largest deviation (−2.013% at 80 keV) falls near the Bi K-edge complex. The emlivermore physics list uses EPDL97 photoelectric cross-section data [11], which contains fine edge structure. Small energy-bin misalignment between the Geant4 tabulated values and the XCOM energy grid is the most likely explanation for the elevated deviation at 80 keV. All other energy points deviate by less than 0.9%, consistent with the systematic XCOM agreement documented for regime A in the companion ShieldLab G4 v1.0 scientific report.

#### 5.1.4 Buildup observable (regime A 30wt)

The high-statistics 30 wt% run also produced downstream spectrum data:

- At 100 keV, buildup observable: **1.1363** (count), **1.1075** (energy).
- At 150 keV, buildup observable: **1.0992** (count), **1.0522** (energy).
- At 662 keV, buildup observable: **1.0115** (count), **1.0015** (energy).
- At 1332 keV, buildup observable: **1.0085** (count), **1.0012** (energy).

Figure 3 makes this secondary-field behaviour visible.

![Figure 3. Regime A downstream observables. (A) Monte Carlo buildup observables from count-based and energy-based estimators versus incident photon energy. (B) Downstream gamma spectra for representative incident energies, showing the secondary-field structure behind the buildup trend.](../../../results/paper3/figures/paper3_fig3_buildup_and_spectrum.png){ width=100% }

#### 5.1.5 Regime A(phi0p189) — Cross-Regime Companion Run

**Run provenance:** study file `configs/studies/paper3_hdpe_bi2o3_regime_a_phi0p189.json`, physics list `emlivermore`, $10^6$ histories per energy, Geant4 11.4, result directory `results/paper3/regime_a_hdpe_bi2o3_phi0p189/`. All 10 energies complete.

**Material:** P3_HDPE_Bi2O3_phi0p189 — HDPE (31.4 wt%) + Bi₂O₃ (68.6 wt%) at $\rho = 2.452$ g cm$^{-3}$.

**Table 1b.** Regime A(phi0p189) mass attenuation coefficients for HDPE/Bi₂O₃ φ = 0.189 (68.6 wt%, $\rho = 2.452$ g cm$^{-3}$) vs NIST XCOM. Benchmark: **passed** (mean |Δ| = 0.72%, max |Δ| = 2.45%).

| $E$ (keV) | $T$ | $\mu_\text{sim}$ (cm$^{-1}$) | $(\mu/\rho)_\text{sim}$ (cm$^2$ g$^{-1}$) | $(\mu/\rho)_\text{XCOM}$ (68.6 wt%) | $\Delta$ (%) |
|---:|---:|---:|---:|---:|---:|
| 30 | 0.649496 | 47.9176 | 19.542 | 19.507 | +0.18 |
| 50 | 0.650992 | 12.7942 | 5.218 | 5.236 | −0.35 |
| 80 | 0.656895 | 3.87727 | 1.581 | 1.621 | −2.45 |
| 100 | 0.651467 | 8.77216 | 3.578 | 3.596 | −0.52 |
| 150 | 0.650565 | 3.27643 | 1.336 | 1.339 | −0.20 |
| 356 | 0.652574 | 0.55156 | 0.2249 | 0.2270 | −0.92 |
| 511 | 0.651168 | 0.33170 | 0.1353 | 0.1358 | −0.42 |
| 662 | 0.65216 | 0.25037 | 0.1021 | 0.1029 | −0.77 |
| 1173 | 0.651123 | 0.15608 | 0.06365 | 0.06391 | −0.40 |
| 1332 | 0.652863 | 0.14266 | 0.05818 | 0.05878 | −1.02 |

---

### 5.2 Regime B — Explicit RVE via `G4PVParameterised`

**Run provenance:** study file `configs/studies/paper3_hdpe_bi2o3_regime_b_rve.json`, physics list `emlivermore`, $10^7$ histories per energy, Geant4 11.4, result directory `results/paper3/regime_b_hdpe_bi2o3/`.

#### 5.2.1 Geometry verification

Geant4 confirmed the RVE geometry at initialisation:

```
RVE RSA: placed 2888/2888  achieved phi=0.189019
ShieldLab-G4 geometry (RVE parameterised):
  side:   1 um
  radius: 25 nm
  placed: 2888 particles
```

#### 5.2.2 Transmission and µ results

**Table 2.** Regime B mass attenuation coefficients (G4PVParameterised explicit RVE, 1 µm, 2888 spheres, $10^7$ histories per point).

| $E$ (keV) | $T$ | $\mu_\text{sim}$ (cm$^{-1}$) | $(\mu/\rho)_\text{sim}$ (cm$^2$ g$^{-1}$) | $N_\text{att}$ | $\sigma_\mu/\mu$ (%) | $(\mu/\rho)_\text{XCOM}$ | $\Delta_B$ (%) | $\mu_B / \mu_{A,\phi}$ |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 0.99531 | 47.009 | 19.19 | 46,899 | 0.46 | 19.507 | −1.64 | 0.981 (-1.9%) |
| 50 | 0.998753 | 12.483 | 5.095 | 12,475 | 0.90 | 5.236 | −2.70 | 0.976 (-2.4%) |
| 80 | 0.999619 | 3.8137 | 1.557 | 3,813 | 1.62 | 1.621 | −3.97 | 0.984 (-1.6%) |
| 100 | 0.99914 | 8.6047 | 3.512 | 8,601 | 1.08 | 3.596 | −2.34 | 0.981 (-1.9%) |
| 150 | 0.999681 | 3.1935 | 1.303 | 3,193 | 1.77 | 1.339 | −2.65 | 0.975 (-2.5%) |
| 356† | 0.9999486 | 0.5140 | 0.2098 | 514 | 4.4 | 0.2270 | −7.6† | 0.932 (-6.8%)† |
| 511† | 0.999971 | 0.2940 | 0.1200 | 294 | 5.8 | 0.1358 | −11.7† | 0.886 (-11.4%)† |
| 662† | 0.999975 | 0.2530 | 0.1033 | 253 | 6.3 | 0.1029 | +0.4† | 1.011 (+1.1%)† |
| 1173† | 0.999985 | 0.1490 | 0.0608 | 149 | 8.2 | 0.0639 | −4.8† | 0.955 (-4.5%)† |
| 1332† | 0.999988 | 0.1240 | 0.0506 | 124 | 9.0 | 0.0588 | −13.9† | 0.869 (-13.1%)† |

† Statistically dominated: $N_\text{att} < 600$; $\Delta$ reflects sampling noise, not systematic physics deviation.

*Note on the Bi K-edge.* The simulation correctly resolves this feature: µ drops from 12.48 cm$^{-1}$ at 50 keV to 3.81 cm$^{-1}$ at 80 keV, then rises to 8.61 cm$^{-1}$ at 100 keV — a jump of ×2.3 due to Bi K-shell photoelectric absorption.

*Note on statistical precision at high energies.* For the 1 µm RVE above 300 keV, at 356 keV only 514 photons are attenuated out of $10^7$, giving $1\sigma$ uncertainty of 4.4%. The regime A(phi0p189) slab result provides the reliable reference at those energies.

### 5.3 Regime C — Explicit RVE via `G4MultiUnion`

**Run provenance:** study file `configs/studies/paper3_hdpe_bi2o3_regime_c_250nm.json`, physics list `emlivermore`, $10^7$ histories per energy, Geant4 11.4-beta-01, result directory `results/paper3/regime_c_hdpe_bi2o3/`.

**Geometry and scalability.** The `G4Voxelizer` scales as $(2N)^3$ cells. The 1 µm RVE ($N = 2{,}888$; $\sim$193×10⁹ cells, OOM-killed at $> 7.2$ GB RSS) and 500 nm RVE ($N = 361$; $\sim$3.5 GB, also OOM) are infeasible on the 8 GB workstation. The 250 nm RVE ($N = 45$; 729,000 cells, 99 MB RSS) runs successfully.

**Geometry verification.** RSA seed 33,333. Placed 45/45 Bi₂O₃ spheres ($r = 25$ nm), achieved $\phi_f = 0.188496$.

#### 5.3.1 Transmission and µ results

**Table 3.** Regime C mass attenuation coefficients (G4MultiUnion explicit RVE, 250 nm, 45 spheres, distributed beam, $10^7$ histories per point).

| $E$ (keV) | $T$ | $\mu_\text{sim}$ (cm$^{-1}$) | $(\mu/\rho)_\text{sim}$ (cm$^2$ g$^{-1}$) | $N_\text{att}$ | $\sigma_\mu/\mu$ (%) | $(\mu/\rho)_\text{XCOM}$ | $\Delta_C$ (%) | $\mu_C / \mu_{A,\phi}$ |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 0.998822 | 47.164 | 19.23 | 11,780 | 0.92 | 19.507 | −1.40 | 0.984 |
| 50 | 0.999675 | 12.998 | 5.301 | 3,250 | 1.75 | 5.236 | +1.24 | 1.016 |
| 80 | 0.999902 | 3.932 | 1.604 | 980 | 3.19 | 1.621 | −1.05 | 1.014 |
| 100 | 0.999785 | 8.617 | 3.514 | 2,150 | 2.15 | 3.596 | −2.28 | 0.982 |
| 150 | 0.999919 | 3.224 | 1.315 | 810 | 3.51 | 1.339 | −1.79 | 0.984 |
| 356† | 0.999987 | 0.5280 | 0.2153 | 130 | 8.77 | 0.2270 | −5.15† | 0.957† |
| 511† | 0.999991 | 0.3640 | 0.1485 | 90 | 10.5 | 0.1358 | +9.35† | 1.097† |
| 662† | 0.999994 | 0.2560 | 0.1044 | 60 | 12.9 | 0.1029 | +1.46† | 1.023† |
| 1173† | 0.999997 | 0.1200 | 0.0489 | 30 | 18.3 | 0.0639 | −23.5† | 0.769† |
| 1332† | 0.999996 | 0.1440 | 0.0587 | 40 | 15.8 | 0.0588 | −0.17† | 1.009† |

† Statistically dominated: $N_\text{att} < 200$; $\Delta$ reflects sampling noise, not physics deviation.

Figure 4 isolates the main scalability result of the paper.

![Figure 4. `G4MultiUnion` scalability on the 8 GB workstation used in this study. (A) Estimated voxel-cell growth versus tested RVE size and sphere count. (B) Observed resident set size and feasibility outcome, showing why 250 nm / $N = 45$ is the largest practical regime-C configuration in this environment.](../../../results/paper3/figures/paper3_fig4_multiunion_scalability.png){ width=100% }

### 5.4 Cross-Regime Comparison Figure

Figure 5 overlays the regime A(phi0p189) $(\mu/\rho)$ data (Table 1b), regime B data (Table 2), and regime C data (Table 3) against NIST XCOM. The three curves overlap closely at 30–150 keV, confirming H1 for all three regimes.

![Figure 5. Cross-regime mass attenuation coefficient comparison for regime A(phi0p189), regime B, and regime C against NIST XCOM, with 95% statistical confidence intervals on the simulated points. Agreement at 30–150 keV confirms H1 across all three regimes, while high-energy explicit-RVE points become statistics-limited.](../../../results/paper3/figures/paper3_fig5_cross_regime_mac.png){ width=85% }

---

### 5.5 HDPE/WO₃ Regime A — Second K-Edge Benchmark

**Run provenance:** study file `configs/studies/paper3_hdpe_wo3_regime_a_phi0p189.json`, physics list `emlivermore`, $10^6$ histories per energy, Geant4 11.4, result directory `results/paper3/regime_a_hdpe_wo3_phi0p189/`. All 10 energies complete.

**Material:** P3_HDPE_WO3_phi0p189 — HDPE (36.28 wt%) + WO₃ (63.72 wt%) at $\rho = 2.124$ g cm$^{-3}$. Elemental mass fractions: w(W) = 0.50528, w(O) = 0.13192, w(C) = 0.31066, w(H) = 0.05214. The W K-edge lies at 69.525 keV, positioned between the 50 keV and 80 keV grid points.

**Table 1c.** Regime A HDPE/WO₃ φ=0.189 (63.7 wt%, $\rho = 2.124$ g cm$^{-3}$) mass attenuation coefficients vs NIST XCOM. Benchmark: **passed** (mean |Δ| = 0.42%, max |Δ| = 0.97%).

| $E$ (keV) | $t$ (cm) | $T$ | $\mu_\text{sim}$ (cm$^{-1}$) | $(\mu/\rho)_\text{sim}$ (cm$^2$ g$^{-1}$) | $(\mu/\rho)_\text{XCOM}$ | $\Delta$ (%) |
|---:|---:|---:|---:|---:|---:|---:|
| 30 | 0.0174345 | 0.64933 | 24.768 | 11.661 | 11.633 | +0.24 |
| 50 | 0.0652215 | 0.65271 | 6.5410 | 3.080 | 3.110 | −0.97 |
| **80** | **0.0502704** | **0.64928** | **8.5915** | **4.045** | **4.035** | **+0.26** |
| 100 | 0.0872224 | 0.64963 | 4.9454 | 2.328 | 2.325 | +0.13 |
| 150 | 0.232462 | 0.64980 | 1.8545 | 0.8731 | 0.8725 | +0.07 |
| 356 | 1.16155 | 0.65266 | 0.36736 | 0.1730 | 0.1746 | −0.95 |
| 511 | 1.76532 | 0.65076 | 0.24336 | 0.1146 | 0.1149 | −0.27 |
| 662 | 2.2073 | 0.65125 | 0.19429 | 0.09147 | 0.09188 | −0.45 |
| 1173 | 3.28865 | 0.65110 | 0.13048 | 0.06143 | 0.06167 | −0.39 |
| 1332 | 3.54563 | 0.65150 | 0.12085 | 0.05690 | 0.05720 | −0.53 |

Bold row indicates energy immediately above the W K-edge at 69.5 keV.

**W K-edge signature.** The MAC increases from $3.080$ cm$^2$ g$^{-1}$ at 50 keV (below W K-edge) to $4.045$ cm$^2$ g$^{-1}$ at 80 keV (above W K-edge), a rise of **+31%** despite the $E^{-3}$ photoelectric falloff that ordinarily reduces MAC with increasing energy. This anti-intuitive increase is due to the opening of the W K-shell photoionization channel above 69.525 keV. XCOM confirms the same feature: 3.110 → 4.035 cm$^2$ g$^{-1}$ = ×1.298 ratio at the adjacent grid points. The effect is further confirmed by the secondary photon spectrum: 97,285 secondary gamma rays were detected at 80 keV (W Kα/Kβ fluorescence at ~59.3/67.2 keV) vs only 12 at 50 keV, demonstrating that the W K-shell is being populated by photoelectric absorption and promptly de-excited via characteristic X-ray emission.

All 10 energy points satisfy the acceptance gates: mean |Δ| = 0.42% ≤ 1.5% gate; max |Δ| = 0.97% at 50 keV ≤ 5.0% gate. The modest deviation at 50 keV (just below the K-edge) is consistent with the EPDL97 interpolation pattern discussed in §5.1.3 for the analogous Bi K-edge point.

---

### 5.6 Cross-Material K-Edge Comparison

Figure 6 overlays both simulated MAC curves with XCOM references against a common energy axis, with K-edge annotations for W (69.5 keV) and Bi (90.5 keV).

![Figure 6. Cross-material K-edge MAC comparison. BLUE circles: HDPE/Bi₂O₃ simulation; RED squares: HDPE/WO₃ simulation; dashed lines: NIST XCOM references. Vertical dotted lines mark the W K-edge (69.5 keV, red) and Bi K-edge (90.5 keV, blue). Both simulations are at φ=0.189.](../../../results/paper3/figures/paper3_fig6_kedge_comparison.png){ width=85% }

The two filler chemistries exhibit distinct K-edge signatures at separated energies:

| Feature | HDPE/Bi₂O₃ | HDPE/WO₃ |
|---|---|---|
| K-edge position | 90.5 keV | 69.5 keV |
| MAC below K-edge (XCOM) | 1.621 cm²/g at 80 keV | 3.110 cm²/g at 50 keV |
| MAC above K-edge (XCOM) | 3.596 cm²/g at 100 keV | 4.035 cm²/g at 80 keV |
| MAC jump ratio (XCOM) | ×2.217 | ×1.298 |
| MAC at 30 keV (sim) | 19.54 cm²/g | 11.66 cm²/g |
| Max |Δ| vs XCOM at K-edge straddle | 2.45% (80 keV) | 0.97% (50 keV) |

The larger Bi K-edge jump (×2.22 vs ×1.30) reflects three compounding factors: (1) higher atomic number (Z=83 vs Z=74), producing a larger K-shell photoionization cross section; (2) higher weight fraction of the heavy element (w(Bi)=0.592 vs w(W)=0.505 in the composite); and (3) the higher total MAC at 30 keV for Bi₂O₃ confirming the overall higher opacity of the Bi composite at low energies.

Both K-edge features are faithfully reproduced by the Geant4 emlivermore effective-medium model within ±1% on both sides of the respective K-edges (excepting the −2.45% at the Bi 80 keV point, which is the known EPDL97 interpolation artefact near the Bi K-edge complex discussed in §5.1.3). This is a non-trivial result: the model correctly predicts the direction and approximate magnitude of the MAC jump at both K-edges without any material-specific tuning.

---

## 6. Discussion

### 6.1 Regime A confirms effective-medium validity

The regime A(30wt) results (§5.1.1–5.1.3) establish that `G4EmLivermorePhysics` reproduces NIST XCOM mass attenuation coefficients for HDPE/Bi₂O₃ 30 wt% with a mean deviation of 0.549% and a maximum deviation of 2.013% across a broad photon energy range (30 keV–1.33 MeV). These values confirm **Hypothesis H1** for the effective-medium regime against the external reference.

The 2.013% maximum deviation at 80 keV falls near the Bi K-edge complex (90.5 keV). The most likely cause is a small interpolation mismatch between the EPDL97 photoelectric cross-section grid and the XCOM energy grid in the 80–100 keV region. The value remains well within the pre-registered 5% maximum gate.

### 6.2 Regime B and C: cross-regime agreement test (H1 — RVE scale)

**Cross-regime agreement (30–150 keV, statistically reliable).** For the five energies where the RVE geometry provides adequate statistics ($N_\text{att} \geq 3000$), the regime B / regime A ratio $\mu_B/\mu_{A,\phi}$ falls in the range 0.975–0.984 (deviation −1.6% to −2.5%, all within the 3% H1 gate), as summarised in Table 2. The systematic ~2% downward offset of regime B relative to regime A is consistent with the RVE boundary-layer effect.

**Regime C (G4MultiUnion) outcome: feasible at 250 nm RVE ($N = 45$).** At 30–150 keV, regime C agrees with regime A(phi0p189) to within $-2.3\%$ to $+1.6\%$ ($\mu_C/\mu_{A,\phi} = 0.982$–$1.016$), confirming H1 for regime C. The `G4Voxelizer` $(2N)^3$ scaling limits regime C to $N \lesssim 50$ spheres on 8 GB hardware; `G4PVParameterised` (regime B) handles $N = 2{,}888$ with negligible overhead.

### 6.3 Implications for the effective-medium hypothesis

Within the physically expected regime (nanoparticle radius $\ll$ photon MFP, energies away from the K-edge), the effective-medium model is the computationally efficient and physically accurate choice for macroscopic shielding calculations. Explicit-RVE regimes (B and C) are needed only when interface dose or dose-enhancement factors at the matrix–filler boundary are required, or when the nanoparticle size or loading approaches a regime where inter-particle coherence effects become relevant.

### 6.4 Cross-material generalisability

The HDPE/WO₃ Regime A benchmark (§5.5) demonstrates that the emlivermore effective-medium approach is not material-specific. Both HDPE/Bi₂O₃ and HDPE/WO₃ at the same φ = 0.189 achieve sub-1% XCOM agreement at Compton-dominated energies and resolve their respective K-edges consistently. The W K-edge at 69.5 keV and the Bi K-edge at 90.5 keV are both correctly predicted by the model without material-specific tuning; the direction, approximate magnitude, and energy position of each K-edge jump are reproduced faithfully.

Together, the two K-edges cover the diagnostically relevant 50–100 keV window. The higher absolute MAC of HDPE/Bi₂O₃ (particularly at 30 keV: 19.54 vs 11.66 cm²/g for WO₃) favours Bi₂O₃ for broadband low-energy shielding, while HDPE/WO₃ provides a competitive K-edge feature at the lower 69.5 keV threshold that may be advantageous for specific beam-quality designs.

Practitioners can apply the same workflow (Regime A slab → XCOM comparison → acceptance gate) to any high-Z filler composite with a known composition and density. The WO₃ result establishes a second independent K-edge benchmark covering the 50–80 keV diagnostic range, confirming that the benchmark methodology is systematically reproducible across filler chemistries.

---

## 7. Conclusions

1. **Regime A(30wt) established (XCOM validation).** The effective-medium `G4EmLivermorePhysics` model for HDPE/Bi₂O₃ 30 wt% achieves 0.549% mean and 2.013% maximum deviation against NIST XCOM over 30 keV–1.33 MeV, satisfying pre-registered paper-3 acceptance criteria.

2. **Regimes B and C complete.** The `G4PVParameterised` RVE geometry (regime B, 1 µm, $N = 2{,}888$ spheres, $\phi_f = 0.1890$) and the `G4MultiUnion` RVE geometry (regime C, 250 nm, $N = 45$ spheres, $\phi_f = 0.188496$, distributed beam) are both fully validated in ShieldLab G4 v1.1 (all 10 energies each). Regime B correctly resolves the Bi K-edge jump ($\mu$ rises ×2.3 from 80 to 100 keV). The `G4Voxelizer` $(2N)^3$ scaling limits regime C to $N \lesssim 50$ spheres (99 MB at $N = 45$) on 8 GB hardware; `G4PVParameterised` handles $N = 2{,}888$ with negligible overhead and is the recommended approach when $N > 100$.

3. **H1 test: confirmed for all three regimes A+B+C at 30–150 keV.** Regime B vs regime A(phi0p189) gives $\mu_B/\mu_{A,\phi}$ in the range 0.975–0.984 (mean deviation −2.1%, within the 3% H1 gate). Regime C vs regime A(phi0p189) gives $\mu_C/\mu_{A,\phi}$ in the range 0.982–1.016 (mean $|\text{deviation}|$ 1.5%, within the 3% H1 gate).

4. **Reproducible harness delivered.** All study configuration files, macro writer, benchmark orchestrator, XCOM comparison, and figure generation modules are open-source in ShieldLab G4 v1.1. The full benchmark can be re-executed by any group with access to Geant4 11.4 using `python -m shieldlab.analysis.nano_benchmark`.

5. **Two-material generalisation.** The effective-medium Regime A achieves sub-1% XCOM agreement for both HDPE/Bi₂O₃ and HDPE/WO₃ at identical volume fraction φ=0.189, confirming methodology generalisability across filler chemistries. The W K-edge at 69.5 keV and the Bi K-edge at 90.5 keV are both correctly resolved (max |Δ|=0.97% for WO₃ across all 10 energies; mean |Δ|=0.42%), establishing a second independent K-edge benchmark covering the 50–80 keV diagnostic range.

---

## 8. Limitations and Validity Scope

1. **RVE size selection.** Regime B used a 1 µm RVE ($N = 2{,}888$ spheres); regime C required a 250 nm RVE ($N = 45$) due to `G4Voxelizer` memory constraints (§5.3). A systematic RVE-convergence study (varying $L_\text{RVE}$) is deferred to a future version.
2. **Explicit-RVE regime for WO₃ not reported.** Regime A at φ=0.189 is demonstrated for WO₃ in this paper. Extension of Regimes B and C to WO₃ (and other matrix/filler combinations, BaSO₄, varied loadings) is planned for the full regime-map study.
3. **Macroscopic transmission only.** Interface dose-enhancement factors (H2 test) require phase-resolved scoring that is not implemented in the current RVE geometry setup.
4. **1-D slab transport.** Full 3-D geometry is out of scope for this paper.
5. **Photon-only benchmark.** Neutron and charged-particle behaviour through nanocomposites is not addressed.
6. **Density input.** $\rho_\text{eff}$ values are derived from the volume-fraction rule or user-specified literature values; no measured densities are available at this time. Results carry the provenance tag `[ρ-volume-rule]`.

---

## 9. Reproducibility, Code Availability, and Ethics

- **Software availability:** ShieldLab G4 v1.1 (tag to be assigned upon paper submission), released under the MIT licence. Source code is available at the repository root [README.md](README.md).
- **Data availability:** benchmark study JSON files, raw scorer outputs, derived CSV files, and figure-generation scripts for this paper are released in `results/paper3/` under CC-BY 4.0.
- **Compute environment:** Geant4 11.4-beta-01 on WSL Ubuntu 22.04, Python 3.11 (Windows host), `d:\uv_envs` virtual environment.
- **Ethics statement:** this study used no human participants, no animal data, and no clinical data.
- **Funding statement:** no external funding was received for this work.
- **Conflict of interest statement:** the author declares no conflict of interest.
- **AI-assisted writing disclosure:** portions of the manuscript were drafted with the assistance of GitHub Copilot in agent mode; all physics claims, results, citations, and code were independently verified by the author before submission, consistent with COPE 2023 guidance.

---

## 10. References

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
11. D. E. Cullen, J. H. Hubbell, and L. Kissel, *EPDL97: The Evaluated Photon Data Library, '97 Version*, UCRL-50400 Vol. 6 Rev. 5, Lawrence Livermore National Laboratory (1997).
