#!/usr/bin/env python3
"""
Nutrition Anaemia Growth Determinants — Ghana 261 Districts
Interactive Dash surveillance dashboard: stunting · anaemia · IYCF · diarrhoea
Run: python app.py  →  http://127.0.0.1:8050
"""
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc

# ── Data ─────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)
DATA = os.path.join(BASE, "data", "processed", "master_261district_nutrition_FINAL.csv")

df = pd.read_csv(DATA)

# Resolve outcome columns (handle naming variants)
OUTCOME_MAP = {
    "stunting_prev":          "Stunting Prevalence (%)",
    "anaemia_prev":           "Anaemia Prevalence (6–59 m, %)",
    "iycf_inadequacy_prev":   "IYCF Inadequacy (%)",
    "diarrhoea_prev":         "Diarrhoea Prevalence (%)",
}
# Keep only columns that exist
OUTCOME_MAP = {k: v for k, v in OUTCOME_MAP.items() if k in df.columns}
if not OUTCOME_MAP:
    # Fallback: grab first 4 numeric columns that look like prevalence
    numeric_cols = df.select_dtypes("number").columns.tolist()
    for c in numeric_cols[:4]:
        OUTCOME_MAP[c] = c.replace("_", " ").title()

SHAP_MAP = {
    "Water & sanitation access":  0.47,
    "Female illiteracy":          0.38,
    "Poverty rate":               0.31,
    "NHIS coverage":              0.22,
    "Population density":         0.14,
    "Under-15 share":             0.11,
    "Urbanicity":                 0.09,
}

KPI_DATA = {
    "Moran's I (stunting)":         ("0.937 (p = 0.002)", "success"),
    "Moran's I (anaemia)":          ("0.959 (p = 0.002)", "success"),
    "Quadruple-burden hotspots":    ("17 districts",       "danger"),
    "Joint HH clusters (4 outcomes)": ("49 districts",    "warning"),
    "XGBoost LOROCV AUC":           ("0.88 ± 0.04",       "info"),
    "Top SHAP: Water & sanitation": ("|SHAP| = 0.47",     "secondary"),
}

# ── App layout ────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="Ghana Nutrition SAE — 261 Districts",
)
server = app.server


def kpi_card(label, value, color="warning"):
    return dbc.Card(
        dbc.CardBody([
            html.P(label, className="text-muted mb-1", style={"fontSize": "0.70rem"}),
            html.H6(value, className=f"text-{color} mb-0 fw-bold"),
        ]),
        className="mb-2 h-100",
    )


app.layout = dbc.Container(
    fluid=True,
    style={"backgroundColor": "#0d1117", "minHeight": "100vh"},
    children=[
        # ── Header ──────────────────────────────────────────────────────────
        dbc.Row(dbc.Col(
            html.H4(
                "Small-area Estimation of Child-Nutrition Outcomes — Ghana 261 Districts",
                className="text-center text-light py-3",
            )
        )),
        dbc.Row(dbc.Col(
            html.P(
                "Bayesian BYM2-SAE · LISA clustering · GWR non-stationarity · "
                "XGBoost + SHAP determinants · 2022 GDHS × 2021 PHC",
                className="text-center text-muted mb-3",
                style={"fontSize": "0.82rem"},
            )
        )),

        # ── KPI row ─────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col(kpi_card(lbl, val, col), md=2)
            for lbl, (val, col) in KPI_DATA.items()
        ], className="mb-3"),

        # ── Controls ────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.Label("Outcome", className="text-light small"),
                dcc.Dropdown(
                    id="outcome-select",
                    options=[{"label": v, "value": k} for k, v in OUTCOME_MAP.items()],
                    value=next(iter(OUTCOME_MAP)),
                    clearable=False,
                    style={"backgroundColor": "#161b22", "color": "#c9d1d9"},
                ),
            ], md=4),
            dbc.Col([
                html.Label("Colour scale", className="text-light small"),
                dcc.Dropdown(
                    id="colorscale-select",
                    options=[
                        {"label": "OrRd",     "value": "OrRd"},
                        {"label": "YlOrRd",   "value": "YlOrRd"},
                        {"label": "Viridis",  "value": "Viridis"},
                        {"label": "Plasma",   "value": "Plasma"},
                        {"label": "RdYlGn_r", "value": "RdYlGn_r"},
                    ],
                    value="OrRd",
                    clearable=False,
                    style={"backgroundColor": "#161b22", "color": "#c9d1d9"},
                ),
            ], md=3),
        ], className="mb-3"),

        # ── Main charts ─────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col(dcc.Graph(id="scatter-map",  style={"height": "480px"}), md=7),
            dbc.Col(dcc.Graph(id="shap-bar",     style={"height": "480px"}), md=5),
        ], className="mb-3"),

        # ── Distribution + hotspot table ────────────────────────────────────
        dbc.Row([
            dbc.Col(dcc.Graph(id="histogram",    style={"height": "340px"}), md=5),
            dbc.Col(dcc.Graph(id="box-region",   style={"height": "340px"}), md=7),
        ], className="mb-3"),

        # ── Data table ──────────────────────────────────────────────────────
        dbc.Row(dbc.Col([
            html.H6("District data", className="text-light mb-2"),
            dash_table.DataTable(
                id="district-table",
                style_table={"overflowX": "auto"},
                style_cell={
                    "backgroundColor": "#161b22",
                    "color": "#c9d1d9",
                    "fontSize": "0.75rem",
                    "border": "1px solid #30363d",
                },
                style_header={
                    "backgroundColor": "#21262d",
                    "color": "#f0f6fc",
                    "fontWeight": "bold",
                },
                page_size=12,
                sort_action="native",
                filter_action="native",
            ),
        ])),

        # ── Footer ──────────────────────────────────────────────────────────
        dbc.Row(dbc.Col(
            html.P(
                "Valentine Golden Ghanem · Ghana COCOBOD Cocoa Clinic · "
                "ORCID: 0009-0002-8332-0220 · "
                "Data: 2022 GDHS (GSS/GHS/ICF) + 2021 PHC (GSS) — public aggregate data only",
                className="text-center text-muted py-3",
                style={"fontSize": "0.70rem"},
            )
        )),
    ],
)


# ── Callbacks ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("scatter-map",   "figure"),
    Output("shap-bar",      "figure"),
    Output("histogram",     "figure"),
    Output("box-region",    "figure"),
    Output("district-table","data"),
    Output("district-table","columns"),
    Input("outcome-select",     "value"),
    Input("colorscale-select",  "value"),
)
def update_charts(outcome, colorscale):
    label = OUTCOME_MAP.get(outcome, outcome)

    # ── Scatter / bubble map (lat/lon → scatter if no geometry) ─────────────
    if "lat" in df.columns and "lon" in df.columns:
        fig_map = px.scatter_geo(
            df,
            lat="lat", lon="lon",
            color=outcome,
            size=outcome,
            color_continuous_scale=colorscale,
            projection="mercator",
            scope="africa",
            hover_name=df.columns[0],
            hover_data={outcome: ":.2f"},
            title=f"{label} — Ghana 261 Districts",
            template="plotly_dark",
        )
        fig_map.update_geos(fitbounds="locations", showland=True,
                            landcolor="#21262d", showocean=True, oceancolor="#0d1117")
    else:
        # Fallback: ranked bar chart
        df_sorted = df.sort_values(outcome, ascending=False).head(30)
        dist_col  = df.columns[0]
        fig_map = px.bar(
            df_sorted, x=dist_col, y=outcome,
            color=outcome, color_continuous_scale=colorscale,
            title=f"Top-30 districts — {label}",
            template="plotly_dark",
        )
        fig_map.update_layout(xaxis_tickangle=-45)

    fig_map.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        coloraxis_colorbar={"title": "%", "tickfont": {"color": "#c9d1d9"}},
    )

    # ── SHAP importance bar ─────────────────────────────────────────────────
    shap_df = pd.DataFrame({
        "Feature":         list(SHAP_MAP.keys()),
        "Mean |SHAP|":     list(SHAP_MAP.values()),
    }).sort_values("Mean |SHAP|")

    fig_shap = px.bar(
        shap_df, x="Mean |SHAP|", y="Feature", orientation="h",
        color="Mean |SHAP|", color_continuous_scale="Oranges",
        title="SHAP determinant importance (XGBoost)",
        template="plotly_dark",
    )
    fig_shap.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        showlegend=False, coloraxis_showscale=False,
        yaxis={"tickfont": {"size": 11}},
    )

    # ── Histogram ───────────────────────────────────────────────────────────
    fig_hist = px.histogram(
        df, x=outcome, nbins=30,
        color_discrete_sequence=["#f39c12"],
        title=f"Distribution — {label}",
        template="plotly_dark",
    )
    fig_hist.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
        margin={"l": 40, "r": 10, "t": 40, "b": 40},
    )

    # ── Box by region ───────────────────────────────────────────────────────
    region_col = next(
        (c for c in df.columns if "region" in c.lower()), None
    )
    if region_col:
        fig_box = px.box(
            df.sort_values(outcome, ascending=False),
            x=region_col, y=outcome,
            color=region_col,
            title=f"Distribution by region — {label}",
            template="plotly_dark",
        )
        fig_box.update_layout(
            showlegend=False,
            paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
            margin={"l": 40, "r": 10, "t": 40, "b": 80},
            xaxis_tickangle=-45,
        )
    else:
        # Fallback — quartile bar
        quantiles = df[outcome].quantile([0.25, 0.50, 0.75, 1.0])
        fig_box = px.bar(
            x=["Q1 (25th pctile)", "Median", "Q3 (75th pctile)", "Max"],
            y=quantiles.values,
            color_discrete_sequence=["#3498db"],
            title=f"Quartile summary — {label}",
            template="plotly_dark",
        )
        fig_box.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
            margin={"l": 40, "r": 10, "t": 40, "b": 40},
        )

    # ── Table data ──────────────────────────────────────────────────────────
    display_cols = ([df.columns[0]] + [region_col] if region_col else [df.columns[0]]) + \
                   list(OUTCOME_MAP.keys())
    display_cols = [c for c in display_cols if c in df.columns][:8]
    tbl_df = df[display_cols].copy()
    for c in tbl_df.select_dtypes("number").columns:
        tbl_df[c] = tbl_df[c].round(2)

    columns = [{"name": c.replace("_", " ").title(), "id": c} for c in tbl_df.columns]
    data    = tbl_df.to_dict("records")

    return fig_map, fig_shap, fig_hist, fig_box, data, columns


if __name__ == "__main__":
    app.run(debug=True, port=8050)
