Paper title: Memory-Efficient Geant4 Modelling Regimes for Nanocomposite Radiation Shielding: Effective Medium, Explicit Nanoparticle Geometry, and Hybrid Representative-Volume Validation
Reviewer: 2 — Domain & Significance
Date: 2026-05-18
Round: 1

OVERALL RECOMMENDATION:
  [ ] Accept as is
  [ ] Minor revisions
  [x] Major revisions
  [ ] Reject

SUMMARY (2–3 sentences):
The manuscript has a publishable core result: for this HDPE/Bi2O3 system, effective-medium transport remains valid for macroscopic attenuation at 30–150 keV, while `G4MultiUnion` fails to scale usefully beyond very small explicit RVEs. The domain-level weakness is presentation: the paper does not yet help the reader see the regime choices, the scalability result, or the practical recommendation quickly enough.

MAJOR COMMENTS (each must be addressed before submission):
M1. Location: Introduction / Methods
    Comment: There is no visual regime map or schematic showing what regimes A, B, and C actually are, how they differ geometrically, and where each is scientifically justified. For a paper centered on modelling-regime choice, this is a major communication gap.
    Required action: Add a conceptual figure or diagram that shows the three regimes and the recommended usage logic.

M2. Location: Section 5.3 and Section 6.2
    Comment: The `G4MultiUnion` scalability finding is one of the strongest contributions in the paper, but it is currently buried in text and one table-free paragraph. A reviewer should not have to extract the 250 nm / 500 nm / 1 µm story manually from prose.
    Required action: Add a dedicated scalability figure that visualizes node count, voxel-cell growth, and observed feasibility for the tested RVE sizes.

M3. Location: Section 5.1.4 and Discussion
    Comment: The paper mentions buildup observables and downstream spectrum behavior, but does not show them graphically. That weakens the bridge between the benchmark methodology and the broader shielding-physics interpretation.
    Required action: Add a figure for the buildup observable trend and, if available from the canonical outputs, a downstream spectrum visualization.

MINOR COMMENTS (strongly recommended):
m1. Location: Conclusions
    Comment: The practical recommendation is present, but a diagrammatic summary would make the paper far more useful for practitioners.
    Suggested fix: Let the conceptual figure end with a “recommended default / validation-only / not scalable” framing for regimes A/B/C.

m2. Location: Figure package overall
    Comment: A paper with this amount of methods/results content should not present only one figure.
    Suggested fix: Build a five-figure package with at least one diagram and four data-driven figures.

SPECIFIC COMMENTS (line-level):
- Section 5.3: The 8 GB workstation scalability result deserves its own visual summary.
- Section 6.2: The architecture distinction between `G4PVParameterised` and `G4MultiUnion` is a headline result; make it visible, not only textual.
- Results/Discussion boundary: keep any new figures tightly tied to existing reported numbers rather than adding fresh claims.