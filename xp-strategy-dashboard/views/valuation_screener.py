"""Valuation & Consensus screener over factor_zoo + consensus."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, ui
from data import store

ui.page_setup("Valuation Screener", "🔎")
ui.page_header("Valuation & Consensus Screener",
               "Single-name screen: forward multiples, yields, analyst "
               "recommendations and revision momentum.")
ui.mode_banner()

scr, provs = store.get_screener()
if scr.empty or "cod_ativo" not in scr.columns:
    st.warning("Screener universe unavailable in this data mode.")
    st.stop()

# ------------------------------------------------------------- filters
sectors = sorted(scr["macro_sector_xp"].dropna().unique()) \
    if "macro_sector_xp" in scr.columns else []
sel_sec = st.sidebar.multiselect("XP macro sector", sectors)
if sel_sec:
    scr = scr[scr["macro_sector_xp"].isin(sel_sec)]

if "market_cap_class" in scr.columns and scr["market_cap_class"].notna().any():
    mc_bn = scr["market_cap_class"] / 1e9
    lo, hi = float(mc_bn.min()), float(mc_bn.max())
    if hi > lo:
        rng = st.sidebar.slider("Market cap (BRL bn)", lo, hi, (lo, hi))
        scr = scr[mc_bn.between(*rng)]

metric_cols = {
    "price_to_earnings_fwd": "P/E fwd",
    "ev_to_ebitda_fwd": "EV/EBITDA fwd",
    "earnings_yield_fwd": "Earnings yield fwd",
    "dividend_yield_ltm": "Dividend yield LTM",
    "fcf_yield_ltm": "FCF yield LTM",
    "analyst_rec": "Analyst rec (1=buy)",
    "analyst_revisions_netincome_momentum_63d_blended": "NI revisions 63d",
    "12m_momentum": "12M momentum",
    "roe": "ROE",
}
avail = {c: n for c, n in metric_cols.items() if c in scr.columns}

# ------------------------------------------------------------- KPIs
kpis = []
for col, name in list(avail.items())[:4]:
    med = scr[col].median()
    is_pct = "yield" in col or "momentum" in col or col == "roe"
    kpis.append((f"Median {name}",
                 ui.fmt_pct(med) if is_pct else ui.fmt_num(med, 1), None))
kpis.append(("Names in screen", str(len(scr)), None))
ui.kpi_row(kpis)
st.divider()

c1, c2 = st.columns((6, 6))
with c1:
    st.subheader("Cross-section")
    axes = list(avail)
    x_sel = st.selectbox("X axis", axes, index=0)
    y_default = axes.index("roe") if "roe" in axes else min(1, len(axes) - 1)
    y_sel = st.selectbox("Y axis", axes, index=y_default)
    sub = scr.dropna(subset=[x_sel, y_sel])
    st.plotly_chart(
        charts.scatter(sub, x_sel, y_sel, "cod_ativo",
                       color_by_sign="analyst_revisions_netincome_momentum_63d_blended"
                       if "analyst_revisions_netincome_momentum_63d_blended"
                       in sub.columns else None,
                       height=440,
                       title=f"{avail[x_sel]} vs {avail[y_sel]} "
                             "(green/red = NI revision sign)",
                       x_pct="yield" in x_sel or "momentum" in x_sel,
                       y_pct="yield" in y_sel or "momentum" in y_sel),
        width="stretch")

with c2:
    st.subheader("Distribution")
    d_sel = st.selectbox("Metric", axes,
                         index=axes.index(x_sel) if x_sel in axes else 0,
                         key="dist_metric")
    import plotly.graph_objects as go
    vals = scr[d_sel].dropna()
    fig = go.Figure(go.Histogram(x=vals, nbinsx=30,
                                 marker=dict(color=charts.SERIES[0],
                                             line=dict(width=1,
                                                       color=charts.SURFACE))))
    fig.update_layout(height=440, paper_bgcolor=charts.SURFACE,
                      plot_bgcolor=charts.SURFACE, bargap=0.05,
                      margin=dict(l=10, r=10, t=30, b=10),
                      title=dict(text=f"{avail[d_sel]} across {len(vals)} names",
                                 font=dict(size=14), x=0))
    fig.update_xaxes(gridcolor=charts.GRID)
    fig.update_yaxes(gridcolor=charts.GRID)
    st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("Screen table")
table_cols = ["cod_ativo"] + (["name"] if "name" in scr.columns else []) + \
    (["macro_sector_xp"] if "macro_sector_xp" in scr.columns else []) + \
    list(avail)
tbl = scr[table_cols].set_index("cod_ativo").sort_values(
    list(avail)[0], ascending=True)
fmt = {}
for col in avail:
    fmt[col] = "{:.1%}" if ("yield" in col or "momentum" in col
                            or col == "roe") else "{:,.1f}"
st.dataframe(tbl.rename(columns=avail | {"macro_sector_xp": "Sector",
                                         "name": "Name"})
             .style.format({avail.get(k, k): v for k, v in fmt.items()}),
             width="stretch", height=480)

for key, prov in provs.items():
    ui.provenance_badge(prov, key)
