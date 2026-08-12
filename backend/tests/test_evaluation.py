"""overlap 기반 평가 테스트 — 기대값은 손으로 계산한 값이다.

매칭 규칙: 탐지 스팬과 골드 스팬의 반개구간이 1글자 이상 겹치고 PIIType이
같을 때만 매치된다. 매칭은 greedy one-to-one(골드와 탐지 각각 최대 한 번만
사용)이다.
"""

import math

from core.evaluation import evaluate, evaluate_module
from core.spec import PIIType, Span


def _span(start, end, type_):
    return Span(start=start, end=end, type=type_, module="m", text="x")


def test_hand_computed_example():
    # 골드: 스팬 3개.
    gold = [
        _span(0, 3, PIIType.NAME),    # G1
        _span(10, 24, PIIType.RRN),   # G2
        _span(30, 43, PIIType.PHONE), # G3 (will be missed)
    ]
    # 탐지: 스팬 3개.
    detections = [
        _span(0, 2, PIIType.NAME),    # D1 overlaps G1, same type -> TP
        _span(10, 24, PIIType.RRN),   # D2 overlaps G2, same type -> TP
        _span(50, 60, PIIType.EMAIL), # D3 matches nothing        -> FP
    ]
    # 기대 카운트:
    #   tp = 2 (G1<->D1, G2<->D2)
    #   fp = 1 (D3)
    #   fn = 1 (G3 미매치)
    # precision = tp/(tp+fp) = 2/3 = 0.6666...
    # recall    = tp/(tp+fn) = 2/3 = 0.6666...
    # f1        = 2*p*r/(p+r) = 2/3 = 0.6666...
    m = evaluate_module(gold, detections)
    assert m["tp"] == 2
    assert m["fp"] == 1
    assert m["fn"] == 1
    assert math.isclose(m["precision"], 2 / 3)
    assert math.isclose(m["recall"], 2 / 3)
    assert math.isclose(m["f1"], 2 / 3)


def test_greedy_one_to_one():
    # 골드 1개에 같은 타입의 겹치는 탐지 2개: 하나만 매치될 수 있다.
    gold = [_span(0, 10, PIIType.NAME)]
    detections = [
        _span(0, 5, PIIType.NAME),   # matches gold -> TP
        _span(5, 10, PIIType.NAME),  # gold already used -> FP
    ]
    # tp=1, fp=1, fn=0
    # precision = 1/2 = 0.5, recall = 1/1 = 1.0, f1 = 2*0.5*1/1.5 = 0.6666...
    m = evaluate_module(gold, detections)
    assert (m["tp"], m["fp"], m["fn"]) == (1, 1, 0)
    assert math.isclose(m["precision"], 0.5)
    assert math.isclose(m["recall"], 1.0)
    assert math.isclose(m["f1"], 2 / 3)


def test_type_mismatch_is_not_a_match():
    gold = [_span(0, 10, PIIType.NAME)]
    detections = [_span(0, 10, PIIType.ADDRESS)]  # overlaps but wrong type
    m = evaluate_module(gold, detections)
    assert (m["tp"], m["fp"], m["fn"]) == (0, 1, 1)


def test_zero_division_yields_zero():
    m = evaluate_module([], [])
    assert m == {"precision": 0.0, "recall": 0.0, "f1": 0.0, "tp": 0, "fp": 0, "fn": 0}


def test_evaluate_multi_module():
    gold = [_span(0, 3, PIIType.NAME)]
    detections_by_module = {
        "hit": [_span(0, 3, PIIType.NAME)],
        "miss": [_span(50, 55, PIIType.EMAIL)],
    }
    metrics = evaluate(gold, detections_by_module)
    assert metrics["hit"]["tp"] == 1
    assert metrics["miss"]["tp"] == 0
    assert metrics["miss"]["fp"] == 1
    assert metrics["miss"]["fn"] == 1


def test_evaluate_filters_gold_by_module_supported_types():
    gold = [
        _span(0, 3, PIIType.NAME),
        _span(4, 17, PIIType.EMAIL),
        _span(18, 31, PIIType.PHONE),
    ]

    metrics = evaluate(
        gold,
        {"rule_email": []},
        {"rule_email": {PIIType.EMAIL}},
    )

    assert metrics["rule_email"]["tp"] == 0
    assert metrics["rule_email"]["fp"] == 0
    assert metrics["rule_email"]["fn"] == 1
