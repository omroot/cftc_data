"""Show how individual CFTC NYMEX + ICE columns sum to produce Marouen's cot_db.csv values.

Mapping:
- cot_db "Commercial" = Disagg Combined Prod/Merch NYMEX (067651) + ICE (067411)
  Source: disaggregated_combined.csv, columns: prod_merc_positions_long, prod_merc_positions_short

- cot_db "ManagedMoney" = Legacy Combined NonCommercial NYMEX (067651) + ICE (067411)
  Source: legacy_combined.csv, columns: noncomm_positions_long_all, noncomm_positions_short_all
"""

import pandas as pd

COT_DB_PATH = "cftc_downloads/from_marouen/cot_db.csv"
CFTC_LEGACY_COMBINED_PATH = "cftc_downloads/legacy_combined.csv"
CFTC_DISAGG_COMBINED_PATH = "cftc_downloads/disaggregated_combined.csv"
OUTPUT_PATH = "cftc_downloads/cot_db_breakdown.csv"

NYMEX_WTI_CODE = "067651"
ICE_BRENT_CODE = "067411"
DATE_COL = "report_date_as_yyyy_mm_dd"


def load_split(path, code_col, date_col, value_cols):
    """Load a CFTC dataset and return NYMEX and ICE rows separately, keyed by date."""
    df = pd.read_csv(path, low_memory=False)
    df[date_col] = pd.to_datetime(df[date_col])
    for col in value_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    nymex = df[df[code_col] == NYMEX_WTI_CODE][[date_col] + value_cols].copy()
    ice = df[df[code_col] == ICE_BRENT_CODE][[date_col] + value_cols].copy()
    return nymex, ice


def main():
    # Load cot_db CL
    db = pd.read_csv(COT_DB_PATH)
    db["tradeDate"] = pd.to_datetime(db["tradeDate"])
    cl = db[db["Name"] == "CL"].dropna(subset=["ManagedMoney_LongPosition"]).copy()
    cl = cl[["tradeDate", "CommercialLongPosition", "CommercialShortPosition",
             "Commercial_NetPosition", "ManagedMoney_LongPosition",
             "ManagedMoney_ShortPosition", "ManagedMoney_NetPosition"]]

    # Commercial = Disagg Combined Prod/Merch
    disagg_cols = ["prod_merc_positions_long", "prod_merc_positions_short"]
    nymex_disagg, ice_disagg = load_split(
        CFTC_DISAGG_COMBINED_PATH, "cftc_contract_market_code", DATE_COL, disagg_cols,
    )

    # ManagedMoney = Legacy Combined NonCommercial
    legacy_cols = ["noncomm_positions_long_all", "noncomm_positions_short_all"]
    nymex_legacy, ice_legacy = load_split(
        CFTC_LEGACY_COMBINED_PATH, "cftc_contract_market_code", DATE_COL, legacy_cols,
    )

    # Merge all onto cot_db dates, preserving original CFTC column names with exchange prefix
    out = cl.copy()

    # Disagg Combined: NYMEX prod_merc
    out = pd.merge(out, nymex_disagg.rename(columns={
        DATE_COL: "tradeDate",
        "prod_merc_positions_long": "nymex_067651/prod_merc_positions_long",
        "prod_merc_positions_short": "nymex_067651/prod_merc_positions_short",
    }), on="tradeDate", how="inner")

    # Disagg Combined: ICE prod_merc
    out = pd.merge(out, ice_disagg.rename(columns={
        DATE_COL: "tradeDate",
        "prod_merc_positions_long": "ice_067411/prod_merc_positions_long",
        "prod_merc_positions_short": "ice_067411/prod_merc_positions_short",
    }), on="tradeDate", how="inner")

    # Legacy Combined: NYMEX noncomm
    out = pd.merge(out, nymex_legacy.rename(columns={
        DATE_COL: "tradeDate",
        "noncomm_positions_long_all": "nymex_067651/noncomm_positions_long_all",
        "noncomm_positions_short_all": "nymex_067651/noncomm_positions_short_all",
    }), on="tradeDate", how="inner")

    # Legacy Combined: ICE noncomm
    out = pd.merge(out, ice_legacy.rename(columns={
        DATE_COL: "tradeDate",
        "noncomm_positions_long_all": "ice_067411/noncomm_positions_long_all",
        "noncomm_positions_short_all": "ice_067411/noncomm_positions_short_all",
    }), on="tradeDate", how="inner")

    # Compute sums and diffs — Commercial
    out["sum/prod_merc_positions_long"] = (
        out["nymex_067651/prod_merc_positions_long"] + out["ice_067411/prod_merc_positions_long"]
    )
    out["sum/prod_merc_positions_short"] = (
        out["nymex_067651/prod_merc_positions_short"] + out["ice_067411/prod_merc_positions_short"]
    )
    out["diff_comm_long"] = out["CommercialLongPosition"] - out["sum/prod_merc_positions_long"]
    out["diff_comm_short"] = out["CommercialShortPosition"] - out["sum/prod_merc_positions_short"]

    # Compute sums and diffs — ManagedMoney
    out["sum/noncomm_positions_long_all"] = (
        out["nymex_067651/noncomm_positions_long_all"] + out["ice_067411/noncomm_positions_long_all"]
    )
    out["sum/noncomm_positions_short_all"] = (
        out["nymex_067651/noncomm_positions_short_all"] + out["ice_067411/noncomm_positions_short_all"]
    )
    out["diff_mm_long"] = out["ManagedMoney_LongPosition"] - out["sum/noncomm_positions_long_all"]
    out["diff_mm_short"] = out["ManagedMoney_ShortPosition"] - out["sum/noncomm_positions_short_all"]

    # Reorder columns for clarity
    out = out[[
        "tradeDate",
        # Commercial Long breakdown
        "CommercialLongPosition",
        "nymex_067651/prod_merc_positions_long",
        "ice_067411/prod_merc_positions_long",
        "sum/prod_merc_positions_long",
        "diff_comm_long",
        # Commercial Short breakdown
        "CommercialShortPosition",
        "nymex_067651/prod_merc_positions_short",
        "ice_067411/prod_merc_positions_short",
        "sum/prod_merc_positions_short",
        "diff_comm_short",
        # Commercial Net
        "Commercial_NetPosition",
        # ManagedMoney Long breakdown
        "ManagedMoney_LongPosition",
        "nymex_067651/noncomm_positions_long_all",
        "ice_067411/noncomm_positions_long_all",
        "sum/noncomm_positions_long_all",
        "diff_mm_long",
        # ManagedMoney Short breakdown
        "ManagedMoney_ShortPosition",
        "nymex_067651/noncomm_positions_short_all",
        "ice_067411/noncomm_positions_short_all",
        "sum/noncomm_positions_short_all",
        "diff_mm_short",
        # ManagedMoney Net
        "ManagedMoney_NetPosition",
    ]]

    out = out.sort_values("tradeDate").reset_index(drop=True)
    out.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved {len(out)} rows to {OUTPUT_PATH}")
    print(f"Date range: {out['tradeDate'].min().date()} to {out['tradeDate'].max().date()}")
    print()
    print("Column layout (sources: disaggregated_combined.csv + legacy_combined.csv):")
    print("  CommercialLongPosition  = nymex_067651/prod_merc_positions_long  + ice_067411/prod_merc_positions_long")
    print("  CommercialShortPosition = nymex_067651/prod_merc_positions_short + ice_067411/prod_merc_positions_short")
    print("  ManagedMoney_LongPosition  = nymex_067651/noncomm_positions_long_all  + ice_067411/noncomm_positions_long_all")
    print("  ManagedMoney_ShortPosition = nymex_067651/noncomm_positions_short_all + ice_067411/noncomm_positions_short_all")
    print()
    print("Diff stats:")
    for col in ["diff_comm_long", "diff_comm_short", "diff_mm_long", "diff_mm_short"]:
        vals = out[col].abs()
        exact = int((vals == 0).sum())
        near = int((vals <= 1).sum())
        print(f"  {col}: min={out[col].min()}, max={out[col].max()}, exact={exact}/{len(out)}, near(<=1)={near}/{len(out)}")


if __name__ == "__main__":
    main()
