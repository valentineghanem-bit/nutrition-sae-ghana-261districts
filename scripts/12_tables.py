#!/usr/bin/env python3
"""12_tables.py - five Q1 results tables (CSV + markdown)."""
import numpy as np
import pandas as pd

OUT, TAB = "data/processed", "tables"
import os
os.makedirs(TAB, exist_ok=True)
OUTS = [("stunting", "Stunting"), ("anaemia", "Anaemia"),
        ("iycf", "IYCF inadequacy"), ("diarrhoea", "Diarrhoea")]

m = pd.read_csv(OUT + "/master_261district_nutrition.csv")
mg = pd.read_csv(OUT + "/moran_global.csv")
sae = pd.read_csv(OUT + "/sae_summary.csv")
gwr = pd.read_csv(OUT + "/gwr_summary.csv")
mlp = pd.read_csv(OUT + "/ml_performance.csv")
hot = pd.read_csv(OUT + "/hotspot_classifier.csv")
shimp = pd.read_csv(OUT + "/shap_importance.csv")
biv = pd.read_csv(OUT + "/bivariate_lisa_global.csv")
md = ["# Results Tables - Nutrition/Anaemia/Child-Health Determinants, "
      "Ghana 261 Districts\n"]

# ---- Table 1: district characteristics --------------------------------------
def msd(x):
    return f"{x.mean():.1f} ({x.std():.1f})"
def medi(x):
    return f"{x.median():.1f} [{x.quantile(.25):.1f}-{x.quantile(.75):.1f}]"
covs = [("Poverty incidence (%)", "poverty_incidence"),
        ("Poverty intensity (%)", "poverty_intensity"),
        ("Illiteracy rate (%)", "illiteracy_rate"),
        ("NHIS-uninsured share (%)", "nhis_uninsured_rate"),
        ("Employment rate (%)", "employment_rate"),
        ("Under-15 population share (%)", "under15_share"),
        ("Improved water (%, region)", "improved_water_pct"),
        ("Improved sanitation (%, region)", "improved_sanitation_pct")]
t1 = []
for lab, c in covs:
    t1.append({"Characteristic": lab, "Mean (SD)": msd(m[c]),
               "Median [IQR]": medi(m[c]),
               "Range": f"{m[c].min():.1f}-{m[c].max():.1f}"})
for key, lab in OUTS:
    c = key + "_district_pct"
    t1.append({"Characteristic": lab + " - district posterior (%)",
               "Mean (SD)": msd(m[c]), "Median [IQR]": medi(m[c]),
               "Range": f"{m[c].min():.1f}-{m[c].max():.1f}"})
t1 = pd.DataFrame(t1)
t1.to_csv(TAB + "/Table1_district_characteristics.csv", index=False)
md.append("## Table 1. Characteristics of the 261 districts of Ghana, 2022\n")
md.append(t1.to_markdown(index=False) + "\n")

# ---- Table 2: spatial autocorrelation ---------------------------------------
t2 = []
for key, lab in OUTS:
    g = mg[mg.outcome == key].iloc[0]
    hh = int((m[key + "_lisa_cluster"] == "HH").sum())
    ll = int((m[key + "_lisa_cluster"] == "LL").sum())
    gh = int((m[key + "_gistar_class"] == "hotspot").sum())
    gc = int((m[key + "_gistar_class"] == "coldspot").sum())
    t2.append({"Outcome": lab,
               "Moran's I (queen)": f"{g.moran_I_queen:.3f}",
               "z": f"{g.z_queen:.1f}", "p": f"{g.p_queen:.3f}",
               "Moran's I (KNN5)": f"{g.moran_I_knn5:.3f}",
               "LISA HH / LL": f"{hh} / {ll}",
               "Gi* hot / cold": f"{gh} / {gc}"})
t2 = pd.DataFrame(t2)
t2.to_csv(TAB + "/Table2_spatial_autocorrelation.csv", index=False)
md.append("\n## Table 2. Global and local spatial autocorrelation "
          "(BYM2 posterior surfaces)\n")
md.append(t2.to_markdown(index=False) + "\n")

# ---- Table 3: SHAP determinant ranking --------------------------------------
t3 = []
for key, lab in OUTS:
    s = (shimp[shimp.outcome == key]
         .sort_values("mean_abs_shap", ascending=False).head(5))
    for rank, (_, r) in enumerate(s.iterrows(), 1):
        t3.append({"Outcome": lab, "Rank": rank,
                   "Determinant": r.feature_label,
                   "Mean |SHAP|": f"{r.mean_abs_shap:.3f}",
                   "95% bootstrap CI": f"{r.boot_lo:.3f}-{r.boot_hi:.3f}", "Stability SD": f"{r.boot_sd:.3f}",
                   "Stability (CV)": f"{r.boot_cv:.2f}"})
t3 = pd.DataFrame(t3)
t3.to_csv(TAB + "/Table3_shap_determinants.csv", index=False)
md.append("\n## Table 3. SHAP determinant importance - top 5 per outcome "
          "(XGBoost exact TreeSHAP, 40x bootstrap)\n")
md.append(t3.to_markdown(index=False) + "\n")

# ---- Table 4: SAE / GWR / ML summary ----------------------------------------
t4 = []
for key, lab in OUTS:
    s = sae[sae.outcome == key].iloc[0]
    g = gwr[gwr.outcome == key].iloc[0]
    x = mlp[(mlp.outcome == key) & (mlp.model == "XGBoost")].iloc[0]
    rf = mlp[(mlp.outcome == key) & (mlp.model == "RandomForest")].iloc[0]
    h = hot[hot.outcome == key]
    aucpr = f"{h.AUC_PR.iloc[0]:.3f}" if len(h) else "-"
    t4.append({"Outcome": lab,
               "phi (spatial fraction)": f"{s.phi_spatial:.2f}",
               "Hotspots P>0.95": int(s.hotspots_P95),
               "GWR dAICc": f"{g.delta_aicc:.0f}",
               "GWR non-stationary": "Yes" if g.nonstationary else "No",
               "XGB LOROCV R2": f"{x.spatial_LOROCV_R2:.2f}",
               "RF LOROCV R2": f"{rf.spatial_LOROCV_R2:.2f}",
               "Hotspot AUC-PR": aucpr})
t4 = pd.DataFrame(t4)
t4.to_csv(TAB + "/Table4_model_summary.csv", index=False)
md.append("\n## Table 4. Small-area, GWR and machine-learning model summary\n")
md.append(t4.to_markdown(index=False) + "\n")

# ---- Table 5: quadruple-burden hotspot districts ----------------------------
m["n_hot"] = sum((m[k + "_exceedance_prob"] > 0.95).astype(int)
                 for k, _ in OUTS)
q = m[m["n_hot"] == 4][["district", "region", "stunting_district_pct",
                        "anaemia_district_pct", "iycf_district_pct",
                        "diarrhoea_district_pct"]].copy()
q = q.sort_values(["region", "district"]).rename(columns={
    "district": "District", "region": "Region",
    "stunting_district_pct": "Stunting %", "anaemia_district_pct": "Anaemia %",
    "iycf_district_pct": "IYCF inadeq %",
    "diarrhoea_district_pct": "Diarrhoea %"})
q.to_csv(TAB + "/Table5_quadruple_burden_hotspots.csv", index=False)
md.append("\n## Table 5. Confirmed quadruple-burden hotspot districts "
          f"(P>0.95 for all four outcomes; n = {len(q)})\n")
md.append(q.to_markdown(index=False) + "\n")

open(TAB + "/Results_Tables.md", "w").write("\n".join(md))
print(f"5 tables written. Table1 rows={len(t1)} Table5 rows={len(q)}")
for t, nm in [(t2, "T2"), (t4, "T4")]:
    print(nm, "OK", t.shape)
