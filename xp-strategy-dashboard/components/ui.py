"""Shared UI helpers: KPI tiles, provenance badges, formatting, page chrome."""

from __future__ import annotations

from typing import Iterable, Optional, Tuple

import pandas as pd
import streamlit as st

import config
from data.store import Provenance

# design tokens (light theme; see .streamlit/config.toml)
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GOOD = "#006300"
BAD = "#d03b3b"
HAIRLINE = "#e1e0d9"


def page_setup(title: str, icon: str = "📈") -> None:
    st.set_page_config(page_title=f"{title} · XP Strategy", page_icon=icon,
                       layout="wide")
    st.markdown(
        f"""
        <style>
          .block-container {{ padding-top: 2.2rem; padding-bottom: 2rem; }}
          [data-testid="stMetricValue"] {{ font-size: 1.55rem; }}
          [data-testid="stMetricLabel"] {{ color: {INK_SECONDARY}; }}
          h1, h2, h3 {{ letter-spacing: -0.01em; }}
          .xp-badge {{
            display:inline-block; padding:2px 8px; border-radius:10px;
            font-size:0.72rem; font-weight:600; vertical-align:middle;
            margin-left:6px;
          }}
          .xp-badge-real {{ background:#e7f2e7; color:{GOOD}; }}
          .xp-badge-synth {{ background:#fdeaea; color:{BAD}; }}
          .xp-asof {{ color:{INK_MUTED}; font-size:0.75rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "") -> None:
    st.title(title)
    if subtitle:
        st.markdown(f"<span style='color:{INK_SECONDARY}'>{subtitle}</span>",
                    unsafe_allow_html=True)


def mode_banner() -> None:
    if config.DATA_SOURCE == "github":
        st.caption(
            "🔧 **DEV mode** (`DATA_SOURCE=github`) — public GitHub samples; "
            "panels marked **SYNTHETIC** run on generated demo data because "
            "the sample extract is too small. On the corporate machine set "
            "`DATA_SOURCE=prod` to read `\\\\xpdocs\\...` directly."
        )


def provenance_badge(prov: Provenance, label: str = "") -> None:
    """'data as of X' caption + real/synthetic badge for a panel."""
    name = label or prov.key
    if prov.is_synthetic:
        badge = "<span class='xp-badge xp-badge-synth'>SYNTHETIC</span>"
        why = f" — {prov.reason}" if prov.reason else ""
    else:
        badge = "<span class='xp-badge xp-badge-real'>REAL</span>"
        why = ""
    st.markdown(
        f"<div class='xp-asof'>{name} · data as of <b>{prov.as_of}</b>"
        f"{badge}{why}</div>",
        unsafe_allow_html=True,
    )


def kpi_row(items: Iterable[tuple]) -> None:
    """Row of KPI tiles: (label, value, delta) tuples; delta optional/None."""
    items = list(items)
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        label, value, delta = (item + (None,))[:3]
        with col:
            st.metric(label, value, delta=delta)


# --- interactive controls ---------------------------------------------------

_PRESET_DAYS = {"1M": 30, "3M": 91, "6M": 182, "12M": 365}
PRESETS = ("1M", "3M", "6M", "YTD", "12M", "All", "Custom")


def date_range_control(dates: pd.Series, key: str, default: str = "3M",
                       sidebar: bool = True) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Period selector: preset chips + custom from/to pickers.

    Clamps to the range actually present in ``dates`` and returns
    ``(start, end)`` timestamps (inclusive). Presets are anchored on the
    *latest data point*, not today, so stale samples still filter sensibly.
    """
    dates = pd.to_datetime(pd.Series(dates)).dropna()
    if dates.empty:
        today = pd.Timestamp.today().normalize()
        return today - pd.Timedelta(days=90), today
    dmin, dmax = dates.min().normalize(), dates.max().normalize()
    box = st.sidebar if sidebar else st
    box.markdown("**Period**")
    preset = box.radio("Period", PRESETS, index=PRESETS.index(default),
                       horizontal=not sidebar, key=f"{key}_preset",
                       label_visibility="collapsed")
    if preset == "Custom":
        start_d = box.date_input("From", value=dmin.date(),
                                 min_value=dmin.date(), max_value=dmax.date(),
                                 key=f"{key}_from")
        end_d = box.date_input("To", value=dmax.date(),
                               min_value=dmin.date(), max_value=dmax.date(),
                               key=f"{key}_to")
        start, end = pd.Timestamp(start_d), pd.Timestamp(end_d)
        if start > end:
            box.warning("'From' is after 'To' — dates swapped.")
            start, end = end, start
    elif preset == "All":
        start, end = dmin, dmax
    elif preset == "YTD":
        start = pd.Timestamp(year=dmax.year, month=1, day=1)
        end = dmax
    else:
        start = dmax - pd.Timedelta(days=_PRESET_DAYS[preset])
        end = dmax
    start = max(start, dmin)
    box.caption(f"{start:%Y-%m-%d} → {end:%Y-%m-%d}")
    return start, end


def download_button(df: pd.DataFrame, label: str, filename: str) -> None:
    """CSV export for the table/chart the user is looking at."""
    st.download_button(f"⬇ {label}", df.to_csv(index=False).encode("utf-8"),
                       file_name=filename, mime="text/csv")


# --- formatting -------------------------------------------------------------

def fmt_pct(x: Optional[float], digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and (x != x)):
        return "–"
    return f"{x * 100:,.{digits}f}%"


def fmt_num(x: Optional[float], digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and (x != x)):
        return "–"
    return f"{x:,.{digits}f}"


def fmt_brl_mm(x: Optional[float]) -> str:
    """Compact BRL: millions/billions."""
    if x is None or (isinstance(x, float) and (x != x)):
        return "–"
    ax = abs(x)
    if ax >= 1e9:
        return f"{x / 1e9:,.1f} bn"
    if ax >= 1e6:
        return f"{x / 1e6:,.1f} mm"
    return f"{x:,.0f}"
