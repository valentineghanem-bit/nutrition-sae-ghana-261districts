#!/usr/bin/env python3
"""build_dashboard.py - self-contained interactive surveillance dashboard.

Project 10: Ghana child-nutrition small-area estimation.
Embeds a simplified 260-district GeoJSON, the 261-district master data, SHAP
determinants, spatial statistics, region outcomes and the quadruple-burden
hotspot table. Plotly.js is loaded pinned from cdnjs. The polygon-to-district
crosswalk replicates 09_figures_maps.py (within-region nearest centroid).
Output: dashboard/Nutrition_Dashboard.html
"""
import csv
import json
import math
import os

BASE = os.environ.get("PROJ_BASE", os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")
TAB = os.path.join(BASE, "tables")
OUTDIR = os.path.join(BASE, "dashboard")
os.makedirs(OUTDIR, exist_ok=True)
OUT = os.path.join(OUTDIR, "Nutrition_Dashboard.html")

OUTS = ["stunting", "anaemia", "iycf", "diarrhoea"]
LABEL = {"stunting": "Stunting", "anaemia": "Anaemia",
         "iycf": "IYCF inadequacy", "diarrhoea": "Diarrhoea"}


def haversine(la1, lo1, la2, lo2):
    R, p = 6371.0, math.pi / 180.0
    a = (math.sin((la2 - la1) * p / 2) ** 2 + math.cos(la1 * p) *
         math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


# ---- 1. master district data -------------------------------------------------
with open(os.path.join(PROC, "master_261district_nutrition_FINAL.csv"),
          encoding="utf-8") as fh:
    master_text = fh.read()
rows = list(csv.DictReader(master_text.splitlines()))

DISTRICTS = {}
for r in rows:
    d = {"region": r["region"], "lat": float(r["lat"]), "lon": float(r["lon"])}
    for o in OUTS:
        d[o] = {
            "pct": round(float(r[o + "_district_pct"]), 2),
            "lo": round(float(r[o + "_district_lo95"]), 2),
            "hi": round(float(r[o + "_district_hi95"]), 2),
            "exc": round(float(r[o + "_exceedance_prob"]), 3),
            "lisa": r[o + "_lisa_cluster"],
        }
    DISTRICTS[r["district"]] = d

# ---- 2. GeoJSON: simplify + polygon-to-district crosswalk --------------------
gj = json.load(open(os.path.join(RAW, "Ghana_New_260_District.geojson")))
ALIAS = {"NORTHERN EAST": "NORTH EAST"}


def simplify_ring(ring, dp=3):
    out = []
    last = None
    for x, y in ring:
        pt = [round(x, dp), round(y, dp)]
        if pt != last:
            out.append(pt)
            last = pt
    if len(out) >= 3 and out[0] != out[-1]:
        out.append(out[0])
    return out if len(out) >= 4 else None


feats, centroids, pregs = [], [], []
for i, ft in enumerate(gj["features"]):
    g = ft["geometry"]
    raw_rings = ([g["coordinates"][0]] if g["type"] == "Polygon"
                 else [poly[0] for poly in g["coordinates"]])
    rings = [s for s in (simplify_ring(r) for r in raw_rings) if s]
    if not rings:
        continue
    allpts = [pt for r in rings for pt in r]
    cen = [sum(p[1] for p in allpts) / len(allpts),
           sum(p[0] for p in allpts) / len(allpts)]
    rg = str(ft["properties"]["REGION"]).strip().upper()
    rg = ALIAS.get(rg, rg)
    centroids.append(cen)
    pregs.append(rg)
    feats.append({
        "type": "Feature", "id": len(feats),
        "properties": {"region": ft["properties"]["REGION"]},
        "geometry": {"type": "MultiPolygon",
                     "coordinates": [[r] for r in rings]},
    })

# crosswalk: each polygon -> nearest within-region district centroid
names = list(DISTRICTS.keys())
XWALK = []
for p in range(len(feats)):
    cand = [n for n in names if DISTRICTS[n]["region"].upper() == pregs[p]]
    if not cand:
        cand = names
    best = min(cand, key=lambda n: haversine(
        centroids[p][0], centroids[p][1],
        DISTRICTS[n]["lat"], DISTRICTS[n]["lon"]))
    XWALK.append(best)

GEOJSON = {"type": "FeatureCollection", "features": feats}

# ---- 3. SHAP determinants (Table 3) ------------------------------------------
SHAP = {o: [] for o in OUTS}
keymap = {"Stunting": "stunting", "Anaemia": "anaemia",
          "IYCF inadequacy": "iycf", "Diarrhoea": "diarrhoea"}
with open(os.path.join(TAB, "Table3_shap_determinants.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        o = keymap[r["Outcome"]]
        lo, hi = r["95% bootstrap CI"].split("-")
        SHAP[o].append({"name": r["Determinant"],
                        "val": float(r["Mean |SHAP|"]),
                        "lo": float(lo), "hi": float(hi)})

# ---- 4. spatial / model statistics (canonical values) ------------------------
cv = {}
with open(os.path.join(PROC, "Canonical_Values_Nutrition.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        cv[r["value_name"]] = float(r["value"])
STATS = {}
for o in OUTS:
    STATS[o] = {
        "min": cv["district_" + o + "_min"], "max": cv["district_" + o + "_max"],
        "median": cv["district_" + o + "_median"],
        "moran": cv[o + "_moran_I"], "moran_p": cv[o + "_moran_p"],
        "phi": cv[o + "_phi_spatial"], "lisaHH": int(cv[o + "_lisa_HH"]),
        "hotspots": int(cv[o + "_hotspots_P95"]), "gwr": cv[o + "_gwr_dAICc"],
        "xgb": cv[o + "_xgb_LOROCV_R2"], "aucpr": cv[o + "_hotspot_AUCPR"],
    }

# ---- 5. region outcomes (16 regions) -----------------------------------------
REGIONS = []
with open(os.path.join(PROC, "region_outcomes_2022.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        REGIONS.append({"region": r["region"],
                        "stunting": float(r["stunting_pct"]),
                        "anaemia": float(r["anaemia_pct"]),
                        "iycf": float(r["iycf_inadeq_pct"]),
                        "diarrhoea": float(r["diarrhoea_pct"])})

# ---- 6. quadruple-burden hotspots (Table 5) ----------------------------------
HOTSPOTS = []
with open(os.path.join(TAB, "Table5_quadruple_burden_hotspots.csv"),
          encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        HOTSPOTS.append({"district": r["District"], "region": r["Region"],
                         "stunting": float(r["Stunting %"]),
                         "anaemia": float(r["Anaemia %"]),
                         "iycf": float(r["IYCF inadeq %"]),
                         "diarrhoea": float(r["Diarrhoea %"])})

PAYLOAD = {
    "geojson": GEOJSON, "xwalk": XWALK, "districts": DISTRICTS,
    "shap": SHAP, "stats": STATS, "regions": REGIONS, "hotspots": HOTSPOTS,
}
data_js = json.dumps(PAYLOAD, separators=(",", ":"))
csv_js = json.dumps(master_text)

print("polygons:", len(feats), "| districts:", len(DISTRICTS),
      "| payload:", round(len(data_js) / 1024 / 1024, 2), "MB")

# ============================ HTML ===========================================
HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ghana Child-Nutrition District Surveillance Dashboard</title>
<script>__PLOTLYJS__</script>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif; background:#eef2f4;
  color:#1a1a1a; }
.wrap { max-width:1500px; margin:0 auto; padding:18px; }
header { background:#1d4e6f; color:#fff; padding:20px 26px; border-radius:8px;
  border-bottom:6px solid #c25e00; }
header h1 { font-size:23px; font-weight:700; line-height:1.25; }
header .sub { font-size:14px; color:#cfe2ec; margin-top:6px; }
header .vintage { font-size:12px; color:#9fc0d2; margin-top:8px; }
.kpis { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin:16px 0; }
.kpi { background:#fff; border-radius:7px; padding:14px 15px; border-left:5px solid #c25e00;
  box-shadow:0 1px 4px rgba(0,0,0,.07); }
.kpi .n { font-size:25px; font-weight:700; color:#1d4e6f; }
.kpi .l { font-size:11.6px; color:#52616b; margin-top:5px; line-height:1.3; }
.controls { background:#fff; border-radius:7px; padding:13px 16px; margin-bottom:16px;
  display:flex; gap:26px; flex-wrap:wrap; align-items:center;
  box-shadow:0 1px 4px rgba(0,0,0,.07); }
.cgroup { display:flex; gap:8px; align-items:center; }
.cgroup .lab { font-size:12px; font-weight:700; color:#1d4e6f;
  text-transform:uppercase; letter-spacing:.5px; margin-right:3px; }
.btn { font-size:13px; padding:7px 13px; border:1.5px solid #c2ced4; background:#f5f8f9;
  color:#33424b; border-radius:5px; cursor:pointer; font-family:inherit; }
.btn:hover { border-color:#2e8b8b; }
.btn.on { background:#1d4e6f; color:#fff; border-color:#1d4e6f; }
.panel { background:#fff; border-radius:7px; padding:16px 18px; margin-bottom:16px;
  box-shadow:0 1px 4px rgba(0,0,0,.07); }
.panel h2 { font-size:15px; color:#1d4e6f; margin-bottom:4px;
  border-bottom:2px solid #2e8b8b; padding-bottom:5px; }
.panel .note { font-size:11.5px; color:#6b7780; margin:5px 0 9px; }
.grid2 { display:grid; grid-template-columns:1.6fr 1fr; gap:16px; }
.statbox { display:grid; grid-template-columns:1fr 1fr; gap:8px 14px; }
.stat { border-bottom:1px solid #e6ecef; padding:6px 2px; }
.stat .sv { font-size:18px; font-weight:700; color:#1d4e6f; }
.stat .sl { font-size:10.8px; color:#6b7780; line-height:1.25; }
#map { width:100%; height:560px; }
#shap { width:100%; height:300px; }
#region { width:100%; height:340px; }
.lisaLegend { display:none; gap:14px; flex-wrap:wrap; margin-top:8px; font-size:12px; }
.lisaLegend span { display:inline-flex; align-items:center; gap:5px; }
.sw { width:15px; height:15px; border-radius:3px; display:inline-block;
  border:1px solid #ccc; }
table { width:100%; border-collapse:collapse; font-size:12.6px; }
th,td { padding:7px 9px; text-align:left; border-bottom:1px solid #e6ecef; }
th { background:#1d4e6f; color:#fff; font-size:11.5px; text-transform:uppercase;
  letter-spacing:.4px; position:sticky; top:0; }
tbody tr:nth-child(even) { background:#f5f8f9; }
td.num { text-align:right; font-variant-numeric:tabular-nums; }
.tablewrap { max-height:430px; overflow:auto; border:1px solid #e6ecef; border-radius:5px; }
footer { background:#1d4e6f; color:#d7e4ec; border-radius:8px; padding:18px 24px;
  font-size:11.8px; line-height:1.6; }
footer h3 { color:#ffd9b0; font-size:12.5px; text-transform:uppercase;
  letter-spacing:.6px; margin-bottom:6px; }
footer b { color:#fff; }
.dlbtn { display:inline-block; margin-top:10px; background:#c25e00; color:#fff;
  padding:9px 16px; border-radius:5px; font-size:12.5px; border:none; cursor:pointer;
  font-family:inherit; font-weight:700; }
@media (max-width:980px){ .kpis{grid-template-columns:repeat(2,1fr);}
  .grid2{grid-template-columns:1fr;} }
</style></head><body>
<div class="wrap">

<header>
  <h1>Childhood stunting, anaemia, infant-feeding inadequacy and diarrhoea
  &mdash; district surveillance dashboard, 261 districts of Ghana</h1>
  <div class="sub">Modelled small-area (BYM2) posterior estimates from the 2022
  Ghana Demographic and Health Survey and the 2021 Population &amp; Housing
  Census. District values are model-based posteriors &mdash; read with their
  95&#37; credible intervals.</div>
  <div class="vintage">Data vintage: GDHS 2022 &middot; PHC 2021 &nbsp;|&nbsp;
  Dashboard build: __BUILD__ &nbsp;|&nbsp; Reporting: STROBE, RECORD-Spatial,
  TRIPOD+AI</div>
</header>

<div class="kpis">
  <div class="kpi"><div class="n">261</div>
    <div class="l">districts with modelled posterior estimates</div></div>
  <div class="kpi"><div class="n">17</div>
    <div class="l">quadruple-burden hotspot districts (all four outcomes)</div></div>
  <div class="kpi"><div class="n">0.82&ndash;0.96</div>
    <div class="l">Global Moran's I range (all p&nbsp;=&nbsp;0.002)</div></div>
  <div class="kpi"><div class="n">30.5&ndash;74.4&#37;</div>
    <div class="l">district anaemia posterior range</div></div>
  <div class="kpi"><div class="n">0.78</div>
    <div class="l">stunting &times; anaemia bivariate Moran's I</div></div>
</div>

<div class="controls">
  <div class="cgroup"><span class="lab">Outcome</span>
    <button class="btn out on" data-o="stunting">Stunting</button>
    <button class="btn out" data-o="anaemia">Anaemia</button>
    <button class="btn out" data-o="iycf">IYCF inadequacy</button>
    <button class="btn out" data-o="diarrhoea">Diarrhoea</button>
  </div>
  <div class="cgroup"><span class="lab">Map layer</span>
    <button class="btn met on" data-m="pct">Posterior prevalence</button>
    <button class="btn met" data-m="exc">Exceedance probability</button>
    <button class="btn met" data-m="lisa">LISA cluster</button>
  </div>
</div>

<div class="panel">
  <h2 id="mapTitle">Modelled district posterior prevalence</h2>
  <div class="note" id="mapNote"></div>
  <div id="map"></div>
  <div class="lisaLegend" id="lisaLegend">
    <span><i class="sw" style="background:#c1292e"></i>High-High</span>
    <span><i class="sw" style="background:#235789"></i>Low-Low</span>
    <span><i class="sw" style="background:#f1a208"></i>High-Low</span>
    <span><i class="sw" style="background:#7ec4cf"></i>Low-High</span>
    <span><i class="sw" style="background:#e8e8e8"></i>Not significant</span>
  </div>
</div>

<div class="grid2">
  <div class="panel">
    <h2 id="shapTitle">SHAP determinant importance</h2>
    <div class="note">Mean absolute SHAP value (XGBoost native TreeSHAP) with
    95&#37; bootstrap interval. Determinant importance describes the modelled
    burden surface; it is not a causal estimate.</div>
    <div id="shap"></div>
  </div>
  <div class="panel">
    <h2 id="statTitle">Spatial &amp; model statistics</h2>
    <div class="note">For the selected outcome.</div>
    <div class="statbox" id="statbox"></div>
  </div>
</div>

<div class="panel">
  <h2 id="regionTitle">Region direct estimates (16 GDHS regions)</h2>
  <div class="note">2022 GDHS region direct estimates &mdash; the effective
  inferential unit. District posteriors are benchmarked to these values.</div>
  <div id="region"></div>
</div>

<div class="panel">
  <h2>Quadruple-burden hotspot districts</h2>
  <div class="note">Districts with posterior exceedance probability &gt;&nbsp;0.95
  for all four outcomes simultaneously (17 districts; modelled posterior
  estimates).</div>
  <div class="tablewrap">
    <table><thead><tr>
      <th>District</th><th>Region</th><th>Stunting&nbsp;%</th>
      <th>Anaemia&nbsp;%</th><th>IYCF&nbsp;inadeq&nbsp;%</th>
      <th>Diarrhoea&nbsp;%</th>
    </tr></thead><tbody id="hotbody"></tbody></table>
  </div>
</div>

<footer>
  <h3>Methodology &amp; data sources</h3>
  District posteriors were produced by benchmarked Besag&ndash;York&ndash;Molli&eacute;
  (BYM2) Bayesian small-area estimation over a queen-contiguity graph of the
  261 districts. The 16 regions of Ghana &mdash; the 16 GDHS regions &mdash;
  are the effective inferential unit and district means are benchmarked to
  the region direct estimates. Spatial structure:
  Global Moran's I, LISA and Getis-Ord Gi*. Determinants: XGBoost interpreted
  with SHAP under spatial leave-one-region-out cross-validation.
  <b>Every district value is a model-based posterior and should be read with its
  credible interval.</b><br>
  <b>Data:</b> Ghana Demographic and Health Survey 2022 (GSS, GHS, ICF); 2021
  Population &amp; Housing Census (Ghana Statistical Service). District polygons:
  260-district boundary file (Guan district shares its parent Oti polygon on the
  map; it is included in all data tables).<br>
  <b>Reporting:</b> STROBE &middot; RECORD-Spatial &middot; TRIPOD+AI. &nbsp;
  <b>Ethics:</b> public aggregate data, no personal identifiers, no new approval
  required.<br>
  <b>Author:</b> Valentine Golden Ghanem, Ghana COCOBOD Cocoa Clinic, Accra,
  Ghana &middot; ORCID 0009-0002-8332-0220 &middot; valentineghanem@gmail.com
  <br>
  <button class="dlbtn" id="dlbtn">Download master district dataset (CSV)</button>
</footer>

</div>
<script>
const D = __DATA__;
const MASTERCSV = __CSV__;
const LAB = {stunting:"Stunting",anaemia:"Anaemia",iycf:"IYCF inadequacy",
  diarrhoea:"Diarrhoea"};
const LISACODE = {ns:0,LL:1,LH:2,HL:3,HH:4};
const LISACOL = ["#e8e8e8","#235789","#7ec4cf","#f1a208","#c1292e"];
let curO = "stunting", curM = "pct";

function fmt(x,d){ return Number(x).toFixed(d===undefined?1:d); }

function mapZ(){
  const xs = D.xwalk, ds = D.districts;
  const z=[], txt=[];
  for(let i=0;i<xs.length;i++){
    const rec = ds[xs[i]][curO];
    if(curM==="pct"){ z.push(rec.pct);
      txt.push("<b>"+xs[i]+"</b><br>Posterior "+LAB[curO]+": "+fmt(rec.pct)+
        "%<br>95% CrI "+fmt(rec.lo)+"-"+fmt(rec.hi)+"%"); }
    else if(curM==="exc"){ z.push(rec.exc);
      txt.push("<b>"+xs[i]+"</b><br>P(exceeds national mean): "+fmt(rec.exc,3)); }
    else { z.push(LISACODE[rec.lisa]!==undefined?LISACODE[rec.lisa]:0);
      txt.push("<b>"+xs[i]+"</b><br>LISA cluster: "+rec.lisa); }
  }
  return {z,txt};
}

function drawMap(){
  const {z,txt} = mapZ();
  let colorscale, zmin, zmax, showbar, cbTitle;
  if(curM==="pct"){ colorscale="YlOrRd"; zmin=Math.min(...z); zmax=Math.max(...z);
    showbar=true; cbTitle=LAB[curO]+" %"; }
  else if(curM==="exc"){ colorscale=[[0,"#f7f0f7"],[0.5,"#d98fc0"],[1,"#7a0177"]];
    zmin=0; zmax=1; showbar=true; cbTitle="P(>mean)"; }
  else { colorscale=[];
    for(let k=0;k<5;k++){ colorscale.push([k/5,LISACOL[k]]);
      colorscale.push([(k+1)/5,LISACOL[k]]); }
    zmin=-0.5; zmax=4.5; showbar=false; cbTitle=""; }
  const trace = { type:"choropleth", geojson:D.geojson, featureidkey:"id",
    locations:[...Array(D.xwalk.length).keys()], z:z, text:txt,
    hoverinfo:"text", colorscale:colorscale, zmin:zmin, zmax:zmax,
    marker:{line:{color:"#ffffff",width:0.4}},
    showscale:showbar, colorbar:{title:{text:cbTitle,side:"right"},
      thickness:14,len:0.82} };
  const layout = { margin:{l:0,r:0,t:0,b:0},
    geo:{ fitbounds:"locations", visible:false, projection:{type:"mercator"},
      bgcolor:"rgba(0,0,0,0)" },
    paper_bgcolor:"rgba(0,0,0,0)" };
  Plotly.react("map",[trace],layout,{responsive:true,displayModeBar:false});
  document.getElementById("lisaLegend").style.display =
    (curM==="lisa")?"flex":"none";
  const titles = {pct:"Modelled district posterior prevalence",
    exc:"Posterior exceedance probability",
    lisa:"LISA spatial cluster classification"};
  const notes = {
    pct:"BYM2 posterior mean prevalence of "+LAB[curO].toLowerCase()+
      " by district. Hover for the 95% credible interval.",
    exc:"Posterior probability that a district exceeds the population-weighted "+
      "national mean. Districts above 0.95 are confirmed hotspots.",
    lisa:"Local Indicators of Spatial Association (p<0.05, FDR-controlled): "+
      "High-High and Low-Low cluster cores, High-Low and Low-High outliers."};
  document.getElementById("mapTitle").textContent =
    titles[curM]+" — "+LAB[curO];
  document.getElementById("mapNote").textContent = notes[curM];
}

function drawShap(){
  const s = D.shap[curO].slice().reverse();
  const names = s.map(d=>d.name), vals = s.map(d=>d.val);
  const emp = s.map(d=>d.hi-d.val), emm = s.map(d=>d.val-d.lo);
  const trace = { type:"bar", orientation:"h", x:vals, y:names,
    marker:{color:"#2e8b8b"},
    error_x:{type:"data",symmetric:false,array:emp,arrayminus:emm,
      color:"#1d4e6f",thickness:1.5,width:4},
    hovertemplate:"%{y}: %{x:.3f}<extra></extra>" };
  const layout = { margin:{l:130,r:18,t:8,b:34},
    xaxis:{title:{text:"Mean |SHAP| value",font:{size:11}},
      gridcolor:"#e6ecef",zeroline:false},
    yaxis:{automargin:true,tickfont:{size:11}},
    paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)" };
  Plotly.react("shap",[trace],layout,{responsive:true,displayModeBar:false});
  document.getElementById("shapTitle").textContent =
    "SHAP determinant importance — "+LAB[curO];
}

function drawRegion(){
  const rg = D.regions.slice().sort((a,b)=>a[curO]-b[curO]);
  const trace = { type:"bar", x:rg.map(r=>r.region), y:rg.map(r=>r[curO]),
    marker:{color:rg.map(r=>r[curO]),colorscale:"YlOrRd",
      line:{color:"#b9863a",width:0.5}},
    hovertemplate:"%{x}: %{y:.1f}%<extra></extra>" };
  const layout = { margin:{l:48,r:14,t:8,b:96},
    xaxis:{tickangle:-45,tickfont:{size:10.5}},
    yaxis:{title:{text:LAB[curO]+" (%)",font:{size:11}},gridcolor:"#e6ecef"},
    paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)" };
  Plotly.react("region",[trace],layout,{responsive:true,displayModeBar:false});
  document.getElementById("regionTitle").textContent =
    "Region direct estimates (16 GDHS regions) — "+LAB[curO];
}

function drawStats(){
  const s = D.stats[curO];
  const items = [
    [fmt(s.min)+"–"+fmt(s.max)+"%","District posterior range"],
    [fmt(s.median)+"%","District median"],
    [fmt(s.moran,3),"Global Moran's I (p="+fmt(s.moran_p,3)+")"],
    [fmt(s.phi,2),"Spatial fraction φ"],
    [s.lisaHH,"LISA High-High districts"],
    [s.hotspots,"Hotspots P(>mean)>0.95"],
    [fmt(s.gwr,0),"GWR ΔAICc over OLS"],
    [fmt(s.xgb,2),"XGBoost LOROCV R²"],
    [fmt(s.aucpr,3),"Hotspot classifier AUC-PR"],
  ];
  document.getElementById("statbox").innerHTML = items.map(it=>
    '<div class="stat"><div class="sv">'+it[0]+'</div>'+
    '<div class="sl">'+it[1]+'</div></div>').join("");
  document.getElementById("statTitle").textContent =
    "Spatial & model statistics — "+LAB[curO];
}

function buildHotspots(){
  const tb = document.getElementById("hotbody");
  tb.innerHTML = D.hotspots.map(h=>
    "<tr><td>"+h.district+"</td><td>"+h.region+"</td>"+
    '<td class="num">'+fmt(h.stunting)+'</td>'+
    '<td class="num">'+fmt(h.anaemia)+'</td>'+
    '<td class="num">'+fmt(h.iycf)+'</td>'+
    '<td class="num">'+fmt(h.diarrhoea)+'</td></tr>').join("");
}

function refresh(){ drawMap(); drawShap(); drawRegion(); drawStats(); }

document.querySelectorAll(".btn.out").forEach(b=>b.addEventListener("click",()=>{
  document.querySelectorAll(".btn.out").forEach(x=>x.classList.remove("on"));
  b.classList.add("on"); curO=b.dataset.o; refresh();
}));
document.querySelectorAll(".btn.met").forEach(b=>b.addEventListener("click",()=>{
  document.querySelectorAll(".btn.met").forEach(x=>x.classList.remove("on"));
  b.classList.add("on"); curM=b.dataset.m; drawMap();
}));
document.getElementById("dlbtn").addEventListener("click",()=>{
  const blob = new Blob([MASTERCSV],{type:"text/csv"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "master_261district_nutrition_FINAL.csv";
  document.body.appendChild(a); a.click(); a.remove();
});

buildHotspots();
refresh();
</script>
</body></html>
"""

import datetime

# Embed Plotly.js inline so the dashboard works offline / on first clone.
PLOTLY_PATHS = [
    os.environ.get("PLOTLY_JS"),
    "/tmp/pylibs/plotly/package_data/plotly.min.js",
    os.path.join(os.path.dirname(__file__), "vendor", "plotly.min.js"),
]
plotly_js = None
for cand in PLOTLY_PATHS:
    if cand and os.path.exists(cand):
        plotly_js = open(cand, encoding="utf-8").read()
        break
if plotly_js is None:
    raise SystemExit("plotly.min.js not found; install python `plotly` or "
                     "drop the file at scripts/vendor/plotly.min.js")

HTML = (HTML.replace("__PLOTLYJS__", plotly_js)
        .replace("__DATA__", data_js).replace("__CSV__", csv_js)
        .replace("__BUILD__", datetime.date.today().isoformat()))
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(HTML)
print("Dashboard written:", OUT, round(len(HTML) / 1024 / 1024, 2), "MB")
