"""CFTC Positioning page layout."""

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc


def _kpi_card(title, value_id):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-subtitle mb-1 text-muted",
                     style={"fontSize": "0.75rem"}),
            html.H4(id=value_id, children="—",
                     className="card-title mb-0",
                     style={"fontSize": "1.1rem", "fontWeight": "bold"}),
        ]),
        className="shadow-sm",
        style={"minWidth": "140px"},
    )


page_cftc_positioning = dbc.Container(
    fluid=True,
    children=[
        html.H3("CFTC Positioning Data", className="mt-2 mb-3"),

        # ── report type subtabs ────────────────────────────────────────
        dbc.Tabs(
            id="cftc-tabs",
            active_tab="disaggregated",
            children=[
                dbc.Tab(label="Disaggregated", tab_id="disaggregated"),
                dbc.Tab(label="Aggregated", tab_id="aggregated"),
            ],
            className="mb-3",
        ),

        # ── filter row ──────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.Label("Commodity", className="fw-bold mb-1",
                           style={"fontSize": "0.8rem"}),
                dcc.Dropdown(id="cftc-commodity", placeholder="Select commodity…"),
            ], md=2),
            dbc.Col([
                html.Label("Market / Contract", className="fw-bold mb-1",
                           style={"fontSize": "0.8rem"}),
                dcc.Dropdown(id="cftc-market", placeholder="Select market…"),
            ], md=2),
            dbc.Col([
                html.Label("Contract Type", className="fw-bold mb-1",
                           style={"fontSize": "0.8rem"}),
                dcc.Dropdown(id="cftc-contract-type",
                             placeholder="Select…",
                             clearable=False),
            ], md=2),
            dbc.Col([
                html.Label("Trader Category", className="fw-bold mb-1",
                           style={"fontSize": "0.8rem"}),
                dcc.Dropdown(id="cftc-trader-cat",
                             placeholder="Select categories…",
                             multi=True),
            ], md=2),
            dbc.Col([
                html.Label("Time Range", className="fw-bold mb-1",
                           style={"fontSize": "0.8rem"}),
                dcc.Dropdown(
                    id="cftc-timerange",
                    options=[
                        {"label": "1 Year", "value": 52},
                        {"label": "2 Years", "value": 104},
                        {"label": "5 Years", "value": 260},
                        {"label": "10 Years", "value": 520},
                        {"label": "All", "value": 0},
                    ],
                    value=260,
                    clearable=False,
                ),
            ], md=2),
            dbc.Col([
                html.Label("Z-Score Lookback", className="fw-bold mb-1",
                           style={"fontSize": "0.8rem"}),
                dcc.Dropdown(
                    id="cftc-zscore-lookback",
                    options=[
                        {"label": "26 Weeks", "value": 26},
                        {"label": "52 Weeks", "value": 52},
                        {"label": "104 Weeks", "value": 104},
                        {"label": "156 Weeks", "value": 156},
                    ],
                    value=52,
                    clearable=False,
                ),
            ], md=2),
        ], className="mb-3"),

        # ── KPI cards — Long row ──────────────────────────────────────
        html.H6("LONG", className="text-uppercase text-muted mb-1",
                 style={"fontSize": "0.7rem", "letterSpacing": "0.05em"}),
        dbc.Row([
            dbc.Col(_kpi_card("Position", "cftc-kpi-long-val"), width="auto"),
            dbc.Col(_kpi_card("WoW Change", "cftc-kpi-long-wow"), width="auto"),
            dbc.Col(_kpi_card("% of OI", "cftc-kpi-long-pctoi"), width="auto"),
            dbc.Col(_kpi_card("Long Z-Score (vs hist.)", "cftc-kpi-long-zscore"), width="auto"),
        ], className="mb-2 g-2"),

        # ── KPI cards — Short row ─────────────────────────────────────
        html.H6("SHORT", className="text-uppercase text-muted mb-1",
                 style={"fontSize": "0.7rem", "letterSpacing": "0.05em"}),
        dbc.Row([
            dbc.Col(_kpi_card("Position", "cftc-kpi-short-val"), width="auto"),
            dbc.Col(_kpi_card("WoW Change", "cftc-kpi-short-wow"), width="auto"),
            dbc.Col(_kpi_card("% of OI", "cftc-kpi-short-pctoi"), width="auto"),
            dbc.Col(_kpi_card("Short Z-Score (vs hist.)", "cftc-kpi-short-zscore"), width="auto"),
        ], className="mb-2 g-2"),

        # ── KPI cards — Net row ───────────────────────────────────────
        html.H6("NET", className="text-uppercase text-muted mb-1",
                 style={"fontSize": "0.7rem", "letterSpacing": "0.05em"}),
        dbc.Row([
            dbc.Col(_kpi_card("Position", "cftc-kpi-net-val"), width="auto"),
            dbc.Col(_kpi_card("WoW Change", "cftc-kpi-net-wow"), width="auto"),
            dbc.Col(_kpi_card("Net % of OI", "cftc-kpi-net-pctoi"), width="auto"),
            dbc.Col(_kpi_card("Net Z-Score (vs hist.)", "cftc-kpi-net-zscore"), width="auto"),
            dbc.Col(_kpi_card("Top-4 Conc (L/S)", "cftc-kpi-conc4"), width="auto"),
            dbc.Col(_kpi_card("Top-8 Conc (L/S)", "cftc-kpi-conc8"), width="auto"),
            dbc.Col(_kpi_card("As of Date", "cftc-kpi-date"), width="auto"),
        ], className="mb-3 g-2"),

        # ── row 1: long + short positioning ────────────────────────
        dcc.Loading(
            dbc.Row([
                dbc.Col(dcc.Graph(id="cftc-chart-long",
                                  config={"displayModeBar": True}), md=6),
                dbc.Col(dcc.Graph(id="cftc-chart-short",
                                  config={"displayModeBar": True}), md=6),
            ], className="mb-3"),
        ),

        # ── row 2: net positioning overlay (hero, full width) ─────────
        dcc.Loading(
            dbc.Row([
                dbc.Col(dcc.Graph(id="cftc-chart-net",
                                  config={"displayModeBar": True}), md=12),
            ], className="mb-3"),
        ),

        # ── row 2: net % of OI + z-score ──────────────────────────────
        dcc.Loading(
            dbc.Row([
                dbc.Col(dcc.Graph(id="cftc-chart-pctoi",
                                  config={"displayModeBar": True}), md=6),
                dbc.Col(dcc.Graph(id="cftc-chart-zscore",
                                  config={"displayModeBar": True}), md=6),
            ], className="mb-3"),
        ),

        # ── row 3: weekly change + breakdown ──────────────────────────
        dcc.Loading(
            dbc.Row([
                dbc.Col(dcc.Graph(id="cftc-chart-weekly-change",
                                  config={"displayModeBar": True}), md=6),
                dbc.Col(dcc.Graph(id="cftc-chart-breakdown",
                                  config={"displayModeBar": True}), md=6),
            ], className="mb-3"),
        ),

        # ── row 4: open interest + concentration ──────────────────────
        dcc.Loading(
            dbc.Row([
                dbc.Col(dcc.Graph(id="cftc-chart-oi",
                                  config={"displayModeBar": True}), md=6),
                dbc.Col(dcc.Graph(id="cftc-chart-concentration",
                                  config={"displayModeBar": True}), md=6),
            ], className="mb-3"),
        ),

        # ── raw data table ──────────────────────────────────────────────
        html.H5("Raw Data", className="mt-2 mb-2"),
        dash_table.DataTable(
            id="cftc-table",
            page_size=15,
            sort_action="native",
            filter_action="native",
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "4px 8px",
                         "fontSize": "0.85rem"},
            style_header={"fontWeight": "bold", "backgroundColor": "#f0f0f0"},
        ),
    ],
)
