"""Callbacks for the CFTC Positioning page."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, no_update

from dashboard.dashboard.data import loader_cftc as cftc
from dashboard.dashboard.data import loader_cftc_aggregated as cftc_agg


# ── contract type options per report tab ─────────────────────────────────

_CONTRACT_OPTS_DISAGG = [
    {"label": "Futures Only", "value": "futures_only"},
    {"label": "Combined (F+O)", "value": "combined"},
]
_CONTRACT_OPTS_AGG = [
    {"label": "Combined (F+O)", "value": "combined"},
]


# ── trader category metadata per report tab ──────────────────────────────

_TRADER_CATS_DISAGG = {
    "mm":      {"label": "Managed Money",     "net_col": "mm_net",      "long_col": "m_money_positions_long_all",  "short_col": "m_money_positions_short_all",  "color": "#2ca02c"},
    "pm":      {"label": "Prod/Merch",        "net_col": "pm_net",      "long_col": "prod_merc_positions_long",    "short_col": "prod_merc_positions_short",    "color": "#1f77b4"},
    "swap":    {"label": "Swap Dealers",       "net_col": "swap_net",    "long_col": "swap_positions_long_all",     "short_col": "swap__positions_short_all",    "color": "#ff7f0e"},
    "other":   {"label": "Other Reportable",   "net_col": "other_net",   "long_col": "other_rept_positions_long",   "short_col": "other_rept_positions_short",   "color": "#9467bd"},
    "nonrept": {"label": "Non-Reportable",     "net_col": "nonrept_net", "long_col": "nonrept_positions_long_all",  "short_col": "nonrept_positions_short_all",  "color": "#8c564b"},
}

_TRADER_CATS_AGG = {
    "noncomm": {"label": "Non-Commercial",  "net_col": "noncomm_net", "long_col": "noncomm_positions_long_all",  "short_col": "noncomm_positions_short_all",  "color": "#2ca02c"},
    "comm":    {"label": "Commercial",       "net_col": "comm_net",    "long_col": "comm_positions_long_all",     "short_col": "comm_positions_short_all",     "color": "#1f77b4"},
    "nonrept": {"label": "Non-Reportable",   "net_col": "nonrept_net", "long_col": "nonrept_positions_long_all",  "short_col": "nonrept_positions_short_all",  "color": "#8c564b"},
}

_DEFAULT_DISAGG = ["mm"]
_DEFAULT_AGG = ["noncomm"]


def _get_cat_meta(active_tab):
    """Return (category_dict, default_keys) for the active tab."""
    if active_tab == "aggregated":
        return _TRADER_CATS_AGG, _DEFAULT_AGG
    return _TRADER_CATS_DISAGG, _DEFAULT_DISAGG


def _hex_to_rgb(hex_color):
    """Convert '#rrggbb' to 'r,g,b' string for rgba usage."""
    h = hex_color.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


# ── cascading dropdowns ──────────────────────────────────────────────────

@callback(
    Output("cftc-contract-type", "options"),
    Output("cftc-contract-type", "value"),
    Input("cftc-tabs", "active_tab"),
)
def update_contract_type_options(active_tab):
    if active_tab == "aggregated":
        return _CONTRACT_OPTS_AGG, "combined"
    return _CONTRACT_OPTS_DISAGG, "futures_only"


@callback(
    Output("cftc-trader-cat", "options"),
    Output("cftc-trader-cat", "value"),
    Input("cftc-tabs", "active_tab"),
)
def update_trader_cat_options(active_tab):
    cats, defaults = _get_cat_meta(active_tab)
    options = [{"label": v["label"], "value": k} for k, v in cats.items()]
    return options, defaults


@callback(
    Output("cftc-commodity", "options"),
    Output("cftc-commodity", "value"),
    Input("url", "pathname"),
    Input("cftc-tabs", "active_tab"),
    Input("cftc-contract-type", "value"),
)
def populate_commodities(pathname, active_tab, contract_type):
    if active_tab == "aggregated":
        opts = cftc_agg.get_commodities()
    else:
        opts = cftc.get_commodities(contract_type or "futures_only")
    values = [o["value"] for o in opts]
    default = "CRUDE OIL" if "CRUDE OIL" in values else (values[0] if values else None)
    return opts, default


@callback(
    Output("cftc-market", "options"),
    Output("cftc-market", "value"),
    Input("cftc-commodity", "value"),
    Input("cftc-tabs", "active_tab"),
    Input("cftc-contract-type", "value"),
)
def update_markets(commodity, active_tab, contract_type):
    if not commodity:
        return [], None
    if active_tab == "aggregated":
        opts = cftc_agg.get_markets(commodity)
        default = cftc_agg.get_default_market(commodity)
    else:
        ct = contract_type or "futures_only"
        opts = cftc.get_markets(commodity, ct)
        default = cftc.get_default_market(commodity, ct)
    opts = [{"label": "ALL", "value": "__ALL__"}] + opts
    return opts, default


# ── helper: empty figure ────────────────────────────────────────────────

def _empty_fig(height=350):
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=20, t=30, b=30),
        height=height,
    )
    return fig


# ── main update callback ────────────────────────────────────────────────

@callback(
    # Long KPIs
    Output("cftc-kpi-long-val", "children"),
    Output("cftc-kpi-long-wow", "children"),
    Output("cftc-kpi-long-pctoi", "children"),
    Output("cftc-kpi-long-zscore", "children"),
    # Short KPIs
    Output("cftc-kpi-short-val", "children"),
    Output("cftc-kpi-short-wow", "children"),
    Output("cftc-kpi-short-pctoi", "children"),
    Output("cftc-kpi-short-zscore", "children"),
    # Net KPIs
    Output("cftc-kpi-net-val", "children"),
    Output("cftc-kpi-net-wow", "children"),
    Output("cftc-kpi-net-pctoi", "children"),
    Output("cftc-kpi-net-zscore", "children"),
    Output("cftc-kpi-conc4", "children"),
    Output("cftc-kpi-conc8", "children"),
    Output("cftc-kpi-date", "children"),
    Output("cftc-chart-long", "figure"),
    Output("cftc-chart-short", "figure"),
    Output("cftc-chart-net", "figure"),
    Output("cftc-chart-pctoi", "figure"),
    Output("cftc-chart-oi", "figure"),
    Output("cftc-chart-breakdown", "figure"),
    Output("cftc-chart-weekly-change", "figure"),
    Output("cftc-chart-zscore", "figure"),
    Output("cftc-chart-concentration", "figure"),
    Output("cftc-table", "data"),
    Output("cftc-table", "columns"),
    Input("cftc-market", "value"),
    Input("cftc-timerange", "value"),
    Input("cftc-zscore-lookback", "value"),
    Input("cftc-trader-cat", "value"),
    State("cftc-commodity", "value"),
    State("cftc-tabs", "active_tab"),
    State("cftc-contract-type", "value"),
)
def update_cftc_page(market, timerange, lookback, trader_cats, commodity, active_tab, contract_type):
    ef = _empty_fig
    empty_cols = []
    kpi_defaults = ("—",) * 15  # 4 long + 4 short + 4 net + conc4 + conc8 + date
    defaults = (*kpi_defaults,
                ef(), ef(), ef(), ef(), ef(), ef(), ef(), ef(), ef(),
                [], empty_cols)

    if not commodity or not market:
        return defaults

    is_agg = active_tab == "aggregated"
    cat_meta, default_keys = _get_cat_meta(active_tab)

    # ── defensive filtering: discard stale category keys after tab switch
    if not trader_cats:
        selected_keys = default_keys
    else:
        selected_keys = [k for k in trader_cats if k in cat_meta]
        if not selected_keys:
            selected_keys = default_keys

    multi = len(selected_keys) > 1
    primary_key = selected_keys[0]
    primary_meta = cat_meta[primary_key]
    primary_net_col = primary_meta["net_col"]

    # ── load data ─────────────────────────────────────────────────────
    if is_agg:
        sub = cftc_agg.get_series(commodity, market)
    else:
        ct = contract_type or "futures_only"
        sub = cftc.get_cftc_series(commodity, market, ct)

    if sub.empty:
        return defaults

    # apply time range
    if timerange and timerange > 0:
        cutoff = sub["date"].max() - pd.Timedelta(weeks=timerange)
        sf = sub[sub["date"] >= cutoff].copy()
    else:
        sf = sub.copy()

    if sf.empty:
        return defaults

    # ── KPIs (always primary category) ─────────────────────────────
    if is_agg:
        kpis = cftc_agg.compute_kpis(sub, lookback, net_col=primary_net_col)
    else:
        kpis = cftc.compute_kpis(sub, lookback, net_col=primary_net_col)

    net_val = kpis["net_val"]

    def fmt(val):
        if val is None:
            return "—"
        return f"{val:,.0f}"

    def fmt_change(val):
        if val is None:
            return "—"
        sign = "+" if val > 0 else ""
        return f"{sign}{val:,.0f}"

    # ── compute Long / Short / Net KPIs ────────────────────────────
    latest_row = sub.iloc[-1]
    prev_row = sub.iloc[-2] if len(sub) > 1 else None
    long_col = primary_meta["long_col"]
    short_col = primary_meta["short_col"]
    oi = latest_row["open_interest_all"]

    compute_zs = cftc_agg.compute_zscore if is_agg else cftc.compute_zscore

    # Long KPIs
    long_val = latest_row.get(long_col)
    long_prev = prev_row[long_col] if prev_row is not None else None
    long_wow = long_val - long_prev if long_val is not None and long_prev is not None else None
    long_pctoi = (long_val / oi * 100) if long_val is not None and oi and oi != 0 else None
    long_zs = compute_zs(sub[long_col], lookback)
    long_zscore = long_zs.iloc[-1] if not long_zs.empty else None

    kpi_long_val = fmt(long_val)
    kpi_long_wow = fmt_change(long_wow)
    kpi_long_pctoi = f"{long_pctoi:.1f}%" if long_pctoi is not None else "—"
    kpi_long_zscore = f"{long_zscore:+.2f}" if long_zscore is not None and not np.isnan(long_zscore) else "—"

    # Short KPIs
    short_val = latest_row.get(short_col)
    short_prev = prev_row[short_col] if prev_row is not None else None
    short_wow = short_val - short_prev if short_val is not None and short_prev is not None else None
    short_pctoi = (short_val / oi * 100) if short_val is not None and oi and oi != 0 else None
    short_zs = compute_zs(sub[short_col], lookback)
    short_zscore = short_zs.iloc[-1] if not short_zs.empty else None

    kpi_short_val = fmt(short_val)
    kpi_short_wow = fmt_change(short_wow)
    kpi_short_pctoi = f"{short_pctoi:.1f}%" if short_pctoi is not None else "—"
    kpi_short_zscore = f"{short_zscore:+.2f}" if short_zscore is not None and not np.isnan(short_zscore) else "—"

    # Net KPIs
    net_val = kpis["net_val"]
    kpi_net_val = fmt(net_val)
    kpi_net_wow = fmt_change(kpis["wow_change"])
    kpi_net_pctoi = f'{kpis["net_pct_oi"]:.1f}%' if kpis["net_pct_oi"] is not None else "—"
    kpi_net_zscore = f'{kpis["zscore"]:+.2f}' if kpis["zscore"] is not None else "—"
    kpi_conc4 = (
        f'{kpis["top4_conc_long"]:.1f}% / {kpis["top4_conc_short"]:.1f}%'
        if kpis["top4_conc_long"] is not None and kpis["top4_conc_short"] is not None
        else "—"
    )
    top8_long = latest_row.get("conc_gross_le_8_tdr_long")
    top8_short = latest_row.get("conc_gross_le_8_tdr_short")
    kpi_conc8 = (
        f'{top8_long:.1f}% / {top8_short:.1f}%'
        if top8_long is not None and top8_short is not None
        else "—"
    )
    kpi_date = kpis["latest_date"].strftime("%Y-%m-%d") if kpis["latest_date"] is not None else "—"

    # ── 0a. Long Positioning chart ──────────────────────────────────
    fig_long = go.Figure()
    for key in selected_keys:
        meta = cat_meta[key]
        fig_long.add_trace(go.Scatter(
            x=sf["date"], y=sf[meta["long_col"]],
            mode="lines", name=meta["label"],
            line=dict(color=meta["color"], width=2),
        ))
    fig_long.update_layout(
        title="Long Positions",
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=30),
        height=370,
        yaxis_title="Contracts",
        hovermode="x unified",
    )

    # ── 0b. Short Positioning chart ─────────────────────────────────
    fig_short = go.Figure()
    for key in selected_keys:
        meta = cat_meta[key]
        fig_short.add_trace(go.Scatter(
            x=sf["date"], y=sf[meta["short_col"]],
            mode="lines", name=meta["label"],
            line=dict(color=meta["color"], width=2, dash="dash"),
        ))
    fig_short.update_layout(
        title="Short Positions",
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=30),
        height=370,
        yaxis_title="Contracts",
        hovermode="x unified",
    )

    # ── 1. Net Positioning chart (hero) ─────────────────────────────
    fig_net = go.Figure()
    if multi:
        for key in selected_keys:
            meta = cat_meta[key]
            fig_net.add_trace(go.Scatter(
                x=sf["date"], y=sf[meta["net_col"]],
                mode="lines", name=meta["label"],
                line=dict(color=meta["color"], width=2),
            ))
        fig_net.add_hline(y=0, line_dash="dash", line_color="gray",
                          line_width=1, opacity=0.5)
    else:
        color = primary_meta["color"]
        rgb = _hex_to_rgb(color)
        fig_net.add_trace(go.Scatter(
            x=sf["date"], y=sf[primary_net_col],
            mode="lines", name=primary_meta["label"],
            line=dict(color=color, width=2),
            fill="tozeroy", fillcolor=f"rgba({rgb},0.15)",
        ))
    fig_net.update_layout(
        title="Net Positioning" if multi else f"{primary_meta['label']} Net Positioning",
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=30),
        height=370,
        yaxis_title="Contracts",
        hovermode="x unified",
    )

    # ── 2. Net as % of OI chart ─────────────────────────────────────
    fig_pctoi = go.Figure()
    for key in selected_keys:
        meta = cat_meta[key]
        oi = sf["open_interest_all"]
        pct = (sf[meta["net_col"]] / oi * 100).replace([np.inf, -np.inf], np.nan)
        fig_pctoi.add_trace(go.Scatter(
            x=sf["date"], y=pct,
            mode="lines", name=meta["label"],
            line=dict(color=meta["color"], width=2),
        ))
    fig_pctoi.add_hline(y=0, line_dash="dash", line_color="gray",
                        line_width=1, opacity=0.5)
    fig_pctoi.update_layout(
        title="Net as % of Open Interest",
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=30),
        height=370,
        yaxis_title="% of OI",
        hovermode="x unified",
    )

    # ── 3. Open Interest chart ──────────────────────────────────────
    fig_oi = go.Figure()
    fig_oi.add_trace(go.Scatter(
        x=sf["date"], y=sf["open_interest_all"],
        mode="lines", name="Open Interest",
        line=dict(color="#ff7f0e", width=1.5),
        fill="tozeroy", fillcolor="rgba(255,127,14,0.1)",
    ))
    fig_oi.update_layout(
        title="Open Interest",
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=30),
        height=370,
        yaxis_title="Contracts",
        hovermode="x unified",
    )

    # ── 4. Position Breakdown stacked bar ───────────────────────────
    fig_bd = go.Figure()
    if is_agg:
        breakdown_spec = [
            ("noncomm_net", "Non-Commercial", "#2ca02c"),
            ("comm_net", "Commercial", "#1f77b4"),
            ("nonrept_net", "Non-Reportable", "#8c564b"),
        ]
    else:
        breakdown_spec = [
            ("pm_net", "Prod/Merch", "#1f77b4"),
            ("swap_net", "Swap Dealers", "#ff7f0e"),
            ("mm_net", "Managed Money", "#2ca02c"),
            ("other_net", "Other Rept", "#9467bd"),
            ("nonrept_net", "Non-Reportable", "#8c564b"),
        ]
    for col, name, color in breakdown_spec:
        fig_bd.add_trace(go.Bar(
            x=sf["date"], y=sf[col], name=name,
            marker_color=color,
        ))
    fig_bd.update_layout(
        title="Position Breakdown (Net)",
        barmode="relative",
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=30),
        height=370,
        yaxis_title="Contracts",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )

    # ── 5. Weekly Change bars ───────────────────────────────────────
    fig_wc = go.Figure()
    if multi:
        for key in selected_keys:
            meta = cat_meta[key]
            net_change = sf[meta["net_col"]].diff()
            fig_wc.add_trace(go.Bar(
                x=sf["date"], y=net_change,
                name=meta["label"],
                marker_color=meta["color"],
            ))
        fig_wc.update_layout(barmode="group")
    else:
        net_change = sf[primary_net_col].diff()
        colors = ["#2ca02c" if v >= 0 else "#d62728" for v in net_change.fillna(0)]
        fig_wc.add_trace(go.Bar(
            x=sf["date"], y=net_change,
            marker_color=colors, name=f"{primary_meta['label']} Change",
        ))
    fig_wc.update_layout(
        title="Net Weekly Change" if multi else f"{primary_meta['label']} Net Weekly Change",
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=30),
        height=370,
        yaxis_title="Contracts",
        hovermode="x unified",
    )

    # ── 6. Z-Score chart ────────────────────────────────────────────
    fig_zs = go.Figure()
    compute_zs = cftc_agg.compute_zscore if is_agg else cftc.compute_zscore
    if multi:
        for key in selected_keys:
            meta = cat_meta[key]
            zs = compute_zs(sf[meta["net_col"]], lookback)
            fig_zs.add_trace(go.Scatter(
                x=sf["date"], y=zs,
                mode="lines", name=meta["label"],
                line=dict(color=meta["color"], width=2),
            ))
    else:
        zs = compute_zs(sf[primary_net_col], lookback)
        fig_zs.add_trace(go.Scatter(
            x=sf["date"], y=zs,
            mode="lines", name="Z-Score",
            line=dict(color=primary_meta["color"], width=2),
        ))
    for level, color, dash in [
        (2, "red", "dash"), (1, "orange", "dot"),
        (0, "gray", "dash"),
        (-1, "orange", "dot"), (-2, "red", "dash"),
    ]:
        fig_zs.add_hline(
            y=level, line_dash=dash, line_color=color,
            line_width=1, opacity=0.6,
            annotation_text=f"{level:+d}" if level != 0 else "0",
            annotation_position="right",
        )
    fig_zs.update_layout(
        title=f"Net Positioning Z-Score ({lookback}w lookback)",
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=30),
        height=370,
        yaxis_title="Z-Score",
        hovermode="x unified",
    )

    # ── 7. Concentration Ratios chart ───────────────────────────────
    latest = sf.iloc[-1]
    conc_data = {
        "Top 4 Long": latest.get("conc_gross_le_4_tdr_long", 0) or 0,
        "Top 4 Short": latest.get("conc_gross_le_4_tdr_short", 0) or 0,
        "Top 8 Long": latest.get("conc_gross_le_8_tdr_long", 0) or 0,
        "Top 8 Short": latest.get("conc_gross_le_8_tdr_short", 0) or 0,
    }
    fig_conc = go.Figure()
    fig_conc.add_trace(go.Bar(
        x=["Top 4", "Top 8"],
        y=[conc_data["Top 4 Long"], conc_data["Top 8 Long"]],
        name="Long", marker_color="#2ca02c",
    ))
    fig_conc.add_trace(go.Bar(
        x=["Top 4", "Top 8"],
        y=[conc_data["Top 4 Short"], conc_data["Top 8 Short"]],
        name="Short", marker_color="#d62728",
    ))
    fig_conc.update_layout(
        title="Concentration Ratios (% of OI)",
        barmode="group",
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=30),
        height=370,
        yaxis_title="% of OI",
        hovermode="x unified",
    )

    # ── table data + columns ──────────────────────────────────────
    if is_agg:
        table_col_ids = [
            "date", "noncomm_net", "comm_net", "nonrept_net",
            "open_interest_all", "conc_gross_le_4_tdr_long",
            "conc_gross_le_4_tdr_short",
        ]
        table_columns = [
            {"name": "Date", "id": "date"},
            {"name": "Non-Comm Net", "id": "noncomm_net", "type": "numeric"},
            {"name": "Comm Net", "id": "comm_net", "type": "numeric"},
            {"name": "Non-Rept Net", "id": "nonrept_net", "type": "numeric"},
            {"name": "Open Interest", "id": "open_interest_all", "type": "numeric"},
            {"name": "Top4 Long %", "id": "conc_gross_le_4_tdr_long", "type": "numeric"},
            {"name": "Top4 Short %", "id": "conc_gross_le_4_tdr_short", "type": "numeric"},
        ]
    else:
        table_col_ids = [
            "date", "mm_net", "pm_net", "swap_net", "other_net",
            "open_interest_all", "conc_gross_le_4_tdr_long",
            "conc_gross_le_4_tdr_short",
        ]
        table_columns = [
            {"name": "Date", "id": "date"},
            {"name": "MM Net", "id": "mm_net", "type": "numeric"},
            {"name": "PM Net", "id": "pm_net", "type": "numeric"},
            {"name": "Swap Net", "id": "swap_net", "type": "numeric"},
            {"name": "Other Net", "id": "other_net", "type": "numeric"},
            {"name": "Open Interest", "id": "open_interest_all", "type": "numeric"},
            {"name": "Top4 Long %", "id": "conc_gross_le_4_tdr_long", "type": "numeric"},
            {"name": "Top4 Short %", "id": "conc_gross_le_4_tdr_short", "type": "numeric"},
        ]

    table_df = sf[table_col_ids].copy()
    table_df["date"] = table_df["date"].dt.strftime("%Y-%m-%d")
    table_data = table_df.sort_values("date", ascending=False).to_dict("records")

    return (
        kpi_long_val, kpi_long_wow, kpi_long_pctoi, kpi_long_zscore,
        kpi_short_val, kpi_short_wow, kpi_short_pctoi, kpi_short_zscore,
        kpi_net_val, kpi_net_wow, kpi_net_pctoi, kpi_net_zscore, kpi_conc4, kpi_conc8, kpi_date,
        fig_long, fig_short, fig_net, fig_pctoi, fig_oi, fig_bd, fig_wc, fig_zs, fig_conc,
        table_data, table_columns,
    )
