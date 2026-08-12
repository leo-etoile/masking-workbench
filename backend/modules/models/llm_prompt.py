"""AI 모듈: LLM 프롬프트 기반 PII 추출 (Claude).

LLM에게 한국어 진료 자유서술 텍스트에서 PII를 추출하도록 요청하고,
반환된 결과를 원문 텍스트에 재정렬(re-anchor)한 스팬으로 돌려준다.

핵심 동작
---------
* ``requires_external_network = True`` — 파이프라인이 synthetic 전용
  게이트로 감싸며, 비-synthetic 입력에서는 호출이 차단된다.
* ``anthropic`` SDK는 네트워크 호출 **내부에서** 지연 import하므로,
  패키지가 없어도 백엔드와 다른 모든 모듈은 정상 동작한다.
* 결정론성: ``temperature=0`` 고정, 결과는
  ``sha256(text + module id + MODULE_VERSION)`` 키로 디스크에 캐싱된다.
  캐시 적중 시 API 호출을 건너뛴다.
* 우아한 실패: ``anthropic`` 미설치 또는 ``ANTHROPIC_API_KEY`` 미설정 시
  :meth:`detect`가 명확한 ``RuntimeError``를 던지고, 파이프라인이 이를
  ``module_errors``에 기록한다(실행 전체를 죽이지 않는다).

스팬 재정렬(re-anchoring)
------------------------
모델은 오프셋이 아니라 표면 문자열을 반환한다. 반환된 각 문자열을
``str.find``로 원문에서 찾아(모든 출현이 각각 스팬이 됨)
``text[start:end] == span.text``를 보장한다.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import List

from core.spec import PIIType, Span

MODEL = "claude-sonnet-5"
MODULE_VERSION = "1"

_CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache" / "llm_prompt"

# 모델이 반환하는 enum 이름을 대소문자 구분 없이 받아들인다.
_TYPE_MAP = {t.value.upper(): t for t in PIIType}

_PROMPT_TEMPLATE = (
    "You are a PII detector for Korean clinical free text (진료기록).\n"
    "Find every piece of personally identifiable information in the text below.\n"
    "Return ONLY a JSON array. Each element must be an object with keys:\n"
    '  "type": one of {types}\n'
    '  "text": the exact surface string as it appears in the source\n'
    '  "hint": a short approximate location hint (optional)\n'
    "Do not add commentary, do not wrap the JSON in markdown fences.\n\n"
    "TEXT:\n{text}\n"
)


class LLMPromptModule:
    id = "llm_prompt"
    display_name = "LLM 프롬프트 추출 (Claude)"
    requires_external_network = True
    supported_types = tuple(PIIType)
    description = (
        "Claude LLM 기반. 정규식으로 잡기 힘든 이름/주소/병원명 등 모든 PII 유형을 "
        "자유서술 문맥에서 추출. 외부 네트워크 호출이 필요해 synthetic 데이터에서만 "
        "동작하며, temperature=0으로 결정론적이고 결과는 캐싱됨."
    )

    # -- 공개 API ----------------------------------------------------------

    def detect(self, text: str) -> List[Span]:
        items = self._load_cache(text)
        if items is None:
            raw = self._call_model(text)
            items = self._parse(raw)
            self._save_cache(text, items)
        return self._anchor(text, items)

    # -- 네트워크 ----------------------------------------------------------

    def _call_model(self, text: str) -> str:
        """Anthropic API를 호출해 원시 텍스트 응답을 반환한다.

        SDK나 API 키가 없으면 명확한 ``RuntimeError``를 던진다.
        """

        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - 환경 의존
            raise RuntimeError(
                "llm_prompt requires the 'anthropic' package, which is not "
                "installed. Install it or disable this module."
            ) from exc

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "llm_prompt requires the ANTHROPIC_API_KEY environment "
                "variable, which is not set."
            )

        client = anthropic.Anthropic(api_key=api_key)
        prompt = _PROMPT_TEMPLATE.format(
            types=", ".join(t.value for t in PIIType), text=text
        )
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_text(response)

    # -- 파싱 / 재정렬 -----------------------------------------------------

    @staticmethod
    def _parse(raw: str) -> List[dict]:
        """모델의 JSON 배열을 {type, text} dict 리스트로 파싱한다."""

        payload = _strip_fences(raw)
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            # 차선책: 첫 번째 [...] 블록을 추출해 재시도한다.
            match = re.search(r"\[.*\]", payload, re.DOTALL)
            if not match:
                return []
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                return []

        items: List[dict] = []
        if not isinstance(data, list):
            return items
        for entry in data:
            if not isinstance(entry, dict):
                continue
            raw_type = str(entry.get("type", "")).strip().upper()
            surface = entry.get("text", "")
            if raw_type not in _TYPE_MAP:
                continue  # 알 수 없는 타입은 무시
            if not isinstance(surface, str) or not surface:
                continue
            items.append({"type": raw_type, "text": surface})
        return items

    def _anchor(self, text: str, items: List[dict]) -> List[Span]:
        """반환된 각 표면 문자열의 위치를 원문 텍스트에서 찾는다."""

        spans: List[Span] = []
        for item in items:
            pii_type = _TYPE_MAP[item["type"]]
            surface = item["text"]
            start = text.find(surface)
            while start != -1:
                spans.append(
                    Span(
                        start=start,
                        end=start + len(surface),
                        type=pii_type,
                        module=self.id,
                        text=surface,
                    )
                )
                start = text.find(surface, start + 1)
        return spans

    # -- 캐시 --------------------------------------------------------------

    def _cache_path(self, text: str) -> Path:
        key = hashlib.sha256(
            (text + self.id + MODULE_VERSION).encode("utf-8")
        ).hexdigest()
        return _CACHE_DIR / f"{key}.json"

    def _load_cache(self, text: str) -> List[dict] | None:
        path = self._cache_path(text)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _save_cache(self, text: str, items: List[dict]) -> None:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._cache_path(text).write_text(
            json.dumps(items, ensure_ascii=False), encoding="utf-8"
        )


def _strip_fences(raw: str) -> str:
    """```json ... ``` 마크다운 펜스가 있으면 제거한다."""

    stripped = raw.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\n?", "", stripped)
        stripped = re.sub(r"\n?```$", "", stripped)
    return stripped.strip()


def _extract_text(response) -> str:
    """Anthropic Messages 응답(객체 또는 dict)에서 텍스트를 추출한다."""

    content = getattr(response, "content", None)
    if content is None and isinstance(response, dict):
        content = response.get("content")
    if content is None:
        return ""

    parts: List[str] = []
    for block in content:
        text_val = getattr(block, "text", None)
        if text_val is None and isinstance(block, dict):
            text_val = block.get("text")
        if text_val:
            parts.append(text_val)
    return "".join(parts)


MODULE = LLMPromptModule()
