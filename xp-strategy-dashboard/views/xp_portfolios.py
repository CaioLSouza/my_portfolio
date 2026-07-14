"""XP Portfolios — composition, performance vs IBOV, active bets."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, ui
from data import store, transforms

ui.page_setup("XP Portfolios", "🗂️")
ui.page_header("XP Recommended Portfolios",
               "Composition, monthly performance vs Ibovespa and active bets "
               "for TOP Ações, TOP Dividendos, Small Caps and ESG.")
ui.mode_banner()

pf, prov = store.get_portfolios()
hist = pf.get("history", pd.DataFrame())
perf = pf.get("performance", pd.DataFrame())

if hist.empty:
    st.warning("Portfolio composition could not be parsed from the workbook.")
    st.stop()

portfolios = sorted(hist["portfolio"].unique())
sel = st.sidebar.selectbox("Portfolio", portfolios)

cur = transforms.current_composition(hist[hist["portfolio"] == sel])
h = hist[hist["portfolio"] == sel]

# ------------------------------------------------------------- KPI row
n_names = len(cur)
last_reb = cur["date"].max() if len(cur) else None
kpis = [("Holdings", str(n_names), None)]
if last_reb is not None:
    kpis.append(("Last rebalance", f"{last_reb:%Y-%m-%d}", None))
if not perf.empty:
    p = perf[(perf["portfolio"].str.contains(sel.split(" XP")[0].strip(),
                                             case=False, regex=False))
             | (perf["portfolio"] == sel)]
    own = p[p["series"] != "IBOV"]
    bench = p[p["series"] == "IBOV"]
    if "inception_return" in p.columns:
        if len(own):
            kpis.append(("Since inception",
                         ui.fmt_pct(own["inception_return"].iloc[-1]), None))
        if len(own) and len(bench):
            kpis.append(("IBOV since inception",
                         ui.fmt_pct(bench["inception_return"].iloc[-1]),
                         None))
ui.kpi_row(kpis)
ui.provenance_badge(prov, "performance_carteiras")
st.divider()

c1, c2 = st.columns((5, 7))

# ------------------------------------------------------- composition now
with c1:
    st.subheader("Current composition")
    if len(cur):
        show = cur.sort_values("weight", ascending=False)
        st.plotly_chart(
            charts.bar_mag(show["ticker"], show["weight"], height=420,
                           title=f"Weights (%) — {last_reb:%b %Y}",
                           value_fmt=".1f"),
            width="stretch")
        st.dataframe(
            show[["ticker", "weight"]].set_index("ticker")
            .style.format({"weight": "{:.1f}%"}), width="stretch", height=240)

# ------------------------------------------------------- weight history
with c2:
    st.subheader("Composition history")
    piv = (h.pivot_table(index="ticker", columns="date", values="weight",
                         aggfunc="last"))
    piv = piv.loc[piv.notna().any(axis=1)]
    # keep the ~25 most-held names so the heatmap stays readable
    order = piv.fillna(0).mean(axis=1).sort_values(ascending=False)
    piv = piv.loc[order.index[:25]]
    piv.columns = [f"{c:%Y-%m}" for c in piv.columns]
    if not piv.empty:
        st.plotly_chart(
            charts.heatmap(piv, height=560, fmt=".1f", sequential=True,
                           show_text=False,
                           title="Weight (%) per rebalance date — blank = "
                                 "not held"),
            width="stretch")

st.divider()

# ------------------------------------------------------- performance
st.subheader("Monthly performance vs Ibovespa")
if not perf.empty:
    p = perf[(perf["portfolio"].str.contains(sel.split(" XP")[0].strip(),
                                             case=False, regex=False))
             | (perf["portfolio"] == sel)]
    if p.empty:
        st.info("No performance block found for this portfolio in the sample "
                "workbook (only two blocks fit the 10-row extract).")
    else:
        piv = (p.pivot_table(index="date", columns="series",
                             values="monthly_return", aggfunc="last")
               .sort_index())
        own_col = [c for c in piv.columns if c != "IBOV"]
        cols = own_col[:1] + (["IBOV"] if "IBOV" in piv.columns else [])
        dfp = piv[cols].dropna(how="all").reset_index()
        cc1, cc2 = st.columns(2)
        with cc1:
            st.plotly_chart(
                charts.grouped_bars(dfp, "date", cols, height=360,
                                    title="Monthly returns"),
                width="stretch")
        with cc2:
            cumdf = dfp.copy()
            for c in cols:
                cumdf[c] = (1 + cumdf[c].fillna(0)).cumprod() - 1
            st.plotly_chart(
                charts.line(cumdf, "date", cols, height=360, pct=True,
                            title="Cumulative return (window shown)"),
                width="stretch")
else:
    st.info("Performance blocks unavailable.")

st.divider()

# ------------------------------------------------------- active bets
st.subheader("Active bets vs IBOV")
idxc, prov_idx = store.get_source("index_composition")
if len(cur) and isinstance(idxc, pd.DataFrame) and "IBOV" in idxc.columns:
    snap = transforms.latest_snapshot(idxc)
    bench = snap[["cod_ativo", "IBOV"]].rename(columns={"IBOV": "bench_weight"})
    bets = cur.merge(bench, left_on="ticker", right_on="cod_ativo", how="left")
    bets["bench_weight"] = bets["bench_weight"].fillna(0)
    bets["active"] = bets["weight"] - bets["bench_weight"]
    bets = bets.sort_values("active")
    st.plotly_chart(
        charts.bar_signed(bets["ticker"], bets["active"], height=380,
                          title="Portfolio weight − IBOV weight (pp)",
                          value_fmt=".1f"),
        width="stretch")
    ui.provenance_badge(prov_idx, "index_composition")
else:
    st.info("Index composition unavailable for active-bet calculation.")
