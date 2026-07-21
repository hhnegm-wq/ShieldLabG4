# Simulated Peer Review — Round 1, Reviewer 1
## Paper 2: *ShieldLab G4: An Open-Source Software Platform for Gamma-Ray Shielding Simulation and Validation*
### Role: Methods & Statistics Reviewer

---

**Reviewer 1 Report**

**Summary of the paper**

This manuscript describes ShieldLab G4, an open-source software platform that wraps Geant4 for gamma-ray shielding simulation and exposes it via a REST API, CLI, Python SDK, and Streamlit web interface. The validation benchmarks mass attenuation coefficients (MAC) and half-value/tenth-value layer thicknesses against NIST XCOM reference data for nine materials across 56 energy-material combinations. The paper follows the SoftwareX Original Software Article format.

**Overall recommendation:** Minor revision

---

### Major Comments

**M1. Quantitative threshold for validation claim**

The manuscript claims "excellent agreement" with NIST XCOM (§5 or §7), with a reported mean absolute deviation of 0.44% and a maximum of 15.26%. The maximum of 15.26% (Bismuth at 0.06 MeV near the K-edge) is non-trivial and should be explicitly addressed:

- The abstract should disclose both values: mean and maximum.
- The limitations section should state that near-edge interpolation in log-log XCOM data is the root cause.
- The pass/fail criterion (≤5% for 54/56 points?) should be stated explicitly, not just visually implied by the figure.

**M2. OLS regression panel A — interpretation**

The OLS slope in Figure 3 panel A should be reported with its standard error and p-value, not only the value (e.g., "slope = 1.0002 ± 0.0003, R² = 0.9998, p < 10⁻⁶"). Without these, readers cannot assess whether the slope is statistically distinguishable from unity. Add a table or annotations directly on the figure.

**M3. Independence of benchmark data points**

The 56 data points span 9 materials × 6–8 energies per material. Many points within a material are correlated because the same Geant4 geometry and material definition are reused. The statistical description should acknowledge this: "56 independent energy-material combinations were evaluated, though points within the same material share a common geometry configuration."

**M4. Residual symmetry**

Figure 3 panel B shows a systematic negative bias for several materials at low energy. This should be noted in the figure caption or discussion. Is this bias reproduced in independent runs, or is it stochastic?

---

### Minor Comments

**m1.** Table 1 (§3 or §2, State of the Field): the column "Geant4 version" — is the version 11.4 referring to the installed system library or the minimum supported version? Clarify.

**m2.** §8 (Governance/QA): "155 passing tests" — over what environment? Operating system, Python version, Geant4 version should be specified.

**m3.** §11 (Availability/Installation): The `pip install shieldlabg4` command implies the package is on PyPI. If it is not yet on PyPI at submission time, this must be changed to `pip install -e .` with a note.

**m4.** §12 (Limitations L2): "simplified geometry" — specify what geometries are supported (slab only? cylinder? wedge?) to help readers assess scope.

**m5.** The DOCX/PDF figure captions should include explicit axis labels matching the figure axes (units, symbols). Currently the captions partially duplicate the axis labels without adding interpretive value.

---

### Response Requested

Please provide:
1. Updated Figure 3 with OLS slope ± SE and R² annotated.
2. Revised abstract disclosing both mean (0.44%) and max (15.26%) deviation.
3. Revised §12 L2 with explicit geometry list.
4. Clarification of the PyPI availability claim.

---
*Reviewer 1 declaration: No conflict of interest.*
