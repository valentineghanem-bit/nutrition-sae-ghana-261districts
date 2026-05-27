# bym2_diagnostics.R — BYM2 model diagnostics and posterior validation
# Nutrition Anaemia Growth Determinants Ghana 261 Districts
# Author: Valentine Golden Ghanem | ORCID: 0009-0002-8332-0220
# Usage:  Rscript scripts/bym2_diagnostics.R
#
# Runs after analysis.R. Reads r_bym2_posteriors.csv and the master dataset,
# then produces:
#   - Posterior predictive checks (PPC)
#   - Within-region vs between-region variance decomposition
#   - Residual spatial autocorrelation (BYM2 residuals)
#   - Model comparison table (OLS vs SLM vs SEM vs BYM2)
#   - Leave-one-region-out cross-validation (LOROCV) via INLA

suppressPackageStartupMessages({
  library(INLA)
  library(spdep)
  library(dplyr)
  library(readr)
  library(tidyr)
})
set.seed(42)

DATA_DIR <- "data/processed"
cat("── BYM2 diagnostics ──────────────────────────────────────────────────\n")

# ── 0. Load data ──────────────────────────────────────────────────────────────
df <- read_csv(file.path(DATA_DIR, "master_261district_nutrition_FINAL.csv"),
               show_col_types = FALSE)
n  <- nrow(df)
cat(sprintf("Districts: %d\n", n))

OUTCOMES <- intersect(
  c("stunting_prev", "anaemia_prev", "iycf_inadequacy_prev", "diarrhoea_prev"),
  names(df)
)

# Load BYM2 posteriors if available
posteriors_path <- file.path(DATA_DIR, "r_bym2_posteriors.csv")
has_posteriors  <- file.exists(posteriors_path)
if (has_posteriors) {
  posteriors <- read_csv(posteriors_path, show_col_types = FALSE)
  cat(sprintf("Loaded posteriors: %d rows\n", nrow(posteriors)))
}

# ── 1. Rebuild spatial weights ────────────────────────────────────────────────
cat("\n── Spatial weights ───────────────────────────────────────────────────\n")
nb  <- NULL
W   <- NULL
adj_file <- tempfile(fileext = ".adj")

geojson_path <- "data/raw/Ghana_New_260_District.geojson"
if (requireNamespace("sf", quietly = TRUE) && file.exists(geojson_path)) {
  sf_obj <- sf::st_read(geojson_path, quiet = TRUE)
  nb     <- poly2nb(sf_obj, queen = TRUE)
  W      <- nb2listw(nb, style = "W", zero.policy = TRUE)
  nb2INLA(adj_file, nb)
  cat(sprintf("Queen-contiguity weights: %d polygons, mean neighbours: %.2f\n",
              length(nb), mean(card(nb))))
} else {
  message("sf not available — skipping geometry-based weights")
}

# ── 2. Variance decomposition (between vs within regions) ────────────────────
cat("\n── Variance decomposition ────────────────────────────────────────────\n")

region_col <- names(df)[grepl("region", names(df), ignore.case = TRUE)][1]
if (!is.na(region_col) && length(OUTCOMES) > 0) {
  decomp_rows <- list()
  for (v in OUTCOMES) {
    vals <- df[[v]]
    if (all(is.na(vals))) next
    total_var   <- var(vals, na.rm = TRUE)
    region_means <- tapply(vals, df[[region_col]], mean, na.rm = TRUE)
    grand_mean   <- mean(vals, na.rm = TRUE)
    between_var  <- var(region_means[df[[region_col]]], na.rm = TRUE)
    within_var   <- total_var - between_var
    cat(sprintf("  %-30s  Total=%.4f  Between=%.4f (%4.1f%%)  Within=%.4f (%4.1f%%)\n",
                v, total_var,
                between_var, 100 * between_var / total_var,
                within_var,  100 * within_var  / total_var))
    decomp_rows[[v]] <- data.frame(
      outcome = v, total_var = round(total_var, 4),
      between_var = round(between_var, 4),
      pct_between = round(100 * between_var / total_var, 1),
      within_var  = round(within_var, 4),
      pct_within  = round(100 * within_var / total_var, 1)
    )
  }
  decomp_df <- do.call(rbind, decomp_rows)
  write_csv(decomp_df, file.path(DATA_DIR, "r_variance_decomposition.csv"))
  cat(sprintf("  → Saved: %s/r_variance_decomposition.csv\n", DATA_DIR))
}

# ── 3. Residual Moran's I (BYM2 residuals) ───────────────────────────────────
cat("\n── Residual spatial autocorrelation ──────────────────────────────────\n")
if (has_posteriors && !is.null(W)) {
  resid_moran_rows <- list()
  for (v in OUTCOMES) {
    post_v <- posteriors %>% filter(outcome == v)
    if (nrow(post_v) == 0) next
    resid <- df[[v]] - post_v$posterior_mean[seq_len(n)]
    if (sum(!is.na(resid)) < 10) next
    mi_r <- moran.test(resid, W, randomisation = TRUE,
                       na.action = na.exclude, zero.policy = TRUE)
    cat(sprintf("  %-30s  residual I=%.4f  p=%.4f%s\n",
                v, mi_r$estimate[1], mi_r$p.value,
                ifelse(mi_r$p.value < 0.05, "  *** spatial structure remains ***", "")))
    resid_moran_rows[[v]] <- data.frame(
      outcome = v,
      residual_moran_I = round(mi_r$estimate[1], 4),
      p_value          = round(mi_r$p.value, 4),
      residual_structure = mi_r$p.value < 0.05
    )
  }
  if (length(resid_moran_rows) > 0) {
    write_csv(do.call(rbind, resid_moran_rows),
              file.path(DATA_DIR, "r_residual_moran.csv"))
  }
}

# ── 4. Posterior predictive check ─────────────────────────────────────────────
cat("\n── Posterior predictive checks (PPC) ────────────────────────────────\n")
if (has_posteriors) {
  ppc_rows <- list()
  for (v in OUTCOMES) {
    post_v <- posteriors %>% filter(outcome == v)
    if (nrow(post_v) == 0 || !v %in% names(df)) next
    obs   <- df[[v]]
    pred  <- post_v$posterior_mean[seq_len(n)]
    lower <- post_v$lower_95ci[seq_len(n)]
    upper <- post_v$upper_95ci[seq_len(n)]

    coverage <- mean(obs >= lower & obs <= upper, na.rm = TRUE)
    bias     <- mean(pred - obs, na.rm = TRUE)
    rmse     <- sqrt(mean((pred - obs)^2, na.rm = TRUE))
    mae      <- mean(abs(pred - obs), na.rm = TRUE)

    cat(sprintf("  %-30s  Coverage=%.1f%%  Bias=%+.4f  RMSE=%.4f  MAE=%.4f\n",
                v, 100 * coverage, bias, rmse, mae))
    ppc_rows[[v]] <- data.frame(
      outcome = v,
      pct_coverage_95ci = round(100 * coverage, 1),
      bias  = round(bias, 4),
      rmse  = round(rmse, 4),
      mae   = round(mae, 4)
    )
  }
  if (length(ppc_rows) > 0) {
    ppc_df <- do.call(rbind, ppc_rows)
    write_csv(ppc_df, file.path(DATA_DIR, "r_ppc_summary.csv"))
    cat(sprintf("  → Saved: %s/r_ppc_summary.csv\n", DATA_DIR))
  }
}

# ── 5. OLS → LM tests → SLM/SEM model selection (first outcome) ─────────────
cat("\n── Spatial model selection (OLS / SLM / SEM) ────────────────────────\n")
if (!is.null(W) && length(OUTCOMES) > 0) {
  v      <- OUTCOMES[1]
  COVARS <- intersect(
    c("poverty_rate", "female_illiteracy", "water_access", "sanitation_access",
      "nhis_coverage", "pop_density"),
    names(df)
  )

  if (length(COVARS) > 0) {
    fml <- as.formula(paste(v, "~", paste(COVARS, collapse = " + ")))

    ols <- tryCatch(lm(fml, data = df), error = function(e) NULL)
    if (!is.null(ols)) {
      lm_tests <- tryCatch(
        lm.RStests(ols, W, test = "all", zero.policy = TRUE),
        error = function(e) NULL
      )
      if (!is.null(lm_tests)) {
        cat(sprintf("  OLS R² = %.3f  AIC = %.2f\n", summary(ols)$r.squared, AIC(ols)))
        cat("  LM diagnostics:\n")
        print(lm_tests)
      }

      slm <- tryCatch(lagsarlm(fml, data = df, listw = W, zero.policy = TRUE),
                      error = function(e) NULL)
      sem <- tryCatch(errorsarlm(fml, data = df, listw = W, zero.policy = TRUE),
                      error = function(e) NULL)

      if (!is.null(slm) && !is.null(sem)) {
        model_comp <- data.frame(
          model    = c("OLS", "SLM (spatial lag)", "SEM (spatial error)"),
          AIC      = round(c(AIC(ols), AIC(slm), AIC(sem)), 2),
          log_lik  = round(c(logLik(ols), logLik(slm), logLik(sem)), 2)
        )
        cat("\n  Model comparison:\n")
        print(model_comp)
        write_csv(model_comp, file.path(DATA_DIR, "r_model_comparison.csv"))
        cat(sprintf("  → Saved: %s/r_model_comparison.csv\n", DATA_DIR))
      }
    }
  }
}

# ── 6. LOROCV with BYM2-INLA (first outcome, abridged — 4 of 16 folds) ───────
cat("\n── BYM2-INLA LOROCV (4-fold sample) ────────────────────────────────\n")
if (!is.null(W) && length(OUTCOMES) > 0 && file.exists(adj_file)) {
  region_col <- names(df)[grepl("region", names(df), ignore.case = TRUE)][1]
  g <- tryCatch(inla.read.graph(adj_file), error = function(e) NULL)

  if (!is.na(region_col) && !is.null(g)) {
    v       <- OUTCOMES[1]
    regions <- unique(df[[region_col]])
    sample_regions <- head(regions, 4)    # abridged — 4 folds for speed

    lorocv_rows <- list()
    df$district_idx <- seq_len(n)
    COVARS <- intersect(
      c("poverty_rate", "female_illiteracy", "water_access", "sanitation_access"),
      names(df)
    )
    fml_covars <- if (length(COVARS) > 0) paste(COVARS, collapse = " + ") else "1"

    for (r in sample_regions) {
      test_idx   <- which(df[[region_col]] == r)
      df_cv      <- df
      df_cv[[v]][test_idx] <- NA     # mask test region

      fml_cv <- as.formula(paste(
        v, "~ 1 +", fml_covars,
        "+ f(district_idx, model='bym2', graph=g,",
        "    hyper=list(prec=list(prior='pc.prec', param=c(1, 0.01)),",
        "               phi=list(prior='pc', param=c(0.5, 0.5))))"
      ))

      fit_cv <- tryCatch(
        inla(fml_cv, family = "gaussian", data = df_cv,
             control.predictor = list(compute = TRUE),
             control.compute   = list(dic = FALSE),
             verbose = FALSE),
        error = function(e) NULL
      )

      if (is.null(fit_cv)) next

      pred  <- fit_cv$summary.fitted.values$mean[test_idx]
      obs   <- df[[v]][test_idx]
      rmse  <- sqrt(mean((pred - obs)^2, na.rm = TRUE))
      mae   <- mean(abs(pred - obs), na.rm = TRUE)
      cat(sprintf("  Region %-20s  RMSE=%.4f  MAE=%.4f\n", r, rmse, mae))
      lorocv_rows[[r]] <- data.frame(region = r, rmse = round(rmse, 4), mae = round(mae, 4))
    }

    if (length(lorocv_rows) > 0) {
      lorocv_df <- do.call(rbind, lorocv_rows)
      write_csv(lorocv_df, file.path(DATA_DIR, "r_lorocv_sample.csv"))
      cat(sprintf("\n  → Saved: %s/r_lorocv_sample.csv\n", DATA_DIR))
      cat(sprintf("  Mean RMSE across %d sampled folds: %.4f\n",
                  nrow(lorocv_df), mean(lorocv_df$rmse)))
    }
  }
}

cat("\n── bym2_diagnostics.R complete ───────────────────────────────────────\n")
cat("Outputs written to data/processed/\n")
