#!/usr/bin/env python3
"""build_poster.py - A0 landscape conference poster (self-contained HTML).

Project 10: Ghana child-nutrition small-area estimation.
Four-column A0-landscape layout (1900x1344 px, ratio 1.414).
Embeds Figures 1, 4 and 5 as base64 PNG and an ORCID QR code as inline SVG.
Output: poster/Nutrition_Poster.html
"""
import base64
import io
import os

import qrcode
import qrcode.image.svg

BASE = os.environ.get("PROJ_BASE", os.path.join(os.path.dirname(__file__), ".."))
FIG = os.path.join(BASE, "figures")
OUTDIR = os.path.join(BASE, "poster")
os.makedirs(OUTDIR, exist_ok=True)
OUT = os.path.join(OUTDIR, "Nutrition_Poster.html")


def b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


fig1 = b64(os.path.join(FIG, "fig1_choropleth_prevalence.png"))
fig4 = b64(os.path.join(FIG, "fig4_bivariate_lisa.png"))
fig5 = b64(os.path.join(FIG, "fig5_shap_importance.png"))

# ---- ORCID QR code -----------------------------------------------------------
qr = qrcode.QRCode(box_size=10, border=1,
                   error_correction=qrcode.constants.ERROR_CORRECT_M)
qr.add_data("https://orcid.org/0009-0002-8332-0220")
qr.make(fit=True)
_buf = io.BytesIO()
qr.make_image(image_factory=qrcode.image.svg.SvgPathImage).save(_buf)
qr_svg = _buf.getvalue().decode("utf-8")
qr_svg = qr_svg.split("?>", 1)[-1].strip()  # drop XML declaration

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #54606b; font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; }
.poster {
  width: 1900px; height: 1344px; margin: 24px auto; background: #ffffff;
  display: flex; flex-direction: column; overflow: hidden;
  box-shadow: 0 6px 30px rgba(0,0,0,0.4);
}
header {
  background: #1d4e6f; color: #ffffff; padding: 22px 40px 18px 40px;
  border-bottom: 7px solid #c25e00;
}
header h1 { font-size: 33px; line-height: 1.16; font-weight: 700; }
header .sub { font-size: 20px; color: #cfe2ec; margin-top: 7px; font-weight: 400; }
header .auth { font-size: 17px; color: #ffffff; margin-top: 9px; }
header .auth b { color: #ffd9b0; }
.body { flex: 1; display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 0; }
.col { padding: 16px 22px; min-width: 0; }
.col + .col { border-left: 2px solid #e3e9ec; }
h2 { font-size: 22px; color: #1d4e6f; font-weight: 700; margin: 2px 0 8px 0;
  padding-bottom: 4px; border-bottom: 3px solid #2e8b8b; }
h2:not(:first-child) { margin-top: 15px; }
p, li { font-size: 14.6px; line-height: 1.44; color: #1a1a1a; text-align: justify; }
p { margin-bottom: 7px; }
ul { margin: 2px 0 6px 18px; }
li { margin-bottom: 4px; }
.kpis { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 3px 0 10px 0; }
.kpi { background: #f0f4f6; border-left: 5px solid #c25e00; padding: 8px 10px; }
.kpi .n { font-size: 23px; font-weight: 700; color: #1d4e6f; line-height: 1.05; }
.kpi .l { font-size: 11.5px; color: #41525c; margin-top: 4px; line-height: 1.26; }
figure { margin: 7px 0 4px 0; text-align: center; }
figure img { max-width: 100%; height: auto; border: 1px solid #d4dde1; display: block;
  margin: 0 auto; }
img.f1 { max-height: 400px; }
img.f5 { max-height: 270px; }
img.f4 { max-height: 372px; }
figcaption { font-size: 12px; font-style: italic; color: #41525c;
  margin-top: 5px; line-height: 1.32; text-align: left; }
.box { background: #f0f4f6; border: 1px solid #d4dde1; padding: 10px 12px;
  margin: 7px 0; }
.box h3 { font-size: 14.5px; color: #1d4e6f; margin-bottom: 5px; }
.box .hs { font-size: 12.6px; line-height: 1.48; color: #1a1a1a; }
.box .hs b { color: #1d4e6f; }
.policy li::marker { color: #c25e00; }
.concl { background: #1d4e6f; color: #ffffff; padding: 12px 14px; margin-top: 8px; }
.concl h2 { color: #ffffff; border-bottom-color: #c25e00; margin-top: 0; }
.concl p { color: #eef4f7; font-size: 14.4px; margin-bottom: 0; }
footer {
  background: #1d4e6f; color: #ffffff; padding: 13px 40px;
  display: flex; gap: 26px; align-items: flex-start;
  border-top: 7px solid #c25e00;
}
footer .refs { flex: 1; }
footer h4 { font-size: 13.5px; color: #ffd9b0; margin-bottom: 5px;
  text-transform: uppercase; letter-spacing: .6px; }
footer ol { margin-left: 17px; }
footer ol li { font-size: 11px; color: #dce7ee; line-height: 1.38; margin-bottom: 2px;
  text-align: left; }
footer .meta { font-size: 11.4px; color: #cfe2ec; line-height: 1.5; max-width: 320px; }
footer .meta b { color: #ffffff; }
.qr { text-align: center; }
.qr svg { width: 108px; height: 108px; background: #ffffff; padding: 6px;
  border-radius: 3px; }
.qr div { font-size: 10.4px; color: #cfe2ec; margin-top: 4px; max-width: 124px; }
@page { size: A0 landscape; margin: 0; }
"""

REFS = [
 "Takele BA, Gezie LD, Alamneh TS. Pooled prevalence of stunting and associated "
 "factors among children aged 6-59 months in Sub-Saharan Africa: a Bayesian "
 "multilevel approach. PLoS One. 2022;17(10):e0275889.",
 "Tesema GA, Tessema ZT, Tamirat KS, Teshale AB. Prevalence and determinants of "
 "severity levels of anemia among children aged 6-59 months in sub-Saharan "
 "Africa. PLoS One. 2021;16(4):e0249978.",
 "Ghana Statistical Service, Ghana Health Service, ICF. Ghana Demographic and "
 "Health Survey 2022. Accra and Rockville (MD): GSS and ICF; 2024. Report FR387.",
 "Aheto JMK, Dagne GA. Geostatistical analysis, web-based mapping and "
 "environmental determinants of under-5 stunting: 2014 Ghana DHS. Lancet Planet "
 "Health. 2021;5(6):e347-e355.",
 "Mercer LD, Wakefield J, Pantazis A, et al. Space-time smoothing of complex "
 "survey data: small area estimation for child mortality. Ann Appl Stat. "
 "2015;9(4):1889-1905.",
 "Riebler A, Sorbye SH, Simpson D, Rue H. An intuitive Bayesian spatial model "
 "for disease mapping that accounts for scaling. Stat Methods Med Res. "
 "2016;25(4):1145-1165.",
]
refs_html = "".join(f"<li>{r}</li>" for r in REFS)

HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Ghana Child-Nutrition Small-Area Estimation - Conference Poster</title>
<style>__CSS__</style></head><body>
<div class="poster">

<header>
  <h1>Small-area estimation of childhood stunting, anaemia, infant-feeding
  inadequacy and diarrhoea across the 261 districts of Ghana</h1>
  <div class="sub">A Bayesian spatial and machine-learning analysis of the
  2022 Demographic and Health Survey</div>
  <div class="auth"><b>Valentine Golden Ghanem</b> &nbsp;&middot;&nbsp;
  Ghana COCOBOD Cocoa Clinic, Accra, Ghana &nbsp;&middot;&nbsp;
  ORCID 0009-0002-8332-0220 &nbsp;&middot;&nbsp; valentineghanem@gmail.com</div>
</header>

<div class="body">

  <div class="col">
    <h2>Background</h2>
    <p>Across sub-Saharan Africa an estimated 35&#37; of children aged 6&ndash;59
    months are stunted and 64&#37; are anaemic. Ghana's national stunting fell
    from 33&#37; in 1993 to 17&#37; in 2022 &mdash; but the national mean hides a
    near three-fold regional gradient, from 10&#37; in Eastern Region to 30&#37;
    in the north.</p>
    <p>Ghana plans and budgets child-nutrition programmes at the
    <b>district</b> level, yet the Demographic and Health Survey is powered only
    to the 16 <b>regions</b>. District managers therefore have no
    directly-measured estimates to act on. No previous study has produced joint,
    multi-outcome small-area estimates for Ghana's 261 districts.</p>

    <h2>Methods</h2>
    <p><b>Design.</b> Ecological, cross-sectional, spatially-resolved analysis
    of all 261 metropolitan, municipal and district assemblies (MMDAs);
    reference year 2022.</p>
    <ul>
      <li><b>Outcomes</b> &mdash; 2022 GDHS region direct estimates (16 regions =
      effective inferential unit): stunting, anaemia (6&ndash;59 m), infant and
      young child feeding (IYCF) inadequacy, diarrhoea.</li>
      <li><b>Covariates</b> &mdash; 2021 Population &amp; Housing Census, at
      district level (poverty, illiteracy, NHIS cover, under-15 share,
      urbanicity, water and sanitation).</li>
      <li><b>Small-area estimation</b> &mdash; benchmarked Besag&ndash;York&ndash;
      Molli&eacute; (BYM2) Bayesian model over a queen-contiguity graph of the
      261 districts; district means benchmarked to region direct estimates.</li>
      <li><b>Spatial analysis</b> &mdash; Global Moran's I, Local Indicators of
      Spatial Association (LISA), bivariate LISA, Getis-Ord Gi*.</li>
      <li><b>Non-stationarity</b> &mdash; geographically weighted regression
      (GWR) with an adaptive bi-square kernel.</li>
      <li><b>Determinants</b> &mdash; Random Forest and XGBoost interpreted with
      SHAP; spatial leave-one-region-out cross-validation (16 folds).</li>
      <li><b>Reporting</b> &mdash; STROBE, RECORD-Spatial, TRIPOD+AI.</li>
    </ul>
  </div>

  <div class="col">
    <h2>Results</h2>
    <div class="kpis">
      <div class="kpi"><div class="n">17</div>
        <div class="l">districts in the quadruple-burden core &mdash; hotspots
        for all four outcomes at once</div></div>
      <div class="kpi"><div class="n">0.82&ndash;0.96</div>
        <div class="l">Global Moran's I across the four surfaces (all
        p&nbsp;=&nbsp;0.002)</div></div>
      <div class="kpi"><div class="n">0.78</div>
        <div class="l">stunting &times; anaemia bivariate Moran's I; 49 joint
        High-High districts</div></div>
      <div class="kpi"><div class="n">225&ndash;368</div>
        <div class="l">GWR &Delta;AICc over OLS &mdash; effects are spatially
        non-stationary</div></div>
    </div>
    <p>Modelled district posterior prevalence spanned <b>7.5&ndash;34.6&#37;</b>
    (stunting), <b>30.5&ndash;74.4&#37;</b> (anaemia), <b>58.5&ndash;91.8&#37;</b>
    (IYCF inadequacy) and <b>4.2&ndash;34.1&#37;</b> (diarrhoea). All four
    surfaces were strongly spatially clustered and co-located.</p>
    <figure>
      <img class="f1" src="data:image/png;base64,__FIG1__" alt="Choropleth of
      modelled district posterior prevalence for the four outcomes">
      <figcaption>Figure&nbsp;1. Modelled district posterior prevalence (BYM2
      small-area estimation), 261 districts of Ghana, 2022. Estimates are
      model-based.</figcaption>
    </figure>
  </div>

  <div class="col">
    <h2>Determinants</h2>
    <p>SHAP analysis identified <b>water and sanitation access, female
    illiteracy and poverty</b> as the dominant determinants of the district
    burden surface. Improved water and poverty incidence did not enter the
    small-area model, so their importance is independent of it.</p>
    <figure>
      <img class="f5" src="data:image/png;base64,__FIG5__" alt="SHAP determinant
      importance bar charts for the four outcomes">
      <figcaption>Figure&nbsp;2. SHAP determinant importance (XGBoost native
      TreeSHAP), top determinants per outcome, with 95&#37; bootstrap intervals.
      </figcaption>
    </figure>
    <p>The four outcomes co-located most strongly for stunting and anaemia
    (bivariate Moran's I&nbsp;=&nbsp;0.78; 49 joint High-High districts).</p>
    <figure>
      <img class="f4" src="data:image/png;base64,__FIG4__" alt="Bivariate LISA
      cluster map of stunting and anaemia">
      <figcaption>Figure&nbsp;3. Bivariate LISA &mdash; spatial co-clustering of
      childhood stunting and anaemia.</figcaption>
    </figure>
  </div>

  <div class="col">
    <h2>Quadruple-burden core</h2>
    <div class="box">
      <h3>Hotspot districts &mdash; all four outcomes</h3>
      <div class="hs">Posterior exceedance probability &gt;&nbsp;0.95 for
      <b>all four</b> outcomes (17 districts):<br>
      <b>Northern (14):</b> Gushegu Municipal, Karaga, Kpandai, Kumbungu, Mion,
      Nanton, Nanumba North Municipal, Nanumba South, Saboba, Savelugu
      Municipal, Tatale Sanguli, Tolon, Yendi Municipal, Zabzugu.<br>
      <b>Savannah (3):</b> Central Gonja, North East Gonja, North Gonja.</div>
    </div>
    <div class="concl">
      <h2>Conclusions</h2>
      <p>Childhood stunting, anaemia, infant-feeding inadequacy and diarrhoea in
      Ghana are not four separate problems but a single, spatially-concentrated
      syndemic. The modelled district burden surface converges on a compact
      17-district core in Northern and Savannah Regions. Determinant effects
      vary geographically, so a single national model is inadequate. District
      estimates are model-based posteriors, read with their credible intervals.
      </p>
    </div>
    <h2>Policy implications</h2>
    <ul class="policy">
      <li>A national-mean framing cannot allocate resources &mdash; a defined
      17-district core can.</li>
      <li>Concentrate integrated water, sanitation, maternal-education and
      nutrition investment on the quadruple-burden core.</li>
      <li>Calibrate intervention design regionally rather than as a uniform
      national package.</li>
      <li>The reproducible small-area-estimation pipeline is a transferable tool
      for district-targeted, equity-focused policy.</li>
    </ul>
  </div>

</div>

<footer>
  <div class="refs">
    <h4>Key references</h4>
    <ol>__REFS__</ol>
  </div>
  <div class="meta">
    <h4>Data &amp; reporting</h4>
    <b>Data:</b> Ghana DHS 2022 (GSS, GHS, ICF); 2021 Population &amp; Housing
    Census (GSS).<br>
    <b>Reporting:</b> STROBE &middot; RECORD-Spatial &middot; TRIPOD+AI.<br>
    <b>Ethics:</b> public aggregate data; no new approval. <b>Funding:</b> none.
    <b>Competing interests:</b> none.
  </div>
  <div class="qr">
    __QR__
    <div>Author ORCID &amp; analysis pipeline</div>
  </div>
</footer>

</div>
</body></html>
"""

HTML = (HTML.replace("__CSS__", CSS).replace("__FIG1__", fig1)
        .replace("__FIG4__", fig4).replace("__FIG5__", fig5)
        .replace("__REFS__", refs_html).replace("__QR__", qr_svg))

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(HTML)
print("Poster written:", OUT, round(len(HTML) / 1024 / 1024, 2), "MB")
