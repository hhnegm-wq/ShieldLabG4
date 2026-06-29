# Memory-Efficient Geant4 Modelling Regimes for Nanocomposite Radiation Shielding: Effective Medium, Explicit Nanoparticle Geometry, and Hybrid Representative-Volume Validation

**Hani H. Negm**  
*Department of Physics, **[AFFILIATION REQUIRED — DO NOT SUBMIT WITH PLACEHOLDER]***

---

## Abstract

Nanoparticle-loaded shielding materials are commonly represented in Monte Carlo simulations as homogeneous mixtures, although the term *nanocomposite* often suggests a resolved microstructure. This paper evaluates when such homogenisation is physically sufficient, when explicit nanoparticle geometry is necessary, and how both can be combined without prohibitive memory or tracking cost. Four Geant4 modelling regimes are proposed and benchmarked: (i) effective-medium mass-fraction material construction, (ii) explicit nanoparticle placement using parameterised volumes, (iii) voxelised multi-union inclusion geometry for moderate particle counts, and (iv) a hybrid representative-volume-element correction workflow in which explicit nanoparticle transport is restricted to a small validation cell and used to calibrate large-scale homogeneous slab simulations. The study is designed around polymer/high-Z oxide shielding systems, including HDPE/Bi2O3 and HDPE/WO3, over diagnostic-to-gamma-ray energies. Primary endpoints include transmitted photon fluence, deposited dose, secondary-electron dose enhancement near inclusions, runtime, memory footprint, geometry initialisation time, and agreement with NIST XCOM mass attenuation coefficients. The expected outcome is a decision framework showing that effective-medium modelling is optimal for most macroscopic shielding studies above tens of keV, while explicit geometry is justified only for nanoscale dose-enhancement or interface-dose questions. The hybrid representative-volume approach is proposed as the publishable compromise: it retains macroscopic Geant4 efficiency while quantifying the physics regime in which nanoparticle structure changes local energy deposition.

**Keywords:** Geant4; nanocomposite; radiation shielding; effective medium; nanoparticle; G4MultiUnion; parameterised geometry; representative volume element

---

## 1. Research Question and Novelty

The central question is not simply whether Geant4 can draw many nanoparticles. It can. The publishable question is:

> Which Geant4 nanocomposite modelling regime gives the best physics fidelity per unit memory and runtime for radiation-shielding applications?

The proposed novelty is a controlled comparison of four regimes using the same material composition, source spectrum, scoring geometry, physics list, random seeds, and validation metrics. The paper must explicitly separate two physical problems:

1. **Macroscopic shielding:** transmission, HVL/TVL, attenuation, broad-beam dose behind a slab. These are usually governed by elemental composition and density, so homogeneous material construction is expected to be optimal.
2. **Microscopic nanoparticle physics:** dose enhancement around high-Z inclusions, electron escape from particles, and interface-scale energy deposition. These require local geometry only in small representative volumes.

This separation is what makes the work suitable for a Q1-style article: it avoids the weak claim that explicit nanoparticles are always better and instead delivers a validated regime map.

---

## 2. Geant4 Modelling Regimes

### 2.1 Regime A — Effective-Medium Material Construction

The nanocomposite is built as one `G4Material` using elemental mass fractions and a measured or estimated bulk density. This is the regime already implemented in ShieldLab G4 through `MaterialRegistry::AddMassFractionMaterialCommand`.

For a matrix mass fraction `w_m` and filler mass fraction `w_f`, compound formulae are expanded to elemental mass fractions and added to a single material:

```cpp
auto* material = new G4Material(name, density * g / cm3, numberOfElements);
material->AddElement(element, massFraction);
```

**Best for:** macroscopic gamma shielding, candidate screening, composition sweeps, HVL/TVL, transmission, regulatory-dose estimates.

**Memory/runtime:** lowest; one logical material and ordinary slab geometry.

**Limitation:** cannot score dose gradients around individual nanoparticles.

### 2.2 Regime B — Explicit Nanoparticles with Parameterised Placement

Nanoparticles are represented as individual `G4Orb` or `G4Sphere` volumes embedded in a matrix. A custom `G4VPVParameterisation` supplies particle positions and optionally radii.

**Best for:** local dose enhancement, nano-radiosensitisation, particle-size studies, clustered vs dispersed distributions.

**Memory/runtime:** acceptable for small representative cells; not acceptable for macroscopic slabs at realistic nanoparticle counts.

**Main risk:** a real 1 cm3 composite can contain far more particles than can be explicitly placed, so this method must be restricted to an RVE.

### 2.3 Regime C — Voxelised Multi-Union Inclusions

`G4MultiUnion` can combine many displaced solids of one material into a single voxelised structure. The Geant4 Application Developer Guide documents `G4MultiUnion` as a standard construct since Geant4 10.4, with internal optimisation after `Voxelize()`.

**Best for:** moderate particle clusters, aggregate inclusions, fixed inclusion maps, comparison with parameterised placement at the same particle count.

**Memory/runtime:** better navigation than many independent placements for some clustered geometries, but still limited by particle count and geometry construction cost.

**Limitation:** all nodes in a `G4MultiUnion` share one material; complex multi-material inclusions require multiple unions or conventional placements.

### 2.4 Regime D — Hybrid RVE-Corrected Effective Medium

This is the recommended out-of-the-box strategy.

1. Use Regime A for the full shield slab.
2. Use Regime B or C only inside a small representative volume element.
3. Score local quantities in the RVE: secondary-electron dose, interface dose, and dose-enhancement factor.
4. Build a correction map as a function of energy, filler loading, particle radius, and clustering index.
5. Use the correction map only when the macroscopic homogeneous assumption is insufficient.

**Best for:** publishable nanocomposite shielding research because it avoids impossible full-scale nanoparticle geometry while still quantifying nanoscale effects.

**Memory/runtime:** controlled by a hard cap on RVE particle count.

**Recommendation:** make this the main paper contribution.

---

## 3. Density Treatment

Geant4 cannot construct a physical `G4Material` without density. Density is required because linear attenuation, transport step lengths, ionisation loss, and dose all depend on mass per unit volume.

The paper should compare three density inputs:

1. **Measured density:** preferred for experimental validation.
2. **Rule-of-mixtures density from volume fractions:** useful when filler loading and constituent densities are known.
3. **Mass-fraction-derived density estimate:** acceptable only for screening and must be labelled as an estimate.

For a two-phase composite with volume fraction `phi_f`, a first-order estimate is:

\[
\rho_\mathrm{eff} = \phi_f \rho_f + (1 - \phi_f)\rho_m
\]

For known mass fraction `w_f`, the corresponding ideal no-void density estimate is:

\[
\rho_\mathrm{eff} = \left(\frac{w_f}{\rho_f} + \frac{1-w_f}{\rho_m}\right)^{-1}
\]

Porosity can be included as:

\[
\rho_\mathrm{eff,porous} = (1-P)\rho_\mathrm{eff}
\]

---

## 4. Benchmark Design

### 4.1 Materials

The initial systems should be:

- HDPE/Bi2O3 at 5, 15, 30, and 50 wt% filler.
- HDPE/WO3 at 5, 15, 30, and 50 wt% filler.
- Epoxy/BaSO4 or silicone/BaSO4 as a lower-Z comparison.

All formulae are expanded into elemental mass fractions. The same effective density is used across regimes for fair macroscopic comparison.

### 4.2 Energies

Use two energy bands:

- Diagnostic range: 30, 50, 80, 100, 150 keV.
- Gamma shielding range: 356, 511, 662, 1173, 1332 keV.

The diagnostic band is where explicit nanoparticles may matter for local electron-dose effects. The gamma band tests the expectation that homogeneous modelling is sufficient for shielding transmission.

### 4.3 Geometry

Use three geometries:

1. **Full slab:** homogeneous 5 cm and 10 cm slab for transmission.
2. **RVE cube:** 1-10 um cube with explicitly placed nanoparticles for local dose.
3. **Clustered RVE:** same filler mass but nonuniform particle distributions to test aggregation effects.

### 4.4 Metrics

Report both physics and computational metrics:

- Transmission factor.
- Mass attenuation coefficient back-calculated from transmission.
- Deposited dose in matrix and filler.
- Interface dose-enhancement factor.
- Runtime per 1e6 histories.
- Peak memory.
- Geometry construction time.
- Number of placed particles or union nodes.
- Relative deviation from homogeneous XCOM prediction.

### 4.5 Acceptance Criteria

- Regime A should agree with NIST XCOM mass-fraction MAC within the existing ShieldLab photon benchmark tolerance away from absorption edges.
- Regimes B and C should converge to Regime A for macroscopic transmission when the RVE is statistically representative.
- Regimes B and C may diverge from Regime A for local dose near particle surfaces; this is not a failure but the main use case.
- Regime D is successful if it reproduces explicit-RVE local metrics while retaining full-slab runtime close to Regime A.

---

## 5. Figure Plan

1. **Figure 1:** Conceptual diagram of the four regimes: homogeneous slab, parameterised particles, multi-union cluster, hybrid RVE correction.
2. **Figure 2:** Runtime and peak memory versus particle count for Regimes B and C.
3. **Figure 3:** Transmission versus photon energy for Regimes A-C compared with XCOM.
4. **Figure 4:** Local radial dose profile around a high-Z nanoparticle at diagnostic energies.
5. **Figure 5:** Regime map: recommended method as a function of photon energy, target observable, and particle count.
6. **Figure 6:** Workflow diagram linking ShieldLab composition entry, Geant4 macro generation, RVE benchmark, and publication outputs.

---

## 6. Recommended Implementation in ShieldLab G4

The practical implementation should be staged:

1. Add a first-class nano-composite material command that accepts matrix formula, filler formula, loading, constituent densities, and optional porosity, then builds a homogeneous `G4Material`.
2. Add an RVE generator for explicit nanoparticle benchmark cells with a hard particle-count cap.
3. Add a `G4MultiUnion` cluster mode for moderate particle-count comparison.
4. Add benchmark scripts that export runtime, memory, and physics metrics to JSON/CSV.
5. Add publication figure generation using the existing `shieldlab.viz` style layer.

The default production regime should remain effective-medium modelling. Explicit geometry should be labelled as **RVE research mode**, not as the default full-shield mode.

---

## 7. Preliminary Recommendation Matrix

| Target question | Recommended regime | Reason |
|---|---:|---|
| Fast shielding screening | A | Composition and density dominate; lowest cost. |
| Full slab transmission at Cs-137 / Co-60 energies | A | Explicit nanoscale geometry adds cost without expected macroscopic benefit. |
| Diagnostic-energy local dose near high-Z inclusions | B or C | Secondary electrons and interfaces may matter. |
| Clustered nanoparticles | C | Multi-union geometry can represent fixed aggregates efficiently. |
| Q1 paper comparing physics and performance | D | Combines practical full-scale simulation with explicit nanoscale validation. |
| Production UI default | A plus optional D-derived warning/correction | Robust, fast, avoids memory blow-ups. |

---

## 8. Real Reference List to Verify and Use

Only verified, real references should be used. No invented nanoparticle papers should be inserted without DOI/manual verification.

1. S. Agostinelli et al., "Geant4-a simulation toolkit," *Nuclear Instruments and Methods in Physics Research A*, 506, 250-303, 2003. DOI: 10.1016/S0168-9002(03)01368-8.
2. J. Allison et al., "Geant4 developments and applications," *IEEE Transactions on Nuclear Science*, 53, 270-278, 2006. DOI: 10.1109/TNS.2006.869826.
3. J. Allison et al., "Recent developments in Geant4," *Nuclear Instruments and Methods in Physics Research A*, 835, 186-225, 2016. DOI: 10.1016/j.nima.2016.06.125.
4. M. J. Berger, J. H. Hubbell, S. M. Seltzer, J. Chang, J. S. Coursey, R. Sukumar, D. S. Zucker, and K. Olsen, *XCOM: Photon Cross Section Database*, NIST Standard Reference Database 8 (XGAM), National Institute of Standards and Technology.
5. J. H. Hubbell and S. M. Seltzer, *Tables of X-Ray Mass Attenuation Coefficients and Mass Energy-Absorption Coefficients from 1 keV to 20 MeV for Elements Z = 1 to 92 and 48 Additional Substances of Dosimetric Interest*, NISTIR 5632, 1995.
6. J. H. Hubbell, "Photon mass attenuation and energy-absorption coefficients from 1 keV to 20 MeV," *International Journal of Applied Radiation and Isotopes*, 33, 1269-1290, 1982. DOI: 10.1016/0020-708X(82)90248-4.
7. S. Incerti et al., "Comparison of Geant4 very low energy cross section models with experimental data in water," *Medical Physics*, 37, 4692-4708, 2010. DOI: 10.1118/1.3476457.
8. S. Incerti et al., "The Geant4-DNA project," *International Journal of Modeling, Simulation, and Scientific Computing*, 1, 157-178, 2010. DOI: 10.1142/S1793962310000122.
9. H. N. Tran et al., "Geant4 Monte Carlo simulation of absorbed dose and radiolysis yields enhancement from a gold nanoparticle under MeV proton irradiation," *Nuclear Instruments and Methods in Physics Research B*, 373, 126-139, 2016. DOI: 10.1016/j.nimb.2016.01.017.
10. J. H. Hubbell, "Review of photon interaction cross section data in the medical and biological context," *Physics in Medicine and Biology*, 44, R1-R22, 1999. DOI: 10.1088/0031-9155/44/1/001.

References for specific Bi2O3/HDPE, WO3/polymer, and BaSO4/polymer experimental composites must be added only after manual DOI verification.

---

## 9. Work Packages

| WP | Task | Output |
|---|---|---|
| WP1 | Literature lock | Verified DOI bibliography for nanocomposite shielding and Geant4 nanoparticle modelling. |
| WP2 | Homogeneous material command | Macro/API support for matrix + filler + density/porosity. |
| WP3 | RVE explicit geometry | Parameterised nanoparticle placement with particle-count cap. |
| WP4 | MultiUnion benchmark | Cluster/aggregate geometry mode using `G4MultiUnion`. |
| WP5 | Benchmark runner | JSON/CSV outputs for memory, runtime, transmission, dose. |
| WP6 | Figures | Six publication-grade figures. |
| WP7 | Manuscript completion | Results, discussion, limitations, and journal formatting. |

---

## 10. Current Status

This is a design manuscript and benchmark protocol. It intentionally contains no fabricated numerical results. The next scientific milestone is to implement the benchmark harness and generate reproducible results before writing the Results and Discussion sections.
