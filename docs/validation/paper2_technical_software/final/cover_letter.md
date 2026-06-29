---
# Cover Letter — SoftwareX Submission
**Journal:** SoftwareX (Elsevier)
**Manuscript type:** Original Software Article
---

[Date]

The Editors
*SoftwareX*
Elsevier

Dear Editors,

We submit our manuscript, **"ShieldLab G4: An Open-Source Software Platform for Gamma-Ray Shielding Simulation and Validation"**, for consideration as an Original Software Article in *SoftwareX*.

**What the software does.** ShieldLab G4 is an open-source platform that exposes Geant4 Monte Carlo physics through a production-grade REST API (FastAPI), a Python SDK, a command-line interface, and an interactive Streamlit web application. It computes mass attenuation coefficients (MAC), half-value layers (HVL), and tenth-value layers (TVL) for photon energies from 0.01 to 10 MeV across a library of shielding materials. The platform is container-ready and includes a reference deployment on Microsoft Azure with Microsoft Entra ID authentication and OpenTelemetry observability.

**Why this fills a gap.** Authoritative codes such as NIST XCOM and EGSnrc are single-purpose or require institutional licensing and local installation. Geant4 itself provides no web interface, REST API, or automated validation pipeline. ShieldLab G4 uniquely combines Geant4 physics fidelity with open, accessible interfaces and a rigorous three-tier CI/CD gate that blocks deployment if benchmark agreement with NIST XCOM drops below acceptance thresholds. To our knowledge, no comparable tool provides an end-to-end open-source REST API backed by Monte Carlo transport with automated benchmark verification.

**Validation.** We benchmarked the platform against NIST XCOM reference data for nine materials (Lead, Water, Concrete, Aluminium, Iron, Copper, Tungsten, HDPE, Bismuth) over 56 energy–material combinations spanning the diagnostic and therapy photon range. The mean absolute relative deviation is **0.44%**, with 54 of 56 points within ±5%. The two points exceeding this threshold (Bismuth near the 88 keV K-edge) arise from known log-log interpolation artefacts in the NIST dataset and are explicitly flagged in the software and this manuscript.

**Reproducibility.** The full benchmark dataset (`data_validation_report.csv`), figure-generation scripts, and verification script (`verify_manuscript.py`) are included with the submission. The software includes 155 automated tests covering unit, integration, physics-benchmark, and end-to-end UI layers.

**Availability.** The source code is available at [GitHub repository URL] under [License]. A citable archive will be deposited on Zenodo prior to acceptance.

This manuscript has not been submitted elsewhere and is not currently under review. All authors have approved the submission. We declare no conflicts of interest.

We suggest the following reviewers based on their expertise in Monte Carlo radiation transport software:
- *[Suggested reviewer 1, affiliation]*
- *[Suggested reviewer 2, affiliation]*

We thank the editorial team for their time and consideration.

Sincerely,

[Author Name]
[Institution]
[Email]
[ORCID]
