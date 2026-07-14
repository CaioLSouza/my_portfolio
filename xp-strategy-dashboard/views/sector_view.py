"""Sector View — everything aggregated by XP macro sector."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, ui
from data import store, transforms

ui.page_setup("Sector View", "🏭")
ui.page_header("Sector View",
               "Performance, valuation, flows and short positioning rolled "
               "up to the XP macro-sector taxonomy.")
ui.mode_banner()

sect_idx, prov_si = store.get_sector_indices()
scr, provs = store.get_screener()

# ------------------------------------------------------- performance
st.subheader("Sector performance (value-weighted indices)")
sector_cols = [c for c in sect_idx.columns if c not in ("data", "Ibovespa")]
rows = {}
for c in sector_cols:
    wr = transforms.window_returns(sect_idx[c], sect_idx["data"])
    if wr:
        rows[c] = wr
if rows:
    hm = pd.DataFrame(rows).T
    hm = hm[[c for c in ("1M", "3M", "6M", "YTD", "12M") if c in hm.columns]]
    st.plotly_chart(charts.heatmap(hm.sort_values(hm.columns[0],
                                                  ascending=False),
                                   height=420),
                    width="stretch")
ui.provenance_badge(prov_si, "sector_index")

st.divider()

c1, c2 = st.columns((6, 6))
with c1:
    st.subheader("Relative to Ibovespa — 12M")
    if "Ibovespa" in sect_idx.columns and rows:
        ib = transforms.window_returns(sect_idx["Ibovespa"], sect_idx["data"])
        rel = {s: v.get("12M", float("nan")) - ib.get("12M", 0)
               for s, v in rows.items()}
        rel_s = pd.Series(rel).dropna().sort_values()
        st.plotly_chart(
            charts.bar_signed(rel_s.index, rel_s.values, height=420,
                              value_fmt=".1%"),
            width="stretch")

with c2:
    st.subheader("Sector index history (rebased = 100, 12M)")
    pick = st.multiselect("Sectors", sector_cols,
                          default=sector_cols[:4])
    if pick:
        recent = sect_idx[sect_idx["data"] >=
                          sect_idx["data"].max() - pd.Timedelta(days=365)]
        st.plotly_chart(
            charts.line(recent, "data", pick, height=380, normalize=True),
            width="stretch")

st.divider()

# ------------------------------------------------------- fundamentals
st.subheader("Fundamentals & positioning by sector")
if "macro_sector_xp" in scr.columns:
    agg_spec = {}
    for col, how, label in (
        ("price_to_earnings_fwd", "median", "P/E fwd (med)"),
        ("ev_to_ebitda_fwd", "median", "EV/EBITDA fwd (med)"),
        ("dividend_yield_ltm", "median", "Div yield (med)"),
        ("roe", "median", "ROE (med)"),
        ("12m_momentum", "median", "12M mom (med)"),
        ("short_interest_pct", "median", "SI % FF (med)"),
        ("analyst_rec", "mean", "Rec (1=buy)"),
    ):
        if col in scr.columns:
            agg_spec[label] = (col, how)
    if agg_spec:
        agg = scr.groupby("macro_sector_xp").agg(**agg_spec)
        pct_cols = [c for c in agg.columns
                    if "yield" in c.lower() or "mom" in c.lower()
                    or "ROE" in c or "SI" in c]
        def _sign_color(v: float) -> str:
            if isinstance(v, (int, float)) and v == v:
                return ("color:#006300" if v > 0 else
                        "color:#d03b3b" if v < 0 else "")
            return ""

        styler = agg.style.format("{:,.1f}")
        styler = styler.format("{:.1%}", subset=pct_cols)
        mom_cols = [c for c in agg.columns if "mom" in c.lower()]
        if mom_cols:
            styler = styler.map(_sign_color, subset=mom_cols)
        st.dataframe(styler, width="stretch", height=520)
    for key, prov in provs.items():
        ui.provenance_badge(prov, key)
else:
    st.info("Screener universe has no sector mapping in this mode.")
