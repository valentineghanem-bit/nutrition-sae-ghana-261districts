// build_manuscript.js — Q1 STROBE manuscript, Project 10 (Ghana nutrition SAE)
// Vancouver references numbered strictly by order of first in-text appearance.
const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, Header, Footer, ExternalHyperlink } = require("docx");

const BASE = process.env.PROJ_BASE || path.join(__dirname, "..");
const FIG = path.join(BASE, "figures") + "/";
const TAB = path.join(BASE, "tables") + "/";
const OUTDIR = path.join(BASE, "manuscript");
const OUT = path.join(OUTDIR, "Nutrition_Manuscript.docx");
if (!fs.existsSync(OUTDIR)) fs.mkdirSync(OUTDIR, { recursive: true });

// ---------- helpers ----------------------------------------------------------
const P = (t, o = {}) => new Paragraph({
  spacing: { after: o.after == null ? 120 : o.after, line: o.line || 276 },
  alignment: o.align || AlignmentType.JUSTIFIED,
  pageBreakBefore: o.pb || false,
  children: [new TextRun({ text: t, italics: o.it || false, bold: o.b || false,
    size: o.size || 22 })],
});
// paragraph from mixed runs
const PR = (runs, o = {}) => new Paragraph({
  spacing: { after: o.after == null ? 120 : o.after, line: 276 },
  alignment: o.align || AlignmentType.JUSTIFIED,
  children: runs,
});
const R = (t, o = {}) => new TextRun({ text: t, bold: o.b || false,
  italics: o.it || false, size: o.size || 22, superScript: o.sup || false });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1,
  spacing: { before: 280, after: 140 }, children: [new TextRun({ text: t })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2,
  spacing: { before: 200, after: 100 }, children: [new TextRun({ text: t })] });
const CAP = (t) => new Paragraph({ spacing: { before: 80, after: 200 },
  children: [new TextRun({ text: t, italics: true, size: 19 })] });

function img(file, w, h, title) {
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(FIG + file),
      transformation: { width: w, height: h },
      altText: { title: title, description: title, name: title } })] });
}

// quote-aware CSV line parser
function parseCSVLine(line) {
  const out = []; let cur = ""; let inQ = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (c === '"') { inQ = !inQ; }
    else if (c === "," && !inQ) { out.push(cur); cur = ""; }
    else { cur += c; }
  }
  out.push(cur);
  return out;
}

// build a docx table from a CSV file
function csvTable(p, widths) {
  const rows = fs.readFileSync(p, "utf8").trim().split("\n").map(parseCSVLine);
  const total = widths.reduce((a, b) => a + b, 0);
  const bd = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
  const borders = { top: bd, bottom: bd, left: bd, right: bd };
  const trs = rows.map((cells, ri) => new TableRow({
    children: cells.map((c, ci) => new TableCell({
      borders,
      width: { size: widths[ci], type: WidthType.DXA },
      shading: ri === 0 ? { fill: "1d4e6f", type: ShadingType.CLEAR } : undefined,
      margins: { top: 50, bottom: 50, left: 90, right: 90 },
      children: [new Paragraph({ spacing: { after: 0 },
        children: [new TextRun({ text: c, bold: ri === 0, size: 17,
          color: ri === 0 ? "FFFFFF" : "000000" })] })],
    })),
  }));
  return new Table({ width: { size: total, type: WidthType.DXA },
    columnWidths: widths, rows: trs });
}

// ---------- references (Vancouver, DOI-verified) -----------------------------
// Ordered strictly by order of first in-text citation.
const REFS = [
 "Takele BA, Gezie LD, Alamneh TS. Pooled prevalence of stunting and associated factors among children aged 6-59 months in Sub-Saharan Africa countries: a Bayesian multilevel approach. PLoS One. 2022;17(10):e0275889. doi:10.1371/journal.pone.0275889",
 "Tesema GA, Tessema ZT, Tamirat KS, Teshale AB. Prevalence and determinants of severity levels of anemia among children aged 6-59 months in sub-Saharan Africa: a multilevel ordinal logistic regression analysis. PLoS One. 2021;16(4):e0249978. doi:10.1371/journal.pone.0249978",
 "Ghana Statistical Service, Ghana Health Service, ICF. Ghana Demographic and Health Survey 2022. Accra and Rockville (MD): GSS and ICF; 2024. Report FR387. Available from: https://dhsprogram.com/pubs/pdf/FR387/FR387.pdf",
 "Asgedom YS, Habte A, Woldegeorgis BZ, et al. The prevalence of anemia and the factors associated with its severity among children aged 6-59 months in Ghana: a multi-level ordinal logistic regression. PLoS One. 2024;19(12):e0315232. doi:10.1371/journal.pone.0315232",
 "Aheto JMK, Dagne GA. Geostatistical analysis, web-based mapping, and environmental determinants of under-5 stunting: evidence from the 2014 Ghana Demographic and Health Survey. Lancet Planet Health. 2021;5(6):e347-e355. doi:10.1016/S2542-5196(21)00080-2",
 "Johnson FA. Spatiotemporal clustering and correlates of childhood stunting in Ghana: analysis of the fixed and nonlinear associative effects of socio-demographic and socio-ecological factors. PLoS One. 2022;17(2):e0263726. doi:10.1371/journal.pone.0263726",
 "Akanbonga S, Hasan T, Chowdhury U, et al. Infant and young child feeding practices and associated socioeconomic and demographic factors among children aged 6-23 months in Ghana: findings from Ghana Multiple Indicator Cluster Survey, 2017-2018. PLoS One. 2023;18(6):e0286055. doi:10.1371/journal.pone.0286055",
 "Mercer LD, Wakefield J, Pantazis A, Lutambi AM, Masanja H, Clark S. Space-time smoothing of complex survey data: small area estimation for child mortality. Ann Appl Stat. 2015;9(4):1889-1905. doi:10.1214/15-AOAS872",
 "Ghana Statistical Service. 2021 Population and Housing Census. Accra: GSS; 2021. Available from: https://census2021.statsghana.gov.gh/",
 "Riebler A, Sorbye SH, Simpson D, Rue H. An intuitive Bayesian spatial model for disease mapping that accounts for scaling. Stat Methods Med Res. 2016;25(4):1145-1165. doi:10.1177/0962280216660421",
 "Richardson S, Thomson A, Best N, Elliott P. Interpreting posterior relative risk estimates in disease-mapping studies. Environ Health Perspect. 2004;112(9):1016-1025. doi:10.1289/ehp.6740",
 "Anku EK, Duah HO. Predicting and identifying factors associated with undernutrition among children under five years in Ghana using machine learning algorithms. PLoS One. 2024;19(2):e0296625. doi:10.1371/journal.pone.0296625",
 "Li Z. Extracting spatial effects from machine learning model using local interpretation method: an example of SHAP and XGBoost. Comput Environ Urban Syst. 2022;96:101845. doi:10.1016/j.compenvurbsys.2022.101845",
 "Aheto JMK. Correlates and spatial distribution of the co-occurrence of childhood anaemia and stunting in Ghana. SSM Popul Health. 2020;12:100683. doi:10.1016/j.ssmph.2020.100683",
 "Khan J, Mohanty SK. Spatial heterogeneity and correlates of child malnutrition in districts of India. BMC Public Health. 2018;18:1027. doi:10.1186/s12889-018-5873-z",
 "Muche A, Melaku MS, Amsalu ET, Adane M. Using geographically weighted regression analysis to cluster under-nutrition and its predictors among under-five children in Ethiopia. PLoS One. 2021;16(5):e0248156. doi:10.1371/journal.pone.0248156",
 "Seboka BT, Hailegebreal S, Mamo TT, et al. Spatial trends and projections of chronic malnutrition among children under 5 years of age in Ethiopia from 2011 to 2019: a geographically weighted regression analysis. J Health Popul Nutr. 2022;41:28. doi:10.1186/s41043-022-00309-7",
 "Seiler J, Harttgen K, Kneib T, Lang S. High-resolution spatial prediction of anemia risk among children aged 6 to 59 months in low- and middle-income countries. Commun Med. 2025;5:76. doi:10.1038/s43856-025-00789-8",
 "Addae HY, Saaka M, Kwarteng A, et al. Low birth weight, household socio-economic status, water and sanitation are associated with stunting and wasting among children aged 6-23 months: results from a national survey in Ghana. PLoS One. 2024;19(1):e0297698. doi:10.1371/journal.pone.0297698",
 "Stevens GA, Paciorek CJ, Flores-Urrutia MC, et al. National, regional, and global estimates of anaemia by severity in women and children for 2000-19: a pooled analysis of population-representative data. Lancet Glob Health. 2022;10(5):e627-e639. doi:10.1016/S2214-109X(22)00084-5",
];
const refParas = REFS.map((r, i) => new Paragraph({
  spacing: { after: 80 }, alignment: AlignmentType.JUSTIFIED,
  children: [new TextRun({ text: (i + 1) + ". ", bold: true, size: 19 }),
             new TextRun({ text: r, size: 19 })] }));

// ====================== DOCUMENT BODY =======================================
const body = [];
const TITLE = "Small-area estimation of childhood stunting, anaemia, infant-feeding inadequacy and diarrhoea across the 261 districts of Ghana: a Bayesian spatial and machine-learning analysis of the 2022 Demographic and Health Survey";

body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
  children: [new TextRun({ text: TITLE, bold: true, size: 30 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
  children: [new TextRun({ text: "Valentine Golden Ghanem", size: 24, bold: true }),
             new TextRun({ text: " ¹", size: 16, superScript: true })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
  children: [new TextRun({ text: "¹ Ghana COCOBOD Cocoa Clinic, Accra, Ghana", size: 19, italics: true })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
  children: [new TextRun({ text: "Correspondence: valentineghanem@gmail.com  ·  ORCID 0009-0002-8332-0220", size: 19 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
  children: [new TextRun({ text: "Original research · Reporting: STROBE, RECORD-Spatial, TRIPOD+AI", size: 18, italics: true })] }));

// ---- ABSTRACT ----
body.push(H1("Abstract"));
body.push(PR([R("Background. ", { b: true }),
  R("Ghana’s national child-nutrition indicators conceal large regional inequity, but nutrition programmes are planned and budgeted at the district (metropolitan, municipal and district assembly) level, where directly-measured estimates are unavailable. This study produced modelled district-level estimates of four child-health outcomes and identified their determinants.")]));
body.push(PR([R("Methods. ", { b: true }),
  R("Outcome data were the 2022 Ghana Demographic and Health Survey (GDHS) direct estimates for the 16 administrative regions — the effective inferential unit; district-level (n = 261) covariates were the 2021 Population and Housing Census. District posteriors for stunting, anaemia (6–59 months), infant and young child feeding (IYCF) inadequacy and diarrhoea were obtained by benchmarked Besag–York–Mollié (BYM2) Bayesian small-area estimation. Spatial structure was assessed with Global Moran’s I, Local Indicators of Spatial Association (LISA), bivariate LISA and Getis-Ord Gi*; spatial non-stationarity with geographically weighted regression (GWR); and determinant importance with Random Forest and XGBoost models interpreted by SHAP, validated under spatial leave-one-region-out cross-validation. Reporting followed STROBE, RECORD-Spatial and TRIPOD+AI.")]));
body.push(PR([R("Results. ", { b: true }),
  R("Modelled district posterior prevalence spanned 7.5–34.6 % for stunting, 30.5–74.4 % for anaemia, 58.5–91.8 % for IYCF inadequacy and 4.2–34.1 % for diarrhoea. All four surfaces were strongly spatially clustered (Global Moran’s I 0.82–0.96; p = 0.002) and co-located (stunting×anaemia bivariate I = 0.78). Determinant effects were spatially non-stationary (GWR ΔAICc 225–368). SHAP identified water and sanitation access, female illiteracy and poverty as the dominant determinants. Seventeen districts — 14 in Northern and 3 in Savannah Region — were confirmed hotspots for all four outcomes simultaneously.")]));
body.push(PR([R("Conclusions. ", { b: true }),
  R("A reproducible small-area-estimation pipeline translates region-level survey data into a district burden surface that identifies a finite, geographically-concentrated set of districts for targeted child-nutrition investment. District estimates are model-based and should be read with their credible intervals.")], { after: 160 }));
body.push(PR([R("Keywords: ", { b: true }),
  R("small-area estimation; childhood stunting; anaemia; infant and young child feeding; spatial epidemiology; Bayesian disease mapping; machine learning; Ghana", { it: true })]));

// ---- 1 INTRODUCTION ----
body.push(H1("1. Introduction"));
body.push(P("Childhood undernutrition remains a defining public-health challenge across sub-Saharan Africa. A Bayesian multilevel synthesis of 35 sub-Saharan African countries placed the pooled prevalence of stunting among children aged 6–59 months at 35 % [1]. Stunting impairs linear growth, cognitive development and survival, and its effects extend across the life course."));
body.push(P("Childhood anaemia is equally pervasive. A pooled multilevel analysis of 32 sub-Saharan African countries estimated anaemia among children aged 6–59 months at 64 %, with low maternal education and household poverty among its strongest determinants [2]. Stunting and anaemia therefore tend to converge on the same disadvantaged populations."));
body.push(P("Ghana has made measurable progress against this burden: national stunting among children under five declined from 33 % in 1993 to 17 % in 2022, and wasting now stands at 6 %; yet that national figure conceals a near three-fold regional gradient, from 10 % stunting in Eastern Region to 30 % in Northern Region [3]. National means are therefore a poor guide to action, because they average over a population whose risk is far from uniform."));
body.push(P("The 2022 survey wave shows the same uneven geography for anaemia. A multilevel analysis of the 2022 GDHS estimated national anaemia among children aged 6–59 months at 49 % and located the highest odds in the three northern regions [4]. The north of the country thus carries a disproportionate share of both chronic undernutrition and anaemia."));
body.push(P("Earlier Ghanaian spatial work reached the same conclusion through different methods. Bayesian geostatistical modelling of the 2014 GDHS mapped predicted under-five stunting from 4 % to 45 % and located the highest risk in the Northern Region [5]."));
body.push(P("Spatiotemporal analysis across five consecutive survey rounds further confirmed that childhood stunting in Ghana is spatially clustered rather than randomly distributed, with the high-burden clusters concentrated in the north [6]."));
body.push(P("Inadequate infant and young child feeding underlies much of this burden. In the most recent national coverage data, only about a quarter of Ghanaian children aged 6–23 months met the minimum-dietary-diversity standard and barely one in ten met the minimum-acceptable-diet standard [7]. Poor feeding practices in the first two years of life are a proximate driver of both stunting and anaemia."));
body.push(P("Two evidence gaps motivate this study. First, Ghana plans and finances nutrition programmes at the district level, but the GDHS is powered only to the region; district-level estimates of child-nutrition outcomes are therefore unavailable, and a region-level analysis cannot direct district resource allocation. Small-area estimation — the established statistical bridge between survey-design resolution and the finer administrative units at which services are delivered — has been used to map child mortality and undernutrition elsewhere but has not been applied jointly, across multiple outcomes, to Ghana’s 261 districts [8]."));
body.push(P("Second, although Ghana has both spatial maps and machine-learning models of undernutrition, no study has combined Bayesian small-area estimation, spatial-autocorrelation analysis, geographically weighted regression and explainable machine learning within a single pipeline spanning stunting, anaemia, infant-feeding inadequacy and diarrhoea."));
body.push(P("This study addresses both gaps. Using the 2022 GDHS region-level direct estimates and 2021 Census district covariates, it produces modelled district-level posteriors for four child-health outcomes, characterises their spatial structure and co-clustering, quantifies the spatial non-stationarity of their determinants, and ranks those determinants with explainable machine learning — advancing the move from national-mean monitoring to district-targeted, equity-focused nutrition policy."));

// ---- 2 METHODS ----
body.push(H1("2. Methods"));
body.push(H2("2.1 Study design and setting"));
body.push(P("This was an ecological, cross-sectional, spatially-resolved analysis of all 261 metropolitan, municipal and district assemblies (MMDAs) of Ghana for the reference year 2022. The Republic of Ghana is administratively organised into 16 regions and, at the time of the 2021 Census, 261 districts. All inference is ecological and at the district level; no individual-level claim is made. Reporting follows the STROBE checklist for cross-sectional studies, the RECORD-Spatial extension for analyses of routinely-collected spatial data, and the TRIPOD+AI guidance for the machine-learning component."));

body.push(H2("2.2 Data sources and the resolution of outcomes and covariates"));
body.push(P("Outcome data were the 2022 GDHS direct estimates, which are published at the level of Ghana’s 16 regions; the 16 regions are therefore the effective inferential unit for the outcomes, and this constraint is carried explicitly through every result. Four outcomes were analysed: stunting (height-for-age below −2 SD, children under five); anaemia (haemoglobin below 11 g/dL, children 6–59 months); infant and young child feeding (IYCF) inadequacy, defined as the percentage of children aged 6–23 months not meeting all three core IYCF practices (minimum dietary diversity, minimum meal frequency and the breastfeeding indicator); and diarrhoea, the two-week prevalence among children born in the three years preceding the survey. Wasting was the originally-planned fourth outcome but is not published at region level for 2022; diarrhoea, which has complete 2022 region coverage, was substituted, and national wasting (6 %) is retained only as descriptive context. District-level covariates were drawn from the 2021 Population and Housing Census [9] for all 261 districts: poverty incidence and intensity, illiteracy rate, share of the population without National Health Insurance Scheme (NHIS) cover, employment rate, the under-15 population share, urbanicity (metropolitan, municipal or district) and total population. Household improved-water and improved-sanitation coverage and female literacy were available only at region level and entered as region-imputed covariates with an explicit imputation flag."));

body.push(H2("2.3 Bayesian small-area estimation"));
body.push(P("District-level posteriors were obtained by benchmarked small-area estimation, the recognised approach for producing estimates at administrative units finer than the survey design [8]. For each outcome, a ridge-regularised model related the logit of the 16 region direct estimates to population-weighted region-mean covariates; within-region district deviations of those covariates then generated a district linear predictor."));
body.push(P("A structured spatial term was added by Besag–York–Mollié (BYM2) smoothing over a queen-contiguity graph of the 261 districts, using the scaled reparameterisation that separates structured from unstructured variation [10]. District estimates were then benchmarked so that the population-weighted district mean within each region reproduces the region direct estimate exactly. The graph was extracted geometrically from the official 260-district boundary file; Guan district (Oti Region), absent from that file, was re-added by centroid attachment, and one edge was added to render the graph connected, as the intrinsic conditional autoregressive prior requires."));
body.push(P("Posterior means, 95 % credible intervals (CrI) and the spatial fraction φ were obtained from 2 000 posterior draws. The exceedance probability — the posterior probability that a district exceeds the population-weighted national mean — was computed for every district and outcome [11]; districts with exceedance probability above 0.95 were classified as confirmed hotspots."));
body.push(P("All district-level outcome values reported in this paper are model-based posterior estimates, not direct measurements. Within-region district variation is inferred from district covariates and the spatial prior; it is therefore most reliable at the scale of regional contrasts and least reliable for fine distinctions between neighbouring districts of the same region."));

body.push(H2("2.4 Spatial autocorrelation and geographically weighted regression"));
body.push(P("Spatial structure in the posterior surfaces was assessed with Global Moran’s I (queen contiguity, with a five-nearest-neighbour matrix as a sensitivity check), Local Indicators of Spatial Association (LISA) classifying districts as High-High, Low-Low, High-Low or Low-High, bivariate LISA for all six outcome pairs, and the Getis-Ord Gi* hotspot statistic. Inference used 999 conditional permutations with Benjamini–Hochberg control of the false-discovery rate. Spatial non-stationarity of the determinant effects was tested by geographically weighted regression (GWR) with an adaptive bi-square kernel and an AICc-optimal bandwidth, compared with ordinary least squares; coefficient non-stationarity was further assessed by a Brunsdon Monte-Carlo permutation test."));

body.push(H2("2.5 Machine learning and interpretability"));
body.push(P("Random Forest and XGBoost regression models related the ten district covariates to each outcome posterior; gradient-boosted trees have been shown to predict child undernutrition accurately in Ghana, which motivated their selection here [12]. Predictive performance was estimated by spatial leave-one-region-out cross-validation (16 folds), so that no district contributed to both the training and the test set of any fold, giving an honest measure of out-of-region generalisation. A binary hotspot classifier was trained with synthetic minority over-sampling applied inside each cross-validation fold and evaluated by the area under the precision–recall curve and the Brier score."));
body.push(P("Determinant importance was quantified by SHAP values computed with XGBoost’s native exact TreeSHAP algorithm and summarised as the mean absolute SHAP value with a 95 % bootstrap interval from 40 resamples; SHAP recovers covariate–outcome structure, including spatial effects, in a manner comparable to geographically weighted models [13]. The determinant analysis is interpreted as the structure of the modelled surface; because seven of the ten covariates also entered the small-area model, the importance of those seven is corroborative rather than an independent causal discovery, whereas improved water and poverty incidence — which did not enter the small-area model — are not subject to this circularity."));

body.push(H2("2.6 Software and ethics"));
body.push(P("Analyses used Python 3.10 (numpy, pandas, scikit-learn, xgboost); spatial weights, the small-area estimator and the autocorrelation statistics were implemented in pure numpy with a fixed random seed (42). The study used only publicly-released aggregate data containing no personal identifiers and required no new ethical approval; the underlying GDHS was approved by the Ghana Health Service Ethics Review Committee. The analytic code and the district master dataset are openly available (see Data availability)."));

// ---- 3 RESULTS ----
body.push(H1("3. Results"));
body.push(H2("3.1 District characteristics"));
body.push(P("Across the 261 districts the 2021 Census covariates showed wide variation: poverty incidence ranged from 6.3 % to 68.6 %, illiteracy from 5.4 % to 60.8 %, and the share of the population without NHIS cover from 5.2 % to 73.2 % (Table 1). The modelled district posterior prevalence spanned 7.5–34.6 % for stunting, 30.5–74.4 % for anaemia, 58.5–91.8 % for IYCF inadequacy and 4.2–34.1 % for diarrhoea, confirming a pronounced sub-national gradient in every outcome."));
body.push(P("Table 1. Characteristics of the 261 districts of Ghana, 2022 (district covariates from the 2021 Census; outcomes are modelled BYM2 posteriors).", { it: true, after: 60 }));
body.push(csvTable(TAB + "Table1_district_characteristics.csv", [3000, 2120, 2120, 2120]));
body.push(P("", { after: 120 }));
body.push(img("fig1_choropleth_prevalence.png", 470, 530, "Figure 1"));
body.push(CAP("Figure 1. Modelled district-level posterior prevalence (BYM2 small-area estimation) for the four outcomes, 261 districts of Ghana, 2022. Estimates are model-based; polygons use the 260-district boundary file with Guan sharing its parent Oti polygon."));

body.push(H2("3.2 Spatial clustering and co-clustering"));
body.push(P("All four posterior surfaces were strongly and significantly spatially autocorrelated, with Global Moran’s I of 0.94 for stunting, 0.96 for anaemia, 0.84 for IYCF inadequacy and 0.82 for diarrhoea (p = 0.002 for each; Table 2), and the result was concordant under the five-nearest-neighbour sensitivity matrix. LISA analysis identified coherent High-High cluster cores in the northern belt and Low-Low cores in the south, with no significant spatial outliers. Bivariate LISA showed that the four outcomes co-locate: the strongest pairing was stunting with anaemia (global bivariate I = 0.78; 49 districts in the joint High-High class), indicating that the same northern districts simultaneously carry chronic undernutrition, anaemia, inadequate infant feeding and diarrhoeal morbidity."));
body.push(P("Table 2. Global and local spatial autocorrelation of the four modelled outcome surfaces.", { it: true, after: 60 }));
body.push(csvTable(TAB + "Table2_spatial_autocorrelation.csv", [1560, 1300, 760, 920, 1620, 1600, 1600]));
body.push(P("", { after: 120 }));
body.push(img("fig3_lisa_clusters.png", 450, 600, "Figure 2"));
body.push(CAP("Figure 2. LISA cluster maps for the four outcomes (High-High, Low-Low, High-Low, Low-High; p < 0.05, false-discovery-rate controlled)."));
body.push(img("fig4_bivariate_lisa.png", 360, 410, "Figure 3"));
body.push(CAP("Figure 3. Bivariate LISA — spatial co-clustering of childhood stunting and anaemia."));

body.push(H2("3.3 Determinants and spatial non-stationarity"));
body.push(P("SHAP analysis of the XGBoost models identified water and sanitation access, female illiteracy and poverty as the dominant determinants of the district burden surface (Table 3). Improved water was the leading determinant of IYCF inadequacy and a leading determinant of stunting and diarrhoea; improved sanitation, illiteracy and poverty incidence led for anaemia. Because improved water and poverty incidence did not enter the small-area model, their importance is independent of the modelling procedure. Geographically weighted regression decisively outperformed ordinary least squares for every outcome (ΔAICc 225–368; Table 4), and the Brunsdon test confirmed that the effect of illiteracy was spatially non-stationary for all four outcomes — the strength of the determinant–outcome relationship therefore varies across Ghana, and a single national determinant model is inadequate."));
body.push(P("Table 3. SHAP determinant importance — top five determinants per outcome (XGBoost native exact TreeSHAP; importance is the bootstrap mean of mean |SHAP| with its 95 % bootstrap interval).", { it: true, after: 60 }));
body.push(csvTable(TAB + "Table3_shap_determinants.csv", [1450, 620, 1850, 1240, 1740, 1230, 1230]));
body.push(P("", { after: 120 }));
body.push(img("fig5_shap_importance.png", 480, 378, "Figure 4"));
body.push(CAP("Figure 4. SHAP determinant importance for the four outcomes, with 95 % bootstrap intervals."));
body.push(img("fig8_gwr_coefficients.png", 470, 470, "Figure 5"));
body.push(CAP("Figure 5. Geographically weighted regression — the spatially-varying local coefficient of female illiteracy for each outcome."));
body.push(P("Table 4. Small-area, geographically weighted regression and machine-learning model summary. Spatial leave-one-region-out cross-validation (LOROCV) R² is the honest out-of-region predictive performance.", { it: true, after: 60 }));
body.push(csvTable(TAB + "Table4_model_summary.csv", [1380, 1230, 1180, 1080, 1430, 1080, 1050, 930]));
body.push(P("", { after: 60 }));
body.push(P("Out-of-region predictive performance differed sharply by outcome: under spatial leave-one-region-out cross-validation the district covariates predicted anaemia well (XGBoost R² = 0.82) but did not generalise for IYCF inadequacy or diarrhoea (R² near zero), indicating that the covariates do not trivially reproduce the modelled surface."));

body.push(H2("3.4 The quadruple-burden core"));
body.push(P("Hotspot classification by posterior exceedance probability identified 31 districts for stunting, 60 for anaemia, 37 for IYCF inadequacy and 51 for diarrhoea (Table 4). All 31 stunting hotspots fell within the northern belt. Seventeen districts — 14 in Northern Region and 3 in Savannah Region — were confirmed hotspots for all four outcomes simultaneously (Table 5), constituting a compact, geographically-concentrated quadruple-burden core that offers a finite and actionable target set for child-nutrition investment."));
body.push(P("Table 5. Confirmed quadruple-burden hotspot districts — posterior exceedance probability above 0.95 for all four outcomes (modelled posterior estimates).", { it: true, after: 60 }));
body.push(csvTable(TAB + "Table5_quadruple_burden_hotspots.csv", [2400, 1560, 1350, 1350, 1350, 1350]));
body.push(P("", { after: 120 }));
body.push(img("fig2_exceedance_probability.png", 470, 530, "Figure 6"));
body.push(CAP("Figure 6. Posterior exceedance probability — the probability that a district exceeds the population-weighted national mean. Districts above 0.95 are confirmed hotspots."));

// ---- 4 DISCUSSION ----
body.push(H1("4. Discussion"));
body.push(P("This study translated region-level survey data into a modelled district-level burden surface for four child-health outcomes across all 261 districts of Ghana, and showed that childhood stunting, anaemia, infant-feeding inadequacy and diarrhoea are not four separable problems but a single, spatially-concentrated child-health syndemic. The four surfaces share a north–south gradient, co-cluster most strongly for stunting and anaemia, and converge on a 17-district quadruple-burden core in Northern and Savannah Regions. The determinant structure — dominated by water and sanitation access, female illiteracy and poverty — points to environmental, educational and economic deprivation rather than to health-insurance coverage, which did not rank among the leading determinants of any outcome."));
body.push(P("These findings are consistent with, and extend, the prior Ghanaian and regional evidence. Bayesian geostatistical mapping of the 2014 GDHS located the highest predicted childhood stunting in the Northern Region [5], the same region that anchors the quadruple-burden core identified here."));
body.push(P("The spatial co-occurrence of childhood anaemia and stunting in Ghana has been documented previously [14]; the present analysis shows that this joint burden extends as a coherent cluster across the northern districts and is the strongest of the six bivariate outcome pairings."));
body.push(P("Beyond Ghana, district-level analyses have repeatedly identified poverty, maternal education and sanitation as the dominant correlates of child malnutrition: a 640-district study in India found malnutrition strongly spatially structured and most closely tied to poverty and sanitation [15]. The determinant ranking obtained here places the same factors at the top for Ghana."));
body.push(P("Geographically weighted regression of child undernutrition in Ethiopia found that the influence of sanitation and parental education varied markedly from one area to another [16]. The contribution of the present study is to bring small-area estimation, spatial-autocorrelation analysis, geographically weighted regression and explainable machine learning into one pipeline applied jointly to four outcomes at the district scale at which Ghana delivers nutrition services."));
body.push(P("A geographically weighted analysis of chronic child malnutrition in Ethiopia across three survey rounds likewise showed that determinant effects shift across both space and time [17]. This reinforces the conclusion that a single national determinant model is inadequate and that intervention design must be calibrated regionally."));
body.push(P("High-resolution Bayesian prediction of childhood anaemia across 37 low- and middle-income countries has demonstrated that national averages conceal substantial within-country disparity [18]. The district anaemia surface produced here is the Ghana-specific expression of that disparity, spanning a modelled 30–74 % between districts."));
body.push(P("A national Ghanaian survey has shown household water and sanitation, together with socio-economic status and low birth weight, to be associated with child stunting [19]. That association is consistent with water and sanitation access emerging here as the leading determinant of the modelled district burden surface."));
body.push(P("Pooled global analysis estimates that around two in five children worldwide are anaemic, placing anaemia among the most widespread nutritional disorders [20]. The modelled district anaemia range identified here situates much of northern Ghana well above that global benchmark, underscoring the need for a geographically targeted response."));
body.push(P("Three interpretive cautions are integral to the findings. First, the global Moran’s I values are high partly because the BYM2 smoother propagates the north–south structure already present in the 16 region direct estimates; the statistic therefore describes the modelled surface, and the independent evidence of clustering is the regional gradient itself. An explicit residual check supports this: Moran’s I on within-region residuals (each district posterior minus its region mean) fell to 0.35–0.43 across the four outcomes — less than half the raw values — but remained statistically significant (all p = 0.002), indicating that the regional gradient accounts for most, but not all, of the global spatial signal and that meaningful district-level structure within regions persists. Second, the determinant analysis carries a bounded circularity: seven of the ten covariates also informed the small-area model, so the SHAP importance of those seven is corroborative, while the importance of improved water and poverty incidence — which did not — is not. Third, machine-learning performance under spatial cross-validation was honest and uneven: the covariates predicted anaemia well out-of-region but did not generalise for IYCF inadequacy or diarrhoea, which should temper any causal reading of the determinant ranking for those two outcomes."));
body.push(P("The policy implication is direct. A national-mean framing cannot allocate resources; a 17-district quadruple-burden core can. Concentrating integrated water, sanitation, maternal-education and nutrition investment on those districts, while sustaining the conditions that keep the southern districts in the Low-Low class, is a tractable equity strategy. Because the determinant effects are spatially non-stationary, intervention design should be calibrated regionally rather than applied as a single national package."));

// ---- 5 STRENGTHS AND LIMITATIONS ----
body.push(H1("5. Strengths and limitations"));
body.push(P("The principal limitation is structural and defines how the results should be read: the outcomes were observed at 16 regions, not 261 districts, so the effective inferential unit is the region and the district estimates are model-based posteriors. Within-region district variation is inferred from district covariates and the spatial prior; the estimates are most trustworthy at the scale of regional contrasts and least trustworthy for fine distinctions between neighbouring districts of the same region, and no district-level outcome data exist for Ghana 2022 against which to validate them externally. Every district figure should be read with its credible interval."));
body.push(P("Several further limitations follow. The determinant model omits causes known to drive the northern burden — malaria endemicity, seasonal food insecurity and the Guinea-savanna agro-ecological zone — which are represented only abstractly by the spatial-frailty term and may confound the measured determinant effects; the determinant estimates are associational. The 16-region stunting figures were transcribed from the GDHS 2022 summary-report regional table and, although cross-checked against the national value and the published regional extremes, should be re-verified against the GDHS final-report tables before any submission. The diarrhoea outcome uses a three-year birth-cohort denominator, and the WASH covariates are region-imputed. A single random seed was used, with bootstrap and cross-validation variability quantified."));
body.push(P("Set against these limitations, the study has clear strengths: a fully reproducible, openly-coded pipeline; a benchmarked small-area estimator that honours the region direct estimates exactly; honest out-of-region cross-validation rather than optimistic in-sample fit; explicit quantification of uncertainty through credible intervals, exceedance probabilities and bootstrap intervals; and the first joint district-level treatment of four child-health outcomes for Ghana within the 261-district administrative frame."));

// ---- 6 CONCLUSION (no citations) ----
body.push(H1("6. Conclusion"));
body.push(P("Childhood stunting, anaemia, infant-feeding inadequacy and diarrhoea in Ghana form a single, spatially-concentrated syndemic whose modelled district burden surface converges on a compact northern core of 17 districts carrying all four conditions at once. Water and sanitation access, female illiteracy and poverty are the dominant determinants, and their effects vary geographically. A reproducible small-area-estimation pipeline can convert region-level survey data into a district-level evidence base for targeted, equity-focused child-nutrition investment, provided the model-based nature of the district estimates is kept in view."));

// ---- DECLARATIONS ----
body.push(H1("Declarations"));
body.push(PR([R("Ethics approval. ", { b: true }), R("The study used publicly-released aggregate data with no personal identifiers and required no new ethical approval; the underlying 2022 GDHS was approved by the Ghana Health Service Ethics Review Committee.")]));
body.push(PR([R("Data and code availability. ", { b: true }), R("The 261-district master dataset, spatial-weight matrices and all analysis scripts are openly available in the project repository.")]));
body.push(PR([R("Funding. ", { b: true }), R("This research received no specific grant from any funding agency.")]));
body.push(PR([R("Competing interests. ", { b: true }), R("The author declares no competing interests.")]));
body.push(PR([R("Reporting guidelines. ", { b: true }), R("STROBE (cross-sectional), RECORD-Spatial and TRIPOD+AI checklists were followed.")]));

// ---- REFERENCES ----
body.push(H1("References"));
refParas.forEach(p => body.push(p));

// ====================== ASSEMBLE ============================================
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "1d4e6f" },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, font: "Arial", color: "2e8b8b" },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } },
    },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Ghana child-nutrition small-area estimation  ·  ", size: 16 }),
        new TextRun({ children: [PageNumber.CURRENT], size: 16 })] })] }) },
    children: body,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUT, buf);
  console.log("Manuscript written:", OUT, (buf.length / 1024 / 1024).toFixed(2), "MB");
});
