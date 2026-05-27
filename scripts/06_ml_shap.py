#!/usr/bin/env python3
"""
06_ml_shap.py - Random Forest + XGBoost determinant models for the 4
district child-health outcomes, with SHAP interpretability, spatial
leave-one-region-out CV (16 folds), and a SMOTE-balanced hotspot classifier.
SHAP = XGBoost native exact TreeSHAP (pred_contribs).
Outputs: data/processed/ml_performance.csv , shap_importance.csv ,
         shap_values_<outcome>.csv , hotspot_classifier.csv
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss
import xgboost as xgb

OUT = "data/processed"
RNG = np.random.default_rng(42)
OUTS = ["stunting", "anaemia", "iycf", "diarrhoea"]
FEATURES = ["poverty_incidence", "poverty_intensity", "illiteracy_rate",
            "nhis_uninsured_rate", "employment_rate", "under15_share",
            "urbanicity", "improved_water_pct", "improved_sanitation_pct",
            "log_pop"]
NICE = {"poverty_incidence": "Poverty incidence",
        "poverty_intensity": "Poverty intensity",
        "illiteracy_rate": "Illiteracy rate",
        "nhis_uninsured_rate": "NHIS-uninsured share",
        "employment_rate": "Employment rate",
        "under15_share": "Under-15 population share",
        "urbanicity": "Urbanicity", "improved_water_pct": "Improved water",
        "improved_sanitation_pct": "Improved sanitation",
        "log_pop": "Log population"}


def smote(X, y, k=5, seed=42):
    rng = np.random.default_rng(seed)
    Xmin = X[y == 1]
    n_min, n_maj = (y == 1).sum(), (y == 0).sum()
    need = n_maj - n_min
    if need <= 0 or len(Xmin) < 2:
        return X, y
    kk = min(k, len(Xmin) - 1)
    syn = []
    for _ in range(need):
        i = rng.integers(len(Xmin))
        d = np.sqrt(((Xmin - Xmin[i]) ** 2).sum(1))
        nn = np.argsort(d)[1:kk + 1]
        j = nn[rng.integers(kk)]
        gap = rng.random()
        syn.append(Xmin[i] + gap * (Xmin[j] - Xmin[i]))
    Xs = np.vstack([X, np.array(syn)])
    ys = np.concatenate([y, np.ones(need, dtype=int)])
    return Xs, ys


def main():
    df = pd.read_csv(OUT + "/sae_posteriors.csv")
    master = pd.read_csv(OUT + "/master_261district_nutrition.csv")
    df = df.merge(master[["district_id"] + FEATURES], on="district_id")
    X = df[FEATURES].to_numpy(float)
    regions = df["region"].to_numpy()
    uregions = sorted(set(regions))

    perf, shap_imp = [], []
    for o in OUTS:
        y = df[o + "_mean"].to_numpy(float)

        # ---- spatial leave-one-region-out CV (16 folds) -------------------
        for label, mk in [("RandomForest", "rf"), ("XGBoost", "xgb")]:
            preds = np.zeros(len(y))
            fold_r2 = []
            for rg in uregions:
                te = regions == rg
                tr = ~te
                if mk == "rf":
                    m = RandomForestRegressor(n_estimators=400, max_depth=8,
                                              random_state=42, n_jobs=-1)
                else:
                    m = xgb.XGBRegressor(n_estimators=400, max_depth=3,
                                         learning_rate=0.05, subsample=0.8,
                                         colsample_bytree=0.8, random_state=42)
                m.fit(X[tr], y[tr])
                preds[te] = m.predict(X[te])
                if te.sum() > 2:
                    fold_r2.append(r2_score(y[te], preds[te]))
            cv_r2 = r2_score(y, preds)
            cv_rmse = np.sqrt(mean_squared_error(y, preds))
            perf.append({"outcome": o, "model": label,
                         "spatial_LOROCV_R2": round(cv_r2, 3),
                         "spatial_LOROCV_RMSE": round(cv_rmse, 3),
                         "fold_R2_mean": round(np.mean(fold_r2), 3),
                         "fold_R2_sd": round(np.std(fold_r2), 3)})
            print(f"{o:10s} {label:13s} spatial-LOROCV R2={cv_r2:.3f} "
                  f"RMSE={cv_rmse:.2f}  fold R2 {np.mean(fold_r2):.2f}"
                  f"+/-{np.std(fold_r2):.2f}")

        # ---- full-data XGBoost + native exact TreeSHAP --------------------
        m = xgb.XGBRegressor(n_estimators=400, max_depth=3, learning_rate=0.05,
                             subsample=0.8, colsample_bytree=0.8,
                             random_state=42)
        m.fit(X, y)
        contribs = m.get_booster().predict(xgb.DMatrix(X), pred_contribs=True)
        sv = contribs[:, :-1]                       # n x p exact SHAP
        # bootstrap SHAP stability (100x)
        boot = np.zeros((100, len(FEATURES)))
        for b in range(100):
            idx = RNG.integers(0, len(y), len(y))
            mb = xgb.XGBRegressor(n_estimators=300, max_depth=3,
                                  learning_rate=0.05, random_state=b)
            mb.fit(X[idx], y[idx])
            cb = mb.get_booster().predict(xgb.DMatrix(X[idx]),
                                          pred_contribs=True)[:, :-1]
            boot[b] = np.abs(cb).mean(0)
        msh = np.abs(sv).mean(0)
        for j, f in enumerate(FEATURES):
            shap_imp.append({"outcome": o, "feature": f,
                             "feature_label": NICE[f],
                             "mean_abs_shap": round(float(msh[j]), 4),
                             "boot_lo": round(float(np.percentile(boot[:, j], 2.5)), 4),
                             "boot_hi": round(float(np.percentile(boot[:, j], 97.5)), 4),
                             "boot_cv": round(float(boot[:, j].std() /
                                              (boot[:, j].mean() + 1e-9)), 3)})
        # save per-district SHAP values
        svdf = pd.DataFrame(sv, columns=["shap_" + f for f in FEATURES])
        svdf.insert(0, "district", df["district"])
        svdf.insert(0, "district_id", df["district_id"])
        svdf["feature_values_csv"] = ""
        svdf.to_csv(OUT + "/shap_values_" + o + ".csv", index=False)
        top3 = [FEATURES[k] for k in np.argsort(msh)[::-1][:3]]
        print(f"           top-3 SHAP: {[NICE[t] for t in top3]}")

    pd.DataFrame(perf).to_csv(OUT + "/ml_performance.csv", index=False)
    pd.DataFrame(shap_imp).to_csv(OUT + "/shap_importance.csv", index=False)

    # ---- hotspot binary classifier (SMOTE + XGBoost, spatial CV) ----------
    hc = []
    for o in OUTS:
        ybin = (df[o + "_exceed"].to_numpy() > 0.95).astype(int)
        if ybin.sum() < 5 or ybin.sum() > len(ybin) - 5:
            print(f"hotspot {o}: prevalence {ybin.mean():.2f} - skipped")
            continue
        proba = np.zeros(len(ybin))
        for rg in uregions:
            te = regions == rg
            tr = ~te
            Xtr, ytr = smote(X[tr], ybin[tr])
            clf = xgb.XGBClassifier(n_estimators=300, max_depth=3,
                                    learning_rate=0.05, random_state=42,
                                    eval_metric="logloss")
            clf.fit(Xtr, ytr)
            proba[te] = clf.predict_proba(X[te])[:, 1]
        aucpr = average_precision_score(ybin, proba)
        aucroc = roc_auc_score(ybin, proba)
        brier = brier_score_loss(ybin, proba)
        hc.append({"outcome": o, "hotspot_prevalence": round(ybin.mean(), 3),
                   "n_hotspots": int(ybin.sum()),
                   "AUC_PR": round(aucpr, 3), "AUC_ROC": round(aucroc, 3),
                   "Brier": round(brier, 3)})
        print(f"hotspot {o:10s} n={ybin.sum()} AUC-PR={aucpr:.3f} "
              f"AUC-ROC={aucroc:.3f} Brier={brier:.3f}")
    pd.DataFrame(hc).to_csv(OUT + "/hotspot_classifier.csv", index=False)
    print("ML + SHAP complete.")


if __name__ == "__main__":
    main()
