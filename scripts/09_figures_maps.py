#!/usr/bin/env python3
"""09_figures_maps.py - district choropleth maps from the 260-polygon GeoJSON:
SAE posterior prevalence, BYM exceedance probability, LISA cluster maps,
bivariate LISA. 300 DPI."""
import os
os.environ["MPLCONFIGDIR"] = "/tmp/mplcfg"
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
from matplotlib.collections import PatchCollection

OUT, FIG, RAW = "data/processed", "figures", "data/raw"
OUTS = [("stunting", "Stunting"), ("anaemia", "Anaemia"),
        ("iycf", "IYCF inadequacy"), ("diarrhoea", "Diarrhoea")]


def haversine(la1, lo1, la2, lo2):
    R, p = 6371.0, np.pi / 180.0
    a = (np.sin((la2 - la1) * p / 2) ** 2 + np.cos(la1 * p) *
         np.cos(la2 * p) * np.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * R * np.arcsin(np.sqrt(a))


def load_polys():
    gj = json.load(open(RAW + "/Ghana_New_260_District.geojson"))
    polys, cent, preg = [], [], []
    alias = {"NORTHERN EAST": "NORTH EAST"}
    for ft in gj["features"]:
        rings = []
        g = ft["geometry"]
        if g["type"] == "Polygon":
            rings = [g["coordinates"][0]]
        else:
            rings = [poly[0] for poly in g["coordinates"]]
        polys.append(rings)
        allpts = np.array([pt for r in rings for pt in r])
        cent.append([allpts[:, 1].mean(), allpts[:, 0].mean()])
        rg = str(ft["properties"]["REGION"]).strip().upper()
        preg.append(alias.get(rg, rg))
    return polys, np.array(cent), preg


def poly_values(df, col, polys, cent, preg):
    """Map each polygon to a district value via within-region nearest centroid."""
    lat = df["lat"].to_numpy(float)
    lon = df["lon"].to_numpy(float)
    reg = df["region"].str.upper().to_numpy()
    val = df[col].to_numpy()
    pv = np.full(len(polys), np.nan)
    for p in range(len(polys)):
        cand = np.where(reg == preg[p])[0]
        if len(cand) == 0:
            cand = np.arange(len(df))
        dd = haversine(cent[p, 0], cent[p, 1], lat[cand], lon[cand])
        pv[p] = val[cand[int(np.argmin(dd))]]
    return pv


def draw(ax, polys, vals, cmap, vmin, vmax, title, cats=None, catcol=None):
    patches, colors = [], []
    for p, rings in enumerate(polys):
        for r in rings:
            patches.append(MplPoly(np.array(r), closed=True))
            if cats is not None:
                colors.append(catcol.get(cats[p], "#dddddd"))
            else:
                colors.append(vals[p])
    if cats is not None:
        pc = PatchCollection(patches, facecolor=colors, edgecolor="white",
                             linewidth=0.2)
        ax.add_collection(pc)
    else:
        pc = PatchCollection(patches, cmap=cmap, edgecolor="white",
                             linewidth=0.2)
        pc.set_array(np.array(colors))
        pc.set_clim(vmin, vmax)
        ax.add_collection(pc)
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=12, fontweight="semibold")
    return pc


def main():
    df = pd.read_csv(OUT + "/master_261district_nutrition.csv")
    polys, cent, preg = load_polys()

    # Fig 1 - SAE posterior prevalence choropleths
    fig, axes = plt.subplots(2, 2, figsize=(13, 13))
    for ax, (key, lab) in zip(axes.ravel(), OUTS):
        pv = poly_values(df, key + "_district_pct", polys, cent, preg)
        pc = draw(ax, polys, pv, "YlOrRd", np.nanpercentile(pv, 2),
                  np.nanpercentile(pv, 98),
                  f"{lab} - BYM2 posterior mean (%)")
        plt.colorbar(pc, ax=ax, shrink=0.7, label="District prevalence (%)")
    fig.suptitle("Figure 1. District-level small-area posterior prevalence, "
                 "Ghana 2022 (261 districts)", fontsize=13, fontweight="bold")
    fig.text(0.5, 0.01, "BYM2 small-area estimation; GDHS 2022 region direct "
             "estimates + 2021 Census district covariates. Polygons: 260-"
             "district GeoJSON (Guan shares its parent Oti polygon).",
             ha="center", fontsize=8.5, style="italic")
    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    plt.savefig(FIG + "/fig1_choropleth_prevalence.png", dpi=300,
                bbox_inches="tight")
    plt.close()
    print("Fig 1 done")

    # Fig 2 - exceedance probability maps
    fig, axes = plt.subplots(2, 2, figsize=(13, 13))
    for ax, (key, lab) in zip(axes.ravel(), OUTS):
        pv = poly_values(df, key + "_exceedance_prob", polys, cent, preg)
        pc = draw(ax, polys, pv, "RdPu", 0, 1,
                  f"{lab} - P(prevalence > national mean)")
        plt.colorbar(pc, ax=ax, shrink=0.7, label="Exceedance probability")
    fig.suptitle("Figure 2. Posterior exceedance probability - confirmed "
                 "hotspots P>0.95", fontsize=13, fontweight="bold")
    fig.text(0.5, 0.01, "Districts with exceedance probability > 0.95 are "
             "confirmed high-burden hotspots (stunting 31, anaemia 60, "
             "IYCF 37, diarrhoea 51).", ha="center", fontsize=8.5,
             style="italic")
    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    plt.savefig(FIG + "/fig2_exceedance_probability.png", dpi=300,
                bbox_inches="tight")
    plt.close()
    print("Fig 2 done")

    # Fig 3 - LISA cluster maps
    catcol = {"HH": "#c1292e", "LL": "#235789", "HL": "#f1a208",
              "LH": "#7ec4cf", "ns": "#e8e8e8"}
    fig, axes = plt.subplots(2, 2, figsize=(13, 13))
    for ax, (key, lab) in zip(axes.ravel(), OUTS):
        cats = poly_values_cat(df, key + "_lisa_cluster", polys, cent, preg)
        draw(ax, polys, None, None, 0, 1,
             f"{lab} - LISA clusters", cats=cats, catcol=catcol)
    handles = [plt.Rectangle((0, 0), 1, 1, fc=catcol[c]) for c in
               ["HH", "LL", "HL", "LH", "ns"]]
    fig.legend(handles, ["High-High", "Low-Low", "High-Low", "Low-High",
               "Not significant"], loc="lower center", ncol=5, fontsize=9)
    fig.suptitle("Figure 3. Local Indicators of Spatial Association (LISA) "
                 "clusters, p<0.05 (FDR)", fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0.05, 1, 0.96])
    plt.savefig(FIG + "/fig3_lisa_clusters.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("Fig 3 done")

    # Fig 4 - bivariate LISA stunting x anaemia
    bl = pd.read_csv(OUT + "/bivariate_lisa.csv")
    dfb = df.merge(bl[["district_id", "stunting_x_anaemia_cat"]],
                   on="district_id")
    cats = poly_values_cat(dfb, "stunting_x_anaemia_cat", polys, cent, preg)
    fig, ax = plt.subplots(figsize=(8, 9))
    draw(ax, polys, None, None, 0, 1,
         "Bivariate LISA: stunting (x) vs anaemia (spatial lag)",
         cats=cats, catcol=catcol)
    handles = [plt.Rectangle((0, 0), 1, 1, fc=catcol[c]) for c in
               ["HH", "LL", "HL", "LH", "ns"]]
    ax.legend(handles, ["High stunting-High anaemia",
              "Low-Low", "High-Low", "Low-High", "Not significant"],
              loc="lower left", fontsize=8)
    fig.suptitle("Figure 4. Bivariate spatial co-clustering of childhood "
                 "stunting and anaemia", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG + "/fig4_bivariate_lisa.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("Fig 4 done")


def poly_values_cat(df, col, polys, cent, preg):
    lat = df["lat"].to_numpy(float)
    lon = df["lon"].to_numpy(float)
    reg = df["region"].str.upper().to_numpy()
    val = df[col].astype(str).to_numpy()
    pv = []
    for p in range(len(polys)):
        cand = np.where(reg == preg[p])[0]
        if len(cand) == 0:
            cand = np.arange(len(df))
        dd = haversine(cent[p, 0], cent[p, 1], lat[cand], lon[cand])
        pv.append(val[cand[int(np.argmin(dd))]])
    return pv


if __name__ == "__main__":
    main()
