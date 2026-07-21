# Simulated Peer Review — Round 1, Reviewer 2
## Paper 2: *ShieldLab G4: An Open-Source Software Platform for Gamma-Ray Shielding Simulation and Validation*
### Role: Domain Expert (Radiation Physics & Software Engineering)

---

**Reviewer 2 Report**

**Summary of the paper**

This manuscript presents ShieldLab G4, a cloud-deployable open-source platform for Geant4-based gamma-ray shielding calculations. The architecture is well-thought-out, combining a Geant4 worker, FastAPI backend, Streamlit frontend, async job queue, and OpenTelemetry observability into a coherent production-grade system. Validation is performed against NIST XCOM for nine materials. The paper fits well within the scope of SoftwareX.

**Overall recommendation:** Minor revision (with one significant question)

---

### Major Comments

**M1. Comparison to existing validated codes**

The State of the Field (§2) compares ShieldLab G4 against five tools (XCOM, EGSnrc, FLUKA, OpenMC, FRED). However, the most direct comparable open-source tools for *API-accessible* shielding calculations are not discussed:

- **Shielding10** (ORNL): deterministic gamma shielding for standard geometries.
- **MCNP** wrappers (various GitHub repos): exist but are not open-source due to MCNP licensing.
- **openPHC** or similar: if it exists, compare.

The authors should either add these to Table 1 or explicitly state why they were excluded (e.g., "We focus on Monte Carlo platforms with documented open-source licenses and Python APIs").

**M2. Cloud deployment security**

§9 describes Azure deployment with Microsoft Entra ID (OAuth 2.0) authentication and RBAC. This is appropriate. However:

- What is the threat model? Is the API exposed to the public internet or only to internal users?
- Is the Geant4 worker sandboxed (container, no network egress)?
- Are there rate limits on the worker to prevent resource exhaustion by authenticated users?

For a paper describing a production-deployable tool, at least 2–3 sentences on the security posture are needed. A public URL for a compute-intensive physics simulation has significant abuse potential.

**M3. Reproducibility of simulations**

Monte Carlo simulations are stochastic. The manuscript does not specify:

- What random seed strategy is used (fixed seed for reproducibility vs. non-deterministic production mode)?
- What is the statistical uncertainty per run (relative standard deviation)?
- Are results reproducible bit-for-bit across Geant4 versions?

Readers need this to assess whether benchmark comparisons are meaningful or require re-running.

---

### Minor Comments

**m1.** §1 (Introduction): "100+ isotopes" is mentioned. The exact number and the source of the isotope data (NIST, ENSDF, Geant4 built-in?) should be stated.

**m2.** §4 (Statement of Need): The claim that "no comparable open-source tool provides an end-to-end REST API" should be softened to "to our knowledge" unless a systematic search was conducted.

**m3.** §6 (Illustrative Examples): The Python SDK example uses `import shieldlabg4`. Is this the exact import name in the installed package? Confirm it matches `python/pyproject.toml`.

**m4.** §8 (Governance): CI is described as three-tier (ci_gate → science_gate → release_gate). The manuscript should state the time-to-result for a typical PR run, which helps readers assess suitability for large-scale use.

**m5.** CRediT: Only one author role is listed. For a multi-tool, multi-domain software paper, a more complete CRediT statement is expected.

**m6.** The paper mentions OpenTelemetry for observability but does not describe what metrics/traces are exported. Add at least one example (e.g., simulation latency histogram, job queue depth).

---

### Response Requested

Please provide:
1. Revised §2 with explicit justification for the tools selected for comparison.
2. A paragraph in §9 addressing the security posture of the deployed system.
3. A paragraph or table row in §3 or §5 specifying random seed strategy and typical run-to-run reproducibility.
4. Clarification of the "100+ isotopes" claim with a source reference.

---
*Reviewer 2 declaration: No conflict of interest.*
