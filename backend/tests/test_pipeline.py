"""파이프라인 테스트: 모듈 격리, 결정론성, synthetic 게이트,
모듈별 타임아웃."""

import time

import pytest

from core import pipeline
from core.spec import PIIType, Span


class GoodModule:
    id = "good"
    display_name = "Good"
    requires_external_network = False

    def detect(self, text):
        return [Span(start=0, end=2, type=PIIType.NAME, module=self.id, text=text[0:2])]


class FailingModule:
    id = "boom"
    display_name = "Boom"
    requires_external_network = False

    def detect(self, text):
        raise ValueError("intentional failure")


class HangingModule:
    """진짜로 멈춘 모듈을 흉내 낸다(응답 없는 네트워크 호출 등).

    timeout(0.2s)보다 훨씬 길게 잠들어, 파이프라인이 워커 종료를
    기다렸다면 테스트의 경과 시간 단언이 실패하게 만든다.
    """

    id = "hang"
    display_name = "Hang"
    requires_external_network = False

    def detect(self, text):
        time.sleep(30)
        return []


class ExternalModule:
    id = "ext"
    display_name = "External"
    requires_external_network = True

    def detect(self, text):
        return [Span(start=0, end=1, type=PIIType.NAME, module=self.id, text=text[0:1])]


def _fake_registry(*modules):
    table = {m.id: m for m in modules}
    return lambda module_id: table.get(module_id)


def test_isolation_failing_module_does_not_kill_others(monkeypatch):
    monkeypatch.setattr(pipeline, "get_module", _fake_registry(GoodModule(), FailingModule()))
    result = pipeline.run("abcd", ["good", "boom"], synthetic=True)
    assert "good" in result.results
    assert len(result.results["good"]) == 1
    assert "boom" in result.module_errors
    assert "intentional failure" in result.module_errors["boom"]


def test_determinism(monkeypatch):
    monkeypatch.setattr(pipeline, "get_module", _fake_registry(GoodModule()))
    r1 = pipeline.run("abcd", ["good"], synthetic=True)
    r2 = pipeline.run("abcd", ["good"], synthetic=True)
    assert r1.results == r2.results
    assert r1.module_errors == r2.module_errors
    assert r1.blocked == r2.blocked


def test_synthetic_gate_blocks_external_when_not_synthetic(monkeypatch):
    monkeypatch.setattr(pipeline, "get_module", _fake_registry(ExternalModule()))
    result = pipeline.run("abcd", ["ext"], synthetic=False)
    assert result.blocked == ["ext"]
    assert "ext" not in result.results


def test_synthetic_gate_invokes_external_when_synthetic(monkeypatch):
    monkeypatch.setattr(pipeline, "get_module", _fake_registry(ExternalModule()))
    result = pipeline.run("abcd", ["ext"], synthetic=True)
    assert result.blocked == []
    assert "ext" in result.results
    assert len(result.results["ext"]) == 1


def test_unknown_module_reported_as_error(monkeypatch):
    monkeypatch.setattr(pipeline, "get_module", _fake_registry(GoodModule()))
    result = pipeline.run("abcd", ["nope"], synthetic=True)
    assert "nope" in result.module_errors


def test_timeout_is_isolated_and_wall_clock_enforced(monkeypatch):
    monkeypatch.setattr(pipeline, "get_module", _fake_registry(HangingModule(), GoodModule()))
    started = time.monotonic()
    result = pipeline.run("abcd", ["good", "hang"], synthetic=True, timeout=0.2)
    elapsed = time.monotonic() - started
    # 실효성 단언: 멈춘 모듈(30초 sleep)을 기다리지 않고 timeout 직후 반환해야 한다.
    assert elapsed < 2.0, f"파이프라인이 멈춘 모듈을 기다림 (경과 {elapsed:.2f}s)"
    assert "hang" in result.module_errors
    assert "timed out" in result.module_errors["hang"]
    assert "good" in result.results
