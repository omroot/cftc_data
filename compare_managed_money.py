"""Compare Managed Money WTI positions between Marouen's Bloomberg file and CFTC download.

Covers both Disaggregated Futures Only and Disaggregated Combined reports.
"""

import pandas as pd

MAROUEN_PATH = "cftc_downloads/from_marouen/cot_report_wti (3).csv"
CFTC_FUTURES_PATH = "cftc_downloads/disaggregated_futures_only.csv"
CFTC_COMBINED_PATH = "cftc_downloads/disaggregated_combined.csv"
OUTPUT_PATH = "cftc_downloads/managed_money_comparison.csv"

WTI_CONTRACT_CODE = "067651"

# Marouen columns — Futures Only
MAROUEN_FUTURES_COLS = [
    "CFTC NYMEX Crude Oil Managed Money Long Contracts/Disagg Futures Only",
    "CFTC NYMEX Crude Oil Managed Money Short Contracts/Disagg Futures Only",
    "CFTC NYMEX Crude Oil Managed Money Spreading Contracts/Disagg Futures Only",
    "CFTC NYMEX Crude Oil Managed Money Net Total/Disagg Futures Only",
]

# Marouen columns — Combined
MAROUEN_COMBINED_COLS = [
    "CFTC NYMEX Crude Oil Managed Money Long Contracts/Disagg Combined",
    "CFTC NYMEX Crude Oil Managed Money Short Contracts/Disagg Combined",
    "CFTC NYMEX Crude Oil Managed Money Spreading Contracts/Disagg Combined",
    "CFTC NYMEX Crude Oil Managed Money Net Total/Disagg Combined",
]

# CFTC raw columns (same field names in both futures-only and combined datasets)
CFTC_COLS = [
    "m_money_positions_long_all",
    "m_money_positions_short_all",
    "m_money_positions_spread",
]


def load_cftc_wti(path):
    """Load a CFTC dataset and filter to WTI by contract code."""
    df = pd.read_csv(path)
    df["report_date_as_yyyy_mm_dd"] = pd.to_datetime(df["report_date_as_yyyy_mm_dd"])
    return df[df["cftc_contract_market_code"] == WTI_CONTRACT_CODE].copy()


def compare(merged, marouen_cols, cftc_cols, suffix):
    """Build comparison columns for one report type."""
    out = pd.DataFrame()

    for col in marouen_cols:
        out[col] = pd.to_numeric(merged[col], errors="coerce")

    for col in cftc_cols:
        out[f"{col}/{suffix}"] = pd.to_numeric(merged[col], errors="coerce")

    # Compute net from CFTC (long - short)
    net_col = f"m_money_net_computed/{suffix}"
    out[net_col] = out[f"{cftc_cols[0]}/{suffix}"] - out[f"{cftc_cols[1]}/{suffix}"]

    # Diffs
    out[f"diff_long/{suffix}"] = out[marouen_cols[0]] - out[f"{cftc_cols[0]}/{suffix}"]
    out[f"diff_short/{suffix}"] = out[marouen_cols[1]] - out[f"{cftc_cols[1]}/{suffix}"]
    out[f"diff_spread/{suffix}"] = out[marouen_cols[2]] - out[f"{cftc_cols[2]}/{suffix}"]
    out[f"diff_net/{suffix}"] = out[marouen_cols[3]] - out[net_col]

    return out


def main():
    # Load Marouen's Bloomberg file
    marouen = pd.read_csv(MAROUEN_PATH)
    marouen = marouen.rename(columns={marouen.columns[0]: "date"})
    marouen["date"] = pd.to_datetime(marouen["date"])

    # Load CFTC datasets
    cftc_futures = load_cftc_wti(CFTC_FUTURES_PATH)
    cftc_combined = load_cftc_wti(CFTC_COMBINED_PATH)

    # Merge Marouen with each CFTC dataset
    merged_futures = pd.merge(
        marouen, cftc_futures, left_on="date", right_on="report_date_as_yyyy_mm_dd", how="inner"
    )
    merged_combined = pd.merge(
        marouen, cftc_combined, left_on="date", right_on="report_date_as_yyyy_mm_dd", how="inner"
    )

    # Build comparison columns
    futures_out = compare(merged_futures, MAROUEN_FUTURES_COLS, CFTC_COLS, "futures_only")
    combined_out = compare(merged_combined, MAROUEN_COMBINED_COLS, CFTC_COLS, "combined")

    # Combine into single output (align on date)
    futures_out["date"] = merged_futures["date"].values
    combined_out["date"] = merged_combined["date"].values

    out = pd.merge(futures_out, combined_out, on="date", how="outer")
    out = out.sort_values("date").reset_index(drop=True)

    # Move date to first column
    cols = ["date"] + [c for c in out.columns if c != "date"]
    out = out[cols]

    out.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved {len(out)} rows to {OUTPUT_PATH}")
    print(f"Date range: {out['date'].min().date()} to {out['date'].max().date()}")

    for suffix in ["futures_only", "combined"]:
        print(f"\nDiff stats ({suffix}):")
        for field in ["long", "short", "spread", "net"]:
            col = f"diff_{field}/{suffix}"
            if col in out.columns:
                print(f"  {col}: min={out[col].min()}, max={out[col].max()}, sum={out[col].sum()}")


if __name__ == "__main__":
    main()
