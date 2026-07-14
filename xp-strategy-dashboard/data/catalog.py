"""Source catalog: the single source of truth for where data lives.

The catalog is a CSV published alongside the sample files
(``catalog.csv``). One row per source with both the corporate UNC path
(``prod_path`` + ``prod_filetype``) and the public sample location
(``github_raw_url`` + ``sample_filetype``). Nothing outside the catalog
hardcodes a data path.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd

import config

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SourceSpec:
    key: str
    prod_path: str
    prod_filetype: str
    sample_file: str
    sample_filetype: str
    csv_sep: str
    sheets: str
    github_raw_url: str
    description: str

    @property
    def filetype(self) -> str:
        """File type for the *current* mode (prod parquet != sample xlsx)."""
        return (
            self.prod_filetype
            if config.DATA_SOURCE == "prod"
            else self.sample_filetype
        ).strip().lower()

    @property
    def location(self) -> str:
        """Address of the file for the current mode."""
        return (
            self.prod_path if config.DATA_SOURCE == "prod" else self.github_raw_url
        )


def _parse_catalog(csv_text: str) -> Dict[str, SourceSpec]:
    df = pd.read_csv(io.StringIO(csv_text), dtype=str).fillna("")
    specs: Dict[str, SourceSpec] = {}
    for _, row in df.iterrows():
        spec = SourceSpec(
            key=row["key"].strip(),
            prod_path=row["prod_path"].strip(),
            prod_filetype=row["prod_filetype"].strip(),
            sample_file=row["sample_file"].strip(),
            sample_filetype=row["sample_filetype"].strip(),
            csv_sep=row.get("csv_sep", "").strip() or ",",
            sheets=row.get("sheets", "").strip(),
            github_raw_url=row["github_raw_url"].strip(),
            description=row.get("description", "").strip(),
        )
        specs[spec.key] = spec
    return specs


def _fetch_catalog_text() -> Optional[str]:
    """Download catalog.csv (github mode only). Returns None on failure."""
    if config.DATA_SOURCE == "prod":
        return None  # never touch the network in prod mode
    try:
        import requests

        resp = requests.get(config.CATALOG_URL, timeout=config.REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:  # noqa: BLE001 - any failure falls back to snapshot
        log.warning("Could not fetch catalog from GitHub (%s); using local snapshot", exc)
        return None


def load_catalog() -> Dict[str, SourceSpec]:
    """Load the source registry, preferring the live GitHub catalog in dev.

    Falls back to the vendored snapshot so the app still starts offline
    (and always in prod mode, which must not perform network calls).
    """
    text = _fetch_catalog_text()
    if text is None:
        text = config.CATALOG_LOCAL_FALLBACK.read_text(encoding="utf-8")
    specs = _parse_catalog(text)
    if not specs:
        raise RuntimeError("Catalog parsed to zero sources — check catalog.csv")
    return specs
