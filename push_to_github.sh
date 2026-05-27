#!/usr/bin/env bash
# /github-publish — Nutrition Anaemia Growth Determinants Ghana 261 Districts
# Pattern: EX-007 (/tmp clone-and-push) — git operations on Windows /mnt paths fail
#
# Usage:
#   1. Ensure ~/.claude/github.env contains:
#        export GITHUB_PAT=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
#   2. Run: bash push_to_github.sh
#
# Prerequisites confirmed:
#   ✓ QA_PASSED_2026-05-26.txt badge present
#   ✓ SYNC_REPORT_2026-05-26.md present
#   ✓ 17 quadruple-burden hotspot districts confirmed
#
# Repo URL: https://github.com/valentineghanem-bit/nutrition-sae-ghana-261districts
set -euo pipefail

SRC="/c/Users/VGhanem/Documents/Claude/Projects/Public Health & Epidemiology Research Skills/10. Nutrition Anaemia Growth Determinants Ghana 261 Districts"
TMP="/tmp/nutrition_ghana_clean_repo"
REPO_SLUG="nutrition-sae-ghana-261districts"
GH_USER="valentineghanem-bit"

# Load PAT (do not log)
if [[ -f ~/.claude/github.env ]]; then
  source ~/.claude/github.env
elif [[ -z "${GITHUB_PAT:-}" ]]; then
  echo "ERROR: GITHUB_PAT not set. Add ghp_... to ~/.claude/github.env"
  exit 1
fi

echo "[1/6] Clone source to /tmp (EX-007 — Windows path git ops unreliable)"
rm -rf "$TMP"
mkdir -p "$TMP"

# Copy all files then remove excluded items (rsync unavailable on Windows Git Bash)
cp -rp "$SRC/." "$TMP/"

# Remove: manuscripts (Tenet 20 — NEVER commit)
rm -rf "$TMP/manuscript" "$TMP"/*.docx "$TMP"/**/*.docx 2>/dev/null || true
find "$TMP" -name '*.docx' -delete 2>/dev/null || true
find "$TMP" -name '~$*' -delete 2>/dev/null || true

# Remove: AIPOCH working / phase documents
find "$TMP" -maxdepth 1 -name 'Phase*_*.md' -delete 2>/dev/null || true
find "$TMP" -maxdepth 1 -name 'Phase*.mermaid' -delete 2>/dev/null || true
find "$TMP" -maxdepth 1 -name 'QA_Audit_Report*.md' -delete 2>/dev/null || true
find "$TMP" -maxdepth 1 -name 'PUSH_HANDOFF.md' -delete 2>/dev/null || true
find "$TMP" -maxdepth 1 -name 'AIPOCH_Learning_Log*.md' -delete 2>/dev/null || true
find "$TMP" -maxdepth 1 -name 'QA_CONDITIONAL_*.txt' -delete 2>/dev/null || true
find "$TMP" -maxdepth 1 -name 'publish.ps1' -delete 2>/dev/null || true

# Remove: preview / clip images
find "$TMP" -name '_preview_*.png' -delete 2>/dev/null || true
find "$TMP" -name '_pv*.png' -delete 2>/dev/null || true
find "$TMP" -name '_clip_*.png' -delete 2>/dev/null || true
find "$TMP" -name '_dash_*.png' -delete 2>/dev/null || true

# Remove: Python build artefacts
find "$TMP" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "$TMP" -name '*.pyc' -delete 2>/dev/null || true

# Remove: git dir if accidentally copied
rm -rf "$TMP/.git" 2>/dev/null || true

echo "[2/6] Initialise git + LFS"
cd "$TMP"
git init -q
git lfs install 2>/dev/null || true
git lfs track "*.png" "*.geojson" "*.npy" 2>/dev/null || true
git add .gitattributes 2>/dev/null || true

echo "[3/6] Configure remote and identity"
git config user.email "valentineghanem@gmail.com"
git config user.name "Valentine Golden Ghanem"
git remote add origin "https://${GH_USER}:${GITHUB_PAT}@github.com/${GH_USER}/${REPO_SLUG}.git"

echo "[4/6] Stage and commit"
git add -A
git commit -q -m "Initial release v1.0.0 — Nutrition/Anaemia/Growth Ghana 261-district Bayesian spatial ML

QA_PASSED 2026-05-26.
Study: Small-area estimation of childhood stunting, anaemia, IYCF inadequacy
and diarrhoea across the 261 districts of Ghana (2022 GDHS; 2021 PHC covariates).

- 17 quadruple-burden hotspot districts (14 Northern + 3 Savannah; all 4 outcomes)
- Spatial clustering: Global Moran's I 0.82-0.96 (all p = 0.002)
- Within-region residual Moran's I 0.35-0.43 (p = 0.002)
- BYM-SAE Bayesian posteriors + XGBoost + SHAP determinants
- Master CSV 261 districts; 9 canonical figures; dashboard + poster
- Reporting: STROBE · RECORD-Spatial · TRIPOD+AI
- Target: Maternal & Child Nutrition (Wiley; Gold OA; DOAJ)"

echo "[5/6] Push to main"
git branch -M main
git push -u origin main 2>&1 | grep -v "^remote: "

echo "[6/6] Confirm"
echo ""
echo "Published: https://github.com/${GH_USER}/${REPO_SLUG}"
echo "Latest commit: $(git rev-parse --short HEAD)"
echo "QA badge: QA_PASSED_2026-05-26.txt"
