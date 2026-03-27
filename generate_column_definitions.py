"""Generate a CSV mapping each column of the CFTC Disaggregated Combined report
to its official definition (from CFTC explanatory notes).

Reads the actual column headers from disaggregated_combined.csv and pairs them
with hand-curated definitions sourced from:
  https://www.cftc.gov/idc/groups/public/@commitmentsoftraders/documents/file/disaggregatedcotexplanatorynot.pdf
  https://www.cftc.gov/MarketReports/CommitmentsofTraders/ExplanatoryNotes/index.htm
"""

import csv

CFTC_PATH = "cftc_downloads/disaggregated_combined.csv"
OUTPUT_PATH = "cftc_downloads/disaggregated_combined_column_definitions.csv"

# --------------------------------------------------------------------------- #
# Definitions keyed by column name.
#
# Trader categories (from the CFTC disaggregated explanatory notes PDF):
#   Producer/Merchant/Processor/User — entities that predominantly produce,
#       process, pack, or handle a physical commodity and hedge via futures.
#   Swap Dealer — entities dealing primarily in swaps, using futures to hedge
#       swap exposure. Counterparties may be speculative or commercial.
#   Managed Money (Money Manager) — registered CTAs, CPOs, or unregistered
#       funds managing organised futures trading on behalf of clients.
#   Other Reportables — every other reportable trader not in the above three.
#
# Crop-year breakdown:
#   All   = all contract months combined.
#   Old   = old (expiring) crop year; for non-ag commodities may equal "All".
#   Other = remaining contract months not in "Old".
#
# Spreading — offsetting long and short positions in different calendar months,
#   or offsetting futures and options in the same or different months.
#   Reported for Swap Dealers, Managed Money, and Other Reportables only.
#   Producer/Merchant positions are reported long or short only (no spreading).
# --------------------------------------------------------------------------- #

DEFINITIONS = {
    # ── Identifiers ──────────────────────────────────────────────────────────
    "id": ("Identifier", "All", "Unique record identifier."),
    "market_and_exchange_names": ("Identifier", "All", "Full name of the market and exchange."),
    "report_date_as_yyyy_mm_dd": ("Identifier", "All", "Report date (each Tuesday's open interest, published Friday)."),
    "yyyy_report_week_ww": ("Identifier", "All", "Year and week number of the report."),
    "contract_market_name": ("Identifier", "All", "Name of the contract market."),
    "cftc_contract_market_code": ("Identifier", "All", "CFTC code for the contract market."),
    "cftc_market_code": ("Identifier", "All", "CFTC market code."),
    "cftc_region_code": ("Identifier", "All", "CFTC region code."),
    "cftc_commodity_code": ("Identifier", "All", "CFTC commodity code."),
    "commodity_name": ("Identifier", "All", "Name of the commodity."),

    # ── Positions — All months ───────────────────────────────────────────────
    "open_interest_all": ("Open Interest", "All", "Total open interest (all contract months). Options converted to futures-equivalent using delta factors."),
    "prod_merc_positions_long": ("Positions", "All", "Producer/Merchant/Processor/User long positions. Entities that predominantly produce, process, pack, or handle a physical commodity and hedge risks via futures."),
    "prod_merc_positions_short": ("Positions", "All", "Producer/Merchant/Processor/User short positions."),
    "swap_positions_long_all": ("Positions", "All", "Swap Dealer long positions. Entities dealing primarily in swaps for a commodity, using futures to hedge swap exposure."),
    "swap__positions_short_all": ("Positions", "All", "Swap Dealer short positions."),
    "swap__positions_spread_all": ("Positions", "All", "Swap Dealer spreading positions. Offsetting long and short positions in different calendar months, or offsetting futures and options."),
    "m_money_positions_long_all": ("Positions", "All", "Managed Money (Money Manager) long positions. Registered CTAs, CPOs, or unregistered funds managing organized futures trading on behalf of clients."),
    "m_money_positions_short_all": ("Positions", "All", "Managed Money short positions."),
    "m_money_positions_spread": ("Positions", "All", "Managed Money spreading positions. Offsetting long and short positions in different calendar months."),
    "other_rept_positions_long": ("Positions", "All", "Other Reportables long positions. Every other reportable trader not classified as Producer/Merchant, Swap Dealer, or Money Manager."),
    "other_rept_positions_short": ("Positions", "All", "Other Reportables short positions."),
    "other_rept_positions_spread": ("Positions", "All", "Other Reportables spreading positions."),
    "tot_rept_positions_long_all": ("Positions", "All", "Total Reportable long positions (sum of all four categories including spreading)."),
    "tot_rept_positions_short": ("Positions", "All", "Total Reportable short positions (sum of all four categories including spreading)."),
    "nonrept_positions_long_all": ("Positions", "All", "Nonreportable long positions. Derived: open_interest_all minus tot_rept_positions_long_all."),
    "nonrept_positions_short_all": ("Positions", "All", "Nonreportable short positions. Derived: open_interest_all minus tot_rept_positions_short."),

    # ── Positions — Old crop year ────────────────────────────────────────────
    "open_interest_old": ("Open Interest", "Old Crop", "Total open interest (old crop year months only). Applies to commodities with defined marketing seasons."),
    "prod_merc_positions_long_1": ("Positions", "Old Crop", "Producer/Merchant long positions (old crop year)."),
    "prod_merc_positions_short_1": ("Positions", "Old Crop", "Producer/Merchant short positions (old crop year)."),
    "swap_positions_long_old": ("Positions", "Old Crop", "Swap Dealer long positions (old crop year)."),
    "swap__positions_short_old": ("Positions", "Old Crop", "Swap Dealer short positions (old crop year)."),
    "swap__positions_spread_old": ("Positions", "Old Crop", "Swap Dealer spreading positions (old crop year)."),
    "m_money_positions_long_old": ("Positions", "Old Crop", "Managed Money long positions (old crop year)."),
    "m_money_positions_short_old": ("Positions", "Old Crop", "Managed Money short positions (old crop year)."),
    "m_money_positions_spread_1": ("Positions", "Old Crop", "Managed Money spreading positions (old crop year)."),
    "other_rept_positions_long_1": ("Positions", "Old Crop", "Other Reportables long positions (old crop year)."),
    "other_rept_positions_short_1": ("Positions", "Old Crop", "Other Reportables short positions (old crop year)."),
    "other_rept_positions_spread_1": ("Positions", "Old Crop", "Other Reportables spreading positions (old crop year)."),
    "tot_rept_positions_long_old": ("Positions", "Old Crop", "Total Reportable long positions (old crop year)."),
    "tot_rept_positions_short_1": ("Positions", "Old Crop", "Total Reportable short positions (old crop year)."),
    "nonrept_positions_long_old": ("Positions", "Old Crop", "Nonreportable long positions (old crop year)."),
    "nonrept_positions_short_old": ("Positions", "Old Crop", "Nonreportable short positions (old crop year)."),

    # ── Positions — Other crop year ──────────────────────────────────────────
    "open_interest_other": ("Open Interest", "Other Crop", "Total open interest (other crop year months)."),
    "prod_merc_positions_long_2": ("Positions", "Other Crop", "Producer/Merchant long positions (other crop year)."),
    "prod_merc_positions_short_2": ("Positions", "Other Crop", "Producer/Merchant short positions (other crop year)."),
    "swap_positions_long_other": ("Positions", "Other Crop", "Swap Dealer long positions (other crop year)."),
    "swap__positions_short_other": ("Positions", "Other Crop", "Swap Dealer short positions (other crop year)."),
    "swap__positions_spread_other": ("Positions", "Other Crop", "Swap Dealer spreading positions (other crop year)."),
    "m_money_positions_long_other": ("Positions", "Other Crop", "Managed Money long positions (other crop year)."),
    "m_money_positions_short_other": ("Positions", "Other Crop", "Managed Money short positions (other crop year)."),
    "m_money_positions_spread_2": ("Positions", "Other Crop", "Managed Money spreading positions (other crop year)."),
    "other_rept_positions_long_2": ("Positions", "Other Crop", "Other Reportables long positions (other crop year)."),
    "other_rept_positions_short_2": ("Positions", "Other Crop", "Other Reportables short positions (other crop year)."),
    "other_rept_positions_spread_2": ("Positions", "Other Crop", "Other Reportables spreading positions (other crop year)."),
    "tot_rept_positions_long_other": ("Positions", "Other Crop", "Total Reportable long positions (other crop year)."),
    "tot_rept_positions_short_2": ("Positions", "Other Crop", "Total Reportable short positions (other crop year)."),
    "nonrept_positions_long_other": ("Positions", "Other Crop", "Nonreportable long positions (other crop year)."),
    "nonrept_positions_short_other": ("Positions", "Other Crop", "Nonreportable short positions (other crop year)."),

    # ── Percent of OI — All months ───────────────────────────────────────────
    "pct_of_open_interest_all": ("Pct of OI", "All", "Percent of total open interest (always 100.0)."),
    "pct_of_oi_prod_merc_long": ("Pct of OI", "All", "% of OI: Producer/Merchant long."),
    "pct_of_oi_prod_merc_short": ("Pct of OI", "All", "% of OI: Producer/Merchant short."),
    "pct_of_oi_swap_long_all": ("Pct of OI", "All", "% of OI: Swap Dealer long."),
    "pct_of_oi_swap_short_all": ("Pct of OI", "All", "% of OI: Swap Dealer short."),
    "pct_of_oi_swap_spread_all": ("Pct of OI", "All", "% of OI: Swap Dealer spreading."),
    "pct_of_oi_m_money_long_all": ("Pct of OI", "All", "% of OI: Managed Money long."),
    "pct_of_oi_m_money_short_all": ("Pct of OI", "All", "% of OI: Managed Money short."),
    "pct_of_oi_m_money_spread": ("Pct of OI", "All", "% of OI: Managed Money spreading."),
    "pct_of_oi_other_rept_long": ("Pct of OI", "All", "% of OI: Other Reportables long."),
    "pct_of_oi_other_rept_short": ("Pct of OI", "All", "% of OI: Other Reportables short."),
    "pct_of_oi_other_rept_spread": ("Pct of OI", "All", "% of OI: Other Reportables spreading."),
    "pct_of_oi_tot_rept_long_all": ("Pct of OI", "All", "% of OI: Total Reportable long."),
    "pct_of_oi_tot_rept_short": ("Pct of OI", "All", "% of OI: Total Reportable short."),
    "pct_of_oi_nonrept_long_all": ("Pct of OI", "All", "% of OI: Nonreportable long."),
    "pct_of_oi_nonrept_short_all": ("Pct of OI", "All", "% of OI: Nonreportable short."),

    # ── Percent of OI — Old crop year ────────────────────────────────────────
    "pct_of_open_interest_old": ("Pct of OI", "Old Crop", "Percent of old crop open interest (always 100.0)."),
    "pct_of_oi_prod_merc_long_1": ("Pct of OI", "Old Crop", "% of OI: Producer/Merchant long (old crop)."),
    "pct_of_oi_prod_merc_short_1": ("Pct of OI", "Old Crop", "% of OI: Producer/Merchant short (old crop)."),
    "pct_of_oi_swap_long_old": ("Pct of OI", "Old Crop", "% of OI: Swap Dealer long (old crop)."),
    "pct_of_oi_swap_short_old": ("Pct of OI", "Old Crop", "% of OI: Swap Dealer short (old crop)."),
    "pct_of_oi_swap_spread_old": ("Pct of OI", "Old Crop", "% of OI: Swap Dealer spreading (old crop)."),
    "pct_of_oi_m_money_long_old": ("Pct of OI", "Old Crop", "% of OI: Managed Money long (old crop)."),
    "pct_of_oi_m_money_short_old": ("Pct of OI", "Old Crop", "% of OI: Managed Money short (old crop)."),
    "pct_of_oi_m_money_spread_1": ("Pct of OI", "Old Crop", "% of OI: Managed Money spreading (old crop)."),
    "pct_of_oi_other_rept_long_1": ("Pct of OI", "Old Crop", "% of OI: Other Reportables long (old crop)."),
    "pct_of_oi_other_rept_short_1": ("Pct of OI", "Old Crop", "% of OI: Other Reportables short (old crop)."),
    "pct_of_oi_other_rept_spread_1": ("Pct of OI", "Old Crop", "% of OI: Other Reportables spreading (old crop)."),
    "pct_of_oi_tot_rept_long_old": ("Pct of OI", "Old Crop", "% of OI: Total Reportable long (old crop)."),
    "pct_of_oi_tot_rept_short_1": ("Pct of OI", "Old Crop", "% of OI: Total Reportable short (old crop)."),
    "pct_of_oi_nonrept_long_old": ("Pct of OI", "Old Crop", "% of OI: Nonreportable long (old crop)."),
    "pct_of_oi_nonrept_short_old": ("Pct of OI", "Old Crop", "% of OI: Nonreportable short (old crop)."),

    # ── Percent of OI — Other crop year ──────────────────────────────────────
    "pct_of_open_interest_other": ("Pct of OI", "Other Crop", "Percent of other crop open interest (always 100.0)."),
    "pct_of_oi_prod_merc_long_2": ("Pct of OI", "Other Crop", "% of OI: Producer/Merchant long (other crop)."),
    "pct_of_oi_prod_merc_short_2": ("Pct of OI", "Other Crop", "% of OI: Producer/Merchant short (other crop)."),
    "pct_of_oi_swap_long_other": ("Pct of OI", "Other Crop", "% of OI: Swap Dealer long (other crop)."),
    "pct_of_oi_swap_short_other": ("Pct of OI", "Other Crop", "% of OI: Swap Dealer short (other crop)."),
    "pct_of_oi_swap_spread_other": ("Pct of OI", "Other Crop", "% of OI: Swap Dealer spreading (other crop)."),
    "pct_of_oi_m_money_long_other": ("Pct of OI", "Other Crop", "% of OI: Managed Money long (other crop)."),
    "pct_of_oi_m_money_short_other": ("Pct of OI", "Other Crop", "% of OI: Managed Money short (other crop)."),
    "pct_of_oi_m_money_spread_2": ("Pct of OI", "Other Crop", "% of OI: Managed Money spreading (other crop)."),
    "pct_of_oi_other_rept_long_2": ("Pct of OI", "Other Crop", "% of OI: Other Reportables long (other crop)."),
    "pct_of_oi_other_rept_short_2": ("Pct of OI", "Other Crop", "% of OI: Other Reportables short (other crop)."),
    "pct_of_oi_other_rept_spread_2": ("Pct of OI", "Other Crop", "% of OI: Other Reportables spreading (other crop)."),
    "pct_of_oi_tot_rept_long_other": ("Pct of OI", "Other Crop", "% of OI: Total Reportable long (other crop)."),
    "pct_of_oi_tot_rept_short_2": ("Pct of OI", "Other Crop", "% of OI: Total Reportable short (other crop)."),
    "pct_of_oi_nonrept_long_other": ("Pct of OI", "Other Crop", "% of OI: Nonreportable long (other crop)."),
    "pct_of_oi_nonrept_short_other": ("Pct of OI", "Other Crop", "% of OI: Nonreportable short (other crop)."),

    # ── Number of Traders — All months ───────────────────────────────────────
    "traders_tot_all": ("Traders", "All", "Total number of reportable traders (all months)."),
    "traders_prod_merc_long_all": ("Traders", "All", "Number of Producer/Merchant traders long."),
    "traders_prod_merc_short_all": ("Traders", "All", "Number of Producer/Merchant traders short."),
    "traders_swap_long_all": ("Traders", "All", "Number of Swap Dealer traders long."),
    "traders_swap_short_all": ("Traders", "All", "Number of Swap Dealer traders short."),
    "traders_swap_spread_all": ("Traders", "All", "Number of Swap Dealer traders spreading."),
    "traders_m_money_long_all": ("Traders", "All", "Number of Managed Money traders long."),
    "traders_m_money_short_all": ("Traders", "All", "Number of Managed Money traders short."),
    "traders_m_money_spread_all": ("Traders", "All", "Number of Managed Money traders spreading."),
    "traders_other_rept_long_all": ("Traders", "All", "Number of Other Reportable traders long."),
    "traders_other_rept_short": ("Traders", "All", "Number of Other Reportable traders short."),
    "traders_other_rept_spread": ("Traders", "All", "Number of Other Reportable traders spreading."),
    "traders_tot_rept_long_all": ("Traders", "All", "Total reportable traders long."),
    "traders_tot_rept_short_all": ("Traders", "All", "Total reportable traders short."),

    # ── Number of Traders — Old crop year ────────────────────────────────────
    "traders_tot_old": ("Traders", "Old Crop", "Total number of reportable traders (old crop)."),
    "traders_prod_merc_long_old": ("Traders", "Old Crop", "Number of Producer/Merchant traders long (old crop)."),
    "traders_prod_merc_short_old": ("Traders", "Old Crop", "Number of Producer/Merchant traders short (old crop)."),
    "traders_swap_long_old": ("Traders", "Old Crop", "Number of Swap Dealer traders long (old crop)."),
    "traders_swap_short_old": ("Traders", "Old Crop", "Number of Swap Dealer traders short (old crop)."),
    "traders_swap_spread_old": ("Traders", "Old Crop", "Number of Swap Dealer traders spreading (old crop)."),
    "traders_m_money_long_old": ("Traders", "Old Crop", "Number of Managed Money traders long (old crop)."),
    "traders_m_money_short_old": ("Traders", "Old Crop", "Number of Managed Money traders short (old crop)."),
    "traders_m_money_spread_old": ("Traders", "Old Crop", "Number of Managed Money traders spreading (old crop)."),
    "traders_other_rept_long_old": ("Traders", "Old Crop", "Number of Other Reportable traders long (old crop)."),
    "traders_other_rept_short_1": ("Traders", "Old Crop", "Number of Other Reportable traders short (old crop)."),
    "traders_other_rept_spread_1": ("Traders", "Old Crop", "Number of Other Reportable traders spreading (old crop)."),
    "traders_tot_rept_long_old": ("Traders", "Old Crop", "Total reportable traders long (old crop)."),
    "traders_tot_rept_short_old": ("Traders", "Old Crop", "Total reportable traders short (old crop)."),

    # ── Number of Traders — Other crop year ──────────────────────────────────
    "traders_tot_other": ("Traders", "Other Crop", "Total number of reportable traders (other crop)."),
    "traders_prod_merc_long_other": ("Traders", "Other Crop", "Number of Producer/Merchant traders long (other crop)."),
    "traders_prod_merc_short_other": ("Traders", "Other Crop", "Number of Producer/Merchant traders short (other crop)."),
    "traders_swap_long_other": ("Traders", "Other Crop", "Number of Swap Dealer traders long (other crop)."),
    "traders_swap_short_other": ("Traders", "Other Crop", "Number of Swap Dealer traders short (other crop)."),
    "traders_swap_spread_other": ("Traders", "Other Crop", "Number of Swap Dealer traders spreading (other crop)."),
    "traders_m_money_long_other": ("Traders", "Other Crop", "Number of Managed Money traders long (other crop)."),
    "traders_m_money_short_other": ("Traders", "Other Crop", "Number of Managed Money traders short (other crop)."),
    "traders_m_money_spread_other": ("Traders", "Other Crop", "Number of Managed Money traders spreading (other crop)."),
    "traders_other_rept_long_other": ("Traders", "Other Crop", "Number of Other Reportable traders long (other crop)."),
    "traders_other_rept_short_2": ("Traders", "Other Crop", "Number of Other Reportable traders short (other crop)."),
    "traders_other_rept_spread_2": ("Traders", "Other Crop", "Number of Other Reportable traders spreading (other crop)."),
    "traders_tot_rept_long_other": ("Traders", "Other Crop", "Total reportable traders long (other crop)."),
    "traders_tot_rept_short_other": ("Traders", "Other Crop", "Total reportable traders short (other crop)."),

    # ── Concentration Ratios — All months ────────────────────────────────────
    "conc_gross_le_4_tdr_long": ("Concentration", "All", "% of OI held by largest 4 traders gross long."),
    "conc_gross_le_4_tdr_short": ("Concentration", "All", "% of OI held by largest 4 traders gross short."),
    "conc_gross_le_8_tdr_long": ("Concentration", "All", "% of OI held by largest 8 traders gross long."),
    "conc_gross_le_8_tdr_short": ("Concentration", "All", "% of OI held by largest 8 traders gross short."),
    "conc_net_le_4_tdr_long_all": ("Concentration", "All", "% of OI held by largest 4 traders net long."),
    "conc_net_le_4_tdr_short_all": ("Concentration", "All", "% of OI held by largest 4 traders net short."),
    "conc_net_le_8_tdr_long_all": ("Concentration", "All", "% of OI held by largest 8 traders net long."),
    "conc_net_le_8_tdr_short_all": ("Concentration", "All", "% of OI held by largest 8 traders net short."),

    # ── Concentration Ratios — Old crop year ─────────────────────────────────
    "conc_gross_le_4_tdr_long_1": ("Concentration", "Old Crop", "% of OI held by largest 4 traders gross long (old crop)."),
    "conc_gross_le_4_tdr_short_1": ("Concentration", "Old Crop", "% of OI held by largest 4 traders gross short (old crop)."),
    "conc_gross_le_8_tdr_long_1": ("Concentration", "Old Crop", "% of OI held by largest 8 traders gross long (old crop)."),
    "conc_gross_le_8_tdr_short_1": ("Concentration", "Old Crop", "% of OI held by largest 8 traders gross short (old crop)."),
    "conc_net_le_4_tdr_long_old": ("Concentration", "Old Crop", "% of OI held by largest 4 traders net long (old crop)."),
    "conc_net_le_4_tdr_short_old": ("Concentration", "Old Crop", "% of OI held by largest 4 traders net short (old crop)."),
    "conc_net_le_8_tdr_long_old": ("Concentration", "Old Crop", "% of OI held by largest 8 traders net long (old crop)."),
    "conc_net_le_8_tdr_short_old": ("Concentration", "Old Crop", "% of OI held by largest 8 traders net short (old crop)."),

    # ── Concentration Ratios — Other crop year ───────────────────────────────
    "conc_gross_le_4_tdr_long_2": ("Concentration", "Other Crop", "% of OI held by largest 4 traders gross long (other crop)."),
    "conc_gross_le_4_tdr_short_2": ("Concentration", "Other Crop", "% of OI held by largest 4 traders gross short (other crop)."),
    "conc_gross_le_8_tdr_long_2": ("Concentration", "Other Crop", "% of OI held by largest 8 traders gross long (other crop)."),
    "conc_gross_le_8_tdr_short_2": ("Concentration", "Other Crop", "% of OI held by largest 8 traders gross short (other crop)."),
    "conc_net_le_4_tdr_long_other": ("Concentration", "Other Crop", "% of OI held by largest 4 traders net long (other crop)."),
    "conc_net_le_4_tdr_short_other": ("Concentration", "Other Crop", "% of OI held by largest 4 traders net short (other crop)."),
    "conc_net_le_8_tdr_long_other": ("Concentration", "Other Crop", "% of OI held by largest 8 traders net long (other crop)."),
    "conc_net_le_8_tdr_short_other": ("Concentration", "Other Crop", "% of OI held by largest 8 traders net short (other crop)."),

    # ── Metadata ─────────────────────────────────────────────────────────────
    "contract_units": ("Metadata", "All", "Units of the contract (e.g. 1,000 BARRELS)."),
    "cftc_subgroup_code": ("Metadata", "All", "CFTC subgroup classification code."),
    "commodity": ("Metadata", "All", "Commodity name (short form)."),
    "commodity_subgroup_name": ("Metadata", "All", "Commodity subgroup (e.g. Crude Oil, Natural Gas)."),
    "commodity_group_name": ("Metadata", "All", "Commodity group (e.g. Petroleum and Products, Natural Gas and Related)."),
    "futonly_or_combined": ("Metadata", "All", "Whether row is futures-only (FutOnly) or futures-and-options combined (FutOpCombined). In the combined report, options are converted to futures-equivalent using exchange-supplied delta factors."),

    # ── Week-over-week Changes ───────────────────────────────────────────────
    "change_in_open_interest_all": ("Changes", "All", "Week-over-week change in total open interest."),
    "change_in_prod_merc_long": ("Changes", "All", "Week-over-week change in Producer/Merchant long positions."),
    "change_in_prod_merc_short": ("Changes", "All", "Week-over-week change in Producer/Merchant short positions."),
    "change_in_swap_long_all": ("Changes", "All", "Week-over-week change in Swap Dealer long positions."),
    "change_in_swap_short_all": ("Changes", "All", "Week-over-week change in Swap Dealer short positions."),
    "change_in_swap_spread_all": ("Changes", "All", "Week-over-week change in Swap Dealer spreading positions."),
    "change_in_m_money_long_all": ("Changes", "All", "Week-over-week change in Managed Money long positions."),
    "change_in_m_money_short_all": ("Changes", "All", "Week-over-week change in Managed Money short positions."),
    "change_in_m_money_spread": ("Changes", "All", "Week-over-week change in Managed Money spreading positions."),
    "change_in_other_rept_long": ("Changes", "All", "Week-over-week change in Other Reportables long positions."),
    "change_in_other_rept_short": ("Changes", "All", "Week-over-week change in Other Reportables short positions."),
    "change_in_other_rept_spread": ("Changes", "All", "Week-over-week change in Other Reportables spreading positions."),
    "change_in_tot_rept_long_all": ("Changes", "All", "Week-over-week change in Total Reportable long positions."),
    "change_in_tot_rept_short": ("Changes", "All", "Week-over-week change in Total Reportable short positions."),
    "change_in_nonrept_long_all": ("Changes", "All", "Week-over-week change in Nonreportable long positions."),
    "change_in_nonrept_short_all": ("Changes", "All", "Week-over-week change in Nonreportable short positions."),
}


def main():
    # Read column headers from the actual CFTC file
    with open(CFTC_PATH, "r") as f:
        reader = csv.reader(f)
        headers = next(reader)

    # Write definitions CSV
    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["column_number", "column_name", "category", "crop_year", "definition"])

        for i, col_name in enumerate(headers, start=1):
            if col_name in DEFINITIONS:
                category, crop_year, definition = DEFINITIONS[col_name]
            else:
                category, crop_year, definition = ("Unknown", "", f"No definition found for '{col_name}'.")
            writer.writerow([i, col_name, category, crop_year, definition])

    print(f"Wrote {len(headers)} column definitions to {OUTPUT_PATH}")

    # Sanity check: flag any columns missing from the definitions dict
    missing = [h for h in headers if h not in DEFINITIONS]
    if missing:
        print(f"\nWARNING: {len(missing)} columns not in definitions dict:")
        for m in missing:
            print(f"  - {m}")
    else:
        print("All columns matched.")


if __name__ == "__main__":
    main()
