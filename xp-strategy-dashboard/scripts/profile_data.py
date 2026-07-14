"""Phase 0 — profile every catalog source and write DATA_PROFILE.md.

Run from the project root:  python scripts/profile_data.py
Uses the real data layer (github mode) so what we profile is exactly what
the app will see.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.loaders import get_catalog, load_source  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "DATA_PROFILE.md"


def _fmt_dtypes(df: pd.DataFrame, max_cols: int = 40) -> str:
    items = [f"`{c}`: {t}" for c, t in df.dtypes.items()]
    shown = items[:max_cols]
    extra = f" … (+{len(items) - max_cols} more)" if len(items) > max_cols else ""
    return ", ".join(shown) + extra


def _date_range(df: pd.DataFrame) -> str:
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            s = df[col].dropna()
            if len(s):
                return f"`{col}`: {s.min():%Y-%m-%d} → {s.max():%Y-%m-%d} ({s.nunique()} unique)"
    return "no datetime column detected"


def _ticker_count(df: pd.DataFrame) -> str:
    for cand in ("cod_ativo", "ticker", "TICKER", "codigo"):
        if cand in df.columns:
            return f"`{cand}`: {df[cand].nunique()} unique"
    return "no ticker column detected"


def _null_pct(df: pd.DataFrame, top: int = 12) -> str:
    pct = (df.isna().mean() * 100).sort_values(ascending=False)
    pct = pct[pct > 0].head(top)
    if pct.empty:
        return "no nulls"
    return ", ".join(f"`{c}` {v:.0f}%" for c, v in pct.items())


def profile() -> str:
    catalog = get_catalog()
    lines = [
        "# DATA_PROFILE — Phase 0 discovery (github samples)",
        "",
        f"Profiled {len(catalog)} sources via the app's own loader "
        "(`DATA_SOURCE=github`). Samples are small extracts; prod parquets "
        "may add `(cod_ativo, data)` index columns and far more rows.",
        "",
    ]
    for key, spec in catalog.items():
        res = load_source(key)
        df = res.df
        lines += [f"## `{key}`", ""]
        lines += [f"- **Description:** {spec.description}"]
        lines += [f"- **Prod:** `{spec.prod_path}` ({spec.prod_filetype})"]
        lines += [f"- **Sample type:** {spec.sample_filetype}" +
                  (f", csv sep `{spec.csv_sep}`" if spec.sample_filetype == "csv" else "")]
        if res.meta.is_synthetic:
            lines += [f"- **LOAD FAILED — synthetic fallback.** Error: {res.meta.error}", ""]
            continue
        if res.sheets and len(res.sheets) > 1:
            lines += [f"- **Sheets:** {', '.join(res.sheets)}"]
        lines += [f"- **Shape:** {df.shape[0]} rows × {df.shape[1]} cols"]
        lines += [f"- **Date range:** {_date_range(df)}"]
        lines += [f"- **Tickers:** {_ticker_count(df)}"]
        lines += [f"- **Nulls (top):** {_null_pct(df)}"]
        lines += [f"- **Dtypes:** {_fmt_dtypes(df)}", ""]
        sample = df.head(3).to_markdown(index=False)
        # keep very wide tables readable in the md file
        if df.shape[1] > 12:
            sample = df.iloc[:3, :12].to_markdown(index=False) + f"\n\n_(first 12 of {df.shape[1]} columns)_"
        lines += ["Sample rows:", "", sample, ""]
        # profile extra sheets briefly
        for name, sdf in list(res.sheets.items())[:8]:
            if len(res.sheets) > 1:
                lines += [f"**Sheet `{name}`** — {sdf.shape[0]}×{sdf.shape[1]}; "
                          f"cols: {', '.join(map(str, sdf.columns[:15]))}"
                          + (" …" if sdf.shape[1] > 15 else ""), ""]
    return "\n".join(lines)


if __name__ == "__main__":
    OUT.write_text(profile(), encoding="utf-8")
    print(f"Wrote {OUT}")
