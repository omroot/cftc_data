"""Data Guide page — explains COT report types, trader categories, and all commodities/contracts."""

from dash import html
import dash_bootstrap_components as dbc


def _section_header(title):
    return html.H5(title, className="mt-4 mb-2")


def _def_table(rows):
    """Render a two-column definition table."""
    _td_style = {"padding": "6px 10px", "borderBottom": "1px solid #eee", "verticalAlign": "top"}
    return html.Table(
        [html.Tbody([
            html.Tr([
                html.Td(html.Code(t) if isinstance(t, str) else t,
                         style={**_td_style, "whiteSpace": "nowrap", "fontWeight": "600", "minWidth": "180px"}),
                html.Td(d, style=_td_style),
            ]) for t, d in rows
        ])],
        style={"fontSize": "0.85rem", "width": "100%", "borderCollapse": "collapse"},
    )


# ── Report Types ─────────────────────────────────────────────────────────

_report_types_card = dbc.Card(
    dbc.CardBody([
        html.H4("COT Report Types", className="card-title"),
        html.P([
            "The CFTC publishes two main flavors of the weekly ",
            html.Strong("Commitments of Traders (COT)"),
            " report. Both cover the same underlying futures/options "
            "positions, but they differ in ",
            html.Em("how traders are classified"),
            ".",
        ]),

        _section_header("Aggregated (Legacy) Report"),
        html.P(
            "The original COT report, published since 1962. It groups all "
            "traders into just three broad categories:"
        ),
        _def_table([
            ("Commercial", [
                "Traders who use futures to hedge a physical business risk. "
                "For example, an oil producer hedging future production, or "
                "a refiner locking in feedstock costs. Commercials must file a ",
                html.Strong("CFTC Form 40"),
                " demonstrating a bona fide hedging purpose. They are often "
                "called 'hedgers' and tend to be ",
                html.Em("contrarian"),
                " — selling into rallies and buying dips because they are "
                "offsetting exposure in their physical operations.",
            ]),
            ("Non-Commercial", [
                "Large speculators — traders who do ",
                html.Em("not"),
                " qualify as commercial hedgers and hold positions above "
                "CFTC reportable thresholds. This bucket includes hedge funds, "
                "CTAs (commodity trading advisors), and proprietary trading firms. "
                "Often called 'large specs', they tend to be ",
                html.Em("trend-followers"),
                " and their net positioning is widely watched as a sentiment indicator.",
            ]),
            ("Non-Reportable", [
                "Small traders whose positions fall below the CFTC's reporting "
                "thresholds. Their positions are calculated as the residual: "
                "Total Open Interest minus (Commercial + Non-Commercial). "
                "Generally considered 'dumb money' — historically a useful "
                "contrarian indicator at extremes.",
            ]),
        ]),
        html.P([
            html.Strong("Data source: "),
            html.Code("legacy_combined.csv"),
            " — combined futures + options.",
        ], className="text-muted mt-3", style={"fontSize": "0.85rem"}),

        _section_header("Disaggregated Report"),
        html.P(
            "Introduced in 2009, this report splits the old 'Commercial' and "
            "'Non-Commercial' categories into finer groups, giving much better "
            "visibility into who is doing what:"
        ),
        _def_table([
            ("Producer/Merchant", [
                "Physical hedgers — the 'real economy' participants. Oil producers, "
                "miners, farmers, refiners, and physical commodity dealers. "
                "Equivalent to most of the old 'Commercial' category. Their "
                "positioning reflects physical supply/demand fundamentals.",
            ]),
            ("Swap Dealers", [
                "Banks and dealers who intermediate OTC swap exposure. A swap dealer "
                "might sell an OTC commodity swap to an airline, then hedge that "
                "exposure with an offsetting futures position. Their positioning "
                "reflects OTC flow rather than proprietary views. This category "
                "was previously lumped into 'Commercial' in the legacy report.",
            ]),
            ("Managed Money", [
                "Hedge funds, CTAs, and commodity pool operators who manage money "
                "for others. This is the most-watched category — it captures "
                "speculative/systematic flow. Roughly equivalent to the core of "
                "the old 'Non-Commercial' category, but cleaner because swap "
                "dealers have been separated out.",
            ]),
            ("Other Reportable", [
                "Large traders who don't fit the above three categories — "
                "e.g. treasury departments of non-financial corporates, or "
                "other large entities that don't qualify as producers, swap "
                "dealers, or managed money.",
            ]),
            ("Non-Reportable", [
                "Same as the legacy report — small traders below reporting "
                "thresholds, computed as the residual.",
            ]),
        ]),
        html.P([
            html.Strong("Data sources: "),
            html.Code("disaggregated_futures_only.csv"),
            " (futures only) and ",
            html.Code("disaggregated_combined.csv"),
            " (futures + options).",
        ], className="text-muted mt-3", style={"fontSize": "0.85rem"}),

        _section_header("Which Report Should I Use?"),
        _def_table([
            ("Disaggregated", [
                html.Strong("Recommended for most analysis. "),
                "The Managed Money category gives a cleaner read of speculative "
                "positioning than the legacy Non-Commercial bucket (which mixed "
                "specs with swap dealers). Use this for sentiment analysis, "
                "crowding signals, and z-score based indicators.",
            ]),
            ("Aggregated", [
                "Useful for longer historical analysis (data goes back to 1986 "
                "vs 2006 for disaggregated), and for markets where the "
                "commercial/speculator split is all you need. Also useful as a "
                "cross-check.",
            ]),
        ]),
    ]),
    className="shadow-sm mb-4",
)


# ── Contract Types ───────────────────────────────────────────────────────

_contract_types_card = dbc.Card(
    dbc.CardBody([
        html.H4("Contract Types", className="card-title"),
        html.P(
            "When viewing the disaggregated report, you can choose between "
            "two contract type breakdowns:"
        ),
        _def_table([
            ("Futures Only", [
                "Positions in futures contracts only. This is the ",
                html.Strong("most commonly used"),
                " view and is considered the 'cleaner' signal because futures "
                "positions are more directly tied to directional bets. Most "
                "analyst references to 'COT data' mean futures-only.",
            ]),
            ("Combined (F+O)", [
                "Futures plus delta-adjusted options positions combined. Options "
                "are converted to futures-equivalent contracts using their delta. "
                "This gives a more complete picture of total exposure, but can be "
                "noisier because options strategies (spreads, straddles) may not "
                "reflect directional intent.",
            ]),
        ]),
        html.P([
            html.Strong("Note: "),
            "The aggregated (legacy) report in this dashboard uses combined "
            "(futures + options) data only.",
        ], className="text-muted mt-3", style={"fontSize": "0.85rem"}),
    ]),
    className="shadow-sm mb-4",
)


# ── Key Metrics ──────────────────────────────────────────────────────────

_metrics_card = dbc.Card(
    dbc.CardBody([
        html.H4("Key Metrics Explained", className="card-title"),
        _def_table([
            ("Net Position", [
                "Long contracts minus Short contracts for a given trader category. "
                "A positive net means the group is net long (bullish); negative "
                "means net short (bearish). The absolute level matters less than "
                "the direction of change and how extreme it is relative to history.",
            ]),
            ("Open Interest (OI)", [
                "Total number of outstanding contracts (each contract has a long "
                "and a short side). Rising OI with rising prices = new money "
                "entering bullish bets. Falling OI with falling prices = longs "
                "liquidating.",
            ]),
            ("Net as % of OI", [
                "Net position divided by total open interest. Normalizes for "
                "market size differences. Useful for comparing positioning "
                "across commodities or across time as market size changes.",
            ]),
            ("Z-Score", [
                "How many standard deviations the current net position is from "
                "its rolling mean (configurable lookback). Values above +2 or "
                "below -2 indicate extreme positioning that historically tends "
                "to mean-revert. Commonly used as a contrarian signal.",
            ]),
            ("Concentration Ratios", [
                "Percentage of total open interest held by the top 4 (or top 8) "
                "largest traders, split by long and short. High concentration "
                "means a few players dominate — the market is more vulnerable "
                "to sharp moves if they unwind.",
            ]),
            ("WoW Change", [
                "Week-over-week change in net position. Shows the direction and "
                "magnitude of the latest flow. Large sudden changes often signal "
                "a positioning shift underway.",
            ]),
        ]),
    ]),
    className="shadow-sm mb-4",
)


# ── Commodity Groups ─────────────────────────────────────────────────────

_commodity_groups_card = dbc.Card(
    dbc.CardBody([
        html.H4("Commodity Groups", className="card-title"),
        html.P(
            "The CFTC organizes commodities into broad groups. The disaggregated "
            "report covers Agriculture and Natural Resources. The legacy report "
            "additionally includes Financial Instruments."
        ),

        _section_header("Agriculture"),
        html.P("Physical agricultural commodities and related products."),
        _def_table([
            ("CORN", "The most actively traded grain. Benchmark contract on CME. Used as feed, ethanol feedstock, and food."),
            ("SOYBEANS", "Key oilseed — crushed into soybean meal (animal feed) and soybean oil. Traded on CME."),
            ("SOYBEAN MEAL", "High-protein animal feed ingredient. A crush product of soybeans."),
            ("SOYBEAN OIL", "Edible oil and biodiesel feedstock. The other crush product."),
            ("WHEAT", "Multiple contracts: SRW (soft red winter, CME), HRW (hard red winter, KC), HRSpring (Minneapolis). Different grades for different end uses (bread, pastry, feed)."),
            ("COTTON", "Cotton No. 2 on ICE — benchmark for global cotton pricing."),
            ("SUGAR", "Sugar No. 11 on ICE — the global raw sugar benchmark. Brazil is the marginal producer."),
            ("COFFEE", "Coffee C on ICE — Arabica coffee benchmark. Highly weather-sensitive (Brazil frost risk)."),
            ("COCOA", "ICE Cocoa — priced in USD/tonne. West Africa (Ivory Coast, Ghana) dominates supply."),
            ("LIVE CATTLE", "CME live cattle — fed cattle ready for slaughter. Physical delivery."),
            ("FEEDER CATTLE", "CME feeder cattle — young cattle entering feedlots. Cash-settled."),
            ("LEAN HOGS", "CME lean hogs — cash-settled against the CME Lean Hog Index."),
            ("FROZEN CONCENTRATED ORANGE JUICE", "ICE FCOJ — a thin but volatile market driven by Florida weather."),
            ("OATS", "CME oats — a smaller grain market often used as a leading indicator for other grains."),
            ("RICE", "CME rough rice — the least liquid of the major grain contracts."),
            ("CANOLA AND PRODUCTS", "ICE Canada canola — a key oilseed for Canadian agriculture."),
            ("MILK", "CME milk futures — Class III (cheese), Class IV, and Non-Fat Dry Milk."),
            ("CHEESE", "CME cash-settled cheese and dry whey futures."),
            ("BUTTER", "CME cash-settled butter."),
            ("PALM OIL", "Malaysian palm oil calendar swap and crude palm oil contracts on CME."),
            ("LUMBER", "CME random length lumber — highly cyclical, tied to housing starts."),
            ("FERTILIZER", "CME urea (granular) FOB US Gulf — a newer contract tracking fertilizer costs."),
            ("FREIGHT RATE", "Dry bulk shipping indices — Capesize, Panamax, Supramax T/C averages."),
            ("PORK BELLIES", "The original 'belly' contract — now delisted but historical data remains."),
        ]),

        _section_header("Energy"),
        html.P("Crude oil, refined products, natural gas, and power."),
        _def_table([
            ("CRUDE OIL", [
                "The most important commodity. Multiple contracts exist:",
                html.Ul([
                    html.Li([html.Strong("WTI-PHYSICAL"), " — the main NYMEX WTI crude futures (CL). By far the most liquid, with 2M+ OI. Physical delivery at Cushing, OK. ", html.Em("This is the one to watch for directional positioning.")]),
                    html.Li([html.Strong("CRUDE OIL, LIGHT SWEET-WTI"), " — ICE WTI contract. Smaller but significant."]),
                    html.Li([html.Strong("BRENT LAST DAY"), " — ICE Brent crude. The global benchmark (used to price ~80% of world oil)."]),
                    html.Li([html.Strong("WTI Houston / WTI Midland"), " — basis/differential contracts reflecting regional pipeline logistics."]),
                    html.Li([html.Strong("WTI-BRENT CALENDAR"), " — spread between WTI and Brent."]),
                    html.Li([html.Strong("WTI FINANCIAL CRUDE OIL"), " — cash-settled financial WTI."]),
                    html.Li([html.Strong("CRUDE DIFF-WCS/TMX"), " — Canadian crude differentials (Western Canadian Select, Trans Mountain)."]),
                ]),
            ]),
            ("NATURAL GAS", [
                "Extensive set of contracts reflecting the complexity of the North American gas market:",
                html.Ul([
                    html.Li([html.Strong("HENRY HUB"), " — the benchmark NYMEX natural gas futures. Henry Hub, Louisiana is the pricing point for most US gas."]),
                    html.Li([html.Strong("Basis contracts"), " (WAHA, PERMIAN, SOCAL, PG&E, ALGONQUIN, etc.) — price differentials between regional hubs and Henry Hub. Reflect pipeline constraints and local supply/demand."]),
                    html.Li([html.Strong("DUTCH TTF"), " — European natural gas benchmark (Title Transfer Facility, Netherlands)."]),
                    html.Li([html.Strong("E-MINI NATURAL GAS"), " — smaller-sized contract for retail/smaller institutional participants."]),
                ]),
            ]),
            ("GASOLINE", [
                html.Strong("GASOLINE RBOB"),
                " — the main NYMEX gasoline futures (Reformulated Blendstock for Oxygenate Blending). "
                "Also includes RBOB calendar spreads, crack spreads (gasoline vs crude), and regional contracts.",
            ]),
            ("HEATING OIL-DIESEL-GASOIL", [
                html.Strong("NY HARBOR ULSD"),
                " — the main NYMEX ultra-low sulfur diesel contract. Also includes ICE gasoil (European diesel benchmark), "
                "Singapore gasoil, and various crack/basis spreads.",
            ]),
            ("ETHANOL", "CBT ethanol and related contracts — relevant for gasoline blending and corn demand."),
            ("FUEL OIL", "Residual fuel oil contracts across multiple regions — USGC, Singapore, Rotterdam. Includes marine fuel (0.5% sulfur) post-IMO 2020."),
            ("JET FUEL", "Gulf Coast and Singapore jet fuel/kerosene contracts."),
            ("NATURAL GAS LIQUIDS", "Propane (Mont Belvieu, Conway, Far East), butane, ethane, and natural gasoline. Critical for petrochemical and heating markets."),
            ("NAPHTHA", "European, Japanese, and Singapore naphtha — petrochemical feedstock and gasoline blending component."),
            ("ELECTRICITY", "Regional US power contracts — PJM, ERCOT, NYISO, ISO-NE, MISO, CAISO, and others. Peak and off-peak."),
            ("COAL", "Central Appalachian, API 2 (European), API 4 (South African), Powder River Basin thermal coal."),
            ("POLLUTION", "Carbon allowances (California Cap-and-Trade, RGGI, EU EUA), RECs (Renewable Energy Certificates), and RINs (Renewable Identification Numbers)."),
        ]),

        _section_header("Metals"),
        html.P("Precious and industrial metals."),
        _def_table([
            ("GOLD", [
                html.Strong("GOLD"),
                " — COMEX gold futures (GC). The dominant precious metals contract. Also includes Micro Gold (1/10 size).",
            ]),
            ("SILVER", [
                html.Strong("SILVER"),
                " — COMEX silver futures (SI). More volatile than gold, with both monetary and industrial demand. Also includes Micro Silver.",
            ]),
            ("COPPER", [
                html.Strong("COPPER-#1"),
                " — COMEX copper futures (HG). A key industrial/economic bellwether ('Dr. Copper'). Also includes Micro Copper.",
            ]),
            ("PLATINUM", "NYMEX platinum — auto catalyst and jewelry demand. Much smaller market than gold."),
            ("PALLADIUM", "NYMEX palladium — primarily auto catalyst demand (gasoline engines)."),
            ("ALUMINUM", "CME aluminum — includes LME-equivalent contracts and Midwest premium."),
            ("IRON ORE", "CME iron ore 62% Fe CFR China (TSI) — key steelmaking input."),
            ("STEEL", "CME hot-rolled coil steel — both North American and European contracts."),
            ("COBALT", "CME cobalt — battery/EV supply chain metal."),
            ("LITHIUM", "CME lithium hydroxide — battery/EV supply chain."),
            ("SCRAP METAL", "CME busheling ferrous scrap and steel scrap."),
        ]),

        _section_header("Financial Instruments (Legacy Report Only)"),
        html.P(
            "The aggregated report additionally covers financial futures — "
            "currencies, interest rates, equity indices, and cryptocurrencies. "
            "These are not available in the disaggregated report."
        ),
        _def_table([
            ("Currencies", "EUR, JPY, GBP, CAD, AUD, CHF, MXN, BRL, NZD, ZAR, and others."),
            ("Interest Rates", "Eurodollars, SOFR, Treasury bonds/notes (2Y, 5Y, 10Y, 30Y), interest rate swaps."),
            ("Equity Indices", "S&P 500 (E-mini and Micro), Nasdaq 100, Dow Jones, Russell 2000, VIX."),
            ("Crypto", "Bitcoin, Ether, and smaller coins (Litecoin, Cardano, Dogecoin, etc.)."),
        ]),
    ]),
    className="shadow-sm mb-4",
)


# ── How to Read COT Data ─────────────────────────────────────────────────

_how_to_read_card = dbc.Card(
    dbc.CardBody([
        html.H4("How to Read COT Data", className="card-title"),
        html.P(
            "The COT report is released every Friday at 3:30pm ET, covering "
            "positions as of the prior Tuesday. Here are the key things to look for:"
        ),
        html.Ul([
            html.Li([
                html.Strong("Managed Money net positioning: "),
                "The single most-watched number. Extreme net long = crowded bullish "
                "trade (contrarian bearish). Extreme net short = crowded bearish "
                "(contrarian bullish). Use the Z-Score to identify extremes.",
            ]),
            html.Li([
                html.Strong("Direction of weekly change: "),
                "Is managed money adding to longs (bullish flow) or to shorts "
                "(bearish flow)? A sustained trend of weekly additions in one "
                "direction confirms momentum.",
            ]),
            html.Li([
                html.Strong("Producer/Merchant positioning: "),
                "Producers are usually net short (hedging production). When "
                "producers reduce hedges (become less short), it can signal "
                "they expect lower prices and don't need to lock in current levels.",
            ]),
            html.Li([
                html.Strong("Open interest trends: "),
                "Rising OI + rising prices = new longs entering (bullish). "
                "Falling OI + falling prices = long liquidation (bearish but "
                "may be near exhaustion). Rising OI + falling prices = new shorts "
                "entering (bearish).",
            ]),
            html.Li([
                html.Strong("Concentration risk: "),
                "If the top 4 traders hold >40% of OI on one side, the market "
                "is vulnerable to sharp moves if they change position.",
            ]),
            html.Li([
                html.Strong("Longs vs Shorts separately: "),
                "Net position can mask what's actually happening. A net reduction "
                "could come from longs selling OR shorts covering — these have "
                "very different implications. Always check the long and short "
                "charts individually.",
            ]),
        ]),
    ]),
    className="shadow-sm mb-4",
)


# ── Caveats ──────────────────────────────────────────────────────────────

_caveats_card = dbc.Card(
    dbc.CardBody([
        html.H4("Caveats and Limitations", className="card-title"),
        html.Ul([
            html.Li([
                html.Strong("3-day lag: "),
                "Positions are as-of Tuesday, released Friday. By the time you "
                "see the data, the market may have moved significantly.",
            ]),
            html.Li([
                html.Strong("Classification is imperfect: "),
                "A bank classified as a 'Swap Dealer' may also run a prop desk. "
                "Categories reflect the entity's primary business, not necessarily "
                "the intent behind every position.",
            ]),
            html.Li([
                html.Strong("Net ≠ Directional: "),
                "A trader classified as 'long' in futures might be hedging a short "
                "OTC position. The COT data only shows exchange-traded positions.",
            ]),
            html.Li([
                html.Strong("ALL market aggregation: "),
                "When using the 'ALL' option in Market/Contract, positions are "
                "summed across all contracts for a commodity. This includes spreads "
                "and differentials, which may offset directional exposure. "
                "The benchmark contract (e.g. WTI-PHYSICAL) is usually more "
                "informative for directional analysis.",
            ]),
            html.Li([
                html.Strong("Not a timing tool: "),
                "COT data is best used for identifying positioning extremes and "
                "confirming trends, not for precise entry/exit timing.",
            ]),
        ]),
    ]),
    className="shadow-sm mb-4",
)


# ── Assembled Page ───────────────────────────────────────────────────────

page_data_guide = dbc.Container(
    fluid=True,
    children=[
        html.H3("CFTC Data Guide", className="mt-2 mb-1"),
        html.P("Understanding the Commitment of Traders reports, trader categories, "
               "and commodity markets.",
               className="text-muted mb-3", style={"fontSize": "0.9rem"}),
        _report_types_card,
        _contract_types_card,
        _metrics_card,
        _commodity_groups_card,
        _how_to_read_card,
        _caveats_card,
    ],
)
