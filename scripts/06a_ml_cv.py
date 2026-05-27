#!/usr/bin/env python3
"""06a - spatial leave-one-region-out CV (RF + XGBoost), 4 outcomes."""
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error
import xgboost as xgb
OUT = "data/processed"
OUTS = ["stunting", "anaemia", "iycf", "diarrhoea"]
FEATURES = ["poverty_incidence","poverty_intensity","illiteracy_rate",
            "nhis_uninsured_rate","employment_rate","under15_share",
            "urbanicity","improved_water_pct","improved_sanitation_pct","log_pop"]
df = pd.read_csv(OUT+"/sae_posteriors.csv")
master = pd.read_csv(OUT+"/master_261district_nutrition.csv")
df = df.merge(master[["district_id"]+FEATURES], on="district_id")
X = df[FEATURES].to_numpy(float)
regions = df["region"].to_numpy()
uregions = sorted(set(regions))
perf = []
for o in OUTS:
    y = df[o+"_mean"].to_numpy(float)
    for label, mk in [("RandomForest","rf"),("XGBoost","xgb")]:
        preds = np.zeros(len(y)); fold_r2 = []
        for rg in uregions:
            te = regions==rg; tr = ~te
            if mk=="rf":
                m = RandomForestRegressor(n_estimators=200,max_depth=8,
                                          random_state=42,n_jobs=-1)
            else:
                m = xgb.XGBRegressor(n_estimators=300,max_depth=3,
                                     learning_rate=0.05,subsample=0.8,
                                     colsample_bytree=0.8,random_state=42)
            m.fit(X[tr],y[tr]); preds[te] = m.predict(X[te])
            if te.sum()>2: fold_r2.append(r2_score(y[te],preds[te]))
        perf.append({"outcome":o,"model":label,
                     "spatial_LOROCV_R2":round(r2_score(y,preds),3),
                     "spatial_LOROCV_RMSE":round(np.sqrt(mean_squared_error(y,preds)),3),
                     "fold_R2_mean":round(np.mean(fold_r2),3),
                     "fold_R2_sd":round(np.std(fold_r2),3)})
        print(f"{o:10s} {label:13s} LOROCV-R2={perf[-1]['spatial_LOROCV_R2']:.3f} "
              f"RMSE={perf[-1]['spatial_LOROCV_RMSE']:.2f} "
              f"foldR2={perf[-1]['fold_R2_mean']:.2f}+/-{perf[-1]['fold_R2_sd']:.2f}")
pd.DataFrame(perf).to_csv(OUT+"/ml_performance.csv",index=False)
print("06a done")
