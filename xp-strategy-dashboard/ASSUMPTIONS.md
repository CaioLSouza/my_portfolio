# ASSUMPTIONS — decisions taken autonomously (round 1)

Ordered roughly by impact. Each one is a default I chose so work could
continue without questions; all are easy to revisit next round.

1. **Project location.** Built inside `my_portfolio/xp-strategy-dashboard/`
   (this repo hosts the user's other projects). It is fully self-contained —
   copy the folder to the corporate machine as-is.
2. **Synthetic "demo universe" in dev mode.** The GitHub samples have only
   ~10 rows each, and three core panels (`factor_zoo`, `consensus`,
   `singlename_flows`) lost their `(cod_ativo, data)` index columns on
   export. Rather than show empty screens, in `DATA_SOURCE=github` the store
   substitutes a coherent generated market (~65 real B3 tickers, 3y of
   consistent prices/flows/shorts/consensus, real prod column names) whenever
   a sample is too thin (`<5` tickers for panels, `<40` rows for series).
   Every synthetic panel is badged **SYNTHETIC** with the reason, and the
   Data Health page lists real vs synthetic per source. In `prod` mode no
   substitution ever happens — only a *failed* load falls back (flagged).
   Real samples drive: `performance_carteiras`, `investors_participation`,
   `future_flows`, `comp_sheet`, `sector_classification`.
3. **Portfolio workbook parsing.** Composition history is read from the
   `<EcoPortfolio>` JSON blob embedded in each `Carteira - *` sheet header
   (found by regex anchor, not cell position) — it carries the full
   ticker × rebalance-date weight matrix. Monthly performance comes from the
   `Performance` sheet blocks anchored on the text "Desde o início"
   (rows below = portfolio then IBOV). The duplicated first date column in
   those blocks (which looks like YTD) is skipped; only unique month-end
   columns are kept. The `Desempenho *` sheets (weights again) and `Lâmina`
   were not parsed this round.
4. **Benchmark.** IBOV is treated as the benchmark for every portfolio
   (the workbook itself pairs each block with an IBOV row). Active bets =
   current portfolio weight − latest IBOV weight from `index_composition`.
5. **Analyst rec scale.** `analyst_rec` is assumed 1 = strong buy … 5 = sell
   (Refinitiv convention). COMP SHEET `RECOMMENDATION` uses its literal
   Buy/Neutral/Sell strings.
6. **Upside definition.** `TARGET / close_price − 1`. In dev mode the join
   between the *real* comp sheet and the *synthetic* price universe is
   suppressed (meaningless upside); prod joins `market_data` close.
7. **Factor windows.** Trailing 1M/3M/6M/YTD/12M computed from the
   cumulative factor indices (base 1); family metrics are the plain mean of
   the family's factor columns (`-ALL` variants, both constrained and
   unconstrained, weighted equally).
8. **Flows.** Cash-market net flow = `*_purchases − *_sales` per investor
   group. Futures net = `CAPT_LIQ` summed by `categoria_investidor` (all
   `macro_produto` values pooled). Single-name flow normalizations use the
   precomputed `_to_adtv` / `_to_ff` columns as-is.
9. **Cache policy.** 15-min in-memory TTL (`st.cache_data`) + downloaded
   sample files kept 24 h in `./.cache` (github mode only). Prod reads the
   UNC file directly on cache miss; no local copy of corporate data is
   persisted beyond process memory.
10. **UI language/format.** All UI in English, `1,234.5` number format,
    green/red used exclusively for sign (gains/losses, in/outflows);
    series identity uses a colorblind-validated blue/aqua/yellow/violet/
    magenta/orange order.
11. **BDRs.** No dedicated page this round (lowest-value module); the source
    is still loaded, health-checked and available via the data layer.
12. **`sheets` handling.** For multi-sheet sources the loader returns all
    sheets; pages use `Daily`/`Cumulative` (investors_participation) and
    `Top`/`Bottom`/`LS` (factor_returns) by name and fall back gracefully if
    a sheet is missing.
13. **catalog fallback.** A snapshot of `catalog.csv` is vendored at
    `data/catalog_snapshot.csv` so the app boots offline (and in prod, which
    never touches the network); github mode refreshes it from the raw URL
    when reachable.
