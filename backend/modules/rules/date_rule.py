"""규칙 모듈: 날짜 탐지.

탐지 대상:

* ``YYYY-MM-DD``, ``YYYY.MM.DD`` (구분자는 일관되어야 함)
* ``YY.MM.DD`` (2자리 연도, 점 구분)
* 한글 표기 ``1990년 3월 5일`` (공백 유무 무관, ``1990년3월5일`` 포함)

문맥 가드로 더 긴 숫자열 내부를 매치하지 않으며, 2자리 연도 패턴이
4자리 연도 날짜의 꼬리 부분을 매치하는 것을 방지한다.
"""

from __future__ import annotations

import re
from typing import List

from core.spec import PIIType, Span

_PATTERNS = [
    # YYYY-MM-DD / YYYY.MM.DD — 역참조로 구분자 일관성을 강제한다.
    re.compile(r"(?<!\d)\d{4}([-.])\d{1,2}\1\d{1,2}(?!\d)"),
    # YY.MM.DD (점 구분).
    re.compile(r"(?<!\d)\d{2}\.\d{1,2}\.\d{1,2}(?!\d)"),
    # 한글 표기 1990년 3월 5일 (공백 선택).
    re.compile(r"(?<!\d)\d{4}\s*년\s*\d{1,2}\s*월\s*\d{1,2}\s*일"),
]


class DateModule:
    id = "rule_date"
    display_name = "날짜 (규칙)"
    requires_external_network = False
    supported_types = (PIIType.DATE,)
    description = (
        "1. YYYY-MM-DD\n"
        "2. YYYY.MM.DD\n"
        "3. YY.MM.DD\n"
        "4. 1990년 3월 5일\n"
        "※ 겹치는 매치는 가장 앞서고 긴 쪽만 남김"
    )

    def detect(self, text: str) -> List[Span]:
        found: List[Span] = []
        for pattern in _PATTERNS:
            for m in pattern.finditer(text):
                found.append(
                    Span(
                        start=m.start(),
                        end=m.end(),
                        type=PIIType.DATE,
                        module=self.id,
                        text=m.group(),
                    )
                )

        # 겹침 중복 제거: 가장 앞서고 긴 스팬을 유지하고,
        # 이미 유지된 스팬과 겹치는 스팬은 버린다.
        found.sort(key=lambda s: (s.start, -(s.end - s.start)))
        kept: List[Span] = []
        for span in found:
            if any(span.start < k.end and k.start < span.end for k in kept):
                continue
            kept.append(span)
        return kept


MODULE = DateModule()
