"""Central configuration for the XP Strategy Dashboard.

One codebase, two data modes selected via the DATA_SOURCE environment variable:

- ``github`` (default): development mode. Each source is downloaded from its
  ``github_raw_url`` (small public samples) and cached under ``./.cache``.
- ``prod``: corporate mode. Each source is read from its UNC ``prod_path``
  (``\\\\xpdocs\\...``). No network calls are made in this mode.

All data access is strictly read-only. Cache artifacts stay inside the
project folder and never on the network share.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# --- mode switch -----------------------------------------------------------
DATA_SOURCE = os.environ.get("DATA_SOURCE", "github").strip().lower()
if DATA_SOURCE not in ("github", "prod"):
    DATA_SOURCE = "github"

# --- cache -----------------------------------------------------------------
CACHE_DIR = PROJECT_ROOT / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

# In-memory (st.cache_data) TTL, seconds. Prod files update ~daily; a short
# TTL keeps the app responsive while picking up intraday refreshes.
MEMORY_TTL_SECONDS = int(os.environ.get("XPSD_TTL", 15 * 60))

# On-disk cache max age for downloaded sample files (github mode only).
DISK_CACHE_MAX_AGE_SECONDS = int(os.environ.get("XPSD_DISK_TTL", 24 * 3600))

# --- catalog locations ------------------------------------------------------
CATALOG_BASE_URL = (
    "https://raw.githubusercontent.com/CaioLSouza/datasets/refs/heads/"
    "claude/s3-link-access-nzk1gb/xp-strategy-dashboard/"
)
CATALOG_URL = CATALOG_BASE_URL + "catalog.csv"

# Vendored snapshot used as offline fallback (kept in sync manually).
CATALOG_LOCAL_FALLBACK = PROJECT_ROOT / "data" / "catalog_snapshot.csv"

# --- misc ------------------------------------------------------------------
REQUEST_TIMEOUT_SECONDS = 30
APP_TITLE = "XP Equity Strategy Cockpit"
