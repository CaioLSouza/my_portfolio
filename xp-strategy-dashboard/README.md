# XP Equity Strategy Cockpit

Internal dashboard for the XP Equity Strategy/Quant desk: market flows,
recommended-portfolio performance, factor monitor, valuation & consensus
screener, short interest, research coverage and sector views — one
Streamlit app, driven by the desk's 15 data sources.

## Quick start (development / personal machine)

```bash
pip install -r requirements.txt
streamlit run app.py            # DATA_SOURCE defaults to "github"
```

The app downloads small public samples from the
[`CaioLSouza/datasets`](https://github.com/CaioLSouza/datasets) repo
(branch `claude/s3-link-access-nzk1gb`, folder `xp-strategy-dashboard/`),
caching them in `./.cache`. Panels whose sample is too thin to be useful run
on clearly-badged **SYNTHETIC** demo data — see the *Data Health* page for a
per-source breakdown.

## Production (XP corporate Windows machine)

**Full step-by-step guide (install options, offline pip, preflight,
troubleshooting): [`DEPLOYMENT.md`](DEPLOYMENT.md).** Short version:

```bat
python scripts\check_prod_env.py   :: preflight: packages + \\xpdocs access
start_dashboard.bat                :: sets DATA_SOURCE=prod and launches
```

In `prod` mode every source is read directly from its UNC path
(`\\xpdocs\...`) as listed in the catalog — parquet/xlsx/xlsm/csv chosen per
source — and the app performs **zero network calls**. All access is
read-only; nothing is ever written to the share and no data leaves the
machine. If a file is locked or missing the panel degrades to a flagged
fallback instead of crashing.

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `DATA_SOURCE` | `github` | `github` = public samples (dev) · `prod` = corporate UNC paths |
| `XPSD_TTL` | `900` | in-memory cache TTL, seconds |
| `XPSD_DISK_TTL` | `86400` | max age of downloaded sample files in `./.cache`, seconds |

## Layout

```
app.py                  # st.navigation router
config.py               # mode switch, cache config, catalog locations
data/
  catalog.py            # catalog.csv -> SourceSpec registry (single source of truth for paths)
  catalog_snapshot.csv  # vendored offline fallback of the catalog
  loaders.py            # resilient mode-aware loaders + disk cache + synthetic fallback
  transforms.py         # anchor parsing (portfolio workbook), flows, factor windows, joins
  demo.py               # coherent synthetic demo universe (dev only, always badged)
  store.py              # cached page-facing getters with provenance
components/             # ui helpers (KPI rows, badges) and Plotly chart factories
views/                  # one file per dashboard module (9 pages)
scripts/
  profile_data.py       # Phase 0 profiler -> DATA_PROFILE.md
  smoke_test.py         # headless AppTest run of every page
```

## Docs

- `PLAN.md` — architecture and phase plan
- `DATA_PROFILE.md` — profiled schema of all 15 sources
- `ASSUMPTIONS.md` — every decision taken autonomously in round 1
- `WORKLOG.md` — what was done, phase by phase

## Testing

```bash
python scripts/smoke_test.py                    # dev mode, all pages
DATA_SOURCE=prod python scripts/smoke_test.py   # prod-mode degradation path
python scripts/profile_data.py                  # regenerate DATA_PROFILE.md
```
