"""Schema-level transforms: they operate on column names, never on the data
mode, so they behave identically on GitHub samples and prod files.

Includes the anchor-based parser for the report-style
``performance_carteiras`` workbook (merged cells, shifted headers): blocks
are located by *text anchors* — the ``<EcoPortfolio>`` JSON header, the
"Ticker" header cell, the "Desde o início" performance header — never by
fixed cell positions.
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# generic helpers
# --------------------------------------------------------------------------

def filter_dates(df: pd.DataFrame, start, end,
                 date_col: str = "date") -> pd.DataFrame:
    """Rows whose date_col falls inside [start, end] (inclusive)."""
    if date_col not in df.columns or df.empty:
        return df
    d = pd.to_datetime(df[date_col])
    return df[(d >= pd.Timestamp(start)) & (d <= pd.Timestamp(end))]


def latest_snapshot(df: pd.DataFrame, date_col: str = "data",
                    by: str = "cod_ativo") -> pd.DataFrame:
    """Most recent row per ticker (panel -> cross-section)."""
    if date_col not in df.columns or by not in df.columns:
        return df
    return df.sort_values(date_col).groupby(by, as_index=False).tail(1)


def add_sector(df: pd.DataFrame, sectors: pd.DataFrame,
               ticker_col: str = "cod_ativo") -> pd.DataFrame:
    """Join the XP sector taxonomy on cod_ativo (master join key)."""
    if sectors.empty or "cod_ativo" not in sectors.columns:
        return df
    cols = [c for c in ("cod_ativo", "name", "macro_sector_xp", "sector_xp",
                        "GICS_sector") if c in sectors.columns]
    right = sectors[cols].drop_duplicates("cod_ativo")
    return df.merge(right, left_on=ticker_col, right_on="cod_ativo",
                    how="left", suffixes=("", "_sec"))


def window_returns(series: pd.Series, dates: pd.Series) -> Dict[str, float]:
    """Trailing-window returns for an index/level series (1m/3m/6m/YTD/12m)."""
    s = pd.Series(series.values, index=pd.to_datetime(dates.values)).dropna().sort_index()
    if len(s) < 2:
        return {}
    last_date, last = s.index[-1], s.iloc[-1]
    out: Dict[str, float] = {}
    for label, days in (("1M", 30), ("3M", 91), ("6M", 182), ("12M", 365)):
        past = s[s.index <= last_date - pd.Timedelta(days=days)]
        if len(past):
            out[label] = last / past.iloc[-1] - 1
    ytd = s[s.index < pd.Timestamp(year=last_date.year, month=1, day=1)]
    if len(ytd):
        out["YTD"] = last / ytd.iloc[-1] - 1
    return out


# --------------------------------------------------------------------------
# flows
# --------------------------------------------------------------------------

PARTICIPANT_GROUPS = ("foreign_investors", "institutional_investors",
                      "individual_investors", "financial_institutions", "others")


def net_participation(df: pd.DataFrame) -> pd.DataFrame:
    """B3 cash-market net flow per investor group (purchases - sales)."""
    if "date" not in df.columns:
        return pd.DataFrame()
    out = pd.DataFrame({"date": pd.to_datetime(df["date"])})
    for g in PARTICIPANT_GROUPS:
        p, s = f"{g}_purchases", f"{g}_sales"
        if p in df.columns and s in df.columns:
            out[g] = df[p] - df[s]
    return out


def futures_net_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Futures-market net inflow (CAPT_LIQ) pivoted by investor category."""
    need = {"data_pregao", "categoria_investidor", "CAPT_LIQ"}
    if not need.issubset(df.columns):
        return pd.DataFrame()
    pv = (df.pivot_table(index="data_pregao", columns="categoria_investidor",
                         values="CAPT_LIQ", aggfunc="sum").sort_index())
    return pv


def top_singlename_flows(df: pd.DataFrame, investor: str = "foreigners",
                         window: str = "21d", metric: str = "flow",
                         n: int = 15) -> pd.DataFrame:
    """Largest inflows/outflows per ticker for one investor/window."""
    col = f"{window}_{investor}_{metric}" if metric == "flow" else \
        f"{window}_{investor}_flow_{metric}"
    if col not in df.columns or "cod_ativo" not in df.columns:
        return pd.DataFrame()
    snap = latest_snapshot(df)[["cod_ativo", col]].dropna()
    snap = snap.rename(columns={col: "value"})
    top = snap.nlargest(n, "value")
    bottom = snap.nsmallest(n, "value")
    return pd.concat([top, bottom]).drop_duplicates("cod_ativo").sort_values("value")


# --------------------------------------------------------------------------
# factors
# --------------------------------------------------------------------------

def factor_family_table(ls: pd.DataFrame) -> pd.DataFrame:
    """Per-factor trailing returns from the LS (long-short) index sheet."""
    if "data" not in ls.columns:
        return pd.DataFrame()
    rows: List[dict] = []
    for col in ls.columns:
        if col == "data" or "/" not in str(col):
            continue
        fam, factor = str(col).split("/", 1)
        wr = window_returns(ls[col], ls["data"])
        if not wr:
            continue
        rows.append({"family": fam, "factor": factor.replace("-ALL", ""), **wr})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# valuation / coverage
# --------------------------------------------------------------------------

def comp_sheet_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Identity + valuation columns of the comp sheet, with upside."""
    keep = [c for c in ("TICKER", "NAME", "SECTOR_XP", "LEAD_ANALYST", "PDATE",
                        "RECOMMENDATION", "RESTRICTED", "TARGET", "KE", "KD",
                        "WACC", "close_price") if c in df.columns]
    out = df[keep].copy()
    if {"TARGET", "close_price"}.issubset(out.columns):
        out["upside"] = out["TARGET"] / out["close_price"] - 1
    return out


# --------------------------------------------------------------------------
# performance_carteiras — anchor-based parsing
# --------------------------------------------------------------------------

_ECO_RE = re.compile(r"<EcoPortfolio>(\{.*\})", re.DOTALL)


def _parse_ecoportfolio_blob(text: str) -> Optional[pd.DataFrame]:
    """Extract the ticker x rebalance-date weight matrix embedded as JSON in
    the header cell of each ``Carteira - *`` sheet."""
    m = _ECO_RE.search(text)
    if not m:
        return None
    try:
        blob = json.loads(m.group(1))
        data = blob["data"]
        header, rows = data[0], data[1:]
        dates = [h for h in header[1:] if h]
        recs = []
        for row in rows:
            ticker = row[0]
            if not ticker:
                continue
            for dt, w in zip(dates, row[1:]):
                if w is not None:
                    recs.append({"ticker": ticker, "date": pd.Timestamp(dt),
                                 "weight": float(w),
                                 "portfolio": blob.get("name", "?")})
        return pd.DataFrame(recs) if recs else None
    except Exception:
        return None


def parse_portfolio_history(sheets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Composition history (ticker, date, weight, portfolio) from every
    ``Carteira - *`` sheet's EcoPortfolio JSON."""
    frames = []
    for name, df in sheets.items():
        if not str(name).startswith("Carteira"):
            continue
        for cell in map(str, df.columns[:3]):
            parsed = _parse_ecoportfolio_blob(cell)
            if parsed is not None:
                frames.append(parsed)
                break
        else:
            # JSON may sit in a data cell rather than the header
            head = df.head(3).astype(str)
            for cell in head.values.ravel():
                parsed = _parse_ecoportfolio_blob(cell)
                if parsed is not None:
                    frames.append(parsed)
                    break
    if not frames:
        return pd.DataFrame(columns=["ticker", "date", "weight", "portfolio"])
    return pd.concat(frames, ignore_index=True)


def parse_performance_blocks(sheets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Monthly performance blocks from the ``Performance`` sheet.

    Anchor: any row whose second cell is 'Desde o início' is a header row;
    the following rows (until a blank) are series (portfolio, then IBOV).
    Returns tidy rows: (portfolio, series, date, monthly_return, inception_return).
    """
    perf = None
    for name, df in sheets.items():
        if str(name).strip().lower() == "performance":
            perf = df
            break
    if perf is None:
        return pd.DataFrame()
    grid = perf.copy()
    grid.columns = range(grid.shape[1])
    # ensure header text rows are part of the grid (loader may have promoted them)
    records = []
    arr = grid.values
    n_rows, n_cols = arr.shape
    r = 0
    while r < n_rows:
        row = arr[r]
        anchor_cols = [c for c in range(n_cols)
                       if isinstance(row[c], str) and "desde o in" in row[c].strip().lower()]
        if not anchor_cols:
            r += 1
            continue
        a = anchor_cols[0]
        date_cols = [(c, pd.to_datetime(row[c], errors="coerce"))
                     for c in range(a + 1, n_cols)]
        date_cols = [(c, d) for c, d in date_cols if pd.notna(d)]
        rr = r + 1
        block_name = None
        while rr < n_rows:
            label = arr[rr][a - 1] if a >= 1 else None
            if not isinstance(label, str) or not label.strip():
                break
            label = re.sub(r"\s+", " ", label).strip()
            if block_name is None:
                block_name = label
            series = "IBOV" if label.upper().startswith("IBOV") else block_name
            inception = pd.to_numeric(arr[rr][a], errors="coerce")
            seen = set()
            for c, d in date_cols:
                if d in seen:
                    continue  # duplicated first column (YTD) — keep monthly only
                seen.add(d)
                val = pd.to_numeric(arr[rr][c], errors="coerce")
                if pd.notna(val):
                    records.append({"portfolio": block_name, "series": series,
                                    "date": d, "monthly_return": float(val),
                                    "inception_return": float(inception)
                                    if pd.notna(inception) else np.nan})
            rr += 1
        r = rr + 1
    return pd.DataFrame(records)


def current_composition(history: pd.DataFrame) -> pd.DataFrame:
    """Latest rebalance-date weights per portfolio."""
    if history.empty:
        return history
    out = []
    for pf, grp in history.groupby("portfolio"):
        last = grp["date"].max()
        cur = grp[grp["date"] == last].copy()
        cur = cur[cur["weight"] > 0]
        out.append(cur)
    return pd.concat(out, ignore_index=True) if out else history.iloc[0:0]
