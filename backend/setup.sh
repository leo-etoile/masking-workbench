#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 not found. Install Python 3.13 first: https://www.python.org/downloads/"
    exit 1
fi

if [ ! -d .venv ]; then
    echo "[1/2] Creating virtual environment..."
    python3 -m venv .venv
fi

echo "[2/2] Installing dependencies. Needs internet access..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo
echo "Setup complete. Set ANTHROPIC_API_KEY before using the LLM module."
echo "First run also downloads Leo97/KoELECTRA-small-v3-modu-ner from Hugging Face Hub"
echo "(needs internet once, cached locally after that)."
echo
echo "Run the API with:"
echo "  .venv/bin/python -m uvicorn api.main:app --reload"
