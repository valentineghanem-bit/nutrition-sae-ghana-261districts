#!/usr/bin/env python3
"""10_figures_stats.py - SHAP summary + beeswarm, Moran scatterplots,
GWR local-coefficient maps, covariate correlation heatmap. 300 DPI."""
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
FEATURES = ["poverty_incidence", "poverty_intensity", "illiteracy_rate",
            "nhis_uninsured_rate", "employment_rate", "under15_share",
            "urbanicity", "improved_water_pct", "improved_sanitation_pct",
            "log_pop"]
NICE = {"poverty_incidence": "Poverty incidence",
        "poverty_intensity": "Poverty intensity",
        "illiteracy_rate": "Illiteracy rate",
        "nhis_uninsured_rate": "NHIS-uninsured share",
        "employment_rate": "Employment rate",
        "under15_share": "Under-15 share", "urbanicity": "Urbanicity",
        "improved_water_pct": "Improved water",
        "improved_sanitation_pct": "Improved sanitation",
        "log_pop": "Log population"}


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
        g = ft["geometry"]
        rings = ([g["coordinates"][0]] if g["type"] == "Polygon"
                 else [poly[0] for poly in g["coordinates"]])
        polys.append(rings)
        allpts = np.array([pt for r in rings for pt in r])
        cent.append([allpts[:, 1].mean(), allpts[:, 0].mean()])
        rg = str(ft["properties"]["REGION"]).strip().upper()
        preg.append(alias.get(rg, rg))
    return polys, np.array(cent), preg


def pv_map(df, col, polys, cent, preg):
    lat, lon = df["lat"].to_numpy(float), df["lon"].to_numpy(float)
    reg, val = df["region"].str.upper().to_numpy(), df[col].to_numpy()
    out = np.full(len(polys), np.nan)
    for p in range(len(polys)):
        cand = np.where(reg == preg[p])[0]
        if len(cand) == 0:
            cand = np.arange(len(df))
        dd = haversine(cent[p, 0], cent[p, 1], lat[cand], lon[cand])
        out[p] = val[cand[int(np.argmin(dd))]]
    return out


def main():
    df = pd.read_csv(OUT + "/master_261district_nutrition.csv")
    shimp = pd.read_csv(OUT + "/shap_importance.csv")
    W = np.load(OUT + "/W_queen.npy").astype(float)
    Wr = W / W.sum(1, keepdims=True)

    # Fig 5 - SHAP summary bar with bootstrap CI
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    for ax, (key, lab) in zip(axes.ravel(), OUTS):
        s = shimp[shimp.outcome == key].sort_values("mean_abs_shap")
        y = np.arange(len(s))
        err = np.clip([s["mean_abs_shap"] - s["boot_lo"],
                       s["boot_hi"] - s["mean_abs_shap"]], 0, None)
        ax.barh(y, s["mean_abs_shap"], xerr=err, color="#c97b30",
                edgecolor="#5a3410", error_kw={"elinewidth": 1})
        ax.set_yticks(y)
        ax.set_yticklabels(s["feature_label"], fontsize=9)
        ax.set_xlabel("Mean |SHAP value|  (95% bootstrap CI)", fontsize=10,
                      fontweight="semibold")
        ax.set_title(f"{lab}", fontsize=12, fontweight="semibold")
    fig.suptitle("Figure 5. SHAP determinant importance - XGBoost native "
                 "exact TreeSHAP (40x bootstrap)", fontsize=13,
                 fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(FIG + "/fig5_shap_importance.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("Fig 5 done")

    # Fig 6 - SHAP beeswarm
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    for ax, (key, lab) in zip(axes.ravel(), OUTS):
        sv = pd.read_csv(OUT + "/shap_values_" + key + ".csv")
        order = (shimp[shimp.outcome == key]
                 .sort_values("mean_abs_shap")["feature"].tolist())
        for yi, f in enumerate(order):
            s = sv["shap_" + f].to_numpy()
            v = sv["val_" + f].to_numpy()
            vn = (v - v.min()) / (np.ptp(v) + 1e-9)
            jit = yi + (np.random.rand(len(s)) - 0.5) * 0.6
            ax.scatter(s, jit, c=vn, cmap="coolwarm", s=8, alpha=0.7)
        ax.axvline(0, color="#888", lw=0.8)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([NICE[f] for f in order], fontsize=9)
        ax.set_xlabel("SHAP value (impact on district prevalence)",
                      fontsize=10, fontweight="semibold")
        ax.set_title(lab, fontsize=12, fontweight="semibold")
    sm = plt.cm.ScalarMappable(cmap="coolwarm")
    sm.set_array([0, 1])
    fig.colorbar(sm, ax=axes, shrink=0.5, label="Feature value (low->high)")
    fig.suptitle("Figure 6. SHAP beeswarm - direction and magnitude of "
                 "determinant effects", fontsize=13, fontweight="bold")
    plt.savefig(FIG + "/fig6_shap_beeswarm.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("Fig 6 done")

    # Fig 7 - Moran scatterplots
    mg = pd.read_csv(OUT + "/moran_global.csv")
    fig, axes = plt.subplots(2, 2, figsize=(12, 11))
    for ax, (key, lab) in zip(axes.ravel(), OUTS):
        x = df[key + "_district_pct"].to_numpy()
        z = (x - x.mean()) / x.std()
        lag = Wr @ z
        I = float(mg[mg.outcome == key].moran_I_queen.iloc[0])
        ax.scatter(z, lag, s=14, color="#235789", alpha=0.6)
        b = np.polyfit(z, lag, 1)
        xs = np.array([z.min(), z.max()])
        ax.plot(xs, b[0] * xs + b[1], color="#c1292e", lw=2)
        ax.axhline(0, color="#aaa", lw=0.7)
        ax.axvline(0, color="#aaa", lw=0.7)
        ax.set_xlabel("Standardised prevalence (z)", fontsize=10)
        ax.set_ylabel("Spatial lag", fontsize=10)
        ax.set_title(f"{lab} - Moran's I = {I:.3f}", fontsize=12,
                     fontweight="semibold")
    fig.suptitle("Figure 7. Moran's I scatterplots - global spatial "
                 "autocorrelation", fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(FIG + "/fig7_moran_scatter.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("Fig 7 done")

    # Fig 8 - GWR local coefficient maps (illiteracy)
    gc = pd.read_csv(OUT + "/gwr_local_coefficients.csv")
    dfg = df.merge(gc, on="district_id", suffixes=("", "_g"))
    polys, cent, preg = load_polys()
    fig, axes = plt.subplots(2, 2, figsize=(13, 13))
    for ax, (key, lab) in zip(axes.ravel(), OUTS):
        col = key + "_b_illiteracy_rate"
        pv = pv_map(dfg, col, polys, cent, preg)
        lim = np.nanmax(np.abs(pv))
        patches, colors = [], []
        for rings in polys:
            for r in rings:
                patches.append(MplPoly(np.array(r), closed=True))
        for p, rings in enumerate(polys):
            for r in rings:
                colors.append(pv[p])
        pc = PatchCollection(patches, cmap="RdBu_r", edgecolor="white",
                             linewidth=0.2)
        pc.set_array(np.array(colors))
        pc.set_clim(-lim, lim)
        ax.add_collection(pc)
        ax.autoscale_view()
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"{lab} - local GWR coefficient: illiteracy",
                     fontsize=11, fontweight="semibold")
        plt.colorbar(pc, ax=ax, shrink=0.7, label="Local beta (logit scale)")
    fig.suptitle("Figure 8. Geographically weighted regression - spatially "
                 "varying effect of illiteracy", fontsize=13,
                 fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(FIG + "/fig8_gwr_coefficients.png", dpi=300,
                bbox_inches="tight")
    plt.close()
    print("Fig 8 done")

    # Fig 9 - correlation heatmap
    cols = FEATURES + [k + "_district_pct" for k, _ in OUTS]
    labels = [NICE[f] for f in FEATURES] + [l for _, l in OUTS]
    C = np.corrcoef(df[cols].to_numpy().T)
    fig, ax = plt.subplots(figsize=(11, 9.5))
    im = ax.imshow(C, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=90, fontsize=8)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f"{C[i,j]:.2f}", ha="center", va="center",
                    fontsize=6, color="white" if abs(C[i, j]) > 0.5 else "black")
    plt.colorbar(im, shrink=0.8, label="Pearson r")
    ax.set_title("Figure 9. Covariate-outcome correlation matrix "
                 "(district level)", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG + "/fig9_correlation_matrix.png", dpi=300,
                bbox_inches="tight")
    plt.close()
    print("Fig 9 done")


if __name__ == "__main__":
    main()
