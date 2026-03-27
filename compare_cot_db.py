"""Compare cot_db.csv (from Marouen/Bloomberg) against CFTC downloads for WTI (CL).

Mapping discovered:
- cot_db "Commercial" = Disaggregated Combined Prod/Merch (NYMEX 067651 + ICE 067411)
- cot_db "ManagedMoney" = Legacy Combined NonCommercial (NYMEX 067651 + ICE 067411)

This is a Bloomberg hybrid: it uses the disaggregated Prod/Merch definition for
"Commercial" and the legacy NonCommercial definition for "ManagedMoney", both from
the combined (futures + options) report, summing NYMEX WTI and ICE Brent.
"""

import pandas as pd

COT_DB_PATH = "cftc_downloads/from_marouen/cot_db.csv"
CFTC_LEGACY_COMBINED_PATH = "cftc_downloads/legacy_combined.csv"
CFTC_DISAGG_COMBINED_PATH = "cftc_downloads/disaggregated_combined.csv"
OUTPUT_PATH = "cftc_downloads/cot_db_comparison.csv"

NYMEX_WTI_CODE = "067651"
ICE_BRENT_CODE = "067411"


def load_and_sum(path, code_col, date_col, value_cols):
    """Load a CFTC dataset, filter to WTI+Brent, and sum NYMEX+ICE per date."""
    df = pd.read_csv(path, low_memory=False)
    df[date_col] = pd.to_datetime(df[date_col])

    for col in value_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    nymex = df[df[code_col] == NYMEX_WTI_CODE][[date_col] + value_cols].copy()
    ice = df[df[code_col] == ICE_BRENT_CODE][[date_col] + value_cols].copy()

    merged = pd.merge(nymex, ice, on=date_col, suffixes=("_nymex", "_ice"))
    for col in value_cols:
        merged[col] = merged[f"{col}_nymex"] + merged[f"{col}_ice"]

    return merged[[date_col] + value_cols]


def main():
    # Load cot_db CL data
    db = pd.read_csv(COT_DB_PATH)
    db["tradeDate"] = pd.to_datetime(db["tradeDate"])
    cl = db[db["Name"] == "CL"].dropna(subset=["ManagedMoney_LongPosition"]).copy()

    # ManagedMoney = Legacy Combined NonCommercial (NYMEX + ICE)
    legacy_cols = ["noncomm_positions_long_all", "noncomm_positions_short_all"]
    legacy = load_and_sum(
        CFTC_LEGACY_COMBINED_PATH, "cftc_contract_market_code",
        "report_date_as_yyyy_mm_dd", legacy_cols,
    )

    # Commercial = Disagg Combined Prod/Merch (NYMEX + ICE)
    disagg_cols = ["prod_merc_positions_long", "prod_merc_positions_short"]
    disagg = load_and_sum(
        CFTC_DISAGG_COMBINED_PATH, "cftc_contract_market_code",
        "report_date_as_yyyy_mm_dd", disagg_cols,
    )

    # Merge everything on date
    comp = pd.merge(
        cl[["tradeDate", "Commercial_NetPosition", "CommercialLongPosition",
            "CommercialShortPosition", "ManagedMoney_NetPosition",
            "ManagedMoney_LongPosition", "ManagedMoney_ShortPosition"]],
        legacy, left_on="tradeDate", right_on="report_date_as_yyyy_mm_dd", how="inner",
    )
    comp = pd.merge(
        comp, disagg, left_on="tradeDate", right_on="report_date_as_yyyy_mm_dd", how="inner",
    )

    # Build output with original column names
    out = pd.DataFrame()
    out["date"] = comp["tradeDate"]

    # Commercial
    out["CommercialLongPosition"] = comp["CommercialLongPosition"]
    out["prod_merc_positions_long"] = comp["prod_merc_positions_long"]
    out["diff_comm_long"] = comp["CommercialLongPosition"] - comp["prod_merc_positions_long"]

    out["CommercialShortPosition"] = comp["CommercialShortPosition"]
    out["prod_merc_positions_short"] = comp["prod_merc_positions_short"]
    out["diff_comm_short"] = comp["CommercialShortPosition"] - comp["prod_merc_positions_short"]

    out["Commercial_NetPosition"] = comp["Commercial_NetPosition"]
    out["prod_merc_net_computed"] = comp["prod_merc_positions_long"] - comp["prod_merc_positions_short"]
    out["diff_comm_net"] = comp["Commercial_NetPosition"] - out["prod_merc_net_computed"]

    # Managed Money
    out["ManagedMoney_LongPosition"] = comp["ManagedMoney_LongPosition"]
    out["noncomm_positions_long_all"] = comp["noncomm_positions_long_all"]
    out["diff_mm_long"] = comp["ManagedMoney_LongPosition"] - comp["noncomm_positions_long_all"]

    out["ManagedMoney_ShortPosition"] = comp["ManagedMoney_ShortPosition"]
    out["noncomm_positions_short_all"] = comp["noncomm_positions_short_all"]
    out["diff_mm_short"] = comp["ManagedMoney_ShortPosition"] - comp["noncomm_positions_short_all"]

    out["ManagedMoney_NetPosition"] = comp["ManagedMoney_NetPosition"]
    out["noncomm_net_computed"] = comp["noncomm_positions_long_all"] - comp["noncomm_positions_short_all"]
    out["diff_mm_net"] = comp["ManagedMoney_NetPosition"] - out["noncomm_net_computed"]

    out = out.sort_values("date").reset_index(drop=True)
    out.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved {len(out)} rows to {OUTPUT_PATH}")
    print(f"Date range: {out['date'].min().date()} to {out['date'].max().date()}")
    print(f"\nMapping:")
    print(f"  Commercial   = Disagg Combined Prod/Merch (NYMEX WTI + ICE Brent)")
    print(f"  ManagedMoney = Legacy Combined NonCommercial (NYMEX WTI + ICE Brent)")
    print(f"\nDiff stats:")
    for col in [c for c in out.columns if c.startswith("diff_")]:
        vals = out[col].abs()
        exact = int((vals <= 1).sum())
        print(f"  {col}: min={out[col].min()}, max={out[col].max()}, exact(<=1)={exact}/{len(out)}")


if __name__ == "__main__":
    main()
