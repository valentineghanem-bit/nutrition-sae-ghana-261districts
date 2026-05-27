#!/usr/bin/env python3
"""11_fig6_rebuild.py - cleaner SHAP beeswarm: dedicated colorbar axis,
generous spacing, controlled jitter, no label/point overlap."""
import os
os.environ["MPLCONFIGDIR"] = "/tmp/mplcfg"
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT, FIG = "data/processed", "figures"
OUTS = [("stunting", "Stunting"), ("anaemia", "Anaemia"),
        ("iycf", "IYCF inadequacy"), ("diarrhoea", "Diarrhoea")]
NICE = {"poverty_incidence": "Poverty incidence",
        "poverty_intensity": "Poverty intensity",
        "illiteracy_rate": "Illiteracy rate",
        "nhis_uninsured_rate": "NHIS-uninsured share",
        "employment_rate": "Employment rate",
        "under15_share": "Under-15 share", "urbanicity": "Urbanicity",
        "improved_water_pct": "Improved water",
        "improved_sanitation_pct": "Improved sanitation",
        "log_pop": "Log population"}

shimp = pd.read_csv(OUT + "/shap_importance.csv")
rng = np.random.default_rng(42)

fig, axes = plt.subplots(2, 2, figsize=(17, 13.5))
fig.subplots_adjust(left=0.16, right=0.88, top=0.90, bottom=0.10,
                    wspace=0.62, hspace=0.34)

for ax, (key, lab) in zip(axes.ravel(), OUTS):
    sv = pd.read_csv(OUT + "/shap_values_" + key + ".csv")
    order = (shimp[shimp.outcome == key]
             .sort_values("mean_abs_shap")["feature"].tolist())
    alls = np.concatenate([sv["shap_" + f].to_numpy() for f in order])
    xlo, xhi = alls.min(), alls.max()
    pad = 0.08 * (xhi - xlo)
    for yi, f in enumerate(order):
        s = sv["shap_" + f].to_numpy()
        v = sv["val_" + f].to_numpy()
        vn = (v - v.min()) / (np.ptp(v) + 1e-9)
        jit = yi + (rng.random(len(s)) - 0.5) * 0.34
        sc = ax.scatter(s, jit, c=vn, cmap="coolwarm", s=7, alpha=0.55,
                        linewidths=0)
    ax.axvline(0, color="#555", lw=0.9, zorder=0)
    for yi in range(len(order)):
        ax.axhline(yi, color="#f0f0f0", lw=6, zorder=-1)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([NICE[f] for f in order], fontsize=10)
    ax.set_ylim(-0.7, len(order) - 0.3)
    ax.set_xlim(xlo - pad, xhi + pad)
    ax.set_xlabel("SHAP value  (impact on district prevalence, pp)",
                  fontsize=10, fontweight="semibold")
    ax.set_title(lab, fontsize=13, fontweight="semibold", pad=8)
    ax.tick_params(axis="x", labelsize=9)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)

cax = fig.add_axes([0.91, 0.30, 0.015, 0.40])
sm = plt.cm.ScalarMappable(cmap="coolwarm")
sm.set_array([0, 1])
cb = fig.colorbar(sm, cax=cax)
cb.set_ticks([0, 1])
cb.set_ticklabels(["Low", "High"])
cb.set_label("District feature value", fontsize=10, fontweight="semibold")

fig.suptitle("Figure 6. SHAP beeswarm - direction and magnitude of "
             "determinant effects on district prevalence",
             fontsize=14, fontweight="bold", y=0.965)
fig.text(0.5, 0.035, "Each point = one of 261 districts. Horizontal position "
         "= SHAP contribution; colour = the district's value of that feature. "
         "Features ordered by mean |SHAP|. XGBoost native exact TreeSHAP.",
         ha="center", fontsize=9, style="italic")
plt.savefig(FIG + "/fig6_shap_beeswarm.png", dpi=300, bbox_inches="tight")
plt.close()
print("Figure 6 rebuilt")
