"""Callbacks for the TFF Positioning page."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, no_update

from dashboard.dashboard.data import loader_tff as tff


# -- trader category metadata -------------------------------------------------

_TRADER_CATS = {
    "lev_money":  {"label": "Leveraged Money",   "net_col": "lev_money_net",  "long_col": "lev_money_positions_long",   "short_col": "lev_money_positions_short",   "color": "#2ca02c"},
    "asset_mgr":  {"label": "Asset Manager",     "net_col": "asset_mgr_net",  "long_col": "asset_mgr_positions_long",   "short_col": "asset_mgr_positions_short",   "color": "#1f77b4"},
    "dealer":     {"label": "Dealer",             "net_col": "dealer_net",     "long_col": "dealer_positions_long_all",  "short_col": "dealer_positions_short_all",  "color": "#ff7f0e"},
    "other":      {"label": "Other Reportable",   "net_col": "other_net",      "long_col": "other_rept_positions_long",  "short_col": "other_rept_positions_short",  "color": "#9467bd"},
    "nonrept":    {"label": "Non-Reportable",     "net_col": "nonrept_net",    "long_col": "nonrept_positions_long_all", "short_col": "nonrept_positions_short_all", "color": "#8c564b"},
}

_DEFAULT_CATS = ["lev_money"]


def _hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


# -- cascading dropdowns ------------------------------------------------------

@callback(
    Output("tff-trader-cat", "options"),
    Output("tff-trader-cat", "value"),
    Input("url", "pathname"),
)
def update_tff_trader_cat_options(pathname):
    options = [{"label": v["label"], "value": k} for k, v in _TRADER_CATS.items()]
    return options, _DEFAULT_CATS


@callback(
    Output("tff-commodity", "options"),
    Output("tff-commodity", "value"),
    Input("url", "pathname"),
    Input("tff-contract-type", "value"),
)
def populate_tff_commodities(pathname, contract_type):
    opts = tff.get_commodities(contract_type or "futures_only")
    values = [o["value"] for o in opts]
    default = values[0] if values else None
    return opts, default


@callback(
    Output("tff-market", "options"),
    Output("tff-market", "value"),
    Input("tff-commodity", "value"),
    Input("tff-contract-type", "value"),
)
def update_tff_markets(commodity, contract_type):
    if not commodity:
        return [], None
    ct = contract_type or "futures_only"
    opts = tff.get_markets(commodity, ct)
    default = tff.get_default_market(commodity, ct)
    opts = [{"label": "ALL", "value": "__ALL__"}] + opts
    return opts, default


# -- helper: empty figure ------------------------------------------------------

def _empty_fig(height=350):
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=20, t=30, b=30),
        height=height,
    )
    return fig


# -- main update callback ------------------------------------------------------

@callback(
    # Long KPIs
    Output("tff-kpi-long-val", "children"),
    Output("tff-kpi-long-wow", "children"),
    Output("tff-kpi-long-pctoi", "children"),
    Output("tff-kpi-long-zscore", "children"),
    # Short KPIs
    Output("tff-kpi-short-val", "children"),
    Output("tff-kpi-short-wow", "children"),
    Output("tff-kpi-short-pctoi", "children"),
    Output("tff-kpi-short-zscore", "children"),
    # Net KPIs
    Output("tff-kpi-net-val", "children"),
    Output("tff-kpi-net-wow", "children"),
    Output("tff-kpi-net-pctoi", "children"),
    Output("tff-kpi-net-zscore", "children"),
    Output("tff-kpi-conc4", "children"),
    Output("tff-kpi-conc8", "children"),
    Output("tff-kpi-date", "children"),
    Output("tff-chart-long", "figure"),
    Output("tff-chart-short", "figure"),
    Output("tff-chart-net", "figure"),
    Output("tff-chart-pctoi", "figure"),
    Output("tff-chart-oi", "figure"),
    Output("tff-chart-breakdown", "figure"),
    Output("tff-chart-weekly-change", "figure"),
    Output("tff-chart-zscore", "figure"),
    Output("tff-chart-concentration", "figure"),
    Output("tff-table", "data"),
    Output("tff-table", "columns"),
    Input("tff-market", "value"),
    Input("tff-timerange", "value"),
    Input("tff-zscore-lookback", "value"),
    Input("tff-trader-cat", "value"),
    State("tff-commodity", "value"),
    State("tff-contract-type", "value"),
)
def update_tff_page(market, timerange, lookback, trader_cats, commodity, contract_type):
    ef = _empty_fig
    empty_cols = []
    kpi_defaults = ("—",) * 15
    defaults = (*kpi_defaults,
                ef(), ef(), ef(), ef(), ef(), ef(), ef(), ef(), ef(),
                [], empty_cols)

    if not commodity or not market:
        return defaults

    # -- defensive filtering of stale category keys
    if not trader_cats:
        selected_keys = _DEFAULT_CATS
    else:
        selected_keys = [k for k in trader_cats if k in _TRADER_CATS]
        if not selected_keys:
            selected_keys = _DEFAULT_CATS

    multi = len(selected_keys) > 1
    primary_key = selected_keys[0]
    primary_meta = _TRADER_CATS[primary_key]
    primary_net_col = primary_meta["net_col"]

    # -- load data
    ct = contract_type or "futures_only"
    sub = tff.get_tff_series(commodity, market, ct)

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

    # -- KPIs (primary category) -----------------------------------------------
    kpis = tff.compute_kpis(sub, lookback, net_col=primary_net_col)

    def fmt(val):
        if val is None:
            return "—"
        return f"{val:,.0f}"

    def fmt_change(val):
        if val is None:
            return "—"
        sign = "+" if val > 0 else ""
        return f"{sign}{val:,.0f}"

    latest_row = sub.iloc[-1]
    prev_row = sub.iloc[-2] if len(sub) > 1 else None
    long_col = primary_meta["long_col"]
    short_col = primary_meta["short_col"]
    oi = latest_row["open_interest_all"]

    # Long KPIs
    long_val = latest_row.get(long_col)
    long_prev = prev_row[long_col] if prev_row is not None else None
    long_wow = long_val - long_prev if long_val is not None and long_prev is not None else None
    long_pctoi = (long_val / oi * 100) if long_val is not None and oi and oi != 0 else None
    long_zs = tff.compute_zscore(sub[long_col], lookback)
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
    short_zs = tff.compute_zscore(sub[short_col], lookback)
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

    # -- 0a. Long Positioning chart --------------------------------------------
    fig_long = go.Figure()
    for key in selected_keys:
        meta = _TRADER_CATS[key]
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

    # -- 0b. Short Positioning chart -------------------------------------------
    fig_short = go.Figure()
    for key in selected_keys:
        meta = _TRADER_CATS[key]
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

    # -- 1. Net Positioning chart (hero) ---------------------------------------
    fig_net = go.Figure()
    if multi:
        for key in selected_keys:
            meta = _TRADER_CATS[key]
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

    # -- 2. Net as % of OI chart -----------------------------------------------
    fig_pctoi = go.Figure()
    for key in selected_keys:
        meta = _TRADER_CATS[key]
        oi_series = sf["open_interest_all"]
        pct = (sf[meta["net_col"]] / oi_series * 100).replace([np.inf, -np.inf], np.nan)
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

    # -- 3. Open Interest chart ------------------------------------------------
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

    # -- 4. Position Breakdown stacked bar -------------------------------------
    fig_bd = go.Figure()
    breakdown_spec = [
        ("dealer_net", "Dealer", "#ff7f0e"),
        ("asset_mgr_net", "Asset Manager", "#1f77b4"),
        ("lev_money_net", "Leveraged Money", "#2ca02c"),
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

    # -- 5. Weekly Change bars -------------------------------------------------
    fig_wc = go.Figure()
    if multi:
        for key in selected_keys:
            meta = _TRADER_CATS[key]
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

    # -- 6. Z-Score chart ------------------------------------------------------
    fig_zs = go.Figure()
    if multi:
        for key in selected_keys:
            meta = _TRADER_CATS[key]
            zs = tff.compute_zscore(sf[meta["net_col"]], lookback)
            fig_zs.add_trace(go.Scatter(
                x=sf["date"], y=zs,
                mode="lines", name=meta["label"],
                line=dict(color=meta["color"], width=2),
            ))
    else:
        zs = tff.compute_zscore(sf[primary_net_col], lookback)
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

    # -- 7. Concentration Ratios chart -----------------------------------------
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

    # -- table data + columns --------------------------------------------------
    table_col_ids = [
        "date", "lev_money_net", "asset_mgr_net", "dealer_net", "other_net",
        "open_interest_all", "conc_gross_le_4_tdr_long",
        "conc_gross_le_4_tdr_short",
    ]
    table_columns = [
        {"name": "Date", "id": "date"},
        {"name": "Lev Money Net", "id": "lev_money_net", "type": "numeric"},
        {"name": "Asset Mgr Net", "id": "asset_mgr_net", "type": "numeric"},
        {"name": "Dealer Net", "id": "dealer_net", "type": "numeric"},
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
