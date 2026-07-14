"""Short Interest monitor — most shorted, days to cover, lending rates."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, ui
from data import store, transforms

ui.page_setup("Short Interest", "📉")
ui.page_header("Short Interest Monitor",
               "Most-shorted names, borrowing cost, days to cover and "
               "1-month changes in short positioning.")
ui.mode_banner()

ss, prov = store.get_source("short_selling")
sec, _ = store.get_sectors()

if "cod_ativo" not in ss.columns:
    st.warning("Short-selling data unavailable in this mode.")
    st.stop()

snap = transforms.latest_snapshot(ss)
snap = transforms.add_sector(snap, sec)
if "macro_sector_xp" not in snap.columns or \
        snap["macro_sector_xp"].isna().mean() > 0.5:
    from data import demo
    snap = transforms.latest_snapshot(ss)
    snap = transforms.add_sector(snap, demo.sector_classification())

# 1M change in short interest pct
if {"data", "short_interest_pct"}.issubset(ss.columns):
    cutoff = ss["data"].max() - pd.Timedelta(days=30)
    past = (ss[ss["data"] <= cutoff].sort_values("data")
            .groupby("cod_ativo").tail(1)[["cod_ativo", "short_interest_pct"]]
            .rename(columns={"short_interest_pct": "si_1m_ago"}))
    snap = snap.merge(past, on="cod_ativo", how="left")
    snap["si_1m_chg"] = snap["short_interest_pct"] - snap["si_1m_ago"]

# ------------------------------------------------------------- KPIs
kpis = []
if "short_interest_pct" in snap.columns:
    top_name = snap.loc[snap["short_interest_pct"].idxmax()]
    kpis.append((f"Most shorted — {top_name['cod_ativo']}",
                 ui.fmt_pct(top_name["short_interest_pct"]), None))
    kpis.append(("Median SI % free float",
                 ui.fmt_pct(snap["short_interest_pct"].median()), None))
if "lending_rate" in snap.columns:
    kpis.append(("Median lending rate",
                 ui.fmt_num(snap["lending_rate"].median(), 2) + "% a.a.", None))
if "days_to_cover" in snap.columns:
    kpis.append(("Median days to cover",
                 ui.fmt_num(snap["days_to_cover"].median(), 1), None))
ui.kpi_row(kpis)
st.divider()

c1, c2 = st.columns((6, 6))
with c1:
    st.subheader("Most shorted (% of free float)")
    top = snap.nlargest(15, "short_interest_pct")
    st.plotly_chart(
        charts.bar_mag(top["cod_ativo"], top["short_interest_pct"],
                       height=420, value_fmt=".1%", pct_axis=True),
        width="stretch")

with c2:
    st.subheader("Crowdedness map")
    sub = snap.dropna(subset=["days_to_cover", "lending_rate"])
    if len(sub):
        st.plotly_chart(
            charts.scatter(sub, "days_to_cover", "lending_rate", "cod_ativo",
                           color_by_sign="si_1m_chg"
                           if "si_1m_chg" in sub.columns else None,
                           height=420,
                           title="Days to cover × lending rate "
                                 "(green/red = 1M SI change)"),
            width="stretch")

st.divider()

c3, c4 = st.columns((6, 6))
with c3:
    st.subheader("Biggest 1M changes in SI (pp of free float)")
    if "si_1m_chg" in snap.columns and snap["si_1m_chg"].notna().any():
        chg = snap.dropna(subset=["si_1m_chg"])
        movers = pd.concat([chg.nlargest(8, "si_1m_chg"),
                            chg.nsmallest(8, "si_1m_chg")])
        movers = movers.sort_values("si_1m_chg")
        st.plotly_chart(
            charts.bar_signed(movers["cod_ativo"],
                              movers["si_1m_chg"] * 100,
                              height=420, value_fmt=".2f"),
            width="stretch")
    else:
        st.info("Not enough history for 1M change.")

with c4:
    st.subheader("By XP macro sector — median SI %")
    if "macro_sector_xp" in snap.columns:
        agg = (snap.groupby("macro_sector_xp")["short_interest_pct"]
               .median().dropna().sort_values())
        st.plotly_chart(
            charts.bar_mag(agg.index, agg.values, height=420,
                           value_fmt=".1%", pct_axis=True),
            width="stretch")

st.divider()
st.subheader("Short interest table")
cols = [c for c in ("cod_ativo", "macro_sector_xp", "short_interest_pct",
                    "si_1m_chg", "lending_rate", "days_to_cover",
                    "short_interest_value", "surprise_in_si")
        if c in snap.columns]
tbl = (snap[cols].set_index("cod_ativo")
       .sort_values("short_interest_pct", ascending=False))
st.dataframe(tbl.style.format({
    "short_interest_pct": "{:.1%}", "si_1m_chg": "{:+.2%}",
    "lending_rate": "{:.2f}", "days_to_cover": "{:.1f}",
    "short_interest_value": "{:,.0f}", "surprise_in_si": "{:.2f}"}),
    width="stretch", height=420)
ui.provenance_badge(prov, "short_selling")
