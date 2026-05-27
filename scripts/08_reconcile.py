#!/usr/bin/env python3
"""
08_reconcile.py - Phase 5 reconciliation (idempotent).
 (1) fixes sae_summary.csv hotspot counts (canonical = saved posteriors)
 (2) builds ONE authoritative Master CSV (46 cols, unambiguous names)
 (3) regenerates the Canonical Values Register
 (4) writes a data dictionary
 (5) prints a full cross-file reconciliation check
Reads the 22-column covariate base; selects base columns explicitly so the
script is safe to re-run.
"""
import numpy as np
import pandas as pd

OUT = "data/processed"
OUTS = ["stunting", "anaemia", "iycf", "diarrhoea"]
BASE_COLS = ["district_id", "district", "region", "lat", "lon", "urban_class",
             "urbanicity", "total_pop", "log_pop", "poverty_incidence",
             "poverty_intensity", "illiteracy_rate", "nhis_uninsured_rate",
             "employment_rate", "under15_share", "improved_water_pct",
             "improved_sanitation_pct", "women_literate_pct", "stunting_pct",
             "anaemia_pct", "iycf_inadeq_pct", "diarrhoea_pct"]

m = pd.read_csv(OUT + "/master_261district_nutrition.csv")
m = m[BASE_COLS].copy()                       # idempotent: keep only base cols
post = pd.read_csv(OUT + "/sae_posteriors.csv")
lisa = pd.read_csv(OUT + "/lisa_clusters.csv")
gi = pd.read_csv(OUT + "/getis_ord.csv")
sae = pd.read_csv(OUT + "/sae_summary.csv")
gwr = pd.read_csv(OUT + "/gwr_summary.csv")
mlp = pd.read_csv(OUT + "/ml_performance.csv")
hot = pd.read_csv(OUT + "/hotspot_classifier.csv")
mg = pd.read_csv(OUT + "/moran_global.csv")

# ---- (1) fix sae_summary hotspot counts -------------------------------------
fixed = []
for _, r in sae.iterrows():
    o = r["outcome"]
    canon = int((post[o + "_exceed"] > 0.95).sum())
    if int(r["hotspots_P95"]) != canon:
        print(f"FIX sae_summary {o}: hotspots_P95 {int(r['hotspots_P95'])}"
              f" -> {canon}")
    d = r.to_dict()
    d["hotspots_P95"] = canon
    fixed.append(d)
sae = pd.DataFrame(fixed)
sae.to_csv(OUT + "/sae_summary.csv", index=False)

# ---- (2) authoritative Master CSV -------------------------------------------
mas = m.rename(columns={"stunting_pct": "stunting_region_pct",
                        "anaemia_pct": "anaemia_region_pct",
                        "iycf_inadeq_pct": "iycf_region_pct",
                        "diarrhoea_pct": "diarrhoea_region_pct"})
for o in OUTS:
    mas[o + "_district_pct"] = post[o + "_mean"].to_numpy()
    mas[o + "_district_lo95"] = post[o + "_lo"].to_numpy()
    mas[o + "_district_hi95"] = post[o + "_hi"].to_numpy()
    mas[o + "_exceedance_prob"] = post[o + "_exceed"].to_numpy()
    mas[o + "_lisa_cluster"] = lisa.set_index("district_id").loc[
        mas["district_id"], o + "_lisa_cat"].to_numpy()
    mas[o + "_gistar_class"] = gi.set_index("district_id").loc[
        mas["district_id"], o + "_class"].to_numpy()

mas.to_csv(OUT + "/master_261district_nutrition.csv", index=False)
mas.to_csv(OUT + "/master_261district_nutrition_FINAL.csv", index=False)
print(f"Authoritative Master CSV: {mas.shape[0]} districts x {mas.shape[1]} cols")

# ---- (3) Canonical Values Register ------------------------------------------
reg = []
for o in OUTS:
    pm = mas[o + "_district_pct"]
    reg += [(f"district_{o}_min", round(float(pm.min()), 2)),
            (f"district_{o}_max", round(float(pm.max()), 2)),
            (f"district_{o}_median", round(float(pm.median()), 2)),
            (f"{o}_moran_I", float(mg[mg.outcome == o].moran_I_queen.iloc[0])),
            (f"{o}_moran_p", float(mg[mg.outcome == o].p_queen.iloc[0])),
            (f"{o}_phi_spatial", float(sae[sae.outcome == o].phi_spatial.iloc[0])),
            (f"{o}_hotspots_P95", int((mas[o + "_exceedance_prob"] > 0.95).sum())),
            (f"{o}_lisa_HH", int((mas[o + "_lisa_cluster"] == "HH").sum())),
            (f"{o}_gwr_dAICc", float(gwr[gwr.outcome == o].delta_aicc.iloc[0])),
            (f"{o}_xgb_LOROCV_R2", float(
                mlp[(mlp.outcome == o) & (mlp.model == "XGBoost")]
                .spatial_LOROCV_R2.iloc[0]))]
    if (hot.outcome == o).any():
        reg.append((f"{o}_hotspot_AUCPR",
                    float(hot[hot.outcome == o].AUC_PR.iloc[0])))
cv = pd.DataFrame(reg, columns=["value_name", "value"])
cv.to_csv(OUT + "/Canonical_Values_Nutrition.csv", index=False)

# ---- (4) data dictionary ----------------------------------------------------
dd = [
 ("district_id", "Sequential district identifier (1-261)"),
 ("district", "MMDA name (GSS 2021 Census)"),
 ("region", "Region (16-region 2022 structure)"),
 ("lat,lon", "District centroid coordinates (decimal degrees)"),
 ("urban_class,urbanicity", "Metropolitan/Municipal/District; ordinal 3/2/1"),
 ("total_pop,log_pop", "Total population 2021 Census; natural log"),
 ("poverty_incidence", "% population multidimensionally poor (Census 2021)"),
 ("poverty_intensity", "Mean deprivation share among the poor (%)"),
 ("illiteracy_rate", "% population illiterate (Census 2021)"),
 ("nhis_uninsured_rate", "% population without NHIS cover (Census 2021)"),
 ("employment_rate", "% labour force employed (Census 2021)"),
 ("under15_share", "% population aged under 15 (Census 2021)"),
 ("improved_water_pct", "% households improved water (GDHS 2022, region)"),
 ("improved_sanitation_pct", "% households improved sanitation (GDHS 2022, region)"),
 ("women_literate_pct", "% women literate (GDHS 2022, region)"),
 ("<outcome>_region_pct", "GDHS 2022 region direct estimate (%): stunting "
  "HAZ<-2SD u5; anaemia Hb<11 6-59m; iycf inadequacy (fails >=1 IYCF "
  "practice) 6-23m; diarrhoea 2-week prevalence u5"),
 ("<outcome>_district_pct", "BYM2 SAE posterior mean district prevalence (%)"),
 ("<outcome>_district_lo95/hi95", "95% credible interval bounds (%)"),
 ("<outcome>_exceedance_prob", "Posterior P(district prevalence > national mean)"),
 ("<outcome>_lisa_cluster", "Local Moran cluster: HH/LL/HL/LH/ns (p<0.05, FDR)"),
 ("<outcome>_gistar_class", "Getis-Ord Gi*: hotspot/coldspot/ns (|z|>1.96)"),
]
with open(OUT + "/master_csv_data_dictionary.txt", "w") as f:
    f.write("DATA DICTIONARY - master_261district_nutrition.csv (261 x 46)\n")
    f.write("=" * 64 + "\n")
    for k, v in dd:
        f.write(f"{k}\n    {v}\n")

# ---- (5) reconciliation check -----------------------------------------------
print("\n=== RECONCILIATION CHECK ===")
ok = True
for o in OUTS:
    h_mas = int((mas[o + "_exceedance_prob"] > 0.95).sum())
    h_sae = int(sae[sae.outcome == o].hotspots_P95.iloc[0])
    h_hot = (int(hot[hot.outcome == o].n_hotspots.iloc[0])
             if (hot.outcome == o).any() else h_mas)
    h_can = int(cv[cv.value_name == o + "_hotspots_P95"].value.iloc[0])
    agree = h_mas == h_sae == h_hot == h_can
    ok &= agree
    print(f"  {o:10s} hotspots master={h_mas} sae={h_sae} clf={h_hot} "
          f"canon={h_can}  {'OK' if agree else 'MISMATCH'}")
miss = [c for o in OUTS for c in
        [o + "_region_pct", o + "_district_pct", o + "_lisa_cluster"]
        if c not in mas.columns]
nn = {o: int(mas[o + "_district_pct"].notna().sum()) for o in OUTS}
dup = mas.columns[mas.columns.duplicated()].tolist()
print(f"  outcome columns present : {'OK' if not miss else 'MISSING ' + str(miss)}")
print(f"  district outcomes non-null (261 each): {nn}")
print(f"  duplicate columns       : {'none' if not dup else dup}")
print(f"  master CSV shape        : {mas.shape}")
print(f"\nRECONCILIATION: "
      f"{'ALL CONSISTENT' if ok and not miss and not dup else 'ERRORS REMAIN'}")
