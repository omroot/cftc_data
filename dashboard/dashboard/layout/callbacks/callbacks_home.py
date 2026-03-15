"""Callbacks for the Home page — CFTC positioning KPIs + data refresh."""

import logging
import sys
from pathlib import Path

import pandas as pd
from dash import Input, Output, callback, html, no_update

from dashboard.dashboard.data import loader_cftc as cftc
from dashboard.dashboard.data import loader_cftc_aggregated as cftc_agg

logger = logging.getLogger(__name__)

# Resolve the repo root so we can import the downloader
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_CFTC_DOWNLOADS = _REPO_ROOT / "cftc_downloads"

# Commodities shown on the home page
# (commodity_name, market, id_prefix)
# Using combined (F+O) and __ALL__ markets for all
_HOME_COMMODITIES = [
    ("CRUDE OIL", "WTI-PHYSICAL", "wti"),
    ("HEATING OIL-DIESEL-GASOIL", "NY HARBOR ULSD", "ho"),
    ("GASOLINE", "GASOLINE RBOB", "rbob"),
    ("NATURAL GAS", "__ALL__", "ng"),
    ("GOLD", "__ALL__", "gold"),
    ("SILVER", "__ALL__", "silver"),
    ("ELECTRICITY", "__ALL__", "elec"),
]


def _fmt_value(val):
    if val is None or pd.isna(val):
        return "—"
    return f"{val:,.0f}"


def _fmt_change(val, prefix="WoW "):
    if val is None or pd.isna(val):
        return ""
    sign = "+" if val >= 0 else ""
    return f"{prefix}{sign}{val:,.0f}"


def _fmt_date(dt):
    if dt is None or pd.isna(dt):
        return "—"
    if isinstance(dt, pd.Timestamp):
        return dt.strftime("%Y-%m-%d")
    return str(dt)[:10]


# ── Build output list dynamically ─────────────────────────────────────────

_KPI_OUTPUTS = []
for _, _, prefix in _HOME_COMMODITIES:
    _KPI_OUTPUTS.extend([
        Output(f"home-kpi-{prefix}-net", "children"),
        Output(f"home-kpi-{prefix}-chg", "children"),
        Output(f"home-kpi-{prefix}-zscore", "children"),
        Output(f"home-kpi-{prefix}-pctoi", "children"),
    ])
_KPI_OUTPUTS.append(Output("home-fresh-cftc", "children"))

_NUM_OUTPUTS = len(_KPI_OUTPUTS)


@callback(
    *_KPI_OUTPUTS,
    Input("url", "pathname"),
    Input("home-refresh-status", "children"),  # re-trigger after refresh
)
def update_home_kpis(pathname, _refresh_status):
    if pathname not in ("/", "/home"):
        return (no_update,) * _NUM_OUTPUTS

    results = []
    cftc_date = None

    for commodity, market, _ in _HOME_COMMODITIES:
        try:
            # Use combined (F+O) contract type
            sub = cftc.get_cftc_series(commodity, market, "combined")
            kpis = cftc.compute_kpis(sub)

            net_str = _fmt_value(kpis["net_val"])
            wow_str = _fmt_change(kpis["wow_change"], prefix="")

            zs = kpis["zscore"]
            zs_str = f"{zs:+.2f}" if zs is not None else "—"

            pctoi = kpis["net_pct_oi"]
            pctoi_str = f"{pctoi:.1f}%" if pctoi is not None else "—"

            if cftc_date is None:
                cftc_date = kpis["latest_date"]

            results.extend([net_str, wow_str, zs_str, pctoi_str])
        except Exception:
            logger.exception("Error computing CFTC KPI for %s / %s", commodity, market)
            results.extend(["—", "", "—", "—"])

    results.append(f"CFTC: {_fmt_date(cftc_date)}")

    return tuple(results)


@callback(
    Output("home-refresh-status", "children"),
    Input("home-btn-refresh", "n_clicks"),
    prevent_initial_call=True,
)
def refresh_cftc_data(n_clicks):
    """Download delta for all CFTC datasets and clear cached data."""
    if not n_clicks:
        return no_update

    try:
        # Import the downloader
        sys.path.insert(0, str(_REPO_ROOT))
        from cftc_config import load_cftc_credentials
        from cftc_downloader import update_all_datasets

        creds_path = _REPO_ROOT / "cftc_api_info"
        credentials = load_cftc_credentials(creds_path)

        results = update_all_datasets(_CFTC_DOWNLOADS, credentials["key_id"])

        # Clear lru_cache so the dashboard picks up new data
        cftc.load_cftc.cache_clear()
        cftc.load_cftc_combined.cache_clear()
        cftc_agg.load_cftc_aggregated.cache_clear()

        # Build summary
        lines = []
        for name, info in results.items():
            lines.append(f"{name}: +{info['new_rows']} rows, latest {info['latest_date']}")
        summary = " | ".join(lines)

        return html.Span([
            html.Strong("Refreshed! ", style={"color": "#2ca02c"}),
            summary,
        ])

    except Exception as e:
        logger.exception("Error refreshing CFTC data")
        return html.Span([
            html.Strong("Error: ", style={"color": "#d62728"}),
            str(e),
        ])
