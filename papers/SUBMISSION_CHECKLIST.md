# Submission Checklist — ShieldLab G4 Manuscripts

> **Purpose:** This file lists every submission-blocking item for Paper 1 (scientific) and
> Paper 2 (technical software). It must be reviewed and all items resolved before submitting
> either manuscript to a journal. Items marked **BLOCKER** will cause desk rejection or
> embarrassment if submitted uncorrected.

---

## Paper 1 · `paper1_scientific/manuscript_scientific_v08.md`

### Author / Affiliation
- [ ] **BLOCKER** Replace `[AFFILIATION REQUIRED — DO NOT SUBMIT WITH PLACEHOLDER]` on line 4
  with the full institutional affiliation (department, university, city, country, postal code)
  and any co-author affiliations if applicable.
- [ ] Confirm ORCID iD(s) and add to author block if the target journal requires them.

### Figures
- [ ] All figures referenced in the text (`fig1_parity.png`, `fig2_material_bar.png`,
  `fig3_buildup.png`, `fig4_dose.png`, `fig5_literature.png`, `fig6_stopping.png`,
  `fig7_geant4.png`, `fig8_tyvek_comparison.png`, `fig9_workflow_diagram.png`,
  `fig10_comparison_table.png`) must exist as publication-quality files at
  `paper1_scientific/figures/` before submission.
- [ ] Check that figure resolution meets journal minimum (typically 300 dpi for raster,
  vector preferred for line graphs).

### Data & Code Availability
- [ ] Insert the public repository URL in the Data Availability Statement
  (currently reads "available at the project repository" — needs the actual URL).
- [ ] Insert the Zenodo DOI once the software deposit is finalized.

### References
- [ ] Verify references [16]–[21] (Negm et al.) have correct DOIs and publication details
  (one is listed as 2025, confirm it is published/in-press before submission).

### Acknowledgements
- [ ] Insert journal name once target journal is confirmed (currently says "the editorial team
  of [Journal]" in the Acknowledgements section).
- [ ] Add any grant numbers or funding agency acknowledgements.

### CRediT Author Contributions
- [ ] Confirm CRediT roles with any co-authors.
- [ ] Paper currently lists all roles under a single author — if co-authors are added,
  split the CRediT statement accordingly.

### Technical
- [ ] Run `verify_manuscript.py` and confirm all checks pass before submission package is built.
- [ ] Supplementary Table S1 values are computed from the live codebase — re-run computation
  if `nist_estar.py` or `ion_range.py` is modified after this date.

---

## Paper 2 · `paper2_technical_software/manuscript_technical_software_v02.md`

### Author / Affiliation
- [ ] **BLOCKER** Replace `[AFFILIATION REQUIRED — DO NOT SUBMIT WITH PLACEHOLDER]` on line 4
  with the full institutional affiliation.

### Cover Letter
- [ ] `paper2_technical_software/final/cover_letter.md` line 38 still contains `[Institution]`
  — update it with the real affiliation before submission.

### Data & Code Availability
- [ ] Insert the public repository URL in the Data Availability Statement.
- [ ] Insert the Zenodo DOI once deposit is finalized.

### Test Count
- [ ] Paper 2 cites the number of automated tests. Verify this matches the actual test count
  (`pytest --collect-only -q | tail -5`) before submitting.

### References
- [ ] Reference [6] (Zenodo DOI for ShieldLab G4) must be the finalized Zenodo DOI — do not
  submit with a placeholder URL.

### Technical
- [ ] Run `verify_manuscript.py` and confirm all checks pass.
- [ ] Ensure the Docker image version cited in §6 matches the most recent published release.

---

## Shared Items (Both Papers)

- [ ] Run the full test suite one final time immediately before submission and confirm
  `188 passed, 5 skipped` (or better) with no failures.
- [ ] Confirm the Geant4 version in the manuscripts (11.4) matches the build used for
  all MC results.
- [ ] Ensure `backups/` contains a timestamped snapshot of the code state at submission.

---

*Last updated: 2026-05-17 (automated — Items 1–15 of physics/science roadmap complete).*
