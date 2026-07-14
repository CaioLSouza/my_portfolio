"""Data Health — per-source status, freshness and provenance."""

from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from components import ui
from data import store

ui.page_setup("Data Health", "🩺")
ui.page_header("Data Health",
               "Where every panel's data comes from, how fresh it is, and "
               "whether a synthetic stand-in is active.")
ui.mode_banner()

provs = store.all_provenance()

rows = []
for key, p in provs.items():
    rows.append({
        "source": key,
        "origin": "SYNTHETIC" if p.is_synthetic else "REAL",
        "why synthetic": p.reason,
        "data as of": p.as_of,
        "rows": p.n_rows,
        "file modified": p.last_modified,
        "location (current mode)": p.location,
    })
df = pd.DataFrame(rows).set_index("source")

n_synth = int((df["origin"] == "SYNTHETIC").sum())
ui.kpi_row([
    ("Mode", config.DATA_SOURCE.upper(), None),
    ("Sources", str(len(df)), None),
    ("Real", str(len(df) - n_synth), None),
    ("Synthetic", str(n_synth), None),
])
st.divider()


def _color_origin(v: str) -> str:
    return ("background-color:#fdeaea;color:#d03b3b;font-weight:600"
            if v == "SYNTHETIC"
            else "background-color:#e7f2e7;color:#006300;font-weight:600")


st.dataframe(df.style.map(_color_origin, subset=["origin"]),
             width="stretch", height=580)

st.caption(
    f"Cache directory: `{config.CACHE_DIR}` · memory TTL "
    f"{config.MEMORY_TTL_SECONDS // 60} min · disk cache max age "
    f"{config.DISK_CACHE_MAX_AGE_SECONDS // 3600} h. All reads are "
    "read-only; nothing is ever written to the network share and no data "
    "leaves this machine in prod mode."
)
