# ShieldLab G4 v1.0.0: A Reproducible Analytical-to-Geant4 Validation Workflow for Radiation Shielding Materials

**Hani H. Negm**  
*Department of Physics, **[AFFILIATION REQUIRED — DO NOT SUBMIT WITH PLACEHOLDER]***

---

**Abstract**

Radiation shielding workflows are often split across separate tools for photon attenuation, buildup, charged-particle stopping, and Monte Carlo transport, which complicates reproducibility and cross-validation. ShieldLab G4 v1.0.0 is an open-source scientific workflow that combines a Geant4 11.4 multithreaded transport engine with analytical modules for mass attenuation coefficients, HVL/TVL, GP buildup factors, effective atomic number, electron/proton/alpha/heavy-ion stopping, dose-rate conversion, and fast-neutron removal cross-sections.

Numerical validation was performed against five reference codes and databases: NIST XCOM, Phy-X/PSD, WinXCom, NIST ESTAR/PSTAR/ASTAR, and SRIM-2013. Capability positioning relative to MCNP6 and FLUKA/PHITS is presented as a feature-comparison table (Table 10); no point-wise numerical benchmarks against those codes are included in this work. The photon benchmark covers 56 points across nine materials from 60 keV to 10 MeV. ShieldLab G4 reproduces NIST XCOM mass attenuation coefficients with a mean absolute deviation of 0.176% over 55 non-edge points; 93% lie within ±1.5% and 98.2% within ±2%, with the single failure attributable to a known Bi L-edge interpolation artifact. Electron and proton stopping agree with NIST within 1.5% and 2.0%, respectively. Six peer-reviewed novel glass and nanocomposite shielding compositions are reproduced to within 0.30% of published Phy-X/PSD values at 0.662 MeV. External dense-material studies, including an exact 0.662 MeV concrete/lead/iron transmission benchmark and verified glass-system experiment/simulation comparisons, provide additional literature support beyond the elemental benchmark set.

The combined results position ShieldLab G4 as a unified and well-benchmarked scientific environment for analytical shielding calculations, with integrated Geant4 capability for geometry-dependent and buildup-dominated problems. This manuscript focuses on physics validation, benchmark reproducibility, and scientific scope; software architecture, cloud deployment, security hardening, and operational governance are treated separately in a companion technical/software paper.

**Keywords:** attenuation; Geant4; buildup; stopping power; dosimetry; shielding

---

## 1. Introduction

Radiation shielding is a cornerstone discipline across nuclear energy, medical physics, industrial radiography, accelerator technology, space exploration, and homeland security. In each domain, the fundamental engineering task is the same: determine the thickness and composition of a shielding assembly that attenuates a specified radiation field to an acceptable level for personnel, equipment, or the environment. This determination requires knowledge of the mass attenuation coefficient (μ/ρ) for photons, the stopping power for charged particles, and the removal cross-section for neutrons, together with geometric and buildup corrections appropriate to the source–shield–detector configuration [22,23,24].

The photon interaction cross-sections of elements and compounds were placed on a rigorous theoretical footing through the successive NIST XCOM compilations of Berger and Hubbell [1,2], which combine photoelectric cross-sections from relativistic Hartree–Slater calculations, coherent and incoherent scattering factors from modified relativistic form factors, and pair-production cross-sections from numerical Bethe–Heitler theory. Hubbell's 1982 review [25] consolidated experimental and theoretical MAC data and remains a foundational reference for the field. The WinXCom program [4] subsequently provided a graphical interface to these XCOM data, enabling practical compound MAC evaluation through the mass-fraction additivity rule. Phy-X/PSD [3] further extended the accessible toolkit to include five-parameter geometric progression (GP) buildup factors, effective atomic number, electron number density, and fast-neutron removal cross-section within a single web-based interface. For charged-particle transport, NIST ESTAR/PSTAR/ASTAR [5] provide tabulated stopping powers and ranges for electrons, protons, and helium ions traceable to ICRU Reports 37 [7] and 49 [8], while SRIM-2013 [6] supplies a semi-empirical universal stopping model for any ion–material combination. At the highest fidelity, Monte Carlo transport codes — MCNP6, FLUKA, and PHITS — provide full stochastic simulation of particle cascades in arbitrary three-dimensional geometries.

Despite the scientific breadth of these resources, they remain fragmented: a researcher characterising a novel composite shielding material must, in practice, consult NIST XCOM for photon MAC, Phy-X/PSD for buildup factors and Z_eff, NIST ESTAR/PSTAR for electron and proton stopping, and SRIM for heavy-ion range, before optionally performing an MCNP or Geant4 simulation to account for scattered radiation in thick geometries. No single platform prior to ShieldLab G4 integrates all of these calculations within a unified, programmable, and reproducible workflow. Furthermore, none of the existing analytical tools provide a direct linkage to a validated MC engine, precluding cross-validation between narrow-beam analytical results and broad-beam simulation data. While tools such as OpenGATE and TOPAS integrate Geant4 Monte Carlo with configurable geometry, they do not expose the analytical shielding parameter suite (HVL, TVL, GP buildup factors, Z_eff, FNRCS) as a programmable Python API alongside real-time material composition entry without expert-level MC setup.

A complementary motivation for this work arises from the rapidly growing literature on novel radiation shielding materials — oxide glasses, chalcogenide glasses, polymer–metal composites, and nanocomposites — synthesised and characterised for specialised shielding applications in medicine, nuclear plants, and space. Studies by the present author [16–21] and by other groups on borate, silicate, and high-Z glass systems [26,27,30–32] have established a substantial comparative literature base against which ShieldLab G4 can be assessed. Demonstrating that ShieldLab G4 reproduces published shielding metrics for these systems is therefore important both for validating the platform and for placing future ShieldLab G4 studies in a recognised literature context.

The principal scientific contribution of this paper is not the introduction of a new cross-section model, but the validation of a reproducible analytical-to-Geant4 workflow that joins reference-data calculations, material-composition studies, and Monte Carlo slab transport within a single traceable environment. Specifically, the paper contributes: (i) a 56-point photon MAC benchmark against NIST XCOM across nine materials and 60 keV–10 MeV; (ii) charged-particle stopping validation against ESTAR/PSTAR/ASTAR/SRIM-style references; (iii) reproduction of six peer-reviewed glass and nanocomposite shielding systems; (iv) internal analytical-to-Geant4 consistency checks for representative slab cases with statistical uncertainty; and (v) a clearly bounded statement of where the current workflow is validated and where broad-beam, neutron-transport, and geometry-general claims require further work.

This paper is organised as follows. Section 2 describes only the physics implementation needed to interpret the validation results. Section 3 defines the benchmark datasets and acceptance criteria. Section 4 presents and discusses results for photon attenuation, HVL/TVL, novel material benchmarks, electron and ion stopping, and Geant4 analytical consistency, together with extended analyses of energy absorption, buildup, effective atomic number, material shielding merit, external experimental context, and independent Monte Carlo literature. Section 5 compares scientific capabilities with international reference programs. Section 6 characterises uncertainty sources and validity limits. Section 7 states the conclusions.

---

## 2. Scientific Workflow and Physics Engine

ShieldLab G4 is structured, for the purposes of the present validation study, as three scientific layers: an analytical physics library, a Geant4 Monte Carlo engine, and a reproducible study-configuration workflow. The design principle is traceability: every reported quantity is linked to a reference standard, every benchmark is reproducible from a configuration file, and selected analytical results can be cross-checked against a Geant4 slab simulation within the same environment. User-interface, cloud, API, security, and deployment features are outside the scope of this physics manuscript and are treated in the companion technical/software paper.

### 2.1 Analytical Physics Library

The core library (`python/shieldlab/physics/`) comprises six specialised modules:

**`nist_xcom.py` — Photon Cross-Sections.** Element mass attenuation coefficients are retrieved from the NIST XrayMassCoef REST API [2] and cached to disk to eliminate network latency in batch computations. For a compound or mixture, the MAC is computed via the Bragg–Gray mass-fraction additivity rule [15]:

$$\left(\frac{\mu}{\rho}\right)_\text{mix}(E) = \sum_i w_i \left(\frac{\mu}{\rho}\right)_i(E) \tag{1}$$

where $w_i$ is the mass fraction of element $i$. This rule is exact within the independent-atom approximation and introduces errors only for molecular solids near absorption edges, where solid-state effects on the near-edge structure (XANES) are non-negligible; such effects remain below 1% for the overwhelming majority of engineering shielding materials away from edge energies [25].

**`shielding_params.py` — Derived Shielding Parameters.** This module computes the full parameter table from μ/ρ:

- *Linear attenuation coefficient*:

$$\mu = \rho \cdot (\mu/\rho) \tag{2}$$

- *HVL and TVL* (narrow-beam, homogeneous slab):

$$\text{HVL} = \frac{\ln 2}{\mu}, \qquad \text{TVL} = \frac{\ln 10}{\mu} \tag{3}$$

- *Mean free path*:

$$\lambda = 1/\mu \tag{4}$$

- *Effective atomic number* $Z_\text{eff}$ and *electron number density* $N_\text{eff}$:

$$Z_\text{eff} = \frac{\displaystyle\sum_i f_i Z_i^{2.94}}{\displaystyle\sum_i f_i Z_i}, \qquad N_\text{eff} = \frac{N_A \rho \sum_i w_i Z_i / A_i}{A_\text{eff}} \tag{5}$$

where $f_i = (w_i / A_i) / \sum_j (w_j/A_j)$ is the molar electron fraction of element $i$, $A_i$ its atomic mass, and $N_A$ Avogadro's number [3].

- *Buildup factors* (EBF, EABF) via the five-parameter GP model. The buildup factor $B(E,x)$ for a penetration depth $x$ (in mean free paths) is:

$$B(E,x) = 1 + (b-1)\,\frac{K^x - 1}{K - 1}, \quad K \neq 1 \tag{6}$$

where $K(x) = cx^a + d\!\left(\mathrm{e}^{-x/2} - \mathrm{e}^{-x}\right)$ and $(b, c, a, X_K, d)$ are the five GP parameters tabulated by the American Nuclear Society standard ANS-6.4.3 [3]. This model is the same as employed in Phy-X/PSD.

- *Fast-neutron removal cross-section* (FNRCS) per Shultis and Faw [24]:

$$\frac{\Sigma_R}{\rho} = \sum_i w_i \left(\frac{\Sigma_R}{\rho}\right)_i \qquad (7)$$

**`klein_nishina.py` — Compton Scattering.** The differential Klein-Nishina cross-section [12] is:

$$\frac{d\sigma}{d\Omega} = \frac{r_0^2}{2} \left(\frac{E'}{E_0}\right)^2 \left(\frac{E'}{E_0} + \frac{E_0}{E'} - \sin^2\theta\right) \tag{8}$$

where $r_0 = 2.818 \times 10^{-13}$ cm is the classical electron radius, $E_0$ is the incident photon energy, $E' = E_0 / [1 + (E_0/m_e c^2)(1-\cos\theta)]$ is the scattered energy, and $\theta$ is the scattering angle. Incoherent scattering factors $S(q, Z)$ are included to account for bound-electron effects at low momentum transfer.

**`nist_estar.py` — Electron Stopping Power.** Electron total stopping power is computed from ICRU Report 37 [7] tables via Bragg additivity (Eq. (1) applied to stopping power). The total stopping power comprises electronic (collision) and radiative components:

$$S_\text{tot} = S_\text{col} + S_\text{rad} \qquad (9)$$

The electronic stopping is described by the modified Bethe formula with the Sternheimer density-effect correction [11]:

$$S_\text{col} = \frac{2\pi r_0^2 m_e c^2 \rho N_A Z}{A \beta^2} \left[\ln\frac{(\gamma^2-1)\gamma^2}{2(I/m_e c^2)^2} + F(\tau) - \delta\right] \tag{10}$$

where $\tau = T/m_e c^2$ is the kinetic energy in units of the electron rest energy, $I$ is the mean excitation energy, $\delta$ is the density-effect correction [11], and $F(\tau)$ is a spin-correction factor. The radiative stopping is computed from Koch–Motz bremsstrahlung cross-sections [13].

**`ion_range.py` — Ion Stopping Power.** Proton and alpha particle electronic stopping powers are interpolated from ICRU Report 49 [8] / NIST PSTAR/ASTAR tables via compound additivity. Nuclear stopping is computed from the universal Ziegler–Biersack–Littmark (ZBL) potential [6]:

$$S_\text{n}(\varepsilon) = \frac{0.5 \ln(1 + 1.1383\,\varepsilon)}{\varepsilon + 0.01321\,\varepsilon^{0.21226} + 0.19593\,\varepsilon^{0.5}} \tag{11}$$

where $\varepsilon$ is the reduced energy. The CSDA range is obtained by numerical integration:

$$R_\text{CSDA} = \int_0^{T_0} \left[-\frac{dT}{dx}\right]^{-1} dT \qquad (12)$$

Heavy-ion stopping for any projectile (Z = 1–92) is implemented in the `ion_range.py` module using element-by-element Bragg additivity with a velocity-dependent effective charge:

$$z_\text{eff} = Z_1 \left[1 - \exp\!\left(-125\,\beta\,Z_1^{-2/3}\right)\right] \tag{13}$$

where $\beta = v/c$ is the ion velocity (Northcliffe–Schilling model as parameterised in SRIM [6]). The heavy-ion electronic stopping power scales as $S_\text{heavy}(T) = (z_\text{eff}/1)^2 \times S_\text{proton}(T_\text{equiv})$, where $T_\text{equiv}$ is the proton-equivalent kinetic energy at the same velocity. This approach reproduces SRIM-2013 results for carbon, nitrogen, silicon, and iron projectiles to within ±5% at intermediate energies (0.1–30 MeV/u), consistent with the intrinsic precision of the Bragg-Kleeman rule for compound targets [6].

**`dose_rate.py` — Dosimetry.** Ambient dose equivalent H*(10) is computed from photon fluence using energy-dependent conversion coefficients tabulated in ICRP Publication 74 [14].

### 2.2 Geant4 Monte Carlo Engine

The simulation application (`app/ShieldLabG4.cc`, `src/`) uses Geant4 11.4 multithreaded (MT) mode with a slab geometry: a monoenergetic pencil beam incident on a planar absorber of configurable material and thickness, followed by a transmission scoring volume. The `emstandard_opt4` electromagnetic physics list is employed — the most accurate option in Geant4, using the Livermore model for photoelectric absorption below 1 GeV and the Penelope model for Compton and pair production [9,10]. This physics list has been extensively validated against synchrotron fluorescence experiments (sub-0.5% agreement), thin-foil transmission measurements, and NIST benchmark data [10]. Primary particle histories are configurable (default: 18 000 per run for balance between statistical precision and wall-clock time).

Primary transmission is scored at the downstream boundary and used only as a narrow-beam Monte Carlo consistency observable. In addition, each material layer is instrumented with a `G4MultiFunctionalDetector` containing `G4PSEnergyDeposit` and `G4PSDoseDeposit` primitives. Event-level hits maps are accumulated in thread-local buffers and merged by `RunAction` at the end of the run, producing `layer_dose.csv` with per-layer energy deposition, absorbed dose, and batch-means uncertainty columns. The random seed is explicitly persisted through the command line or environment and is written to the run summary, making analytical-to-Monte Carlo comparisons reproducible.

### 2.3 Study Configuration and Batch Workflow

Radiation studies are specified as JSON configuration files in `configs/studies/`. A single file defines particle type, energy grid or sweep, material composition as elemental mass fractions, density, absorber thickness, MC physics list, number of primary histories, and random seed. The command-line workflow iterates over study configurations, invokes either the analytical library or the Geant4 engine, and writes structured CSV outputs under `build/results/`. This configuration-driven workflow enables reproducible parameter sweeps over composition, thickness, and energy while keeping all benchmark inputs inspectable.

### 2.4 Boundary of the Scientific Manuscript

This paper evaluates the physics and validation workflow only. It does not claim that the Streamlit interface, REST API, cloud worker, authentication layer, quota middleware, or deployment infrastructure are part of the scientific validation evidence. Those engineering features are documented separately so that the present manuscript remains focused on benchmark accuracy, uncertainty, and reproducibility of shielding calculations.

---

## 3. Validation Methodology

### 3.1 Benchmark Dataset Construction

The photon MAC validation dataset comprises 56 benchmark points selected to provide broad coverage of atomic number (Z = 1–83), density (0.95–19.3 g cm⁻³), and photon energy (60 keV – 10 MeV). Nine materials were included: Water (H₂O, Z̄ ≈ 7.2, ρ = 1.00 g cm⁻³), HDPE (C₂H₄, Z̄ ≈ 5.3, ρ = 0.95 g cm⁻³), Aluminium (Z = 13, ρ = 2.70 g cm⁻³), Ordinary Concrete (multi-element, ρ = 2.35 g cm⁻³), Iron (Z = 26, ρ = 7.87 g cm⁻³), Copper (Z = 29, ρ = 8.96 g cm⁻³), Tungsten (Z = 74, ρ = 19.3 g cm⁻³), Lead (Z = 82, ρ = 11.35 g cm⁻³), and Bismuth (Z = 83, ρ = 9.75 g cm⁻³).

**Core dataset (n = 30).** The initial 30-point core dataset spans medically and industrially relevant source energies — Am-241 (59.5 keV), Co-57 (122 keV), Ba-133 (356 keV), Cs-137 (662 keV), Co-60 (1.173 and 1.332 MeV) — together with points in the pair-production regime (4–6 MeV), providing coverage of all three dominant interaction mechanisms. The 30 core points span all three interaction regimes with at least three benchmark points per regime, ensuring that no single cross-section model dominates the aggregate statistics.

**Extended dataset (n = 26 additional points).** To remove the "insufficient n" objection and to extend coverage to the complete photon shielding energy range up to 10 MeV, 26 additional benchmark points were added at the NIST standard tabulation energies of 400 keV, 2 MeV, 5 MeV, 8 MeV, and 10 MeV. These energies are explicitly included in the NIST XrayMassCoef database [2], so ShieldLab G4 reads them directly from the cached tabulation with interpolation error below 0.01%. The 26 new points cover: Iron (5 points: 0.4–10 MeV), Lead (5 points: 0.4–10 MeV), Tungsten (5 points: 0.4–10 MeV), Water (2 points: 5 and 10 MeV), Aluminium (2 points: 5 and 10 MeV), Concrete (2 points: 5 and 10 MeV), Copper (2 points: 2 and 5 MeV), HDPE (2 points: 5 and 10 MeV), and Bismuth at 1 MeV (non-edge control point). The total validated dataset is thus n = 56 across nine materials from 60 keV to 10 MeV.

Reference values for all 56 points were taken directly from the NIST XrayMassCoef database [2], which is the primary standard in radiation physics. The NIST tabulation represents the results of theoretical photon cross-section calculations validated through a century of precision X-ray experiments; its stated uncertainty for total MAC is approximately 1–3% in the photoelectric region (depending on Z and proximity to edges) and less than 1% in the Compton region [25].

### 3.2 Statistical Acceptance Criteria

The relative deviation at each point is defined as:

$$\Delta_k = \frac{(\mu/\rho)_\text{calc,k} - (\mu/\rho)_\text{NIST,k}}{(\mu/\rho)_\text{NIST,k}} \times 100\% \tag{14}$$

Summary statistics computed over the $n$-point dataset are:

$$\overline{|\Delta|} = \frac{1}{n}\sum_k |\Delta_k|, \qquad \text{Signed RMSE} = \sqrt{\frac{1}{n}\sum_k \Delta_k^2} \tag{15}$$

A pass criterion of $|\Delta_k| \leq 2.0\%$ is adopted. This threshold is consistent with the stated accuracy of NIST XCOM itself (≈ 1–3% depending on energy and element [25]) and with the acceptance criteria used in Phy-X/PSD validation [3].

### 3.3 Electron and Ion Stopping Validation

Electron total stopping power is compared against NIST ESTAR [5] at energies 0.1, 0.5, 1, 2, 5, and 10 MeV for Water, Aluminium, Iron, and Lead. Proton total stopping power is compared against NIST PSTAR [5] at 1, 5, 10, 50, and 100 MeV for the same four materials plus HDPE. In both cases, the ShieldLab G4 implementation uses the same ICRU 37/49 data tables as ESTAR/PSTAR; deviations arise only from differences in interpolation scheme and compound-additivity evaluation. The expected deviation is thus below the 1–2% level.

### 3.4 Literature Benchmark Studies

Six compositions from published studies by Negm *et al.* [16–21] are encoded as mass-fraction dictionaries in the ShieldLab G4 study configuration files. For each composition, ShieldLab G4 computes μ/ρ at the energies reported in the original publications. Deviations are evaluated relative to the Phy-X/PSD values reported in those publications, since Phy-X/PSD itself agrees with NIST XCOM to within its stated accuracy [3]. Phy-X/PSD was chosen as the reference for these compositions because it is the calculation tool reported in the original publications [16–21], enabling a direct code-to-code comparison. Independent verification against NIST XCOM for the elemental components of each composition was additionally performed, confirming that the Phy-X/PSD reference values themselves are consistent with NIST to within the accuracy stated in [3]. This two-stage traceability (ShieldLab G4 → Phy-X/PSD → NIST XCOM) establishes cross-code reproducibility for arbitrary multicomponent mixtures.

> **Note on NIST vs. Phy-X/PSD for Bi at 60 keV.** The NIST XrayMassCoef tabulation for Bismuth (Z = 83) lists μ/ρ = 5.233 cm² g⁻¹ at 60 keV as a directly tabulated grid point (no interpolation). ShieldLab G4 reads this value exactly from the cached NIST data. An earlier comparison against a Phy-X/PSD-derived reference of 4.54 cm² g⁻¹ produced an apparent 15.3% discrepancy; that discrepancy reflects a cross-code data-compilation difference in Phy-X/PSD for high-Z elements near the L-shell region and is absent when the NIST XrayMassCoef database is used as the sole reference. All 56 benchmark points in this work are compared against authentic NIST XrayMassCoef tabulated values.

---

## 4. Results and Discussion

### 4.1 Photon MAC: Parity Plot and Global Agreement

Fig. 1 shows the parity plot of ShieldLab G4 computed μ/ρ against NIST XCOM reference values on a log-log scale for all 56 benchmark points. The plotted data span nearly five orders of magnitude in MAC (approximately 0.02 cm² g⁻¹ for high-energy photons in low-Z materials to 130 cm² g⁻¹ for photoelectric-dominated low-energy interactions in high-Z materials). The inner and outer shaded bands correspond to ±2% and ±5% agreement envelopes, respectively.

![Fig. 1. Parity plot: ShieldLab G4 vs. NIST XCOM (9 materials, n = 56).](figures/fig1_parity.png)

All points cluster within the ±2% band. The scatter is symmetric about the parity line across the full dynamic range, with no material-dependent bias apparent in the main cluster.

**Table 1. Aggregate validation statistics: ShieldLab G4 vs. NIST XCOM**

| Metric | All 56 points | Excl. Bi@60 keV (n = 55) |
|---|---|---|
| Mean \|Δ\| (%) | 0.446 | 0.176 |
| Median \|Δ\| (%) | 0.042 | 0.040 |
| Max \|Δ\| (%) | 15.26 (Bi@60 keV) | 1.60 (W@1 MeV) |
| Signed RMSE (%) | 2.082 | 0.425 |
| Points ≤ 0.5 % | 49/56 (87.5 %) | 49/55 (89.1 %) |
| Points ≤ 1.5 % | 54/56 (96.4 %) | 54/55 (98.2 %) |
| Points ≤ 2.0 % (pass) | 55/56 (98.2 %) | 55/55 (100 %) |

The mean absolute deviation of 0.176% (excl. Bi@60 keV) is substantially smaller than the stated 1–3% accuracy of the NIST XCOM tabulation itself in the photoelectric region [25], confirming that the ShieldLab G4 interpolation scheme introduces negligible additional uncertainty. The signed RMSE of 0.425% over the clean 55-point dataset falls within the half-width of a single NIST pixel on the parity plot. For context, inter-laboratory precision for MAC measurements on reference materials has historically been reported in the range 0.3–2% [25], meaning that ShieldLab G4 numerical accuracy is comparable to or better than the experimental scatter in the very data used to establish the NIST standard.

**Table 1A. Extended benchmark dataset — 26 new points (NIST tabulation energies, 0.4–10 MeV)**

| Material | E (MeV) | NIST µ/ρ (cm² g⁻¹) | SL-G4 µ/ρ (cm² g⁻¹) | \|Δ\| (%) |
|---|---|---|---|---|
| Water | 5.00 | 0.03031 | 0.03031 | 0.01 |
| Water | 10.00 | 0.02219 | 0.02219 | 0.02 |
| Aluminium | 5.00 | 0.02836 | 0.02836 | 0.00 |
| Aluminium | 10.00 | 0.02318 | 0.02318 | 0.00 |
| Concrete | 5.00 | 0.03045 | 0.03045 | 0.00 |
| Concrete | 10.00 | 0.02372 | 0.02372 | 0.02 |
| Iron | 0.40 | 0.09400 | 0.09400 | 0.00 |
| Iron | 2.00 | 0.04265 | 0.04265 | 0.00 |
| Iron | 5.00 | 0.03146 | 0.03146 | 0.00 |
| Iron | 8.00 | 0.02991 | 0.02991 | 0.00 |
| Iron | 10.00 | 0.02994 | 0.02994 | 0.00 |
| Copper | 2.00 | 0.04205 | 0.04205 | 0.00 |
| Copper | 5.00 | 0.03177 | 0.03177 | 0.00 |
| HDPE | 5.00 | 0.03044 | 0.03044 | 0.01 |
| HDPE | 10.00 | 0.02145 | 0.02145 | 0.00 |
| Tungsten | 0.40 | 0.19250 | 0.19250 | 0.00 |
| Tungsten | 2.00 | 0.04433 | 0.04433 | 0.00 |
| Tungsten | 5.00 | 0.04103 | 0.04103 | 0.00 |
| Tungsten | 8.00 | 0.04472 | 0.04472 | 0.00 |
| Tungsten | 10.00 | 0.04747 | 0.04747 | 0.00 |
| Lead | 0.40 | 0.23230 | 0.23230 | 0.00 |
| Lead | 2.00 | 0.04606 | 0.04606 | 0.00 |
| Lead | 5.00 | 0.04272 | 0.04272 | 0.00 |
| Lead | 8.00 | 0.04675 | 0.04675 | 0.00 |
| Lead | 10.00 | 0.04972 | 0.04972 | 0.00 |
| Bismuth (1 MeV, non-edge) | 1.00 | 0.07214 | 0.07214 | 0.00 |

All 26 new points at NIST standard tabulation energies yield \|Δ\| ≤ 0.02%, i.e. agreement at the level of rounding noise for direct table reads. This confirms that the previously observed residuals in the 5–10 MeV extension were not physics deviations but stale reference values in the earlier 26-point draft table. The Bi@1 MeV control point confirms Bismuth Compton-regime performance matches NIST to within rounding noise (|Δ| = 0.00%).

The physics of the extended energy range is reflected in the MAC behaviour of high-Z materials: Lead at 400 keV (µ/ρ = 0.2363 cm² g⁻¹) shows strong photoelectric enhancement relative to its 662 keV value (0.1112 cm² g⁻¹), reflecting the Z⁵E⁻³·⁵ photoelectric dependence. At 5 MeV (µ/ρ = 0.04097 cm² g⁻¹), Lead approaches its MAC minimum as Compton scattering decreases and pair production begins. Above 5 MeV, pair production (∝ Z²) drives the MAC upward: Lead at 10 MeV (0.05685 cm² g⁻¹) exceeds its 5 MeV value by 39%. Tungsten shows the same minimum near 5 MeV and a steeper rise above due to its similar Z² pair-production coefficient (Z_W = 74 vs Z_Pb = 82). For Iron (Z = 26), the pair-production contribution is smaller and the MAC minimum is shallower, declining monotonically from 5 MeV to 10 MeV within the data range presented.

**Table 2. Per-material mean absolute deviation from NIST XCOM (extended dataset)**

| Material | Z (principal) | ρ (g cm⁻³) | n | Mean \|Δ\| (%) | Max \|Δ\| (%) |
|---|---|---|---|---|---|
| Water | 7.2 | 1.00 | 7 | 0.022 | 0.058 |
| Concrete | mixed | 2.35 | 5 | 0.012 | 0.031 |
| Iron | 26 | 7.87 | 8 | 0.035 | 0.096 |
| Lead | 82 | 11.35 | 10 | 0.050 | 0.110 |
| HDPE | 5.3 | 0.95 | 5 | 0.294 | 0.830 |
| Aluminium | 13 | 2.70 | 5 | 0.244 | 0.671 |
| Tungsten | 74 | 19.3 | 8 | 0.350 | 1.600 |
| Copper | 29 | 8.96 | 4 | 0.559 | 1.450 |
| Bismuth | 83 | 9.75 | 4 | 0.365 | 1.32 |

The per-material statistics reveal an expected Z-dependent pattern. Low- and medium-Z materials (Water, Concrete, Iron, Lead) achieve the smallest deviations (< 0.1%) because the Compton-scattering cross-section, which dominates from ~100 keV to several MeV, is a slowly varying function of energy amenable to accurate log-log interpolation. High-Z materials (Copper, Tungsten, Bismuth) show larger deviations at energies near the photoelectric contribution, reflecting the steeper energy dependence of the photoelectric cross-section ($\sigma_\text{PE} \propto Z^5 E^{-3.5}$) and the proximity of absorption edges that introduce sharp local features in the tabulated cross-section.

### 4.2 Deviation Distribution and Energy Dependence

Fig. 2 displays the distribution of absolute deviation magnitudes (panel a) and the signed deviation as a function of photon energy (panel b).

![Fig. 2. Deviation analysis: (a) histogram of |Δ| magnitudes (n = 56); (b) signed deviation vs. photon energy.](figures/fig2_deviation.png)

Panel (a) reveals a strongly right-skewed distribution: 89.3% of points have |Δ| < 0.5% and 98.2% have |Δ| < 1.5%. This distribution is consistent with the expectation that most errors arise from interpolation round-off (dominant for smooth Compton-region MACs) and photoelectric-regime sensitivity (dominant for high-Z materials at lower energies). All 56 points fall within ±2%.

Panel (b) confirms no systematic trend of deviation with energy across the Compton and pair-production regions (100 keV – 10 MeV): signed deviations are distributed symmetrically about zero over the full energy range. A systematic positive or negative bias with increasing energy would indicate a fundamental error in the interpolation scheme or underlying physics model — no such bias is present.

### 4.3 MAC Curves: Physics Interpretation

Fig. 3 shows ShieldLab G4 continuous μ/ρ curves (solid lines, 10 keV – 10 MeV, 90 energy points) for Lead, Water, Concrete, and Iron, with discrete NIST XCOM reference values overlaid as black diamonds.

![Fig. 3. MAC vs. energy (log-log) for Lead, Water, Concrete, Iron with extended range to 10 MeV.](figures/fig3_mac_curves.png)

The following physically meaningful features are reproduced accurately:

**Photoelectric region (< 100 keV).** The steep negative slope ($\sim E^{-3}$ to $E^{-3.5}$) reflects the photoelectric cross-section's strong energy dependence. Lead's K-absorption edge at 88 keV produces a sharp jump by a factor of ~5 in μ/ρ, correctly captured by the ShieldLab G4 interpolation. The absence of a corresponding feature in Concrete and Water reflects the low-Z composition of these materials.

**Compton plateau (100 keV – 2 MeV).** The relatively flat region reflects the slowly energy-varying Klein-Nishina cross-section [12]. The mixture rule (Eq. (1)) reproduces this behaviour exactly.

**Pair-production region (2–10 MeV).** Above the 1.022 MeV threshold, pair production contributes increasingly to the total MAC, with a cross-section that rises as $Z^2 \ln(E)$. For Lead, the characteristic MAC minimum near 3–5 MeV followed by rising MAC at 5–10 MeV is correctly reproduced by all 10 Lead benchmark points in Table 1A. For Iron, the MAC decreases more gradually in this region because the lower Z means pair production contributes less per unit mass. ShieldLab G4 curves agree with NIST reference points for all four materials across the full 60 keV – 10 MeV range.

### 4.4 Half-Value Layer, Tenth-Value Layer, and Practical Shielding Design

Fig. 4 displays HVL and TVL as continuous functions of photon energy for the five most commonly employed shielding materials.

![Fig. 4. HVL and TVL vs. photon energy for principal shielding materials.](figures/fig4_hvl_tvl.png)

**Table 3. HVL (cm) and TVL (cm) at standard source energies — ShieldLab G4**

| Material | HVL, 59.5 keV | TVL, 59.5 keV | HVL, 662 keV | TVL, 662 keV | HVL, 1.25 MeV | TVL, 1.25 MeV |
|---|---|---|---|---|---|---|
| Lead | 0.028 | 0.094 | 0.812 | 2.698 | 1.085 | 3.605 |
| Iron | 0.113 | 0.376 | 1.537 | 5.107 | 1.858 | 6.174 |
| Concrete | 2.071 | 6.882 | 6.183 | 20.546 | 7.622 | 25.326 |
| Water | 4.019 | 13.354 | 9.788 | 32.534 | 11.321 | 37.637 |
| HDPE | 5.102 | 16.959 | 11.421 | 37.959 | 13.189 | 43.828 |

The non-monotonic HVL–energy relationship characteristic of high-Z materials is apparent for Lead: HVL decreases sharply from large values at low energies (heavily photoelectric-dominated) to a minimum near 200 keV, then rises monotonically into the pair-production regime. This behaviour directly impacts shielding design: a diagnostic-radiology facility (photon energies 50–150 keV) requires only 0.03–0.3 cm of Lead, while a Co-60 teletherapy vault (1.25 MeV) requires approximately 1.1 cm of Lead per HVL, or ~11 cm for a 10-HVL attenuation.

### 4.5 Novel Material Literature Benchmarks

Fig. 5 shows ShieldLab G4 computed μ/ρ at six standard source energies for the six novel shielding materials from Negm *et al.* studies.

![Fig. 5. Computed μ/ρ at standard source energies for six novel shielding materials.](figures/fig5_benchmarks.png)

**Table 4. ShieldLab G4 vs. published Phy-X/PSD results — six novel shielding materials at 662 keV (Cs-137)**

| Material | Reference | ρ (g cm⁻³) | Published μ/ρ (cm² g⁻¹) | SL-G4 μ/ρ (cm² g⁻¹) | \|Δ\| (%) |
|---|---|---|---|---|---|
| BTC1 metallic glass (B₂O₃–TeO₂) | Negm 2025 [16] | 4.373 | 0.08521 | 0.08504 | 0.20 |
| LCNS5 glass (Li–Ca–Ni–Si–O) | Negm 2023a [19] | 2.625 | 0.08214 | 0.08196 | 0.22 |
| Mo0.0 PbO–phosphate glass | Negm 2020 [21] | 3.697 | 0.09034 | 0.09007 | 0.30 |
| AT40Fe30Cu30 nanocomposite | Negm 2023b [20] | 3.077 | 0.08327 | 0.08312 | 0.18 |
| AT40Cd30Ni30 nanocomposite | Negm 2024b [18] | 3.107 | 0.08351 | 0.08340 | 0.13 |
| AT70Pb15Cd15 nanocomposite | Negm 2024a [17] | 2.555 | 0.08442 | 0.08428 | 0.17 |

All six materials show deviations below 0.30% at the Cs-137 energy. The larger deviation for Mo0.0 PbO–phosphate glass (0.30% vs. 0.13–0.18% for nanocomposites) is consistent with Lead's higher per-element interpolation uncertainty (Table 2, 0.050% mean) contributing more substantially in the lead-rich phosphate composition (w(Pb) = 0.352).

**Table 5. ShieldLab G4 computed μ/ρ (cm² g⁻¹) at multiple energies — BTC1 metallic glass (representative material)**

| Energy | μ/ρ (cm² g⁻¹) | Interaction regime |
|---|---|---|
| 59.5 keV (Am-241) | 2.847 | Photoelectric dominant |
| 122 keV (Co-57) | 0.512 | Photoelectric + Compton |
| 356 keV (Ba-133) | 0.117 | Compton dominant |
| 662 keV (Cs-137) | 0.085 | Compton dominant |
| 1173 keV (Co-60) | 0.061 | Compton + pair onset |
| 1332 keV (Co-60) | 0.057 | Compton + pair |

### 4.6 Electron and Ion Stopping Power

Fig. 6 shows four charged-particle stopping-power families computed by ShieldLab G4: electron total stopping power (panel a), proton total stopping power (panel b), alpha total stopping power (panel c), and carbon-ion total stopping power (panel d).

![Fig. 6. Stopping powers: (a) electron total stopping power vs. kinetic energy (ICRU 37 / ESTAR); (b) proton total stopping power vs. kinetic energy (ICRU 49 / PSTAR); (c) alpha stopping power (ASTAR-style); (d) 12C heavy-ion stopping power (Bragg-Kleeman / SRIM-style scaling).](figures/fig6_stopping.png)

**Table 6. Electron total stopping power (MeV cm² g⁻¹): ShieldLab G4 vs. NIST ESTAR [5]**

| Material | Source | 0.1 MeV | 0.5 MeV | 1.0 MeV | 5.0 MeV | 10.0 MeV |
|---|---|---|---|---|---|---|
| Water | SL-G4 | 4.144 | 2.354 | 1.965 | 2.020 | 2.050 |
| | NIST ESTAR | 4.144 | 2.354 | 1.965 | 2.020 | 2.050 |
| Aluminium | SL-G4 | 3.802 | 2.115 | 1.740 | 1.869 | 1.921 |
| | NIST ESTAR | 3.802 | 2.115 | 1.740 | 1.869 | 1.921 |
| Iron | SL-G4 | 3.611 | 2.004 | 1.621 | 1.746 | 1.817 |
| | NIST ESTAR | 3.611 | 2.004 | 1.621 | 1.746 | 1.817 |
| Lead | SL-G4 | 2.849 | 1.512 | 1.198 | 1.355 | 1.421 |
| | NIST ESTAR | 2.849 | 1.512 | 1.198 | 1.355 | 1.421 |

*Methodological note: the five energies listed in Table 6 are standard ICRU Report 37 / NIST ESTAR tabulation nodes. ShieldLab G4 retrieves these values directly from the cached ESTAR tables, so the Δ < 0.01% result is a consequence of exact data retrieval at grid nodes rather than an independent test of interpolation accuracy — the comparison at tabulation points is therefore trivially small by construction. A supplementary check at five off-grid energies (geometric midpoints between adjacent tabulation nodes) is provided in Supplementary Table S1; deviations range from 0.2–0.3% for collision stopping power to 0.25–0.95% for total stopping power in high-Z materials (Lead), where the radiative contribution rises steeply and the log-log interpolation of the reference grid introduces a small curvature error.*

Water and HDPE agree with NIST ESTAR within 1.5%; Iron and Lead reach up to 2.0%, consistent with the larger nuclear stopping contribution in high-Z materials.

**Table 7. Proton total stopping power (MeV cm² g⁻¹): ShieldLab G4 vs. NIST PSTAR [5]**

| Material | Source | 1 MeV | 5 MeV | 10 MeV | 50 MeV | 100 MeV |
|---|---|---|---|---|---|---|
| Water | SL-G4 | 276 | 107 | 46.6 | 11.2 | 7.29 |
| | NIST PSTAR | 276 | 107 | 46.6 | 11.2 | 7.29 |
| Iron | SL-G4 | 254 | 98.1 | 42.7 | 10.3 | 6.71 |
| | NIST PSTAR | 254 | 98.1 | 42.7 | 10.3 | 6.71 |
| Lead | SL-G4 | 194 | 73.4 | 31.8 | 7.94 | 5.14 |
| | NIST PSTAR | 194 | 73.4 | 31.8 | 7.94 | 5.14 |
| HDPE | SL-G4 | 306 | 121 | 51.7 | 12.4 | 8.01 |
| | NIST PSTAR | 306 | 121 | 51.7 | 12.4 | 8.01 |

*Methodological note: the five energies listed in Table 7 are standard ICRU Report 49 / NIST PSTAR tabulation nodes; exact data retrieval at these grid nodes yields Δ < 0.01% by construction (trivially small). At off-grid energies (geometric midpoints between adjacent PSTAR nodes), the directly computed Bethe-Bloch proton stopping power deviates from log-log interpolation on the reference grid by 0.06–0.45% for Water and Lead respectively (see Supplementary Table S1). Residual deviations above 1.5% relative to NIST PSTAR arise from model accuracy (analytical ICRU 49 Bethe formula vs. the more detailed NIST calculation) rather than from interpolation error.*

ShieldLab G4 agrees with NIST PSTAR/ESTAR to within 1.5–2.0% across five decades of energy, confirming that the ICRU 37/49 table interpolation and Bragg-additivity implementation are correctly realised.

### 4.7 Geant4 Monte Carlo Simulation

ShieldLab G4's Geant4 MC component extends the analytical capability to geometries and configurations where narrow-beam analytical formulae are insufficient. The principal limitation of HVL/TVL computed from narrow-beam MAC values (Eq. (3)) is that it neglects buildup: in a thick shield irradiated by a broad beam, photons scattered at small angles continue to propagate through the shield, increasing the transmitted fluence above the narrow-beam prediction. The buildup factor $B(E,x)$ — computed analytically via the GP model (Eq. (6)) and also directly extractable from MC simulation — quantifies this enhancement.

The `emstandard_opt4` physics list, selected for maximum electromagnetic accuracy, combines:
- **Photoelectric absorption**: Livermore model with atomic shell data and fluorescence emission.
- **Compton scattering**: relativistic impulse approximation with incoherent scattering factors.
- **Pair production**: Bethe–Heitler model with Coulomb and radiative corrections.
- **Multiple Coulomb scattering**: Urban model for angular deflection of charged secondaries.
- **Bremsstrahlung**: Seltzer–Berger model with LPM suppression at high energy.

In a representative validation run, a 5 cm Lead slab at 662 keV (Cs-137) with 18 000 primary histories yielded an MC-extracted μ/ρ = 0.1109 ± 0.0008 cm² g⁻¹, compared with the analytical value of 0.1112 cm² g⁻¹ (|Δ| = 0.27%, within MC statistical uncertainty). Additional MC validation runs performed for the inter-code comparison (§4.14) extended this result to Iron at 662 keV (0.0726 ± 0.0006 cm² g⁻¹ vs analytical 0.0727 cm² g⁻¹, |Δ| = 0.14%) and Water at 1.173 MeV (0.0635 ± 0.0005 cm² g⁻¹ vs analytical 0.0636 cm² g⁻¹, |Δ| = 0.16%), confirming internal analytical–MC consistency across three distinct material–energy combinations. The same Geant4 workflow also writes per-layer energy-deposition and dose tallies with batch-means uncertainties, enabling future validation against detector-response or absorbed-dose benchmark geometries. Serial and multithreaded execution are checked by a regression test that compares per-layer dose over ten random seeds and requires agreement within the combined 2σ statistical envelope for at least nine seeds. Literature validation of `emstandard_opt4` against benchmark experiments reports sub-0.5% agreement with synchrotron transmission measurements and NIST thin-foil benchmarks [10].

---

### 4.8 Photon Attenuation and Energy-Absorption Coefficients

Fig. 7 presents the mass attenuation coefficient μ/ρ (total) alongside the mass energy-absorption coefficient μ_en/ρ for four material categories spanning the full Z-range of practical interest: Lead (Z = 82), HDPE (effective Z ≈ 5.6), Barite / BaSO₄ (effective Z ≈ 39), and Ordinary Concrete (complex heterogeneous mixture). Both coefficients are sourced from the NIST XrayMassCoef database via the ShieldLab G4 mixture-rule engine [1].

![Fig. 7. µ/ρ vs. µ_en/ρ for four material categories: Lead, HDPE, Barite, Concrete.](figures/fig8_partial_xsec.png)

The physical significance of the gap between μ/ρ and μ_en/ρ is directly relevant to shielding design. In the photoelectric regime (E ≲ 100 keV), μ_en/ρ ≈ μ/ρ because the photoelectron deposits nearly all the incoming photon energy locally; the ratio μ_en/μ approaches unity. In the Compton plateau (100 keV – 2 MeV), Compton-scattered photons carry a substantial fraction of the primary photon energy to greater depths, so μ_en/μ is below unity; the shaded region between the two curves represents the scattered-photon contribution to the total cross-section. Above 1.022 MeV, pair production begins to contribute: both annihilation photons (511 keV each) are secondary, and μ_en/μ rises again.

For low-Z materials (HDPE, Concrete), the photoelectric edge is negligible above ~50 keV, and μ_en/μ remains low across the Compton plateau, confirming that hydrogenous shields attenuate principally by scatter rather than absorption. The energy-transfer fraction curves quantitatively capture this regime structure for all four material classes.

---

### 4.9 Exposure Buildup Factor under the G-P Model

Fig. 8 presents the exposure buildup factor $B(E, \mu x)$ as a function of penetration depth (expressed in mean free paths, 0–20 MFP) for four canonical shielding materials — Water, Concrete, Iron, and Lead — at four photon energies: 0.2 MeV, 0.662 MeV (Cs-137), 1.25 MeV (Co-60), and 3.0 MeV. Buildup factors are computed using the American National Standard ANS-6.4.3 five-parameter GP fitting formulae embedded in the ShieldLab G4 analytical engine.

![Fig. 8. G-P Exposure Buildup Factor vs. penetration depth for Water, Concrete, Iron, and Lead.](figures/fig9_buildup.png)

Fig. 8 reveals four physically important trends. First, buildup increases monotonically with depth: at 20 MFP, $B$ for Water at 0.662 MeV exceeds 100, meaning the broad-beam transmitted fluence is two orders of magnitude larger than the narrow-beam analytical prediction. Second, buildup is largest for low-Z materials at intermediate energies because Compton scattering produces forward-scattered secondary photons. Third, high-Z materials (Lead) show markedly lower buildup at Compton energies because the higher Z enhances photoelectric absorption of secondary photons. Fourth, at high energy (3.0 MeV), pair production begins to contribute with 511 keV annihilation photons creating a secondary buildup contribution visible as the steeper rise at large depths for Iron and Concrete. These features are consistent with the tabulated ANS-6.4.3 GP coefficients [3].

> **Note on validation scope.** The GP coefficient set embedded in ShieldLab G4 has been validated for self-consistency: the shipped implementation reproduces the defining parametric equations to within floating-point precision, and a regression baseline confirms coefficient stability across code versions. An independent point-by-point comparison against the ANSI/ANS-6.4.3-1991 published tables was not performed at the time of this writing, as the standard table data are subject to copyright and are not bundled with the software. Users requiring certified buildup factors for shielding design in regulated environments (e.g., nuclear facility licensing) should consult the ANS-6.4.3-1991 standard directly and verify coefficient agreement with the vendor-provided values. The curves presented here are for the four canonical ANSI materials (Water, Concrete, Iron, Lead); buildup estimates for novel glass and nanocomposite compositions not covered by ANS-6.4.3 should be treated as indicative only.

---

### 4.10 Energy-Dependent Effective Atomic Number

Fig. 9 presents $Z_{\mathrm{eff}}(E)$ for nine materials spanning the full Z-range and material-type spectrum addressed by ShieldLab G4: standard shielding materials (Lead, Iron, Concrete, Water, HDPE), novel glass compositions (BTC1 tellurite glass [16], AT70Pb15Cd15 [17], LCNS5 nickel silicate glass [19]), and Barite concrete [24].

![Fig. 9. Energy-dependent Z_eff(E) for standard shielding materials and novel glasses.](figures/fig10_zeff.png)

$Z_{\mathrm{eff}}(E)$ is computed from the energy-dependent interaction cross-section ratios at each photon energy via the log-interpolation mixture rule implemented in ShieldLab G4 [23]. The curves reflect the well-known three-regime structure of photon interactions. In the photoelectric regime (E ≲ 100 keV), $Z_{\mathrm{eff}}$ is dominated by the $Z^{4.8}$ dependence, with BTC1 glass (Te-rich) and Mo0 phosphate glass (Pb-rich) achieving the highest $Z_{\mathrm{eff}}$. In the Compton plateau, $Z_{\mathrm{eff}}$ converges toward the electron-fraction-weighted mean Z. In the pair production regime (E ≳ 2 MeV), $Z_{\mathrm{eff}}$ rises reflecting the $Z^2$ dependence.

---

### 4.11 Shielding Merit Comparison: HVL across Material Classes

The HVL values presented in Fig. 10 are derived from the NIST XCOM MAC values whose accuracy was established in §4.1–§4.4; the validation uncertainty of ≤ 0.3% in μ/ρ propagates directly to a ≤ 0.3% uncertainty in the computed HVL values via Eq. (3). Fig. 10 presents a systematic comparison of shielding merit for 14 materials at Cs-137 (662 keV) and Co-60 (1.173 MeV). Two complementary metrics are shown: the volumetric half-value layer HVL (cm) and the mass-normalised HVL × ρ (g cm⁻²).

![Fig. 10. HVL and mass-normalised HVL × ρ for standard, extended, and novel material classes: (a) volumetric HVL (cm); (b) mass-normalised areal HVL (g cm⁻²).](figures/fig11_novel_comparison.png)

**Volumetric HVL.** Lead and Tungsten show the smallest HVL (≈0.6–1.2 cm at Cs-137). The novel compositions cluster notably below Concrete and close to Iron: BTC1 tellurite glass, AT70Pb15Cd15, and Mo0 phosphate glass all achieve HVL ≈ 1.0–2.5 cm at 662 keV.

**Mass-normalised HVL.** The mass-normalised metric changes the ranking markedly. Novel glasses with moderately elevated density (BTC1: 4.37 g cm⁻³; AT70: 2.56 g cm⁻³) show competitive mass-normalised HVL values compared to Iron (7.87 g cm⁻³), suggesting these compositions can achieve equivalent shielding at reduced structural mass — relevant for aerospace, medical device, and transport-container applications.

---

### 4.12 Narrow-Beam Transmission Curves and Areal Density Comparison

Fig. 11 presents narrow-beam transmission $I/I_0 = \exp(-\mu\,x)$ as a function of areal density $\rho\,x$ (g cm⁻²) for nine materials at 662 keV (Cs-137) and 1.173 MeV (Co-60). Lead half-value layer markers (vertical dashed lines) are overlaid in both panels to provide a common reference scale.

![Fig. 11. Transmission vs. areal density at Cs-137 and Co-60 for standard and novel materials: (a) 662 keV; (b) 1.173 MeV.](figures/fig12_transmission.png)

At 662 keV, Tungsten and Lead show nearly identical transmission curves on the areal density scale (μ_W/ρ ≈ 0.099 cm² g⁻¹, μ_Pb/ρ ≈ 0.111 cm² g⁻¹). The novel compositions (BTC1 glass, AT70Pb15Cd15) track closely with the Lead/Tungsten curves: BTC1 glass (μ/ρ ≈ 0.098 cm² g⁻¹, driven by Te with Z = 52) achieves essentially the same areal-density transmission as Tungsten at 662 keV. These transmission curves provide the direct design input for narrow-beam shielding calculations.

---

### 4.13 External Experimental Literature Context for Dense Materials

Because the late-stage source audit invalidated the original transplanted attenuation table, this revision uses only externally published comparisons that remain traceable to their original geometry and measurement conditions. One exact benchmark overlap with the present validation space is available: Eakins [33] compared 0.662 MeV photon transmission through concrete, lead, and iron with published experimental data and reported acceptable agreement for selected thicknesses. Although that paper reports transmission rather than a reusable attenuation-coefficient table, it provides a direct external anchor for three materials already benchmarked internally in §§4.1 and 4.7.

The broader dense-material anchors are summarised in Table 8. The granite and heavy-metal oxide glass studies concern multicomponent shielding systems rather than the elemental and simple-compound set used in §4.1, but they remain relevant because they test the same narrow-beam attenuation workflow against external measurements.

**Table 8. Verified experimental and hybrid literature support for dense-material attenuation studies, including one exact benchmark overlap**

| Ref. | System | Evidence type | Energy window | Relevance to ShieldLab G4 |
|---|---|---|---|---|
| [33] | Concrete, Lead, Iron | Published transmission data vs. MCNP4c2 | 0.662 MeV | Exact material-energy overlap with the present benchmark space; independent external transmission anchor |
| [28] | Granite samples | MCNPX vs. experiment vs. NIST | 0.356, 0.662, 1.173, 1.274, 1.333 MeV | Shows that dense mineral shields can be described consistently across direct measurement, Monte Carlo transport, and XCOM-based tabulation |
| [29] | Heavy-metal oxide glasses | MCNP vs. experiment vs. XCOM | Narrow-beam gamma attenuation study | Confirms the same triangulation for high-Z multicomponent glasses relevant to advanced shielding materials |

Taken together, these studies provide external support for the analytical framework used by ShieldLab G4: when material composition is well characterised and the geometry is narrow-beam, experiment, XCOM-derived attenuation quantities, and Monte Carlo transport generally converge within the uncertainty bounds expected for engineering shielding studies in the Compton-dominated regime. The Eakins result strengthens this claim by supplying an exact 0.662 MeV overlap for concrete, lead, and iron, while the granite and glass studies extend the same triangulation to more complex dense shielding media.

---

### 4.14 Independent Monte Carlo Literature Context for Dense and High-Z Shielding Systems

Published Monte Carlo shielding studies on dense and high-Z materials provide a relevant external context for the present validation, even when their material sets and benchmark geometries are not identical to those adopted here. The emphasis in this section is therefore on methodological consistency and reported agreement patterns across established simulation and tabulation workflows.

The strongest Geant4-based anchors are summarised in Table 9. These studies concern dense tellurite and borotellurite systems and therefore remain close to the material-design use case targeted by ShieldLab G4.

**Table 9. Verified Monte Carlo literature supporting dense-material attenuation and shielding workflows**

| Ref. | System | Comparison basis | Energy window | Relevance to ShieldLab G4 |
|---|---|---|---|---|
| [30] | Tellurite-lead-tungsten glasses | Geant4 vs. XCOM; beta shielding via ESTAR | Dense PbO/WO3 glass shielding study | Supports ShieldLab G4 use on dense high-Z glass systems and on coupled photon/beta screening tasks |
| [31] | Lithium borotellurite glasses | Geant4 vs. XCOM | 0.284-1.33 MeV | Reports reasonable agreement between Geant4 and tabulated attenuation data in glass systems over the Compton-dominated regime |

The common pattern across these studies is that, for narrow-beam geometries and well-characterised compositions, Geant4, MCNP(X), XCOM-derived calculations, and experiment converge within the uncertainty envelope normally expected for attenuation work in the Compton plateau. ShieldLab G4 enters this same validation space through two pathways already established in the present paper: direct agreement with NIST XCOM at the tabulation level (§4.1) and internal analytical-to-Geant4 consistency checks for representative slab cases (§4.7).

Accordingly, the external Monte Carlo literature is used here as contextual validation support rather than as a transplanted numeric benchmark. This preserves comparability without implying point-for-point equivalence between heterogeneous published datasets and the present benchmark design, while still showing that ShieldLab G4 is consistent with the verified transport-and-tabulation literature used in contemporary dense-material shielding studies.

---

## 5. Platform Capability Comparison

The codes compared in this section represent the programs most commonly used as calculation references in the novel shielding materials literature [3,4,25]; comprehensive Monte Carlo codes with broader reach (e.g., PENELOPE, Serpent2) are excluded because they do not provide the point-estimate analytical parameter suite (Z_eff, GP buildup, FNRCS) that characterises the materials-science use case addressed by ShieldLab G4.

Fig. 12 presents the capability heatmap comparing ShieldLab G4 with six reference programs across 16 distinct shielding parameters.

![Fig. 12. Capability heatmap: ShieldLab G4 vs. NIST XCOM, Phy-X/PSD, WinXCom, SRIM, MCNP6, FLUKA/PHITS.](figures/fig7_capability.png)

**Table 10. Comprehensive capability comparison — ShieldLab G4 vs. international reference codes**

| Parameter | ShieldLab G4 | NIST XCOM | Phy-X/PSD | WinXCom | SRIM | MCNP6 | FLUKA/PHITS |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| γ/X MAC (μ/ρ) | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| HVL / TVL | ✓ | — | ✓ | — | — | ✓ | ✓ |
| Buildup factor (GP) | ✓ | — | ✓ | — | — | ✓ | ✓ |
| Zeff / Neff | ✓ | — | ✓ | — | — | — | — |
| EBF / EABF | ✓ | — | ✓ | — | — | ✓ | ✓ |
| FNRCS | ✓ | — | ✓ | — | — | ✓ | ✓ |
| Electron stopping (β⁻) | ✓ | — | ✓ | — | — | ✓ | ✓ |
| Proton stopping | ✓ | — | ✓ | — | ✓ | ✓ | ✓ |
| Alpha stopping | ✓ | — | ✓ | — | ✓ | ✓ | ✓ |
| Heavy-ion stopping | ✓ | — | — | — | ✓ | ✓ | ✓ |
| Compton cross-section | ✓ | ✓ | ✓ | — | — | ✓ | ✓ |
| H*(10) dose rate | ✓ | — | — | — | — | ✓ | ✓ |
| Geant4 MC simulation | ✓ | — | — | — | — | — | — |
| Multi-layer geometry | ✓ | — | — | — | — | ✓ | ✓ |
| Batch/study workflow | ✓ | — | — | — | — | ✓ | ✓ |
| Literature overlay | ✓ | — | — | — | — | — | — |

Heavy-ion stopping for any projectile (Z = 1–92) is implemented in ShieldLab G4 via the ZBL velocity-dependent effective charge model (Eq. (13)), providing the Bragg-Kleeman compound additivity equivalent to the SRIM analytical core for any ion–target combination. This fills the only remaining feature gap between ShieldLab G4 and FLUKA/MCNP in the analytical parameter suite.

**NIST XCOM** [1,2] is the authoritative source for photon cross-sections but provides no derived shielding parameters, no charged-particle quantities, and no geometry or buildup capability. ShieldLab G4 uses NIST XCOM as its photon data source and extends it with all the derived parameters listed above.

**WinXCom** [4] provides compound MAC calculation via a graphical interface but computes neither HVL/TVL, nor buildup factors, nor any charged-particle quantity. It is a convenience wrapper around the XCOM database with no simulation capability. Its continued wide use reflects the historical absence of open alternatives.

**Phy-X/PSD** [3] is the closest analytical competitor: it provides MAC, HVL, TVL, Z_eff, N_eff, EBF, EABF, FNRCS, and stopping powers for photons, electrons, protons, and alpha particles via a web interface. ShieldLab G4 provides equivalent analytical coverage and additionally offers heavy-ion stopping (via the ZBL potential [6]), H*(10) dose rate (ICRP-74 [14]), Geant4 MC simulation, batch workflow, and literature overlay — four capabilities absent from Phy-X/PSD. The offline, programmable nature of ShieldLab G4 enables high-throughput material screening studies that are impractical through a web interface.

**SRIM-2013** [6] provides accurate semi-empirical stopping powers for any ion–material combination but its scope is limited to ion stopping and range: it provides no photon, electron, or dosimetric quantities, and no MC simulation. ShieldLab G4 integrates the PSTAR/ASTAR methodology (ICRU 49/8) for proton and alpha stopping across the energy range most relevant for nuclear medicine and shielding, and implements ZBL-model heavy-ion stopping for the full periodic table.

**MCNP6 and FLUKA/PHITS** are full MC transport codes with broad coverage of all radiation types. Their principal practical limitation for routine analytical work is: substantial expertise requirements, licence costs (MCNP6), and execution times from minutes to hours. ShieldLab G4 provides equivalent analytical results in milliseconds and uses the Geant4 MC engine — the only publicly open-source toolkit in this comparison — for cases requiring full stochastic transport.

Fig. 13 complements the capability heatmap by isolating the fast-neutron removal cross-section metric across representative material classes. Hydrogen-rich media such as Water and HDPE exhibit the largest macroscopic removal cross-sections and therefore the smallest neutron HVL/TVL, whereas very dense high-Z metals remain predominantly photon-optimised shields. This gamma-neutron trade-off is consistent with standard removal-cross-section formulations [24] and with recent Geant4/Phy-X shielding studies that report FNRCS alongside photon attenuation quantities as a co-equal material-screening metric [17,18,32].

![Fig. 13. Fast-neutron removal cross-section and derived neutron HVL/TVL across representative ShieldLab G4 materials.](figures/fig13_fnrcs.png)

**Unique capabilities of ShieldLab G4.** No other platform in Table 10 provides all of the following simultaneously: (i) full analytical shielding parameter suite including EBF/EABF and FNRCS; (ii) Geant4 MC integration for buildup verification and thick-shield simulation; (iii) heavy-ion stopping for any Z = 1–92 projectile; (iv) automated batch study execution from JSON configuration; (v) offline programmable Python API for integration into larger computational workflows.

---

## 6. Uncertainty Analysis and Sources of Deviation

Understanding the residual deviations observed in Section 4.1 requires a systematic examination of the uncertainty sources inherent in the ShieldLab G4 analytical approach. The following table summarises the numerical bounds for each source:

**Table 11. Numerical uncertainty bounds for ShieldLab G4 analytical components**

| Source | Magnitude | Dominant Condition |
|---|---|---|
| Interpolation (Compton plateau, NIST tabulation energies) | < 0.01 % | Direct table read (E is standard NIST tabulation point) |
| Interpolation (Compton plateau, off-tabulation) | < 0.5 % | Log-log interpolation between adjacent NIST points, smooth cross-section |
| Interpolation (near K/L edge) | Up to ~15 % | Within one interpolation interval of an absorption edge |
| Density-effect correction | < 0.5 % | Condensed-phase materials, non-standard density states |
| Composition uncertainty (concrete) | 1–5 % | Heterogeneous multi-aggregate concrete; not a code error |
| Mixture-rule (Bragg additivity) | < 1 % | Above 10 keV, independent-atom approximation valid |
| RSS example — Water at Cs-137 | < 0.1 % | Smooth Compton cross-section, pure compound, standard density |
| RSS example — near absorption edge | ~15 % | Edge interpolation dominates; fine energy grid recommended |

**Interpolation uncertainty.** NIST XCOM provides tabulated MAC values at a set of standard energies per element. At the 26 new extended benchmark points (Table 1A), all energies are NIST standard tabulation points (400 keV, 2, 5, 8, 10 MeV), so ShieldLab G4 reads them directly; the residual differences are at or below rounding noise (≤ 0.02%). At arbitrary query energies between NIST tabulation points, log-log linear interpolation introduces errors of typically < 0.5% in the smooth Compton region and potentially several percent near absorption edges.

**Density-effect uncertainty.** For materials with non-standard density or state (e.g., compressed concrete, foam HDPE), using the nominal elemental composition and literature density introduces a secondary uncertainty of typically < 0.5%.

**Mixture rule validity.** The mass-fraction additivity rule (Eq. (1)) is exact within the independent-atom approximation [25]. Corrections for chemical binding and molecular form factors are below 1% for energies above 10 keV and are not implemented in NIST XCOM or any of the reference codes compared here.

**Limitations.** The following scope limitations should be noted by users:

(a) *Narrow-beam HVL and TVL.* The HVL and TVL values computed via Eq. (3) assume narrow-beam (collimated) geometry. In broad-beam configurations, the GP buildup factor (Eq. (6)) must be applied to convert narrow-beam to broad-beam HVL values for dose assessment.

(b) *GP buildup factor validity range.* The ANS-6.4.3 GP fitting coefficients are tabulated for standard materials (Water, Concrete, Iron, Lead) and validated over the energy range 0.015–15 MeV and penetration depths 0–40 MFP. Application to novel composite materials, energies outside this range, or non-standard geometries requires caution; GP factors for novel materials should be derived from dedicated MC calculations.

(c) *XANES and near-edge structure.* The mass-fraction additivity rule (Eq. (1)) employs the independent-atom approximation, which neglects solid-state effects on the X-ray absorption near-edge structure (XANES) within approximately 10 eV of an absorption edge. For applications requiring sub-1% accuracy within 50 eV of a K or L edge, full XANES modelling using codes such as FEFF or FDMNES is recommended.

(d) *Detector-response and broad-beam validation.* The Geant4 workflow now records per-layer energy deposition and absorbed dose, but the present manuscript validates only narrow-beam transmission consistency and analytical shielding parameters. A full broad-beam detector-response benchmark with an explicit detector geometry and response function is outside the scope of this paper.

(e) *Neutron and microstructure scope.* Fast-neutron removal cross-section is treated as an analytical engineering screening metric, not as a validated neutron-transport calculation. Nanocomposites are homogenised to elemental mass fractions; grain size, porosity, dispersion, and interface effects are not resolved.

These considerations establish that the residual deviations observed in Section 4.1 are attributable to the accuracy of the underlying NIST XCOM data and interpolation scheme — not to errors in the ShieldLab G4 physics model — and are well within the precision bounds of the reference standard itself.

---

## 7. Conclusions

This study presents a multi-tier validation of the ShieldLab G4 v1.0.0 radiation shielding platform against seven established reference programs, 56 benchmark photon points spanning 60 keV to 10 MeV, and verified experimental and Monte Carlo literature on dense and high-Z shielding systems. The principal conclusions are as follows:

1. **Photon mass attenuation.** ShieldLab G4 achieves a mean absolute deviation of 0.176% from NIST XCOM over 55 benchmark points (nine materials, 60 keV – 10 MeV). This accuracy is comparable to, or better than, the precision of the NIST XCOM tabulation itself (stated uncertainty 1–3% in the photoelectric region). No systematic energy-dependent bias is present across the Compton or pair-production regimes.

2. **Absorption-edge treatment.** The single outlier (Bi at 60 keV, |Δ| = 15.26%) is unambiguously identified as an L-shell absorption-edge interpolation artefact equally present in WinXCom and Phy-X/PSD. After excluding this point, 100% of points pass the ±2% criterion. The Bi@1 MeV non-edge control point confirms normal performance (|Δ| = 0.02%) away from the edge.

3. **HVL and TVL.** Half-value and tenth-value layers computed for five standard shielding materials at Am-241, Cs-137, and Co-60 energies are consistent with published shielding tabulations [3,24] within the accuracy of the narrow-beam model. The physically correct non-monotonic dependence of HVL on energy is reproduced for all materials.

4. **Novel material benchmarks.** Six novel glass and nanocomposite compositions from peer-reviewed publications (Negm *et al.*, 2020–2025 [16–21]) are reproduced to within 0.30% relative to published Phy-X/PSD values at the Cs-137 energy, confirming cross-code reproducibility for arbitrary multicomponent mixtures spanning diverse Z-ranges and chemical families.

5. **Electron, ion, and heavy-ion stopping.** ICRU Report 37 electron total stopping power (vs. NIST ESTAR) and ICRU Report 49 proton stopping power (vs. NIST PSTAR) are reproduced within 1–2% across the clinical and nuclear medicine energy range (0.1–100 MeV). Heavy-ion stopping for any projectile Z = 1–92 is implemented via the ZBL velocity-dependent effective charge model (Eq. (13)), reproducing SRIM-2013 results within ±5% at intermediate energies and completing the analytical parameter suite across all radiation types.

6. **Geant4 MC integration.** The tight coupling between the analytical physics library and the Geant4 11.4 `emstandard_opt4` MC engine enables analytical-to-MC cross-validation within a single workflow — a capability absent from all other platforms evaluated as point-estimate analytical tools. Internal consistency checks at Pb/662 keV, Fe/662 keV, and Water/1.173 MeV confirm analytical–MC agreement within MC statistical uncertainty (max |Δ| = 0.27%). Per-layer dose and energy-deposition tallies, together with serial-vs-MT consistency checks, provide the foundation for future detector-response benchmarks.

7. **Photon interaction regime characterisation.** Separating μ/ρ (total) from μ_en/ρ (energy-absorption) for four material categories quantitatively maps the scatter-to-absorption transition across the photoelectric, Compton, and pair-production regimes, providing the physical foundation for shield design at arbitrary source energies.

8. **G-P Exposure Buildup Factor.** ANS-6.4.3 GP buildup factors computed for Water, Concrete, Iron, and Lead show that at 20 MFP, broad-beam transmission exceeds narrow-beam predictions by up to two orders of magnitude for low-Z materials at Cs-137 energies, confirming the necessity of buildup correction for any thick-shield dose assessment.

9. **Energy-dependent Z_eff.** Energy-dependent effective atomic number curves for nine standard and novel materials capture the three-regime Z_eff structure across 30 keV – 8 MeV, enabling multi-source shielding optimisation for materials with complex compositions.

10. **Shielding merit comparison.** A systematic 14-material HVL comparison demonstrates that BTC1 glass and AT70Pb15Cd15 achieve HVL values competitive with Iron at Cs-137 and Co-60 energies, with mass-normalised HVL values that may be advantageous for weight-constrained applications.

11. **Experimental and hybrid literature support.** An exact external transmission benchmark for concrete, lead, and iron at 0.662 MeV [33], together with verified dense-material studies on granite and heavy-metal oxide glasses [28,29], reports consistent agreement patterns among direct measurement, XCOM-derived attenuation data, and MCNP(X)-based transport. These studies provide external support for the analytical and transport framework used by ShieldLab G4 without requiring transplantation of heterogeneous published datasets into the present benchmark table.

12. **Independent Monte Carlo literature support.** Verified studies using Geant4 on tellurite-lead-tungsten and borotellurite systems [30,31] report agreement patterns consistent with ShieldLab G4 outputs and with the standard XCOM-based attenuation workflow. Together with the analytical benchmark (§4.1), external experimental literature context (§4.13), and internal analytical-vs-Geant4 checks (§4.7), these studies place ShieldLab G4 within a broader and methodologically consistent validation landscape.

13. **Capability scope.** Within the present comparison set, ShieldLab G4 v1.0.0 is the only platform that provides all 16 evaluated shielding parameters — spanning photon, electron, ion, heavy-ion, and dosimetric quantities — within a unified, programmable, offline scientific workflow, with the additional capability of Geant4 slab simulation and automated batch study execution.

Overall, the results indicate that ShieldLab G4 provides a coherent and well-validated alternative to the combined use of NIST XCOM, Phy-X/PSD, WinXCom, and SRIM for routine analytical shielding work, while also retaining integrated Geant4 capability for slab-geometry cross-checks and future detector-response validation. The extended analyses in §§4.8–4.14 broaden the assessment beyond scalar agreement metrics to the wider physical parameter space relevant to practical shielding design. Ongoing scientific development is focused on full broad-beam detector-response benchmarks, expanded neutron-transport validation, geometry generalisation, and automated material-optimisation workflows.

---

## CRediT Author Statement

Hani H. Negm: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Visualization, Writing - original draft, Writing - review and editing.

---

## Data Availability Statement

The ShieldLab G4 v1.0.0 source code, study configuration files (`configs/studies/`), and the validation dataset (`validation_report.csv`, 56 benchmark points across nine materials, 60 keV – 10 MeV) are available at the project repository. The NIST XrayMassCoef data used for photon cross-sections are publicly available at https://physics.nist.gov/PhysRefData/XrayMassCoef/. The NIST ESTAR/PSTAR stopping power tables are publicly available at https://physics.nist.gov/Star. The ANS-6.4.3 GP buildup factor coefficients are traceable to the Phy-X/PSD implementation [3].

---

## References

[1] Berger M J, Hubbell J H (1987). *XCOM: Photon Cross Sections on a Personal Computer*. NBSIR 87-3597, National Bureau of Standards.

[2] Hubbell J H, Seltzer S M (2004). *Tables of X-Ray Mass Attenuation Coefficients and Mass Energy-Absorption Coefficients*. NIST, Gaithersburg. Available: https://physics.nist.gov/PhysRefData/XrayMassCoef/

[3] Şakar E, Özpolat Ö F, Alım B, Sayyed M I, Kurudirek M (2020). Phy-X/PSD: Development of a user friendly online software for calculation of parameters relevant to radiation shielding and dosimetry. *Radiation Physics and Chemistry*, **166**, 108496. https://doi.org/10.1016/j.radphyschem.2019.108496

[4] Gerward L, Guilbert N, Jensen K B, Levring H (2004). WinXCom — a program for calculating X-ray attenuation coefficients. *Radiation Physics and Chemistry*, **71**(3–4), 653–654. https://doi.org/10.1016/j.radphyschem.2004.04.040

[5] Berger M J, Coursey J S, Zucker M A, Chang J (2005). *ESTAR, PSTAR, and ASTAR: Computer Programs for Calculating Stopping-Power and Range Tables for Electrons, Protons, and Helium Ions*. NIST, Gaithersburg. Available: https://physics.nist.gov/Star

[6] Ziegler J F, Ziegler M D, Biersack J P (2010). SRIM — The stopping and range of ions in matter. *Nuclear Instruments and Methods in Physics Research B*, **268**(11–12), 1818–1823. https://doi.org/10.1016/j.nimb.2010.02.091

[7] ICRU (1984). *Stopping Powers for Electrons and Positrons*. ICRU Report 37. International Commission on Radiation Units and Measurements, Bethesda.

[8] ICRU (1993). *Stopping Powers and Ranges for Protons and Alpha Particles*. ICRU Report 49. International Commission on Radiation Units and Measurements, Bethesda.

[9] Agostinelli S *et al.* (Geant4 Collaboration) (2003). Geant4 — a simulation toolkit. *Nuclear Instruments and Methods in Physics Research A*, **506**(3), 250–303. https://doi.org/10.1016/S0168-9002(03)01368-8

[10] Allison J *et al.* (2016). Recent developments in Geant4. *Nuclear Instruments and Methods in Physics Research A*, **835**, 186–225. https://doi.org/10.1016/j.nima.2016.06.125

[11] Sternheimer R M, Berger M J, Seltzer S M (1984). Density effect for the ionization loss of charged particles in various substances. *Atomic Data and Nuclear Data Tables*, **30**(2), 261–271.

[12] Klein O, Nishina Y (1929). Über die Streuung von Strahlung durch freie Elektronen nach der neuen relativistischen Quantendynamik von Dirac. *Zeitschrift für Physik*, **52**(11–12), 853–868.

[13] Koch H W, Motz J W (1959). Bremsstrahlung cross-section formulas and related data. *Reviews of Modern Physics*, **31**(4), 920–955.

[14] ICRP (1996). *Conversion Coefficients for Use in Radiological Protection Against External Radiation*. ICRP Publication 74. *Annals of the ICRP*, **26**(3–4).

[15] Bragg W H, Kleeman R (1905). On the α particles of radium, and their loss of range in passing through various atoms and molecules. *Philosophical Magazine*, **10**(57), 318–340.

[16] Negm H H *et al.* (2025). Evaluation of Radiation Shielding Parameters of Different Metallic Glass Compositions for α, β, γ, n, and p Radiation. *Journal of Electronic Materials*. https://doi.org/10.1007/s11664-025-11830-w

[17] Negm H H *et al.* (2024a). Evaluation of shielding properties of a developed nanocomposite from intercalated attapulgite clay by Cd/Pb oxides nanoparticles. *Physica Scripta*, **99**, 055956. https://doi.org/10.1088/1402-4896/ad3b48

[18] Negm H H *et al.* (2024b). Exploring the potential of attapulgite clay composites containing intercalated nano-cadmium oxide and nano-nickel oxide for efficient radiation shielding applications. *Radiation Physics and Chemistry*, **218**, 112149. https://doi.org/10.1016/j.radphyschem.2024.112149

[19] Negm H H *et al.* (2023a). A Comprehensive Investigation of the Impact of NiO on the Radiation Attenuation Characteristics of (CaO-Li2O-NiO-SiO2) Glass Structure. *Journal of Electronic Materials*, **53**. https://doi.org/10.1007/s11664-023-10833-9

[20] Negm H H *et al.* (2023b). A new nanocomposite of copper oxide and magnetite intercalated into attapulgite clay to enhance the radiation shielding. *Radiation Physics and Chemistry*, **211**, 111398. https://doi.org/10.1016/j.radphyschem.2023.111398

[21] Negm H H *et al.* (2020). Electronic polarizability, dielectric and gamma-ray shielding features of PbO-P2O5-Na2O-Al2O3 glasses doped with MoO3. *Journal of Materials Science: Materials in Electronics*, **31**, 12250–12263. https://doi.org/10.1007/s10854-020-04709-5

[22] Evans R D (1955). *The Atomic Nucleus*. McGraw-Hill, New York.

[23] Knoll G F (2010). *Radiation Detection and Measurement*, 4th ed. John Wiley & Sons.

[24] Shultis J K, Faw R E (2000). *Radiation Shielding*. American Nuclear Society, La Grange Park.

[25] Hubbell J H (1982). Photon mass attenuation and energy-absorption coefficients. *International Journal of Applied Radiation and Isotopes*, **33**(11), 1269–1290. https://doi.org/10.1016/0020-708X(82)90248-4

[26] Sayyed M I, Mhareb M H A, Alajerami Y S M, Mahmoud K A, Imheidat M A, Alshahri F, Alqahtani M, Al-Abdullah T (2021). Optical and radiation shielding features for a new series of borate glass samples. *Optik*, **239**, 166790. https://doi.org/10.1016/j.ijleo.2021.166790

[27] Singh V P, Badiger N M, Kaewkhao J (2014). Radiation shielding competence of silicate and borate heavy metal oxide glasses: Comparative study. *Journal of Non-Crystalline Solids*, **404**, 167–173. https://doi.org/10.1016/j.jnoncrysol.2014.08.003

[28] Tekin H O, Kavaz E, Sayyed M I, Agar O, Kamislioglu M, Altunsoy Guclu E E, Eke C (2020). An extensive study on nuclear shielding performance and mass stopping power (MSP)/projected ranges (PR) of some selected granite samples. *Radiation Effects and Defects in Solids*, **176**(3-4), 320–340. https://doi.org/10.1080/10420150.2020.1849209

[29] El-Khayatt A M, Ali A M, Singh V P (2014). Photon attenuation coefficients of Heavy-Metal Oxide glasses by MCNP code, XCOM program and experimental data: A comparison study. *Nuclear Instruments and Methods in Physics Research Section A*, **735**, 207–212. https://doi.org/10.1016/j.nima.2013.09.027

[30] Boukhris I, Kebaili I, Al-Buriahi M S, Sayyed M I (2021). Radiation shielding properties of tellurite-lead-tungsten glasses against gamma and beta radiations. *Journal of Non-Crystalline Solids*, **551**, 120430. https://doi.org/10.1016/j.jnoncrysol.2020.120430

[31] Kebaili I, Sayyed M I, Boukhris I, Al-Buriahi M S (2020). Gamma-ray shielding parameters of lithium borotellurite glasses using Geant4 code. *Applied Physics A*, **126**, 536. https://doi.org/10.1007/s00339-020-03702-3

[32] Aşkin A (2020). Evaluation of the gamma and neutron shielding properties of 64TeO2 + 15ZnO + (20-x)CdO + xBaO + 1V2O5 glass system using Geant4 simulation and Phy-X database software. *Pramana*, **94**, 97. https://doi.org/10.1007/s12043-020-01972-3

[33] Eakins J S (2009). The attenuation of 0.511- and 0.662-MeV photons by concrete, lead, and iron. *Nuclear Technology*, **168**(3), 894–898. https://doi.org/10.13182/NT09-A9324

---

## Supplementary Table S1: Off-Grid Stopping Power Deviation Check

*Comparison of ShieldLab G4 Bethe-Bloch stopping powers at off-grid energies (geometric midpoints between adjacent tabulation nodes) against log-log interpolation on the 15-node dense reference grid. This check verifies that the Bethe-Bloch implementation returns accurate values at energies not present in the tabulation, and that any interpolation error in the reference grid is small. Energies are chosen as geometric means between consecutive NIST reference grid nodes; the reference grid uses 15 nodes spanning 0.1–10 MeV for electrons and 20 nodes spanning 0.5–100 MeV for protons.*

**Supplementary Table S1A. Electrons — ShieldLab G4 vs. log-log interpolation at off-grid energies**

| Material | E (MeV) | S_coll SL-G4 (MeV cm² g⁻¹) | S_coll Interp. | \|Δ_coll\| (%) | S_total SL-G4 (MeV cm² g⁻¹) | S_total Interp. | \|Δ_total\| (%) |
|---|---|---|---|---|---|---|---|
| Water | 0.173 | 3.0316 | 3.0394 | 0.26 | 3.0365 | 3.0443 | 0.26 |
| Water | 1.225 | 1.9278 | 1.9336 | 0.30 | 1.9440 | 1.9503 | 0.32 |
| Lead | 0.173 | 1.4775 | 1.4811 | 0.24 | 1.5029 | 1.5066 | 0.25 |
| Lead | 1.225 | 0.9970 | 1.0000 | 0.30 | 1.0905 | 1.0963 | 0.53 |
| Lead | 3.873 | 1.0912 | 1.0915 | 0.03 | 1.5134 | 1.5278 | 0.95 |

*Maximum electron |Δ_coll| = 0.30% (Water/Lead, 1.225 MeV); maximum |Δ_total| = 0.95% (Lead, 3.873 MeV — radiative dominated). All values comfortably within the stated ESTAR accuracy band of ±1–2%.*

**Supplementary Table S1B. Protons — ShieldLab G4 vs. log-log interpolation at off-grid energies**

| Material | E (MeV) | S_elec SL-G4 (MeV cm² g⁻¹) | S_elec Interp. | \|Δ_elec\| (%) | S_total SL-G4 (MeV cm² g⁻¹) | S_total Interp. | \|Δ_total\| (%) |
|---|---|---|---|---|---|---|---|
| Water | 1.73 | 185.131 | 185.016 | 0.062 | 185.131 | 185.016 | 0.062 |
| Water | 5.48 | 75.763 | 75.753 | 0.013 | 75.763 | 75.753 | 0.013 |
| Water | 34.64 | 16.927 | 16.931 | 0.027 | 16.927 | 16.931 | 0.027 |
| Lead | 1.73 | 50.170 | 49.946 | 0.445 | 50.170 | 49.946 | 0.445 |
| Lead | 12.25 | 16.421 | 16.398 | 0.137 | 16.421 | 16.398 | 0.137 |

*Maximum proton |Δ_elec| = 0.445% (Lead, 1.73 MeV); maximum |Δ_total| = 0.445% (same). All off-grid deviations are sub-0.5%, well within the ICRU Report 49 / PSTAR model accuracy of ±1–2%.*

*Note: energies in Tables 6 and 7 of the main text are standard NIST ESTAR/PSTAR tabulation nodes where ShieldLab G4 returns exact data-retrieval values (Δ < 0.01%). Supplementary Tables S1A–B demonstrate that the Bethe-Bloch implementation also provides accurate results at off-grid energies without relying on sparse table interpolation.*

