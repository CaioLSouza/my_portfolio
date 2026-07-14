"""Preflight check for the corporate (prod) environment.

Run this ONCE on the XP Windows machine before starting the dashboard:

    python scripts\\check_prod_env.py

It verifies, without loading any data and without any network access:
  1. Python version and required packages;
  2. that every catalog source's UNC path is reachable and readable;
  3. write access to the local ./.cache folder (never to the network).

Exit code 0 = ready to run; 1 = something needs attention (details printed).
Read-only: the script never writes to, moves or locks any network file.
"""

from __future__ import annotations

import importlib
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DATA_SOURCE", "prod")

REQUIRED_PACKAGES = ("streamlit", "pandas", "plotly", "openpyxl", "pyarrow")
MIN_PYTHON = (3, 10)

problems: list[str] = []


def check_python() -> None:
    ok = sys.version_info >= MIN_PYTHON
    print(f"[{'ok' if ok else 'FAIL'}] Python {sys.version.split()[0]} "
          f"(need >= {'.'.join(map(str, MIN_PYTHON))})")
    if not ok:
        problems.append("Python too old — install Python 3.10+")


def check_packages() -> None:
    for pkg in REQUIRED_PACKAGES:
        try:
            mod = importlib.import_module(pkg)
            ver = getattr(mod, "__version__", "?")
            print(f"[ok]   package {pkg} {ver}")
        except ImportError:
            print(f"[FAIL] package {pkg} missing")
            problems.append(
                f"missing package '{pkg}' — pip install -r requirements.txt "
                "(see DEPLOYMENT.md for the offline-wheels option)")


def check_sources() -> None:
    import config
    from data.catalog import load_catalog

    print(f"\nMode: DATA_SOURCE={config.DATA_SOURCE}")
    if config.DATA_SOURCE != "prod":
        print("       (set DATA_SOURCE=prod to check the corporate paths)")
    try:
        catalog = load_catalog()
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] could not load catalog: {exc}")
        problems.append("catalog unreadable — is data/catalog_snapshot.csv "
                        "present?")
        return
    print(f"[ok]   catalog loaded — {len(catalog)} sources\n")

    width = max(len(k) for k in catalog)
    for key, spec in catalog.items():
        path = Path(spec.prod_path)
        try:
            if path.exists():
                st_ = path.stat()
                mtime = datetime.fromtimestamp(st_.st_mtime)
                # readability probe: open for read and pull the first bytes
                with open(path, "rb") as fh:
                    fh.read(16)
                print(f"[ok]   {key:<{width}}  {st_.st_size/1e6:8.1f} MB  "
                      f"modified {mtime:%Y-%m-%d %H:%M}")
            else:
                print(f"[FAIL] {key:<{width}}  not found: {spec.prod_path}")
                problems.append(f"{key}: path not found (check share access "
                                "/ VPN / drive mapping)")
        except PermissionError:
            print(f"[FAIL] {key:<{width}}  permission denied")
            problems.append(f"{key}: no read permission on the share")
        except OSError as exc:
            print(f"[WARN] {key:<{width}}  {type(exc).__name__}: {exc} "
                  "(file may be locked — the app will retry and degrade "
                  "gracefully)")


def check_cache_dir() -> None:
    import config
    probe = config.CACHE_DIR / ".write_probe"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        print(f"\n[ok]   local cache writable: {config.CACHE_DIR}")
    except OSError as exc:
        print(f"\n[FAIL] cannot write to {config.CACHE_DIR}: {exc}")
        problems.append("local .cache folder not writable")


if __name__ == "__main__":
    print("XP Strategy Dashboard — production preflight\n" + "=" * 46)
    check_python()
    check_packages()
    check_sources()
    check_cache_dir()
    print("\n" + "=" * 46)
    if problems:
        print(f"{len(problems)} issue(s) to fix:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print("All checks passed — run:  start_dashboard.bat")
    sys.exit(0)
