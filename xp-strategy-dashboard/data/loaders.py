"""Resilient, mode-aware loaders for every catalog source.

Contract: ``load_source(key)`` never raises. It returns a ``LoadResult``
whose ``meta`` records where the data came from, when, and whether it is a
synthetic stand-in (``is_synthetic=True``) generated because the real file
was unreachable. Pages surface that flag instead of crashing.

Two cache layers:
- disk (``./.cache``): github mode stores the downloaded raw file (age-based
  invalidation); prod mode is a direct local read so no disk copy is made.
- memory: Streamlit ``st.cache_data`` wrappers live in ``data/store.py``.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

import config
from data.catalog import SourceSpec, load_catalog

log = logging.getLogger(__name__)


@dataclass
class LoadMeta:
    key: str
    mode: str
    location: str
    filetype: str
    loaded_at: datetime
    last_modified: Optional[datetime] = None
    n_rows: int = 0
    is_synthetic: bool = False
    error: str = ""


@dataclass
class LoadResult:
    df: pd.DataFrame
    meta: LoadMeta
    sheets: Dict[str, pd.DataFrame] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.meta.is_synthetic and self.meta.error == ""


# --------------------------------------------------------------------------
# file acquisition
# --------------------------------------------------------------------------

def _cached_download(spec: SourceSpec) -> Path:
    """Download the sample file to ./.cache (github mode), reusing fresh copies."""
    ext = spec.sample_filetype.strip().lower()
    target = config.CACHE_DIR / f"{spec.key}.{ext}"
    if target.exists():
        age = time.time() - target.stat().st_mtime
        if age < config.DISK_CACHE_MAX_AGE_SECONDS:
            return target
    import requests

    resp = requests.get(spec.github_raw_url, timeout=config.REQUEST_TIMEOUT_SECONDS)
    resp.raise_for_status()
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_bytes(resp.content)
    tmp.replace(target)
    return target


def _resolve_local_path(spec: SourceSpec) -> Path:
    """Return a local filesystem path for the source in the current mode."""
    if config.DATA_SOURCE == "prod":
        return Path(spec.prod_path)  # UNC path; direct read-only access
    try:
        return _cached_download(spec)
    except Exception:
        # offline fallback: reuse a stale cached copy if one exists
        ext = spec.sample_filetype.strip().lower()
        stale = config.CACHE_DIR / f"{spec.key}.{ext}"
        if stale.exists():
            log.warning("%s: download failed, using stale cache", spec.key)
            return stale
        raise


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------

DATE_COLUMN_CANDIDATES = ("data", "date", "data_pregao", "dt", "pdate")


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Schema-defensive cleanup applied to every tabular source.

    Prod parquets are often indexed by (cod_ativo, data); samples may carry
    those as plain columns or not at all. Normalize to plain columns and
    parse the obvious date columns.
    """
    if isinstance(df.index, pd.MultiIndex) or df.index.name:
        df = df.reset_index()
    df.columns = [str(c).strip() for c in df.columns]
    # drop unnamed export artifacts (e.g. "Unnamed: 0" from Excel dumps)
    junk = [c for c in df.columns if c.lower().startswith("unnamed:")]
    if junk:
        first = junk[0]
        # keep a nameless first column if it looks like data (dates/tickers)
        if first == df.columns[0] and df[first].notna().mean() > 0.9:
            df = df.rename(columns={first: "index_col"})
            junk = junk[1:]
        df = df.drop(columns=junk, errors="ignore")
    for col in df.columns:
        if col.lower() in DATE_COLUMN_CANDIDATES or col == "index_col":
            parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")
            if parsed.notna().mean() > 0.8:
                df[col] = parsed
                if col == "index_col":
                    df = df.rename(columns={"index_col": "date"})
    return df


def _read_csv(path: Path, spec: SourceSpec) -> pd.DataFrame:
    sep = spec.csv_sep or ","
    try:
        df = pd.read_csv(path, sep=sep)
    except Exception:
        df = pd.read_csv(path, sep=None, engine="python")  # sniff separator
    if df.shape[1] == 1 and sep == ",":
        # wrong separator in catalog — retry with ';'
        df = pd.read_csv(path, sep=";")
    return df


def _read_excel_all(path: Path) -> Dict[str, pd.DataFrame]:
    return pd.read_excel(path, sheet_name=None, engine="openpyxl")


def _parse_file(path: Path, spec: SourceSpec) -> LoadResult:
    ftype = spec.filetype
    sheets: Dict[str, pd.DataFrame] = {}
    if ftype in ("xlsx", "xlsm"):
        raw_sheets = _read_excel_all(path)
        if spec.key == "performance_carteiras":
            # report-style workbook: keep sheets raw, anchor-parsing happens
            # in transforms.parse_portfolios (merged cells, shifted headers)
            sheets = raw_sheets
            first = next(iter(raw_sheets.values())) if raw_sheets else pd.DataFrame()
            df = first
        else:
            sheets = {name: _normalize(sdf) for name, sdf in raw_sheets.items()}
            df = next(iter(sheets.values())) if sheets else pd.DataFrame()
    elif ftype == "parquet":
        df = _normalize(pd.read_parquet(path))
    elif ftype == "csv":
        df = _normalize(_read_csv(path, spec))
    else:
        raise ValueError(f"Unsupported filetype '{ftype}' for {spec.key}")

    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        mtime = None
    meta = LoadMeta(
        key=spec.key,
        mode=config.DATA_SOURCE,
        location=spec.location,
        filetype=ftype,
        loaded_at=datetime.now(),
        last_modified=mtime,
        n_rows=len(df),
    )
    return LoadResult(df=df, meta=meta, sheets=sheets)


# --------------------------------------------------------------------------
# synthetic fallbacks
# --------------------------------------------------------------------------

def _synthetic(spec: SourceSpec, error: str) -> LoadResult:
    """Small schema-shaped mock so pages render with a SYNTHETIC badge."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=30)
    tickers = ["AAAA3", "BBBB4", "CCCC3", "DDDD11", "EEEE3"]
    generic = pd.DataFrame(
        {
            "cod_ativo": np.repeat(tickers, len(dates)),
            "data": np.tile(dates, len(tickers)),
            "value": rng.normal(0, 1, len(tickers) * len(dates)).cumsum(),
        }
    )
    meta = LoadMeta(
        key=spec.key,
        mode=config.DATA_SOURCE,
        location=spec.location,
        filetype=spec.filetype,
        loaded_at=datetime.now(),
        n_rows=len(generic),
        is_synthetic=True,
        error=error,
    )
    return LoadResult(df=generic, meta=meta)


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

_CATALOG: Optional[Dict[str, SourceSpec]] = None


def get_catalog() -> Dict[str, SourceSpec]:
    global _CATALOG
    if _CATALOG is None:
        _CATALOG = load_catalog()
    return _CATALOG


def load_source(key: str) -> LoadResult:
    """Load one catalog source. Never raises; degrades to a synthetic mock."""
    try:
        spec = get_catalog()[key]
    except KeyError:
        dummy = SourceSpec(key, "", "", "", "csv", ",", "", "", "unknown source")
        return _synthetic(dummy, f"source '{key}' not in catalog")
    try:
        path = _resolve_local_path(spec)
        return _parse_file(path, spec)
    except Exception as exc:  # noqa: BLE001 - resilience contract
        log.exception("Failed to load %s", key)
        return _synthetic(spec, f"{type(exc).__name__}: {exc}")
