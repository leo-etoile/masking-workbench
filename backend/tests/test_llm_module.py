"""LLM 프롬프트 모듈 테스트 — anthropic 클라이언트를 모킹해 사용한다.

실제 네트워크 호출은 전혀 없다. 가짜 ``anthropic`` 모듈을 ``sys.modules``에
주입하고 다음을 검증한다: 타입 매핑, 스팬 재정렬(모든 출현 위치), 디스크
캐싱(두 번째 호출은 API를 건너뜀), 우아한 실패 에러.
"""

import sys
import types

import pytest

from core.spec import PIIType
from modules.models import llm_prompt
from modules.models.llm_prompt import MODULE as LLM

_MODEL_JSON = (
    '[{"type":"NAME","text":"홍길동","hint":"앞"},'
    '{"type":"RRN","text":"990101-1234567"},'
    '{"type":"BOGUS","text":"무시됨"}]'
)


def _make_fake_anthropic(call_counter):
    module = types.ModuleType("anthropic")

    class _Block:
        def __init__(self, text):
            self.text = text
            self.type = "text"

    class _Response:
        def __init__(self, text):
            self.content = [_Block(text)]

    class _Messages:
        def create(self, **kwargs):
            call_counter.append(kwargs)
            assert kwargs["temperature"] == 0
            assert kwargs["model"] == llm_prompt.MODEL
            return _Response(_MODEL_JSON)

    class _Client:
        def __init__(self, **kwargs):
            self.messages = _Messages()

    module.Anthropic = _Client
    return module


def test_detect_maps_types_and_anchors_all_occurrences(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_prompt, "_CACHE_DIR", tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    calls = []
    monkeypatch.setitem(sys.modules, "anthropic", _make_fake_anthropic(calls))

    text = "환자 홍길동 990101-1234567 재방문한 홍길동"
    spans = LLM.detect(text)

    # UNKNOWN 타입은 무시됨; 홍길동 2회 + RRN 1회 출현 => 스팬 3개.
    assert len(spans) == 3
    for span in spans:
        assert text[span.start:span.end] == span.text
    name_spans = [s for s in spans if s.type == PIIType.NAME]
    rrn_spans = [s for s in spans if s.type == PIIType.RRN]
    assert len(name_spans) == 2
    assert len(rrn_spans) == 1
    assert len(calls) == 1  # API called once


def test_cache_hit_skips_api(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_prompt, "_CACHE_DIR", tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    calls = []
    monkeypatch.setitem(sys.modules, "anthropic", _make_fake_anthropic(calls))

    text = "환자 홍길동 990101-1234567"
    first = LLM.detect(text)
    assert len(calls) == 1
    assert any(tmp_path.glob("*.json"))

    # 두 번째 호출: API가 예외를 던지게 만들어도 캐시가 요청을 처리해야 한다.
    def _boom(**kwargs):
        raise AssertionError("API should not be called on cache hit")

    sys.modules["anthropic"].Anthropic = lambda **kw: types.SimpleNamespace(
        messages=types.SimpleNamespace(create=_boom)
    )
    second = LLM.detect(text)
    assert len(calls) == 1  # unchanged
    assert [(s.start, s.end, s.type) for s in first] == [
        (s.start, s.end, s.type) for s in second
    ]


def test_missing_api_key_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_prompt, "_CACHE_DIR", tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "anthropic", _make_fake_anthropic([]))
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        LLM.detect("uncached text 123")


def test_missing_package_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_prompt, "_CACHE_DIR", tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    # 패키지가 설치되지 않은 상황을 시뮬레이션한다.
    monkeypatch.setitem(sys.modules, "anthropic", None)
    with pytest.raises(RuntimeError, match="anthropic"):
        LLM.detect("another uncached text 456")
