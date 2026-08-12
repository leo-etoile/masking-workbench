@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found on PATH. Install Python 3.13 first: https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist .venv (
    echo [1/2] Creating virtual environment...
    python -m venv .venv
)

echo [2/2] Installing dependencies. Needs internet access...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency install failed. See the log above.
    pause
    exit /b 1
)

echo.
echo Setup complete. Set ANTHROPIC_API_KEY before using the LLM module.
echo First run also downloads Leo97/KoELECTRA-small-v3-modu-ner from Hugging Face Hub
echo (needs internet once, cached locally after that).
echo.
echo Run the API with:
echo   .venv\Scripts\python.exe -m uvicorn api.main:app --reload
pause
