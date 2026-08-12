"""규칙 모듈: 주민등록번호(RRN) 탐지.

탐지 대상:

* ``123456-1234567`` (하이픈 포함, 6 + 7자리)
* ``1234561234567`` (하이픈 없는 13자리)
* ``123456-1******``, ``123456-*******`` 같은 뒷자리 마스킹 변형

문맥 가드(negative look-behind/look-ahead)로 더 긴 숫자열 내부를 매치하지
않는다. 예를 들어 15자리 숫자는 주민등록번호로 보고되지 않는다.
"""

from __future__ import annotations

import re
from typing import List

from core.spec import PIIType, Span

# 하이픈 형태(뒷자리 마스킹 포함): 6자리 숫자 + 하이픈 + 숫자 또는 '*' 7자
# (최소한 앞부분은 실제 숫자여야 한다).
_HYPHEN = re.compile(r"(?<![\d*])\d{6}-[\d*]{7}(?![\d*])")

# 하이픈 없는 13자리 형태. 더 긴 숫자열의 일부가 되지 않도록 가드한다.
_PLAIN = re.compile(r"(?<!\d)\d{13}(?!\d)")


class RRNModule:
    id = "rule_rrn"
    display_name = "주민등록번호 (규칙)"
    requires_external_network = False
    supported_types = (PIIType.RRN,)
    description = (
        "1. 123456-1234567 (하이픈, 6+7자리)\n"
        "2. 1234561234567 (하이픈 없음, 13자리)\n"
        "3. 123456-1****** (뒷자리 마스킹 변형)\n"
        "※ 더 긴 숫자열의 일부는 매치하지 않음"
    )

    def detect(self, text: str) -> List[Span]:
        spans: List[Span] = []
        for pattern in (_HYPHEN, _PLAIN):
            for m in pattern.finditer(text):
                spans.append(
                    Span(
                        start=m.start(),
                        end=m.end(),
                        type=PIIType.RRN,
                        module=self.id,
                        text=m.group(),
                    )
                )
        return spans


MODULE = RRNModule()
