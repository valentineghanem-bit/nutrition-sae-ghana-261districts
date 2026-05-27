# analysis.R — Nutrition Anaemia Growth Determinants Ghana 261 Districts
# BYM2-INLA small-area estimation + spdep spatial diagnostics
# Author: Valentine Golden Ghanem | ORCID: 0009-0002-8332-0220
# Usage:  Rscript analysis.R
# Outputs: data/processed/ — posterior CSVs + spatial diagnostic summaries

suppressPackageStartupMessages({
  library(INLA)
  library(spdep)
  library(dplyr)
  library(readr)
})
set.seed(42)

DATA_DIR <- "data/processed"
OUT_DIR  <- "data/processed"

# ── 1. Load master dataset ────────────────────────────────────────────────────
cat("── Loading master dataset ────────────────────────────────────────────\n")
df <- read_csv(file.path(DATA_DIR, "master_261district_nutrition_FINAL.csv"),
               show_col_types = FALSE)
cat(sprintf("Loaded: %d districts × %d variables\n", nrow(df), ncol(df)))

OUTCOMES <- c("stunting_prev", "anaemia_prev", "iycf_inadequacy_prev", "diarrhoea_prev")
# fall back gracefully if exact column names differ
OUTCOMES <- intersect(OUTCOMES, names(df))
if (length(OUTCOMES) == 0) {
  # Try common naming variants
  cands <- grep("stunt|anaem|iycf|diarr", names(df), value = TRUE, ignore.case = TRUE)
  OUTCOMES <- head(cands, 4)
}
cat(sprintf("Outcome columns resolved: %s\n", paste(OUTCOMES, collapse = ", ")))

COVARS <- intersect(
  c("poverty_rate", "female_illiteracy", "water_access", "sanitation_access",
    "nhis_coverage", "pop_density", "under15_share", "urbanicity"),
  names(df)
)
cat(sprintf("Covariate columns: %s\n", paste(COVARS, collapse = ", ")))

# ── 2. Spatial weights (queen contiguity) ────────────────────────────────────
cat("\n── Spatial weights (queen contiguity) ───────────────────────────────\n")
W_mat <- NULL
nb    <- NULL

# Try to build neighbour list from the adjacency report or GeoJSON
geojson_path <- "data/raw/Ghana_New_260_District.geojson"
if (requireNamespace("sf", quietly = TRUE) && file.exists(geojson_path)) {
  sf_obj <- sf::st_read(geojson_path, quiet = TRUE)
  nb     <- poly2nb(sf_obj, queen = TRUE)
  W_mat  <- nb2listw(nb, style = "W", zero.policy = TRUE)
  cat(sprintf("Built queen-contiguity weights: %d polygons\n", length(nb)))
} else {
  # Fall back to KNN-5 on district index (approximate)
  message("sf/GeoJSON not available — falling back to index-based KNN-5 weights.")
  n      <- nrow(df)
  coords <- cbind(seq_len(n), rep(0, n))
  knn5   <- knearneigh(coords, k = 5)
  nb     <- knn2nb(knn5)
  W_mat  <- nb2listw(nb, style = "W")
}

# ── 3. Global Moran's I for each outcome ─────────────────────────────────────
cat("\n── Global Moran's I ──────────────────────────────────────────────────\n")
moran_rows <- list()
for (v in OUTCOMES) {
  vals <- df[[v]]
  if (sum(!is.na(vals)) > 10) {
    mi <- moran.test(vals, W_mat, randomisation = TRUE, na.action = na.exclude,
                     zero.policy = TRUE)
    cat(sprintf("  %-30s  I = %6.4f   z = %6.3f   p = %.4f\n",
                v, mi$estimate[1], mi$statistic, mi$p.value))
    moran_rows[[v]] <- data.frame(
      outcome = v, moran_I = round(mi$estimate[1], 4),
      z_score = round(mi$statistic, 3), p_value = round(mi$p.value, 4)
    )
  }
}
moran_df <- do.call(rbind, moran_rows)
write_csv(moran_df, file.path(OUT_DIR, "r_moran_global.csv"))
cat(sprintf("  → Saved: %s/r_moran_global.csv\n", OUT_DIR))

# ── 4. BYM2 model via INLA (one model per outcome) ───────────────────────────
cat("\n── BYM2-INLA small-area estimation ──────────────────────────────────\n")

# Build node-edge adjacency for INLA BYM2
# INLA needs an nb2INLA adjacency file
adj_file <- tempfile(fileext = ".adj")
nb2INLA(adj_file, nb)
g <- inla.read.graph(adj_file)

n_districts <- nrow(df)
df$district_idx <- seq_len(n_districts)   # node index for INLA random effect

posterior_rows <- list()

for (v in OUTCOMES) {
  if (!v %in% names(df)) next
  cat(sprintf("\n  Fitting BYM2 for: %s\n", v))
  df$y_scaled <- df[[v]]

  # Covariate formula — include only available columns
  fml_covars <- if (length(COVARS) > 0) {
    paste(COVARS, collapse = " + ")
  } else {
    "1"
  }

  fml <- as.formula(paste(
    "y_scaled ~ 1 +", fml_covars,
    "+ f(district_idx, model='bym2', graph=g,",
    "    hyper=list(prec=list(prior='pc.prec', param=c(1, 0.01)),",
    "               phi=list(prior='pc', param=c(0.5, 0.5))))"
  ))

  fit <- tryCatch(
    inla(fml,
         family     = "gaussian",
         data       = df,
         control.compute = list(dic = TRUE, waic = TRUE, cpo = TRUE),
         control.predictor = list(compute = TRUE),
         verbose    = FALSE),
    error = function(e) {
      cat(sprintf("    INLA failed for %s: %s\n", v, conditionMessage(e)))
      NULL
    }
  )

  if (is.null(fit)) next

  cat(sprintf("    DIC = %.2f   WAIC = %.2f\n",
              fit$dic$dic, fit$waic$waic))

  # Extract posterior means and 95% credible intervals for each district
  lin_pred <- fit$summary.fitted.values
  post_df  <- data.frame(
    district_idx     = seq_len(nrow(lin_pred)),
    outcome          = v,
    posterior_mean   = round(lin_pred$mean, 4),
    posterior_sd     = round(lin_pred$sd, 4),
    lower_95ci       = round(lin_pred$`0.025quant`, 4),
    upper_95ci       = round(lin_pred$`0.975quant`, 4),
    dic              = round(fit$dic$dic, 2),
    waic             = round(fit$waic$waic, 2)
  )
  posterior_rows[[v]] <- post_df

  # Spatial random effect (combined BYM2)
  re_df <- fit$summary.random$district_idx
  re_out <- data.frame(
    district_idx = re_df$ID,
    outcome      = v,
    re_mean      = round(re_df$mean, 4),
    re_sd        = round(re_df$sd, 4)
  )
  write_csv(re_out, file.path(OUT_DIR, paste0("r_bym2_re_", v, ".csv")))
}

if (length(posterior_rows) > 0) {
  posteriors_all <- do.call(rbind, posterior_rows)
  write_csv(posteriors_all, file.path(OUT_DIR, "r_bym2_posteriors.csv"))
  cat(sprintf("\n  → Saved: %s/r_bym2_posteriors.csv (%d rows)\n",
              OUT_DIR, nrow(posteriors_all)))
} else {
  cat("  No posterior results to save.\n")
}

# ── 5. LISA (Local Moran's I) for stunting and anaemia ───────────────────────
cat("\n── Local Moran's I (LISA) ────────────────────────────────────────────\n")
lisa_rows <- list()

for (v in head(OUTCOMES, 2)) {
  vals <- df[[v]]
  if (sum(!is.na(vals)) > 10) {
    lm_i <- localmoran(vals, W_mat, na.action = na.exclude, zero.policy = TRUE)
    quadrant <- rep("NS", nrow(lm_i))
    # Significant at p < 0.05
    sig <- lm_i[, 5] < 0.05
    z_vals    <- scale(vals)[, 1]
    z_lagged  <- lag.listw(W_mat, vals, zero.policy = TRUE)
    z_lag_sc  <- scale(z_lagged)[, 1]
    quadrant[sig & z_vals > 0 & z_lag_sc > 0] <- "HH"
    quadrant[sig & z_vals < 0 & z_lag_sc < 0] <- "LL"
    quadrant[sig & z_vals > 0 & z_lag_sc < 0] <- "HL"
    quadrant[sig & z_vals < 0 & z_lag_sc > 0] <- "LH"
    tab <- table(quadrant)
    cat(sprintf("  %-30s  HH=%d  LL=%d  HL=%d  LH=%d\n",
                v,
                sum(quadrant == "HH"), sum(quadrant == "LL"),
                sum(quadrant == "HL"), sum(quadrant == "LH")))
    lisa_rows[[v]] <- data.frame(
      district_idx = seq_len(nrow(lm_i)),
      outcome      = v,
      local_moran_I = round(lm_i[, 1], 4),
      p_value       = round(lm_i[, 5], 4),
      quadrant      = quadrant
    )
  }
}

if (length(lisa_rows) > 0) {
  lisa_all <- do.call(rbind, lisa_rows)
  write_csv(lisa_all, file.path(OUT_DIR, "r_lisa_clusters.csv"))
  cat(sprintf("  → Saved: %s/r_lisa_clusters.csv\n", OUT_DIR))
}

# ── 6. Moran's I on BYM2 residuals (model adequacy) ─────────────────────────
cat("\n── Residual spatial autocorrelation (BYM2 fitted values) ────────────\n")
if (length(posterior_rows) > 0) {
  for (v in names(posterior_rows)) {
    post_sub <- posterior_rows[[v]]
    if ("posterior_mean" %in% names(post_sub) && v %in% names(df)) {
      resid <- df[[v]] - post_sub$posterior_mean
      if (sum(!is.na(resid)) > 10) {
        mi_r <- moran.test(resid, W_mat, randomisation = TRUE,
                           na.action = na.exclude, zero.policy = TRUE)
        cat(sprintf("  %-30s  residual I = %6.4f   p = %.4f\n",
                    v, mi_r$estimate[1], mi_r$p.value))
      }
    }
  }
}

cat("\n── analysis.R complete ───────────────────────────────────────────────\n")
cat("Outputs written to data/processed/\n")
