# Controlled Geant4 Benchmarking of Nanocomposite Radiation Shielding Across Effective-Medium and Explicit-RVE Regimes for Six K-Edge Filler Chemistries

**Hani H. Negm**¹

¹ *Hani Negm, Department of Physics, College of Science, Jouf University*

**Corresponding author:** <hhnegm@ju.edu.sa>

**Manuscript version:** v09 (derived from v08 on 2026-05-19; all six K-edge filler chemistries benchmarked across all three regimes)

**Target journals (Q1, in priority order):**

1. *Radiation Physics and Chemistry* (Elsevier, IF ≈ 2.9; primary scope match — shielding + MC methodology)
2. *Nuclear Instruments and Methods in Physics Research A* (NIM A, Elsevier; established Geant4 methods venue)
3. *Computer Physics Communications* (Elsevier; physics + software methodology)
4. *Physics in Medicine and Biology* (IOP; if diagnostic-energy nano-dose results are emphasised)
5. *Annals of Nuclear Energy* (Elsevier; if shielding-engineering framing is emphasised)

---

## Abstract

Nanoparticle-filled shielding polymers are commonly simulated in Geant4 as homogeneous mixtures, even when experiments describe them as nanocomposites. The validity boundary of that homogenised representation relative to explicit nanoparticle geometry remains poorly quantified for shielding photon transport, especially near high-Z K-edges. This work presents a controlled, reproducible Geant4 benchmark across six K-edge filler chemistries and three geometric modelling regimes.

The tested materials are HDPE/Bi₂O₃, HDPE/WO₃, HDPE/BaWO₄, HDPE/Gd₂O₃, HDPE/PbWO₄ at filler volume fraction φ=0.189, and an HDPE/Bi₂O₃/WO₃ ternary at φ(Bi₂O₃)=0.10 and φ(WO₃)=0.10. Regime A represents each material as a homogeneous effective-medium `G4Material`; Regime B resolves 25 nm filler spheres in a 1 µm representative volume element (RVE) using `G4PVParameterised`; Regime C resolves a 250 nm RVE using `G4MultiUnion`. All simulations use Geant4 11.4-beta-01, `G4EmLivermorePhysics`, and a photon energy grid from 30 keV to 1.332 MeV. The primary endpoint is the mass attenuation coefficient, μ/ρ(E), benchmarked against NIST XCOM for Regime A and against the matched Regime-A baseline for explicit-RVE regimes.

All six Regime-A effective-medium benchmarks satisfy the pre-registered XCOM acceptance criteria. Mean absolute percent differences are 0.339–0.793%, and maximum absolute differences are 0.967–2.933%, with the largest deviation occurring for Gd₂O₃ at 50 keV where the Gd K-edge (50.239 keV) straddles the grid point. For the five single-explicit-filler binary materials, Regime B agrees with the matched Regime-A baseline at 30–150 keV within the ±3% H1 gate: Bi₂O₃ (0.975–0.984), WO₃ (0.988–1.022), BaWO₄ (0.992–1.010), Gd₂O₃ (0.999–1.012), and PbWO₄ (0.976–1.010). Regime C confirms the same trend for Bi₂O₃ and WO₃, while 250 nm finite-RVE and low-count fluctuations produce isolated >3% deviations for BaWO₄, Gd₂O₃, and PbWO₄. The ternary explicit-RVE runs are reported as a negative-control validity test: although the Regime-A ternary mixture passes XCOM with mean |Δ|=0.498%, the explicit-RVE implementation spatialises only Bi₂O₃ spheres and is not composition-equivalent to the full Bi₂O₃+WO₃ effective medium, yielding B/A and C/A ratios far below unity.

The results support effective-medium modelling for macroscopic photon shielding when μr ≪ 1, provided composition and density are represented consistently. `G4PVParameterised` is the most scalable explicit-RVE validation path for nanoparticle counts above O(100), while `G4MultiUnion` is useful only for small-RVE checks on workstation-class hardware. The benchmark also demonstrates that K-edge behaviour is reproduced without material-specific tuning across Bi, W, Ba/W, Gd, and Pb/W absorber systems.

**Keywords:** Geant4 · radiation shielding · nanocomposite · effective medium · `G4MultiUnion` · `G4PVParameterised` · representative volume element · mass attenuation coefficient · K-edge · Bi₂O₃ · WO₃ · BaWO₄ · Gd₂O₃ · PbWO₄

---

## 1. Introduction

### 1.1 Background

Polymer-matrix radiation-shielding composites loaded with high-Z fillers have become a sustained research focus, driven by the need for lead-free, flexible, and manufacturable alternatives in medical X-ray protection, nuclear medicine, industrial radiography, and aerospace shielding. Common filler chemistries include Bi₂O₃, WO₃, BaSO₄/BaWO₄, Gd₂O₃, PbO/PbWO₄, and related dense oxides. Many experimental papers describe these systems as nanocomposites because the filler particles are prepared or dispersed at sub-micron or nanometre length scales.

In Monte Carlo photon-transport calculations, however, these materials are usually implemented as homogeneous mixtures: elemental mass fractions are supplied to a single material definition, a bulk density is assigned, and the microscopic spatial distribution of filler particles is ignored. This modelling choice is often physically justified for macroscopic transmission because diagnostic and gamma-ray photon mean free paths are typically orders of magnitude larger than a 25–100 nm filler particle. Under that condition, photon attenuation is governed by mass-fraction additivity and the independent-atom approximation, not by the exact particle coordinates.

The difficulty is not the existence of the effective-medium rule itself. The difficulty is knowing when a shielding simulation that calls a material a nanocomposite should remain homogeneous and when explicit nanoparticle geometry is needed. The answer depends on the observable. Macroscopic transmitted fluence may be insensitive to nanoscale geometry, while phase-resolved interface dose, local energy deposition, or dose-enhancement factors may not be.

### 1.2 Gap

Three gaps motivate this work:

1. **Cross-regime validity boundary.** There is no widely available Geant4 benchmark that holds composition, density, source definition, scoring, and physics list constant while varying only the geometric representation: homogeneous material, parameterised explicit RVE, and multi-union explicit RVE.
2. **Material generalisability.** Prior validation is often tied to one filler. A robust shielding workflow should reproduce K-edge behaviour across chemically distinct absorbers, including Bi, W, Ba/W, Gd, and Pb/W systems.
3. **Computational feasibility.** Geant4 provides both `G4PVParameterised` and `G4MultiUnion`, but their practical scaling for shielding-relevant nanoparticle counts is rarely quantified in a way that helps users choose the correct geometry strategy.

### 1.3 Contribution and hypotheses

This paper contributes a controlled benchmark campaign for six K-edge filler chemistries across three modelling regimes. The core scientific question is whether macroscopic attenuation through a nanocomposite at fixed composition is changed by resolving the particles explicitly.

**Hypothesis H1.** For photon energies where the photon mean free path greatly exceeds the nanoparticle radius (μr ≪ 1), transmitted fluence and μ/ρ through the same composition are independent of the choice of Regime A, B, or C within the statistical uncertainty of 10⁶–10⁷-history Geant4 runs, provided composition, density, and scoring are matched.

**Hypothesis H2.** For photon energies E ≲ 100 keV with high-Z fillers, phase-resolved radial dose-enhancement profiles around individual particles may carry spatial structure that an effective-medium material cannot reproduce.

Only H1 is tested quantitatively in this manuscript. H2 requires phase-resolved local scoring and is treated as future work.

The novelty is methodological rather than kernel-level. `G4PVParameterised`, `G4MultiUnion`, and `G4EmLivermorePhysics` are standard Geant4 components; the contribution here is the controlled, reproducible, material-resolved shielding benchmark built from those components.

---

## 2. Theoretical Basis

### 2.1 Effective-medium attenuation

For photon attenuation under the independent-atom approximation, the mass attenuation coefficient of a mixture is

$$
\left(\frac{\mu}{\rho}\right)_\text{mix}(E) = \sum_i w_i \left(\frac{\mu}{\rho}\right)_i(E),
$$

where $w_i$ is the elemental or compound mass fraction. This relation is exact for the tabulated mixture rule used by XCOM, subject to the underlying independent-atom approximation. In Geant4, the same physical expectation should hold when the material is represented by a homogeneous `G4Material` with correct elemental fractions and density.

The spatial distribution of atoms becomes relevant when the heterogeneity length scale approaches the photon mean free path or when the scored observable depends on local phase boundaries rather than bulk transmission. For the present 25 nm particles and photon energies ≥30 keV, the condition μr ≪ 1 is expected to hold for macroscopic transmission.

### 2.2 Effective density and mass fractions

All material densities are derived from a volume-fraction rule unless otherwise noted:

$$
\rho_\text{eff} = \sum_j \phi_j \rho_j.
$$

The corresponding mass fraction of phase $j$ is

$$
w_j = \frac{\phi_j \rho_j}{\rho_\text{eff}}.
$$

This paper uses HDPE density 0.95 g cm⁻³. The binary φ=0.189 cases differ in filler density and therefore in effective density and filler weight fraction. The ternary case uses φ(Bi₂O₃)=0.10 and φ(WO₃)=0.10.

### 2.3 Representative volume elements

A cubic RVE is used for explicit nanoparticle simulations. For a random dispersion of monodisperse spheres of radius $r$ at volume fraction $\phi_f$, the nominal number of particles in an RVE of side $L$ is

$$
N \approx \frac{\phi_f L^3}{(4/3)\pi r^3}.
$$

For $r=25$ nm, $L=1$ µm, and $\phi_f=0.189$, this gives approximately 2,888 spheres. This count is tractable with parameterised placement but not with `G4MultiUnion` on the 8 GB workstation used here. A reduced $L=250$ nm RVE contains approximately 45 spheres for φ=0.189 and approximately 24 spheres for φ=0.10.

---

## 3. Geant4 Modelling Regimes

### 3.1 Regime A — homogeneous effective medium

Regime A defines each composite as a single `G4Material` using elemental mass fractions and an assigned density. Slab thickness is selected per energy to keep transmission near $T \approx 0.65$, which stabilises the direct estimator

$$
\hat\mu = -\frac{\ln T}{t}.
$$

Regime A is the production model for bulk shielding calculations and is directly benchmarked against NIST XCOM.

### 3.2 Regime B — explicit RVE with `G4PVParameterised`

Regime B resolves 25 nm filler spheres using `G4PVParameterised`. Particle centres are generated by random sequential addition with hard-sphere exclusion. The principal binary studies use a 1 µm RVE and 2,888 spheres at φ=0.189. The ternary explicit-RVE studies use 1,528 Bi₂O₃ spheres at φ=0.10.

This regime is the main explicit-geometry validation path because repeated sphere placement remains scalable at O(10³) particle counts.

### 3.3 Regime C — explicit RVE with `G4MultiUnion`

Regime C builds the explicit particles into a single `G4MultiUnion` and calls `Voxelize()`. This provides a useful independent geometry path, but memory use grows rapidly with sphere count. On the present workstation, 1 µm and 500 nm multi-union RVEs were infeasible; the adopted configuration is a 250 nm RVE with 45 spheres for φ=0.189 binary cases and 24 Bi₂O₃ nodes for the ternary φ=0.10 explicit case.

### 3.4 Ternary explicit-RVE interpretation

The ternary Regime-A material is a true HDPE/Bi₂O₃/WO₃ effective medium. The Regime-B and Regime-C ternary geometries spatialise Bi₂O₃ spheres only. Because the explicit geometry does not independently resolve the WO₃ phase as a matched spatial component, the ternary B/A and C/A ratios are not interpreted as a valid H1 pass/fail test for a fully composition-equivalent ternary RVE. They are retained as a stress test showing that composition equivalence is mandatory when comparing effective-medium and explicit-particle representations.

---

## 4. Benchmark Protocol

### 4.1 Materials

**Table M1.** Material design summary for the v09 six-chemistry benchmark.

| Material | Volume fraction | $\rho_\text{eff}$ (g cm$^{-3}$) | Heavy phase wt% | Principal K-edge(s) | Regimes completed |
| --- | ---: | ---: | ---: | --- | --- |
| HDPE/Bi₂O₃ | φ=0.189 | 2.452 | 68.6% Bi₂O₃ | Bi K = 90.526 keV | A+B+C |
| HDPE/WO₃ | φ=0.189 | 2.124 | 63.72% WO₃ | W K = 69.525 keV | A+B+C |
| HDPE/BaWO₄ | φ=0.189 | 1.927 | 60.02% BaWO₄ | Ba K = 37.441 keV; W K = 69.525 keV | A+B+C |
| HDPE/Bi₂O₃/WO₃ | φ(Bi₂O₃)=0.10; φ(WO₃)=0.10 | 2.366 | 37.62% Bi₂O₃; 30.26% WO₃ | W K = 69.525 keV; Bi K = 90.526 keV | A+B+C* |
| HDPE/Gd₂O₃ | φ=0.189 | 2.107 | 63.42% Gd₂O₃ | Gd K = 50.239 keV | A+B+C |
| HDPE/PbWO₄ | φ=0.189 | 2.369 | 67.49% PbWO₄ | W K = 69.525 keV; Pb K = 88.005 keV | A+B+C |

*The ternary explicit-RVE cases resolve Bi₂O₃ spheres only and are treated as a hybrid stress test rather than a composition-equivalent H1 validation.

A separate HDPE/Bi₂O₃ 30 wt% Regime-A validation study from v08 is retained as an independent emlivermore/XCOM calibration case. It is not used as the cross-regime baseline.

### 4.2 Source and energy grid

All runs use mono-energetic photons at 30, 50, 80, 100, 150, 356, 511, 662, 1173, and 1332 keV. The source direction is normal to the slab or RVE. Regime C uses distributed transverse sampling over the 250 nm RVE face to average over the small explicit geometry.

### 4.3 Physics list and software

All runs use `G4EmLivermorePhysics` in Geant4 11.4-beta-01. The Windows host runs Python 3.11 from `d:\uv_envs`; Geant4 execution is performed through WSL Ubuntu 22.04. The benchmark orchestrator is `python -m shieldlab.analysis.nano_benchmark`.

### 4.4 Histories

| Regime | Geometry | Histories per energy | Purpose |
| --- | --- | ---: | --- |
| A | Homogeneous slab | $10^6$ | XCOM validation and reference baseline |
| B | 1 µm parameterised RVE | $10^7$ | Explicit-particle H1 test |
| C | 250 nm multi-union RVE | $10^7$ | Independent explicit-geometry feasibility check |

### 4.5 Acceptance criteria

| Criterion | Metric | Gate |
| --- | --- | ---: |
| Regime A vs XCOM | mean abs. $\Delta(\mu/\rho)$ over 10 energies | ≤1.5% |
| Regime A vs XCOM | max abs. $\Delta(\mu/\rho)$ over 10 energies | ≤5.0% |
| H1 cross-regime | abs. $(\mu_B/\mu_A - 1)$ at 30–150 keV | ≤3% |
| Regime C feasibility | Reported against A with finite-RVE and count caveats | descriptive |

The strict H1 gate is applied to Regime B for composition-equivalent binary materials. Regime C is reported separately because the adopted 250 nm RVE contains only 45 particles at φ=0.189 and therefore includes larger finite-RVE fluctuations.

---

## 5. Results

### 5.1 Regime A XCOM validation across six chemistries

All six Regime-A materials pass the XCOM acceptance gates. The largest deviation is observed for Gd₂O₃ at 50 keV, immediately below the Gd K-edge at 50.239 keV, where small interpolation differences between EPDL97 and XCOM are expected to be amplified.

![Figure 1. Six-material Regime-A validation against NIST XCOM. Panels A-F show HDPE/Bi₂O₃, HDPE/WO₃, HDPE/BaWO₄, HDPE/Bi₂O₃/WO₃, HDPE/Gd₂O₃, and HDPE/PbWO₄, respectively. Symbols are Geant4 `G4EmLivermorePhysics` effective-medium results with 95% statistical intervals; dashed black curves are NIST XCOM references. Dotted vertical lines mark the material-specific K-edges.](../../../results/paper3/figures/v09/paper3_v09_fig1_six_material_xcom_validation.png){ width=100% }

**Table 1.** Regime-A XCOM acceptance summary.

| Material | Mean abs. Δ (%) | Max abs. Δ (%) | Max-deviation energy | Acceptance |
| --- | ---: | ---: | ---: | --- |
| HDPE/Bi₂O₃ | 0.723 | 2.450 | 80 keV | Pass |
| HDPE/WO₃ | 0.426 | 0.967 | 50 keV | Pass |
| HDPE/BaWO₄ | 0.339 | 1.011 | 356 keV | Pass |
| HDPE/Bi₂O₃/WO₃ | 0.498 | 0.987 | 356 keV | Pass |
| HDPE/Gd₂O₃ | 0.793 | 2.933 | 50 keV | Pass |
| HDPE/PbWO₄ | 0.511 | 1.012 | 356 keV | Pass |

**Table 2.** Regime-A simulated mass attenuation coefficients, $(\mu/\rho)_\text{sim}$, in cm$^2$ g$^{-1}$.

| E (keV) | Bi₂O₃ | WO₃ | BaWO₄ | Bi₂O₃/WO₃ | Gd₂O₃ | PbWO₄ |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30 | 19.542 | 11.661 | 8.730 | 16.247 | 8.251 | 15.629 |
| 50 | 5.218 | 3.080 | 4.754 | 4.322 | 2.152 | 4.165 |
| 80 | 1.581 | 4.045 | 3.183 | 2.781 | 3.135 | 2.928 |
| 100 | 3.578 | 2.328 | 1.827 | 3.057 | 1.786 | 2.979 |
| 150 | 1.336 | 0.873 | 0.697 | 1.144 | 0.679 | 1.115 |
| 356 | 0.225 | 0.173 | 0.154 | 0.203 | 0.149 | 0.199 |
| 511 | 0.135 | 0.115 | 0.107 | 0.127 | 0.104 | 0.124 |
| 662 | 0.102 | 0.091 | 0.087 | 0.097 | 0.086 | 0.096 |
| 1173 | 0.064 | 0.061 | 0.060 | 0.062 | 0.059 | 0.062 |
| 1332 | 0.058 | 0.057 | 0.056 | 0.058 | 0.055 | 0.057 |

The K-edge signatures are visible directly in Table 2. WO₃ rises from 3.080 cm² g⁻¹ at 50 keV to 4.045 cm² g⁻¹ at 80 keV after the W K-shell opens. Gd₂O₃ rises from 2.152 to 3.135 cm² g⁻¹ across the 50–80 keV interval after the Gd K-edge. PbWO₄ rises from 2.928 to 2.979 cm² g⁻¹ between 80 and 100 keV, consistent with the Pb K-edge at 88.005 keV. The ternary mixture also rises from 2.781 to 3.057 cm² g⁻¹ between 80 and 100 keV, showing the Bi K-edge contribution superposed on the W-containing baseline.

![Figure 2. K-edge attenuation landscape and XCOM residual map. Panel A overlays the six Regime-A attenuation curves on a common log-energy axis; the grey band marks the 30–150 keV H1 window and dotted vertical guides identify the Ba, Gd, W, Pb, and Bi K-edges. Panel B reports the per-energy percent difference between Geant4 and NIST XCOM for every material. The largest edge-adjacent residual is the Gd₂O₃ point at 50 keV, immediately below the 50.239 keV Gd K-edge.](../../../results/paper3/figures/v09/paper3_v09_fig2_kedge_landscape_delta_heatmap.png){ width=100% }

### 5.2 Regime B explicit-RVE comparison

For composition-equivalent binary systems, the 1 µm `G4PVParameterised` RVE reproduces the Regime-A baseline at 30–150 keV within the ±3% H1 gate. This is the strongest cross-regime result because Regime B has the largest explicit RVE and the best particle-count statistics.

**Table 3.** Regime-B / Regime-A ratios at 30–150 keV.

| Material | 30 keV | 50 keV | 80 keV | 100 keV | 150 keV | Range | Mean abs. ratio deviation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HDPE/Bi₂O₃ | 0.982 | 0.976 | 0.984 | 0.982 | 0.975 | 0.975–0.984 | 2.00% |
| HDPE/WO₃ | 1.000 | 0.997 | 0.988 | 1.022 | 0.997 | 0.988–1.022 | 0.82% |
| HDPE/BaWO₄ | 0.996 | 1.010 | 0.992 | 1.007 | 1.002 | 0.992–1.010 | 0.63% |
| HDPE/Gd₂O₃ | 1.007 | 0.999 | 1.007 | 1.000 | 1.012 | 0.999–1.012 | 0.54% |
| HDPE/PbWO₄ | 0.992 | 0.983 | 0.976 | 0.997 | 1.010 | 0.976–1.010 | 1.22% |
| HDPE/Bi₂O₃/WO₃* | 0.663 | 0.679 | 0.325 | 0.670 | 0.664 | 0.325–0.679 | 39.99% |

*Ternary explicit-RVE ratios are not composition-equivalent to the full ternary Regime-A material and are not counted as an H1 validation pass/fail.

The binary results support H1 for macroscopic attenuation: explicitly resolving 25 nm particles does not change μ/ρ once composition and density are matched. The Bi₂O₃ case carries a small systematic downward offset of about 2%, consistent with the v08 result and RVE boundary-layer/statistical effects. The WO₃, BaWO₄, Gd₂O₃, and PbWO₄ cases show sub-1.3% mean absolute ratio deviation over 30–150 keV.

### 5.3 Regime C multi-union comparison

Regime C provides an independent explicit-geometry implementation, but the feasible RVE is much smaller. The 250 nm RVE gives useful confirmation for Bi₂O₃ and WO₃, while finite-RVE fluctuations become more visible for BaWO₄, Gd₂O₃, and PbWO₄.

**Table 4.** Regime-C / Regime-A ratios at 30–150 keV.

| Material | 30 keV | 50 keV | 80 keV | 100 keV | 150 keV | Range | Mean abs. ratio deviation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HDPE/Bi₂O₃ | 0.984 | 1.016 | 1.014 | 0.982 | 0.984 | 0.982–1.016 | 1.59% |
| HDPE/WO₃ | 0.986 | 0.986 | 1.008 | 0.986 | 1.027 | 0.986–1.027 | 1.53% |
| HDPE/BaWO₄ | 0.992 | 0.955 | 1.001 | 1.005 | 0.926 | 0.926–1.005 | 2.66% |
| HDPE/Gd₂O₃ | 0.993 | 0.969 | 1.009 | 1.062 | 0.967 | 0.967–1.062 | 2.84% |
| HDPE/PbWO₄ | 0.996 | 1.012 | 1.056 | 0.979 | 0.982 | 0.979–1.056 | 2.22% |
| HDPE/Bi₂O₃/WO₃* | 0.658 | 0.680 | 0.331 | 0.634 | 0.656 | 0.331–0.680 | 40.82% |

The multi-union results preserve the qualitative K-edge structure but are more sensitive to small-number RVE sampling. At high energies above 300 keV, the number of attenuated photons falls to O(10–100) in the 250 nm geometry, so the apparent μ/ρ deviations are dominated by counting statistics and are not interpreted as physics disagreement.

![Figure 3. Cross-regime H1 ratio heatmaps at 30–150 keV. Panel A shows Regime B / Regime A ratios for the 1 µm `G4PVParameterised` RVE. Panel B shows Regime C / Regime A ratios for the 250 nm `G4MultiUnion` RVE. The ternary row is boxed and marked as a hybrid non-H1-equivalent stress test because only Bi₂O₃ is spatialised in the explicit geometry.](../../../results/paper3/figures/v09/paper3_v09_fig3_cross_regime_ratio_heatmaps.png){ width=100% }

![Figure 4. Explicit-RVE attenuation curves against the matched Regime-A baseline. Black curves are Regime A; blue triangles are Regime B; orange squares are Regime C. The five binary systems show close agreement in the 30–150 keV H1 window, while high-energy explicit-RVE points broaden because the attenuated counts are small. The ternary panel is shaded to indicate the hybrid explicit geometry.](../../../results/paper3/figures/v09/paper3_v09_fig4_explicit_rve_agreement.png){ width=100% }

### 5.4 Material-specific K-edge findings

**HDPE/Bi₂O₃.** The Bi K-edge at 90.526 keV is captured by the rise from 1.581 cm² g⁻¹ at 80 keV to 3.578 cm² g⁻¹ at 100 keV in Regime A. Regime B resolves the same trend, with μ/ρ increasing from 1.557 to 3.512 cm² g⁻¹.

**HDPE/WO₃.** The W K-edge at 69.525 keV produces the anti-intuitive increase from 3.080 cm² g⁻¹ at 50 keV to 4.045 cm² g⁻¹ at 80 keV, despite the normal $E^{-3}$ photoelectric falloff. Regime B and C preserve this feature.

**HDPE/BaWO₄.** BaWO₄ combines a Ba K-edge at 37.441 keV and a W K-edge at 69.525 keV. The 30–50 keV interval crosses the Ba K-edge but remains dominated by the large low-energy photoelectric decrease. The 50–80 keV interval crosses the W K-edge, partially offsetting the expected falloff.

**HDPE/Bi₂O₃/WO₃ ternary.** The Regime-A ternary mixture passes XCOM and shows additive dual-edge behaviour: the W-containing composition shapes the 50–80 keV interval, and the Bi K-edge produces a 9.9% μ/ρ increase from 80 to 100 keV. The explicit-RVE ternary implementation does not reproduce the full ternary attenuation because it spatialises only Bi₂O₃, making it a useful cautionary case rather than a validated H1 result.

**HDPE/Gd₂O₃.** The Gd K-edge lies at 50.239 keV, almost coincident with the 50 keV grid point. The 2.933% maximum XCOM deviation at 50 keV is therefore physically unsurprising and remains within the 5% gate. The K-edge opening is confirmed by the 45.7% μ/ρ increase from 50 to 80 keV.

**HDPE/PbWO₄.** PbWO₄ combines the W K-edge at 69.525 keV and Pb K-edge at 88.005 keV. The Pb K-edge is visible as a modest rise from 2.928 cm² g⁻¹ at 80 keV to 2.979 cm² g⁻¹ at 100 keV. Regime B preserves the same direction, with 2.857 to 2.970 cm² g⁻¹.

### 5.5 Legacy 30 wt% Bi₂O₃ validation

The v08 30 wt% HDPE/Bi₂O₃ Regime-A validation case is retained as a separate calibration run. It achieved mean |Δ|=0.549% and max |Δ|=2.013% against XCOM over 30 keV–1.332 MeV. Because its supplied density is not the volume-rule density for 30 wt% Bi₂O₃, it is not used in the cross-regime H1 comparisons.

---

## 6. Discussion

### 6.1 Effective-medium validity is material-general

The most important result is that all six effective-medium materials pass the NIST XCOM gate with mean deviations below 0.8% and maximum deviations below 3%. This includes single-edge materials (Bi₂O₃, WO₃, Gd₂O₃), dual-edge tungstates (BaWO₄ and PbWO₄), and the Bi₂O₃/WO₃ ternary mixture. The result supports the use of homogeneous `G4Material` definitions for macroscopic transmission calculations when the user supplies correct composition and density.

### 6.2 Regime B confirms H1 for composition-equivalent binary RVEs

For the five binary systems with matched explicit filler phase and effective-medium baseline, Regime B agrees with Regime A to within ±3% at every 30–150 keV point. This covers K-edge regions for W, Gd, Bi, and Pb. The conclusion is therefore stronger than a single-material benchmark: the explicit location of 25 nm particles does not alter bulk attenuation at diagnostic energies when μr ≪ 1.

The practical implication is that users should not pay the cost of explicit nanoparticle geometry for ordinary shielding transmission unless they need a local observable. Regime A is the correct production model for dose or transmission through bulk nanocomposite slabs.

### 6.3 Regime C is a feasibility check, not the preferred validation path

`G4MultiUnion` provides an independent explicit-geometry construction, but the voxelizer limits usable particle counts on workstation-class hardware. The 250 nm RVE confirms the overall trend but introduces finite-RVE noise. This is visible in the BaWO₄, Gd₂O₃, and PbWO₄ C/A ratios, where individual 30–150 keV points exceed ±3% despite Regime B passing cleanly.

For ShieldLab G4 and similar workflows, `G4PVParameterised` should be used for explicit-RVE validation whenever the particle count exceeds O(100). `G4MultiUnion` remains useful for small-cell geometry sanity checks and for visual/structural validation.

### 6.4 The ternary case defines an important validity condition

The ternary result is scientifically valuable precisely because it prevents an overbroad conclusion. Regime A correctly represents HDPE/Bi₂O₃/WO₃ as a full effective medium and passes XCOM. The explicit-RVE ternary cases, however, spatialise only Bi₂O₃ spheres and therefore do not reproduce the full ternary material response. The B/A and C/A ratios are far below unity, especially at 80 keV where the missing W contribution is most consequential.

This establishes a strict requirement for future multi-filler explicit RVEs: every high-Z phase that contributes materially to μ/ρ must be represented in a composition-equivalent way. A hybrid geometry may be useful for algorithm development, but it must not be interpreted as a validation of a full ternary material unless the missing phase is accounted for consistently.

### 6.5 K-edge physics is captured without tuning

The simulations reproduce multiple K-edge signatures without material-specific tuning: W at 69.5 keV, Gd at 50.2 keV, Bi at 90.5 keV, Ba at 37.4 keV, and Pb at 88.0 keV. The largest XCOM deviations occur at grid points adjacent to K-edges, consistent with known differences between tabulated photoelectric datasets and interpolation schemes. Away from these edge-adjacent points, agreement is typically sub-percent.

---

## 7. Conclusions

1. **All six Regime-A effective-medium benchmarks pass XCOM.** Mean absolute deviations are 0.339–0.793%, and maximum deviations are 0.967–2.933%, satisfying the pre-registered ≤1.5% mean and ≤5% maximum gates.

2. **Regime B confirms H1 for five composition-equivalent binary nanocomposites.** HDPE/Bi₂O₃, HDPE/WO₃, HDPE/BaWO₄, HDPE/Gd₂O₃, and HDPE/PbWO₄ all agree with their matched Regime-A baselines within ±3% at 30–150 keV.

3. **Regime C is feasible only as a small-RVE check on the present hardware.** The 250 nm `G4MultiUnion` cases reproduce the broad material trends, but finite-RVE and counting fluctuations produce larger pointwise deviations than the 1 µm parameterised RVE.

4. **The ternary explicit-RVE result is a negative-control lesson.** A full ternary effective medium can pass XCOM, but an explicit RVE that spatialises only one filler phase is not composition-equivalent and must not be used to claim cross-regime validation of the full ternary material.

5. **Recommended workflow.** Use Regime A for production macroscopic shielding calculations; use Regime B when explicit-particle validation or phase-aware scoring is required; reserve Regime C for small-RVE feasibility checks. For multi-filler systems, enforce composition equivalence before making H1 claims.

---

## 8. Limitations and Validity Scope

1. **Macroscopic transmission only.** This manuscript evaluates transmitted fluence and μ/ρ. Interface dose-enhancement factors and radial dose profiles require phase-resolved scoring and are deferred to the H2 study.
2. **No full multi-filler explicit ternary RVE yet.** The ternary Regime-B and Regime-C runs spatialise Bi₂O₃ only. A future composition-equivalent ternary RVE must resolve both Bi₂O₃ and WO₃ phases or implement an explicitly validated effective background.
3. **Finite Regime-C RVE.** The 250 nm `G4MultiUnion` geometry is the largest practical configuration on the 8 GB workstation used here. Its 45-particle binary RVEs are sufficient for feasibility checks but not for high-precision convergence claims.
4. **No broad-beam buildup validation for all materials.** The main benchmark is narrow-beam attenuation. Buildup observables were retained only for the legacy Bi₂O₃ validation case.
5. **Density provenance.** Densities are volume-rule values or user-specified literature inputs; no measured densities are available for the simulated specimens.
6. **Photon-only scope.** Neutron, electron, and charged-particle transport through these nanocomposites is outside the scope of this paper.
7. **Single particle size.** Explicit-RVE studies use 25 nm radius spheres. Particle-size distributions, clustering, aggregation, and imperfect dispersion are not modelled.

---

## 9. Reproducibility, Code Availability, and Ethics

- **Software availability:** ShieldLab G4 v1.1 (tag to be assigned upon paper submission), released under the MIT licence. Source code is available at the repository root.
- **Data availability:** benchmark study JSON files, raw scorer outputs, derived CSV files, and figure-generation scripts for this paper are released in `results/paper3/` under CC-BY 4.0.
- **Compute environment:** Geant4 11.4-beta-01 on WSL Ubuntu 22.04, Python 3.11 on Windows host, `d:\uv_envs` virtual environment.
- **Primary command:** `python -m shieldlab.analysis.nano_benchmark <study.json> --wsl-distro Ubuntu --geant4-setup /home/negm_/geant4-install/bin/geant4.sh --executable ./build/ShieldLabG4 --no-plots --build-dir .`
- **Figure-generation command:** `python scripts/generate_paper3_v09_figures.py`. The journal-ready PNG/PDF/SVG outputs and manifest are written to `results/paper3/figures/v09/`.
- **Ethics statement:** this study used no human participants, no animal data, and no clinical data.
- **Funding statement:** no external funding was received for this work.
- **Conflict of interest statement:** the author declares no conflict of interest.
- **AI-assisted writing disclosure:** portions of the manuscript were drafted with the assistance of GitHub Copilot in agent mode; all physics claims, results, citations, and code were independently verified by the author before submission, consistent with COPE 2023 guidance.

---

## Appendix A. Regime-A XCOM Comparison Tables

### A.1 HDPE/Bi₂O₃ φ=0.189

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $(\mu/\rho)_\text{XCOM}$ | Δ (%) |
| ---: | ---: | ---: | ---: | ---: |
| 30 | 0.649496 | 19.542 | 19.507 | +0.18 |
| 50 | 0.650992 | 5.218 | 5.236 | −0.35 |
| 80 | 0.656895 | 1.581 | 1.621 | −2.45 |
| 100 | 0.651467 | 3.578 | 3.596 | −0.52 |
| 150 | 0.650565 | 1.336 | 1.339 | −0.20 |
| 356 | 0.652574 | 0.2249 | 0.2270 | −0.92 |
| 511 | 0.651168 | 0.1353 | 0.1358 | −0.42 |
| 662 | 0.652160 | 0.1021 | 0.1029 | −0.77 |
| 1173 | 0.651123 | 0.06365 | 0.06391 | −0.40 |
| 1332 | 0.652863 | 0.05818 | 0.05878 | −1.02 |

### A.2 HDPE/WO₃ φ=0.189

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $(\mu/\rho)_\text{XCOM}$ | Δ (%) |
| ---: | ---: | ---: | ---: | ---: |
| 30 | 0.649330 | 11.661 | 11.633 | +0.24 |
| 50 | 0.652710 | 3.080 | 3.110 | −0.97 |
| 80 | 0.649280 | 4.045 | 4.035 | +0.26 |
| 100 | 0.649630 | 2.328 | 2.325 | +0.13 |
| 150 | 0.649800 | 0.873 | 0.8725 | +0.07 |
| 356 | 0.652660 | 0.173 | 0.1746 | −0.95 |
| 511 | 0.650760 | 0.1146 | 0.1149 | −0.27 |
| 662 | 0.651250 | 0.09147 | 0.09188 | −0.45 |
| 1173 | 0.651100 | 0.06143 | 0.06167 | −0.39 |
| 1332 | 0.651500 | 0.05690 | 0.05720 | −0.53 |

### A.3 HDPE/BaWO₄ φ=0.189

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $(\mu/\rho)_\text{XCOM}$ | Δ (%) |
| ---: | ---: | ---: | ---: | ---: |
| 30 | 0.651490 | 8.730 | 8.777 | −0.532 |
| 50 | 0.650337 | 4.754 | 4.760 | −0.120 |
| 80 | 0.649338 | 3.183 | 3.175 | +0.237 |
| 100 | 0.649725 | 1.827 | 1.826 | +0.098 |
| 150 | 0.649401 | 0.697 | 0.695 | +0.214 |
| 356 | 0.652837 | 0.154 | 0.155 | −1.011 |
| 511 | 0.650650 | 0.107 | 0.107 | −0.232 |
| 662 | 0.651028 | 0.087 | 0.088 | −0.367 |
| 1173 | 0.650962 | 0.060 | 0.061 | −0.344 |
| 1332 | 0.650663 | 0.056 | 0.056 | −0.237 |

### A.4 HDPE/Bi₂O₃/WO₃ ternary

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $(\mu/\rho)_\text{XCOM}$ | Δ (%) |
| ---: | ---: | ---: | ---: | ---: |
| 30 | 0.649456 | 16.247 | 16.215 | +0.194 |
| 50 | 0.651407 | 4.322 | 4.343 | −0.502 |
| 80 | 0.651996 | 2.781 | 2.801 | −0.712 |
| 100 | 0.651373 | 3.057 | 3.072 | −0.490 |
| 150 | 0.650220 | 1.144 | 1.145 | −0.078 |
| 356 | 0.652769 | 0.203 | 0.205 | −0.987 |
| 511 | 0.650295 | 0.127 | 0.127 | −0.105 |
| 662 | 0.652484 | 0.097 | 0.098 | −0.886 |
| 1173 | 0.651227 | 0.062 | 0.063 | −0.438 |
| 1332 | 0.651655 | 0.058 | 0.058 | −0.591 |

### A.5 HDPE/Gd₂O₃ φ=0.189

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $(\mu/\rho)_\text{XCOM}$ | Δ (%) |
| ---: | ---: | ---: | ---: | ---: |
| 30 | 0.651514 | 8.251 | 8.296 | −0.540 |
| 50 | 0.658265 | 2.152 | 2.217 | −2.933 |
| 80 | 0.651055 | 3.135 | 3.147 | −0.377 |
| 100 | 0.650146 | 1.786 | 1.787 | −0.052 |
| 150 | 0.647455 | 0.679 | 0.673 | +0.911 |
| 356 | 0.653293 | 0.149 | 0.151 | −1.173 |
| 511 | 0.650264 | 0.104 | 0.105 | −0.094 |
| 662 | 0.651093 | 0.086 | 0.086 | −0.390 |
| 1173 | 0.652051 | 0.059 | 0.060 | −0.731 |
| 1332 | 0.652036 | 0.055 | 0.056 | −0.726 |

### A.6 HDPE/PbWO₄ φ=0.189

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $(\mu/\rho)_\text{XCOM}$ | Δ (%) |
| ---: | ---: | ---: | ---: | ---: |
| 30 | 0.650187 | 15.629 | 15.639 | −0.067 |
| 50 | 0.651081 | 4.165 | 4.181 | −0.386 |
| 80 | 0.651959 | 2.928 | 2.948 | −0.699 |
| 100 | 0.650701 | 2.979 | 2.986 | −0.250 |
| 150 | 0.649516 | 1.115 | 1.113 | +0.173 |
| 356 | 0.652840 | 0.199 | 0.201 | −1.012 |
| 511 | 0.651781 | 0.124 | 0.125 | −0.635 |
| 662 | 0.652389 | 0.096 | 0.097 | −0.852 |
| 1173 | 0.651323 | 0.062 | 0.062 | −0.472 |
| 1332 | 0.651589 | 0.057 | 0.058 | −0.567 |

---

## Appendix B. Regime-B Explicit-RVE Numerical Results

Each table reports the 1 µm `G4PVParameterised` RVE result with $10^7$ histories per energy.

### B.1 HDPE/Bi₂O₃

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $N_\text{att}$ |
| ---: | ---: | ---: | ---: |
| 30 | 0.995310 | 19.190 | 46,899 |
| 50 | 0.998753 | 5.095 | 12,475 |
| 80 | 0.999619 | 1.557 | 3,813 |
| 100 | 0.999140 | 3.512 | 8,601 |
| 150 | 0.999681 | 1.303 | 3,193 |
| 356 | 0.999949 | 0.2098 | 514 |
| 511 | 0.999971 | 0.1200 | 294 |
| 662 | 0.999975 | 0.1033 | 253 |
| 1173 | 0.999985 | 0.0608 | 149 |
| 1332 | 0.999988 | 0.0506 | 124 |

### B.2 HDPE/WO₃

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $N_\text{att}$ |
| ---: | ---: | ---: | ---: |
| 30 | 0.997526 | 11.660 | 24,740 |
| 50 | 0.999348 | 3.071 | 6,520 |
| 80 | 0.999152 | 3.996 | 8,480 |
| 100 | 0.999494 | 2.381 | 5,060 |
| 150 | 0.999815 | 0.870 | 1,850 |
| 356 | 0.999962 | 0.179 | 381 |
| 511 | 0.999976 | 0.112 | 237 |
| 662 | 0.999981 | 0.087 | 185 |
| 1173 | 0.999986 | 0.064 | 136 |
| 1332 | 0.999987 | 0.061 | 130 |

### B.3 HDPE/BaWO₄

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $N_\text{att}$ |
| ---: | ---: | ---: | ---: |
| 30 | 0.998325 | 8.697 | 16,750 |
| 50 | 0.999076 | 4.800 | 9,240 |
| 80 | 0.999392 | 3.157 | 6,080 |
| 100 | 0.999645 | 1.841 | 3,550 |
| 150 | 0.999865 | 0.699 | 1,350 |
| 356 | 0.999973 | 0.141 | 271 |
| 511 | 0.999978 | 0.116 | 224 |
| 662 | 0.999981 | 0.099 | 191 |
| 1173 | 0.999988 | 0.061 | 118 |
| 1332 | 0.999988 | 0.060 | 116 |

### B.4 HDPE/Bi₂O₃/WO₃ ternary

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $N_\text{att}$ |
| ---: | ---: | ---: | ---: |
| 30 | 0.997455 | 10.769 | 25,477 |
| 50 | 0.999306 | 2.936 | 6,942 |
| 80 | 0.999786 | 0.904 | 2,140 |
| 100 | 0.999516 | 2.047 | 4,843 |
| 150 | 0.999820 | 0.760 | 1,797 |
| 356 | 0.999968 | 0.136 | 322 |
| 511 | 0.999979 | 0.089 | 210 |
| 662 | 0.999982 | 0.075 | 177 |
| 1173 | 0.999987 | 0.054 | 127 |
| 1332 | 0.999989 | 0.044 | 105 |

### B.5 HDPE/Gd₂O₃

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $N_\text{att}$ |
| ---: | ---: | ---: | ---: |
| 30 | 0.998250 | 8.312 | 17,513 |
| 50 | 0.999547 | 2.150 | 4,531 |
| 80 | 0.999335 | 3.157 | 6,651 |
| 100 | 0.999624 | 1.785 | 3,761 |
| 150 | 0.999855 | 0.687 | 1,447 |
| 356 | 0.999967 | 0.157 | 330 |
| 511 | 0.999977 | 0.108 | 227 |
| 662 | 0.999983 | 0.079 | 167 |
| 1173 | 0.999988 | 0.055 | 116 |
| 1332 | 0.999988 | 0.056 | 118 |

### B.6 HDPE/PbWO₄

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $N_\text{att}$ |
| ---: | ---: | ---: | ---: |
| 30 | 0.996333 | 15.507 | 36,735 |
| 50 | 0.999030 | 4.096 | 9,704 |
| 80 | 0.999323 | 2.857 | 6,768 |
| 100 | 0.999297 | 2.970 | 7,036 |
| 150 | 0.999733 | 1.126 | 2,666 |
| 356 | 0.999954 | 0.196 | 464 |
| 511 | 0.999971 | 0.121 | 286 |
| 662 | 0.999979 | 0.090 | 213 |
| 1173 | 0.999985 | 0.062 | 146 |
| 1332 | 0.999987 | 0.053 | 126 |

---

## Appendix C. Regime-C Multi-Union Numerical Results

Each table reports the 250 nm `G4MultiUnion` RVE result with $10^7$ histories per energy.

### C.1 HDPE/Bi₂O₃

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $N_\text{att}$ |
| ---: | ---: | ---: | ---: |
| 30 | 0.998822 | 19.230 | 11,780 |
| 50 | 0.999675 | 5.301 | 3,250 |
| 80 | 0.999902 | 1.604 | 980 |
| 100 | 0.999785 | 3.514 | 2,150 |
| 150 | 0.999919 | 1.315 | 810 |
| 356 | 0.999987 | 0.2153 | 130 |
| 511 | 0.999991 | 0.1485 | 90 |
| 662 | 0.999994 | 0.1044 | 60 |
| 1173 | 0.999997 | 0.0489 | 30 |
| 1332 | 0.999996 | 0.0587 | 40 |

### C.2 HDPE/WO₃

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $N_\text{att}$ |
| ---: | ---: | ---: | ---: |
| 30 | 0.999390 | 11.497 | 6,100 |
| 50 | 0.999839 | 3.038 | 1,610 |
| 80 | 0.999784 | 4.078 | 2,160 |
| 100 | 0.999878 | 2.296 | 1,220 |
| 150 | 0.999952 | 0.896 | 480 |
| 356 | 0.999992 | 0.156 | 80 |
| 511 | 0.999995 | 0.100 | 50 |
| 662 | 0.999995 | 0.094 | 50 |
| 1173 | 0.999997 | 0.051 | 30 |
| 1332 | 0.999997 | 0.049 | 30 |

### C.3 HDPE/BaWO₄

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $N_\text{att}$ |
| ---: | ---: | ---: | ---: |
| 30 | 0.999583 | 8.660 | 4,170 |
| 50 | 0.999781 | 4.542 | 2,190 |
| 80 | 0.999846 | 3.187 | 1,540 |
| 100 | 0.999911 | 1.837 | 890 |
| 150 | 0.999969 | 0.646 | 310 |
| 356 | 0.999994 | 0.116 | 60 |
| 511 | 0.999995 | 0.106 | 50 |
| 662 | 0.999996 | 0.073 | 40 |
| 1173 | 0.999997 | 0.054 | 30 |
| 1332 | 0.999997 | 0.052 | 30 |

### C.4 HDPE/Bi₂O₃/WO₃ ternary

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $N_\text{att}$ |
| ---: | ---: | ---: | ---: |
| 30 | 0.999368 | 10.695 | 6,320 |
| 50 | 0.999826 | 2.939 | 1,740 |
| 80 | 0.999946 | 0.920 | 540 |
| 100 | 0.999885 | 1.938 | 1,150 |
| 150 | 0.999956 | 0.751 | 440 |
| 356 | 0.999992 | 0.140 | 80 |
| 511 | 0.999995 | 0.086 | 50 |
| 662 | 0.999994 | 0.095 | 60 |
| 1173 | 0.999998 | 0.039 | 20 |
| 1332 | 0.999997 | 0.049 | 30 |

### C.5 HDPE/Gd₂O₃

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $N_\text{att}$ |
| ---: | ---: | ---: | ---: |
| 30 | 0.999569 | 8.192 | 4,310 |
| 50 | 0.999890 | 2.086 | 1,100 |
| 80 | 0.999833 | 3.165 | 1,670 |
| 100 | 0.999900 | 1.897 | 1,000 |
| 150 | 0.999965 | 0.657 | 350 |
| 356 | 0.999993 | 0.140 | 70 |
| 511 | 0.999994 | 0.122 | 60 |
| 662 | 0.999996 | 0.076 | 40 |
| 1173 | 0.999997 | 0.057 | 30 |
| 1332 | 0.999997 | 0.047 | 30 |

### C.6 HDPE/PbWO₄

| E (keV) | T | $(\mu/\rho)_\text{sim}$ | $N_\text{att}$ |
| ---: | ---: | ---: | ---: |
| 30 | 0.999078 | 15.570 | 9,220 |
| 50 | 0.999750 | 4.217 | 2,500 |
| 80 | 0.999817 | 3.090 | 1,830 |
| 100 | 0.999827 | 2.916 | 1,730 |
| 150 | 0.999935 | 1.094 | 650 |
| 356 | 0.999989 | 0.189 | 110 |
| 511 | 0.999994 | 0.103 | 60 |
| 662 | 0.999995 | 0.081 | 50 |
| 1173 | 0.999996 | 0.062 | 40 |
| 1332 | 0.999997 | 0.044 | 30 |

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
