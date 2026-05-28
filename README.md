# Small-area Estimation of Childhood Stunting, Anaemia, Infant-Feeding Inadequacy and Diarrhoea Across Ghana's 261 Districts

[![CI](https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts/actions/workflows/ci.yml/badge.svg)](https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts/actions) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/) [![R 4.3+](https://img.shields.io/badge/R-4.3+-blue.svg)](https://www.r-project.org/) [![ORCID](https://img.shields.io/badge/ORCID-0009--0002--8332--0220-green.svg)](https://orcid.org/0009-0002-8332-0220)

**Author:** Valentine Golden Ghanem | Ghana COCOBOD Cocoa Clinic, Accra, Ghana
**ORCID:** [0009-0002-8332-0220](https://orcid.org/0009-0002-8332-0220)
**Affiliation:** Ghana COCOBOD Cocoa Clinic, Accra, Ghana
**Reporting standard:** STROBE · RECORD-Spatial · TRIPOD+AI
**Date:** May 2026
**Status:** Manuscript in preparation

---

## 1. Abstract

**Background.** Ghana's national child-nutrition indicators conceal large regional inequity, but nutrition programmes are planned and budgeted at the district level, where directly-measured estimates are unavailable. This study produces modelled district-level estimates of four child-health outcomes across all 261 districts and identifies their determinants.

**Methods.** Outcome data are the 2022 Ghana DHS direct estimates for the 16 administrative regions — the effective inferential unit; district-level covariates (n = 261) are from the 2021 Population and Housing Census. District posteriors for stunting, anaemia (6–59 months), IYCF inadequacy and diarrhoea were obtained by benchmarked Besag–York–Mollié (BYM2) Bayesian small-area estimation. Spatial structure was assessed with Global Moran's I, LISA, bivariate LISA and Getis-Ord Gi*; spatial non-stationarity with geographically weighted regression (GWR); and determinant importance with Random Forest and XGBoost interpreted by SHAP under spatial leave-one-region-out cross-validation.

**Results.** Modelled district posterior prevalence spans 7.5–34.6% for stunting, 30.5–74.4% for anaemia, 58.5–91.8% for IYCF inadequacy and 4.2–34.1% for diarrhoea. All four surfaces are strongly spatially clustered (Global Moran's I 0.82–0.96; all p = 0.002). SHAP identifies water and sanitation access, female illiteracy and poverty as the dominant determinants. **Seventeen districts — 14 in Northern and 3 in Savannah Region — are confirmed hotspots for all four outcomes simultaneously.**

---

## 2. Research Question & Aims

**Research question:** What is the district-level distribution and structure of childhood stunting, anaemia, infant-feeding inadequacy and diarrhoea across Ghana, and what determinants drive that distribution, given that the underlying survey is powered only to the 16 regions?

**Aims:**
1. Produce modelled district-level posterior estimates (BYM2 benchmarked SAE) for the four outcomes across all 261 districts.
2. Characterise the spatial structure (Global Moran's I, LISA, bivariate LISA, Getis-Ord Gi*) and co-clustering of the four outcomes.
3. Quantify spatial non-stationarity of determinants (GWR vs OLS).
4. Rank determinants with explainable machine learning (XGBoost + SHAP) under honest spatial leave-one-region-out cross-validation.
5. Identify the geographically-concentrated set of districts for targeted child-nutrition investment.

---

## 3. Methods Summary

| Method | Tool | Purpose |
|--------|------|---------|
| BYM2 Bayesian SAE | R-INLA (R 4.2+) | District posterior estimates benchmarked to region direct estimates |
| Global Moran's I (queen + KNN-5 sensitivity) | spdep (R) | Spatial autocorrelation of all four outcomes |
| LISA (999 permutations, BH-FDR) | spdep (R) / esda | Local cluster delineation |
| Bivariate LISA | spdep (R) / esda | Six outcome-pair co-clustering |
| Getis-Ord Gi* | spdep (R) / esda | Hotspot / coldspot detection |
| GWR (adaptive bi-square, AICc-optimal) | mgwr / GWmodel (R) | Spatially varying determinant effects |
| Random Forest + XGBoost + SHAP | scikit-learn / xgboost / shap | Determinant ranking with bootstrapped CIs |
| Spatial LOROCV (16 folds) | Custom | Honest out-of-sample validation |
| Exceedance probability | Custom | P(outcome > national mean) per district |

---

## 4. Data Sources

| Source | Use | Resolution | Access |
|--------|-----|------------|--------|
| Ghana DHS 2022 (GSS · GHS · ICF) | Region direct estimates: stunting, anaemia (6–59 m), IYCF, diarrhoea | 16 regions | Public — [DHS Program FR387](https://dhsprogram.com/pubs/pdf/FR387/FR387.pdf) |
| 2021 Population and Housing Census (GSS) | District covariates: poverty, illiteracy, NHIS, employment, under-15 share, urbanicity | 261 districts | Public — [GSS PHC 2021](https://census2021.statsghana.gov.gh/) |
| Ghana 260-district boundary GeoJSON | Polygons for choropleths and queen-contiguity graph | 260 polygons | `data/raw/Ghana_New_260_District.geojson` |

> No personal identifiers. All inputs are publicly released aggregate data.

---

## 5. Key Findings

| Metric | Value |
|--------|-------|
| Stunting posterior range | 7.5–34.6% |
| Anaemia posterior range | 30.5–74.4% |
| IYCF inadequacy posterior range | 58.5–91.8% |
| Diarrhoea posterior range | 4.2–34.1% |
| Global Moran's I (stunting) | 0.937 (p = 0.002) |
| Global Moran's I (anaemia) | 0.959 (p = 0.002) |
| Stunting × anaemia bivariate Moran's I | 0.78 (49 joint HH districts) |
| Top SHAP determinant | Water and sanitation access |
| Quadruple-burden hotspot districts | **17** (14 Northern + 3 Savannah) |
| XGBoost LOROCV AUC | 0.88 ± 0.04 |

---

## 6. Repository Structure

```
nutrition-sae-ghana-261districts/
├── data/
│   ├── raw/                        # DHS, Census, GeoJSON source files
│   └── processed/                  # Cleaned datasets, posteriors, SHAP outputs
│       └── master_261district_nutrition_FINAL.csv
├── scripts/
│   ├── 01_build_master_dataset.py  # Data integration pipeline
│   ├── 02_build_adjacency.py       # Queen-contiguity graph
│   ├── 03_bym_sae.py               # BYM2 SAE via R-INLA
│   ├── 04_spatial_diagnostics.py
│   ├── 05_gwr.py
│   ├── 06_ml_shap.py
│   ├── 07_consolidate.py … 13_fig5_rebuild.py
│   ├── 14_residual_moran.py        # Residual spatial-autocorrelation check
│   ├── build_poster.py             # A0 conference poster
│   ├── build_dashboard.py          # Interactive HTML dashboard
│   ├── spatial_utils.py            # Reusable spatial analysis utilities
│   └── bym2_diagnostics.R          # BYM2 PPC, LOROCV, residual Moran's I
├── app.py                          # Plotly Dash surveillance dashboard
├── analysis.R                      # BYM2-INLA SAE + spdep spatial diagnostics
├── dashboard/
│   └── Nutrition_Dashboard.html
├── poster/
│   └── Nutrition_Poster.html
├── figures/                        # Manuscript figures (PNG, 300 DPI)
├── tables/                         # Manuscript tables (CSV)
├── tests/
├── run_all.sh                      # One-shot Python pipeline driver
├── requirements.txt
├── Dockerfile
├── CITATION.cff
└── README.md
```

---

## 7. Reproducibility

### 7.1 Requirements

- Python 3.12 (pinned in `requirements.txt`)
- R 4.2+ with packages: INLA, spdep, spatialreg, dplyr (see `analysis.R` header)
- Random seed: 42 throughout; 2,000 posterior draws; 999 permutation iterations
- Estimated runtime: ~20–30 minutes on a standard laptop (BYM2-INLA is compute-intensive)
- Tested on: Ubuntu 22.04 / macOS 14 / Windows 11 (CI: GitHub Actions)

### 7.2 Clone & install

```bash
git clone https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts.git
cd nutrition-sae-ghana-261districts
pip install -r requirements.txt
# Install R-INLA (not on CRAN):
Rscript -e "install.packages('INLA', repos=c(INLA='https://inla.r-inla-download.org/R/stable'), dep=TRUE)"
```

### 7.3 Run the analytical pipeline

```bash
bash run_all.sh
# Or step by step:
python scripts/01_build_master_dataset.py
python scripts/02_build_adjacency.py
Rscript analysis.R
python scripts/04_spatial_diagnostics.py
python scripts/05_gwr.py
python scripts/06_ml_shap.py
```

### 7.4 Run the test suite

```bash
pytest tests/ -v
```

### 7.5 Launch the interactive Dash application

```bash
python app.py
# Visit http://127.0.0.1:8050
```

### 7.6 Open the static HTML dashboard

```bash
# macOS
open dashboard/Nutrition_Dashboard.html
# Windows
start dashboard/Nutrition_Dashboard.html
# Linux
xdg-open dashboard/Nutrition_Dashboard.html
```

---

## 8. Outputs

| Output | Description |
|--------|-------------|
| `data/processed/` | Canonical 261 × 46 master CSV, posteriors, SHAP values, spatial weights |
| `figures/` | Manuscript figures (PNG, 300 DPI) |
| `tables/` | Manuscript tables (CSV) |
| `dashboard/` | Self-contained interactive HTML surveillance dashboard |
| `poster/` | A0 conference poster (HTML, print-ready) |

## 8a. Downloadable Artefacts (HTML)

Both the interactive dashboard and the conference poster are committed as self-contained HTML files — no server, no build step required.

| Artefact | View on GitHub | Live preview | Direct download (raw HTML) |
|----------|---------------|--------------|---------------------------|
| Interactive dashboard | [View](https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts/blob/main/dashboard/Nutrition_Dashboard.html) | [Preview](https://htmlpreview.github.io/?https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts/blob/main/dashboard/Nutrition_Dashboard.html) | [Download](https://raw.githubusercontent.com/valentineghanem-bit/nutrition-sae-ghana-261districts/main/dashboard/Nutrition_Dashboard.html) |
| Conference poster | [View](https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts/blob/main/poster/Nutrition_Poster.html) | [Preview](https://htmlpreview.github.io/?https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts/blob/main/poster/Nutrition_Poster.html) | [Download](https://raw.githubusercontent.com/valentineghanem-bit/nutrition-sae-ghana-261districts/main/poster/Nutrition_Poster.html) |

> **Tip:** The dashboard works fully offline once downloaded. The poster is print-ready at A0 (841 × 1189 mm).

---

## 9. Reporting Standard

This study follows the **STROBE** (Strengthening the Reporting of Observational Studies in Epidemiology) reporting guideline for observational ecological studies. Machine learning components follow **TRIPOD+AI**; spatial statistical components follow **RECORD-Spatial**.

---

## 10. Ethical Statement

This study analyses publicly released aggregate data from the 2022 Ghana Demographic and Health Survey (GSS, GHS, ICF International) and the 2021 Population and Housing Census (Ghana Statistical Service). No personal identifiers were accessed. All inputs are publicly released aggregate statistics at the district or regional level. Ethical review was not required; DHS data were accessed under the standard DHS Programme Data Use Agreement.

---

## 11. Citation

**APA:**
Ghanem, V. G. (2026). *Small-area Estimation of Childhood Stunting, Anaemia, Infant-Feeding Inadequacy and Diarrhoea Across Ghana's 261 Districts.* GitHub. https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts

**BibTeX:**
```bibtex
@misc{ghanem2026nutrition,
  author = {Ghanem, Valentine Golden},
  title  = {Small-area Estimation of Childhood Stunting, Anaemia, Infant-Feeding Inadequacy and Diarrhoea Across Ghana's 261 Districts},
  year   = {2026},
  url    = {https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts}
}
```

A machine-readable citation is provided in `CITATION.cff`.

---

## 12. License

Code is released under the **MIT License** — see [LICENSE](LICENSE) for details.
Outputs and figures: **CC BY 4.0**.

---

## 13. Author & Contact

**Valentine Golden Ghanem**
Ghana COCOBOD Cocoa Clinic, Accra, Ghana
Email: valentineghanem@gmail.com
ORCID: [0009-0002-8332-0220](https://orcid.org/0009-0002-8332-0220)

---

## 14. Acknowledgements

The author thanks the Ghana Statistical Service, Ghana Health Service, and ICF International for the 2022 GDHS and 2021 PHC; the R-INLA team (Rue, Martino, Chopin) for the INLA software used in BYM2-SAE; and the developers of spdep, esda, libpysal, scikit-learn, XGBoost, and SHAP. District estimates are model-based and should be read with their credible intervals.
