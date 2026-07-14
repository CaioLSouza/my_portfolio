# PLAN — XP Equity Strategy Dashboard

## Goal
Internal "cockpit" dashboard for the XP Equity Strategy/Quant desk consolidating:
market flows, recommended-portfolio performance, factor performance, valuation &
consensus, short interest, sector views and research coverage — in a single
Streamlit multipage app.

## Environments (one codebase, two modes)
| Mode | Where | Data origin | File types |
|---|---|---|---|
| `DATA_SOURCE=github` (default) | personal machine (dev) | raw.githubusercontent.com samples | xlsx/csv |
| `DATA_SOURCE=prod` | XP corporate Windows box | UNC paths `\\xpdocs\...` | parquet/xlsx/xlsm/csv |

The runtime source of truth is `catalog.csv` (fetched from GitHub in dev; bundled
copy used as fallback). No hardcoded data paths outside the catalog. All reads are
read-only; cache lives in `./.cache` inside the project folder; no data ever leaves
the machine in prod mode (in prod the app performs zero network calls).

## Architecture
```
app.py                    # entrypoint: Cockpit (overview) + global styling
config.py                 # DATA_SOURCE switch, cache dir, TTLs, catalog locations
data/
  catalog.py              # loads catalog.csv -> SourceSpec registry (15 sources)
  loaders.py              # resilient per-type loaders; mode-aware type selection;
                          # two-layer cache (st.cache_data + ./.cache on disk);
                          # synthetic-mock fallback with is_synthetic flag
  transforms.py           # schema-level transforms: sector joins, flow aggregations,
                          # factor window returns, upside calc, portfolio parsing
pages/
  1_Flow_Monitor.py       # cash-market participation, futures flows, single-name flows
  2_XP_Portfolios.py      # portfolio composition, performance vs IBOV, active bets
  3_Factor_Monitor.py     # factor family returns across windows, LS spreads, rotation
  4_Valuation_Screener.py # single-name screener: P/E fwd, EV/EBITDA fwd, yields, recs
  5_Short_Interest.py     # most shorted, days-to-cover, lending rate, 1m changes
  6_Research_Coverage.py  # comp sheet: rec distribution, upside vs target, by analyst
  7_Sector_View.py        # per-macro-sector aggregates (valuation, flow, performance)
  8_Data_Health.py        # per-source status: mode, rows, last update, synthetic flag
components/
  ui.py                   # KPI cards, section headers, formatting helpers, theming
  charts.py               # plotly chart factories (consistent palette/layout)
scripts/
  profile_data.py         # Phase 0 profiler -> DATA_PROFILE.md
```

## Key decisions
1. **Streamlit + pandas + plotly** — per prompt default; corporate-friendly, no JS build.
2. **Catalog-driven registry.** `data/catalog.py` parses catalog.csv into `SourceSpec`
   dataclasses; the loader picks parser by `prod_filetype` vs `sample_filetype`
   depending on mode. A vendored `catalog.csv` snapshot ships in the repo as offline
   fallback (github mode still refreshes it from the raw URL when reachable).
3. **Resilience contract.** Every load returns `LoadResult(df, meta)`; on failure the
   loader logs, generates a small synthetic frame matching the expected schema, and
   sets `meta.is_synthetic=True` so every page can badge "SYNTHETIC DATA".
4. **Defensive schemas.** Samples may lack the `(cod_ativo, data)` index columns that
   prod parquets have. Loaders normalize: if index cols exist as index, reset them;
   if missing, continue with what's there. Transforms check column presence before use.
5. **performance_carteiras parsed by text anchors** (portfolio names, header rows),
   never fixed cell positions.
6. **UI entirely in English**, international number format, sober palette,
   green/red only as signal. Dense, executive layout.

## Phases
0. Data discovery → `DATA_PROFILE.md` (profile all 15 samples).
1. Data layer: config + catalog + loaders + transforms; unit smoke tests.
2. Pages: Cockpit + 7 thematic modules + Data Health.
3. Self-review loops: run app headless, click through pages via HTTP checks,
   fix errors; 2–3 visual polish passes.
4. Docs (`README`, `ASSUMPTIONS`, `WORKLOG`), `requirements.txt`, commit & push.

## Non-goals (this round)
- BDR module beyond a basic table (optional source, low value density).
- Authentication, deployment automation, scheduled refresh.
- Writing anything to the corporate network.
