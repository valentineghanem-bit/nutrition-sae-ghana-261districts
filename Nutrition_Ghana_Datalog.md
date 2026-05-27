# /datalog — Nutritional Status, Anaemia and Child Growth Determinants, Ghana
### Project 10 | Phase 0 | Compiled 2026-05-19

---

## 1. Provenance summary

| File | Source | Rows × Cols | Geographic resolution | Year range | Outcome class |
|------|--------|------------:|-----------------------|------------|---------------|
| nutrition_indicators_gha.csv | WHO Global Health Observatory (GHO) | 8,449 × 17 | **Country** (Ghana, WHO Afro Region) | up to 2024 | Stunting, wasting, underweight, overweight, BMI thinness/obesity, breastfeeding |
| global_strategy_indicators_gha.csv | WHO GHO | 2,428 × 17 | **Country** | up to 2024 | IYCF, BF initiation, maternal nutrition |
| anemia_subnational_gha.csv | DHS Subnational | 1,009 × 30 | **Region** (n=21 location labels covering pre-2022 = 10 regions and post-2022 = 16 regions plus combined groupings) | 2003, 2008, 2014, 2016, 2019, 2022 | Children/women anaemia (any, mild, moderate, severe) |
| iycf_subnational_gha.csv | DHS Subnational | 408 × 30 | **Region** | 1988–2022 | Early BF initiation, exclusive BF, MAD, MDD, MMF, IYCF-3 practices |
| diarrhea_subnational_gha.csv | DHS Subnational | 5,279 × 30 | **Region** | 1988–2022 | Diarrhoea in children under 5, treatment-seeking |
| water_subnational_gha.csv | DHS Subnational | 4,759 × 30 | **Region** | 1993–2022 | Improved drinking water, time to source, water treatment |
| toilet-facilities_subnational_gha.csv | DHS Subnational | 2,675 × 30 | **Region** | 1993–2022 | Improved sanitation, shared toilet, open defecation |
| child-mortality-rates_subnational_gha.csv | DHS Subnational | 744 × 30 | **Region** | 1988–2022 | NMR, IMR, U5MR (post-, neonatal-, child-) |
| select-education-indicators_subnational_gha.csv | DHS Subnational | 653 × 30 | **Region** | 1993–2022 | Maternal/female schooling, literacy, secondary completion |
| select-gender-indicators_subnational_gha.csv | DHS Subnational | 518 × 30 | **Region** | 1993–2022 | Decision-making autonomy, attitudes toward IPV |
| health-insurance_subnational_gha.csv | DHS Subnational | 779 × 30 | **Region** | 2008–2022 | NHIS coverage (women / men / children) |
| Master_Sheet.xlsx | Ghana Statistical Service Population & Housing Census 2021 | 261 × 18 | **District (MMDA)** | 2021 | Lat/long, poverty incidence, poverty intensity, uninsured, illiterate, age-sex pyramid, employment |
| Ghana_New_260_District.geojson | GSS / OCHA Ghana administrative boundaries | 260 features | **District polygons** | 2020/2021 boundary file (16 regions) | Geometry only |

Extraction date for all DHS / WHO files: 2024-12-30. IRB reference: **publicly released aggregate-level data — Ghana Health Service Ethics Review Board waiver category (aggregate, deidentified, secondary-use)**.

---

## 2. Cleaning decisions

1. Drop the hash-banner row (`#date+year`, `#loc+name`, `#indicator+name`) found in every DHS file — it is an HXL tag carrier, not data.
2. Standardise survey year as integer (`SurveyYear`).
3. Restrict primary analytical wave to **2022 GDHS** (single most recent round; all DHS files have 2022 coverage; n = 21 labels for the post-2022 16-region structure plus combined groups).
4. Drop combined groupings (e.g., "Northern, Upper West, Upper East", "..Northern(post 2022)", "..Savannah", "..North East") in favour of the 16 disaggregated post-2022 regions to match the GeoJSON.
5. WHO GHO `Numeric` column is the percentage; the `Value` column appends 95 % CI as text — split into `point`, `lower`, `upper`.
6. Master Sheet districts: 261 vs GeoJSON 260 (the **261st = Guan in Oti**, dropped by the 2020 boundary file). Re-add Guan to the GeoJSON or note as a structural exclusion.
7. Master Sheet ↔ GeoJSON district-name spelling crosswalk: 175/261 exact overlap. 86 spelling variants (e.g., `"Adentan Municipal"` vs `"ADENTA MUNICIPAL"`, `"Accra Metropolitan Area (AMA)…"` vs `"ACCRA METROPOLIS"`) require a fuzzy / manual crosswalk before merge.

---

## 3. DHIMS2-style completeness flags

- **2022 wave coverage** is uniform across the 9 DHS files at the regional level — no completeness gaps below the 80 % threshold within this single-round subset.
- Pooled-trend analyses (1988–2022) have non-uniform earlier-round coverage (especially IYCF practices, which were not collected pre-2008 for MAD/MDD/MMF). Flag for the Methods.

---

## 4. **Structural data-resolution flag (CRITICAL — requires user decision)**

The user-stated scope ("260 districts subnational spatial ML study") cannot be executed directly from this file set, because:

- **Outcome variables** (stunting, wasting, anaemia, IYCF, diarrhoea) exist in the supplied files only at **WHO national** or **DHS region** (16-region) level.
- **District-level (261)** information is present only for **socio-economic covariates** (Master Sheet) and **geometry** (GeoJSON 260).
- There is no district-level DHS dataset for stunting/wasting/anaemia/IYCF among the uploaded files, and the publicly released DHS 2022 subnational tabulations stop at the region level.

This is a known small-area estimation challenge in the field. The three legitimate Q1 study designs that fit the data are:

| Option | Design | n | Spatial methods feasibility | Methodological strength |
|--------|--------|---|-----------------------------|-------------------------|
| **A — 16-region native** | Analyse 16 Ghana regions, GDHS 2022 wave | 16 | Moran's I, LISA, Bivariate LISA at n=16; OLS only; **no GWR**, **no ML** at this n | Most data-honest; smallest sample but valid spatial inference |
| **B — 261-district via Bayesian small-area estimation (SAE)** | Combine region-level DHS direct estimates + district-level covariates (Master Sheet) in BYM/INLA hierarchical model → posterior district stunting/wasting/anaemia | 261 | Full pipeline: BYM smoothing + LISA + Bivariate LISA + GWR + RF/XGBoost on posterior means | Q1-grade; matches the user-requested spatial-ML stack but requires the SAE bridge to be explicit in Methods |
| **C — 261-district by region-to-district downscaling (no SAE)** | Assign each district its parent region's DHS value → run district-level spatial-ML | 261 | All methods nominally feasible but outcome is constant within region — within-region variance is zero | Methodologically weak; reviewers will reject; ecological fallacy unaddressable |

**Recommended:** **Option B (Bayesian small-area estimation, BYM/INLA)** — it is the only path that legitimately produces 261-district stunting/wasting/anaemia maps from the supplied data, and it matches the user's requested method stack (LISA + Bivariate LISA + Moran's I + GWR + RF + XGBoost + SHAP).

---

## 5. Persistent memory anchors (/memory)

```
Project       : Nutritional status, anaemia, child growth determinants — Ghana subnational
Data sources  : WHO GHO 2024 | GDHS 2022 (region) | GSS 2021 Census (district)
Outcome res.  : Region-level (DHS) → district-level via BYM/INLA SAE (proposed Option B)
Covariate res.: District-level (Master Sheet 261)
Geometry      : Ghana_New_260_District.geojson (16 regions; 260 districts; Guan dropped — re-add)
Reference yr  : 2022 (DHS), 2021 (Census), 2024 (WHO GHO)
IRB           : Aggregate secondary-use — Ghana Health Service ERB waiver category
APC policy    : --ghana-apc-lock active
Alpha / CrI   : 0.05 / 95 %
ML stack      : RF + XGBoost (primary) | SHAP mandatory | SMOTE for rare-event outcomes
Spatial stack : Global Moran's I + Bivariate LISA + Getis-Ord Gi* + GWR
Bayesian stack: BYM2 + iCAR (R-INLA primary; PyMC fallback)
Reporting     : STROBE + RECORD + TRIPOD+AI
```

---

## 6. Status

- [x] All 13 raw files copied to `data/raw/`
- [x] Provenance, schema, year, geographic resolution profiled for every file
- [x] /datalog entry written
- [x] Critical data-resolution flag raised (Section 4)
- [ ] **Awaiting Dr. Ghanem's scope decision (Option A / B / C) before Phase 1 strategy lock**

---

**End of Phase 0 — Data Provenance**
