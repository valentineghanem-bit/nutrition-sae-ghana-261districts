#!/usr/bin/env python3
"""07 - consolidate all analytic outputs into the canonical master CSV
and emit the Canonical Values Register."""
import numpy as np, pandas as pd
OUT="data/processed"
OUTS=["stunting","anaemia","iycf","diarrhoea"]
m=pd.read_csv(OUT+"/master_261district_nutrition.csv")
post=pd.read_csv(OUT+"/sae_posteriors.csv")
lisa=pd.read_csv(OUT+"/lisa_clusters.csv")
gi=pd.read_csv(OUT+"/getis_ord.csv")
df=m.merge(post.drop(columns=["district","region"]),on="district_id")
for o in OUTS:
    df=df.merge(lisa[["district_id",o+"_lisa_cat"]],on="district_id")
    df=df.merge(gi[["district_id",o+"_class"]].rename(
        columns={o+"_class":o+"_gistar"}),on="district_id")
df.to_csv(OUT+"/master_261district_nutrition_FINAL.csv",index=False)

# canonical values register
reg=[]
mg=pd.read_csv(OUT+"/moran_global.csv")
sae=pd.read_csv(OUT+"/sae_summary.csv")
gwr=pd.read_csv(OUT+"/gwr_summary.csv")
mlp=pd.read_csv(OUT+"/ml_performance.csv")
hot=pd.read_csv(OUT+"/hotspot_classifier.csv")
for o in OUTS:
    pm=df[o+"_mean"]
    reg.append(("district_"+o+"_mean_min",round(pm.min(),2)))
    reg.append(("district_"+o+"_mean_max",round(pm.max(),2)))
    reg.append(("district_"+o+"_mean_median",round(pm.median(),2)))
    reg.append((o+"_moran_I",float(mg[mg.outcome==o].moran_I_queen.iloc[0])))
    reg.append((o+"_moran_p",float(mg[mg.outcome==o].p_queen.iloc[0])))
    reg.append((o+"_phi_spatial",float(sae[sae.outcome==o].phi_spatial.iloc[0])))
    reg.append((o+"_hotspots_P95",int((df[o+"_exceed"]>0.95).sum())))
    reg.append((o+"_lisa_HH",int((df[o+"_lisa_cat"]=="HH").sum())))
    reg.append((o+"_gwr_dAICc",float(gwr[gwr.outcome==o].delta_aicc.iloc[0])))
    reg.append((o+"_xgb_LOROCV_R2",float(
        mlp[(mlp.outcome==o)&(mlp.model=="XGBoost")].spatial_LOROCV_R2.iloc[0])))
    if (hot.outcome==o).any():
        reg.append((o+"_hotspot_AUCPR",float(hot[hot.outcome==o].AUC_PR.iloc[0])))
cv=pd.DataFrame(reg,columns=["value_name","value"])
cv.to_csv(OUT+"/Canonical_Values_Nutrition.csv",index=False)
print("FINAL master CSV:",df.shape)
print("\nCanonical Values Register:")
print(cv.to_string(index=False))
# northern-belt check for stunting hotspots
north=["Northern","Savannah","North East","Upper East","Upper West","Oti"]
hs=df[df["stunting_exceed"]>0.95]
print(f"\nStunting hotspots: {len(hs)} | in northern belt: "
      f"{hs['region'].isin(north).sum()} ({100*hs['region'].isin(north).mean():.0f}%)")
