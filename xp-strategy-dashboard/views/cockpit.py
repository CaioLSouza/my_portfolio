"""Cockpit — home view of the XP Equity Strategy dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, ui
from data import store, transforms


ui.page_setup("Cockpit", "🎛️")
ui.page_header(
    "XP Equity Strategy Cockpit",
    "One screen for the desk: market, flows, portfolios, factors, screens.",
)
ui.mode_banner()

# ---------------------------------------------------------------- data
sect_idx, prov_si = store.get_sector_indices()
ip, prov_ip = store.get_source("investors_participation")
fr, prov_fr = store.get_source("factor_returns")
pf, prov_pf = store.get_portfolios()

# ---------------------------------------------------------------- KPIs
kpis = []
if "Ibovespa" in sect_idx.columns:
    ibov = sect_idx[["data", "Ibovespa"]].dropna()
    last = ibov["Ibovespa"].iloc[-1]
    day = last / ibov["Ibovespa"].iloc[-2] - 1 if len(ibov) > 1 else None
    wr = transforms.window_returns(ibov["Ibovespa"], ibov["data"])
    kpis.append(("Ibovespa", ui.fmt_num(last, 0),
                 ui.fmt_pct(day, 2) if day is not None else None))
    kpis.append(("Ibovespa YTD", ui.fmt_pct(wr.get("YTD")),
                 None))
    kpis.append(("Ibovespa 12M", ui.fmt_pct(wr.get("12M")), None))

daily = ip.get("Daily") if isinstance(ip, dict) else None
if daily is not None:
    net = transforms.net_participation(daily)
    if "foreign_investors" in net.columns and len(net):
        kpis.append(("Foreign net flow (last day)",
                     ui.fmt_brl_mm(net["foreign_investors"].iloc[-1]),
                     None))

fam_tbl = transforms.factor_family_table(fr.get("LS", pd.DataFrame())) \
    if isinstance(fr, dict) else pd.DataFrame()
if not fam_tbl.empty and "3M" in fam_tbl.columns:
    fam_3m = fam_tbl.groupby("family")["3M"].mean().sort_values()
    kpis.append((f"Best factor 3M — {fam_3m.index[-1]}",
                 ui.fmt_pct(fam_3m.iloc[-1]), None))

if kpis:
    ui.kpi_row(kpis[:5])

st.divider()

# ------------------------------------------------- market & sectors row
left, right = st.columns((6, 6))

with left:
    st.subheader("Ibovespa — last 12 months")
    if "Ibovespa" in sect_idx.columns:
        recent = sect_idx[sect_idx["data"] >=
                          sect_idx["data"].max() - pd.Timedelta(days=365)]
        st.plotly_chart(charts.line(recent, "data", ["Ibovespa"], height=320),
                        width="stretch")
    ui.provenance_badge(prov_si, "sector_index")

with right:
    st.subheader("Sector performance heatmap")
    sector_cols = [c for c in sect_idx.columns if c not in ("data", "Ibovespa")]
    rows = {}
    for c in sector_cols:
        wr = transforms.window_returns(sect_idx[c], sect_idx["data"])
        if wr:
            rows[c] = wr
    if rows:
        hm = pd.DataFrame(rows).T[["1M", "3M", "6M", "YTD", "12M"]]
        hm = hm.sort_values("1M", ascending=False)
        st.plotly_chart(charts.heatmap(hm, height=380), width="stretch")
    ui.provenance_badge(prov_si, "sector_index")

st.divider()

# ------------------------------------------------- flows & factors row
fleft, fright = st.columns((6, 6))

with fleft:
    st.subheader("Cash-market net flow by investor")
    if daily is not None and len(net):
        names = {"foreign_investors": "Foreign",
                 "institutional_investors": "Institutional",
                 "individual_investors": "Individuals",
                 "financial_institutions": "Financial inst.",
                 "others": "Others"}
        show = net.tail(60)
        cols = [c for c in names if c in show.columns]
        st.plotly_chart(
            charts.grouped_bars(show, "date", cols, names=names, height=320,
                                stacked=True),
            width="stretch")
    ui.provenance_badge(prov_ip, "investors_participation")

with fright:
    st.subheader("Factor families — mean long-short return")
    if not fam_tbl.empty:
        fam = fam_tbl.groupby("family")[["1M", "3M", "YTD"]].mean()
        fam = fam.sort_values("3M")
        st.plotly_chart(
            charts.bar_signed(fam.index, fam["3M"], height=320,
                              title="3M window", value_fmt=".1%"),
            width="stretch")
    ui.provenance_badge(prov_fr, "factor_returns")

st.divider()

# ------------------------------------------------- portfolios teaser
st.subheader("XP recommended portfolios — inception return vs IBOV")
perf = pf.get("performance", pd.DataFrame())
if not perf.empty and "inception_return" in perf.columns:
    latest = (perf.dropna(subset=["inception_return"])
              .groupby(["portfolio", "series"], as_index=False)
              .agg(inception=("inception_return", "last")))
    piv = latest.pivot(index="portfolio", columns="series", values="inception")
    cards = []
    for pf_name, row in piv.iterrows():
        own = row.drop(labels=[c for c in piv.columns if c == "IBOV"]).dropna()
        if own.empty:
            continue
        excess = own.iloc[0] - row.get("IBOV", float("nan"))
        cards.append((pf_name, ui.fmt_pct(own.iloc[0]),
                      f"{ui.fmt_pct(excess)} vs IBOV"))
    if cards:
        ui.kpi_row(cards[:4])
ui.provenance_badge(prov_pf, "performance_carteiras")

st.caption("Navigate with the sidebar: Flow Monitor · XP Portfolios · Factor "
           "Monitor · Valuation Screener · Short Interest · Research Coverage "
           "· Sector View · Data Health")
