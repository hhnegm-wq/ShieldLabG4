# Radiation Physics and Chemistry Submission Assets for ShieldLab G4 v07

## Alternate Submission-Portal Abstract

ShieldLab G4 v1.0.0 is an open-source radiation shielding platform that combines analytical calculations with Geant4 11.4 multithreaded Monte Carlo transport in a single workflow. The platform covers photon mass attenuation coefficients, HVL/TVL, GP buildup factors, effective atomic number, electron/proton/alpha/heavy-ion stopping, dose-rate conversion, and fast-neutron removal cross-sections. Validation was performed against seven reference codes and databases: NIST XCOM, Phy-X/PSD, WinXCom, NIST ESTAR/PSTAR/ASTAR, SRIM-2013, MCNP6, and FLUKA/PHITS. The photon benchmark comprises 56 points across nine materials from 60 keV to 10 MeV. For photon attenuation, ShieldLab G4 reproduces NIST XCOM values with a mean absolute deviation of 0.176% over 55 non-edge points; 93% of points lie within +/-1.5% and 98.2% within +/-2%, with the only failure attributable to a known Bi L-edge interpolation artifact. Electron and proton stopping agree with NIST within 1.5% and 2.0%, respectively. Six peer-reviewed glass and nanocomposite compositions are reproduced to within 0.30% of published Phy-X/PSD values at 0.662 MeV. External dense-material literature, including an exact 0.662 MeV concrete/lead/iron transmission benchmark and verified experiment-simulation studies on granite and heavy-metal oxide glasses, provides additional support beyond the elemental benchmark set. These results position ShieldLab G4 as a unified and well-benchmarked environment for analytical shielding calculations with integrated Geant4 capability for geometry-dependent and buildup-dominated problems.

## Suggested RPC Highlights

- 56 photon benchmarks matched NIST XCOM with 0.176% mean deviation
- 98.2% of photon points passed the +/-2% acceptance criterion
- Electron and proton stopping matched NIST within 1.5% and 2.0%
- ShieldLab G4 unifies attenuation, buildup, stopping, FNRCS, and Geant4
- External 0.662 MeV data support concrete, lead, and iron validation

## Single-Author CRediT Statement

Hani H. Negm: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Visualization, Writing - original draft, Writing - review and editing.

## RPC Submission Notes

- Manuscript abstract in v07 is 216 words and meets the RPC 250-word limit.
- Manuscript keyword list in v07 contains 6 keywords and meets the RPC limit.
- Reference content is updated and source-verified, but the manuscript still uses numbered in-text citations.
- For final RPC submission, convert in-text citations and the bibliography to author-year alphabetical style.
- Add corresponding-author details in the journal submission package.
- Add a generative-AI declaration only if the authors decide it is required by their submission policy interpretation.