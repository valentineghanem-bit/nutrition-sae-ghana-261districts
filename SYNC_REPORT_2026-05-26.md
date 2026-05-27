# Cross-Artifact Sync Report

**Project:** Project 10 — Ghana child-nutrition small-area estimation
**Date:** 2026-05-26
**Repo slug:** `nutrition-sae-ghana-261districts`
**Target host:** https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts
**Verdict:** **SYNC_PASS** — all 16 cross-artifact checks concordant.

## Sync Manifest (12 fields)

| Field | Value |
|---|---|
| study_title | Small-area estimation of childhood stunting, anaemia, infant-feeding inadequacy and diarrhoea across the 261 districts of Ghana: a Bayesian spatial and machine-learning analysis of the 2022 Demographic and Health Survey |
| authors | Valentine Golden Ghanem |
| affiliations | Ghana COCOBOD Cocoa Clinic, Accra, Ghana |
| study_period | 2022 (2022 GDHS; 2021 PHC covariates) |
| geographic_scope | All 261 districts (MMDAs) of Ghana; 16 regions are the effective inferential unit |
| sample_size_N | 261 districts; 16 regions |
| primary_outcome | Modelled district-level posterior prevalence of childhood stunting, anaemia (6-59 m), IYCF inadequacy and diarrhoea |
| primary_result | 17 quadruple-burden hotspot districts (14 Northern + 3 Savannah) confirmed for all four outcomes |
| top_finding_1 | All four surfaces strongly spatially clustered (Global Moran's I 0.82-0.96; all p = 0.002) |
| top_finding_2 | Within-region residual Moran's I 0.35-0.43 (p = 0.002) - regional gradient is the dominant signal; non-trivial within-region clustering persists |
| reporting_guideline | STROBE; RECORD-Spatial; TRIPOD+AI |
| target_journal | Maternal & Child Nutrition (Wiley; Gold OA; DOAJ) |

## Check log

| Field | Manuscript | Poster | Dashboard | README | CITATION.cff | Status |
|---|---|---|---|---|---|---|
| study_title | ✓ | ✓ | — (deliverable title) | ✓ | ✓ | PASS |
| author full-string | ✓ | ✓ | ✓ | ✓ | (structured) | PASS |
| author structured (CITATION.cff YAML) | — | — | — | — | ✓ | PASS |
| ORCID | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| affiliation | ✓ | ✓ | ✓ | ✓ | — | PASS |
| 261 districts | ✓ | ✓ | ✓ | ✓ | — | PASS |
| 16 regions / 16 GDHS regions | ✓ | ✓ | ✓ | ✓ | — | PASS |
| Moran's I 0.82–0.96 | ✓ | ✓ | ✓ | ✓ | — | PASS |
| 17 quadruple-burden districts | ✓ | ✓ | ✓ | ✓ | — | PASS |
| Bivariate I 0.78 | ✓ | ✓ | ✓ | ✓ | — | PASS |
| STROBE | ✓ | ✓ | ✓ | ✓ | — | PASS |
| RECORD-Spatial | ✓ | ✓ | ✓ | ✓ | — | PASS |
| TRIPOD+AI | ✓ | ✓ | ✓ | ✓ | — | PASS |
| GDHS 2022 attribution | ✓ | ✓ | — | ✓ | ✓ | PASS |
| Target journal *Maternal & Child Nutrition* | — | — | — | ✓ | — | PASS (README-only by design) |

**Notes.**
1. The manuscript is excluded from the git commit per Tenet 20 (manuscripts go to journals; repos hold code + outputs).
2. The dashboard title intentionally uses a deliverable-appropriate framing ("district surveillance dashboard, 261 districts of Ghana") rather than the full manuscript title; author, ORCID, sample, methods and statistics are identical.
3. CITATION.cff carries `Valentine Golden` (given-names) + `Ghanem` (family-names) per the CFF 1.2 schema — equivalent to the inline "Valentine Golden Ghanem" used elsewhere.
4. Target journal appears in README and Phase12_Dissemination_Package.md only — manuscripts do not normally declare the target journal in the body.
