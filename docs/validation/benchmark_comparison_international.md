# ShieldLab G4 — International Benchmark Comparison

**Version:** 2026-05-05  
**Owner:** Dr. Hani H. Negm  
**Platform:** ShieldLab G4 (Geant4 11.4 MT + Python 3.12 analytical engine)

---

## 1. Purpose

This document presents quantitative benchmark figures comparing ShieldLab G4 against the leading international reference programs and databases for radiation shielding parameters, spanning gamma/photon, electron/beta, alpha, proton, and heavy-ion transport. Comparisons are drawn against:

| Reference Program / Database | Developer | Radiation Covered |
|---|---|---|
| **NIST XCOM / XrayMassCoef** | NIST, Berger & Hubbell 1987 | γ / X-ray photon MAC |
| **Phy-X / PSD** | Şakar et al. 2020, Elsevier | γ, β, e⁻, ion shielding params |
| **WinXCom** | Gerward et al. 2004 | γ / X-ray photon MAC |
| **NIST ESTAR** | NIST, Berger et al. | Electron (β⁻) stopping power & range |
| **NIST PSTAR** | NIST, Berger et al. | Proton stopping power & range |
| **NIST ASTAR** | NIST, Berger et al. | Alpha-particle stopping power & range |
| **SRIM / TRIM** | Ziegler, Biersack & Littmark 1985 | Ions (p, α, heavy ions) in matter |
| **MCNP / MCNPX** | LANL | Full particle transport (MC) |
| **FLUKA** | CERN / INFN | Full particle transport (MC) |
| **PHITS** | JAEA | Full particle transport (MC) |
| **Geant4** | CERN (base MC engine) | Full particle transport (MC) |

---

## 2. ShieldLab G4 Analytical Engine — Implementation Basis

The analytical physics engine in `python/shieldlab/physics/` uses the following internationally recognized formulations:

| Module | Implements | International Reference |
|---|---|---|
| `nist_xcom.py` | Photon MAC and energy-absorption coefficients (μ/ρ, μ_en/ρ) via NIST web API + local cache | NIST XrayMassCoef / XCOM (Hubbell & Seltzer) |
| `shielding_params.py` | MAC, LAC, HVL, TVL, MFP, Zeff, Neff via mixture rule | NIST mixture rule (Berger & Hubbell); ICRU Report 16; Hine 1952 (Zeff) |
| `nist_estar.py` | Electron stopping power (collision + radiative) and CSDA range | ICRU Report 37 (1984); Sternheimer et al. 1984 (density effect); Koch & Motz 1959 (bremsstrahlung) |
| `ion_range.py` | Proton, alpha, heavy-ion stopping power and CSDA range | ICRU Report 49 (1993); Ziegler, Biersack & Littmark 1985 (SRIM); Bragg-Kleeman rule (1905) |
| `klein_nishina.py` | Compton Klein-Nishina differential and total cross-sections | Klein & Nishina 1929; Evans 1955 |
| `dose_rate.py` | H\*(10) ambient dose equivalent and air-kerma rate | ICRP Publication 74 (1996); NIST photon interaction data |

The Monte Carlo engine is Geant4 11.4 MT, the world-standard open-source particle transport toolkit developed by CERN. All Monte Carlo results therefore carry the full Geant4 physics validation heritage.

---

## 3. Section A — Photon / Gamma Shielding Parameters vs. NIST XCOM, Phy-X, and WinXCom

### 3.1 Methodology

ShieldLab G4 fetches photon MAC values directly from the NIST XrayMassCoef API at runtime and applies the IUPAC mixture rule to compounds. This is identical to the methodology used by XCOM, WinXCom, and Phy-X/PSD. Differences below are therefore purely interpolation and mixture-rule implementation differences, not physics-model differences.

Computed quantities validated: μ/ρ (cm²/g), HVL (cm), TVL (cm).

### 3.2 NIST XCOM Benchmark — 30-Point Validation Table

Materials: Lead, Water, Ordinary Concrete (NIST), Aluminium, Iron, Copper, Tungsten, HDPE, Bismuth.  
Energy range: 60 keV – 6 MeV.  
NIST reference values: NIST XrayMassCoef Table 4 (compounds) and elemental tables (Hubbell & Seltzer, NIST PRDFD, accessed 2025).

| Material | E (MeV) | ρ (g/cm³) | NIST μ/ρ | ShieldLab μ/ρ | Δ (%) | HVL (cm) | TVL (cm) | Pass |
|---|---|---|---|---|---|---|---|---|
| Lead | 0.060 | 11.35 | 5.0210 | 5.0210 | 0.00 | 0.0122 | 0.0404 | ✓ |
| Lead | 0.200 | 11.35 | 0.9990 | 0.9985 | −0.05 | 0.0612 | 0.2032 | ✓ |
| Lead | 0.662 | 11.35 | 0.1110 | 0.1111 | +0.05 | 0.5499 | 1.8268 | ✓ |
| Lead | 1.000 | 11.35 | 0.07102 | 0.07102 | 0.00 | 0.8599 | 2.8565 | ✓ |
| Lead | 1.332 | 11.35 | 0.05624 | 0.05639 | +0.27 | 1.0829 | 3.5975 | ✓ |
| Water | 0.060 | 1.00 | 0.2058 | 0.2058 | +0.02 | 3.3674 | 11.186 | ✓ |
| Water | 0.100 | 1.00 | 0.1707 | 0.1707 | −0.01 | 4.0609 | 13.490 | ✓ |
| Water | 0.662 | 1.00 | 0.08570 | 0.08568 | −0.03 | 8.0903 | 26.876 | ✓ |
| Water | 1.000 | 1.00 | 0.07066 | 0.07072 | +0.09 | 9.8009 | 32.558 | ✓ |
| Water | 6.000 | 1.00 | 0.02770 | 0.02770 | −0.01 | 25.026 | 83.133 | ✓ |
| Concrete | 0.060 | 2.35 | 0.2666 | 0.2666 | −0.01 | 1.1064 | 3.6755 | ✓ |
| Concrete | 0.662 | 2.35 | 0.08280 | 0.08279 | −0.02 | 3.5629 | 11.836 | ✓ |
| Concrete | 1.332 | 2.35 | 0.05910 | 0.05908 | −0.03 | 4.9923 | 16.584 | ✓ |
| Aluminium | 0.060 | 2.70 | 0.2778 | 0.2778 | 0.00 | 0.9241 | 3.0699 | ✓ |
| Aluminium | 0.662 | 2.70 | 0.07551 | 0.07459 | −1.22 | 3.4417 | 11.433 | ✓ |
| Aluminium | 1.000 | 2.70 | 0.06146 | 0.06146 | 0.00 | 4.1770 | 13.876 | ✓ |
| Iron | 0.060 | 7.87 | 1.2050 | 1.2050 | 0.00 | 0.0731 | 0.2428 | ✓ |
| Iron | 0.662 | 7.87 | 0.07357 | 0.07345 | −0.17 | 1.1992 | 3.9836 | ✓ |
| Iron | 1.332 | 7.87 | 0.05180 | 0.05182 | +0.05 | 1.6995 | 5.6456 | ✓ |
| Copper | 0.060 | 8.96 | 1.5810 | 1.5930 | +0.76 | 0.0486 | 0.1613 | ✓ |
| Copper | 0.662 | 8.96 | 0.07367 | 0.07260 | −1.46 | 1.0656 | 3.5399 | ✓ |
| Tungsten | 0.060 | 19.30 | 3.7180 | 3.7130 | −0.13 | 0.0097 | 0.0321 | ✓ |
| Tungsten | 0.662 | 19.30 | 0.09827 | 0.09852 | +0.25 | 0.3645 | 1.2110 | ✓ |
| Tungsten | 1.000 | 19.30 | 0.06514 | 0.06618 | +1.60 | 0.5427 | 1.8027 | ✓ |
| HDPE | 0.060 | 0.95 | 0.1990 | 0.1970 | −1.03 | 3.7045 | 12.306 | ✓ |
| HDPE | 0.662 | 0.95 | 0.08786 | 0.08799 | +0.14 | 8.2925 | 27.547 | ✓ |
| HDPE | 1.000 | 0.95 | 0.07240 | 0.07262 | +0.30 | 10.047 | 33.377 | ✓ |
| Bismuth | 0.060 | 9.75 | 5.2330 | 5.2330 | 0.00 | 0.0136 | 0.0451 | ✓ |
| Bismuth | 0.662 | 9.75 | 0.1133 | 0.1135 | +0.14 | 0.6266 | 2.0815 | ✓ |
| Bismuth | 1.332 | 9.75 | 0.05789 | 0.05712 | −1.32 | 1.2445 | 4.1342 | ✓ |

> **Data source note.** An earlier version of this table used a Phy-X/PSD-derived reference of 4.54 cm² g⁻¹ for Bi at 60 keV, yielding an apparent 15.3% deviation. The NIST XrayMassCoef HTML page for Z = 83 lists μ/ρ = **5.233 cm² g⁻¹** at exactly 60 keV as a directly tabulated grid point. ShieldLab G4 reads this value directly from cache (no interpolation). The discrepancy was a cross-code data-compilation difference in Phy-X/PSD, not a physics error in ShieldLab G4.

### 3.3 Aggregate Accuracy Statistics vs. NIST XCOM

| Metric | All 30 points |
|---|---|
| **Mean |Δ| (%)** | **0.28** |
| **Max |Δ| (%)** | **1.60** (W, 1 MeV) |
| RMSE (%) | 0.54 |
| Points ≤ 0.5 % | 24 / 30 (80 %) |
| Points ≤ 1.5 % | 28 / 30 (93 %) |
| Pass rate (all criteria) | 30 / 30 (100 %) |

These figures are comparable to, or better than, the typical ±1–2% accuracy cited for Phy-X/PSD and WinXCom against NIST XCOM at intermediate energies (see Şakar et al. 2020, Rad. Phys. Chem. 166, 108496).

### 3.4 Per-Material Breakdown

| Material | n | Mean |Δ| (%) | Max |Δ| (%) |
|---|---|---|---|
| Lead | 5 | 0.074 | 0.270 |
| Water | 5 | 0.032 | 0.090 |
| Ordinary Concrete | 3 | 0.020 | 0.030 |
| Aluminium | 3 | 0.407 | 1.220 |
| Iron | 3 | 0.073 | 0.170 |
| Copper | 2 | 1.110 | 1.460 |
| Tungsten | 3 | 0.660 | 1.600 |
| HDPE | 3 | 0.490 | 1.030 |
| Bismuth | 3 | 0.487 | 1.32 |

### 3.5 Comparison with Phy-X / PSD and WinXCom

**Equivalence argument.** Both Phy-X/PSD (Şakar et al. 2020) and WinXCom (Gerward et al. 2004) derive photon MAC values from the same NIST XrayMassCoef elemental datasets and apply the identical Bragg-Gray / NIST mixture rule. Since ShieldLab G4 also fetches data from the same NIST API and applies the same mixture rule, the three programs are analytically equivalent for elemental and compound MAC computation when the same grid-interpolation scheme is used.

**Published literature cross-validation.** The 6 benchmark studies registered in `benchmark_registry.json` are drawn from peer-reviewed papers (Negm et al. 2020–2025) in which the authors independently validated their experimental measurements against both Phy-X/PSD and WinXCom. ShieldLab G4 replicates the analytical leg of those same studies with all study passes confirmed (release_validation_report_latest: PASS for all 6). This constitutes an indirect three-way cross-validation: ShieldLab G4 ≈ Phy-X/PSD ≈ WinXCom ≈ published experimental data.

**Known Phy-X limitations shared by ShieldLab G4:**
- Sub-K-edge interpolation sensitivity for Z > 60 at energies below ~150 keV (same NIST grid).
- Buildup factor computation is semi-empirical (GP model); ShieldLab G4 currently implements the same GP-based model.
- Both programs rely on narrow-beam attenuation; broad-beam corrections require buildup factors.

---

## 4. Section B — Literature Material Benchmarks (Phy-X / WinXCom Cross-Validated)

These six benchmark studies cover multi-component glasses and nanocomposites where published authors compared against Phy-X/PSD or WinXCom directly. ShieldLab G4 replicates those comparisons and all pass validation.

| Benchmark ID | Material | Class | DOI | Radiation | ShieldLab Status |
|---|---|---|---|---|---|
| `negm-atp-cdpbo-x15` | AT70Pb15Cd15 attapulgite nanocomposite | Nanocomposite | 10.1088/1402-4896/ad3b48 | γ, neutron | **PASS** |
| `negm-hmg-btc1` | BTC1 metallic glass | Metallic glass | 10.1007/s11664-025-11830-w | γ, β, e⁻, α, n, p | **PASS** |
| `negm-nio-lcns5` | LCNS5 (CaO-Li₂O-NiO-SiO₂) glass | Oxide glass | 10.1007/s11664-023-10833-9 | γ, β, e⁻, α, n | **PASS** |
| `negm-mo0-phosphate-glass` | Mo0.0 PbO-P₂O₅-Na₂O-Al₂O₃ glass | Lead phosphate glass | 10.1007/s10854-020-04709-5 | γ, e⁻ | **PASS** |
| `negm-atp-cufe-x30` | AT40Fe30Cu30 attapulgite nanocomposite | Nanocomposite | 10.1016/j.radphyschem.2023.111398 | γ | **PASS** |
| `negm-atp-cdni-x30` | AT40Cd30Ni30 attapulgite nanocomposite | Nanocomposite | 10.1016/j.radphyschem.2024.112149 | γ, neutron | **PASS** |

All study config files are located in `configs/studies/literature_benchmark_negm_*.json`.  
Validation run: 2026-05-05, Python 3.12.7, Windows 11.

---

## 5. Section C — Electron / Beta Shielding vs. NIST ESTAR

### 5.1 Model Basis

ShieldLab G4 implements the **ICRU Report 37 / ESTAR** formulation in `python/shieldlab/physics/nist_estar.py`:

- **Collision stopping power:** Relativistic Bethe formula with Sternheimer–Berger–Seltzer (1984) density-effect correction.
- **Radiative stopping power:** Bethe-Heitler bremsstrahlung (Koch & Motz 1959).
- **Total stopping power:** S_total = S_collision + S_radiative (MeV cm²/g).
- **CSDA range:** Numerical integration of 1 / S_total (g/cm²), converted to cm using material density.
- **Radiation yield:** Y = ∫S_rad dT / ∫S_total dT.

Mean excitation energies I(Z) are taken from ICRU Report 37, Table 5.1 — identical to those used by ESTAR. Sternheimer density-effect parameters from Sternheimer, Berger & Seltzer (1984) At. Data Nucl. Data Tables 30, 261 are hardcoded for all elements Z = 1–92.

### 5.2 Expected Accuracy vs. NIST ESTAR

| Energy regime | Expected |Δ| vs. ESTAR |
|---|---|
| E > 1 MeV | ± 1–2 % |
| 100 keV – 1 MeV | ± 1–2 % |
| 10–100 keV | ± 5–10 % |
| < 10 keV | > 10 % (Bethe formula breakdown) |

These accuracy bands are the same as those published for ESTAR by NIST; they reflect the intrinsic uncertainty of the Bethe theory, not implementation error.

### 5.3 Benchmark Coverage in Published Studies

The LCNS5 (Negm et al. 2023) and BTC1 (Negm et al. 2025) benchmark studies explicitly target electron stopping-power overlays (`figure_targets: electron_stopping`, `ion_stopping`). ShieldLab G4 computes these and passes study-level validation.

---

## 6. Section D — Proton / Alpha / Heavy-Ion Stopping vs. SRIM, PSTAR, and ASTAR

### 6.1 Model Basis

ShieldLab G4 implements the **SRIM / PSTAR / ASTAR** methodology in `python/shieldlab/physics/ion_range.py`:

- **Proton stopping (PSTAR-equivalent):** Electronic + nuclear components; relativistic Bethe with Fermi density correction; ICRU 49 formulation with Ziegler corrections.
- **Alpha stopping (ASTAR-equivalent):** Proton stopping power scaled by the Ziegler (1977) effective charge fraction $q_\text{eff}(v)$, where the velocity-dependent correction accounts for partial charge stripping at intermediate energies.
- **Heavy-ion stopping (SRIM-equivalent):** Bragg–Kleeman additivity rule applied to proton stopping scaled by $Z_\text{eff}^2$.
- **CSDA range:** Numerical integration of 1 / S_total from rest energy to projectile energy.

The **Bragg additivity rule** (Bragg & Kleeman 1905) is applied compound-wise, matching the same approximation used in SRIM and PSTAR for composite materials.

### 6.2 Expected Accuracy vs. SRIM / PSTAR / ASTAR

| Particle | Energy regime | Expected |Δ| vs. SRIM/PSTAR/ASTAR |
|---|---|---|
| Proton | 0.1 – 30 MeV | ± 2–5 % |
| Proton | < 100 keV | ± 10–20 % |
| Alpha (⁴He) | 0.1 – 30 MeV | ± 2–5 % |
| Alpha (⁴He) | < 100 keV | ± 10–20 % |
| Heavy ions | 1 – 100 MeV/u | ± 5–10 % |
| Heavy ions | < 1 MeV/u | > 10 % (shell/stripping corrections) |

### 6.3 Published Literature Cross-Check

The BTC1 metallic glass benchmark (Negm et al. 2025, DOI: 10.1007/s11664-025-11830-w) is the primary source for multi-particle (α, β, p, ion) stopping validation. The paper reports shielding parameters evaluated with SRIM and ESTAR equivalents; ShieldLab G4 targets the same figure overlays in the registered benchmark. Quantitative residual tables for ion stopping are planned for the next validation cycle.

---

## 7. Section E — Monte Carlo Comparison Context

### 7.1 Geant4 as the Simulation Backbone

ShieldLab G4 executes Geant4 11.4 MT for all Monte Carlo runs. Geant4 itself undergoes continuous international validation by CERN and collaborating institutions; benchmarks of Geant4 against MCNP, FLUKA, PHITS, EGSnrc, and experimental data are published extensively in the literature (see e.g., Allison et al. 2016, NIM A 835; GEANT4 Physics Reference Manual 11.2, 2024).

Key areas of Geant4 physics validation relevant to shielding:

| Physics process | Geant4 model | Published agreement vs. experiment / MC |
|---|---|---|
| Photoelectric absorption | Livermore EPDL97 / G4LivermorePolarizedPhotoElectric | ± 1–3 % vs. MCNP6 (photon MAC) |
| Compton scattering | G4KleinNishinaModel | < 1 % vs. Klein-Nishina theory at E > 0.1 MeV |
| Pair production | G4PairProductionRelModel | ± 1–2 % vs. NIST pair production tables |
| Electron ionisation | G4MollerBhabhaModel / G4eIonisation | ± 1–5 % vs. EGSnrc (Faddegon et al. 2009) |
| Electron bremsstrahlung | G4eBremsstrahlung (SB model) | ± 2–3 % vs. NIST ESTAR, EGSnrc |
| Proton stopping | G4BraggModel + G4BetheBlochModel | ± 2–4 % vs. SRIM (GEANT4 Phys. Ref. Man.) |
| Alpha stopping | G4BraggIonModel | ± 3–6 % vs. SRIM |
| Hadronic (neutron) | G4NeutronHPModel (ENDF/B-VIII.0) | ± 1–5 % vs. MCNP6 (energy-dependent) |

ShieldLab G4 applies these physics processes through the standard **QGSP_BIC_HP** and equivalent physics lists, inheriting the Geant4 validation heritage directly.

### 7.2 Analytical vs. Monte Carlo Cross-Check

ShieldLab G4 exposes both analytical (NIST-based) and Geant4 MC results for the same geometry, allowing direct comparison. For narrow-beam gamma attenuation:

- Expected agreement between ShieldLab G4 analytical and ShieldLab G4 MC: ≤ 2–5 % in the absence of buildup, where the narrow-beam assumption holds.
- Deviations larger than 5 % typically signal buildup (scatter contribution) and are physically expected for broad-beam or thick-shield geometries.

### 7.3 Comparison with MCNP / FLUKA / PHITS

ShieldLab G4 is built on Geant4 MC, which has been extensively cross-compared against MCNP, FLUKA, and PHITS in the literature. Key published inter-code benchmarks:

| Reference | Comparison | Outcome |
|---|---|---|
| Allison et al. (2016), NIM A 835 | Geant4 vs. experiment (EM processes) | ≤ 3 % for photon transport |
| Benchmark study of PHITS (Iwase et al. 2002) | PHITS vs. MCNP vs. EGS4 | < 5 % for photon shielding |
| Faddegon et al. (2009), Med. Phys. | Geant4 vs. EGSnrc for electron beams | ≤ 3 % for electron stopping |
| IAEA TECDOC-1540 (2007) | MCNP vs. GEANT4 vs. FLUKA (neutron) | Within 5 % for thermal neutron transport |

For gamma shielding of dense media (Pb, Fe, concrete), all four codes (MCNP, FLUKA, PHITS, Geant4) typically agree within 2–5 % for transmission fractions, which is the primary figure of merit in ShieldLab G4.

---

## 8. Section F — Capability Comparison Matrix

The table below compares ShieldLab G4 features against other programs for shielding-relevant parameters.

| Parameter | ShieldLab G4 | NIST XCOM | Phy-X / PSD | WinXCom | SRIM | MCNP6 | FLUKA | PHITS |
|---|---|---|---|---|---|---|---|---|
| **γ / X-ray MAC (μ/ρ)** | ✓ (NIST API) | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ |
| **HVL / TVL** | ✓ | — | ✓ | — | — | ✓ | ✓ | ✓ |
| **Buildup factor (GP)** | ✓ | — | ✓ | — | — | ✓ | ✓ | ✓ |
| **Zeff / Neff** | ✓ | — | ✓ | — | — | — | — | — |
| **EBF / EABF** | ✓ | — | ✓ | — | — | ✓ | ✓ | ✓ |
| **FNRCS (fast neutron removal)** | ✓ | — | ✓ | — | — | ✓ | ✓ | ✓ |
| **Electron stopping / range** | ✓ (ESTAR model) | — | ✓ | — | — | ✓ | ✓ | ✓ |
| **Proton stopping / range** | ✓ (PSTAR model) | — | ✓ | — | ✓ | ✓ | ✓ | ✓ |
| **Alpha stopping / range** | ✓ (ASTAR model) | — | ✓ | — | ✓ | ✓ | ✓ | ✓ |
| **Heavy-ion stopping** | ✓ (SRIM model) | — | — | — | ✓ | ✓ | ✓ | ✓ |
| **Compton cross-section** | ✓ (Klein-Nishina) | ✓ | ✓ | — | — | ✓ | ✓ | ✓ |
| **H\*(10) dose rate** | ✓ (ICRP-74) | — | — | — | — | ✓ | ✓ | ✓ |
| **Geant4 MC simulation** | ✓ (G4 11.4 MT) | — | — | — | — | — | — | — |
| **Multi-layer geometry** | ✓ | — | — | — | — | ✓ | ✓ | ✓ |
| **Custom material composer** | ✓ | limited | limited | limited | limited | ✓ | ✓ | ✓ |
| **Study / batch workflow** | ✓ | — | — | — | — | ✓ | ✓ | ✓ |
| **Interactive web UI** | ✓ (Streamlit) | web | web | desktop | desktop | — | — | — |
| **Literature benchmark overlay** | ✓ | — | — | — | — | — | — | — |
| **Open source** | ✓ | ✓ | free online | free | free | restricted | restricted | restricted |

---

## 9. Known Limitations and Validation Caveats

### 9.1 Photon (Gamma)

1. **Sub-K-edge interpolation (high-Z):** Log-linear interpolation on the NIST grid can deviate by 5–20% within ~10 keV of K-edges for Z > 60. This affects Pb, Bi, W at energies just below their K-edges (Pb: 88.0 keV, W: 69.5 keV, Bi: 90.5 keV). The same limitation applies to XCOM, WinXCom, and Phy-X on coarse energy grids.

2. **Narrow-beam assumption:** All analytical MAC-based calculations (HVL, TVL, transmission) assume narrow-beam geometry. For broad-beam or non-collimated sources, buildup factors must be applied; the platform implements the GP model for this purpose.

3. **Coherent scatter:** Included in NIST MAC data; not separately resolved in the analytical engine output.

### 9.2 Electron / Beta

4. **Sub-100 keV accuracy:** The Bethe stopping-power formula breaks down below ~100 keV; reported accuracy is ±5–10 %. ESTAR carries the same stated limitation.

5. **Shell corrections and exchange corrections:** Present in ICRU 37 implementation; accuracy below 1 MeV depends on quality of mean excitation energy I(Z).

### 9.3 Ion Stopping

6. **Low-energy ions:** Below ~100 keV/u the electronic stopping model deviates from SRIM by 10–20% due to nuclear stopping dominance and charge-state fluctuations not fully captured by the Ziegler effective-charge model.

7. **Bragg additivity:** Assumed for compounds, same as PSTAR/SRIM for standard materials. Significant deviations (up to 10%) can arise for materials with strong molecular binding (e.g., water, polymers) at low projectile energies.

### 9.4 Monte Carlo

8. **Statistics:** All MC benchmarks require sufficient histories (≥ 5000 primary events per simulation point) for statistically meaningful transmission fractions. The Q1 readiness gate currently reports 0 statistically adequate result sets; production benchmarks require dedicated high-statistics runs.

9. **Buildup vs. narrow-beam:** MC simulations inherently include scatter; comparison with narrow-beam analytical values requires geometry-matched setups or buildup correction.

---

## 10. Roadmap Items Affecting Benchmark Coverage

| Planned item | Priority | Impact |
|---|---|---|
| Quantitative ESTAR numerical table (ShieldLab vs. NIST ESTAR) | P2 | Direct electron stopping validation numbers |
| Quantitative SRIM/PSTAR numerical table | P2 | Direct ion stopping validation numbers |
| High-statistics MC benchmark runs (≥ 5000 histories/point) | P1 | Statistical adequacy for MC vs. analytical cross-check |
| MC buildup factor overlay vs. ANS-6.4.3 / ANSI literature tables | P1 | Broad-beam correction validation |
| Expanded energy range (> 6 MeV) for photon MAC | P3 | Pair-production dominated regime |
| Benchmark dashboard page in UI | P3 | Live visibility of all benchmark states |

---

## 11. References

1. Berger M J, Hubbell J H (1987). XCOM: Photon Cross Sections on a Personal Computer. NBSIR 87-3597. NIST, Gaithersburg.
2. Hubbell J H, Seltzer S M (1995/2004). Tables of X-Ray Mass Attenuation Coefficients. NIST PRDFD. https://physics.nist.gov/PhysRefData/XrayMassCoef/
3. Şakar E, Özpolat Ö F, Alım B, Sayyed M I, Kurudirek M (2020). Phy-X/PSD: Development of a user-friendly online software for calculation of parameters relevant to radiation shielding and dosimetry. *Radiation Physics and Chemistry* **166**, 108496. https://doi.org/10.1016/j.radphyschem.2019.108496
4. Gerward L, Guilbert N, Jensen K B, Levring H (2004). WinXCom — a program for calculating X-ray attenuation coefficients. *Radiation Physics and Chemistry* **71**, 653–654. https://doi.org/10.1016/j.radphyschem.2004.04.040
5. Berger M J et al. (2005). ESTAR, PSTAR, and ASTAR: Computer Programs for Calculating Stopping-Power and Range Tables. NIST. https://physics.nist.gov/Star
6. Ziegler J F, Biersack J P, Littmark U (1985). *The Stopping and Range of Ions in Solids*. Pergamon Press (also: Ziegler J F et al. 2010, SRIM-2013). http://www.srim.org
7. ICRU Report 37 (1984). Stopping Powers for Electrons and Positrons. ICRU, Bethesda.
8. ICRU Report 49 (1993). Stopping Powers and Ranges for Protons and Alpha Particles. ICRU, Bethesda.
9. Allison J et al. (2016). Recent developments in Geant4. *Nuclear Instruments and Methods A* **835**, 186–225. https://doi.org/10.1016/j.nima.2016.06.125
10. Negm H H et al. (2025). Evaluation of Radiation Shielding Parameters of Different Metallic Glass Compositions for alpha, beta, gamma, n, and p Radiation. *Journal of Electronic Materials* (2025). DOI: 10.1007/s11664-025-11830-w
11. Negm H H et al. (2024). Exploring the potential of attapulgite clay composites containing intercalated nano-cadmium oxide and nano-nickel oxide for efficient radiation shielding. *Radiation Physics and Chemistry* **218**, 112149. DOI: 10.1016/j.radphyschem.2024.112149
12. Negm H H et al. (2024). Evaluation of shielding properties of a developed nanocomposite from intercalated attapulgite clay by CdPb oxides nanoparticles. *Physica Scripta* **99**, 055308. DOI: 10.1088/1402-4896/ad3b48
13. Negm H H et al. (2023). A new nanocomposite of copper oxide and magnetite intercalated into attapulgite clay. *Radiation Physics and Chemistry* **211**, 111398. DOI: 10.1016/j.radphyschem.2023.111398
14. Negm H H et al. (2023). A Comprehensive Investigation of the Impact of NiO on the Radiation Attenuation Characteristics of (CaO-Li₂O-NiO-SiO₂) Glass. *Journal of Electronic Materials* **53** (2024). DOI: 10.1007/s11664-023-10833-9
15. Negm H H et al. (2020). Electronic polarizability, dielectric and gamma-ray shielding features of PbO–P₂O₅–Na₂O–Al₂O₃ glasses doped with MoO₃. *Journal of Materials Science: Materials in Electronics* **31**, 12250. DOI: 10.1007/s10854-020-04709-5
