# DEPLOYMENT — running on the XP corporate Windows machine

The app is fully self-contained: getting it onto the corporate machine is
copy → install packages → preflight → run. In `DATA_SOURCE=prod` it makes
**zero network calls** — it only reads the `\\xpdocs\...` files listed in
the catalog, read-only, and keeps its cache inside the project folder.

## 1. Get the code onto the machine

Any of these works — pick whichever the corporate policy allows:

- **git** (if github.com is reachable):
  `git clone https://github.com/CaioLSouza/my_portfolio.git`
  → use the `my_portfolio/xp-strategy-dashboard/` folder.
- **ZIP**: GitHub → Code → Download ZIP, extract, keep only
  `xp-strategy-dashboard/`.
- **Manual copy**: copy the `xp-strategy-dashboard/` folder from your
  personal machine (USB / corporate transfer tool). Nothing outside the
  folder is needed; `.cache/` contents can be deleted before copying.

## 2. Install Python + packages

Python **3.10+** (3.11 recommended). During install tick
*"Add python.exe to PATH"*.

### 2a. Machine with pip access (direct or via corporate proxy)

```bat
cd xp-strategy-dashboard
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If pip needs the corporate proxy:
`set HTTPS_PROXY=http://<user>:<pass>@proxy.xp.com:<port>` before the
install (ask infra for the real host/port), or point pip at the internal
mirror if XP runs one: `pip install -r requirements.txt -i <internal-index-url>`.

### 2b. Fully offline machine (pip blocked)

On your **personal** machine (same Python minor version, e.g. 3.11):

```bat
pip download -r requirements.txt -d wheels ^
    --platform win_amd64 --python-version 3.11 --only-binary=:all:
```

Copy the `wheels/` folder next to the project on the corporate machine and:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install --no-index --find-links wheels -r requirements.txt
```

## 3. Preflight (run once)

```bat
.venv\Scripts\activate
python scripts\check_prod_env.py
```

This verifies Python, packages, read access to all 15 UNC paths and local
cache writability — without loading data or touching the network. Fix
anything it flags (usually: share not mounted / no VPN / missing package).
A `[WARN] file may be locked` is fine — the app degrades gracefully and
retries on the next refresh.

## 4. Run

Double-click **`start_dashboard.bat`** (it sets `DATA_SOURCE=prod` and
starts Streamlit), or manually:

```bat
.venv\Scripts\activate
set DATA_SOURCE=prod
python -m streamlit run app.py
```

The browser opens at `http://localhost:8501`. First load of the big
parquets takes a moment; after that the 15-minute in-memory cache keeps
navigation instant. Check the **Data Health** page first — every source
should show origin **REAL**; anything SYNTHETIC there means the file
couldn't be read and shows the reason.

> Note: `start_dashboard.bat` assumes packages are on the default Python.
> If you used a venv, activate it first or edit the .bat to call
> `.venv\Scripts\python -m streamlit run app.py`.

## 5. Security posture (what the app does and doesn't do)

- Reads catalog paths **read-only**; never writes, moves or locks anything
  on `\\xpdocs\...`.
- In prod mode there are no downloads, no telemetry, no external calls
  (`requests` is only imported on the github-mode code path; Streamlit
  usage stats are disabled in `.streamlit/config.toml`).
- Cache and artifacts stay in `./.cache` inside the project folder.
- The dashboard binds to localhost by default; don't expose it with
  `--server.address 0.0.0.0` unless the desk wants LAN access and infra
  approves.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Source shows SYNTHETIC in Data Health | UNC path unreachable — check VPN/share permissions; reason column tells you the exact error |
| `performance_carteiras` fails | .xlsm open with exclusive lock — retry later; reading usually works even while others have it open |
| pip SSL errors behind proxy | use the proxy env vars above or the offline-wheels route |
| Very slow first load | normal for the big parquets over the network; subsequent loads hit the in-memory cache. TTL configurable via `XPSD_TTL` |
| `streamlit` not recognized | venv not activated — run `.venv\Scripts\activate` or use `python -m streamlit` |
