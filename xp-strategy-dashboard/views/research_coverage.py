"""Research Coverage — XP analyst estimates and recommendations (COMP SHEET)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import charts, ui
from data import store, transforms

ui.page_setup("Research Coverage", "📋")
ui.page_header("Research Coverage — COMP SHEET",
               "XP analyst recommendations, targets and implied upside "
               "across the coverage universe.")
ui.mode_banner()

cs, prov = store.get_source("comp_sheet")
summary = transforms.comp_sheet_summary(cs)

if summary.empty or "RECOMMENDATION" not in summary.columns:
    st.warning("COMP SHEET unavailable.")
    st.stop()

# join a current price for upside when the sheet itself has none — only when
# prices and targets come from the same origin (mixing the real comp sheet
# with a synthetic price universe would produce meaningless upsides)
if "upside" not in summary.columns:
    scr, scr_provs = store.get_screener()
    px_synth = scr_provs["factor_zoo"].is_synthetic
    if {"cod_ativo", "close_price"}.issubset(scr.columns) and \
            prov.is_synthetic == px_synth:
        px = scr[["cod_ativo", "close_price"]]
        summary = summary.merge(px, left_on="TICKER", right_on="cod_ativo",
                                how="left")
        if "TARGET" in summary.columns:
            summary["upside"] = summary["TARGET"] / summary["close_price"] - 1
        if summary.get("upside") is not None and \
                summary["upside"].notna().sum() < 3:
            summary = summary.drop(columns=["upside"])

rec_order = ["Buy", "Neutral", "Sell"]
rec_counts = summary["RECOMMENDATION"].value_counts()

kpis = [("Covered names", str(len(summary)), None)]
for rec in rec_order:
    if rec in rec_counts:
        share = ui.fmt_pct(rec_counts[rec] / len(summary), 0)
        kpis.append((rec, f"{int(rec_counts[rec])} · {share}", None))
if "RESTRICTED" in summary.columns:
    kpis.append(("Restricted", str(int(summary["RESTRICTED"].sum())), None))
ui.kpi_row(kpis[:5])
st.divider()

c1, c2 = st.columns((6, 6))
with c1:
    st.subheader("Recommendation mix by sector")
    if "SECTOR_XP" in summary.columns:
        mix = (summary.groupby(["SECTOR_XP", "RECOMMENDATION"]).size()
               .unstack(fill_value=0))
        mix = mix[[c for c in rec_order if c in mix.columns]]
        mix = mix.loc[mix.sum(axis=1).sort_values().index]
        fig = go.Figure()
        rec_colors = {"Buy": charts.GOOD, "Neutral": "#898781",
                      "Sell": charts.BAD}
        for rec in mix.columns:
            fig.add_trace(go.Bar(y=mix.index, x=mix[rec], name=rec,
                                 orientation="h",
                                 marker=dict(color=rec_colors.get(rec,
                                                                  "#52514e"),
                                             line=dict(width=0))))
        fig.update_layout(barmode="stack", height=420,
                          paper_bgcolor=charts.SURFACE,
                          plot_bgcolor=charts.SURFACE,
                          margin=dict(l=10, r=10, t=10, b=10),
                          legend=dict(orientation="h", y=1.02, x=0),
                          bargap=0.25)
        fig.update_xaxes(gridcolor=charts.GRID)
        st.plotly_chart(fig, width="stretch")

with c2:
    st.subheader("Implied upside to target")
    if "upside" in summary.columns and summary["upside"].notna().any():
        up = summary.dropna(subset=["upside"]).sort_values("upside")
        st.plotly_chart(
            charts.bar_signed(up["TICKER"], up["upside"], height=420,
                              title="TARGET / price − 1", value_fmt=".0%"),
            width="stretch")
    else:
        st.info("No current price available to compute upside in this mode "
                "(prod joins the market_data close).")

st.divider()

c3, c4 = st.columns((6, 6))
with c3:
    st.subheader("Coverage per lead analyst")
    if "LEAD_ANALYST" in summary.columns:
        per = summary["LEAD_ANALYST"].value_counts().sort_values(
            ascending=False)
        st.plotly_chart(
            charts.bar_mag(per.index, per.values, height=360,
                           value_fmt=",.0f"),
            width="stretch")

with c4:
    st.subheader("Cost of capital")
    if {"WACC", "SECTOR_XP"}.issubset(summary.columns) and \
            summary["WACC"].notna().any():
        w = (summary.groupby("SECTOR_XP")["WACC"].median()
             .dropna().sort_values(ascending=False))
        st.plotly_chart(
            charts.bar_mag(w.index, w.values, height=360,
                           title="Median WACC by sector",
                           value_fmt=".1%", pct_axis=True),
            width="stretch")

st.divider()
st.subheader("Coverage table")
cols = [c for c in ("TICKER", "NAME", "SECTOR_XP", "LEAD_ANALYST",
                    "RECOMMENDATION", "RESTRICTED", "TARGET", "upside",
                    "WACC", "PDATE") if c in summary.columns]
tbl = summary[cols].set_index("TICKER").sort_values("SECTOR_XP")
st.dataframe(tbl.style.format({"TARGET": "{:,.1f}", "upside": "{:+.0%}",
                               "WACC": "{:.1%}",
                               "PDATE": lambda d: f"{d:%Y-%m-%d}"
                               if pd.notna(d) else "–"}),
             width="stretch", height=440)
ui.provenance_badge(prov, "comp_sheet")
