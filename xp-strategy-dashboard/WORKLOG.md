# WORKLOG

## Phase 0 — data discovery
- Wrote `scripts/profile_data.py` (runs through the app's own loader) and
  generated `DATA_PROFILE.md` for all 15 sources.
- Findings: samples are 10-row extracts; `factor_zoo`/`consensus`/
  `singlename_flows` lost `(cod_ativo, data)` on export; the portfolio
  workbook embeds an `<EcoPortfolio>` JSON with the full weight history;
  `Performance` sheet blocks anchor on "Desde o início"; `bdr_market_data`
  numeric columns arrive as strings; `future_flows` is `;`-separated.

## Phase 1 — data layer
- `config.py` (DATA_SOURCE switch, cache dirs, TTLs), `data/catalog.py`
  (catalog-driven registry + vendored snapshot fallback), `data/loaders.py`
  (mode-aware type selection, disk cache, normalization, synthetic fallback,
  never raises), `data/transforms.py` (anchor parsing, flows, factor
  windows, joins), `data/demo.py` (coherent synthetic demo universe),
  `data/store.py` (cached getters + real-vs-synthetic policy + provenance).
- Verified portfolio parsing on the real workbook: 4 portfolios, 2,232
  weight observations, 66 monthly performance points.

## Phase 2 — pages
- 9 views: Cockpit, Flow Monitor (3 tabs), XP Portfolios, Factor Monitor,
  Valuation Screener, Short Interest, Research Coverage, Sector View,
  Data Health. Shared `components/ui.py` (KPI rows, provenance badges,
  formatting) and `components/charts.py` (palette-validated Plotly
  factories: line, signed bars, magnitude bars, heatmaps, scatter, area).

## Phase 3 — test & polish (3 rounds)
- Round 1: headless `AppTest` smoke of every page → fixed matplotlib
  dependency in Sector View.
- Round 2 (visual, via Playwright screenshots of the live app): replaced
  filename-based nav with `st.navigation` (proper titles/icons); fixed
  chart title/legend overlap; introduced neutral-blue magnitude bars so
  green/red stays signal-only; made the composition-history heatmap
  sequential/blank-aware; realistic demo days-to-cover; percent axes;
  coverage KPIs and upside logic (no real×synthetic joins).
- Round 3: re-screenshot verification; prod-mode smoke test (UNC paths
  unreachable → everything degrades to flagged synthetic without a crash);
  fixed one missing-column guard in XP Portfolios. Final state: 10/10 pages
  pass in `github` **and** `prod` mode.

## Phase 4 — docs & delivery
- README, ASSUMPTIONS, WORKLOG, requirements.txt; committed and pushed.
