"""규칙 모듈: 전화번호 탐지.

탐지 대상:

* 휴대폰: ``010-1234-5678``, ``01012345678``, ``010 1234 5678``
  (011/016/017/018/019 구형 식별번호 포함)
* 유선: ``02-123-4567``, ``031-123-4567`` (지역번호 02, 0XX, 070)

세 그룹 사이 구분자는 하이픈, 공백 하나, 또는 없음이 허용된다.
문맥 가드로 더 긴 숫자열 내부는 매치하지 않는다.
"""

from __future__ import annotations

import re
from typing import List

from core.spec import PIIType, Span

_MOBILE = r"01[016789][-\s]?\d{3,4}[-\s]?\d{4}"
_LANDLINE = r"0(?:2|[3-6]\d|70)[-\s]?\d{3,4}[-\s]?\d{4}"

# 01X 번호가 유선으로 잘못 쪼개지지 않도록 휴대폰 패턴을 먼저 시도한다.
_PHONE = re.compile(rf"(?<!\d)(?:{_MOBILE}|{_LANDLINE})(?!\d)")


class PhoneModule:
    id = "rule_phone"
    display_name = "전화번호 (규칙)"
    requires_external_network = False
    supported_types = (PIIType.PHONE,)
    description = (
        "1. 010-1234-5678 (휴대폰, 하이픈)\n"
        "2. 01012345678 (휴대폰, 구분자 없음)\n"
        "3. 010 1234 5678 (휴대폰, 공백)\n"
        "4. 02-123-4567 (유선, 지역번호)\n"
        "※ 011/016~019 구형 식별번호, 031 등 지역번호도 포함되며\n"
        "  더 긴 숫자열의 일부는 매치하지 않음"
    )

    def detect(self, text: str) -> List[Span]:
        spans: List[Span] = []
        for m in _PHONE.finditer(text):
            spans.append(
                Span(
                    start=m.start(),
                    end=m.end(),
                    type=PIIType.PHONE,
                    module=self.id,
                    text=m.group(),
                )
            )
        return spans


MODULE = PhoneModule()
