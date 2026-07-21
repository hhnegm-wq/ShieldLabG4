# Paper 3 v05 Fix Tracking — Round 1

| # | Reviewer | Comment label | Original text or issue | Fix applied | Location in manuscript | Status |
|---|---|---|---|---|---|---|
| 1 | Internal | W1 | Canonical source file was still named `manuscript_nanogeant4_v03.md` while header said `v04` | Created canonical source `manuscript_nanogeant4_v05.md` and aligned internal version header | Front matter | ✅ Fixed |
| 2 | Internal | W2 | Abstract was 431 words and functioned as a compressed results section | Rewrote abstract to a 4-paragraph final form and reduced it to 201 words by scripted check | Abstract | ✅ Fixed |
| 3 | Internal | W3 | Appendix A contained stale engineering-plan language and outdated completion states | Removed Appendix A entirely so the paper ends after the references section | End matter | ✅ Fixed |
| 4 | Internal | W4 | Figure-style guide had been applied only partially | Updated `paper3_figures.py` with in-script scientific style constants, helper, guide palette, and regenerated the cross-regime figure | Figure generator / Figure F-cross | ✅ Fixed |
| 5 | Internal | W5 | Submission blockers remained in front matter and references | Removed raw affiliation placeholder, inserted verified corresponding-author email, removed placeholder references, normalized Section 9 metadata statements | Front matter, Section 9, References | ✅ Fixed |
| 6 | Internal | W6 | No paper-level verification layer existed | Added `tools/verify_paper3_manuscript_v05.py` and verified the v05 manuscript passes | Verification | ✅ Fixed |
| 7 | R1 | M1 | Cross-regime figure implementation was not robust for regime C and did not visibly support the confidence-interval claim | Reworked `generate_regime_comparison_figure()` to load regime C from `sweep_summary.csv`, plot regime A/B/C together, and add 95% confidence intervals | Figure 5 / canonical generator | ✅ Fixed |
| 8 | R1 | M2 | One figure was insufficient for the paper’s methods/results load | Added a canonical five-figure suite generated from `generate_paper3_figure_suite()` | Figures 1–5 / canonical generator | ✅ Fixed |
| 9 | R1 | M3 | Section 5.4 referenced Table 1 instead of Table 1b for the cross-regime baseline | Rewrote Section 5.4 and corrected the reference to Table 1b | Section 5.4 | ✅ Fixed |
| 10 | R1 | M4 | Keyword count exceeded the production-guide target | Reduced keyword list to 8 targeted terms | Front matter | ✅ Fixed |
| 11 | R2 | M1 | No conceptual regime map or workflow diagram | Added Figure 1 as a regime overview / workflow diagram | Section 3.3 / Figure 1 | ✅ Fixed |
| 12 | R2 | M2 | Scalability result was buried in prose | Added Figure 4 visualizing voxel-cell growth, memory, and feasibility | Section 5.3 / Figure 4 | ✅ Fixed |
| 13 | R2 | M3 | Buildup and downstream spectrum results were not visualized | Added Figure 3 with buildup and downstream spectrum panels | Section 5.1.4 / Figure 3 | ✅ Fixed |