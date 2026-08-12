# EMR Masking Workbench

FastAPI backend + React/Vite frontend for comparing PII masking modules
(rule-based + KLUE NER + LLM prompt) on EMR text, inspecting spans, and
labeling/evaluating results.

## Setup

### Backend

```powershell
# Windows
cd backend
setup.bat
```

```bash
# macOS / Linux
cd backend
./setup.sh
```

Needs Python 3.13 + internet access on first run:
- installs pinned dependencies from `requirements.txt` (no local `.venv` is
  committed — the one on this machine has a hardcoded Windows path and
  won't work elsewhere)
- the `klue_ner` module downloads `Leo97/KoELECTRA-small-v3-modu-ner` from
  Hugging Face Hub the first time it runs (cached locally after that)

Set `ANTHROPIC_API_KEY` in your environment before using the `llm_prompt`
module — it's read from the environment only, nothing is hardcoded or
committed.

Run the API:

```powershell
# Windows
.venv\Scripts\python.exe -m uvicorn api.main:app --reload
```

```bash
# macOS / Linux
.venv/bin/python -m uvicorn api.main:app --reload
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

`package-lock.json` already pins platform-specific native binaries
(Rolldown/oxlint/lightningcss) for both Windows and macOS (arm64 + x64), so
`npm ci` resolves the right ones automatically per machine.

## Tests

```powershell
# Windows (from backend/)
.venv\Scripts\python.exe -m pytest
```

```bash
# macOS / Linux (from backend/)
.venv/bin/python -m pytest
```

```bash
cd frontend && npm run test
```
