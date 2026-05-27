#!/usr/bin/env python3
"""14_residual_moran.py - residual spatial-autocorrelation diagnostic.

Closes the QA-7 open minor: an explicit Moran's I check on the BYM2 posterior
*residuals* after subtracting the region-mean — directly tests whether the high
global Moran's I (0.82-0.96) is driven by the regional gradient (in which case
the within-region residual I will be near zero) or whether substantial
district-level spatial structure remains after the regional signal is removed.

Same statistic and W as 04_spatial_diagnostics.py: row-standardised queen
contiguity, 999 conditional permutations, fixed seed 42.

Inputs : data/processed/sae_posteriors.csv, data/processed/W_queen.npy
Output : data/processed/residual_moran.csv (and console summary)
"""
import numpy as np
import pandas as pd

OUT = "data/processed"
RNG = np.random.default_rng(42)
OUTS = ["stunting", "anaemia", "iycf", "diarrhoea"]
PERMS = 999


def row_std(W):
    rs = W.sum(1, keepdims=True)
    rs[rs == 0] = 1
    return W / rs


def moran_global(x, Wr, perms=PERMS):
    z = x - x.mean()
    n = len(x)
    S0 = Wr.sum()
    den = z @ z
    if den == 0:
        return float("nan"), float("nan"), float("nan")
    I = (n / S0) * ((z @ (Wr @ z)) / den)
    Zp = np.array([RNG.permutation(z) for _ in range(perms)])
    sim = (n / S0) * (np.einsum("ki,ij,kj->k", Zp, Wr, Zp) / den)
    ge = (np.sum(sim >= I) + 1) / (perms + 1)
    p = min(ge, 1 - ge) * 2
    zscore = (I - sim.mean()) / sim.std()
    return I, zscore, p


def main():
    post = pd.read_csv(OUT + "/sae_posteriors.csv")
    W = np.load(OUT + "/W_queen.npy").astype(float)
    Wr = row_std(W)

    rows = []
    print(f"\n{'Outcome':<20}{'Posterior I':>14}{'Within-region':>18}"
          f"{'z':>8}{'p':>10}")
    print("-" * 70)
    for o in OUTS:
        x = post[o + "_mean"].to_numpy()
        # raw posterior Moran's I (for cross-check vs 04 outputs)
        I_raw, _, p_raw = moran_global(x, Wr)
        # within-region residuals
        rmeans = post.groupby("region")[o + "_mean"].transform("mean").to_numpy()
        resid = x - rmeans
        I_res, z_res, p_res = moran_global(resid, Wr)
        print(f"{o:<20}{I_raw:>14.4f}{I_res:>18.4f}{z_res:>8.2f}{p_res:>10.4f}")
        rows.append({"outcome": o, "posterior_moran_I": round(I_raw, 4),
                     "posterior_p": round(p_raw, 4),
                     "within_region_residual_I": round(I_res, 4),
                     "within_region_residual_z": round(z_res, 3),
                     "within_region_residual_p": round(p_res, 4)})
    pd.DataFrame(rows).to_csv(OUT + "/residual_moran.csv", index=False)
    print(f"\nSaved: {OUT}/residual_moran.csv")
    print("\nInterpretation. If within-region residual Moran's I is near zero,")
    print("the regional gradient explains the global spatial signal and the")
    print("BYM2 spatial term has captured the structured component fully.")


if __name__ == "__main__":
    main()
