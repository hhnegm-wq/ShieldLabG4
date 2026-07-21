# Paper 3 v04 Roast and Recovery Plan

## No-Holds-Barred Roast

This is not a submission-ready paper. It is a strong technical draft wearing a submission costume. The physics results are real, the regime-C rescue is real, and the core benchmark story is publishable, but the document still exposes its engineering history on nearly every page. The manuscript says `v04`, but the canonical source file is still named `manuscript_nanogeant4_v03.md`; that alone tells a reviewer the production discipline is lagging behind the science.

The abstract is the clearest example of scope creep defeating craft. At 431 words, it is not an abstract anymore; it is a compressed results section. It tries to carry every regime, every percentage, every implementation detail, and every hardware-scaling anecdote all at once. Instead of giving the editor a clean argument, it dumps the whole lab notebook on the front page.

The front matter is still visibly unfinished. The affiliation is a hard placeholder. The corresponding author line is a hard placeholder. Two references are still hard placeholders. Those are not minor polish misses; they are submission blockers. A paper can survive an awkward sentence. It does not survive "DO NOT SUBMIT WITH PLACEHOLDER" printed in the author block.

The appendix is worse than dead weight: it actively damages credibility. It still calls itself an implementation plan, still says regime B was "in progress," still says regime C was pending, and still lists tasks that are already complete. That makes the manuscript read like a stitched-together project log rather than a finished scientific paper. Any careful reviewer who reaches Appendix A will immediately wonder what else in the paper is stale.

The figure-style application was partial, not full. The cross-regime figure was improved, but the figure module still contains non-compliant styling in other functions, and the palette used for regimes B and C still diverges from the attached guide. That means the claimed style-guide compliance is overstated.

The paper’s scientific core is stronger than its editorial discipline. Right now the science is carrying the manuscript harder than the manuscript is carrying the science.

## Executive Roast

The paper is publishable in substance but not yet credible in production quality. The current version still contains submission-blocking placeholders, a bloated abstract, stale engineering appendix content, inconsistent version/file discipline, and only partial application of the attached figure guide. Reviewers would see a technically serious benchmark wrapped in an unfinished manuscript package.

## Structural Weaknesses List

1. **Canonical version control is broken.** The active source file is still named `manuscript_nanogeant4_v03.md` while the internal header says `v04`.
2. **Submission-blocking placeholders remain.** Affiliation, corresponding author email, and two reference entries are unresolved.
3. **Abstract violates the production guide.** It is 431 words, not the guide target of 200-250 words, and behaves like a mini-results section instead of a disciplined final abstract.
4. **Appendix A is stale and self-undermining.** It still contains project-management language, outdated statuses, and pre-completion task lists.
5. **Figure-style compliance is incomplete.** The figure module only partially implements the attached guide, and the color mapping still diverges from the stated palette.
6. **Final-manuscript metadata is incomplete.** Funding/data/contact/submission metadata are not fully normalized to a final-paper standard.
7. **The manuscript lacks a scripted verification layer.** There is no explicit paper-level verification script to assert that key production fixes are present.

## Step-by-Step Roadmap

1. **Establish a canonical next version.** Create a new source file with a matching versioned filename and header before further revision.
2. **Fix version discipline and verify.** Confirm that source filename, internal version header, and exported DOCX version all match.
3. **Resolve or quarantine submission blockers.** Replace hard placeholders where possible; where external author metadata is missing, convert them into clearly isolated final-input requirements rather than leaving raw placeholders in the paper body.
4. **Rewrite the abstract to guide-compliant form.** Target 200-250 words, four-part structure, and only numbers that are essential and already supported in the body.
5. **Remove or replace the stale appendix.** Either delete it or convert it into a final reproducibility appendix that contains only current facts.
6. **Apply the full figure guide in the codebase.** Update the figure module so the style constants, legend settings, spine/tick behavior, and palette match the attached guide everywhere relevant.
7. **Normalize final metadata sections.** Ensure data availability, funding status, author/contact block, and manuscript versioning read like a final paper package.
8. **Add a verification script.** Script checks for key phrases, placeholder absence, appendix removal, and version consistency.
9. **Export a clean new version.** Generate a new DOCX only after the source passes the verification script.

## Sequential Fix Order for This Revision Round

1. Canonical version/file alignment
2. Abstract rewrite
3. Appendix cleanup
4. Figure-style full compliance
5. Metadata normalization and placeholder cleanup where possible
6. Verification script
7. Final export

## Verification Rule

Each item above should be completed fully, then checked immediately before moving to the next item. No parallel editing across multiple unresolved weaknesses.