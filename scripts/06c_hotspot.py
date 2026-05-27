#!/usr/bin/env python3
"""06c - SMOTE-balanced XGBoost hotspot classifier, spatial LOROCV."""
import numpy as np, pandas as pd, xgboost as xgb
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss
OUT="data/processed"; RNG=np.random.default_rng(42)
OUTS=["stunting","anaemia","iycf","diarrhoea"]
FEATURES=["poverty_incidence","poverty_intensity","illiteracy_rate",
          "nhis_uninsured_rate","employment_rate","under15_share",
          "urbanicity","improved_water_pct","improved_sanitation_pct","log_pop"]
def smote(X,y,k=5,seed=42):
    rng=np.random.default_rng(seed); Xmin=X[y==1]
    need=(y==0).sum()-(y==1).sum()
    if need<=0 or len(Xmin)<2: return X,y
    kk=min(k,len(Xmin)-1); syn=[]
    for _ in range(need):
        i=rng.integers(len(Xmin))
        d=np.sqrt(((Xmin-Xmin[i])**2).sum(1))
        nn=np.argsort(d)[1:kk+1]; j=nn[rng.integers(kk)]
        syn.append(Xmin[i]+rng.random()*(Xmin[j]-Xmin[i]))
    return np.vstack([X,np.array(syn)]),np.concatenate([y,np.ones(need,int)])
df=pd.read_csv(OUT+"/sae_posteriors.csv")
master=pd.read_csv(OUT+"/master_261district_nutrition.csv")
df=df.merge(master[["district_id"]+FEATURES],on="district_id")
X=df[FEATURES].to_numpy(float); regions=df["region"].to_numpy()
uregions=sorted(set(regions)); hc=[]
for o in OUTS:
    ybin=(df[o+"_exceed"].to_numpy()>0.95).astype(int)
    if ybin.sum()<5 or ybin.sum()>len(ybin)-5:
        print(f"{o}: prevalence {ybin.mean():.2f} skipped"); continue
    proba=np.zeros(len(ybin))
    for rg in uregions:
        te=regions==rg; tr=~te
        Xtr,ytr=smote(X[tr],ybin[tr])
        clf=xgb.XGBClassifier(n_estimators=250,max_depth=3,learning_rate=0.05,
                              random_state=42,eval_metric="logloss")
        clf.fit(Xtr,ytr); proba[te]=clf.predict_proba(X[te])[:,1]
    hc.append({"outcome":o,"hotspot_prevalence":round(ybin.mean(),3),
               "n_hotspots":int(ybin.sum()),
               "AUC_PR":round(average_precision_score(ybin,proba),3),
               "AUC_ROC":round(roc_auc_score(ybin,proba),3),
               "Brier":round(brier_score_loss(ybin,proba),3)})
    print(f"{o:10s} n_hot={ybin.sum():3d} AUC-PR={hc[-1]['AUC_PR']:.3f} "
          f"AUC-ROC={hc[-1]['AUC_ROC']:.3f} Brier={hc[-1]['Brier']:.3f}")
pd.DataFrame(hc).to_csv(OUT+"/hotspot_classifier.csv",index=False)
print("06c done")
