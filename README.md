# Small-area estimation of childhood stunting, anaemia, infant-feeding inadequacy and diarrhoea across the 261 districts of Ghana

A Bayesian spatial and machine-learning analysis of the 2022 Ghana Demographic and Health Survey. Target journal: ***Maternal & Child Nutrition*** (Wiley; Gold Open Access; indexed in DOAJ).

[![QA Passed](https://img.shields.io/badge/QA-PASSED_2026--05--26-brightgreen)](QA_PASSED_2026-05-26.txt) [![Reporting](https://img.shields.io/badge/Reporting-STROBE_%C2%B7_RECORD--Spatial_%C2%B7_TRIPOD%2BAI-1d4e6f)](#9-reporting-standard) [![License: MIT](https://img.shields.io/badge/Code-MIT-blue)](LICENSE) [![Outputs: CC BY 4.0](https://img.shields.io/badge/Outputs-CC_BY_4.0-c25e00)](#11-license)

---

## 1. Abstract

**Background.** Ghana's national child-nutrition indicators conceal large regional inequity, but nutrition programmes are planned and budgeted at the district (metropolitan, municipal and district assembly) level, where directly-measured estimates are unavailable. This study produced modelled district-level estimates of four child-health outcomes across all 261 districts and identified their determinants.

**Methods.** Outcome data were the 2022 Ghana DHS direct estimates for the 16 administrative regions — the effective inferential unit; district-level (n = 261) covariates were the 2021 Population and Housing Census. District posteriors for stunting, anaemia (6–59 months), infant and young child feeding (IYCF) inadequacy and diarrhoea were obtained by benchmarked Besag–York–Mollié (BYM2) Bayesian small-area estimation. Spatial structure was assessed with Global Moran's I, LISA, bivariate LISA and Getis-Ord Gi*; spatial non-stationarity with geographically weighted regression (GWR); determinant importance with Random Forest and XGBoost interpreted by SHAP and validated under spatial leave-one-region-out cross-validation. Reporting followed STROBE, RECORD-Spatial and TRIPOD+AI.

**Results.** Modelled district posterior prevalence spanned 7.5–34.6 % for stunting, 30.5–74.4 % for anaemia, 58.5–91.8 % for IYCF inadequacy and 4.2–34.1 % for diarrhoea. All four surfaces were strongly spatially clustered (Global Moran's I 0.82–0.96; all p = 0.002) and co-located (stunting × anaemia bivariate I = 0.78). Determinant effects were spatially non-stationary (GWR ΔAICc 225–368). SHAP identified water and sanitation access, female illiteracy and poverty as the dominant determinants. **Seventeen districts — 14 in Northern and 3 in Savannah Region — were confirmed hotspots for all four outcomes simultaneously.**

**Conclusions.** A reproducible small-area-estimation pipeline translates region-level survey data into a district burden surface that identifies a finite, geographically-concentrated set of districts for targeted child-nutrition investment. District estimates are model-based and should be read with their credible intervals.

---

## 2. Research question and aims

**Research question.** What is the district-level distribution and structure of childhood stunting, anaemia, infant-feeding inadequacy and diarrhoea across Ghana, and what determinants drive that distribution, given that the underlying survey is powered only to the 16 regions?

**Aims.**

1. Produce modelled district-level posterior estimates (BYM2 benchmarked SAE) for the four outcomes across all 261 districts.
2. Characterise the spatial structure (Global Moran's I, LISA, bivariate LISA, Getis-Ord Gi*) and the co-clustering of the four outcomes.
3. Quantify the spatial non-stationarity of determinants (GWR vs OLS).
4. Rank the determinants with explainable machine learning (XGBoost + SHAP) under honest spatial leave-one-region-out cross-validation.
5. Identify the geographically-concentrated set of districts on which to target child-nutrition investment.

---

## 3. Methods summary

**Design.** Ecological, cross-sectional, spatially-resolved analysis of all 261 MMDAs; reference year 2022.

**Small-area estimation.** Benchmarked Besag–York–Mollié (BYM2) Bayesian model over a queen-contiguity graph of the 261 districts; district means benchmarked to region direct estimates. Penalised-complexity priors. 2 000 posterior draws per outcome.

**Spatial analysis.** Global Moran's I (queen + 5-nearest-neighbour sensitivity); Local Indicators of Spatial Association (LISA) with 999 conditional permutations and Benjamini–Hochberg FDR control; bivariate LISA for the six outcome pairs; Getis-Ord Gi*.

**Non-stationarity.** Geographically weighted regression (GWR) with an adaptive bi-square kernel and AICc-optimal bandwidth; Brunsdon Monte-Carlo permutation test on each coefficient.

**Determinants.** Random Forest and XGBoost; SHAP (native exact TreeSHAP) with 95 % bootstrap intervals. Honest spatial leave-one-region-out cross-validation (16 folds) — no district contributes to both train and test in any fold.

**Hotspot classification.** A district is a confirmed outcome hotspot when the posterior exceedance probability (probability of exceeding the population-weighted national mean) exceeds 0.95.

**Software.** R 4.2+ (INLA, spdep, dplyr) for BYM2-INLA SAE and spatial diagnostics (`analysis.R`); Python 3.10 (numpy, pandas, scikit-learn, xgboost, matplotlib, plotly, dash) for ML, visualisation and build tools; fixed random seed 42.

---

## 4. Data sources

| Source | Use | Resolution | Access |
|---|---|---|---|
| Ghana Demographic and Health Survey 2022 (GSS · GHS · ICF) | Region direct estimates for stunting, anaemia (6–59 m), IYCF, diarrhoea | 16 regions | Public — [DHS Program FR387](https://dhsprogram.com/pubs/pdf/FR387/FR387.pdf) |
| 2021 Population and Housing Census (Ghana Statistical Service) | District covariates (poverty, illiteracy, NHIS, employment, under-15 share, urbanicity, population) | 261 districts | Public — [GSS PHC 2021](https://census2021.statsghana.gov.gh/) |
| Ghana 260-district boundary file | Polygons for choropleths and the queen-contiguity graph | 260 polygons (Guan shares its parent Oti polygon) | `data/raw/Ghana_New_260_District.geojson` |
| DHS Spatial Data Repository (subnational time series) | Background context for water, sanitation, education, gender, anaemia and diarrhoea trends | Region | `data/raw/*_subnational_gha.csv` |

No personal identifiers; all inputs are publicly-released aggregate data.

---

## 5. Key findings

- **District posterior prevalence ranges (modelled):** stunting **7.5–34.6 %**, anaemia **30.5–74.4 %**, IYCF inadequacy **58.5–91.8 %**, diarrhoea **4.2–34.1 %**.
- **All four surfaces are strongly spatially clustered.** Global Moran's I = 0.937 (stunting), 0.959 (anaemia), 0.836 (IYCF), 0.821 (diarrhoea); all p = 0.002.
- **Co-clustering is strongest for stunting × anaemia** (bivariate Moran's I = 0.78; 49 joint High-High districts).
- **Determinant effects are spatially non-stationary** (GWR ΔAICc over OLS = 225–368).
- **Top determinants (SHAP):** water and sanitation access, female illiteracy and poverty.
- **Quadruple-burden core:** **17 districts** — 14 Northern + 3 Savannah — are confirmed hotspots (P > 0.95) for all four outcomes simultaneously.
- The regional gradient explains most of the global spatial signal: within-region residual Moran's I drops to 0.35–0.43 (still p = 0.002), confirming a primary regional driver with non-trivial residual district-level clustering.

---

## 6. Repository structure

```
.
├── data/
│   ├── raw/                       Public source files (DHS, Census, GeoJSON)
│   └── processed/                 Cleaned datasets, spatial weights, posteriors, SHAP
│       └── master_261district_nutrition_FINAL.csv   ← canonical 261 × 46 dataset
├── figures/                       Manuscript figures (PNG, 300 DPI)
├── tables/                        Manuscript tables (CSV)
├── scripts/                       Python analysis pipeline (01_* … 14_*) + builders
│   ├── 01_build_master_dataset.py
│   ├── 02_build_adjacency.py
│   ├── 03_bym_sae.py
│   ├── 04_spatial_diagnostics.py
│   ├── 05_gwr.py
│   ├── 06_ml_shap.py, 06a_*, 06b_*, 06c_*
│   ├── 07_consolidate.py
│   ├── 08_reconcile.py
│   ├── 09_figures_maps.py
│   ├── 10_figures_stats.py … 13_fig5_rebuild.py
│   ├── 14_residual_moran.py       ← residual spatial-autocorrelation check
│   ├── build_manuscript.js        Q1 docx builder (Vancouver, STROBE)
│   ├── build_poster.py            A0 landscape conference poster (self-contained)
│   └── build_dashboard.py         Interactive HTML surveillance dashboard
├── dashboard/Nutrition_Dashboard.html    Self-contained interactive dashboard
├── poster/Nutrition_Poster.html          A0-landscape conference poster
├── analysis.R                     BYM2-INLA SAE + spdep spatial diagnostics (R)
├── app.py                         Interactive Dash surveillance dashboard
├── QA_PASSED_2026-05-26.txt       QA badge
├── SYNC_REPORT_2026-05-26.md      Sync validation report
├── Nutrition_Ghana_Datalog.md     Data quality and source log
├── run_all.sh                     One-shot Python pipeline driver
├── requirements.txt               Pinned Python dependencies
├── CITATION.cff                   Machine-readable citation
├── Dockerfile                     Containerised analysis environment
├── .github/workflows/ci.yml       Linting + smoke tests on push/PR
├── .gitignore
├── LICENSE                        MIT (code); outputs CC BY 4.0
└── README.md
```

---

## 7. Reproducibility

### 7.1 Requirements

- Python 3.10+ — `requirements.txt` (numpy, pandas, scikit-learn, xgboost, matplotlib, plotly, dash, python-docx, qrcode).
- R 4.2+ — `INLA`, `spdep`, `dplyr`, `readr` (see §7.8).
- Node.js 18+ (for `scripts/build_manuscript.js`).
- ~2 GB free disk space (figures + dashboard are large self-contained artefacts).

### 7.2 Clone and install

```bash
git clone https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts.git
cd nutrition-sae-ghana-261districts

# Python dependencies
pip install -r requirements.txt

# Node dependencies (manuscript builder)
npm install docx@8.5.0

# R dependencies (BYM2-INLA + spatial diagnostics)
Rscript -e "install.packages(c('spdep','dplyr','readr'), repos='https://cloud.r-project.org')"
Rscript -e "if (!requireNamespace('INLA', quietly=TRUE)) install.packages('INLA', repos=c(INLA='https://inla.r-inla-download.org/R/stable'), dep=TRUE)"
```

### 7.3 Run the analytical pipeline

```bash
bash run_all.sh
```

Or invoke each stage manually:

```bash
python scripts/01_build_master_dataset.py
python scripts/02_build_adjacency.py
python scripts/03_bym_sae.py
python scripts/04_spatial_diagnostics.py
python scripts/05_gwr.py
python scripts/06_ml_shap.py
python scripts/06a_ml_cv.py
python scripts/06b_shap.py
python scripts/06c_hotspot.py
python scripts/07_consolidate.py
python scripts/08_reconcile.py
python scripts/14_residual_moran.py
```

### 7.4 Build the manuscript

```bash
node scripts/build_manuscript.js     # → manuscript/Nutrition_Manuscript.docx
```

### 7.5 Build the conference poster

```bash
python scripts/build_poster.py       # → poster/Nutrition_Poster.html
```

### 7.6 Open the static HTML dashboard

```bash
python scripts/build_dashboard.py    # → dashboard/Nutrition_Dashboard.html
# then open dashboard/Nutrition_Dashboard.html in any modern browser
```

The dashboard is fully self-contained: Plotly.js v3.5.0 is inlined at build time, so the file works offline and requires no CDN.

### 7.7 Run the interactive dashboard app

```bash
python app.py   # → http://127.0.0.1:8050
```

### 7.8 Run R analysis (BYM2-INLA SAE + spatial diagnostics)

```bash
Rscript analysis.R
```

Runs the INLA BYM2 model for each outcome, outputs posterior summaries to `data/processed/`, and prints Global Moran's I, LISA and model-fit diagnostics to console.

### 7.9 Run inside Docker (optional)

```bash
docker build -t ghana-nutrition-sae .
docker run --rm -v "$PWD":/work -w /work ghana-nutrition-sae bash run_all.sh
```

---

## 8. Outputs

| Output | Path |
|---|---|
| Poster (HTML, self-contained) | `poster/Nutrition_Poster.html` |
| Interactive dashboard (HTML, self-contained) | `dashboard/Nutrition_Dashboard.html` |
| Live Dash app | `app.py` (run `python app.py`) |
| Master district dataset (CSV) | `data/processed/master_261district_nutrition_FINAL.csv` |
| Canonical-values register | `data/processed/Canonical_Values_Nutrition.csv` |
| Figures (300 DPI PNG) | `figures/` |
| Tables (CSV) | `tables/` |
| QA badge | `QA_PASSED_2026-05-26.txt` |

---

## 9. Reporting standard

This study follows the **STROBE** (Strengthening the Reporting of Observational Studies in Epidemiology) checklist for observational ecological studies, the **RECORD-Spatial** extension for studies using routinely-collected spatial data, and the **TRIPOD+AI** guidance for the machine-learning prediction component.

---

## 10. Citation

**APA.** Ghanem, V. G. (2026). *Small-area estimation of childhood stunting, anaemia, infant-feeding inadequacy and diarrhoea across the 261 districts of Ghana: a Bayesian spatial and machine-learning analysis of the 2022 Demographic and Health Survey* [Computer software and dataset]. GitHub. https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts

**BibTeX.**

```bibtex
@misc{ghanem2026nutritionsae,
  author = {Ghanem, Valentine Golden},
  title  = {Small-area estimation of childhood stunting, anaemia, infant-feeding inadequacy and diarrhoea across the 261 districts of Ghana: a Bayesian spatial and machine-learning analysis of the 2022 Demographic and Health Survey},
  year   = {2026},
  url    = {https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts}
}
```

A machine-readable citation is provided in [`CITATION.cff`](CITATION.cff).

---

## 11. License

**Code** is released under the **MIT License** — see [`LICENSE`](LICENSE) for details. **Outputs and figures** (manuscript, poster, dashboard, derived tables and figures, processed CSVs): **CC BY 4.0** — re-use freely with attribution to the author and to the underlying GDHS 2022 and PHC 2021 data sources.

---

## 12. Author and contact

**Valentine Golden Ghanem**
Ghana COCOBOD Cocoa Clinic, Accra, Ghana
Email: valentineghanem@gmail.com
ORCID: [0009-0002-8332-0220](https://orcid.org/0009-0002-8332-0220)

---

## 13. Acknowledgements

The author thanks the **Ghana Statistical Service (GSS)**, the **Ghana Health Service (GHS)** and **ICF** for the 2022 Ghana Demographic and Health Survey and the 2021 Population and Housing Census, both released as public-good aggregate data; the **DHS Program** for the Spatial Data Repository; and the open-source scientific Python and Plotly communities for the analytical and visualisation libraries that made the pipeline possible. The work was conducted independently and received no specific external funding.
