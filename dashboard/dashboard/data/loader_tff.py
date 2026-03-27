"""
TFF (Traders in Financial Futures) data loader.

Data files:
  data/cftc_downloads/tff_futures_only.csv
  data/cftc_downloads/tff_combined.csv

TFF trader categories:
  Dealer/Intermediary, Asset Manager/Institutional,
  Leveraged Funds, Other Reportables, Non-Reportable.
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
    "dealer_positions_long_all",
    "dealer_positions_short_all",
    "dealer_positions_spread_all",
    "asset_mgr_positions_long",
    "asset_mgr_positions_short",
    "asset_mgr_positions_spread",
    "lev_money_positions_long",
    "lev_money_positions_short",
    "lev_money_positions_spread",
    "other_rept_positions_long",
    "other_rept_positions_short",
    "other_rept_positions_spread",
    "nonrept_positions_long_all",
    "nonrept_positions_short_all",
    "conc_gross_le_4_tdr_long",
    "conc_gross_le_4_tdr_short",
    "conc_gross_le_8_tdr_long",
    "conc_gross_le_8_tdr_short",
    "change_in_open_interest_all",
    "change_in_lev_money_long",
    "change_in_lev_money_short",
    "contract_units",
]

_BENCHMARK_MARKETS = {
    "UST 10Y NOTE": "10-YEAR U.S. TREASURY NOTES",
    "UST 5Y NOTE": "5-YEAR U.S. TREASURY NOTES",
    "UST BOND": "U.S. TREASURY BONDS",
    "EURODOLLAR": "EURODOLLAR",
    "FED FUNDS": "30-DAY FEDERAL FUNDS",
    "E-MINI S&P 500": "E-MINI S&P 500 STOCK INDEX",
    "EURO FX": "EURO FX",
    "JAPANESE YEN": "JAPANESE YEN",
    "BRITISH POUND": "BRITISH POUND STERLING",
    "VIX FUTURES": "VIX FUTURES",
}


def _load_and_process(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=_USE_COLS)
    df["report_date_as_yyyy_mm_dd"] = pd.to_datetime(
        df["report_date_as_yyyy_mm_dd"], format="mixed"
    )
    df.rename(columns={"report_date_as_yyyy_mm_dd": "date"}, inplace=True)

    num_cols = [
        "open_interest_all",
        "dealer_positions_long_all", "dealer_positions_short_all",
        "dealer_positions_spread_all",
        "asset_mgr_positions_long", "asset_mgr_positions_short",
        "asset_mgr_positions_spread",
        "lev_money_positions_long", "lev_money_positions_short",
        "lev_money_positions_spread",
        "other_rept_positions_long", "other_rept_positions_short",
        "other_rept_positions_spread",
        "nonrept_positions_long_all", "nonrept_positions_short_all",
        "conc_gross_le_4_tdr_long", "conc_gross_le_4_tdr_short",
        "conc_gross_le_8_tdr_long", "conc_gross_le_8_tdr_short",
        "change_in_open_interest_all",
        "change_in_lev_money_long", "change_in_lev_money_short",
    ]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["release_date"] = df["date"] + pd.Timedelta(days=3)

    df["dealer_net"] = df["dealer_positions_long_all"] - df["dealer_positions_short_all"]
    df["asset_mgr_net"] = df["asset_mgr_positions_long"] - df["asset_mgr_positions_short"]
    df["lev_money_net"] = df["lev_money_positions_long"] - df["lev_money_positions_short"]
    df["other_net"] = df["other_rept_positions_long"] - df["other_rept_positions_short"]
    df["nonrept_net"] = df["nonrept_positions_long_all"] - df["nonrept_positions_short_all"]

    for col in ("commodity_name", "contract_market_name", "commodity_group_name"):
        df[col] = df[col].astype("category")

    return df.sort_values("date").reset_index(drop=True)


@lru_cache(maxsize=1)
def load_tff() -> pd.DataFrame:
    path = os.path.join(_DATA_ROOT, "cftc_downloads", "tff_futures_only.csv")
    return _load_and_process(path)


@lru_cache(maxsize=1)
def load_tff_combined() -> pd.DataFrame:
    path = os.path.join(_DATA_ROOT, "cftc_downloads", "tff_combined.csv")
    return _load_and_process(path)


def _get_df(contract_type: str = "futures_only") -> pd.DataFrame:
    if contract_type == "combined":
        return load_tff_combined()
    return load_tff()


# -- dropdown helpers ---------------------------------------------------------

def get_commodities(contract_type: str = "futures_only") -> list[dict]:
    df = _get_df(contract_type)
    names = sorted(df["commodity_name"].dropna().unique())
    return [{"label": n, "value": n} for n in names]


def get_markets(commodity_name: str, contract_type: str = "futures_only") -> list[dict]:
    df = _get_df(contract_type)
    sub = df[df["commodity_name"] == commodity_name]
    names = sorted(sub["contract_market_name"].dropna().unique())
    return [{"label": n, "value": n} for n in names]


def get_default_market(commodity_name: str, contract_type: str = "futures_only") -> str | None:
    markets = get_markets(commodity_name, contract_type)
    if not markets:
        return None
    market_labels = [m["value"] for m in markets]

    benchmark = _BENCHMARK_MARKETS.get(commodity_name)
    if benchmark and benchmark in market_labels:
        return benchmark

    df = _get_df(contract_type)
    sub = df[df["commodity_name"] == commodity_name]
    counts = sub["contract_market_name"].value_counts()
    return counts.index[0] if not counts.empty else market_labels[0]


# -- filtered data ------------------------------------------------------------

def get_tff_series(commodity_name: str, market: str, contract_type: str = "futures_only") -> pd.DataFrame:
    df = _get_df(contract_type)
    if market == "__ALL__":
        return _get_aggregated_series(df, commodity_name)
    sub = df[
        (df["commodity_name"] == commodity_name) &
        (df["contract_market_name"] == market)
    ].copy()
    return sub.sort_values("date").reset_index(drop=True)


def _get_aggregated_series(df: pd.DataFrame, commodity_name: str) -> pd.DataFrame:
    sub = df[df["commodity_name"] == commodity_name].copy()
    if sub.empty:
        return pd.DataFrame()

    sum_cols = [
        "open_interest_all",
        "dealer_positions_long_all", "dealer_positions_short_all",
        "dealer_positions_spread_all",
        "asset_mgr_positions_long", "asset_mgr_positions_short",
        "asset_mgr_positions_spread",
        "lev_money_positions_long", "lev_money_positions_short",
        "lev_money_positions_spread",
        "other_rept_positions_long", "other_rept_positions_short",
        "other_rept_positions_spread",
        "nonrept_positions_long_all", "nonrept_positions_short_all",
        "change_in_open_interest_all",
        "change_in_lev_money_long", "change_in_lev_money_short",
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

    agg["dealer_net"] = agg["dealer_positions_long_all"] - agg["dealer_positions_short_all"]
    agg["asset_mgr_net"] = agg["asset_mgr_positions_long"] - agg["asset_mgr_positions_short"]
    agg["lev_money_net"] = agg["lev_money_positions_long"] - agg["lev_money_positions_short"]
    agg["other_net"] = agg["other_rept_positions_long"] - agg["other_rept_positions_short"]
    agg["nonrept_net"] = agg["nonrept_positions_long_all"] - agg["nonrept_positions_short_all"]
    agg["release_date"] = agg["date"] + pd.Timedelta(days=3)

    return agg.sort_values("date").reset_index(drop=True)


# -- analytics ----------------------------------------------------------------

def compute_zscore(series: pd.Series, lookback: int = 52) -> pd.Series:
    roll_mean = series.rolling(lookback, min_periods=max(1, lookback // 2)).mean()
    roll_std = series.rolling(lookback, min_periods=max(1, lookback // 2)).std()
    return (series - roll_mean) / roll_std.replace(0, np.nan)


def compute_kpis(sub: pd.DataFrame, lookback: int = 52, net_col: str = "lev_money_net") -> dict:
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
