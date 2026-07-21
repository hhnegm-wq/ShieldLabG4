2026-05-18

Hani Negm
Department of Physics, College of Science, Jouf University
Sakaka, Saudi Arabia
Email: hhnegm@ju.edu.sa

Editor
Radiation Physics and Chemistry

Subject: Submission of manuscript for consideration in Radiation Physics and Chemistry

Dear Editor,

I am pleased to submit the manuscript "Memory-Efficient Geant4 Modelling Regimes for Nanocomposite Radiation Shielding: Effective Medium, Explicit Nanoparticle Geometry, and Hybrid Representative-Volume Validation" for consideration as an original research article in Radiation Physics and Chemistry.

The manuscript is well aligned with the journal's readership because it addresses photon attenuation, shielding-material modelling, and Monte Carlo transport methodology in a directly usable form. The study benchmarks three Geant4 modelling regimes for an HDPE/Bi2O3 nanocomposite at matched composition and density: an effective-medium material model, an explicit G4PVParameterised representative-volume geometry, and an explicit G4MultiUnion representative-volume geometry.

The central result is that all three regimes agree within the pre-registered 3% acceptance window at 30-150 keV for the matched HDPE/Bi2O3 benchmark system. This supports the effective-medium approximation for macroscopic attenuation when the photon mean free path greatly exceeds the nanoparticle radius. The study also contributes a practical computational result: G4PVParameterised remains tractable up to a 1 um representative volume containing 2,888 explicit nanoparticles, whereas G4MultiUnion becomes impractical beyond about 45 spheres on 8 GB workstation-class hardware because of voxelizer growth.

The manuscript therefore offers a concrete workflow recommendation for shielding studies: use the effective-medium model as the production default, use explicit parameterised representative volumes as a validation geometry when explicit structure must be checked, and reserve G4MultiUnion for small-cluster stress tests rather than dense large-RVE production work. The novelty is methodological rather than kernel-level, namely a controlled cross-regime shielding benchmark and representative-volume validation workflow implemented in a reproducible open benchmark harness.

This manuscript is original, has not been published previously, and is not under consideration elsewhere. I confirm that I am the sole author and that I approve the submitted version. There are no conflicts of interest to declare, and no external funding supported this work.

Sincerely,

Hani Negm
Department of Physics, College of Science, Jouf University
hhnegm@ju.edu.sa
