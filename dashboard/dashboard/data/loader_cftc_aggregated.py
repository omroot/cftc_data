"""
CFTC aggregated COT data loader.

Data file:
  data/cftc_downloads/legacy_combined.csv  (combined futures + options)

Aggregated COT breaks positions into:
  Commercial, Non-Commercial (Large Speculators), Non-Reportable.
"""

import os
from functools import lru_cache

import numpy as np
import pandas as pd

_DATA_ROOT = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir, os.pardir
)

_USE_COLS = [
    "market_and_exchange_names",
    "report_date_as_yyyy_mm_dd",
    "contract_market_name",
    "cftc_contract_market_code",
    "commodity_name",
    "commodity_subgroup_name",
    "commodity_group_name",
    "open_interest_all",
    "noncomm_positions_long_all",
    "noncomm_positions_short_all",
    "noncomm_postions_spread_all",
    "comm_positions_long_all",
    "comm_positions_short_all",
    "tot_rept_positions_long_all",
    "tot_rept_positions_short",
    "nonrept_positions_long_all",
    "nonrept_positions_short_all",
    "conc_gross_le_4_tdr_long",
    "conc_gross_le_4_tdr_short",
    "conc_gross_le_8_tdr_long",
    "conc_gross_le_8_tdr_short",
    "change_in_open_interest_all",
    "change_in_noncomm_long_all",
    "change_in_noncomm_short_all",
    "contract_units",
]

_BENCHMARK_MARKETS = {
    "CRUDE OIL": "CRUDE OIL, LIGHT SWEET-WTI",
    "NATURAL GAS": "NATURAL GAS",
    "GOLD": "GOLD",
    "SILVER": "SILVER",
    "CORN": "CORN",
    "WHEAT": "WHEAT-SRW",
    "SOYBEANS": "SOYBEANS",
    "SUGAR": "SUGAR NO. 11",
    "COFFEE": "COFFEE C",
    "COCOA": "COCOA",
    "COTTON": "COTTON NO. 2",
    "COPPER": "COPPER-GRADE #1",
}


@lru_cache(maxsize=1)
def load_cftc_aggregated() -> pd.DataFrame:
    path = os.path.join(_DATA_ROOT, "cftc_downloads", "legacy_combined.csv")
    df = pd.read_csv(path, usecols=_USE_COLS)
    df["report_date_as_yyyy_mm_dd"] = pd.to_datetime(
        df["report_date_as_yyyy_mm_dd"], format="mixed"
    )
    df.rename(columns={"report_date_as_yyyy_mm_dd": "date"}, inplace=True)

    num_cols = [
        "open_interest_all",
        "noncomm_positions_long_all", "noncomm_positions_short_all",
        "noncomm_postions_spread_all",
        "comm_positions_long_all", "comm_positions_short_all",
        "tot_rept_positions_long_all", "tot_rept_positions_short",
        "nonrept_positions_long_all", "nonrept_positions_short_all",
        "conc_gross_le_4_tdr_long", "conc_gross_le_4_tdr_short",
        "conc_gross_le_8_tdr_long", "conc_gross_le_8_tdr_short",
        "change_in_open_interest_all",
        "change_in_noncomm_long_all", "change_in_noncomm_short_all",
    ]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["noncomm_net"] = (
        df["noncomm_positions_long_all"] - df["noncomm_positions_short_all"]
    )
    df["comm_net"] = (
        df["comm_positions_long_all"] - df["comm_positions_short_all"]
    )
    df["nonrept_net"] = (
        df["nonrept_positions_long_all"] - df["nonrept_positions_short_all"]
    )

    for col in ("commodity_name", "contract_market_name", "commodity_group_name"):
        df[col] = df[col].astype("category")

    return df.sort_values("date").reset_index(drop=True)


# ── dropdown helpers ─────────────────────────────────────────────────────

def get_commodities() -> list[dict]:
    df = load_cftc_aggregated()
    names = sorted(df["commodity_name"].dropna().unique())
    return [{"label": n, "value": n} for n in names]


def get_markets(commodity_name: str) -> list[dict]:
    df = load_cftc_aggregated()
    sub = df[df["commodity_name"] == commodity_name]
    names = sorted(sub["contract_market_name"].dropna().unique())
    return [{"label": n, "value": n} for n in names]


def get_default_market(commodity_name: str) -> str | None:
    """Return the benchmark market, falling back to market with most data."""
    markets = get_markets(commodity_name)
    if not markets:
        return None
    market_labels = [m["value"] for m in markets]

    benchmark = _BENCHMARK_MARKETS.get(commodity_name)
    if benchmark and benchmark in market_labels:
        return benchmark

    df = load_cftc_aggregated()
    sub = df[df["commodity_name"] == commodity_name]
    counts = sub["contract_market_name"].value_counts()
    return counts.index[0] if not counts.empty else market_labels[0]


# ── filtered data ────────────────────────────────────────────────────────

def get_series(commodity_name: str, market: str) -> pd.DataFrame:
    df = load_cftc_aggregated()
    if market == "__ALL__":
        return _get_aggregated_series(df, commodity_name)
    sub = df[
        (df["commodity_name"] == commodity_name)
        & (df["contract_market_name"] == market)
    ].copy()
    return sub.sort_values("date").reset_index(drop=True)


def _get_aggregated_series(df: pd.DataFrame, commodity_name: str) -> pd.DataFrame:
    """Aggregate all markets for a commodity by summing positions per date."""
    sub = df[df["commodity_name"] == commodity_name].copy()
    if sub.empty:
        return pd.DataFrame()

    sum_cols = [
        "open_interest_all",
        "noncomm_positions_long_all", "noncomm_positions_short_all",
        "noncomm_postions_spread_all",
        "comm_positions_long_all", "comm_positions_short_all",
        "tot_rept_positions_long_all", "tot_rept_positions_short",
        "nonrept_positions_long_all", "nonrept_positions_short_all",
        "change_in_open_interest_all",
        "change_in_noncomm_long_all", "change_in_noncomm_short_all",
    ]
    conc_cols = [
        "conc_gross_le_4_tdr_long", "conc_gross_le_4_tdr_short",
        "conc_gross_le_8_tdr_long", "conc_gross_le_8_tdr_short",
    ]

    agg = sub.groupby("date", observed=True)[sum_cols].sum().reset_index()

    for col in conc_cols:
        sub[f"_w_{col}"] = sub[col] * sub["open_interest_all"]
    conc_agg = sub.groupby("date", observed=True)[[f"_w_{c}" for c in conc_cols]].sum().reset_index()
    oi_agg = sub.groupby("date", observed=True)["open_interest_all"].sum().reset_index()
    conc_agg = conc_agg.merge(oi_agg, on="date")
    for col in conc_cols:
        conc_agg[col] = conc_agg[f"_w_{col}"] / conc_agg["open_interest_all"]
    agg = agg.merge(conc_agg[["date"] + conc_cols], on="date")

    agg["commodity_name"] = commodity_name
    agg["contract_market_name"] = "ALL"

    agg["noncomm_net"] = agg["noncomm_positions_long_all"] - agg["noncomm_positions_short_all"]
    agg["comm_net"] = agg["comm_positions_long_all"] - agg["comm_positions_short_all"]
    agg["nonrept_net"] = agg["nonrept_positions_long_all"] - agg["nonrept_positions_short_all"]

    return agg.sort_values("date").reset_index(drop=True)


# ── analytics ────────────────────────────────────────────────────────────

def compute_zscore(series: pd.Series, lookback: int = 52) -> pd.Series:
    """Rolling z-score of a series."""
    roll_mean = series.rolling(lookback, min_periods=max(1, lookback // 2)).mean()
    roll_std = series.rolling(lookback, min_periods=max(1, lookback // 2)).std()
    return (series - roll_mean) / roll_std.replace(0, np.nan)


def compute_kpis(sub: pd.DataFrame, lookback: int = 52, net_col: str = "noncomm_net") -> dict:
    """
    KPI dict for the aggregated CFTC report:
      net_val, wow_change, net_pct_oi, zscore, top4_conc
    """
    if sub.empty:
        return {
            "net_val": None, "wow_change": None, "net_pct_oi": None,
            "zscore": None, "top4_conc_long": None, "top4_conc_short": None,
            "latest_date": None,
        }

    latest = sub.iloc[-1]
    prev = sub.iloc[-2] if len(sub) > 1 else None

    net_val = latest[net_col]
    wow_change = net_val - prev[net_col] if prev is not None else None
    oi = latest["open_interest_all"]
    net_pct_oi = (net_val / oi * 100) if oi and oi != 0 else None

    zs = compute_zscore(sub[net_col], lookback)
    zscore = zs.iloc[-1] if not zs.empty else None

    return {
        "net_val": net_val,
        "wow_change": wow_change,
        "net_pct_oi": net_pct_oi,
        "zscore": round(zscore, 2) if zscore is not None and not np.isnan(zscore) else None,
        "top4_conc_long": latest.get("conc_gross_le_4_tdr_long"),
        "top4_conc_short": latest.get("conc_gross_le_4_tdr_short"),
        "latest_date": latest["date"],
    }
