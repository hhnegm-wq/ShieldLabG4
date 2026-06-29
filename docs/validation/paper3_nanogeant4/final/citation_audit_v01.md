# Citation Audit

**Document audited:** `manuscript_nanogeant4_v07.md`

## Summary

The retained bibliography was reviewed to check that the references are real publications or reports and not AI-generated placeholders.

- References 1-11 correspond to established Geant4 papers, Hubbell/NIST attenuation references, Geant4-DNA papers, or standard photon-data-library reports.
- Automated URL verification confirmed direct reachability for several items and publisher-host resolution for others.
- Some DOI targets returned `403` or `418` responses because of publisher bot protection; those responses do not indicate fabricated citations.
- References 12 and 13 were removed from the manuscript because they were not cited in the body text.
- No fabricated or placeholder references were identified in the retained bibliography.

## Verification Notes

1. Ref. 1, Geant4 simulation toolkit paper: DOI syntax and bibliographic metadata match the canonical 2003 NIM A article.
2. Ref. 2, Geant4 developments and applications: DOI resolves to IEEE Xplore, which returned an anti-bot response during automated checking.
3. Ref. 3, Recent developments in Geant4: DOI resolved successfully to Elsevier.
4. Ref. 4, Hubbell 1982 attenuation coefficients: DOI metadata is consistent; automated request ended with a connection reset.
5. Ref. 5, Hubbell 1999 review: DOI resolved successfully to the IOP host.
6. Ref. 6, XCOM: NIST URL reachable with HTTP 200.
7. Ref. 7, NISTIR 5632: established NIST report citation; bibliographic metadata is internally consistent.
8. Ref. 8, Geant4 low-energy cross-section comparison in water: DOI resolved to Wiley, which returned HTTP 403 during automated checking.
9. Ref. 9, Geant4-DNA project paper: DOI resolved to World Scientific, which returned HTTP 403 during automated checking.
10. Ref. 10, gold nanoparticle Geant4 study: DOI resolved successfully to Elsevier.
11. Ref. 11, EPDL97 report: standard LLNL photon-data-library report; bibliographic metadata is consistent with the cited report number.
