#!/usr/bin/env python3
"""
05_gwr.py - Geographically weighted regression of district child-health
outcomes (SAE posteriors, logit scale) on key determinants.
Adaptive bi-square kernel; AICc-optimal bandwidth; GWR vs OLS comparison;
Monte-Carlo test of coefficient spatial variability.
Outputs: data/processed/gwr_local_coefficients.csv , gwr_summary.csv
"""
import numpy as np
import pandas as pd

OUT = "data/processed"
RNG = np.random.default_rng(42)
OUTS = ["stunting", "anaemia", "iycf", "diarrhoea"]
DETS = ["poverty_intensity", "illiteracy_rate", "nhis_uninsured_rate"]


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p = np.pi / 180.0
    a = (np.sin((lat2 - lat1) * p / 2) ** 2 +
         np.cos(lat1 * p) * np.cos(lat2 * p) *
         np.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * R * np.arcsin(np.sqrt(a))


def logit(p):
    p = np.clip(p / 100.0, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def gwr_fit(X, y, Dmat, bw):
    """Adaptive bi-square GWR; bw = neighbour count. Returns beta(n,p), yhat,
    trace(S)."""
    n, p = X.shape
    beta = np.zeros((n, p))
    yhat = np.zeros(n)
    trS = 0.0
    for i in range(n):
        d = Dmat[i]
        dk = np.partition(d, bw)[bw]
        w = np.where(d < dk, (1 - (d / dk) ** 2) ** 2, 0.0)
        w[i] = max(w[i], 1e-6)
        Xw = X * w[:, None]
        XtX = Xw.T @ X
        try:
            XtXi = np.linalg.inv(XtX + 1e-8 * np.eye(p))
        except np.linalg.LinAlgError:
            XtXi = np.linalg.pinv(XtX)
        b = XtXi @ (Xw.T @ y)
        beta[i] = b
        yhat[i] = X[i] @ b
        si = X[i] @ XtXi @ Xw.T
        trS += si[i]
    return beta, yhat, trS


def aicc(y, yhat, trS, n):
    rss = np.sum((y - yhat) ** 2)
    sigma2 = rss / n
    return n * np.log(sigma2) + n * np.log(2 * np.pi) + \
        n * (n + trS) / (n - 2 - trS)


def main():
    df = pd.read_csv(OUT + "/sae_posteriors.csv")
    master = pd.read_csv(OUT + "/master_261district_nutrition.csv")
    df = df.merge(master[["district_id", "lat", "lon"] + DETS],
                  on="district_id")
    n = len(df)
    lat = df["lat"].to_numpy(float)
    lon = df["lon"].to_numpy(float)
    Dmat = np.array([haversine(lat[i], lon[i], lat, lon) for i in range(n)])

    Xd = df[DETS].to_numpy(float)
    Xd = (Xd - Xd.mean(0)) / Xd.std(0)
    X = np.hstack([np.ones((n, 1)), Xd])
    p = X.shape[1]

    coef = pd.DataFrame({"district_id": df["district_id"],
                         "district": df["district"], "region": df["region"]})
    summ = []
    for o in OUTS:
        y = logit(df[o + "_mean"].to_numpy())
        # OLS
        b_ols = np.linalg.lstsq(X, y, rcond=None)[0]
        yh_ols = X @ b_ols
        aicc_ols = aicc(y, yh_ols, p, n)
        # GWR adaptive bandwidth search
        best = None
        for bw in range(20, 121, 10):
            beta, yh, trS = gwr_fit(X, y, Dmat, bw)
            ac = aicc(y, yh, trS, n)
            if best is None or ac < best[0]:
                best = (ac, bw, beta, yh, trS)
        aicc_gwr, bw, beta, yh, trS = best
        rss = np.sum((y - yh) ** 2)
        r2 = 1 - rss / np.sum((y - y.mean()) ** 2)
        # Brunsdon Monte-Carlo non-stationarity test: scramble geography,
        # keep each (X_i, y_i) pair intact -> tests if the REAL spatial
        # arrangement yields more coefficient variation than random geography
        obs_var = beta[:, 1:].var(0)
        mc = np.zeros((99, p - 1))
        for k in range(99):
            pi = RNG.permutation(n)
            bp, _, _ = gwr_fit(X[pi], y[pi], Dmat, bw)
            mc[k] = bp[:, 1:].var(0)
        mc_p = (np.sum(mc >= obs_var, axis=0) + 1) / 100.0

        for j, dname in enumerate(DETS):
            coef[o + "_b_" + dname] = np.round(beta[:, j + 1], 4)
        rec = {"outcome": o, "bandwidth_adaptive": bw,
               "aicc_ols": round(aicc_ols, 2), "aicc_gwr": round(aicc_gwr, 2),
               "delta_aicc": round(aicc_ols - aicc_gwr, 2),
               "gwr_R2": round(r2, 3),
               "nonstationary": bool((aicc_ols - aicc_gwr) >= 4)}
        for j, dname in enumerate(DETS):
            rec["mc_p_" + dname] = round(float(mc_p[j]), 3)
            rec["b_range_" + dname] = round(
                float(beta[:, j + 1].max() - beta[:, j + 1].min()), 3)
        summ.append(rec)
        print(f"{o:10s} bw={bw} dAICc={aicc_ols-aicc_gwr:.1f} "
              f"R2={r2:.2f} nonstat={rec['nonstationary']} "
              f"MC-p={[rec['mc_p_'+d] for d in DETS]}")

    coef.to_csv(OUT + "/gwr_local_coefficients.csv", index=False)
    pd.DataFrame(summ).to_csv(OUT + "/gwr_summary.csv", index=False)
    print("GWR complete.")


if __name__ == "__main__":
    main()
