"""Flow Monitor — cash market, futures market, single-name flows."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, ui
from data import store, transforms

ui.page_setup("Flow Monitor", "💧")
ui.page_header("Flow Monitor",
               "Who is buying Brazil: cash-market participation, futures "
               "positioning and single-name flows.")
ui.mode_banner()

tab_cash, tab_fut, tab_single = st.tabs(
    ["Cash market (B3)", "Futures market", "Single-name flows"])

# ------------------------------------------------------------- cash market
with tab_cash:
    ip, prov = store.get_source("investors_participation")
    daily = ip.get("Daily") if isinstance(ip, dict) else None
    cum = ip.get("Cumulative") if isinstance(ip, dict) else None
    names = {"foreign_investors": "Foreign",
             "institutional_investors": "Institutional",
             "individual_investors": "Individuals",
             "financial_institutions": "Financial inst.",
             "others": "Others"}
    if daily is not None:
        net = transforms.net_participation(daily)
        cols = [c for c in names if c in net.columns]
        if len(net):
            latest = net.iloc[-1]
            ui.kpi_row([(names[c], ui.fmt_brl_mm(latest[c]), None)
                        for c in cols][:5])
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                charts.grouped_bars(net.tail(60), "date", cols, names=names,
                                    height=360, stacked=True,
                                    title="Daily net flow (BRL)"),
                width="stretch")
        with c2:
            if cum is not None:
                cnet = transforms.net_participation(cum)
                ccols = [c for c in names if c in cnet.columns]
                st.plotly_chart(
                    charts.line(cnet.tail(126), "date", ccols, names=names,
                                height=360,
                                title="Month-to-date cumulative net flow "
                                      "(resets monthly)"),
                    width="stretch")
        share_cols = [f"{g}_purchases_part" for g in names
                      if f"{g}_purchases_part" in daily.columns]
        if share_cols:
            st.plotly_chart(
                charts.area(daily.tail(126), "date", share_cols,
                            names={f"{g}_purchases_part": n
                                   for g, n in names.items()},
                            height=300, pct=True,
                            title="Share of purchases by investor type"),
                width="stretch")
    ui.provenance_badge(prov, "investors_participation")

# ---------------------------------------------------------------- futures
with tab_fut:
    ff, prov_ff = store.get_source("future_flows")
    pv = transforms.futures_net_by_category(ff)
    if not pv.empty:
        last_day = pv.dropna(how="all").iloc[-1].sort_values()
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                charts.bar_signed(last_day.index, last_day.values, height=360,
                                  title=f"Net inflow by category — "
                                        f"{pv.index.max():%Y-%m-%d} (BRL)",
                                  value_fmt=",.3s"),
                width="stretch")
        with c2:
            cum = pv.fillna(0).cumsum().reset_index()
            st.plotly_chart(
                charts.line(cum, "data_pregao", list(pv.columns), height=360,
                            title="Cumulative net inflow (BRL)"),
                width="stretch")
        st.dataframe(
            pv.tail(15).sort_index(ascending=False).style.format("{:,.0f}"),
            width="stretch")
    ui.provenance_badge(prov_ff, "future_flows")

# --------------------------------------------------------- single-name
with tab_single:
    sf, prov_sf = store.get_source("singlename_flows")
    sec, _ = store.get_sectors()
    c1, c2, c3 = st.columns(3)
    investor = c1.selectbox("Investor", ["foreigners", "retail",
                                         "local_institutions", "others"])
    window = c2.selectbox("Window", ["21d", "63d", "252d"])
    metric = c3.selectbox("Normalization",
                          ["flow", "to_adtv", "to_ff"],
                          format_func={"flow": "BRL",
                                       "to_adtv": "× ADTV",
                                       "to_ff": "% free float"}.get)
    top = transforms.top_singlename_flows(sf, investor, window, metric, n=12)
    if not top.empty:
        c1, c2 = st.columns((6, 6))
        with c1:
            st.plotly_chart(
                charts.bar_signed(top["cod_ativo"], top["value"], height=480,
                                  title=f"Largest {window} {investor} "
                                        "in/outflows",
                                  value_fmt=",.3s" if metric == "flow"
                                  else ",.2f"),
                width="stretch")
        with c2:
            col = (f"{window}_{investor}_flow" if metric == "flow"
                   else f"{window}_{investor}_flow_{metric}")
            snap = transforms.latest_snapshot(sf)
            snap = transforms.add_sector(snap, sec)
            if snap.get("macro_sector_xp") is None or \
                    snap["macro_sector_xp"].isna().all():
                from data import demo
                snap = transforms.latest_snapshot(sf)
                snap = transforms.add_sector(snap, demo.sector_classification())
            if "macro_sector_xp" in snap.columns and col in snap.columns:
                agg = (snap.groupby("macro_sector_xp")[col].sum()
                       .dropna().sort_values())
                st.plotly_chart(
                    charts.bar_signed(agg.index, agg.values, height=480,
                                      title="Aggregated by XP macro sector",
                                      value_fmt=",.3s" if metric == "flow"
                                      else ",.2f"),
                    width="stretch")
    else:
        st.info("Single-name flow columns not available in this data mode.")
    ui.provenance_badge(prov_sf, "singlename_flows")
