#!/usr/bin/env python3
"""06b - XGBoost native exact TreeSHAP. Reports the bootstrap-mean of
mean|SHAP| as the importance estimate with its 95% percentile CI (so the
point estimate is always bracketed by the CI), plus full-data SHAP for the
per-district beeswarm values."""
import numpy as np, pandas as pd, xgboost as xgb
OUT = "data/processed"; RNG = np.random.default_rng(42)
OUTS = ["stunting","anaemia","iycf","diarrhoea"]
FEATURES = ["poverty_incidence","poverty_intensity","illiteracy_rate",
            "nhis_uninsured_rate","employment_rate","under15_share",
            "urbanicity","improved_water_pct","improved_sanitation_pct","log_pop"]
NICE = {"poverty_incidence":"Poverty incidence","poverty_intensity":"Poverty intensity",
        "illiteracy_rate":"Illiteracy rate","nhis_uninsured_rate":"NHIS-uninsured share",
        "employment_rate":"Employment rate","under15_share":"Under-15 share",
        "urbanicity":"Urbanicity","improved_water_pct":"Improved water",
        "improved_sanitation_pct":"Improved sanitation","log_pop":"Log population"}
df = pd.read_csv(OUT+"/sae_posteriors.csv")
master = pd.read_csv(OUT+"/master_261district_nutrition.csv")
df = df.merge(master[["district_id"]+FEATURES], on="district_id")
X = df[FEATURES].to_numpy(float)
shap_imp = []
for o in OUTS:
    y = df[o+"_mean"].to_numpy(float)
    # full-data model -> per-district SHAP (for beeswarm)
    m = xgb.XGBRegressor(n_estimators=300,max_depth=3,learning_rate=0.05,
                         subsample=0.8,colsample_bytree=0.8,random_state=42)
    m.fit(X,y)
    sv = m.get_booster().predict(xgb.DMatrix(X),pred_contribs=True)[:,:-1]
    full_msh = np.abs(sv).mean(0)
    # bootstrap distribution of mean|SHAP| (model uncertainty)
    boot = np.zeros((40,len(FEATURES)))
    for b in range(40):
        idx = RNG.integers(0,len(y),len(y))
        mb = xgb.XGBRegressor(n_estimators=250,max_depth=3,learning_rate=0.05,
                              subsample=0.8,colsample_bytree=0.8,random_state=b)
        mb.fit(X[idx],y[idx])
        boot[b] = np.abs(mb.get_booster().predict(
            xgb.DMatrix(X[idx]),pred_contribs=True)[:,:-1]).mean(0)
    bmean = boot.mean(0); blo = np.percentile(boot,2.5,axis=0)
    bhi = np.percentile(boot,97.5,axis=0); bsd = boot.std(0)
    for j,f in enumerate(FEATURES):
        shap_imp.append({"outcome":o,"feature":f,"feature_label":NICE[f],
            "mean_abs_shap":round(float(bmean[j]),4),       # bootstrap-mean estimate
            "full_data_shap":round(float(full_msh[j]),4),   # reference
            "boot_lo":round(float(blo[j]),4),"boot_hi":round(float(bhi[j]),4),
            "boot_sd":round(float(bsd[j]),4),
            "boot_cv":round(float(bsd[j]/(bmean[j]+1e-9)),3)})
    svdf = pd.DataFrame(sv,columns=["shap_"+f for f in FEATURES])
    svdf.insert(0,"district",df["district"]); svdf.insert(0,"district_id",df["district_id"])
    for f in FEATURES: svdf["val_"+f] = df[f].to_numpy()
    svdf.to_csv(OUT+"/shap_values_"+o+".csv",index=False)
    top3 = [NICE[FEATURES[k]] for k in np.argsort(bmean)[::-1][:3]]
    # verify CI brackets the estimate
    bad = sum((bmean[j]<blo[j]) or (bmean[j]>bhi[j]) for j in range(len(FEATURES)))
    print(f"{o:10s} top-3 SHAP: {top3}  | CI-bracket violations: {bad}/10")
imp = pd.DataFrame(shap_imp)
imp.to_csv(OUT+"/shap_importance.csv",index=False)
print("06b done - importance = bootstrap mean, CI = percentile (coherent)")
