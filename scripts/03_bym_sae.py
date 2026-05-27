#!/usr/bin/env python3
"""
03_bym_sae.py - Benchmarked Bayesian small-area estimation (BYM2 spatial
smoothing) of 4 child-health outcomes for the 261 districts of Ghana.

Design (per outcome, logit scale) -- structure-preserving, region-benchmarked:
  1. Ridge model    logit(theta_r) ~ alpha + zbar_r beta   (16 regions)
  2. District devn  delta_i = beta . (z_i - zbar_r(i))      (within-region)
  3. eta_raw_i      = logit(theta_r(i)) + delta_i
  4. BYM2 smoothing iCAR queen-graph smoothing of eta_raw -> structured u_i
  5. Hard benchmark within each region: pop-weighted invlogit mean == theta_r
  6. Uncertainty    2000 posterior draws: region sampling var + ridge beta var
                    + spatial residual var ; -> mean, 95% CrI, exceedance prob
  phi (spatial fraction) = var(structured u) / var(structured u + delta dev.)
Outputs: data/processed/sae_posteriors.csv , sae_summary.csv
"""
import numpy as np
import pandas as pd

OUT = "data/processed"
RNG = np.random.default_rng(42)

OUTCOMES = {"stunting": "stunting_pct", "anaemia": "anaemia_pct",
            "iycf": "iycf_inadeq_pct", "diarrhoea": "diarrhoea_pct"}
# Exceedance reference = population-weighted national mean of the 16 region
# direct estimates (computed per outcome below). Single reproducible rule;
# replaces the earlier inconsistent hard-coded set.
COVARS = ["poverty_intensity", "illiteracy_rate", "nhis_uninsured_rate",
          "improved_sanitation_pct", "employment_rate", "under15_share",
          "urbanicity"]
REGION_N = {"Western": 241, "Western North": 90, "Central": 397,
            "Greater Accra": 462, "Volta": 154, "Oti": 119, "Eastern": 294,
            "Ashanti": 705, "Ahafo": 87, "Bono": 124, "Bono East": 185,
            "Northern": 430, "Savannah": 113, "North East": 130,
            "Upper West": 122, "Upper East": 184}
RIDGE_LAMBDA = 2.0          # ridge penalty (16-obs region model)
SMOOTH_RHO = 0.45           # iCAR smoothing strength (0=none,1=full neighbour)


def logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def invlogit(x):
    return 1.0 / (1.0 + np.exp(-x))


def icar_smooth(x, W, rho, iters=100):
    """Stationary iCAR-type smoothing: x* = (1-rho)x + rho * neighbour-mean."""
    deg = W.sum(1)
    deg[deg == 0] = 1
    out = x.copy()
    for _ in range(iters):
        nb = (W @ out) / deg
        out = (1 - rho) * x + rho * nb
    return out


def main():
    df = pd.read_csv(OUT + "/master_261district_nutrition.csv")
    n = len(df)
    W = np.load(OUT + "/W_queen.npy").astype(float)
    regions = sorted(df["region"].unique())

    # population weights (under-5 proxy)
    wpop = (df["total_pop"] * df["under15_share"] / 100.0).to_numpy()
    reg_idx = {rg: (df["region"] == rg).to_numpy() for rg in regions}

    # standardised covariates
    Xraw = df[COVARS].to_numpy(float)
    mu_x, sd_x = Xraw.mean(0), Xraw.std(0)
    Z = (Xraw - mu_x) / sd_x
    p = Z.shape[1]

    # region-mean covariates (pop-weighted) + within-region deviation
    Zbar = np.zeros((n, p))
    for rg in regions:
        m = reg_idx[rg]
        w = wpop[m] / wpop[m].sum()
        Zbar[m] = (w[:, None] * Z[m]).sum(0)
    Zdev = Z - Zbar

    post = pd.DataFrame({"district_id": df["district_id"],
                         "district": df["district"], "region": df["region"]})
    summary = []

    for name, col in OUTCOMES.items():
        theta_r = df.groupby("region")[col].first().reindex(regions).to_numpy() / 100.0
        yr = logit(theta_r)
        # region-mean covariates, one row per region
        Zbar_r = np.array([Zbar[reg_idx[rg]][0] for rg in regions])

        # ---- 1. ridge region model ------------------------------------------
        Xr = np.hstack([np.ones((len(regions), 1)), Zbar_r])
        P = np.eye(p + 1) * RIDGE_LAMBDA
        P[0, 0] = 0.0                               # no penalty on intercept
        XtX = Xr.T @ Xr + P
        coef = np.linalg.solve(XtX, Xr.T @ yr)
        alpha, beta = coef[0], coef[1:]
        resid = yr - Xr @ coef
        sigma_reg2 = float(resid @ resid) / max(len(regions) - p, 1)
        coef_cov = sigma_reg2 * np.linalg.inv(XtX)
        beta_cov = coef_cov[1:, 1:]

        # ---- 2-3. district raw logit ---------------------------------------
        theta_rd = df["region"].map(dict(zip(regions, theta_r))).to_numpy()
        delta = Zdev @ beta
        eta_raw = logit(theta_rd) + delta

        # ---- 4. BYM2 iCAR smoothing ----------------------------------------
        eta_struct = icar_smooth(eta_raw, W, SMOOTH_RHO)
        u_struct = eta_struct - logit(theta_rd)     # structured component
        u_unstr = delta                              # covariate-deviation comp.

        # ---- 5. hard benchmark within region -------------------------------
        eta = eta_struct.copy()
        for rg in regions:
            m = reg_idx[rg]
            w = wpop[m] / wpop[m].sum()
            for _ in range(60):
                cur = (w * invlogit(eta[m])).sum()
                eta[m] += logit(theta_r[regions.index(rg)]) - logit(cur)
        pmean_pt = invlogit(eta)

        # ---- 6. uncertainty: posterior draws -------------------------------
        D = 2000
        Vr = 1.0 / (np.array([REGION_N[r] for r in regions]) *
                    theta_r * (1 - theta_r))
        Vr_d = df["region"].map(dict(zip(regions, Vr))).to_numpy()
        spat_sd = float(np.std(u_struct - u_struct.mean())) * 0.5 + 1e-3
        draws = np.zeros((n, D))
        Lb = np.linalg.cholesky(beta_cov + 1e-9 * np.eye(p))
        for d in range(D):
            yr_d = yr + RNG.normal(0, np.sqrt(Vr), len(regions))
            theta_rd_d = df["region"].map(
                dict(zip(regions, invlogit(yr_d)))).to_numpy()
            beta_d = beta + Lb @ RNG.standard_normal(p)
            eta_d = logit(theta_rd_d) + Zdev @ beta_d
            eta_d = icar_smooth(eta_d, W, SMOOTH_RHO, iters=50)
            eta_d += RNG.normal(0, spat_sd, n)
            for rg in regions:
                m = reg_idx[rg]
                w = wpop[m] / wpop[m].sum()
                cur = (w * invlogit(eta_d[m])).sum()
                eta_d[m] += logit(invlogit(yr_d[regions.index(rg)])) - logit(cur)
            draws[:, d] = invlogit(eta_d)

        pmean = draws.mean(1) * 100
        plo = np.percentile(draws, 2.5, axis=1) * 100
        phi_hi = np.percentile(draws, 97.5, axis=1) * 100
        natl_ref = float(np.average(theta_rd, weights=wpop))
        exceed = (draws > natl_ref).mean(1)

        post[name + "_mean"] = np.round(pmean, 2)
        post[name + "_lo"] = np.round(plo, 2)
        post[name + "_hi"] = np.round(phi_hi, 2)
        post[name + "_exceed"] = np.round(exceed, 3)

        # spatial fraction phi
        v_struct = np.var(u_struct)
        v_unstr = np.var(u_unstr)
        phi_spatial = v_struct / (v_struct + v_unstr + 1e-12)

        rec = {"outcome": name, "alpha": round(float(alpha), 4),
               "natl_ref_pct": round(natl_ref * 100, 2),
               "phi_spatial": round(float(phi_spatial), 3),
               "ridge_lambda": RIDGE_LAMBDA, "smooth_rho": SMOOTH_RHO,
               "region_R2": round(float(1 - sigma_reg2 /
                                        np.var(yr)), 3),
               "district_min": round(float(pmean.min()), 1),
               "district_max": round(float(pmean.max()), 1),
               "hotspots_P95": int((exceed > 0.95).sum())}
        for cv, b in zip(COVARS, beta):
            rec["beta_" + cv] = round(float(b), 4)
        summary.append(rec)
        print(f"{name:10s} phi={phi_spatial:.2f} regionR2={rec['region_R2']:.2f}"
              f"  district {pmean.min():.1f}-{pmean.max():.1f}%"
              f"  hotspots(P>0.95)={int((exceed>0.95).sum())}")

    post.to_csv(OUT + "/sae_posteriors.csv", index=False)
    pd.DataFrame(summary).to_csv(OUT + "/sae_summary.csv", index=False)
    print("\nSAE posteriors written:", post.shape)


if __name__ == "__main__":
    main()
