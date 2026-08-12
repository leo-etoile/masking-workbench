"""KLUE 사전학습 NER 모듈 테스트 — transformers 파이프라인을 모킹해 사용한다.

실제 모델 다운로드/추론은 전혀 없다. 가짜 ``transformers`` 모듈을
``sys.modules``에 주입하고 다음을 검증한다: 태그 매핑(PS/LC/OG만 사용, 나머지는
무시), 파이프라인은 인스턴스당 한 번만 로드, 우아한 실패 에러.
"""

import sys
import types

import pytest

from core.spec import PIIType
from modules.models.klue_ner import KlueNERModule

_FAKE_ENTITIES = [
    {"entity_group": "PS", "start": 3, "end": 6, "score": 0.99},
    {"entity_group": "LC", "start": 10, "end": 15, "score": 0.87},
    {"entity_group": "OG", "start": 20, "end": 25, "score": 0.75},
    {"entity_group": "DT", "start": 30, "end": 34, "score": 0.60},  # 무시되어야 함
]


def _make_fake_transformers(load_calls, entities=_FAKE_ENTITIES, on_load=None):
    module = types.ModuleType("transformers")

    def _fake_pipeline(task, model=None, aggregation_strategy=None):
        load_calls.append((task, model, aggregation_strategy))
        if on_load is not None:
            on_load()
        return lambda text: entities

    module.pipeline = _fake_pipeline
    return module


def test_detect_maps_supported_tags_and_ignores_others(monkeypatch):
    loads = []
    monkeypatch.setitem(sys.modules, "transformers", _make_fake_transformers(loads))
    module = KlueNERModule()

    text = "x" * 40
    spans = module.detect(text)

    assert len(spans) == 3  # DT 태그는 무시됨
    by_type = {s.type: s for s in spans}
    assert (by_type[PIIType.NAME].start, by_type[PIIType.NAME].end) == (3, 6)
    assert (by_type[PIIType.ADDRESS].start, by_type[PIIType.ADDRESS].end) == (10, 15)
    assert (by_type[PIIType.HOSPITAL].start, by_type[PIIType.HOSPITAL].end) == (20, 25)
    for span in spans:
        assert span.text == text[span.start:span.end]
        assert span.module == "klue_ner"


def test_pipeline_loaded_once_per_instance(monkeypatch):
    loads = []
    monkeypatch.setitem(sys.modules, "transformers", _make_fake_transformers(loads))
    module = KlueNERModule()

    module.detect("첫 번째 호출 텍스트")
    module.detect("두 번째 호출 텍스트")

    assert len(loads) == 1  # 파이프라인은 한 번만 생성됨
    assert loads[0][1] == "Leo97/KoELECTRA-small-v3-modu-ner"


def test_missing_package_raises(monkeypatch):
    # 패키지가 설치되지 않은 상황을 시뮬레이션한다.
    monkeypatch.setitem(sys.modules, "transformers", None)
    module = KlueNERModule()
    with pytest.raises(RuntimeError, match="transformers"):
        module.detect("uncached text")


def test_model_load_failure_raises(monkeypatch):
    module_ = types.ModuleType("transformers")

    def _raise(*args, **kwargs):
        raise OSError("network unreachable")

    module_.pipeline = _raise
    monkeypatch.setitem(sys.modules, "transformers", module_)

    module = KlueNERModule()
    with pytest.raises(RuntimeError, match="klue_ner"):
        module.detect("uncached text")
