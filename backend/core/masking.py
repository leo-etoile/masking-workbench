"""마스킹: 텍스트 + 스팬을 마스킹된 문자열로 변환한다.

MVP는 **타입 치환**만 지원한다(예: ``[RRN]``, ``[NAME]``). 부분 마스킹과 가역 토큰화는
추후로 미룬다.

겹침(overlap) 처리
-----------------
스팬은 겹칠 수 있다(여러 모듈에서 나올 수 있으므로). 겹치는 스팬은 결정론적으로 연속된
영역으로 병합된다:

1. 스팬을 ``(start, 길이 내림차순)`` 키로 정렬한다(안정 정렬).
2. 인접하거나 겹치는 스팬을 하나의 영역으로 병합한다.
3. 병합된 영역의 **라벨**은 *가장 먼저 시작하는* 스팬의 것을 쓴다. 시작이 같으면
   *더 긴* 스팬이 우선한다(1의 정렬 키가 이를 보장). 시작과 길이가 모두 같으면
   안정 정렬에 의해 입력 순서상 먼저 온 스팬이 유지되므로 결과는 항상 결정론적이다.

치환으로 원문 오프셋이 바뀌므로, 마스킹 텍스트와 함께 **원본 스팬 목록을 변형 없이
그대로** 반환한다(계획서 3장: 원문 스팬 목록을 항상 같이 보관).
"""

from __future__ import annotations

from typing import List, Tuple

from core.spec import Span


def mask(text: str, spans: List[Span]) -> Tuple[str, List[Span]]:
    """``text``의 모든 스팬 영역을 ``[TYPE]``으로 치환한다.

    ``(마스킹된 텍스트, 원본 스팬 목록)`` 튜플을 반환한다. 겹치는 스팬은
    병합된다(모듈 docstring 참고). 입력 ``spans`` 리스트와 그 원소는 변형되지
    않으며 두 번째 반환값으로 그대로 돌려준다.
    """

    if not spans:
        return text, spans

    # start 기준 오름차순, 그리고 길이 기준 내림차순으로 정렬하여 동점 시 첫 스팬이
    # 더 긴 스팬이 되게 한다(아래 라벨 동점 처리를 돕는다).
    ordered = sorted(spans, key=lambda s: (s.start, -(s.end - s.start)))

    # 병합된 영역 구성: (start, end, label_type).
    regions: List[list] = []
    for span in ordered:
        if regions and span.start < regions[-1][1]:
            region = regions[-1]
            # 이 스팬이 더 멀리 뻗으면 영역 끝을 확장한다.
            if span.end > region[1]:
                region[1] = span.end
            # 라벨은 가장 먼저 시작한 스팬의 것으로 유지한다(이미 설정됨). start 순으로
            # 처리하므로 여기서 바꿀 필요가 없다.
        else:
            regions.append([span.start, span.end, span.type])

    # 마스킹된 텍스트를 재구성한다.
    out: List[str] = []
    cursor = 0
    for start, end, label in regions:
        out.append(text[cursor:start])
        out.append(f"[{label.value}]")
        cursor = end
    out.append(text[cursor:])
    return "".join(out), spans
