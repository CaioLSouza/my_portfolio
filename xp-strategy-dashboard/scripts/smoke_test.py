"""Exercise every page headlessly with streamlit.testing.AppTest.

Run from the project root:  python scripts/smoke_test.py
Fails (exit 1) if any page raises an exception.
"""

from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PAGES = ["app.py"] + sorted(str(p.relative_to(ROOT)) for p in
                            (ROOT / "views").glob("*.py"))

failures = 0
for page in PAGES:
    at = AppTest.from_file(str(ROOT / page), default_timeout=180)
    at.run()
    errs = [e.value for e in at.exception]
    status = "FAIL" if errs else "ok"
    print(f"[{status}] {page}")
    for e in errs:
        failures += 1
        print(f"      {e}")

sys.exit(1 if failures else 0)
