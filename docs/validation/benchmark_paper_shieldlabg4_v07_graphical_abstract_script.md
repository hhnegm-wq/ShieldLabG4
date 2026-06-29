# Graphical Abstract Script for ShieldLab G4 v07

## Short On-Figure Title

ShieldLab G4 unifies analytical shielding physics and Geant4 transport

## Main Visual Flow

Left panel:
Fragmented shielding workflow
- Photon attenuation
- HVL/TVL
- Buildup factors
- Charged-particle stopping
- Neutron removal
- Monte Carlo transport

Center panel:
ShieldLab G4 v1.0.0
- Python analytical engine
- Geant4 11.4 multithreaded transport
- Offline programmable workflow
- Batch study execution

Right panel:
Validated output
- 56 photon benchmarks
- 9 materials
- 60 keV to 10 MeV
- Electron and proton stopping benchmarks
- Dense-material literature support

Bottom results strip:
- Mean absolute deviation vs NIST XCOM: 0.176%
- 98.2% of photon points within +/-2%
- Electron stopping within 1.5%
- Proton stopping within 2.0%
- Integrated Geant4 for geometry-dependent cases

## Minimal Text Version for the Graphic

Input physics
Photons + charged particles + neutrons

Integrated platform
Analytical shielding modules + Geant4 transport

Validated performance
56 benchmarks across 9 materials
0.176% mean deviation vs NIST XCOM
98.2% within +/-2%

Practical outcome
One programmable environment for shielding design and verification

## Caption-Style Graphical Abstract Text

ShieldLab G4 v1.0.0 combines analytical shielding calculations with Geant4 transport in one programmable workflow. The platform covers photon attenuation, HVL/TVL, GP buildup, effective atomic number, stopping powers for electrons, protons, alpha particles and heavy ions, dose-rate conversion, and fast-neutron removal cross-sections. Validation against seven reference codes and databases showed 0.176% mean deviation from NIST XCOM over 55 non-edge photon benchmark points, with 98.2% of points within +/-2%, while electron and proton stopping agreed with NIST within 1.5% and 2.0%, respectively.

## Voiceover Script if the Graphic Is Animated

Radiation shielding analysis is often split across multiple tools. ShieldLab G4 brings these calculations together in one platform by coupling analytical shielding physics with Geant4 multithreaded Monte Carlo transport. The framework covers photon attenuation, buildup, charged-particle stopping, neutron removal, and dose-related quantities in a single programmable workflow. Validation across 56 photon benchmarks covering nine materials from 60 keV to 10 MeV showed a mean absolute deviation of 0.176 percent from NIST XCOM, with 98.2 percent of photon points within plus or minus two percent. Electron and proton stopping also matched NIST reference data within 1.5 and 2.0 percent. The result is a unified environment for shielding design, benchmarking, and geometry-dependent verification.

## Designer Notes

- Keep text sparse inside the figure; use icons for photons, ions, neutrons, and layered shields.
- Prefer a left-to-right pipeline: fragmented tools -> ShieldLab G4 -> validated outcomes.
- If only one numeric cluster is shown, keep these three values: 56 benchmarks, 0.176%, 98.2%.
- Avoid detailed tables in the graphic; use one compact metrics box instead.
- Use a separate figure caption if the journal requests a non-text-heavy graphical abstract.