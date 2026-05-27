#!/usr/bin/env python3
"""13 - rebuild fig5 SHAP importance bar (bootstrap-mean estimate + 95% CI)."""
import os
os.environ["MPLCONFIGDIR"] = "/tmp/mplcfg"
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT, FIG = "data/processed", "figures"
OUTS = [("stunting","Stunting"),("anaemia","Anaemia"),
        ("iycf","IYCF inadequacy"),("diarrhoea","Diarrhoea")]
shimp = pd.read_csv(OUT+"/shap_importance.csv")
fig, axes = plt.subplots(2,2,figsize=(14,11))
for ax,(key,lab) in zip(axes.ravel(),OUTS):
    s = shimp[shimp.outcome==key].sort_values("mean_abs_shap")
    y = np.arange(len(s))
    err = np.clip([s["mean_abs_shap"]-s["boot_lo"],
                   s["boot_hi"]-s["mean_abs_shap"]],0,None)
    ax.barh(y,s["mean_abs_shap"],xerr=err,color="#c97b30",
            edgecolor="#5a3410",error_kw={"elinewidth":1.1,"capsize":2})
    ax.set_yticks(y); ax.set_yticklabels(s["feature_label"],fontsize=9)
    ax.set_xlabel("Mean |SHAP value| - bootstrap mean (95% percentile CI)",
                  fontsize=10,fontweight="semibold")
    ax.set_title(lab,fontsize=12,fontweight="semibold")
    for sp in ["top","right"]: ax.spines[sp].set_visible(False)
fig.suptitle("Figure 5. SHAP determinant importance - XGBoost native exact "
             "TreeSHAP (40x bootstrap)",fontsize=13,fontweight="bold")
fig.text(0.5,0.01,"Importance = bootstrap mean of mean|SHAP|; bars show the "
         "95% bootstrap percentile interval.",ha="center",fontsize=8.5,
         style="italic")
plt.tight_layout(rect=[0,0.03,1,0.96])
plt.savefig(FIG+"/fig5_shap_importance.png",dpi=300,bbox_inches="tight")
plt.close(); print("Figure 5 rebuilt")
