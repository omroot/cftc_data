"""Home page layout — CFTC positioning snapshot."""

from dash import dcc, html
import dash_bootstrap_components as dbc


def _kpi_card(title, value_id, change_id=None):
    """A single KPI card with a value and optional change line."""
    body = [
        html.H6(title, className="card-subtitle mb-1 text-muted",
                 style={"fontSize": "0.75rem"}),
        html.H4(id=value_id, children="—",
                 className="card-title mb-0",
                 style={"fontSize": "1.1rem", "fontWeight": "bold"}),
    ]
    if change_id:
        body.append(html.Small(id=change_id, children="",
                               className="text-muted",
                               style={"fontSize": "0.75rem"}))
    return dbc.Card(
        dbc.CardBody(body),
        className="shadow-sm",
        style={"minWidth": "150px"},
    )


def _nav_card(title, description, href):
    """A navigation card linking to another page."""
    return dbc.Card(
        dbc.CardBody([
            html.H5(title, className="card-title mb-1"),
            html.P(description, className="card-text text-muted",
                   style={"fontSize": "0.85rem"}),
            dcc.Link(
                dbc.Button("Go", color="primary", size="sm"),
                href=href,
            ),
        ]),
        className="shadow-sm h-100",
    )


# ── commodity rows config ─────────────────────────────────────────────────
# Each entry: (display_label, id_prefix)
HOME_COMMODITIES_DISPLAY = [
    ("WTI CRUDE OIL", "wti"),
    ("HEATING OIL (NY HARBOR ULSD)", "ho"),
    ("GASOLINE (RBOB)", "rbob"),
    ("NATURAL GAS", "ng"),
    ("GOLD", "gold"),
    ("SILVER", "silver"),
    ("ELECTRICITY", "elec"),
]


def _commodity_kpi_row(label, prefix):
    return [
        html.H6(f"{label} — MANAGED MONEY (COMBINED F+O, ALL CONTRACTS)",
                 className="text-uppercase text-muted mb-2",
                 style={"fontSize": "0.75rem", "letterSpacing": "0.05em"}),
        dbc.Row([
            dbc.Col(_kpi_card("MM Net Position",
                              f"home-kpi-{prefix}-net", f"home-kpi-{prefix}-chg"),
                    xs=6, md=2),
            dbc.Col(_kpi_card("Z-Score (52w)", f"home-kpi-{prefix}-zscore"),
                    xs=6, md=2),
            dbc.Col(_kpi_card("Net % of OI", f"home-kpi-{prefix}-pctoi"),
                    xs=6, md=2),
        ], className="mb-4 g-2"),
    ]


# ── build all commodity KPI rows ──────────────────────────────────────────
_commodity_rows = []
for label, prefix in HOME_COMMODITIES_DISPLAY:
    _commodity_rows.extend(_commodity_kpi_row(label, prefix))


# ── page layout ──────────────────────────────────────────────────────────

page_home = dbc.Container(
    fluid=True,
    children=[
        # ── header ───────────────────────────────────────────────────
        html.H3("CFTC Positioning Snapshot", className="mt-2 mb-0"),
        html.P("At-a-glance Commitment of Traders data",
               className="text-muted mb-3",
               style={"fontSize": "0.9rem"}),

        # ── data freshness + refresh ─────────────────────────────────
        html.H6("DATA FRESHNESS", className="text-uppercase text-muted mb-2",
                 style={"fontSize": "0.75rem", "letterSpacing": "0.05em"}),
        dbc.Row([
            dbc.Col(
                html.Div([
                    dbc.Badge(id="home-fresh-cftc", children="CFTC: —",
                              color="light", text_color="dark",
                              className="me-2 mb-2",
                              style={"fontSize": "0.75rem"}),
                ]),
                width="auto",
            ),
            dbc.Col(
                dbc.Button(
                    [html.I(className="me-1"), "Refresh Data"],
                    id="home-btn-refresh",
                    color="success",
                    size="sm",
                    className="mb-2",
                ),
                width="auto",
            ),
            dbc.Col(
                dcc.Loading(
                    html.Div(id="home-refresh-status", children="",
                             style={"fontSize": "0.85rem"}),
                    type="dot",
                ),
                width="auto",
                className="d-flex align-items-center",
            ),
        ], className="mb-4 g-2 align-items-center"),

        # ── commodity KPI rows ────────────────────────────────────────
        *_commodity_rows,

        # ── navigation cards ─────────────────────────────────────────
        html.H6("PAGES", className="text-uppercase text-muted mb-2",
                 style={"fontSize": "0.75rem", "letterSpacing": "0.05em"}),
        dbc.Row([
            dbc.Col(_nav_card("CFTC Positioning",
                              "Disaggregated and aggregated Commitment of Traders reports "
                              "with net positioning, z-scores, concentration ratios, and more.",
                              "/cftc_positioning"),
                    xs=12, md=6),
            dbc.Col(_nav_card("Data Guide",
                              "Learn about COT report types, trader categories, "
                              "key metrics, and every commodity/contract in the data.",
                              "/data_guide"),
                    xs=12, md=6),
        ], className="mb-4 g-3"),
    ],
)
