"""XP Equity Strategy Dashboard — entrypoint / router.

Run with:  streamlit run app.py
Mode:      DATA_SOURCE=github (dev, default) | DATA_SOURCE=prod (corporate)
"""

from __future__ import annotations

import streamlit as st

pages = [
    st.Page("views/cockpit.py", title="Cockpit", icon="🎛️", default=True),
    st.Page("views/flow_monitor.py", title="Flow Monitor", icon="💧"),
    st.Page("views/xp_portfolios.py", title="XP Portfolios", icon="🗂️"),
    st.Page("views/factor_monitor.py", title="Factor Monitor", icon="🧭"),
    st.Page("views/valuation_screener.py", title="Valuation Screener", icon="🔎"),
    st.Page("views/short_interest.py", title="Short Interest", icon="📉"),
    st.Page("views/research_coverage.py", title="Research Coverage", icon="📋"),
    st.Page("views/sector_view.py", title="Sector View", icon="🏭"),
    st.Page("views/data_health.py", title="Data Health", icon="🩺"),
]

st.navigation(pages).run()
