Paper title: Memory-Efficient Geant4 Modelling Regimes for Nanocomposite Radiation Shielding: Effective Medium, Explicit Nanoparticle Geometry, and Hybrid Representative-Volume Validation
Reviewer: 1 — Methods & Statistics
Date: 2026-05-18
Round: 1

OVERALL RECOMMENDATION:
  [ ] Accept as is
  [ ] Minor revisions
  [x] Major revisions
  [ ] Reject

SUMMARY (2–3 sentences):
The paper presents a technically valuable three-regime Geant4 benchmark and the underlying results are strong enough for submission after revision. The main methods weakness is not the simulation itself but the evidence presentation: the figure package is too thin, the cross-regime figure implementation is incomplete relative to the text, and several important quantitative results are left trapped in tables or prose.

MAJOR COMMENTS (each must be addressed before submission):
M1. Location: Section 5.4 / Figure F-cross / python/shieldlab/viz/paper3_figures.py
    Comment: The text says the cross-regime comparison figure includes regimes A, B, and C and shows 95% statistical confidence intervals, but the current shared figure folder contains only one figure, and the generator path for regime C depends on `reference_comparison.csv`, which is absent from the regime C result directory. That means the figure implementation is not reliably aligned with the manuscript claim. The plotted figure also does not visibly show confidence intervals.
    Required action: Make the cross-regime figure generator robust to regime C inputs from `sweep_summary.csv`, add visible 95% confidence intervals, regenerate the figure, and revise the manuscript text so the figure description matches the actual output.

M2. Location: Whole manuscript, especially Results §5 and Discussion §6
    Comment: The manuscript relies almost entirely on tables. One figure is not enough for a paper making five distinct methodological points: regime map, regime-A validation, buildup/spectrum behavior, regime-C scalability ceiling, and cross-regime agreement. The evidence hierarchy is therefore unbalanced.
    Required action: Expand the canonical figure suite to approximately five figures, generated from one maintained script and all referenced explicitly in the text.

M3. Location: Section 5.4
    Comment: The first sentence of the figure discussion says the regime-A data are from Table 1, but the cross-regime baseline is actually Table 1b. This is a cross-reference error in the main interpretation section.
    Required action: Correct the Table 1 vs Table 1b reference and re-check all figure/table cross-references after adding the expanded figure set.

M4. Location: Front matter / Keywords
    Comment: The production guide target is 5–8 keywords, but the manuscript currently lists ten. That is a minor production error, but it signals that the final packaging pass is incomplete.
    Required action: Reduce the keyword list to 5–8 targeted indexing terms.

MINOR COMMENTS (strongly recommended):
m1. Location: Figure references throughout
    Comment: The manuscript still uses an internal name (`F-cross`) rather than a clean sequential journal-style figure numbering scheme.
    Suggested fix: Renumber and refer to figures as Figure 1–Figure 5 in the body text, keeping file names internal.

m2. Location: Section 5.1.4
    Comment: The buildup observable is tabulated in prose but not visualized.
    Suggested fix: Add a figure panel or dedicated figure for buildup count/energy trends and, if available, downstream spectra.

SPECIFIC COMMENTS (line-level):
- Section 5.4: Replace “Table 1” with “Table 1b” for the cross-regime regime-A baseline.
- Section 5.4: Remove any claim of 95% confidence intervals unless they are actually plotted.
- Keywords line: compress to a journal-appropriate set of 5–8 terms.