#!/usr/bin/env python3
"""04_spatial_diagnostics.py - vectorised spatial autocorrelation on SAE
posteriors. Global Moran's I, LISA, Bivariate LISA (6 pairs), Getis-Ord Gi*.
999-permutation inference (vectorised), Benjamini-Hochberg FDR."""
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
    I = (n / S0) * ((z @ (Wr @ z)) / den)
    Zp = np.array([RNG.permutation(z) for _ in range(perms)])     # perms x n
    sim = (n / S0) * (np.einsum("ki,ij,kj->k", Zp, Wr, Zp) / den)
    ge = (np.sum(sim >= I) + 1) / (perms + 1)
    p = min(ge, 1 - ge) * 2
    zscore = (I - sim.mean()) / sim.std()
    return I, zscore, p


def _perm_index(n, nb, perms):
    """perms x nb matrix of distinct indices drawn from range(n)."""
    rand = RNG.random((perms, n))
    return np.argsort(rand, axis=1)[:, :nb]


def local_perm(zx_i, w_i, pool, perms):
    """vectorised conditional-permutation null for one district."""
    m = len(pool)
    idx = _perm_index(m, len(w_i), perms)        # perms x nb
    samp = pool[idx]                              # perms x nb (values)
    return zx_i * (samp @ w_i)                    # perms,


def lisa(x, Wr, bivar_y=None, perms=PERMS):
    n = len(x)
    if bivar_y is None:
        zx = x - x.mean()
        zy = zx
        m2 = (zx @ zx) / n
        scale = 1.0 / m2
    else:
        zx = (x - x.mean()) / x.std()
        zy = (bivar_y - bivar_y.mean()) / bivar_y.std()
        scale = 1.0
    lag = Wr @ zy
    Ii = scale * zx * lag
    p = np.empty(n)
    allidx = np.arange(n)
    for i in range(n):
        wi_idx = np.where(Wr[i] > 0)[0]
        w_i = Wr[i, wi_idx]
        pool = np.delete(zy, i)
        sim = scale * local_perm(zx[i], w_i, pool, perms)
        ge = (np.sum(sim >= Ii[i]) + 1) / (perms + 1)
        p[i] = min(ge, 1 - ge) * 2
    cat = np.array(["ns"] * n, dtype=object)
    for i in range(n):
        if p[i] < 0.05:
            hi_x = zx[i] > 0
            hi_l = lag[i] > 0
            cat[i] = ("HH" if hi_x and hi_l else "LL" if not hi_x and not hi_l
                      else "HL" if hi_x and not hi_l else "LH")
    return Ii, p, cat, lag


def getis_ord(x, Wb):
    n = len(x)
    Ws = Wb + np.eye(n)
    xbar, s = x.mean(), x.std()
    Gi = np.empty(n)
    for i in range(n):
        wi = Ws[i]
        sw = wi.sum()
        num = wi @ x - xbar * sw
        den = s * np.sqrt(max((n * (wi @ wi) - sw ** 2) / (n - 1), 1e-12))
        Gi[i] = num / den
    return Gi


def bh_fdr(p, q=0.05):
    order = np.argsort(p)
    m = len(p)
    thr = q * np.arange(1, m + 1) / m
    passed = p[order] <= thr
    keep = np.zeros(m, dtype=bool)
    if passed.any():
        keep[order[:np.where(passed)[0].max() + 1]] = True
    return keep


def main():
    df = pd.read_csv(OUT + "/sae_posteriors.csv")
    W = np.load(OUT + "/W_queen.npy").astype(float)
    Wk = np.load(OUT + "/W_knn5.npy").astype(float)
    Wr, Wrk = row_std(W), row_std(Wk)
    vals = {o: df[o + "_mean"].to_numpy() for o in OUTS}

    rows = []
    for o in OUTS:
        I, zs, p = moran_global(vals[o], Wr)
        Ik, zk, pk = moran_global(vals[o], Wrk)
        rows.append({"outcome": o, "moran_I_queen": round(I, 4),
                     "z_queen": round(zs, 3), "p_queen": round(p, 4),
                     "moran_I_knn5": round(Ik, 4), "p_knn5": round(pk, 4)})
        print(f"Moran {o:10s} queen I={I:.3f} z={zs:.1f} p={p:.4f} | "
              f"knn5 I={Ik:.3f} p={pk:.4f}")
    pd.DataFrame(rows).to_csv(OUT + "/moran_global.csv", index=False)

    lc = pd.DataFrame({"district_id": df["district_id"],
                       "district": df["district"], "region": df["region"]})
    for o in OUTS:
        Ii, p, cat, lag = lisa(vals[o], Wr)
        keep = bh_fdr(p)
        cat = np.where(keep, cat, "ns")
        lc[o + "_lisa_I"] = np.round(Ii, 4)
        lc[o + "_lisa_p"] = np.round(p, 4)
        lc[o + "_lisa_cat"] = cat
        c = pd.Series(cat).value_counts().to_dict()
        print(f"LISA {o:10s} HH={c.get('HH',0)} LL={c.get('LL',0)} "
              f"HL={c.get('HL',0)} LH={c.get('LH',0)}")
    lc.to_csv(OUT + "/lisa_clusters.csv", index=False)

    bl = pd.DataFrame({"district_id": df["district_id"],
                       "district": df["district"], "region": df["region"]})
    grows = []
    for a in range(len(OUTS)):
        for b in range(a + 1, len(OUTS)):
            o1, o2 = OUTS[a], OUTS[b]
            Ii, p, cat, lag = lisa(vals[o1], Wr, bivar_y=vals[o2])
            keep = bh_fdr(p)
            cat = np.where(keep, cat, "ns")
            tag = o1 + "_x_" + o2
            bl[tag + "_I"] = np.round(Ii, 4)
            bl[tag + "_cat"] = cat
            c = pd.Series(cat).value_counts().to_dict()
            grows.append({"pair": tag, "global_biv_I": round(Ii.mean(), 4),
                          "HH": c.get("HH", 0), "LL": c.get("LL", 0),
                          "HL": c.get("HL", 0), "LH": c.get("LH", 0)})
            print(f"BivLISA {tag:22s} I={Ii.mean():.3f} HH={c.get('HH',0)} "
                  f"LL={c.get('LL',0)}")
    bl.to_csv(OUT + "/bivariate_lisa.csv", index=False)
    pd.DataFrame(grows).to_csv(OUT + "/bivariate_lisa_global.csv", index=False)

    go = pd.DataFrame({"district_id": df["district_id"],
                       "district": df["district"], "region": df["region"]})
    for o in OUTS:
        Gi = getis_ord(vals[o], W)
        go[o + "_giz"] = np.round(Gi, 3)
        go[o + "_class"] = np.where(Gi > 1.96, "hotspot",
                            np.where(Gi < -1.96, "coldspot", "ns"))
        print(f"Gi* {o:10s} hot={(Gi>1.96).sum()} cold={(Gi<-1.96).sum()}")
    go.to_csv(OUT + "/getis_ord.csv", index=False)
    print("Spatial diagnostics complete.")


if __name__ == "__main__":
    main()
