#!/usr/bin/env bash
# run_all.sh — one-shot driver for the Ghana child-nutrition SAE pipeline.
# Usage:  bash run_all.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "==> 1/14  Build the master district dataset"
python scripts/01_build_master_dataset.py

echo "==> 2/14  Build the queen-contiguity and 5-NN spatial weights"
python scripts/02_build_adjacency.py

echo "==> 3/14  Benchmarked BYM2 small-area estimation"
python scripts/03_bym_sae.py

echo "==> 4/14  Spatial diagnostics (Moran's I, LISA, bivariate LISA, Getis-Ord Gi*)"
python scripts/04_spatial_diagnostics.py

echo "==> 5/14  Geographically weighted regression (GWR)"
python scripts/05_gwr.py

echo "==> 6/14  Machine learning + SHAP determinants"
python scripts/06_ml_shap.py
python scripts/06a_ml_cv.py
python scripts/06b_shap.py
python scripts/06c_hotspot.py

echo "==> 7/14  Consolidate outputs"
python scripts/07_consolidate.py

echo "==> 8/14  Reconcile values against the Canonical Values Register"
python scripts/08_reconcile.py

echo "==> 9/14  Choropleth and cluster maps"
python scripts/09_figures_maps.py

echo "==> 10/14  Statistical figures"
python scripts/10_figures_stats.py
python scripts/11_fig6_rebuild.py
python scripts/13_fig5_rebuild.py

echo "==> 11/14  Manuscript tables"
python scripts/12_tables.py

echo "==> 12/14  Residual spatial-autocorrelation check"
python scripts/14_residual_moran.py

echo "==> 13/14  Build the manuscript (.docx)"
node scripts/build_manuscript.js

echo "==> 14/14  Build the conference poster (.html) and interactive dashboard (.html)"
python scripts/build_poster.py
python scripts/build_dashboard.py

echo
echo "Pipeline complete. Outputs:"
echo "  Manuscript : manuscript/Nutrition_Manuscript.docx"
echo "  Poster     : poster/Nutrition_Poster.html"
echo "  Dashboard  : dashboard/Nutrition_Dashboard.html"
echo "  Master CSV : data/processed/master_261district_nutrition_FINAL.csv"
