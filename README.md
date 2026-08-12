# EMR Masking Workbench

EMR 텍스트에서 PII 마스킹 모듈(규칙 기반 + KLUE NER + LLM 프롬프트)의 결과를
비교하고, 탐지된 span을 확인하고, 라벨링/평가까지 할 수 있는 FastAPI 백엔드 +
React/Vite 프론트엔드 프로젝트.

## 설치

### 백엔드

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

Python 3.13 + 인터넷 연결이 필요합니다(최초 1회):
- `requirements.txt`에 고정된 버전으로 의존성 설치 (로컬 `.venv`는 커밋하지
  않음 — 이 컴퓨터의 `.venv`는 Windows 경로가 하드코딩돼 있어서 다른 곳에서는
  못 씀)
- `klue_ner` 모듈이 최초 실행 시 Hugging Face Hub에서
  `Leo97/KoELECTRA-small-v3-modu-ner` 모델을 내려받음(이후엔 로컬에 캐시됨)

`llm_prompt` 모듈을 쓰려면 `ANTHROPIC_API_KEY`를 환경변수로 설정해야 합니다 —
코드는 환경변수에서만 읽어오고, 키 값은 하드코딩되거나 커밋된 적 없습니다.

```bash
# macOS / Linux (현재 터미널 세션에만 적용)
export ANTHROPIC_API_KEY="your-key-here"

# macOS / Linux (새 터미널에서도 유지, macOS 기본 셸인 zsh 기준)
echo 'export ANTHROPIC_API_KEY="your-key-here"' >> ~/.zshrc && source ~/.zshrc
```

```powershell
# Windows (현재 세션에만 적용)
$env:ANTHROPIC_API_KEY = "your-key-here"

# Windows (새 터미널에서도 유지)
setx ANTHROPIC_API_KEY "your-key-here"
```

API 실행:

```powershell
# Windows
.venv\Scripts\python.exe -m uvicorn api.main:app --reload
```

```bash
# macOS / Linux
.venv/bin/python -m uvicorn api.main:app --reload
```

### 프론트엔드

```bash
cd frontend
npm ci
npm run dev
```

`package-lock.json`에 Windows/macOS(arm64 + x64) 양쪽 네이티브 바이너리
(Rolldown/oxlint/lightningcss)가 이미 고정돼 있어서, `npm ci`만 실행하면
각 머신에 맞는 걸 알아서 받아옵니다.

## 테스트

```powershell
# Windows (backend/ 안에서)
.venv\Scripts\python.exe -m pytest
```

```bash
# macOS / Linux (backend/ 안에서)
.venv/bin/python -m pytest
```

```bash
cd frontend && npm run test
```
