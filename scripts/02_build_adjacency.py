#!/usr/bin/env python3
"""02_build_adjacency.py - queen + KNN5 spatial weights, 261 Ghana districts."""
import json
import numpy as np
import pandas as pd

OUT = "data/processed"
RAW = "data/raw"


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p = np.pi / 180.0
    a = (np.sin((lat2 - lat1) * p / 2) ** 2 +
         np.cos(lat1 * p) * np.cos(lat2 * p) *
         np.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * R * np.arcsin(np.sqrt(a))


def poly_rings(geom):
    t, c = geom["type"], geom["coordinates"]
    if t == "Polygon":
        yield c[0]
    elif t == "MultiPolygon":
        for poly in c:
            yield poly[0]


def components(W):
    n = len(W)
    seen, comps = set(), []
    for s in range(n):
        if s in seen:
            continue
        comp, stack = [], [s]
        seen.add(s)
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in np.where(W[u])[0]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        comps.append(comp)
    return comps


def main():
    df = pd.read_csv(OUT + "/master_261district_nutrition.csv")
    n = len(df)
    lat = df["lat"].to_numpy(float)
    lon = df["lon"].to_numpy(float)
    region = df["region"].to_numpy()

    gj = json.load(open(RAW + "/Ghana_New_260_District.geojson"))
    feats = gj["features"]
    npoly = len(feats)
    pcent = np.zeros((npoly, 2))
    preg, pverts = [], []
    alias = {"NORTHERN EAST": "NORTH EAST"}
    for i, ft in enumerate(feats):
        rg = str(ft["properties"]["REGION"]).strip().upper()
        preg.append(alias.get(rg, rg))
        pts, vs = [], set()
        for ring in poly_rings(ft["geometry"]):
            for x, y in ring:
                pts.append((x, y))
                vs.add((round(x, 5), round(y, 5)))
        pts = np.array(pts)
        pcent[i] = [pts[:, 1].mean(), pts[:, 0].mean()]
        pverts.append(vs)

    Wp = np.zeros((npoly, npoly), dtype=np.int8)
    for i in range(npoly):
        for j in range(i + 1, npoly):
            if pverts[i] & pverts[j]:
                Wp[i, j] = Wp[j, i] = 1
    poly_edges = int(Wp.sum() / 2)

    dist2poly = np.full(n, -1, dtype=int)
    for d in range(n):
        rg = region[d].upper()
        cand = [p for p in range(npoly) if preg[p] == rg]
        if not cand:
            continue
        dd = haversine(lat[d], lon[d], pcent[cand, 0], pcent[cand, 1])
        dist2poly[d] = cand[int(np.argmin(dd))]

    W = np.zeros((n, n), dtype=np.int8)
    for a in range(n):
        pa = dist2poly[a]
        if pa < 0:
            continue
        for b in range(a + 1, n):
            pb = dist2poly[b]
            if pb >= 0 and pa != pb and Wp[pa, pb]:
                W[a, b] = W[b, a] = 1

    unmatched = np.where(dist2poly < 0)[0]
    for d in unmatched:
        dd = haversine(lat[d], lon[d], lat, lon)
        dd[d] = np.inf
        for j in np.argsort(dd)[:3]:
            W[d, j] = W[j, d] = 1

    for d in range(n):
        if W[d].sum() == 0:
            dd = haversine(lat[d], lon[d], lat, lon)
            dd[d] = np.inf
            j = int(np.argmin(dd))
            W[d, j] = W[j, d] = 1

    n_bridges = 0
    while True:
        comps = components(W)
        if len(comps) == 1:
            break
        comps.sort(key=len)
        small = comps[0]
        rest = np.array([d for c in comps[1:] for d in c])
        best = (np.inf, -1, -1)
        for a in small:
            dd = haversine(lat[a], lon[a], lat[rest], lon[rest])
            jm = int(np.argmin(dd))
            if dd[jm] < best[0]:
                best = (dd[jm], a, int(rest[jm]))
        _, a, b = best
        W[a, b] = W[b, a] = 1
        n_bridges += 1

    k = 5
    Wk = np.zeros((n, n), dtype=np.int8)
    for d in range(n):
        dd = haversine(lat[d], lon[d], lat, lon)
        dd[d] = np.inf
        for j in np.argsort(dd)[:k]:
            Wk[d, j] = 1
    Wk = np.maximum(Wk, Wk.T)

    np.save(OUT + "/W_queen.npy", W)
    np.save(OUT + "/W_knn5.npy", Wk)

    deg = W.sum(1)
    L = []
    L.append("ADJACENCY REPORT - Ghana 261 districts")
    L.append("Polygon queen edges (260)   : " + str(poly_edges))
    L.append("District queen edges        : " + str(int(W.sum() / 2)))
    L.append("Mean neighbours (queen)     : " + format(deg.mean(), ".2f"))
    L.append("Min / max neighbours        : " + str(int(deg.min())) + " / " + str(int(deg.max())))
    L.append("Isolates after patching     : " + str(int((deg == 0).sum())))
    L.append("Component bridges added     : " + str(n_bridges))
    L.append("Districts matched to polygon: " + str(int((dist2poly >= 0).sum())) + "/" + str(n))
    L.append("KNN(5) edges                : " + str(int(Wk.sum() / 2)))
    L.append("Graph connected (queen)     : " + str(len(components(W)) == 1))
    open(OUT + "/adjacency_report.txt", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
