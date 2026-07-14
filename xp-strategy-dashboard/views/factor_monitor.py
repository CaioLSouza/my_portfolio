"""Factor Monitor — XP factor family performance, LS spreads, rotation."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, ui
from data import store, transforms

ui.page_setup("Factor Monitor", "🧭")
ui.page_header("Factor Monitor",
               "What is working: XP factor long-short indices by family and "
               "window, and factor rotation over time.")
ui.mode_banner()

fr, prov = store.get_source("factor_returns")
sheet = st.sidebar.radio("Leg", ["LS", "Top", "Bottom"], index=0,
                         help="LS = long-short spread; Top/Bottom = single legs")
df = fr.get(sheet, pd.DataFrame()) if isinstance(fr, dict) else fr

tbl = transforms.factor_family_table(df)
if tbl.empty:
    st.warning("Factor return series unavailable.")
    st.stop()

windows = [w for w in ("1M", "3M", "6M", "YTD", "12M") if w in tbl.columns]

# ------------------------------------------------------------- KPI row
fam_means = tbl.groupby("family")[windows].mean()
if "3M" in fam_means.columns:
    best, worst = fam_means["3M"].idxmax(), fam_means["3M"].idxmin()
    ui.kpi_row([
        ("Best family 3M", best, ui.fmt_pct(fam_means.loc[best, "3M"])),
        ("Worst family 3M", worst, ui.fmt_pct(fam_means.loc[worst, "3M"])),
        ("Families tracked", str(fam_means.shape[0]), None),
        ("Factors tracked", str(len(tbl)), None),
    ])
st.divider()

c1, c2 = st.columns((6, 6))
with c1:
    st.subheader("Family × window heatmap")
    hm = fam_means[windows].sort_values(windows[1] if len(windows) > 1
                                        else windows[0], ascending=False)
    st.plotly_chart(charts.heatmap(hm, height=380), width="stretch")

with c2:
    st.subheader("Factor detail")
    fam_sel = st.selectbox("Family", sorted(tbl["family"].unique()))
    sub = tbl[tbl["family"] == fam_sel].set_index("factor")[windows]
    win_sel = st.selectbox("Window", windows,
                           index=min(1, len(windows) - 1))
    sub = sub.sort_values(win_sel)
    st.plotly_chart(
        charts.bar_signed(sub.index, sub[win_sel], height=300,
                          title=f"{fam_sel} — {win_sel} return",
                          value_fmt=".1%"),
        width="stretch")

st.divider()

st.subheader("Factor rotation — cumulative index by family (rebased = 100)")
if "data" in df.columns:
    fam_cols = {}
    for col in df.columns:
        if "/" in str(col):
            fam_cols.setdefault(str(col).split("/", 1)[0], []).append(col)
    rot = pd.DataFrame({"data": df["data"]})
    for fam, cols in fam_cols.items():
        rot[fam] = df[cols].mean(axis=1)
    horizon = st.radio("Horizon", ["6M", "1Y", "3Y", "All"], index=1,
                       horizontal=True)
    days = {"6M": 182, "1Y": 365, "3Y": 3 * 365}.get(horizon)
    shown = rot if days is None else rot[
        rot["data"] >= rot["data"].max() - pd.Timedelta(days=days)]
    st.plotly_chart(
        charts.line(shown, "data", list(fam_cols), height=420,
                    normalize=True),
        width="stretch")
ui.provenance_badge(prov, "factor_returns")
