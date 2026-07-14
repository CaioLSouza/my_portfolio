@echo off
rem XP Equity Strategy Cockpit — corporate launcher (reads \\xpdocs\... read-only)
cd /d "%~dp0"
set DATA_SOURCE=prod
if exist .venv\Scripts\python.exe (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)
"%PY%" -m streamlit run app.py
pause
