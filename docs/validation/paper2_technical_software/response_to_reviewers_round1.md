# Response To Reviewers — Round 1

## Paper 2: ShieldLab G4 technical/software manuscript

This document summarises how the Round 1 simulated reviewer comments were addressed in the revised manuscript and figure set.

## Reviewer 1

**M1. Quantitative threshold for validation claim**

Addressed. The abstract now reports the mean absolute deviation (0.44%), the maximum deviation (15.26%), and the interpretation of the bismuth outlier near the 0.06 MeV K-edge. Figure 3 and its caption now state that 54 of 56 attenuation points fall within ±5%.

**M2. OLS regression interpretation**

Addressed. Figure 3 Panel A now annotates slope, slope standard error, $R^2$, and $p$-value.

**M3. Independence of benchmark data points**

Addressed in wording. The manuscript now describes the attenuation-validation subset explicitly as 56 energy-material combinations across nine materials, and the reproducibility/statistical discussion clarifies that MT acceptance is statistical rather than bit-identical across all environments.

**M4. Residual symmetry**

Addressed. Figure 3 Panel B now labels the bismuth K-edge outlier directly.

**m1. Geant4 version meaning**

Addressed. Table 2 now labels Geant4 11.4 as the validated baseline.

**m2. Test environment**

Addressed. Section 8.2 now identifies the manuscript-preparation environment as Windows with Python 3.12.7 and states that Geant4-tagged runs require the project binary built against Geant4 11.4.

**m3. PyPI / package naming**

Addressed. Section 11 keeps editable installation (`pip install -e ./python[dev]`) and now states that the import namespace is `shieldlab`.

**m4. Geometry scope**

Addressed. Limitation L3 now explicitly states that only one-dimensional infinite slab attenuation with point-detector approximation is supported; cylindrical, spherical, wedge, voxelised, and broad-beam detector-response geometries remain future work.

**m5. Figure captions**

Addressed. Figure 3 caption now reports the actual axes interpretation and fit statistics more explicitly.

## Reviewer 2

**M1. Comparison set in Table 1**

Addressed. Section 2 now states the selection rule for Table 1 and explains why deterministic calculators and restricted-license wrappers were excluded from the workflow-focused comparison.

**M2. Cloud deployment security**

Addressed. Section 9 now includes an explicit threat-model paragraph, and Figure 5 summarises the hardened deployment posture.

**M3. Reproducibility of simulations**

Addressed. Section 10 now states the seed-precedence order, the scope of repeatability claims, and the MT-versus-serial statistical acceptance rule.

**m1. "100+ isotopes" claim**

Addressed. Limitation L2 now states the exact bundled isotope count: 100 isotopes in an ICRP-107 / ENSDF-derived subset.

**m2. Soften novelty claim**

Addressed. The manuscript now uses "To our knowledge" for the workflow-integration claim.

**m3. Python import name**

Addressed. The manuscript now explicitly states that the installed import namespace is `shieldlab`.

**m4. CI gate timing**

Partially addressed. The gate structure is clearer in Figure 2, but no stable timing benchmark was added because timing varies with environment and Geant4 availability. This can be added later if a dedicated CI runtime table is required.

**m5. CRediT completeness**

No substantive change required. The existing CRediT statement already lists Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Visualization, and Writing roles for the sole listed author.

**m6. Observability outputs**

Addressed. Section 5.3 now describes the span set more explicitly: HTTP request latency, queue submission, worker execution, and result retrieval under shared correlation IDs.

## Additional improvements beyond reviewer comments

- Figure set expanded from 3 figures to 5 figures.
- Figures 1 and 2 were redrawn to eliminate label collisions and improve submission quality.
- Figure 4 now visualises the five-layer reproducibility model.
- Figure 5 now visualises the deployment security and audit posture.

## Remaining submission-time fields

- Institution remains unresolved because no verified affiliation string is present in the repository.
- Public repository URL and Zenodo DOI still need to be inserted once publication metadata is final.