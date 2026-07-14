"""Flow Monitor — cash market, futures market, single-name flows.

Interactive: period presets + custom date range (sidebar, shared by all
tabs), investor-group and category filters, daily/cumulative view toggle,
ticker drill-down and CSV export of whatever is on screen.
"""

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

GROUP_NAMES = {"foreign_investors": "Foreign",
               "institutional_investors": "Institutional",
               "individual_investors": "Individuals",
               "financial_institutions": "Financial inst.",
               "others": "Others"}
INVESTOR_LABELS = {"foreigners": "Foreign", "retail": "Retail",
                   "local_institutions": "Local institutions",
                   "others": "Others"}

# ---------------------------------------------------------------- data
ip, prov_ip = store.get_source("investors_participation")
ff, prov_ff = store.get_source("future_flows")
sf, prov_sf = store.get_source("singlename_flows")

daily = ip.get("Daily") if isinstance(ip, dict) else None
net_all = transforms.net_participation(daily) if daily is not None \
    else pd.DataFrame()

# one date-range control drives every tab; anchor on the union of the
# cash-market and futures calendars so both filter sensibly
all_dates = pd.concat([
    net_all["date"] if "date" in net_all.columns
    else pd.Series(dtype="datetime64[ns]"),
    pd.to_datetime(ff["data_pregao"]) if "data_pregao" in ff.columns
    else pd.Series(dtype="datetime64[ns]"),
], ignore_index=True)
start, end = ui.date_range_control(all_dates, key="flows", default="3M")

tab_cash, tab_fut, tab_single = st.tabs(
    ["Cash market (B3)", "Futures market", "Single-name flows"])

# ------------------------------------------------------------- cash market
with tab_cash:
    if daily is None or net_all.empty:
        st.warning("Cash-market participation unavailable.")
    else:
        groups = [g for g in GROUP_NAMES if g in net_all.columns]
        sel_groups = st.multiselect(
            "Investor groups", groups, default=groups,
            format_func=GROUP_NAMES.get, key="cash_groups")
        cols = sel_groups or groups

        net = transforms.filter_dates(net_all, start, end)
        if net.empty:
            st.info("No cash-market data inside the selected period.")
        else:
            # period KPIs: total net flow per group over the selection
            ui.kpi_row([(f"{GROUP_NAMES[c]} — period net",
                         ui.fmt_brl_mm(net[c].sum()), None)
                        for c in cols][:5])

            view = st.radio("View", ["Daily bars", "Cumulative in period"],
                            horizontal=True, key="cash_view",
                            label_visibility="collapsed")
            c1, c2 = st.columns((7, 5))
            with c1:
                if view == "Daily bars":
                    st.plotly_chart(
                        charts.grouped_bars(net, "date", cols,
                                            names=GROUP_NAMES, height=380,
                                            stacked=True,
                                            title="Daily net flow (BRL)"),
                        width="stretch")
                else:
                    cum = net.copy()
                    for c in cols:
                        cum[c] = cum[c].cumsum()
                    st.plotly_chart(
                        charts.line(cum, "date", cols, names=GROUP_NAMES,
                                    height=380,
                                    title="Cumulative net flow over the "
                                          "selected period (BRL)"),
                        width="stretch")
            with c2:
                tot_s = pd.Series({GROUP_NAMES[c]: net[c].sum()
                                   for c in cols}).sort_values()
                st.plotly_chart(
                    charts.bar_signed(tot_s.index, tot_s.values, height=380,
                                      title="Period total by investor (BRL)",
                                      value_fmt=",.3s"),
                    width="stretch")

            if len(net) >= 10:
                win = st.slider("Rolling window (days)", 5, 63,
                                min(21, max(5, len(net) // 3)),
                                key="cash_roll")
                roll = net.copy()
                for c in cols:
                    roll[c] = roll[c].rolling(win, min_periods=3).mean()
                st.plotly_chart(
                    charts.line(roll, "date", cols, names=GROUP_NAMES,
                                height=320,
                                title=f"{win}-day rolling average daily "
                                      "net flow (BRL)"),
                    width="stretch")

            share_cols = [f"{g}_purchases_part" for g in cols
                          if f"{g}_purchases_part" in daily.columns]
            if share_cols:
                dshare = transforms.filter_dates(daily, start, end)
                st.plotly_chart(
                    charts.area(dshare, "date", share_cols,
                                names={f"{g}_purchases_part": n
                                       for g, n in GROUP_NAMES.items()},
                                height=300, pct=True,
                                title="Share of purchases by investor type"),
                    width="stretch")

            ui.download_button(net.rename(columns=GROUP_NAMES),
                               "Download net flows (CSV)",
                               "cash_market_net_flows.csv")
    ui.provenance_badge(prov_ip, "investors_participation")

# ---------------------------------------------------------------- futures
with tab_fut:
    pv = transforms.futures_net_by_category(ff)
    if pv.empty:
        st.warning("Futures flow data unavailable.")
    else:
        pv = pv[(pv.index >= start) & (pv.index <= end)]
        if pv.empty:
            st.info("No futures data inside the selected period.")
        else:
            cats = list(pv.columns)
            sel_cats = st.multiselect("Investor categories", cats,
                                      default=cats, key="fut_cats")
            pv = pv[sel_cats or cats]

            totals = pv.sum().sort_values()
            ui.kpi_row([(str(c).title(), ui.fmt_brl_mm(v), None)
                        for c, v in totals.items()][:5])

            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(
                    charts.bar_signed(totals.index, totals.values,
                                      height=380,
                                      title="Period net inflow by category "
                                            "(BRL)",
                                      value_fmt=",.3s"),
                    width="stretch")
            with c2:
                cum = pv.fillna(0).cumsum().reset_index()
                st.plotly_chart(
                    charts.line(cum, "data_pregao", list(pv.columns),
                                height=380,
                                title="Cumulative net inflow over the "
                                      "selected period (BRL)"),
                    width="stretch")

            last_day = pv.dropna(how="all")
            if len(last_day):
                snap = last_day.iloc[-1].sort_values()
                st.plotly_chart(
                    charts.bar_signed(snap.index, snap.values, height=300,
                                      title=f"Latest session — "
                                            f"{last_day.index[-1]:%Y-%m-%d}",
                                      value_fmt=",.3s"),
                    width="stretch")

            with st.expander("Daily table"):
                st.dataframe(pv.sort_index(ascending=False)
                             .style.format("{:,.0f}"), width="stretch")
            ui.download_button(pv.reset_index(),
                               "Download futures flows (CSV)",
                               "futures_net_flows.csv")
    ui.provenance_badge(prov_ff, "future_flows")

# --------------------------------------------------------- single-name
with tab_single:
    sec, _ = store.get_sectors()
    has_panel = {"cod_ativo", "data"}.issubset(sf.columns)
    if not has_panel:
        st.warning("Single-name flow panel unavailable in this data mode.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        investor = c1.selectbox("Investor", list(INVESTOR_LABELS),
                                format_func=INVESTOR_LABELS.get)
        window = c2.selectbox("Window", ["21d", "63d", "252d"])
        metric = c3.selectbox("Normalization",
                              ["flow", "to_adtv", "to_ff"],
                              format_func={"flow": "BRL",
                                           "to_adtv": "× ADTV",
                                           "to_ff": "% free float"}.get)
        top_n = c4.slider("Names per side", 5, 25, 12)

        snap = transforms.latest_snapshot(sf)
        snap = transforms.add_sector(snap, sec)
        if "macro_sector_xp" not in snap.columns or \
                snap["macro_sector_xp"].isna().mean() > 0.5:
            from data import demo
            snap = transforms.latest_snapshot(sf)
            snap = transforms.add_sector(snap, demo.sector_classification())

        f1, f2 = st.columns((3, 9))
        sector_col = f1.radio(
            "Sector level (xpqs taxonomy)",
            ["sector_xp", "macro_sector_xp"],
            format_func={"sector_xp": "XP sector",
                         "macro_sector_xp": "XP macro sector"}.get,
            key="sn_sector_level")
        if sector_col not in snap.columns:
            sector_col = "macro_sector_xp"
        sectors = sorted(snap[sector_col].dropna().unique()) \
            if sector_col in snap.columns else []
        sel_sec = f2.multiselect("Filter sectors (blank = all)", sectors,
                                 key="sn_sectors")

        col = (f"{window}_{investor}_flow" if metric == "flow"
               else f"{window}_{investor}_flow_{metric}")
        fmt = ",.3s" if metric == "flow" else ",.2f"

        if col not in snap.columns:
            st.info("Selected flow column not available.")
        else:
            view = snap if not sel_sec else \
                snap[snap[sector_col].isin(sel_sec)]
            ranked = view[["cod_ativo", sector_col, col]].dropna()
            movers = pd.concat([ranked.nlargest(top_n, col),
                                ranked.nsmallest(top_n, col)]) \
                .drop_duplicates("cod_ativo").sort_values(col)

            b1, b2 = st.columns((6, 6))
            with b1:
                st.plotly_chart(
                    charts.bar_signed(movers["cod_ativo"], movers[col],
                                      height=520,
                                      title=f"Largest {window} "
                                            f"{INVESTOR_LABELS[investor]} "
                                            "in/outflows — latest date",
                                      value_fmt=fmt),
                    width="stretch")
            with b2:
                agg = transforms.aggregate_sector_flows(
                    view, investor, window, metric, sector_col)
                agg_title = {
                    "flow": "Sector total flow (Σ BRL)",
                    "to_adtv": "Sector flow ÷ sector ADTV "
                               "(Σ flows / Σ implied ADTVs)",
                    "to_ff": "Sector flow ÷ sector free float "
                             "(Σ flows / Σ implied FF values)",
                }[metric]
                if agg.empty:
                    st.info("Sector aggregation unavailable — flow/ratio "
                            "columns missing for this selection.")
                else:
                    st.plotly_chart(
                        charts.bar_signed(agg.index, agg.values, height=520,
                                          title=agg_title, value_fmt=fmt),
                        width="stretch")

            # ---- ticker drill-down: flow history inside the period ----
            st.subheader("Ticker drill-down")
            tickers = sorted(sf["cod_ativo"].dropna().unique())
            tk = st.selectbox("Ticker", tickers,
                              index=tickers.index("PETR4")
                              if "PETR4" in tickers else 0)
            full = sf[sf["cod_ativo"] == tk].sort_values("data")
            hist = transforms.filter_dates(full, start, end, date_col="data")
            if hist.empty and not full.empty:
                # source calendar doesn't overlap the selected period (can
                # happen in dev, where real samples are stale) — degrade to
                # the ticker's most recent 12 months instead of a blank panel
                anchor = full["data"].max()
                hist = full[full["data"] >= anchor - pd.Timedelta(days=365)]
                st.caption("⚠ Selected period is outside this source's "
                           "calendar — showing the most recent 12 months "
                           "instead.")
            flow_cols = {f"{window}_{inv}_flow": lbl
                         for inv, lbl in INVESTOR_LABELS.items()
                         if f"{window}_{inv}_flow" in hist.columns}
            if hist.empty or not flow_cols:
                st.info("No history available for this ticker.")
            else:
                st.plotly_chart(
                    charts.line(hist, "data", list(flow_cols),
                                names=flow_cols, height=380,
                                title=f"{tk} — rolling {window} flow by "
                                      "investor (BRL)"),
                    width="stretch")
            ui.download_button(movers, "Download movers (CSV)",
                               f"singlename_{investor}_{window}.csv")
    ui.provenance_badge(prov_sf, "singlename_flows")
