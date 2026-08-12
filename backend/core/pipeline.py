"""탐지 파이프라인.

선택된 탐지 모듈들을 단일 텍스트에 대해 실행하고, 그 결과를 **모듈별로 분리**하여
반환한다(union, 병합/중복 제거 없음). 각 모듈은 per-module timeout이 걸린 자체 워커
스레드 안에서 실행되므로, 느리거나 실패하는 모듈이 다른 모듈이나 요청 전체를 절대
쓰러뜨릴 수 없다.

보장 사항
--------
* **격리(isolation)**: 모든 모듈은 timeout이 있는 ``try/except`` 안에서 실행되며,
  실패와 timeout은 ``module_errors``에 기록되고 절대 전파되지 않는다.
* **결정론성(determinism)**: 고정된 입력(text + module ids + synthetic 플래그)에 대해
  실행마다 동일한 출력이 나온다. 각 모듈 안의 스팬은 ``(start, end, type)``으로 정렬되고
  모듈은 id로 키잉된다.
* **synthetic 게이트**: ``synthetic``이 ``False``이면 ``requires_external_network=True``인
  모듈은 호출되지 않고, 대신 그 id가 ``blocked`` 목록에 보고된다.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict, List

from core.registry import get_module
from core.spec import Span, validate_spans

DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass
class PipelineResult:
    """구조화된 파이프라인 출력.

    속성
    ----
    results:
        성공적으로 실행된 모든 모듈에 대한 ``{module_id: [Span, ...]}``.
    module_errors:
        예외를 던지거나 timeout된 모듈에 대한 ``{module_id: message}``.
    blocked:
        외부 네트워크가 필요한데 입력이 synthetic으로 표시되지 않아 건너뛴 모듈 id 목록.
    """

    results: Dict[str, List[Span]] = field(default_factory=dict)
    module_errors: Dict[str, str] = field(default_factory=dict)
    blocked: List[str] = field(default_factory=list)


def _run_one(module, text: str, timeout: float):
    """하나의 모듈 detect()를 스레드 기반 timeout과 함께 실행한다.

    검증되고 정렬된 스팬 목록을 반환한다. 오류/timeout 시에는 예외를 던져서
    호출자가 실패를 기록할 수 있게 한다.

    **데몬 스레드**에서 실행하고 ``join(timeout)``으로 wall-clock 시간을
    강제한다. timeout이 지나면 즉시 ``TimeoutError``를 던지고 워커 스레드는
    그대로 버린다(데몬이므로 프로세스 종료도 막지 않는다). Python 스레드는
    강제 종료가 불가능하므로, 멈춘 모듈을 기다리지 않는 것이 가능한 최선의
    격리다. ``ThreadPoolExecutor``의 ``with`` 블록은 종료 시
    ``shutdown(wait=True)``로 워커가 끝날 때까지 블로킹하기 때문에 사용하지
    않는다.
    """

    outcome: dict = {}

    def _worker() -> None:
        try:
            outcome["spans"] = module.detect(text)
        except BaseException as exc:  # noqa: BLE001 - 예외는 호출 스레드로 전달한다
            outcome["error"] = exc

    thread = threading.Thread(
        target=_worker, daemon=True, name=f"detect-{module.id}"
    )
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        # 워커는 아직 돌고 있지만 기다리지 않고 즉시 반환한다.
        raise TimeoutError(f"module timed out after {timeout:g}s")
    if "error" in outcome:
        raise outcome["error"]

    spans = validate_spans(text, list(outcome["spans"]))
    spans.sort(key=lambda s: (s.start, s.end, s.type.value))
    return spans


def run(
    text: str,
    module_ids: List[str],
    synthetic: bool,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> PipelineResult:
    """선택된 모듈들을 ``text``에 대해 실행하고 :class:`PipelineResult`를 반환한다.

    결정론적 출력을 위해 모듈은 id 정렬 순으로 처리된다. 알 수 없는 module id는
    ``module_errors``에 보고된다.
    """

    result = PipelineResult()

    for module_id in sorted(set(module_ids)):
        module = get_module(module_id)
        if module is None:
            result.module_errors[module_id] = "unknown module id"
            continue

        if module.requires_external_network and not synthetic:
            result.blocked.append(module_id)
            continue

        try:
            result.results[module_id] = _run_one(module, text, timeout)
        except Exception as exc:  # noqa: BLE001 - 격리는 의도된 동작이다
            result.module_errors[module_id] = f"{type(exc).__name__}: {exc}"

    result.blocked.sort()
    return result
