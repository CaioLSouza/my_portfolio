"""What the pages call: cached, provenance-aware data getters.

Policy (github/dev mode only): if a sample loads but is too thin to drive a
page — missing the `(cod_ativo, data)` index columns, a single ticker, or a
handful of rows — the store substitutes the coherent demo universe from
``data/demo.py`` and marks the result ``synthetic``. In prod mode no
substitution happens: a thin file is shown as-is and only a *failed* load
falls back to synthetic data (clearly flagged), so the app never crashes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import streamlit as st

import config
from data import demo, transforms
from data.loaders import LoadResult, get_catalog, load_source

MIN_ROWS = 40          # a time series shorter than this can't drive window charts
MIN_TICKERS = 5        # a panel needs a cross-section


@dataclass
class Provenance:
    key: str
    mode: str
    origin: str           # 'real' | 'synthetic'
    reason: str = ""      # why synthetic, if synthetic
    location: str = ""
    last_modified: str = ""
    n_rows: int = 0
    as_of: str = ""       # max date observed in the data

    @property
    def is_synthetic(self) -> bool:
        return self.origin == "synthetic"


def _as_of(obj: Any) -> str:
    frames = obj.values() if isinstance(obj, dict) else [obj]
    best: Optional[pd.Timestamp] = None
    for df in frames:
        if not isinstance(df, pd.DataFrame):
            continue
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                mx = df[col].max()
                if pd.notna(mx) and (best is None or mx > best):
                    best = mx
    return f"{best:%Y-%m-%d}" if best is not None else "n/a"


def _too_thin(key: str, res: LoadResult) -> str:
    """Return a reason string if the sample can't drive its pages, else ''."""
    df = res.df
    if key in ("factor_zoo", "consensus", "singlename_flows", "short_selling",
               "market_data", "market_cap", "index_composition"):
        if "cod_ativo" not in df.columns:
            return "sample lost the (cod_ativo, data) index columns"
        if df["cod_ativo"].nunique() < MIN_TICKERS:
            return f"sample has only {df['cod_ativo'].nunique()} ticker(s)"
    if key in ("factor_returns", "sector_index"):
        if len(df) < MIN_ROWS:
            return f"sample has only {len(df)} rows"
    if key == "bdr_market_data" and ("Ativo" not in df.columns or
                                     df["Ativo"].nunique() < 2):
        return "sample has a single BDR"
    return ""


def _provenance(key: str, res: LoadResult, origin: str, reason: str,
                data: Any) -> Provenance:
    return Provenance(
        key=key,
        mode=config.DATA_SOURCE,
        origin=origin,
        reason=reason,
        location=res.meta.location,
        last_modified=(f"{res.meta.last_modified:%Y-%m-%d %H:%M}"
                       if res.meta.last_modified else ""),
        n_rows=sum(len(v) for v in data.values()) if isinstance(data, dict)
        else len(data),
        as_of=_as_of(data),
    )


@st.cache_data(ttl=config.MEMORY_TTL_SECONDS, show_spinner="Loading data…")
def get_source(key: str) -> Tuple[Any, Provenance]:
    """Load one source with the real-vs-synthetic policy applied.

    Returns (data, provenance) where data is a DataFrame or, for multi-sheet
    sources, a dict of DataFrames.
    """
    res = load_source(key)
    multi_sheet = key in ("investors_participation", "factor_returns")

    def _real_payload() -> Any:
        return res.sheets if (multi_sheet and res.sheets) else res.df

    if res.meta.is_synthetic:  # file unreachable in either mode
        gen = demo.GENERATORS.get(key)
        data = gen() if gen else res.df
        return data, _provenance(key, res, "synthetic",
                                 f"load failed: {res.meta.error}", data)

    if config.DATA_SOURCE == "github":
        reason = _too_thin(key, res)
        if reason and key in demo.GENERATORS:
            data = demo.GENERATORS[key]()
            return data, _provenance(key, res, "synthetic", reason, data)

    data = _real_payload()
    return data, _provenance(key, res, "real", "", data)


# --------------------------------------------------------------------------
# derived, page-level getters (all cached via get_source)
# --------------------------------------------------------------------------

def get_sectors() -> Tuple[pd.DataFrame, Provenance]:
    data, prov = get_source("sector_classification")
    df = data if isinstance(data, pd.DataFrame) else next(iter(data.values()))
    return df, prov


@st.cache_data(ttl=config.MEMORY_TTL_SECONDS)
def get_sector_indices() -> Tuple[pd.DataFrame, Provenance]:
    df, prov = get_source("sector_index")
    return df, prov


@st.cache_data(ttl=config.MEMORY_TTL_SECONDS)
def get_screener() -> Tuple[pd.DataFrame, Dict[str, Provenance]]:
    """factor_zoo latest snapshot + consensus + sectors, joined on cod_ativo."""
    fz, p1 = get_source("factor_zoo")
    cons, p2 = get_source("consensus")
    sec, p3 = get_sectors()
    snap = transforms.latest_snapshot(fz) if "data" in fz.columns else fz.copy()
    if "cod_ativo" in cons.columns:
        cons_snap = transforms.latest_snapshot(cons)
        overlap = [c for c in cons_snap.columns
                   if c in snap.columns and c != "cod_ativo"]
        snap = snap.merge(cons_snap.drop(columns=overlap), on="cod_ativo",
                          how="left")
    snap = transforms.add_sector(snap, sec)
    # the thin real sector sample may not cover a synthetic universe —
    # fall back to the demo taxonomy so sector filters stay usable
    if ("macro_sector_xp" not in snap.columns
            or snap["macro_sector_xp"].isna().mean() > 0.5):
        snap = snap.drop(columns=[c for c in ("macro_sector_xp", "sector_xp",
                                              "GICS_sector", "name")
                                  if c in snap.columns])
        snap = transforms.add_sector(snap, demo.sector_classification())
    return snap, {"factor_zoo": p1, "consensus": p2, "sector_classification": p3}


@st.cache_data(ttl=config.MEMORY_TTL_SECONDS)
def get_portfolios() -> Tuple[Dict[str, pd.DataFrame], Provenance]:
    """Parsed portfolio composition history + monthly performance blocks."""
    data, prov = get_source("performance_carteiras")
    if prov.is_synthetic and isinstance(data, dict) and "composition" in data:
        hist = data["composition"].assign(date=pd.Timestamp.today().normalize())
        perf = data["performance"].melt(
            id_vars=["portfolio", "date"], var_name="series",
            value_name="monthly_return")
        perf["series"] = perf["series"].map(
            {"portfolio_return": "TOP Ações XP", "benchmark_return": "IBOV"})
        return {"history": hist, "performance": perf}, prov
    # real workbook: raw sheets came back from the loader
    res = load_source("performance_carteiras")
    hist = transforms.parse_portfolio_history(res.sheets)
    perf = transforms.parse_performance_blocks(res.sheets)
    out = {"history": hist, "performance": perf}
    prov.as_of = _as_of(out)  # freshness of the *parsed* data, not sheet 1
    prov.n_rows = len(hist) + len(perf)
    return out, prov


def all_provenance() -> Dict[str, Provenance]:
    out = {}
    for key in get_catalog():
        try:
            _, prov = get_source(key)
            out[key] = prov
        except Exception as exc:  # noqa: BLE001
            out[key] = Provenance(key=key, mode=config.DATA_SOURCE,
                                  origin="synthetic", reason=str(exc))
    return out
