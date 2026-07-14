"""Shared UI helpers: KPI tiles, provenance badges, formatting, page chrome."""

from __future__ import annotations

from typing import Iterable, Optional

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
