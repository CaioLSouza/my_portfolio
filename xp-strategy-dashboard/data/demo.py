"""Coherent synthetic "demo universe" for development mode.

The GitHub samples are tiny extracts (10 rows) and several lost their
``(cod_ativo, data)`` index columns on export. So that every dashboard
module can demonstrate its full functionality during development, this
module fabricates a *coherent* fake market — same tickers, sectors and
prices across all derived sources — matching the real prod schemas.

Everything produced here is flagged ``is_synthetic=True`` by the store and
badged in the UI. In ``DATA_SOURCE=prod`` this module is never used except
as a last-resort fallback when a network file cannot be read.
"""

from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Dict

import numpy as np
import pandas as pd

# ~60 liquid B3 names with a plausible XP macro-sector mapping.
UNIVERSE: Dict[str, str] = {
    "PETR4": "Oil, Gas & Petrochemicals", "PETR3": "Oil, Gas & Petrochemicals",
    "PRIO3": "Oil, Gas & Petrochemicals", "RRRP3": "Oil, Gas & Petrochemicals",
    "UGPA3": "Oil, Gas & Petrochemicals", "VBBR3": "Oil, Gas & Petrochemicals",
    "VALE3": "Metals & Mining", "GGBR4": "Metals & Mining", "CSNA3": "Metals & Mining",
    "USIM5": "Metals & Mining", "CMIN3": "Metals & Mining", "CBAV3": "Metals & Mining",
    "ITUB4": "Banks", "BBDC4": "Banks", "BBAS3": "Banks", "SANB11": "Banks",
    "BPAC11": "Banks", "ITSA4": "Banks",
    "B3SA3": "Financials Non-Banks", "BBSE3": "Financials Non-Banks",
    "CXSE3": "Financials Non-Banks", "PSSA3": "Financials Non-Banks",
    "ABEV3": "Agri, Food & Beverages", "JBSS3": "Agri, Food & Beverages",
    "MBRF3": "Agri, Food & Beverages", "SMTO3": "Agri, Food & Beverages",
    "SLCE3": "Agri, Food & Beverages", "RAIZ4": "Agri, Food & Beverages",
    "SUZB3": "Pulp & Paper", "KLBN11": "Pulp & Paper",
    "ELET3": "Utilities", "CPLE6": "Utilities", "CMIG4": "Utilities",
    "EQTL3": "Utilities", "SBSP3": "Utilities", "EGIE3": "Utilities", "AXIA3": "Utilities",
    "LREN3": "Retail", "MGLU3": "Retail", "ASAI3": "Retail", "PCAR3": "Retail",
    "GMAT3": "Retail", "AZZA3": "Retail",
    "RDOR3": "Health Care", "HAPV3": "Health Care", "FLRY3": "Health Care",
    "HYPE3": "Health Care",
    "RENT3": "Transportation", "RAIL3": "Transportation", "CCRO3": "Transportation",
    "VAMO3": "Transportation", "MOTV3": "Transportation",
    "WEGE3": "Capital Goods", "EMBJ3": "Capital Goods", "TUPY3": "Capital Goods",
    "TOTS3": "TMT", "VIVT3": "TMT", "TIMS3": "TMT", "LWSA3": "TMT",
    "MULT3": "Real Estate", "CYRE3": "Real Estate", "EZTC3": "Real Estate",
    "IGTI11": "Real Estate",
    "YDUQ3": "Education", "COGN3": "Education",
}

N_DAYS = 3 * 252  # ~3 years of business days
SEED = 20260714

INVESTOR_TYPES = ("foreigners", "retail", "local_institutions", "others")
FLOW_WINDOWS = ("21d", "63d", "252d")

FACTOR_FAMILIES = {
    "momentum": ["12m1_momentum-ALL", "6m_momentum-ALL", "price_range-ALL"],
    "value": ["earnings_yield_ltm-ALL", "ebitda_yield_ltm-ALL", "composite-ALL"],
    "quality": ["roe-ALL", "gross_margin-ALL", "composite-ALL"],
    "risk": ["low_beta-ALL", "low_vol-ALL"],
    "size": ["small_size-ALL"],
    "short_interest": ["short_interest_pct-ALL", "composite-ALL"],
    "sellside_revisions": ["earnings_composite-ALL", "composite-ALL"],
}


def _dates() -> pd.DatetimeIndex:
    return pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=N_DAYS)


@lru_cache(maxsize=1)
def _price_panel() -> pd.DataFrame:
    """Backbone: GBM price paths per ticker with a common market driver."""
    rng = np.random.default_rng(SEED)
    dates = _dates()
    tickers = list(UNIVERSE)
    market = rng.normal(0.0004, 0.011, len(dates))
    sector_shift = {s: rng.normal(0, 0.004, len(dates)) for s in set(UNIVERSE.values())}
    frames = []
    for tk in tickers:
        beta = rng.uniform(0.6, 1.4)
        idio = rng.normal(0, 0.014, len(dates))
        rets = beta * market + 0.6 * sector_shift[UNIVERSE[tk]] + idio
        px = float(rng.uniform(8, 90)) * np.exp(np.cumsum(rets))
        vol = rng.lognormal(17, 0.8) * (1 + 0.5 * rng.random(len(dates)))
        frames.append(
            pd.DataFrame(
                {
                    "cod_ativo": tk,
                    "data": dates,
                    "close_price": px,
                    "adj_close_price": px,
                    "open_price": px * (1 + rng.normal(0, 0.004, len(dates))),
                    "high_price": px * (1 + np.abs(rng.normal(0, 0.008, len(dates)))),
                    "low_price": px * (1 - np.abs(rng.normal(0, 0.008, len(dates)))),
                    "avg_price": px,
                    "trading_volume": vol,
                    "number_of_trades": (vol / 5000).astype(int),
                    "number_of_shares_traded": (vol / px).astype(int),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def market_data() -> pd.DataFrame:
    return _price_panel().copy()


def sector_classification() -> pd.DataFrame:
    rows = [
        {
            "cod_ativo": tk,
            "name": tk[:-1].title(),
            "type": "Units" if tk.endswith("11") else "ON/PN",
            "GICS_sector": sec,
            "adjusted_GICS_sector": sec,
            "macro_sector_xp": sec,
            "sector_xp": sec,
            "super_sector_xp": sec,
        }
        for tk, sec in UNIVERSE.items()
    ]
    return pd.DataFrame(rows)


def market_cap() -> pd.DataFrame:
    px = _price_panel()
    rng = np.random.default_rng(SEED + 1)
    shares = {tk: rng.uniform(5e8, 5e9) for tk in UNIVERSE}
    df = px[["cod_ativo", "data", "close_price"]].copy()
    df["market_cap_class"] = df["close_price"] * df["cod_ativo"].map(shares)
    df["market_cap_company"] = df["market_cap_class"] * 1.3
    return df.drop(columns="close_price")


def index_composition() -> pd.DataFrame:
    mc = market_cap()
    last = mc.groupby("cod_ativo", as_index=False).last()
    total = last["market_cap_class"].sum()
    dates = _dates()[-252:]
    rows = []
    for _, r in last.iterrows():
        w = 100 * r["market_cap_class"] / total
        rows.append(pd.DataFrame({
            "cod_ativo": r["cod_ativo"], "data": dates,
            "IBOV": w, "SMLL": np.nan, "MLCX": w, "IBX50": w, "IBX100": w,
        }))
    return pd.concat(rows, ignore_index=True)


def short_selling() -> pd.DataFrame:
    px = _price_panel()
    rng = np.random.default_rng(SEED + 2)
    frames = []
    for tk, grp in px.groupby("cod_ativo"):
        base = rng.uniform(0.01, 0.12)
        si_pct = np.clip(base + np.cumsum(rng.normal(0, 0.002, len(grp))), 0.002, 0.35)
        ff = rng.uniform(3e8, 3e9)
        si = si_pct * ff
        adtv = grp["number_of_shares_traded"].rolling(21, min_periods=1).mean().values
        frames.append(pd.DataFrame({
            "cod_ativo": tk,
            "data": grp["data"].values,
            "short_interest": si,
            "short_interest_pct": si_pct,
            "short_interest_value": si * grp["close_price"].values,
            "lending_rate": np.clip(rng.normal(2.5, 1.2, len(grp)) * si_pct / 0.06, 0.1, 25),
            # sqrt-compress so the cross-section spreads over a realistic
            # 0.3–25d range instead of piling up at a clip boundary
            "days_to_cover": np.clip(np.sqrt(si / np.maximum(adtv, 1)) / 1.6,
                                     0.3, 25),
            "free_float": ff,
            "avg_shorted_price": grp["close_price"].values,
            "market_cap_class": grp["close_price"].values * ff * 2,
            "market_cap_company": grp["close_price"].values * ff * 2.5,
            "surprise_in_si": rng.normal(0, 1, len(grp)),
        }))
    return pd.concat(frames, ignore_index=True)


def singlename_flows() -> pd.DataFrame:
    px = _price_panel()
    rng = np.random.default_rng(SEED + 3)
    frames = []
    for tk, grp in px.groupby("cod_ativo"):
        n = len(grp)
        adtv_brl = (grp["trading_volume"]).rolling(21, min_periods=1).mean().values
        out = {"cod_ativo": tk, "data": grp["data"].values}
        for inv in INVESTOR_TYPES:
            daily = rng.normal(0, 0.08, n) * adtv_brl
            out[f"daily_{inv}_flow"] = daily
            s = pd.Series(daily)
            for w, k in zip((21, 63, 252), FLOW_WINDOWS):
                roll = s.rolling(w, min_periods=5).sum().values
                out[f"{k}_{inv}_flow"] = roll
                out[f"{k}_{inv}_flow_to_adtv"] = roll / np.maximum(adtv_brl, 1)
                out[f"{k}_{inv}_flow_to_ff"] = roll / 5e9
        frames.append(pd.DataFrame(out))
    return pd.concat(frames, ignore_index=True)


def _snapshot_features() -> pd.DataFrame:
    """Latest cross-section used by factor_zoo/consensus fabrication."""
    px = _price_panel()
    rng = np.random.default_rng(SEED + 4)
    last = px.sort_values("data").groupby("cod_ativo").tail(280)
    rows = []
    for tk, grp in last.groupby("cod_ativo"):
        close = grp["close_price"].values
        ret_1m = close[-1] / close[-22] - 1 if len(close) > 22 else np.nan
        ret_3m = close[-1] / close[-64] - 1 if len(close) > 64 else np.nan
        ret_12m = close[-1] / close[0] - 1
        rows.append({
            "cod_ativo": tk,
            "data": grp["data"].iloc[-1],
            "close_price": close[-1],
            "1m_momentum": ret_1m,
            "3m_momentum": ret_3m,
            "12m_momentum": ret_12m,
            "260d_volatility": float(np.std(np.diff(np.log(close))) * np.sqrt(252)),
            "earnings_yield_ltm": rng.normal(0.09, 0.05),
            "earnings_yield_fwd": rng.normal(0.10, 0.05),
            "ebitda_yield_fwd": rng.normal(0.14, 0.06),
            "dividend_yield_ltm": np.clip(rng.normal(0.05, 0.03), 0, 0.15),
            "book_yield_ltm": rng.normal(0.6, 0.3),
            "fcf_yield_ltm": rng.normal(0.07, 0.05),
            "roe": np.clip(rng.normal(0.15, 0.1), -0.2, 0.45),
            "roic": np.clip(rng.normal(0.12, 0.08), -0.15, 0.4),
            "gross_margin": np.clip(rng.normal(0.35, 0.15), 0.05, 0.9),
            "ebitda_margin": np.clip(rng.normal(0.22, 0.12), 0.02, 0.7),
            "beta": rng.uniform(0.5, 1.5),
        })
    return pd.DataFrame(rows)


def factor_zoo() -> pd.DataFrame:
    feats = _snapshot_features()
    sh = short_selling().sort_values("data").groupby("cod_ativo").tail(1)
    fl = singlename_flows().sort_values("data").groupby("cod_ativo").tail(1)
    mc = market_cap().sort_values("data").groupby("cod_ativo").tail(1)
    df = (
        feats.merge(sh.drop(columns=["data"]), on="cod_ativo", how="left", suffixes=("", "_ss"))
        .merge(fl.drop(columns=["data"]), on="cod_ativo", how="left")
        .merge(mc[["cod_ativo", "market_cap_class"]], on="cod_ativo", how="left",
               suffixes=("", "_mc"))
    )
    return df


def consensus() -> pd.DataFrame:
    feats = _snapshot_features()[["cod_ativo", "data", "close_price"]]
    rng = np.random.default_rng(SEED + 5)
    n = len(feats)
    df = feats.copy()
    df["price_to_earnings_fwd"] = np.clip(rng.normal(11, 5, n), 3, 40)
    df["ev_to_ebitda_fwd"] = np.clip(rng.normal(6.5, 2.5, n), 1.5, 20)
    df["analyst_rec"] = np.clip(rng.normal(2.2, 0.5, n), 1, 5)  # 1=strong buy
    df["analyst_number_earnings"] = rng.integers(2, 16, n)
    df["long_term_growth"] = rng.normal(0.10, 0.07, n)
    for w in (63, 126, 252):
        df[f"analyst_revisions_netincome_momentum_{w}d_blended"] = rng.normal(0, 0.05, n)
        df[f"analyst_revisions_ebitda_momentum_{w}d_blended"] = rng.normal(0, 0.04, n)
        df[f"analyst_revisions_sales_momentum_{w}d_blended"] = rng.normal(0, 0.03, n)
        df[f"analyst_revision_rec_momentum_{w}d"] = rng.normal(0, 0.15, n)
    return df


def factor_returns() -> Dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED + 6)
    dates = _dates()
    cols = {}
    drift = {"Top": 0.00035, "Bottom": 0.00010, "LS": 0.00016}
    sheets: Dict[str, pd.DataFrame] = {}
    for sheet, mu in drift.items():
        cols = {"data": dates}
        for fam, factors in FACTOR_FAMILIES.items():
            for f in factors:
                rets = rng.normal(mu, 0.006 if sheet != "LS" else 0.004, len(dates))
                cols[f"{fam}/{f}"] = np.exp(np.cumsum(rets))
        sheets[sheet] = pd.DataFrame(cols)
    return sheets


def sector_index() -> pd.DataFrame:
    px = _price_panel().merge(
        sector_classification()[["cod_ativo", "macro_sector_xp"]], on="cod_ativo"
    )
    mc = market_cap()[["cod_ativo", "data", "market_cap_class"]]
    px = px.merge(mc, on=["cod_ativo", "data"])
    px["ret"] = px.groupby("cod_ativo")["close_price"].pct_change().fillna(0)
    px["w"] = px["market_cap_class"]
    agg = px.groupby(["data", "macro_sector_xp"]).apply(
        lambda g: np.average(g["ret"], weights=g["w"]), include_groups=False
    ).unstack()
    idx = (1 + agg.fillna(0)).cumprod()
    mkt = px.groupby("data").apply(
        lambda g: np.average(g["ret"], weights=g["w"]), include_groups=False
    )
    idx["Ibovespa"] = (1 + mkt.fillna(0)).cumprod() * 130_000 / (1 + mkt.fillna(0)).prod()
    return idx.reset_index().rename(columns={"index": "data"})


def investors_participation() -> Dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED + 7)
    dates = _dates()[-252:]
    groups = ("institutional_investors", "financial_institutions",
              "foreign_investors", "individual_investors", "others")
    share = {"institutional_investors": .28, "financial_institutions": .04,
             "foreign_investors": .55, "individual_investors": .11, "others": .02}
    total = 25e9
    daily = {"date": dates}
    for g in groups:
        buys = total * share[g] * (1 + rng.normal(0, 0.15, len(dates)))
        sells = buys * (1 + rng.normal(0, 0.05, len(dates)))
        daily[f"{g}_purchases"] = buys
        daily[f"{g}_sales"] = sells
        daily[f"{g}_purchases_part"] = buys / (2 * total)
        daily[f"{g}_sales_part"] = sells / (2 * total)
    ddf = pd.DataFrame(daily)
    cum = ddf.copy()
    month = cum["date"].dt.to_period("M")
    for c in cum.columns:
        if c != "date" and not c.endswith("_part"):
            cum[c] = cum.groupby(month)[c].cumsum()
    return {"Daily": ddf, "Cumulative": cum}


def future_flows() -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 8)
    dates = _dates()[-252:]
    cats = ("INVESTIDOR NAO RESIDENTE", "FUNDOS", "PESSOA FISICA",
            "INSTITUICAO FINANCEIRA", "OUTROS")
    rows = []
    for d in dates:
        for c in cats:
            compra = abs(rng.normal(5e10, 2e10))
            venda = compra - rng.normal(0, 5e8)
            rows.append({"data_pregao": d, "macro_produto": "FUTURO",
                         "categoria_investidor": c, "QTD": int(rng.integers(20, 300)),
                         "CAPT_LIQ": compra - venda, "COMPRA": compra, "VENDA": venda,
                         "VOL_NEGOCIADO": compra + venda})
    return pd.DataFrame(rows)


def comp_sheet() -> pd.DataFrame:
    fz = _snapshot_features()
    rng = np.random.default_rng(SEED + 9)
    sec = sector_classification()[["cod_ativo", "macro_sector_xp"]]
    analysts = ["A. Silva", "B. Costa", "C. Rocha", "D. Souza", "E. Lima", "F. Alves"]
    df = fz[["cod_ativo", "close_price"]].merge(sec, on="cod_ativo")
    n = len(df)
    df = df.rename(columns={"cod_ativo": "TICKER", "macro_sector_xp": "SECTOR_XP"})
    df["NAME"] = df["TICKER"].str[:-1].str.title()
    df["LEAD_ANALYST"] = rng.choice(analysts, n)
    df["PDATE"] = pd.Timestamp.today().normalize() - pd.to_timedelta(
        rng.integers(5, 200, n), unit="D")
    df["RECOMMENDATION"] = rng.choice(["Buy", "Neutral", "Sell"], n, p=[.55, .35, .10])
    df["RESTRICTED"] = rng.random(n) < 0.06
    df["TARGET"] = df["close_price"] * (1 + rng.normal(0.18, 0.2, n))
    df["WACC"] = np.clip(rng.normal(0.13, 0.02, n), 0.08, 0.2)
    df["KE"] = df["WACC"] + 0.02
    df["KD"] = df["WACC"] - 0.03
    return df


def bdr_market_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 10)
    dates = _dates()[-252:]
    frames = []
    for tk in ("MMMC34<XBSP>", "AAPL34<XBSP>", "MSFT34<XBSP>", "AMZO34<XBSP>"):
        px = float(rng.uniform(30, 90)) * np.exp(np.cumsum(rng.normal(4e-4, 0.012, len(dates))))
        frames.append(pd.DataFrame({
            "Ativo": tk, "Data": dates, "close_price": px, "adj_close_price": px,
            "open_price": px, "high_price": px * 1.01, "low_price": px * 0.99,
            "avg_price": px, "trading_volume": rng.lognormal(14, 0.5, len(dates)),
            "number_of_trades": rng.integers(1, 500, len(dates)),
            "number_of_shares_traded": rng.integers(100, 50000, len(dates)),
        }))
    return pd.concat(frames, ignore_index=True)


def performance_carteiras() -> Dict[str, pd.DataFrame]:
    """Fabricated parsed-portfolio outputs (used only if the real file fails)."""
    rng = np.random.default_rng(SEED + 11)
    months = pd.date_range(end=pd.Timestamp.today().normalize(), periods=18, freq="ME")
    tickers = list(UNIVERSE)[:12]
    comp = pd.DataFrame({
        "portfolio": "TOP Ações XP", "ticker": tickers,
        "weight": np.full(len(tickers), 100 / len(tickers)),
    })
    perf = pd.DataFrame({
        "portfolio": "TOP Ações XP", "date": months,
        "portfolio_return": rng.normal(0.01, 0.04, len(months)),
        "benchmark_return": rng.normal(0.008, 0.045, len(months)),
    })
    return {"composition": comp, "performance": perf}


GENERATORS = {
    "market_data": market_data,
    "sector_classification": sector_classification,
    "market_cap": market_cap,
    "index_composition": index_composition,
    "short_selling": short_selling,
    "singlename_flows": singlename_flows,
    "factor_zoo": factor_zoo,
    "consensus": consensus,
    "factor_returns": factor_returns,
    "sector_index": sector_index,
    "investors_participation": investors_participation,
    "future_flows": future_flows,
    "comp_sheet": comp_sheet,
    "bdr_market_data": bdr_market_data,
    "performance_carteiras": performance_carteiras,
}
