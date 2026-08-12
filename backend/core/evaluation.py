"""골드 라벨 대비 모듈별 평가.

매칭 기준
---------
탐지 스팬이 골드 스팬과 **매치**되려면 두 반개구간이 한 글자 이상 겹치고
(**overlap**) 타입(:class:`~core.spec.PIIType`)이 같아야 한다.

매칭은 **greedy one-to-one** 방식이다: 골드 스팬 하나는 최대 하나의 탐지와,
탐지 하나는 최대 하나의 골드 스팬과만 매치된다. 골드 스팬을 ``(start, end)``
순으로 순회하면서, 아직 매치되지 않은 탐지들(역시 ``(start, end)`` 순) 중
겹침 + 동일 타입 조건을 만족하는 첫 번째를 차지한다. 이 방식으로 결과가
결정론적이 된다.

매치 결과로부터 모듈별 precision/recall/f1과 tp/fp/fn을 계산한다:

* ``tp`` = 매치된 (골드, 탐지) 쌍의 수
* ``fp`` = 어떤 골드 스팬과도 매치되지 않은 탐지 수
* ``fn`` = 어떤 탐지와도 매치되지 않은 골드 스팬 수

0으로 나누는 경우는 모두 ``0.0``을 반환한다.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from core.spec import PIIType, Span


def _overlaps(a: Span, b: Span) -> bool:
    """두 반개구간이 한 글자 이상 겹치면 True."""

    return a.start < b.end and b.start < a.end


def _match(gold: List[Span], detections: List[Span]) -> int:
    """greedy one-to-one 매칭으로 true positive 개수를 반환한다."""

    gold_sorted = sorted(gold, key=lambda s: (s.start, s.end))
    det_sorted = sorted(detections, key=lambda s: (s.start, s.end))
    used = [False] * len(det_sorted)

    tp = 0
    for g in gold_sorted:
        for i, d in enumerate(det_sorted):
            if used[i]:
                continue
            if d.type == g.type and _overlaps(g, d):
                used[i] = True
                tp += 1
                break
    return tp


def _prf(tp: int, fp: int, fn: int) -> Dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return {"precision": precision, "recall": recall, "f1": f1}


def evaluate_module(gold: List[Span], detections: List[Span]) -> Dict[str, float]:
    """한 모듈의 탐지 결과에 대한 precision/recall/f1과 tp/fp/fn을 계산한다."""

    tp = _match(gold, detections)
    fp = len(detections) - tp
    fn = len(gold) - tp
    metrics = _prf(tp, fp, fn)
    metrics.update({"tp": tp, "fp": fp, "fn": fn})
    return metrics


def evaluate(
    gold: List[Span],
    detections_by_module: Dict[str, List[Span]],
    supported_types_by_module: Optional[Dict[str, Set[PIIType]]] = None,
) -> Dict[str, Dict[str, float]]:
    """각 모듈이 지원하는 유형의 골드 라벨만 사용하여 지표를 계산한다."""

    return {
        module_id: evaluate_module(
            [
                span
                for span in gold
                if supported_types_by_module is None
                or module_id not in supported_types_by_module
                or span.type in supported_types_by_module[module_id]
            ],
            dets,
        )
        for module_id, dets in detections_by_module.items()
    }
