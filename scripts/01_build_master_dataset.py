#!/usr/bin/env python3
"""
01_build_master_dataset.py
Project 10 - Nutrition / Anaemia / Child-Growth Determinants, Ghana 261 districts.
Phase 5 Step 1: integrate 13 raw files -> master_261district_nutrition.csv

Author : Valentine Golden Ghanem | AIPOCH v6.0
Inputs : data/raw/Master_Sheet.xlsx (261 districts, GSS Census 2021 covariates)
         data/raw/Ghana_New_260_District.geojson (260 district polygons)
         data/raw/{anemia,iycf,diarrhea,water,toilet-facilities,
                   select-education-indicators,health-insurance}_subnational_gha.csv
         GDHS 2022 Summary Report - 16-region stunting table (hard-coded, cited)
Output : data/processed/master_261district_nutrition.csv
         data/processed/adjacency_261.npy  (queen-contiguity matrix)
Notes  : Outcomes are region-level (GDHS 2022, 16 regions); covariates are
         district-level (GSS Census 2021). District outcome variation is
         introduced at the SAE stage (script 02), NOT here.
"""
import json
import numpy as np
import pandas as pd

RAW = "data/raw"
OUT = "data/processed"

# ----------------------------------------------------------------------
# 1. Ghana 2022 16-region structure + outcome data
# ----------------------------------------------------------------------
REGIONS16 = ["Western", "Central", "Greater Accra", "Volta", "Eastern",
             "Ashanti", "Western North", "Ahafo", "Bono", "Bono East",
             "Oti", "Northern", "Savannah", "North East",
             "Upper East", "Upper West"]

# DHS subnational location label -> canonical region name
DHS_LOC_MAP = {
    "Western (post 2022)": "Western", "Central": "Central",
    "Greater Accra": "Greater Accra", "Volta (post 2022)": "Volta",
    "Eastern": "Eastern", "Ashanti": "Ashanti",
    "Western North": "Western North", "Ahafo": "Ahafo", "Bono": "Bono",
    "Bono East": "Bono East", "Oti": "Oti",
    "..Northern(post 2022)": "Northern", "..Savannah": "Savannah",
    "..Northeast": "North East", "Upper East": "Upper East",
    "Upper West": "Upper West",
}

# Stunting, % children under 5 (HAZ < -2 SD) -- GDHS 2022 Summary Report,
# "Stunting by Region" infographic map. National 17 %.
STUNTING_2022 = {
    "Western": 14.0, "Central": 17.0, "Greater Accra": 11.0, "Volta": 14.0,
    "Eastern": 10.0, "Ashanti": 17.0, "Western North": 11.0, "Ahafo": 17.0,
    "Bono": 14.0, "Bono East": 17.0, "Oti": 20.0, "Northern": 30.0,
    "Savannah": 21.0, "North East": 29.0, "Upper East": 21.0,
    "Upper West": 17.0,
}


def load_dhs_outcome(fname, indicator, recall=None):
    """Return {region: value} for one DHS subnational indicator, 2022 wave."""
    d = pd.read_csv(f"{RAW}/{fname}", low_memory=False)
    d = d[(d["SurveyYear"] == "2022") & (d["Indicator"] == indicator)]
    d = d[d["Location"].isin(DHS_LOC_MAP)]
    if recall is not None:
        d = d[d["ByVariableLabel"] == recall]
    out = {}
    for _, r in d.iterrows():
        reg = DHS_LOC_MAP[r["Location"]]
        out[reg] = float(r["Value"])
    return out


def main():
    # --- region-level outcomes -------------------------------------------------
    anaemia = load_dhs_outcome("anemia_subnational_gha.csv",
                               "Children with any anemia")
    iycf3 = load_dhs_outcome("iycf_subnational_gha.csv",
                             "Children 6-23 months with 3 IYCF practices")
    iycf_inadeq = {k: round(100.0 - v, 1) for k, v in iycf3.items()}
    diarrhoea = load_dhs_outcome("diarrhea_subnational_gha.csv",
                                 "Children with diarrhea",
                                 recall="Three years preceding the survey")

    # --- region-level covariates (WASH, female literacy, NHIS) -----------------
    water = load_dhs_outcome("water_subnational_gha.csv",
                             "Households using an improved water source")
    sanitation = load_dhs_outcome("toilet-facilities_subnational_gha.csv",
                                  "Households with an improved sanitation facility")
    wlit = load_dhs_outcome("select-education-indicators_subnational_gha.csv",
                            "Women who are literate")

    region_tbl = pd.DataFrame({
        "region": REGIONS16,
        "stunting_pct":   [STUNTING_2022[r] for r in REGIONS16],
        "anaemia_pct":    [anaemia[r] for r in REGIONS16],
        "iycf_inadeq_pct":[iycf_inadeq[r] for r in REGIONS16],
        "diarrhoea_pct":  [diarrhoea[r] for r in REGIONS16],
        "improved_water_pct":      [water[r] for r in REGIONS16],
        "improved_sanitation_pct": [sanitation[r] for r in REGIONS16],
        "women_literate_pct":      [wlit[r] for r in REGIONS16],
    })
    region_tbl.to_csv(f"{OUT}/region_outcomes_2022.csv", index=False)
    print("Region table (16 regions, 2022):")
    print(region_tbl.round(1).to_string(index=False))

    # --- district covariates (Master Sheet, GSS Census 2021) -------------------
    ms = pd.read_excel(f"{RAW}/Master_Sheet.xlsx", sheet_name="Sheet1")
    ms = ms.rename(columns={
        "Metropolitan, Municipal, and District Assemblies (MMDA's)": "district",
        "Region": "region", "Class": "urban_class",
        "Latitude": "lat", "Longitude": "lon",
        "Employed Population": "employed", "Unemployed Population": "unemployed",
        "Incidence of Poverty": "poverty_incidence",
        "Intensity of Poverty": "poverty_intensity",
        "Illiterate Population": "illiterate_n",
        "Uninsured Population": "uninsured_n",
        "Total Population": "total_pop",
    })
    ms["region"] = ms["region"].str.strip().str.title()
    ms["region"] = ms["region"].replace({"North East": "North East"})

    # derived district covariates
    ms["illiteracy_rate"] = 100.0 * ms["illiterate_n"] / ms["total_pop"]
    ms["nhis_uninsured_rate"] = 100.0 * ms["uninsured_n"] / ms["total_pop"]
    lab = ms["employed"] + ms["unemployed"]
    ms["employment_rate"] = 100.0 * ms["employed"] / lab.replace(0, np.nan)
    u15 = (ms["Male Population 0-14"] + ms["Female Population 0-14"])
    ms["under15_share"] = 100.0 * u15 / ms["total_pop"]
    ms["log_pop"] = np.log(ms["total_pop"])
    urb = {"Metropolitan": 3, "Municipal": 2, "District": 1}
    ms["urbanicity"] = ms["urban_class"].str.strip().str.title().map(urb).fillna(1)

    # --- merge region outcomes/covariates onto each district ------------------
    df = ms.merge(region_tbl, on="region", how="left")
    miss = df[df["stunting_pct"].isna()]["region"].unique()
    if len(miss):
        raise SystemExit(f"Unmatched regions: {miss}")

    keep = ["district", "region", "lat", "lon", "urban_class", "urbanicity",
            "total_pop", "log_pop", "poverty_incidence", "poverty_intensity",
            "illiteracy_rate", "nhis_uninsured_rate", "employment_rate",
            "under15_share", "improved_water_pct", "improved_sanitation_pct",
            "women_literate_pct", "stunting_pct", "anaemia_pct",
            "iycf_inadeq_pct", "diarrhoea_pct"]
    df = df[keep].copy()
    df.insert(0, "district_id", range(1, len(df) + 1))

    df.to_csv(f"{OUT}/master_261district_nutrition.csv", index=False)
    print(f"\nMaster dataset written: {df.shape[0]} districts x {df.shape[1]} cols")
    print(f"Districts per region:\n{df['region'].value_counts().to_string()}")
    print(f"\nCovariate summary:")
    print(df[["poverty_incidence", "poverty_intensity", "illiteracy_rate",
              "nhis_uninsured_rate", "employment_rate", "under15_share"]]
          .describe().round(2).to_string())
    return df


if __name__ == "__main__":
    main()
